"""The carried ``reductions`` registry is well formed and bound to its values.

Six things this pins, and one it deliberately does.

1. **Traceability.** ESTABLISHED ELSEWHERE AND NOT HERE. The claim ids,
   reason strings, row orders and keys of the registry are bound to the CLAIM
   FILES and the THREE interface files in
   ``test_reductions_registry_interface.py``. What stays in this file is the
   binding of the frozen values to the CODE.
2. **Admissibility (ADR-0003).** No expected value here comes from MATLAB,
   OpenQKDSecurity, CVX, MOSEK or Julia. The guard reuses
   ``registry.INADMISSIBLE_SOURCES``, imported rather than restated, so the
   registries cannot drift on what an admissible oracle is.
3. **Well-formedness of every frozen OBJECT, checked EXACTLY.** Hermiticity,
   positive semidefiniteness by ALL principal minors (not merely the leading
   ones), POVM completeness, column-stochasticity, orthonormality of the frozen
   unit vectors, and Kraus completeness ``sum_K K+ K = 1``. Every check is exact
   Gaussian-rational arithmetic; NO TOLERANCE APPEARS ANYWHERE, because the
   contract's Section 1.4 says its statements are "operator identities and
   inequalities between EXACTLY DECLARED QUANTITIES".
4. **Internal consistency of the frozen tables.** The frozen physical POVM
   equals ``Lambda+(F)`` computed FROM THE FROZEN KRAUS OPERATORS; the two
   realizing channels agree on the carried span and differ off it; the
   transported projectors are the pull-backs Eq. ``eq:transportproj`` names;
   ``eq:weightroute`` reproduces every emitted weight. (The dimensions of the
   frozen branching target are checked with the registry's removable half.)
5. **The refusal-reason totality proof.** The set of reason strings in the
   registry equals the set in ``interface.yaml`` equals the set spanned by the
   fail-closed rows -- 27 strings over 25 rows at 0.3.0 -- so a twenty-eighth
   string cannot be introduced on either side without a failing test. This is
   the protocol-compiler band's totality-proof precedent applied to the one
   thing THIS contract fixes verbatim that its siblings do not. AND THE FOUR
   MACHINE STRINGS THE 0.3.0 TEXT QUOTES FROM ``meat-core`` 0.5.0 --
   ``bob_povm_not_evaluable``, ``declared_operator_tolerance_open``,
   ``key_length``, ``key_length_claim`` -- are checked to be ABSENT from the
   vocabulary and from ``interface.yaml``'s reason list, because a naive sweep
   of the contract's ``texttt`` tokens would put the count at thirty-one.
6. **No assertion that the package is absent.** The registry never imports
   ``certiqs_key.reductions``, which is asserted on the import graph, and no
   test of this file asserts anything about the package's absence on disk.

**What is deliberately absent: any reconstruction of the module.** Nothing here
squashes a POVM, validates a declaration, composes a chain or emits an artifact.
Every assertion either substitutes a frozen value into a contract equation --
Eq. ``eq:pairing`` for the Kraus adjoint, Eq. ``eq:weightroute`` for the
weights -- or relates two frozen fields
of the same case. That is the discipline ``registry.py`` states for C11 and C12
(an oracle that *is* the implementation checks the solver against itself), and it
binds harder in run A of a two-run band, where no implementation exists yet and
the whole point of the freeze is that run B cannot tune the values to its code.

WHAT IS ABSENT, AND WHY
=======================
This file once also asserted an earlier ``interface.yaml`` -- its claim list,
its convention bullets, its fail-closed rows, its open implementation choices,
its delta blocks, its deferrals, its locator residues -- against the frozen
values. That document has no successor at the same shape (the claims are claim
files under ``spec/modules/reductions/`` and the interface is the core's file
and each submodule's), and a test that reads a missing file is not evidence of
anything, so those tests are not here. Eight of them are re-established, under
their own names, against the claim FILES and the interface files in
``test_reductions_registry_interface.py``:

* ``test_every_oracle_claim_id_exists_in_the_interface``
* ``test_refusal_reason_totality_registry_equals_interface``
* ``test_every_fail_closed_row_has_at_least_one_registry_case``
* ``test_the_interface_key_vocabulary_is_the_frozen_one``
* ``test_the_link_vocabulary_matches_the_interface``
* ``test_the_interface_carries_the_nine_assumption_ledger_rows``
* ``test_the_two_rounding_rules_are_recorded_and_are_two``
* ``test_the_corpus_directory_is_never_named``

The other twenty-two each read a key the interface files DELIBERATELY
RETIRE -- the delta blocks, the change-request candidates, the open
implementation choices, the provenance recount, the accepted-contract pin, the
declared operator tolerance, the wire-form comparison, the locator residues,
the keyed deferral block -- or are a file-name scan over names this repository
does not use.

NO FROZEN NUMBER, CASE, SUPERSESSION MARK OR ORACLE ENTRY IS EDITED. The frozen
registry's prose carries a textual cut that produced its removable half
(``registry_reductions.py`` states it in its header).
"""

from __future__ import annotations

import ast
from fractions import Fraction
from itertools import combinations
from pathlib import Path
from typing import Any, cast

import pytest
from registry_reductions import (
    ASSUMPTION_LEDGER_0_2_0,
    ASSUMPTION_LEDGER_0_3_0,
    ASSURANCE,
    BLK_GT_V0,
    BLK_GT_V1,
    BRANCH_PROBE_WEIGHT_CASES,
    CERT_TWO_SECTOR,
    CERTIFICATE_CASES,
    CERTIFICATE_KINDS,
    CHAIN_CASES,
    CHANGE_REQUEST_CANDIDATES,
    COLSTOCH_CASES,
    COLSTOCH_PROBE_WEIGHTS,
    COLSTOCH_SLOT_WEIGHT,
    DESCENT_COUNTEREXAMPLE,
    INADMISSIBLE_SOURCES,
    KINDS,
    LICENCE_CASES,
    LICENCE_PROBE_IDENTITY,
    LICENCE_TRUSTED,
    LICENCE_UNTRUSTED,
    LINK_KINDS_DEFERRED,
    LINK_KINDS_IMPLEMENTED,
    LINK_RECORDS,
    LINK_STAGES,
    LINK_STATUS_EMITTED,
    MIXTURE_CASE,
    MP_V0,
    MP_V1,
    NOT_SUPERSEDED_AND_WHY,
    NOT_SUPERSEDED_AND_WHY_0_3_0,
    O_ID_OFFSPAN,
    O_OFF,
    O_OFF_PULLBACK_PRIME,
    OBSTRUCTION_CASES,
    PI_FLAG_Q,
    PI_GT_B,
    PI_LEQ_B,
    PI_LEQ_Q,
    PR_OBSTRUCTION,
    PR_ORACLES,
    PROBE22,
    PROBE22_MPRIME,
    PROBE22_SUM_T0,
    PROBE22_TARGET,
    PROBE22_UNSOUND,
    PROBE22_V,
    PSI_0,
    PSI_1,
    REFUSAL_CASES,
    REFUSAL_REASONS,
    REFUSAL_REASONS_0_2_0,
    RELATION_CASES,
    SLOT_VALIDATION_CASES,
    SOURCE_MODES,
    SUPERSEDED_SYMBOLS,
    SUPERSEDED_SYMBOLS_0_3_0,
    SUPERSESSIONS,
    SUPERSESSIONS_0_3_0,
    TIGHT,
    TOL2_BLOCKS,
    TOL2_DCF,
    TOL2_DELTA_T,
    TOL2_EPS_OP,
    TOL2_ETA,
    TOL2_ETA_V,
    TOL2_JOINT_NB,
    TOL2_Q,
    TOL2_RCG,
    TOL2_T,
    TOL2_TARGETPOSCOMP,
    TOL2_TILDE,
    TOL2_TOLERANCE_RECORD,
    TOL2_TOLERANCE_RECORD_ABSENT,
    TOL2_Y,
    TOL_ENTRY_CASES,
    TOL_ENTRY_CLAUSES,
    TOL_ENTRY_DEFAULT_CARRIED,
    TOL_ENTRY_FLAG,
    TOL_ENTRY_OUTSIDE_FORM,
    TOL_ENTRY_PROBE_T0,
    TOL_ENTRY_PROBE_T1,
    TOL_ENTRY_TWO_SECTOR,
    TOL_FLOAT_SENSITIVE_CASES,
    TOL_ROW_CASES,
    TOL_SCOPE_CASES,
    TRANSFER_CASES,
    WEIGHT_ROUTE_CASES,
    WP3,
    WP3_FFSS_V0,
    WP3_FFSS_V1,
    WP3_FWP_V0,
    WP3_FWP_V1,
    WP3_KRAUS,
    WP3_KRAUS_PRIME,
    WP3_M_V0,
    WP3_M_V1,
    Matrix,
    pr_oracle,
)

CONTRACT_VERSION = "0.3.0"
SUPERSEDED_CONTRACT_VERSION = "0.2.0"
#: The version the band BEFORE last froze, still marked and never deleted.
SUPERSEDED_CONTRACT_VERSION_0_1_3 = "0.1.3"
#: The pinned SUPPLIER at 0.3.0 (an import) and the pinned CONSUMER (not one).
SUPPLIER_VERSION = "0.2.0"
CLAIM_IDS = tuple(f"PR{i}" for i in range(1, 14))

F = Fraction


# ---------------------------------------------------------------------------
#  Exact Gaussian-rational arithmetic, local to the tests.
#
#  The registry contains no arithmetic by design; the checks need some, and it
#  lives here. Every operation is exact and no tolerance appears anywhere.
# ---------------------------------------------------------------------------

Gauss = tuple[Fraction, Fraction]


def _add(a: Gauss, b: Gauss) -> Gauss:
    return (a[0] + b[0], a[1] + b[1])


def _sub(a: Gauss, b: Gauss) -> Gauss:
    return (a[0] - b[0], a[1] - b[1])


def _mul(a: Gauss, b: Gauss) -> Gauss:
    return (a[0] * b[0] - a[1] * b[1], a[0] * b[1] + a[1] * b[0])


def _conj(a: Gauss) -> Gauss:
    return (a[0], -a[1])


def _zeros(n: int, m: int | None = None) -> Matrix:
    m = n if m is None else m
    return tuple(tuple((F(0), F(0)) for _ in range(m)) for _ in range(n))


def _eye(n: int) -> Matrix:
    return tuple(
        tuple((F(1), F(0)) if i == j else (F(0), F(0)) for j in range(n))
        for i in range(n)
    )


def _madd(a: Matrix, b: Matrix) -> Matrix:
    return tuple(
        tuple(_add(a[i][j], b[i][j]) for j in range(len(a[0]))) for i in range(len(a))
    )


def _msub(a: Matrix, b: Matrix) -> Matrix:
    return tuple(
        tuple(_sub(a[i][j], b[i][j]) for j in range(len(a[0]))) for i in range(len(a))
    )


def _smul(c: Fraction, a: Matrix) -> Matrix:
    scalar = (c, F(0))
    return tuple(
        tuple(_mul(scalar, a[i][j]) for j in range(len(a[0]))) for i in range(len(a))
    )


def _mmul(a: Matrix, b: Matrix) -> Matrix:
    rows, inner, cols = len(a), len(b), len(b[0])
    out = []
    for i in range(rows):
        row = []
        for j in range(cols):
            acc: Gauss = (F(0), F(0))
            for k in range(inner):
                acc = _add(acc, _mul(a[i][k], b[k][j]))
            row.append(acc)
        out.append(tuple(row))
    return tuple(out)


def _dag(a: Matrix) -> Matrix:
    return tuple(tuple(_conj(a[j][i]) for j in range(len(a))) for i in range(len(a[0])))


def _is_hermitian(a: Matrix) -> bool:
    return a == _dag(a)


def _det(a: Matrix) -> Gauss:
    n = len(a)
    if n == 0:
        return (F(1), F(0))
    if n == 1:
        return a[0][0]
    total: Gauss = (F(0), F(0))
    for j in range(n):
        minor = tuple(tuple(a[i][k] for k in range(n) if k != j) for i in range(1, n))
        term = _mul(a[0][j], _det(minor))
        total = _add(total, term) if j % 2 == 0 else _sub(total, term)
    return total


def _is_psd(a: Matrix) -> bool:
    """Exact PSD test: Hermitian with EVERY principal minor non-negative.

    The leading principal minors alone characterize positive DEFINITENESS, not
    semidefiniteness, so all 2^n - 1 principal minors are checked. The matrices
    here are at most 5 x 5, so the enumeration is cheap and exact.
    """
    if not _is_hermitian(a):
        return False
    n = len(a)
    for size in range(1, n + 1):
        for idx in combinations(range(n), size):
            minor = tuple(tuple(a[i][j] for j in idx) for i in idx)
            value = _det(minor)
            if value[1] != 0 or value[0] < 0:
                return False
    return True


def _adjoint_from_kraus(kraus: tuple[Matrix, ...], x: Matrix) -> Matrix:
    """Eq. eq:pairing read through a Kraus set: Lambda+(X) = sum_K K+ X K."""
    out = _zeros(len(kraus[0][0]))
    for k in kraus:
        out = _madd(out, _mmul(_mmul(_dag(k), x), k))
    return out


def _wp_adjoint(x: Matrix, blocks: tuple[Matrix, Matrix]) -> Matrix:
    """Eq. eq:WPadjoint on WP3's block structure (1 preserved, 2 flag)."""
    flag = _madd(_smul(x[1][1][0], blocks[0]), _smul(x[2][2][0], blocks[1]))
    out = [[(F(0), F(0)) for _ in range(3)] for _ in range(3)]
    out[0][0] = x[0][0]
    for i in range(2):
        for j in range(2):
            out[i + 1][j + 1] = flag[i][j]
    return tuple(tuple(row) for row in out)


def _povm_elements(pairs: tuple[tuple[str, Matrix], ...]) -> list[Matrix]:
    return [matrix for _, matrix in pairs]


# ---------------------------------------------------------------------------
#  1. Traceability against the G4 interface
# ---------------------------------------------------------------------------






@pytest.mark.contract
def test_the_registry_covers_every_claim_of_the_contract() -> None:
    covered = {claim for entry in PR_ORACLES for claim in entry.claims}
    assert set(CLAIM_IDS) <= covered


















# ---------------------------------------------------------------------------
#  2. Admissibility and entry well-formedness
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_no_inadmissible_source_is_named_anywhere() -> None:
    haystacks = [entry.derivation for entry in PR_ORACLES]
    haystacks += [entry.subject for entry in PR_ORACLES]
    haystacks += [case.derivation for case in RELATION_CASES]
    haystacks += [case.derivation for case in CERTIFICATE_CASES]
    haystacks += [case.derivation for case in LICENCE_CASES]
    haystacks += [case.derivation for case in WEIGHT_ROUTE_CASES]
    haystacks += [case.derivation for case in REFUSAL_CASES]
    haystacks += [link.derivation for link in LINK_RECORDS]
    haystacks += [chain.derivation for chain in CHAIN_CASES]
    haystacks += [note for _, _, note in CHANGE_REQUEST_CANDIDATES]
    for text in haystacks:
        for banned in INADMISSIBLE_SOURCES:
            assert banned not in text, banned




@pytest.mark.contract
def test_entries_are_unique_well_kinded_and_carry_a_derivation() -> None:
    ids = [entry.oracle_id for entry in PR_ORACLES]
    assert len(ids) == len(set(ids))
    for entry in PR_ORACLES:
        assert entry.kind in KINDS, (entry.oracle_id, entry.kind)
        assert entry.assurance == ASSURANCE == "estimate"
        # Long enough to redo on paper.
        assert len(entry.derivation) > 200, entry.oracle_id
        assert entry.subject.strip(), entry.oracle_id
        assert pr_oracle(entry.oracle_id) is entry
    with pytest.raises(KeyError):
        pr_oracle("O-PR-DOES-NOT-EXIST")


@pytest.mark.contract
def test_every_hypothesis_names_a_ledger_assumption() -> None:
    known = {row.assumption_id for row in ASSUMPTION_LEDGER_0_2_0}
    for entry in PR_ORACLES:
        for hypothesis in entry.hypotheses:
            assert hypothesis in known, (entry.oracle_id, hypothesis)


# ---------------------------------------------------------------------------
#  3. Well-formedness of every frozen object, checked exactly
# ---------------------------------------------------------------------------


@pytest.mark.contract
@pytest.mark.parametrize("case", RELATION_CASES, ids=lambda c: c.case_id)
def test_every_frozen_relation_carries_two_povms(case: Any) -> None:
    for label, family in (("physical", case.physical), ("target", case.target)):
        elements = _povm_elements(family)
        assert len(elements) == len(case.alphabet), (case.case_id, label)
        total = _zeros(len(elements[0]))
        for element in elements:
            assert _is_hermitian(element), (case.case_id, label)
            assert _is_psd(element), (case.case_id, label)
            total = _madd(total, element)
        expected = _eye(case.source_dim if label == "physical" else case.target_dim)
        assert total == expected, (case.case_id, label)


@pytest.mark.contract
def test_the_frozen_unit_vectors_are_orthonormal() -> None:
    """psi_0 and psi_1 built from the Pythagorean triple (3, 4, 5)."""

    def inner(u: tuple[Gauss, ...], v: tuple[Gauss, ...]) -> Gauss:
        acc: Gauss = (F(0), F(0))
        for a, b in zip(u, v, strict=True):
            acc = _add(acc, _mul(_conj(a), b))
        return acc

    assert inner(PSI_0, PSI_0) == (F(1), F(0))
    assert inner(PSI_1, PSI_1) == (F(1), F(0))
    assert inner(PSI_0, PSI_1) == (F(0), F(0))
    # And they are GENUINELY COMPLEX: a real-only fixture could not exercise
    # the Hermitian-versus-symmetric distinction of Eq. eq:pairing.
    assert any(entry[1] != 0 for entry in PSI_0)
    assert any(entry[1] != 0 for entry in PSI_1)


@pytest.mark.contract
def test_the_frozen_kraus_sets_are_complete() -> None:
    """sum_K K+ K = 1 exactly, for BOTH realizing channels of WP3."""
    for label, kraus in (("Lambda^WP", WP3_KRAUS), ("Lambda'", WP3_KRAUS_PRIME)):
        total = _zeros(3)
        for operator in kraus:
            total = _madd(total, _mmul(_dag(operator), operator))
        assert total == _eye(3), label


@pytest.mark.contract
def test_the_mprime_family_is_a_rank_one_pvm() -> None:
    """M'_v = |psi_v><psi_v|: PSD, complete, and each of trace one."""
    assert _madd(MP_V0, MP_V1) == _eye(2)
    for label, element in (("M'_v0", MP_V0), ("M'_v1", MP_V1)):
        assert _is_psd(element), label
        assert _add(element[0][0], element[1][1]) == (F(1), F(0)), label
        # Rank one: determinant zero.
        assert _det(element) == (F(0), F(0)), label


@pytest.mark.contract
def test_the_above_cutoff_blocks_satisfy_the_certified_weight_condition() -> None:
    """Eq. eq:certweights: blk M^{>N}_v - p_v 1 >= 0, and it equals (1-p) M'_v."""
    weights = dict(WP3["weights"])  # type: ignore[arg-type]
    one_minus = WP3["one_minus_total"]
    assert isinstance(one_minus, Fraction)
    for label, block, mprime in (
        ("v0", BLK_GT_V0, MP_V0),
        ("v1", BLK_GT_V1, MP_V1),
    ):
        residual = _msub(block, _smul(weights[label], _eye(2)))
        assert _is_psd(residual), label
        assert residual == _smul(one_minus, mprime), label
    # And the total weight is admissible: p_v >= 0 and p < 1 (Def. def:targets).
    total = WP3["total_weight"]
    assert isinstance(total, Fraction)
    assert all(value >= 0 for value in weights.values())
    assert total == sum(weights.values())
    assert total < 1








@pytest.mark.contract
@pytest.mark.parametrize("case", WEIGHT_ROUTE_CASES, ids=lambda c: c.case_id)
def test_the_descended_matrices_are_column_stochastic(case: Any) -> None:
    columns = dict(case.descended_matrix)
    assert set(columns) == set(case.letters), case.case_id
    for column, rows in columns.items():
        entries = dict(rows)
        assert set(entries) == set(case.letters), (case.case_id, column)
        assert all(value >= 0 for value in entries.values()), (case.case_id, column)
        assert sum(entries.values()) == 1, (case.case_id, column)


# ---------------------------------------------------------------------------
#  4. Internal consistency of the frozen tables
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_the_frozen_physical_povm_is_the_kraus_adjoint_of_the_target() -> None:
    """Eq. eq:pairing, computed FROM THE FROZEN KRAUS OPERATORS."""
    assert _adjoint_from_kraus(WP3_KRAUS, WP3_FWP_V0) == WP3_M_V0
    assert _adjoint_from_kraus(WP3_KRAUS, WP3_FWP_V1) == WP3_M_V1


@pytest.mark.contract
def test_the_fss_target_pulls_back_to_the_same_physical_povm() -> None:
    """Eq. eq:WPadjoint at p_v = 0, with M'_v replaced by blk M^{>N}_v."""
    blocks = (BLK_GT_V0, BLK_GT_V1)
    assert _wp_adjoint(WP3_FFSS_V0, blocks) == WP3_M_V0
    assert _wp_adjoint(WP3_FFSS_V1, blocks) == WP3_M_V1


@pytest.mark.contract
def test_the_transported_projectors_are_the_frozen_pullbacks() -> None:
    """Eq. eq:transportproj, for BOTH channels and BOTH targets."""
    assert _adjoint_from_kraus(WP3_KRAUS, PI_LEQ_Q) == PI_LEQ_B
    assert _adjoint_from_kraus(WP3_KRAUS, PI_FLAG_Q) == PI_GT_B
    blocks = (BLK_GT_V0, BLK_GT_V1)
    assert _wp_adjoint(PI_LEQ_Q, blocks) == PI_LEQ_B
    assert _wp_adjoint(PI_FLAG_Q, blocks) == PI_GT_B
    # The pull-backs are POSITIVE though NOT multiples of the identity -- the
    # sentence Section 2.1 uses to admit the default pair on c = 0, >=.
    assert _is_psd(PI_LEQ_B) and _is_psd(PI_GT_B)
    assert _smul(F(1), _eye(3)) != PI_LEQ_B
    assert _smul(F(1), _eye(3)) != PI_GT_B


@pytest.mark.contract
def test_the_two_channels_agree_on_the_span_and_differ_off_it() -> None:
    """Lemma lem:statistics' uniqueness clause, and Remark rem:channel-choice."""
    for carried in (WP3_FWP_V0, WP3_FWP_V1, PI_LEQ_Q, PI_FLAG_Q):
        assert _adjoint_from_kraus(WP3_KRAUS, carried) == _adjoint_from_kraus(
            WP3_KRAUS_PRIME, carried
        )
    # Off the span they DISAGREE, and the frozen difference is exact.
    assert _adjoint_from_kraus(WP3_KRAUS, O_OFF) == _zeros(3)
    assert _adjoint_from_kraus(WP3_KRAUS_PRIME, O_OFF) == O_OFF_PULLBACK_PRIME
    assert _zeros(3) != O_OFF_PULLBACK_PRIME
    assert _is_hermitian(O_OFF_PULLBACK_PRIME)
    # And it is GENUINELY COMPLEX: the -+7i/25 entries.
    assert any(O_OFF_PULLBACK_PRIME[i][j][1] != 0 for i in range(3) for j in range(3))
    # The non-trivial IDENTITY certificate that is tied to one channel.
    assert _adjoint_from_kraus(WP3_KRAUS, O_ID_OFFSPAN) == _eye(3)
    assert _adjoint_from_kraus(WP3_KRAUS_PRIME, O_ID_OFFSPAN) != _eye(3)


@pytest.mark.contract
@pytest.mark.parametrize("case", CERTIFICATE_CASES, ids=lambda c: c.case_id)
def test_every_certificate_case_is_typed_and_discharged(case: Any) -> None:
    assert case.certificate_kind in CERTIFICATE_KINDS, case.case_id
    assert case.sound is True, case.case_id
    if case.ohat is None or case.pullback is None:
        # The identity case on PROBE22 carries its data in the instance tables.
        assert case.certificate_kind == "identity", case.case_id
        return
    assert _is_hermitian(case.ohat), case.case_id
    assert _is_hermitian(case.pullback), case.case_id
    if case.certificate_kind == "positivity":
        # The PULL-BACK is positive; the operator on Q need NOT be, and here it
        # is not -- which is the whole content of Corollary cor:pullback (ii).
        assert _is_psd(case.pullback), case.case_id
        assert not _is_psd(case.ohat), case.case_id
        assert case.constant == 0, case.case_id


@pytest.mark.contract
def test_the_cor_fssinstance_pullback_is_the_frozen_one() -> None:
    """Lambda^FSS+(F^FSS_v0 - p_v0 Pi_flag) = [2/3] (+) (5/8) M'_v0."""
    entry = next(c for c in CERTIFICATE_CASES if c.case_id == "WP3-cert-positivity")
    ohat = _msub(WP3_FFSS_V0, _smul(F(1, 4), PI_FLAG_Q))
    assert ohat == entry.ohat
    pullback = _wp_adjoint(ohat, (BLK_GT_V0, BLK_GT_V1))
    assert pullback == entry.pullback
    assert _is_psd(pullback)
    # And it equals M_v0 - (1/4) Pi_>N, the form cor:fssinstance writes.
    assert pullback == _msub(WP3_M_V0, _smul(F(1, 4), PI_GT_B))


@pytest.mark.contract
def test_the_two_sector_entry_cuts_the_strictly_smaller_set() -> None:
    """Remark rem:published: the a > 0 entry is the STRONGER constraint."""
    a, b = F(2, 3), F(1, 4)
    ohat_a0 = _msub(WP3_FFSS_V0, _smul(b, PI_FLAG_Q))
    ohat = _msub(ohat_a0, _smul(a, PI_LEQ_Q))
    entry = next(c for c in CERTIFICATE_CASES if c.case_id == "WP3-cert-two-sector")
    assert ohat == entry.ohat
    assert _wp_adjoint(ohat, (BLK_GT_V0, BLK_GT_V1)) == entry.pullback
    assert _is_psd(entry.pullback)
    # The witness of strictness: sigma = (|q><q| + |f_v1><f_v1|)/2.

    def expectation(operator: Matrix, diagonal: tuple[Fraction, ...]) -> Fraction:
        return sum(
            (operator[i][i][0] * diagonal[i] for i in range(len(diagonal))),
            start=F(0),
        )

    sigma = (F(1, 2), F(0), F(1, 2))
    assert expectation(ohat_a0, sigma) == F(5, 24)
    assert expectation(ohat, sigma) == F(-1, 8)
    assert expectation(ohat_a0, sigma) >= 0
    assert expectation(ohat, sigma) < 0


@pytest.mark.contract
def test_the_probe22_target_is_a_povm_and_the_transplant_fails() -> None:
    """Remark rem:unsound with the numbers that show it fails."""
    order = {v: i for i, v in enumerate(PROBE22_V)}
    assert len(order) == 4
    # The joint family and the target are complete.
    assert sum(preserved for _, preserved, _ in PROBE22_TARGET) == 1
    for k in range(4):
        assert sum(flag[k] for _, _, flag in PROBE22_TARGET) == 1
    # sum_y F_(y,t0): preserved entry IS q_t0, flag entries are NOT.
    q_t0 = F(2, 3)
    preserved = sum(p for outcome, p, _ in PROBE22_TARGET if outcome[1] == "t0")
    flags = tuple(
        sum(flag[k] for outcome, _, flag in PROBE22_TARGET if outcome[1] == "t0")
        for k in range(4)
    )
    assert (preserved, *flags) == PROBE22_SUM_T0
    assert preserved == q_t0
    assert any(value != q_t0 for value in flags)
    # ... but the PULL-BACK is q_t0 1_B exactly (the identity certificate).
    mprime = dict(PROBE22_MPRIME)
    for block in (0, 1):
        value = sum(flags[order[v]] * mprime[v][block] for v in PROBE22_V)
        assert value == q_t0
    # The reachable state and the projector on which the OPERATOR form fails.
    reachable = tuple(mprime[v][0] for v in PROBE22_V)
    assert reachable == tuple(PROBE22_UNSOUND["reachable_state"])  # type: ignore[arg-type]
    assert sum(reachable) == 1
    assert sum(flags[order[v]] * reachable[order[v]] for v in PROBE22_V) == q_t0
    witness = order[("y1", "t0")]
    assert flags[witness] * reachable[witness] == PROBE22_UNSOUND["operator_form_lhs"]
    assert q_t0 * reachable[witness] == PROBE22_UNSOUND["operator_form_rhs"]
    assert PROBE22_UNSOUND["operator_form_lhs"] != PROBE22_UNSOUND["operator_form_rhs"]
    assert PROBE22_UNSOUND["refusal_reason"] == "unsound_constraint_requested"


@pytest.mark.contract
def test_probe22_weights_are_certified_and_below_one() -> None:
    joint = {outcome: (pres, gt) for outcome, pres, gt in PROBE22["joint"]}  # type: ignore[misc]
    weights = dict(PROBE22["weights"])  # type: ignore[arg-type]
    total = PROBE22["total_weight"]
    assert isinstance(total, Fraction)
    assert sum(weights.values()) == total
    assert total < 1
    for outcome, weight in weights.items():
        assert min(joint[outcome][1]) >= weight, outcome
    # And the private setting really is a weight inside the POVM elements.
    q = dict(PROBE22["probe_weights"])  # type: ignore[arg-type]
    assert sum(q.values()) == 1
    assert all(value > 0 for value in q.values())
    conditional = {(y, t): (p, g) for y, t, p, g in PROBE22["conditional"]}  # type: ignore[misc]
    for (y, t), (pres, gt) in joint.items():
        assert pres == q[t] * conditional[(y, t)][0]
        assert gt == tuple(q[t] * value for value in conditional[(y, t)][1])


@pytest.mark.contract
@pytest.mark.parametrize("case", WEIGHT_ROUTE_CASES, ids=lambda c: c.case_id)
def test_eq_weightroute_reproduces_every_emitted_weight(case: Any) -> None:
    columns = dict(case.descended_matrix)
    slot = dict(case.slot_weights)
    q = dict(case.probe_weights)
    emitted = dict(case.emitted_weights)
    for letter, absorbing, r_min in case.bounded_letters:
        # The absorbing flag is READ OFF the frozen matrix, not asserted:
        # Eq. eq:absorbing is R^cg_{y_i|y_i} = 1, the DIAGONAL entry of the
        # bounded letter's own column.
        assert letter in columns, (case.case_id, letter)
        row_value = dict(columns[letter])[letter]
        assert (row_value == 1) is absorbing, (case.case_id, letter)
        # r_min is the minimum over the OTHER columns of THIS row.
        others = [
            dict(columns[other])[letter] for other in case.letters if other != letter
        ]
        expected = min(others) if others else F(0)
        assert expected == r_min, (case.case_id, letter)
        if not absorbing:
            # A non-absorbing bounded letter is REFUSED and emits nothing.
            assert case.refusal_reason == "bounded_letter_not_absorbing"
            assert case.emitted_weights == ()
            continue
        for setting, weight in q.items():
            value = weight * ((1 - r_min) * slot[letter] + r_min)
            assert emitted[(letter, setting)] == value, (case.case_id, letter, setting)
    if case.refusal_reason is None:
        assert case.total_weight == sum(emitted.values())
        assert case.total_weight is not None and case.total_weight < 1
        # Section 2.2: p_(y,t) = 0 for EVERY OTHER (y, t).
        bounded = {letter for letter, _, _ in case.bounded_letters}
        assert {letter for letter, _ in emitted} == bounded


@pytest.mark.contract
def test_the_empty_minimum_convention_is_exercised_exactly_once() -> None:
    """r_min := 0 when Y = {y_i}: the CONSERVATIVE value."""
    singletons = [case for case in WEIGHT_ROUTE_CASES if len(case.letters) == 1]
    assert len(singletons) == 1
    case = singletons[0]
    assert case.case_id == "RC1MIN"
    letter, absorbing, r_min = case.bounded_letters[0]
    assert absorbing is True
    assert r_min == 0
    # The un-improved bound: p_(y,t) = q_t p_i exactly.
    slot = dict(case.slot_weights)[letter]
    for setting, weight in case.probe_weights:
        assert dict(case.emitted_weights)[(letter, setting)] == weight * slot


@pytest.mark.contract
def test_cor_oneabsorbing_holds_on_the_two_letter_case() -> None:
    """R >= 2 forces EVERY r_min to vanish."""
    case = next(c for c in WEIGHT_ROUTE_CASES if c.case_id == "RC3")
    assert len(case.bounded_letters) >= 2
    assert all(absorbing for _, absorbing, _ in case.bounded_letters)
    assert all(r_min == 0 for _, _, r_min in case.bounded_letters)
    # And then the emitted weight is exactly q_t p_i, the un-improved bound.
    slot = dict(case.slot_weights)
    emitted = dict(case.emitted_weights)
    for letter, _, _ in case.bounded_letters:
        for setting, weight in case.probe_weights:
            assert emitted[(letter, setting)] == weight * slot[letter]
    # The input validation sum_i p_i <= 1 (Section 2.1, high_photon_bounds).
    assert sum(slot.values()) <= 1
    # RC2 is the ONLY case where a positive r_min occurs, and it has r = 1.
    improved = [
        c for c in WEIGHT_ROUTE_CASES if any(r > 0 for _, _, r in c.bounded_letters)
    ]
    assert [c.case_id for c in improved] == ["RC2"]
    assert len(improved[0].bounded_letters) == 1


@pytest.mark.contract
def test_the_descent_counterexample_really_fails_to_descend() -> None:
    """Remark rem:descentneedsconstant: two columns, same image, different value."""
    p = DESCENT_COUNTEREXAMPLE["dark_count_probability"]
    assert isinstance(p, Fraction)
    assert DESCENT_COUNTEREXAMPLE["p_ya_given_12"] == 1 - p + p * p
    assert DESCENT_COUNTEREXAMPLE["p_ya_given_124"] == 1
    assert (
        DESCENT_COUNTEREXAMPLE["p_ya_given_12"]
        != DESCENT_COUNTEREXAMPLE["p_ya_given_124"]
    )
    assert DESCENT_COUNTEREXAMPLE["refusal_reason"] == "dark_counts_do_not_descend"








@pytest.mark.contract
def test_the_mixture_branch_weights_are_operators_and_not_numbers() -> None:
    """thm:mixture (iii): an IDENTITY, not a constraint, unless it is a multiple."""
    pullbacks = dict(MIXTURE_CASE["branch_weight_pullbacks"])  # type: ignore[arg-type]
    total = _zeros(4)
    for operator in pullbacks.values():
        total = _madd(total, operator)
    assert total == _eye(4)
    for label, operator in pullbacks.items():
        assert _is_psd(operator), label
        # NOT a multiple of the identity, so no scalar constraint is produced.
        diagonal = {operator[i][i] for i in range(4)}
        assert len(diagonal) > 1, label
    assert MIXTURE_CASE["branch_weight_is_a_constraint"] is False
    assert MIXTURE_CASE["register_is_projective"] is False
    # The physical and target families are POVMs.
    physical = _povm_elements(MIXTURE_CASE["physical"])  # type: ignore[arg-type]
    target = _povm_elements(MIXTURE_CASE["target"])  # type: ignore[arg-type]
    assert _madd(physical[0], physical[1]) == _eye(4)
    assert _madd(target[0], target[1]) == _eye(4)


@pytest.mark.contract
def test_the_obstruction_data_are_admissible_and_the_witness_is_exact() -> None:
    """Proposition prop:obstruction: the POVM, the event bound, the witness."""
    elements = dict(PR_OBSTRUCTION.povm)
    total = _zeros(2)
    for label, element in elements.items():
        assert _is_psd(element), label
        total = _madd(total, element)
    assert total == _eye(2)
    event_sum = _zeros(2)
    for label in PR_OBSTRUCTION.event:
        event_sum = _madd(event_sum, elements[label])
    # The exact rational data from which p_* is the smaller root.
    trace = _add(event_sum[0][0], event_sum[1][1])
    assert trace == (PR_OBSTRUCTION.event_sum_trace, F(0))
    assert _det(event_sum) == (PR_OBSTRUCTION.event_sum_det, F(0))
    # The RATIONAL witness, with its exact PSD certificate.
    shifted = _msub(event_sum, _smul(PR_OBSTRUCTION.rational_witness, _eye(2)))
    assert _add(shifted[0][0], shifted[1][1]) == (
        PR_OBSTRUCTION.witness_shift_trace,
        F(0),
    )
    assert _det(shifted) == (PR_OBSTRUCTION.witness_shift_det, F(0))
    assert _is_psd(shifted)
    assert PR_OBSTRUCTION.rational_witness > 0
    # Two DISTINCT rank-one projections, which is what drives the contradiction.
    assert _det(elements["1"]) == (F(0), F(0))
    assert _det(elements["2"]) == (F(0), F(0))
    assert elements["1"] != elements["2"]


@pytest.mark.contract
def test_both_obstruction_legs_have_a_refusing_and_a_passing_instance() -> None:
    """Lemma lem:obstructions, checked as a PAIR per leg."""
    legs = {case["leg"] for case in OBSTRUCTION_CASES}
    assert legs == {"spectral inclusion", "span monotonicity"}
    refusing = [c for c in OBSTRUCTION_CASES if c["refusal_reason"] is not None]
    passing = [c for c in OBSTRUCTION_CASES if c["refusal_reason"] is None]
    assert refusing and passing
    for case in refusing:
        assert case["refusal_reason"] == "declared_relation_impossible"
    # The spectral leg's numbers: the refusing pair violates ||M_v|| <= ||F_v||,
    # the passing pair satisfies it TIGHTLY.
    spectral = {
        c["case_id"]: c for c in OBSTRUCTION_CASES if c["leg"] == "spectral inclusion"
    }
    bad = spectral["obstruction-i-refuse"]
    good = spectral["obstruction-i-pass"]
    assert bad["physical_norm"] > bad["target_norm"]
    assert good["physical_norm"] == good["target_norm"]
    for case in OBSTRUCTION_CASES:
        assert len(str(case["derivation"])) > 100, case["case_id"]
        for claim in case["claims"]:
            assert claim in CLAIM_IDS, case["case_id"]


@pytest.mark.contract
def test_the_cross_channel_pairing_is_negative_at_the_tight_end() -> None:
    """Eq. eq:crosspairing, and the reachable state it excludes."""
    weights = dict(TIGHT["weights"])  # type: ignore[arg-type]
    above = dict(TIGHT["above_cutoff"])  # type: ignore[arg-type]
    total = TIGHT["total_weight"]
    assert isinstance(total, Fraction)
    assert sum(weights.values()) == total < 1
    # Certified, and TIGHT at o: blk M^{>N}_o = p_o exactly.
    for label, weight in weights.items():
        assert above[label] >= weight
    assert above["o"] == weights["o"]
    mprime = dict(TIGHT["mprime"])  # type: ignore[arg-type]
    for label in ("o", "w"):
        assert mprime[label] == (above[label] - weights[label]) / (1 - total)
    assert sum(mprime.values()) == 1
    flag = TIGHT["ohat_flag_block"]
    assert isinstance(flag, tuple)
    own = flag[0] * above["o"] + flag[1] * above["w"]
    other = flag[0] * mprime["o"] + flag[1] * mprime["w"]
    assert own == TIGHT["pairing_with_own_channel"] == 0
    assert other == TIGHT["pairing_with_other_channel"] == F(-1, 5)
    assert other < 0
    # The excluded state IS reachable under the other channel.
    reachable = TIGHT["reachable_flag_state"]
    assert isinstance(reachable, tuple)
    assert reachable == (mprime["o"], mprime["w"])
    assert flag[0] * reachable[0] + flag[1] * reachable[1] < 0
    assert set(TIGHT["refusal_reasons"]) <= set(REFUSAL_REASONS)  # type: ignore[arg-type]


@pytest.mark.contract
def test_the_one_round_transfer_output_states_are_equal() -> None:
    """Eq. eq:sameoutput: the SAME state, not merely close ones."""
    case = TRANSFER_CASES[0]
    assert case.rounds == 1
    assert dict(case.physical_output) == dict(case.squashed_output)
    assert sum(value for _, value in case.physical_output) == 1
    assert all(value >= 0 for _, value in case.physical_output)
    # No penalty term and no error parameter is frozen anywhere for PR2.
    entry = pr_oracle("O-PR-TRANSFER")
    assert entry.value is None
    assert "epsilon" not in entry.subject


# ---------------------------------------------------------------------------
#  5. Links, chains, and the refusal-reason totality proof
# ---------------------------------------------------------------------------


@pytest.mark.contract
@pytest.mark.parametrize("link", LINK_RECORDS, ids=lambda link: link.link_id)
def test_every_link_record_fills_ten_slots_and_the_licence_rule(link: Any) -> None:
    assert link.stage in LINK_STAGES, link.link_id
    assert link.kind in LINK_KINDS_IMPLEMENTED, link.link_id
    assert link.status in LINK_STATUS_EMITTED, link.link_id
    # Slots 3 and 4 carry the SYSTEM AND THE POVM, both non-empty.
    for slot in (link.source_family, link.target):
        assert len(slot) == 2 and all(part.strip() for part in slot), link.link_id
    assert link.channel_witness.strip(), link.link_id
    assert len(link.carried_operator_pair) == 2, link.link_id
    assert link.reachable_set_statement.strip(), link.link_id
    # THE PRESENCE RULE: licence present EXACTLY WHEN the entry list is non-empty.
    assert (link.licence is not None) == bool(link.constraint_entries), link.link_id
    for _, relation, constant, certificate in link.constraint_entries:
        assert relation in ("<=", "=", ">="), link.link_id
        assert isinstance(constant, Fraction), link.link_id
        assert any(kind in certificate for kind in CERTIFICATE_KINDS), link.link_id
    assert len(link.derivation) > 100, link.link_id


@pytest.mark.contract
def test_the_six_implemented_kinds_each_have_a_link_record() -> None:
    assert {link.kind for link in LINK_RECORDS} == set(LINK_KINDS_IMPLEMENTED)
    assert len(LINK_RECORDS) == 6
    # NO record exists for a deferred kind: those are refusals, not links.
    assert {link.kind for link in LINK_RECORDS}.isdisjoint(LINK_KINDS_DEFERRED)


@pytest.mark.contract
def test_the_chain_conditions_and_the_composite_status() -> None:
    known = {link.link_id for link in LINK_RECORDS}
    for chain in CHAIN_CASES:
        for link_id in chain.links:
            assert link_id in known, (chain.case_id, link_id)
        if chain.refusal_reason is None:
            assert chain.composable and chain.tuple_chained and chain.stage_ordered
            assert chain.composite_status in LINK_STATUS_EMITTED
        else:
            assert chain.refusal_reason in REFUSAL_REASONS
        # Stage ordering, read off the frozen links: no source link may follow a
        # receiver link (Definition def:chain (C3)).
        stages = [
            next(link.stage for link in LINK_RECORDS if link.link_id == link_id)
            for link_id in chain.links
        ]
        seen_receiver = False
        for stage in stages:
            if stage == "receiver":
                seen_receiver = True
            elif seen_receiver:
                assert chain.stage_ordered is False, chain.case_id








@pytest.mark.contract
def test_the_licence_cases_cover_both_source_modes_and_both_relations() -> None:
    modes = {case.source_mode for case in LICENCE_CASES}
    assert modes == set(SOURCE_MODES)
    relations = {case.relation for case in LICENCE_CASES}
    assert relations == {">=", "="}
    for case in LICENCE_CASES:
        assert case.licence_present is True, case.case_id
        assert isinstance(case.constant, Fraction), case.case_id
        assert case.theta_typing.strip(), case.case_id
        assert "A_CList" in case.admissible_set, case.case_id
        # AT eps_op = 0 everything this module emits is >= with c = 0 or =
        # with c = q_t. Every one of these cases is MARKED superseded for
        # eps_op > 0, where cor:tolentries shifts the constant.
        assert (case.relation, case.constant) in {(">=", F(0)), ("=", F(2, 3))}
        assert case.superseded_by == "0.2.0", case.case_id
        assert case.superseded_replacement, case.case_id




# ---------------------------------------------------------------------------
#  6. Run A writes no source file
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_the_registry_is_independent_of_the_package_it_pins() -> None:
    """The registry never imports the package it pins.

    ``src/certiqs_key/reductions/`` is the package that implements this module.
    The registry was frozen before the package existed, so the check is on the
    IMPORT GRAPH and not on the package's presence or absence on disk.
    """
    # Nothing in this registry IMPORTS the package. The check is on the
    # IMPORT GRAPH and not on the text: the module docstring names the path in
    # prose, which is a statement about the repository and not a dependency.
    source = (
        Path(__file__)
        .with_name("registry_reductions.py")
        .read_text(encoding="utf-8")
    )
    imported: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported.add(node.module)
    assert not any(name.startswith("certiqs_key") for name in imported), imported
    assert imported == {"__future__", "dataclasses", "fractions", "registry"}




# ---------------------------------------------------------------------------
#  7. The 0.2.0 delta -- the declared operator tolerance (PR13)
#
#  BAND 2 OF RUN A. Every test below is about the DELTA between 0.1.3 and
#  0.2.0 and about nothing else. None of them reconstructs the module: each
#  either substitutes a frozen value into a contract equation -- Eq.
#  ``eq:psdtest`` for a decision, Eq. ``eq:etadef`` for eta_v, Eq.
#  ``eq:tolprobe`` for the probe pair -- or relates two frozen fields of the
#  same case.
# ---------------------------------------------------------------------------








@pytest.mark.contract
@pytest.mark.parametrize("case", TOL_ROW_CASES, ids=lambda case: str(case.case_id))
def test_every_tolerance_row_decision_matches_its_principal_minor_sums(
    case: Any,
) -> None:
    """Eq. eq:psdtest, applied to the frozen matrix, reproduces the decision.

    THE PREDICATE IS RECOMPUTED FROM THE FROZEN MATRIX and compared with the
    frozen ``principal_minor_sums`` and with the frozen decision. Nothing here
    calls the module; the arithmetic is the local exact one.
    """
    matrix = case.tested_matrix
    d = len(matrix)
    assert all(len(row) == d for row in matrix), case.case_id
    # The tested matrix is Hermitian -- Lemma lem:exactpsd (i)'s hypothesis.
    assert _is_hermitian(matrix), case.case_id
    # e_k(X) = the sum of the k x k PRINCIPAL minors, recomputed by brute force
    # over every principal submatrix. That is the definition Eq. eq:charpoly
    # gives and the one rem:psdalgorithm calls "never necessary" for a solver
    # and perfectly adequate for a two-by-two check.
    sums = []
    for k in range(1, d + 1):
        total = (Fraction(0), Fraction(0))
        for idx in combinations(range(d), k):
            sub = tuple(tuple(matrix[i][j] for j in idx) for i in idx)
            total = _add(total, _det(sub))
        sums.append(total)
    # Every e_k is REAL: a principal minor of a Hermitian matrix is real.
    for value in sums:
        assert value[1] == 0, case.case_id
    assert tuple(value[0] for value in sums) == case.principal_minor_sums, case.case_id
    # Eq. eq:psdtest: X >= 0 iff EVERY e_k >= 0.
    decided = all(value[0] >= 0 for value in sums)
    assert decided is case.admitted, case.case_id
    # And the independent PSD routine agrees, so the two ways of deciding the
    # same predicate cannot drift.
    assert _is_psd(matrix) is case.admitted, case.case_id
    # A refusal names a reason and an admit does not.
    if case.admitted:
        assert case.reason == "", case.case_id
    else:
        assert case.reason in REFUSAL_REASONS_0_2_0, case.case_id
    assert case.labels, case.case_id
    assert case.derivation.strip(), case.case_id
    assert case.claims == ("PR13",), case.case_id


@pytest.mark.contract
def test_the_tolerance_rows_pair_an_admit_with_a_refusal_at_zero() -> None:
    """The tolerance is LOAD-BEARING: the same declaration flips at eps_op = 0."""
    by_id = {case.case_id: case for case in TOL_ROW_CASES}
    pairs = (
        ("TOL2-herm-y0t0-admit", "TOL2-herm-y0t0-refuse-at-zero"),
        ("TOL2-negpart-y0t0-admit", "TOL2-negpart-y0t0-refuse-at-zero"),
    )
    for admit_id, refuse_id in pairs:
        admit, refuse = by_id[admit_id], by_id[refuse_id]
        assert admit.eps_op == TOL2_EPS_OP and admit.admitted is True
        assert refuse.eps_op == 0 and refuse.admitted is False
        assert refuse.reason == "declaration_outside_tolerance"
    # THE TWO DISCRIMINATORS AGAINST THE TESTS AN IMPLEMENTATION SUBSTITUTES.
    # (a) e_1 alone is not enough: a case where e_1 >= 0 and the matrix is not.
    trace_trap = by_id["TOL-posdef-refuse-e1-passes"]
    assert trace_trap.principal_minor_sums[0] >= 0
    assert trace_trap.principal_minor_sums[-1] < 0
    assert trace_trap.admitted is False
    # (b) The LEADING principal minors are not enough either: both are 0 here
    # and e_1 < 0. Sylvester's criterion is for positive DEFINITENESS.
    sylvester = by_id["TOL-posdef-refuse-leading-minors-pass"]
    matrix = sylvester.tested_matrix
    leading = [
        _det(tuple(tuple(matrix[i][j] for j in range(k)) for i in range(k)))
        for k in range(1, len(matrix) + 1)
    ]
    assert all(value[0] >= 0 for value in leading)
    assert sylvester.principal_minor_sums[0] < 0
    assert sylvester.admitted is False
    # (c) The boundary belongs to the ACCEPTING side: Eq. eq:normtest and
    # Eq. eq:psdtest are both non-strict, so W = 0 admits.
    boundary = by_id["TOL-threshold-form-boundary-admit"]
    assert all(value == 0 for value in boundary.principal_minor_sums)
    assert boundary.admitted is True


@pytest.mark.contract
def test_the_float_sensitive_cases_are_named_and_resolve() -> None:
    """Section 2.5: NO row is decided by a floating-point comparison."""
    ids = {case.case_id for case in TOL_ROW_CASES}
    assert len(TOL_FLOAT_SENSITIVE_CASES) == 2
    for case_id, exact_note, admitted, float_note in TOL_FLOAT_SENSITIVE_CASES:
        assert case_id in ids, case_id
        case = next(c for c in TOL_ROW_CASES if c.case_id == case_id)
        assert case.admitted is admitted, case_id
        assert len(exact_note) > 60 and len(float_note) > 200, case_id

    # THE WHOLE FIXTURE IS NON-DYADIC, so the hazard is present before any
    # comparison: a Fraction is dyadic iff its denominator is a power of two.
    def dyadic(value: Fraction) -> bool:
        d = value.denominator
        return d & (d - 1) == 0

    assert not dyadic(TOL2_EPS_OP)
    assert not dyadic(TOL2_DCF)
    assert not dyadic(TOL2_ETA)
    for _, eta in TOL2_ETA_V:
        assert not dyadic(eta)
    for _, delta in TOL2_DELTA_T:
        assert not dyadic(delta)


@pytest.mark.contract
def test_eq_etadef_and_eq_dcf_reproduce_every_frozen_defect() -> None:
    """Dcf from the frozen R^cg, and eta_v = q_t dcf eps_op, recomputed."""
    # Eq. eq:dcf: dcf = max_y sum_y' R^cg_{y|y'}, computed on the frozen matrix.
    row_sums = [sum(entry[0] for entry in row) for row in TOL2_RCG]
    assert max(row_sums) == TOL2_DCF
    # 1 <= dcf <= |Y|, which Lemma lem:tolprop derives from column stochasticity.
    assert 1 <= TOL2_DCF <= len(TOL2_Y)
    # R^cg IS column stochastic and absorbing at the bounded letter y0.
    for j in range(len(TOL2_RCG)):
        assert sum(TOL2_RCG[i][j][0] for i in range(len(TOL2_RCG))) == 1
    assert TOL2_RCG[0][0] == (Fraction(1), Fraction(0))
    # Eq. eq:etadef, outcome by outcome, in the declared order of V.
    q = dict(TOL2_Q)
    for (_, setting), eta in TOL2_ETA_V:
        assert eta == q[setting] * TOL2_DCF * TOL2_EPS_OP
    assert TOL2_ETA == TOL2_DCF * TOL2_EPS_OP
    assert max(eta for _, eta in TOL2_ETA_V) <= TOL2_ETA
    # Cor. cor:tolentries (ii): delta_t = |Y| q_t dcf eps_op = |Y| eta_(y,t).
    eta_by_setting = {setting: eta for (_, setting), eta in TOL2_ETA_V}
    for setting, delta in TOL2_DELTA_T:
        assert delta == len(TOL2_Y) * eta_by_setting[setting]
    # eta_v depends on t ALONE, since dcf and eps_op are common to every v.
    assert eta_by_setting["t0"] == 2 * eta_by_setting["t1"]


@pytest.mark.contract
def test_the_declared_blocks_and_the_post_processed_family_agree() -> None:
    """Section 2.2 steps 1-2, recomputed from the frozen declared blocks."""
    blocks = dict(TOL2_BLOCKS)
    tilde = dict(TOL2_TILDE)
    joint = dict(TOL2_JOINT_NB)
    q = dict(TOL2_Q)
    for i, y in enumerate(TOL2_Y):
        for t in TOL2_T:
            # Step 1: M~_{y|t} = sum_y' R^cg_{y|y'} M_{y'|t}.
            acc = _zeros(2)
            for j, y2 in enumerate(TOL2_Y):
                acc = _madd(acc, _smul(TOL2_RCG[i][j][0], blocks[(y2, t)]))
            assert acc == tilde[(y, t)], (y, t)
            # Step 2: M_(y,t)|nb = q_t M~_{y|t}.
            assert _smul(q[t], acc) == joint[(y, t)], (y, t)
    # At t1 the declared family is EXACTLY a POVM: one declaration with one
    # setting that needs the tolerance and one that does not.
    assert _madd(blocks[("y0", "t1")], blocks[("y1", "t1")]) == _eye(2)
    assert _madd(blocks[("y0", "t0")], blocks[("y1", "t0")]) != _eye(2)


@pytest.mark.contract
@pytest.mark.parametrize("case", TOL_ENTRY_CASES, ids=lambda case: str(case.case_id))
def test_every_shifted_constant_is_weaker_than_its_zero_tolerance_one(
    case: Any,
) -> None:
    """Cor. cor:tolentries: the emitted set never SHRINKS at a positive tolerance.

    Section 2.3 states the hazard in the other direction: "EMITTING A 0.1.3
    CONSTANT AT eps_op > 0 IS UNSAFE -- it would restrict A_CList MORE TIGHTLY
    than eq:certificate licenses". The invariant is therefore that a ``>=``
    entry's constant never RISES and a ``<=`` entry's never FALLS.
    """
    assert case.eps_op == TOL2_EPS_OP, case.case_id
    assert case.labels and case.derivation.strip(), case.case_id
    assert all(claim in CLAIM_IDS for claim in case.claims), case.case_id
    for relation, constant in case.at_zero + case.at_positive:
        assert relation in {">=", "<=", "="}, case.case_id
        assert isinstance(constant, Fraction), case.case_id
    # An EQUALITY at eps_op = 0 becomes a two-sided PAIR; everything else keeps
    # its relation and its arity.
    if any(relation == "=" for relation, _ in case.at_zero):
        assert len(case.at_zero) == 1
        assert len(case.at_positive) == 2
        assert {relation for relation, _ in case.at_positive} == {">=", "<="}
        centre = case.at_zero[0][1]
        low = next(c for r, c in case.at_positive if r == ">=")
        high = next(c for r, c in case.at_positive if r == "<=")
        # The pair BRACKETS the equality symmetrically, at +- delta_t.
        assert low < centre < high, case.case_id
        assert centre - low == high - centre, case.case_id
        assert centre - low in {delta for _, delta in TOL2_DELTA_T}, case.case_id
    else:
        assert len(case.at_zero) == len(case.at_positive) == 1
        (rel0, c0), (rel1, c1) = case.at_zero[0], case.at_positive[0]
        assert rel0 == rel1, case.case_id
        if rel0 == ">=":
            assert c1 <= c0, case.case_id
        else:
            assert c1 >= c0, case.case_id


@pytest.mark.contract
def test_the_shifted_constants_are_the_eta_the_contract_names() -> None:
    """Each shift is the exact quantity cor:tolentries (i)-(iv) gives."""
    eta = dict(TOL2_ETA_V)
    # (i) the flag-sector entry at o = (y0, t0): -eta_o.
    assert TOL_ENTRY_FLAG.at_positive == ((">=", -eta[("y0", "t0")]),)
    assert TOL_ENTRY_FLAG.at_zero == ((">=", Fraction(0)),)
    # (ii) the probe pair at q_t -+ delta_t, both settings.
    delta = dict(TOL2_DELTA_T)
    q = dict(TOL2_Q)
    for case, setting in (
        (TOL_ENTRY_PROBE_T0, "t0"),
        (TOL_ENTRY_PROBE_T1, "t1"),
    ):
        assert case.at_zero == (("=", q[setting]),)
        assert case.at_positive == (
            (">=", q[setting] - delta[setting]),
            ("<=", q[setting] + delta[setting]),
        )
    # (iii) the default carried operators: UNCHANGED, the one family a positive
    # tolerance leaves alone.
    assert TOL_ENTRY_DEFAULT_CARRIED.at_zero == TOL_ENTRY_DEFAULT_CARRIED.at_positive
    assert TOL_ENTRY_DEFAULT_CARRIED.at_positive == ((">=", Fraction(0)),)
    # (iv) eq:two-sector-entry: delta(O^) = eta_e with alpha_e = 1, so -eta_e.
    assert TOL_ENTRY_TWO_SECTOR.at_positive == ((">=", -eta[("y0", "t0")]),)
    # cor:tolentries closes by asserting the four clauses are EXHAUSTIVE.
    assert len(TOL_ENTRY_CLAUSES) == 4
    # FIVE cases over FOUR clauses: clause (ii) is frozen at both settings,
    # which is what makes the t-dependence of delta_t observable.
    clauses = {case.clause.split(" -- ")[0] for case in TOL_ENTRY_CASES}
    assert clauses == {c.split(" -- ")[0] for c in TOL_ENTRY_CLAUSES}
    assert len(clauses) == 4
    assert len(TOL_ENTRY_CASES) == 5
    # A requested operator OUTSIDE eq:tolgeneral's form is REFUSED, not emitted
    # at some other constant.
    assert TOL_ENTRY_OUTSIDE_FORM["emitted"] is False
    assert TOL_ENTRY_OUTSIDE_FORM["reason"] == "constraint_without_certificate"


@pytest.mark.contract
def test_the_tolerance_record_is_null_exactly_when_the_tolerance_is_absent() -> None:
    """Section 2.3's presence rule, as a biconditional over both frozen cases."""
    present, absent = TOL2_TOLERANCE_RECORD, TOL2_TOLERANCE_RECORD_ABSENT
    assert present["present"] is True
    assert Fraction(str(present["operator_tolerance"])) > 0
    assert absent["present"] is False
    assert absent["operator_tolerance"] == 0
    assert absent["record"] is None
    # The record's numbers ARE the ones eq:dcf and eq:etadef give.
    assert present["operator_tolerance"] == TOL2_EPS_OP
    assert present["dark_count_factor"] == TOL2_DCF
    assert tuple(cast("tuple[Any, ...]", present["eta_v"])) == TOL2_ETA_V
    assert present["norm"] == "operator norm"
    assert present["carries_thm_tolerance_i_ii"] is True
    # THE PER-ENTRY SHIFT covers every emitted entry and resolves to a case.
    shifts = dict(cast("tuple[tuple[str, Fraction], ...]", present["per_entry_shift"]))
    assert set(shifts) == {case.case_id for case in TOL_ENTRY_CASES}
    by_id = {case.case_id: case for case in TOL_ENTRY_CASES}
    for case_id, shift in shifts.items():
        case = by_id[case_id]
        if case_id.startswith("TOL2-entry-probe"):
            # The probe shift is the delta the pair is built around.
            assert shift in {delta for _, delta in TOL2_DELTA_T}
        else:
            # Every other shift is the signed constant the entry carries.
            assert shift == case.at_positive[0][1]
    # eq:targetposcomp's three amounts, recomputed from the declared scalars.
    amounts = TOL2_TARGETPOSCOMP
    eta_v = dict(TOL2_ETA_V)[("y0", "t0")]
    assert amounts["negative_part"] == eta_v
    assert amounts["hermiticity_defect"] == 2 * eta_v
    assert amounts["completeness_defect"] == len(TOL2_Y) * TOL2_DCF * TOL2_EPS_OP
    # The completeness amount is v-INDEPENDENT while the other two are not.
    assert amounts["completeness_defect"] != amounts["hermiticity_defect"]


@pytest.mark.contract
@pytest.mark.parametrize("case", TOL_SCOPE_CASES, ids=lambda case: str(case.case_id))
def test_the_tolerance_reaches_the_receiver_blocks_and_no_other_family(
    case: Any,
) -> None:
    """Assumption A-OPTOL (a) vs (b), as an admit and two refusals."""
    assert case.derivation.strip() and case.labels, case.case_id
    # A family is decided IDENTICALLY at every eps_op EXACTLY when it is NOT
    # covered by the tolerance -- which is the whole content of clause (b).
    assert case.decided_at_every_eps_op is not case.covered_by_tolerance
    if case.covered_by_tolerance:
        assert case.admitted is True and case.reason == "", case.case_id
    else:
        assert case.admitted is False, case.case_id
        assert case.reason == "blinding_model_ill_formed", case.case_id
    assert case.reason == "" or case.reason in REFUSAL_REASONS_0_2_0




@pytest.mark.contract
@pytest.mark.parametrize(
    "case", BRANCH_PROBE_WEIGHT_CASES, ids=lambda case: str(case.case_id)
)
def test_eq_branchprobeweight_decides_the_probe_certificate_at_every_eps_op(
    case: Any,
) -> None:
    """The F-5-01 narrowing: the condition, recomputed from the frozen branch."""
    assert case.derivation.strip() and case.labels, case.case_id
    # DECIDED IDENTICALLY AT EVERY eps_op, because a declared branch of the
    # frozen branch model is exact declared data outside the tolerance
    # (A-OPTOL (b)).
    assert set(case.decided_identically_at) == {Fraction(0), TOL2_EPS_OP}
    q = dict(TOL2_Q)
    branch = case.branch
    if branch is None:
        assert case.certificate_discharged is False, case.case_id
        assert case.reason == "constraint_without_certificate", case.case_id
        return
    elements: dict[tuple[str, str], Matrix] = dict(branch)
    # The branch is a POVM iff its elements are PSD and sum to the identity.
    total = _zeros(2)
    for matrix in elements.values():
        assert _is_hermitian(matrix) and _is_psd(matrix), case.case_id
        total = _madd(total, matrix)
    assert (total == _eye(2)) is case.branch_is_exact_povm, case.case_id
    # Eq. eq:branchprobeweight: sum_y M_((y,t)|b) = q_t 1_C for every t.
    holds = True
    for t in TOL2_T:
        acc = _zeros(2)
        for y in TOL2_Y:
            acc = _madd(acc, elements[(y, t)])
        assert acc == dict(case.per_setting_sums)[t], (case.case_id, t)
        if acc != _smul(q[t], _eye(2)):
            holds = False
    assert holds is case.satisfies_branchprobeweight, case.case_id
    assert case.certificate_discharged is (
        case.branch_is_exact_povm and case.satisfies_branchprobeweight
    ), case.case_id
    if not case.certificate_discharged:
        assert case.reason == "constraint_without_certificate", case.case_id


@pytest.mark.contract
def test_the_two_branch_conditions_are_independent() -> None:
    """An EXACT POVM that violates eq:branchprobeweight: the discriminating case."""
    by_id = {case.case_id: case for case in BRANCH_PROBE_WEIGHT_CASES}
    fail = by_id["TOL2-branchprobe-fail-exact-povm"]
    assert fail.branch_is_exact_povm is True
    assert fail.satisfies_branchprobeweight is False
    # So `blinding_model_ill_formed` does NOT fire and the certificate row does.
    assert fail.reason == "constraint_without_certificate"
    assert fail.reason != "blinding_model_ill_formed"
    # The pass case has a branch that is NOT block diagonal at the cutoff, which
    # the frozen branch model permits and which the condition is indifferent to.
    good = by_id["TOL2-branchprobe-pass"]
    assert good.branch is not None
    element = dict(good.branch)[("y0", "t0")]
    assert element[0][1] != (Fraction(0), Fraction(0))
    assert good.certificate_discharged is True
    # All three failure modes Section 4.13 lists are frozen, under ONE reason.
    reasons = {c.reason for c in BRANCH_PROBE_WEIGHT_CASES if c.reason}
    assert reasons == {"constraint_without_certificate"}
    assert len(BRANCH_PROBE_WEIGHT_CASES) == 3


@pytest.mark.contract
@pytest.mark.parametrize(
    "case", SLOT_VALIDATION_CASES, ids=lambda case: str(case.case_id)
)
def test_the_slot_row_is_not_the_total_weight_row(case: Any) -> None:
    """F-4-08: eq:weightroute recomputed, and the two rows decided separately."""
    q = dict(TOL2_Q)
    r_min = dict(case.r_min)
    routed = dict(case.routed_weights)
    bounded = {letter for letter, _ in case.slot}
    for letter, p_i in case.slot:
        factor = (1 - r_min[letter]) * p_i + r_min[letter]
        for t in TOL2_T:
            assert routed[(letter, t)] == q[t] * factor, (case.case_id, letter, t)
    for (letter, _), weight in routed.items():
        if letter not in bounded:
            assert weight == 0, case.case_id
    assert sum(routed.values()) == case.routed_total, case.case_id
    # The SLOT row: p_i >= 0 for every i and sum_i p_i <= 1.
    slot_ok = all(p >= 0 for _, p in case.slot) and sum(p for _, p in case.slot) <= 1
    assert slot_ok is case.slot_row_admits, case.case_id
    # The TOTAL-WEIGHT row: every routed p_v >= 0 and p < 1.
    total_ok = all(w >= 0 for w in routed.values()) and case.routed_total < 1
    assert total_ok is case.total_weight_row_admits, case.case_id
    if not case.slot_row_admits:
        assert case.reason == "high_photon_slot_ill_formed", case.case_id
    assert case.labels and case.derivation.strip(), case.case_id


@pytest.mark.contract
def test_a_negative_slot_weight_is_masked_in_the_routed_total() -> None:
    """The case the new row exists for, and the direction it is refused in."""
    by_id = {case.case_id: case for case in SLOT_VALIDATION_CASES}
    masked = by_id["TOL2-slot-negative-masked"]
    # The two rows DISAGREE: the routed total admits and the slot does not.
    assert masked.total_weight_row_admits is True
    assert masked.slot_row_admits is False
    # And they disagree in SIGN, so no test on the routed weights recovers it.
    assert sum(p for _, p in masked.slot) < 0 < masked.routed_total
    # Only possible where r_min > 0, which cor:oneabsorbing confines to r = 1.
    assert len(masked.slot) == 1
    assert all(value > 0 for _, value in masked.r_min)
    # THE DIRECTION: the routed bound at p_i < 0 is WEAKER than at p_i = 0.
    well = by_id["TOL2-slot-wellformed"]
    r = dict(masked.r_min)["y0"]
    at_zero_p = (1 - r) * Fraction(0) + r
    at_negative = (1 - r) * dict(masked.slot)["y0"] + r
    assert at_negative < at_zero_p
    # At r >= 2 every r_min is 0 and the two rows agree, as cor:oneabsorbing says.
    two = by_id["TOL2-slot-sum-exceeds-one"]
    assert len(two.slot) == 2
    assert all(value == 0 for _, value in two.r_min)
    assert two.routed_total == sum(p for _, p in two.slot)
    assert two.slot_row_admits is two.total_weight_row_admits is False
    # The well-formed case routes to a SHARPENED weight, from R^cg and not optics.
    assert well.routed_total > 0
    assert dict(well.routed_weights)[("y0", "t0")] > dict(well.slot)["y0"] * Fraction(
        2, 3
    )








@pytest.mark.contract
def test_every_supersession_names_a_site_and_a_replacement() -> None:
    """The marks are complete, resolvable, and never a deletion."""
    module = __import__("registry_reductions")
    for record in SUPERSESSIONS:
        assert record.superseded_by == "0.2.0", record.symbol
        assert record.contract_site.strip(), record.symbol
        assert record.replacement, record.symbol
        assert record.note.strip(), record.symbol
        assert record.kind.strip(), record.symbol
        # THE MARKED SYMBOL STILL EXISTS: marking is not deletion.
        assert hasattr(module, record.symbol), record.symbol
        # And every replacement resolves -- either to a module symbol or to a
        # case id frozen in one of the band-2 case tuples.
        known_case_ids = {
            case.case_id
            for group in (
                TOL_ROW_CASES,
                TOL_ENTRY_CASES,
                TOL_SCOPE_CASES,
                BRANCH_PROBE_WEIGHT_CASES,
                SLOT_VALIDATION_CASES,
            )
            for case in group
        }
        for name in record.replacement:
            assert hasattr(module, name) or name in known_case_ids, (
                record.symbol,
                name,
            )
    # Twelve marked symbols, each named once.
    assert len(SUPERSESSIONS) == 12
    assert len(SUPERSEDED_SYMBOLS) == 12
    assert len(set(SUPERSEDED_SYMBOLS)) == 12
    # The DATACLASS marks and the table agree: every instance carrying a
    # `superseded_by` is named in the table, and vice versa for those symbols.
    marked_instances = {
        case.case_id
        for group in (LICENCE_CASES, CERTIFICATE_CASES, REFUSAL_CASES)
        for case in group
        if getattr(case, "superseded_by", None)
    }
    table_case_ids = {record.case_id for record in SUPERSESSIONS}
    assert marked_instances <= table_case_ids
    assert len(marked_instances) == 6
    for case_id in marked_instances:
        record = next(r for r in SUPERSESSIONS if r.case_id == case_id)
        assert record.superseded_by == "0.2.0"
    # WHAT IS NOT MARKED is recorded with its reason, so the complement of the
    # list is stated rather than left to be inferred.
    assert len(NOT_SUPERSEDED_AND_WHY) == 5
    for symbol, reason in NOT_SUPERSEDED_AND_WHY:
        assert symbol.strip() and len(reason) > 80, symbol
        assert symbol not in SUPERSEDED_SYMBOLS, symbol


@pytest.mark.contract
def test_a_constant_supersession_still_holds_at_zero_tolerance() -> None:
    """Supersession here means NARROWED IN SCOPE, not wrong -- except once."""
    by_symbol = {record.symbol: record for record in SUPERSESSIONS}
    # The four CONSTANT marks and the READING mark all stand at eps_op = 0:
    # "At eps_op = 0 every eta_v vanishes, EACH SHIFTED CONSTANT IS THE 0.1.3
    # CONSTANT" (cor:tolentries).
    for symbol in (
        "LICENCE_TRUSTED",
        "LICENCE_UNTRUSTED",
        "LICENCE_PROBE_IDENTITY",
        "CERT_TWO_SECTOR",
        "CERT_IDENTITY_PROBE",
        "ENCODED_CONSTRAINT",
    ):
        assert by_symbol[symbol].still_valid_at_zero_tolerance is True, symbol
    # The VOCABULARY marks and the one INPUT-SHAPE mark do not: they are about
    # the contract's lists and about a datum that no longer type-checks.
    for symbol in (
        "INPUT_KEYS",
        "OUTPUT_KEYS",
        "REFUSAL_REASONS",
        "CONVENTIONS",
        "ASSUMPTION_LEDGER",
        "REFUSAL_CASES",
    ):
        assert by_symbol[symbol].still_valid_at_zero_tolerance is False, symbol
    # And the frozen constants really are the eps_op = 0 ones: each superseded
    # licence constant equals the `at_zero` constant of its replacement.
    replacements = {case.case_id: case for case in TOL_ENTRY_CASES}
    flag = replacements["TOL2-entry-flag-sector"]
    assert LICENCE_TRUSTED.constant == flag.at_zero[0][1]
    assert LICENCE_UNTRUSTED.constant == flag.at_zero[0][1]
    two_sector = replacements["TOL2-entry-two-sector"]
    assert CERT_TWO_SECTOR.constant == two_sector.at_zero[0][1]
    probe = replacements["TOL2-entry-probe-t0"]
    assert LICENCE_PROBE_IDENTITY.constant == probe.at_zero[0][1]




# ---------------------------------------------------------------------------
#  7. Group PR-P -- the column-stochasticity row of contract 0.3.0
# ---------------------------------------------------------------------------
#
#  Every check here either recomputes one of the row's two predicates from the
#  frozen raw matrix, or relates two frozen fields of the same case. Nothing
#  validates a declaration, and nothing imports the implementation.


@pytest.mark.contract
@pytest.mark.parametrize("case", COLSTOCH_CASES, ids=lambda c: c.case_id)
def test_the_column_stochasticity_predicates_decide_every_case(case: Any) -> None:
    """The row's TWO subrules, recomputed exactly from the frozen raw matrix.

    ``sec:failclosed``: R is column-stochastic when ``R_{S|S'} >= 0`` for every
    entry AND ``sum_S R_{S|S'} = 1`` for every column. The row is the
    CONJUNCTION, so a case admits exactly when both hold.
    """
    entries = [value for _, column in case.raw_matrix for _, value in column]
    for value in entries:
        assert isinstance(value, Fraction), case.case_id
    # Every column carries an entry for every pattern, in the declared order.
    assert tuple(name for name, _ in case.raw_matrix) == case.patterns
    for _, column in case.raw_matrix:
        assert tuple(name for name, _ in column) == case.patterns
    # SUBRULE 1: non-negativity, decided by a sign comparison.
    assert min(entries) == case.min_entry, case.case_id
    assert (case.min_entry >= 0) is case.non_negative, case.case_id
    # SUBRULE 2: unit columns, decided by an equality on exact rationals.
    sums = tuple(
        (name, sum((value for _, value in column), Fraction(0)))
        for name, column in case.raw_matrix
    )
    assert sums == case.column_sums, case.case_id
    assert all(total == 1 for _, total in sums) is case.unit_columns, case.case_id
    # THE ROW IS THE CONJUNCTION.
    assert case.column_stochastic_row_admits is (
        case.non_negative and case.unit_columns
    ), case.case_id
    # And the frozen reason is the row's own string exactly when it refuses.
    if not case.column_stochastic_row_admits:
        assert case.reason == "dark_counts_not_column_stochastic", case.case_id


@pytest.mark.contract
@pytest.mark.parametrize("case", COLSTOCH_CASES, ids=lambda c: c.case_id)
def test_the_monotonicity_implication_is_exactly_what_it_says(case: Any) -> None:
    """``R_{S|S'} > 0 => S' subset S`` -- "that exact implication and nothing more".

    The whole boundary between the two rows lives in the STRICT inequality: a
    NEGATIVE entry in a forbidden position satisfies the implication vacuously.
    """
    subsets = {
        "e": frozenset(),
        "1": frozenset("1"),
        "2": frozenset("2"),
        "12": frozenset("12"),
    }
    monotone = True
    for column_name, column in case.raw_matrix:
        source = subsets[column_name]
        for row_name, value in column:
            target = subsets[row_name]
            if value > 0 and not source <= target:
                monotone = False
    assert monotone is case.monotone, case.case_id
    # The descent row is monotone AND descends, under ONE reason string.
    assert case.descent_row_admits is (case.monotone and case.descends), case.case_id
    if not case.descent_row_admits:
        assert case.reason == "dark_counts_do_not_descend", case.case_id


@pytest.mark.contract
def test_the_two_dark_count_rows_do_not_cover_each_other() -> None:
    """Remark rem:darkcompose, made checkable in both directions.

    "A strictly positive entry in a (D2)-forbidden position fails monotonicity
    while leaving column-stochasticity untouched, and a NEGATIVE entry in such
    a position does the reverse -- it satisfies the monotonicity implication
    VACUOUSLY and fails non-negativity."
    """
    by_id = {case.case_id: case for case in COLSTOCH_CASES}
    negative = by_id["CS-negative-vacuous-refuse"]
    positive = by_id["CS-positive-forbidden-refuse"]
    # DIRECTION ONE: the new row refuses, the descent row admits.
    assert negative.column_stochastic_row_admits is False
    assert negative.non_negative is False
    assert negative.unit_columns is True
    assert negative.monotone is True
    assert negative.descent_row_admits is True
    assert negative.reason == "dark_counts_not_column_stochastic"
    # DIRECTION TWO: the new row admits, the descent row refuses.
    assert positive.column_stochastic_row_admits is True
    assert positive.non_negative is True
    assert positive.unit_columns is True
    assert positive.monotone is False
    assert positive.descent_row_admits is False
    assert positive.reason == "dark_counts_do_not_descend"
    # THE TWO ARE A MIRROR PAIR: they differ from the anchor in the SAME cell
    # of the SAME column, by entries of opposite sign, and in nothing else.
    anchor = by_id["CS-canonical-admit"]

    def cell(case: Any, column: str, row: str) -> Fraction:
        entries: dict[str, Fraction] = dict(dict(case.raw_matrix)[column])
        return entries[row]

    assert cell(anchor, "1", "e") == Fraction(0)
    assert cell(negative, "1", "e") == Fraction(-1, 20)
    assert cell(positive, "1", "e") == Fraction(1, 20)
    # The position IS (D2)-forbidden: {1} is not a subset of the empty set.
    assert not frozenset("1") <= frozenset()
    # And every OTHER column is the anchor's, byte for byte.
    for name in ("e", "2", "12"):
        assert dict(negative.raw_matrix)[name] == dict(anchor.raw_matrix)[name]
        assert dict(positive.raw_matrix)[name] == dict(anchor.raw_matrix)[name]




@pytest.mark.contract
def test_one_case_has_a_fibre_of_size_two() -> None:
    """The descent implication must be checked where it is not a relabelling.

    Under the canonical coarse-graining at K = 2 the multiclick set is a single
    pattern, so cg is a BIJECTION and "sum over the fibre" is a sum of one
    term. CS-coarse-admit merges the two single-click patterns, so the
    descended entry is a genuine sum.
    """
    by_id = {case.case_id: case for case in COLSTOCH_CASES}
    merging = by_id["CS-coarse-admit"]
    cg = dict(merging.coarse_graining)
    fibres = {letter: [p for p in cg if cg[p] == letter] for letter in set(cg.values())}
    assert sorted(len(f) for f in fibres.values()) == [1, 1, 2]
    # The size-two fibre's descended entry really is the SUM of two entries.
    empty_column = dict(dict(merging.raw_matrix)["e"])
    descended_empty = dict(dict(merging.descended_matrix)["y_0"])
    assert descended_empty["y_d"] == empty_column["1"] + empty_column["2"]
    assert descended_empty["y_d"] == Fraction(8, 25)
    assert empty_column["1"] == empty_column["2"] == Fraction(4, 25)
    # Every other case uses the canonical bijection, where it IS a relabelling.
    for case in COLSTOCH_CASES:
        if case.case_id == "CS-coarse-admit":
            continue
        sizes: dict[str, list[str]] = {}
        mapping = dict(case.coarse_graining)
        for pattern, letter in mapping.items():
            sizes.setdefault(letter, []).append(pattern)
        assert all(len(v) == 1 for v in sizes.values()), case.case_id


@pytest.mark.contract
@pytest.mark.parametrize("case", COLSTOCH_CASES, ids=lambda c: c.case_id)
def test_no_other_row_catches_what_the_new_row_catches(case: Any) -> None:
    """Eq. eq:weightroute on every case, so a refusal is attributable.

    Remark rem:colstoch names the ONE indirect path a column-sum defect could
    have taken at 0.2.0 that is decidable from R alone: "any ``r_min,i >= 1``
    makes the i-th summand at least 1 and hence ``p >= 1``... either way
    ``total_weight_not_below_one``". Every case here has ``r_min < 1`` and a
    routed total in ``[0, 1)``, so that path does NOT fire and the refusals are
    the rows the cases name.
    """
    descended = dict(case.descended_matrix)
    letters = tuple(name for name, _ in case.descended_matrix)
    row_of_bounded = {
        letter: dict(descended[letter])[case.bounded_letter] for letter in letters
    }
    # ABSORBING at the bounded letter (Eq. eq:absorbing).
    assert (row_of_bounded[case.bounded_letter] == 1) is case.absorbing, case.case_id
    # r_min,i is the minimum over the columns OTHER than the bounded letter.
    others = [row_of_bounded[y] for y in letters if y != case.bounded_letter]
    assert min(others) == case.r_min, case.case_id
    assert case.r_min < 1, case.case_id
    # Eq. eq:weightroute, and the total-weight row's verdict on the result.
    routed = (1 - case.r_min) * COLSTOCH_SLOT_WEIGHT + case.r_min
    weights = [q * routed for _, q in COLSTOCH_PROBE_WEIGHTS]
    total = sum(weights, Fraction(0))
    assert total == routed == case.routed_total, case.case_id
    assert (all(w >= 0 for w in weights) and total < 1) is (
        case.total_weight_row_admits
    ), case.case_id
    assert case.total_weight_row_admits is True, case.case_id
    # The probe weights are a distribution, so the routed total IS the routed
    # weight -- which is why the two are asserted equal above.
    assert sum((q for _, q in COLSTOCH_PROBE_WEIGHTS), Fraction(0)) == 1


@pytest.mark.contract
def test_the_anchor_reproduces_the_band_one_weight_route() -> None:
    """The regression anchor: 0.3.0 refuses strictly more and never less.

    CS-canonical-admit is RC2's declaration read one level lower -- the RAW R
    over ``2^[K]`` rather than the descended matrix group PR-M froze -- and
    under the canonical coarse-graining at K = 2 the two agree entry for entry.
    Every number RC2 pins is reproduced.
    """
    anchor = next(c for c in COLSTOCH_CASES if c.case_id == "CS-canonical-admit")
    rc2 = next(c for c in WEIGHT_ROUTE_CASES if c.case_id == "RC2")
    assert anchor.descended_matrix == rc2.descended_matrix
    assert anchor.r_min == rc2.bounded_letters[0][2] == Fraction(1, 20)
    assert anchor.bounded_letter == rc2.bounded_letters[0][0] == "y_mc"
    assert anchor.absorbing is rc2.bounded_letters[0][1] is True
    assert anchor.routed_total == rc2.total_weight == Fraction(29, 200)
    assert COLSTOCH_SLOT_WEIGHT == rc2.slot_weights[0][1] == Fraction(1, 10)
    assert rc2.probe_weights == COLSTOCH_PROBE_WEIGHTS
    # AND IT IS ADMITTED BY EVERY ROW THE GROUP EXERCISES, which is what makes
    # it a regression anchor rather than another discriminator.
    assert anchor.column_stochastic_row_admits is True
    assert anchor.descent_row_admits is True
    assert anchor.total_weight_row_admits is True
    assert anchor.reason == ""






@pytest.mark.contract
def test_every_0_3_0_supersession_names_a_site_and_a_replacement() -> None:
    """The 0.3.0 marks are complete, resolvable, and never a deletion."""
    module = __import__("registry_reductions")
    for record in SUPERSESSIONS_0_3_0:
        assert record.superseded_by == "0.3.0", record.symbol
        assert record.contract_site.strip(), record.symbol
        assert record.replacement, record.symbol
        assert record.note.strip(), record.symbol
        assert record.kind.strip(), record.symbol
        assert hasattr(module, record.symbol), record.symbol
        for name in record.replacement:
            assert hasattr(module, name), (record.symbol, name)
    assert len(SUPERSESSIONS_0_3_0) == 5
    assert len(SUPERSEDED_SYMBOLS_0_3_0) == len(set(SUPERSEDED_SYMBOLS_0_3_0)) == 5
    # The band-2 marks are NOT re-marked, and the two lists are disjoint.
    assert set(SUPERSEDED_SYMBOLS_0_3_0).isdisjoint(SUPERSEDED_SYMBOLS)
    # WHAT IS NOT MARKED is recorded with its reason.
    assert len(NOT_SUPERSEDED_AND_WHY_0_3_0) == 4
    for symbol, reason in NOT_SUPERSEDED_AND_WHY_0_3_0:
        assert symbol.strip() and len(reason) > 80, symbol
        assert symbol not in SUPERSEDED_SYMBOLS_0_3_0, symbol
    # THE LEDGER MARK IS A READING AND NOT A VALUE CHANGE, which is why its
    # replacement is the same object.
    by_symbol = {record.symbol: record for record in SUPERSESSIONS_0_3_0}
    ledger = by_symbol["ASSUMPTION_LEDGER_0_2_0"]
    assert ledger.kind == "reading"
    assert ledger.still_valid_at_zero_tolerance is True
    assert ASSUMPTION_LEDGER_0_3_0 is ASSUMPTION_LEDGER_0_2_0







