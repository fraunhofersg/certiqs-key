"""The ``protocol-compiler`` registry is well formed, and what it is bound to.

THIRTEEN TESTS ARE ABSENT, AND THIS IS THE RECORD OF WHICH
AND WHY. They would bind this registry to
a single interface transcription and to a
``contract.tex`` pinned by content hash. NEITHER DOCUMENT EXISTS IN THIS
REPOSITORY and neither will: the normative text is the claim files under
spec/modules/protocol-compiler/, assembled into a contract by the harness, and
PRINCIPLES.md section 2.5 replaces content-hash pinning with "an accepted
version is pinned by its commit". The same disposition holds for reductions
(tests/oracles/test_reductions_registry_interface.py's header).

SIX ARE RE-ESTABLISHED, one per absent test, in
``test_protocol_compiler_registry_interface.py``, against THIS repository's
claim files and interface.yaml: the claim-id traceability, the assumption
ledger, the conventions, the two recorded parameters, the machine-key
vocabulary and the verbatim refusal strings.

SEVEN STAY ABSENT, with their reasons:
  * the accepted-contract pin and the content hash -- no such pin exists here;
  * the Part I / Part II section map -- an artefact of a single
    document, which the claim files replace;
  * the provenance recount and the refs-per-provenance check -- ``provenance``
    and ``refs`` are fields of every claim file and are checked by
    ``python -m harness.check_claims``, which is where that obligation lives
    now (harness/README.md);
  * the wire-declaration comparison -- it reads the CONSUMING ENGINE's
    ``manifest.py``, which belongs to meat-core;
  * the open-implementation-choice index -- this module's interface.yaml
    deliberately carries no ``open_choices`` block: what it carries instead is
    ``fixed_by_this_file``, and the reductions move made the same call.

WHAT THIS FILE STILL PINS, and it is the bulk of it.

1. **Admissibility (ADR-0003).** No expected value here comes from MATLAB,
   OpenQKDSecurity, CVX, MOSEK or Julia. The guard reuses
   ``registry.INADMISSIBLE_SOURCES``, imported rather than restated, so the
   registries cannot drift on what an admissible oracle is.
2. **Well-formedness.** Unique ids, a kind from ``registry.KINDS``, and a
   derivation long enough to redo on paper.
3. **Internal consistency of the frozen tables.** Relations that hold *among
   the frozen numbers* -- a joint distribution that sums to one, a ``Phi``
   entry that equals its own fibre sum, a choice mass that equals its declared
   weight at two different states, a conjugation branch pair that genuinely
   differs. These catch a transcription typo. THE DERIVATION IN THE ENTRY, NOT
   THE TABLE, STAYS AUTHORITATIVE.
4. **The PC-G enumeration is TOTAL and MUTUALLY EXCLUSIVE.** Every one of the
   192 points of the seven-axis product is either excluded by a named
   consistency rule or matched by exactly one case. That is the band's top-risk
   item, and it is proved here by iteration rather than asserted.

**What is deliberately absent: any reconstruction of the module.** Nothing here
compiles a specification, runs a validator check, evaluates a gate, composes a
channel or multiplies two matrices. Every assertion either substitutes a frozen
value into an equation of the claims, or relates two frozen fields of the same
case. That is the discipline ``registry.py`` states, and it binds harder in run
A of a two-run band, where no implementation existed yet and the whole point of
the freeze is that run B could not tune the values to its code.

**And no assertion that the package is absent.** The registry's
self-containment is asserted as "this module imports nothing from
``certiqs_key.protocol_compiler``", which stays true now that the package
exists. An assertion about a directory's absence would have passed at the
freeze and died later, and a test that must be deleted to make progress
is not a freeze.
"""

from __future__ import annotations

import itertools
from fractions import Fraction
from pathlib import Path
from typing import Any

import pytest
from registry_instances_bb84 import (
    BB84_ALPHABETS,
    BB84_CASES,
    BB84_D_VERDICTS,
    BB84_GATE_VERDICTS,
    BB84_KEY_MAP,
    BB84_PC_ORACLES,
    BB84_PHI,
    CONJUGATION_BRANCHES,
    bb84_pc_oracle,
)
from registry_protocol_compiler import (
    CHAIN_CASES,
    CHANGE_REQUEST_CANDIDATES,
    DECIDABILITY_COUNTS,
    DIMENSION_ONE_EQUALITIES,
    FEASIBLE_SET_COMPARISONS,
    GATE_AXES,
    GATE_CASES,
    GATE_CONSISTENCY_RULES,
    GATE_VERDICT_VOCABULARY,
    INADMISSIBLE_SOURCES,
    INDEX_MAP_CASES,
    INDEXED_ALPHABETS,
    JOINT_DISTRIBUTION_CASES,
    KEY_MAP_CASES,
    KINDS,
    LINK_STATUS_VOCABULARY,
    PC_ORACLES,
    PERP,
    RECONSTRUCTION_CASES,
    VALIDATOR_CASES,
    WEIGHTED_FAMILY_CASES,
    WITNESS_CASES,
    WITNESS_LEG_FAILURES,
    Matrix,
    WitnessCase,
    pc_oracle,
)
from registry_transmitter import (
    CERTIFICATE_CASES,
    CONSISTENCY_CRITERION_CASES,
    SR3_RECORD,
    TRANSMITTER_PC_ORACLES,
)

#: RE-POINTED TO 0.3.0 BY RUN A OF THE B3 IMPLEMENTATION BAND, and these two
#: constants plus ``SYMBOLS_VERSION`` are the ONLY thing that run re-pointed in
#: this file. They are CONTENT PINS, not frozen expected values: the pins are recomputed
#: once at the close of a band, and a pin left at a superseded version is the
#: "dangling sibling pin" defect rather than evidence of anything.
#:
#: EVERY OTHER ASSERTION IN THIS FILE STILL PINS THE 0.1.4 INTERFACE SURFACE
#: against the frozen registry tuples, so several tests below are RED BY DESIGN
#: until run B re-points them together with the values they read. None was
#: weakened, skipped or xfailed to hide that; the run A report lists them by
#: name and interface.yaml records them under
#: ``delta_from_0_1_4.tests_red_by_design``.
CONTRACT_VERSION = "0.3.0"
SYMBOLS_VERSION = "0.4.0"
#: sha256 of the accepted ``contract.tex`` at CONTRACT_VERSION -- the RELEASED
#: blob (STATUS.yaml ``gates.g3.released_blob_sha256_lf``), which is the signed
#: blob with the ``-draft`` suffix of ``\ContractVersion`` dropped at the
#: signature. An amendment moves it, and moving it is a G3 act -- so a mismatch
#: here is either an unaccepted edit or an accepted one this file has not been
#: re-pointed to.
CONTRACT_SHA256 = "f1441567c99618859890151c990d4e7e47c6cfad42fa385bd0ce3b8835dbe65d"
CLAIM_IDS = (
    "PC1",
    "PC2",
    "PC3",
    "PC4",
    "PC5",
    "PC6",
    "PC7",
    "PC8",
    "PC9",
    "PC10",
    "PC11",
    "PC12",
)


def _entries(matrix: Matrix) -> list[tuple[Fraction, Fraction]]:
    return [entry for row in matrix for entry in row]


def _scalar_bound(case: WitnessCase) -> Fraction:
    """Return the UNTRUSTED right-hand side c_k of a one-entry list.

    D(vi) types Theta_k as a real scalar in untrusted-source mode, so this is a
    narrowing of the frozen field and not a computation.
    """
    assert case.source_mode == "untrusted", case.case_id
    assert len(case.constraints) == 1, case.case_id
    bound = case.constraints[0][2]
    assert isinstance(bound, Fraction), case.case_id
    return bound


# ---------------------------------------------------------------------------
#  1. Traceability against the G4 interface
# ---------------------------------------------------------------------------


#: Lifecycle states in which `contract.tex` is mutable and the content pin
#: below is therefore false BY CONSTRUCTION rather than by defect
#: (the lifecycle table).
_MUTABLE_STATES = frozenset({"drafting", "in-review", "changes-requested"})

#: Every state the lifecycle table defines. Guarding against this set
#: is what stops a typo in STATUS.yaml from silently disabling the pin.


@pytest.mark.contract
def test_the_relocated_instance_was_re_read_and_not_assumed() -> None:
    """The two annexed-instance entries record what was re-read at 0.1.4.

    PC12's environments moved into Part II and Example ``ex:conj`` was the one
    of them the G3 signature discloses as not byte-identical. An entry whose
    text moved under it and that says nothing about having been re-read is
    indistinguishable from one that was never checked.
    """
    # THE TWO ENTRIES ARE registry_instances_bb84.py's -- the worked
    # instance is DATA and not a claim -- so
    # they are read through that half's accessor. NOT ONE BYTE OF THEM MOVED.
    for oracle_id in ("O-PC-BB84", "O-PC-CONJUGATION"):
        note = bb84_pc_oracle(oracle_id).revalidation
        assert len(note.strip()) > 400, oracle_id
        assert "IDENTICAL" in note, oracle_id
    # Every other entry's locators did not move, and none claims otherwise --
    # except O-PC-EXACT-SUMMATION, re-derived by hand and re-frozen
    # under "Re-derive and re-freeze", whose
    # `revalidation` records the derivation and the decision.
    refrozen = {"O-PC-EXACT-SUMMATION"}
    for entry in PC_ORACLES:
        if entry.oracle_id in refrozen:
            assert "RE-FROZEN" in entry.revalidation, entry.oracle_id
            assert "Re-derive and re-freeze" in entry.revalidation, entry.oracle_id
            assert "choice_weights_not_normalized" in entry.revalidation
            continue
        assert entry.revalidation == "", entry.oracle_id
    for entry in TRANSMITTER_PC_ORACLES:
        assert entry.revalidation == "", entry.oracle_id


@pytest.mark.contract
def test_the_registry_covers_every_claim_of_the_contract() -> None:
    """PC1-PC12, ACROSS THE THREE HALVES THE PARTITION MADE.

    The union is what the coverage claim was always about: PC10 and PC11 are
    covered by ``registry_transmitter`` and PC12 by ``registry_instances_bb84``
    because the labels they pin are those modules' now. Reading one
    half alone would report a gap that the cut created and nothing else.
    """
    covered = {
        claim
        for entry in (*PC_ORACLES, *TRANSMITTER_PC_ORACLES, *BB84_PC_ORACLES)
        for claim in entry.claims
    }
    assert set(CLAIM_IDS) <= covered


def _resolve(document: dict[str, Any], site: str) -> str:
    """Resolve an ``open_choices`` site path to the note text it names.

    Three shapes occur, and no others are accepted: ``inputs[key].field``,
    ``outputs[key].field``, and a dotted path from the document root. A site
    that does not resolve is a broken index, which is the failure mode the
    F-4-02 closure exists to make impossible.
    """
    if site.startswith(("inputs[", "outputs[")):
        table, rest = site.split("[", 1)
        key, field = rest.split("].", 1)
        row = next(r for r in document[table] if r["name"] == key)
        value = row[field]
    else:
        value = document
        for part in site.split("."):
            value = value[part]
    assert isinstance(value, str), site
    return value


@pytest.mark.contract
def test_the_change_request_candidates_are_all_dispositioned() -> None:
    assert len(CHANGE_REQUEST_CANDIDATES) == 7
    statuses = [status for status, _, _ in CHANGE_REQUEST_CANDIDATES]
    assert statuses.count("CLEARED") == 6
    routed = [s for s in statuses if s.startswith("ROUTED")]
    assert len(routed) == 1
    for _, gap, reading in CHANGE_REQUEST_CANDIDATES:
        assert len(gap.strip()) > 60
        assert len(reading.strip()) > 120


# ---------------------------------------------------------------------------
#  2. Admissibility and well-formedness
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_no_entry_derives_from_an_inadmissible_source() -> None:
    for entry in PC_ORACLES:
        text = f"{entry.subject}\n{entry.derivation}"
        for source in INADMISSIBLE_SOURCES:
            assert source.lower() not in text.lower(), (entry.oracle_id, source)


@pytest.mark.contract
def test_every_oracle_entry_is_well_formed() -> None:
    identifiers = [entry.oracle_id for entry in PC_ORACLES]
    assert len(identifiers) == len(set(identifiers))
    for entry in PC_ORACLES:
        assert entry.oracle_id.startswith("O-PC-"), entry.oracle_id
        assert entry.kind in KINDS, entry.oracle_id
        assert len(entry.derivation.strip()) > 200, entry.oracle_id
        assert entry.subject.strip(), entry.oracle_id
        # Every entry is estimate-tier: this contract declares no assurance
        # label at all, and nothing it emits is itself tiered.
        assert entry.assurance == "estimate", entry.oracle_id
        assert pc_oracle(entry.oracle_id) is entry


@pytest.mark.contract
def test_unknown_oracle_id_raises() -> None:
    with pytest.raises(KeyError):
        pc_oracle("O-PC-NO-SUCH-ENTRY")


@pytest.mark.contract
def test_every_case_carries_its_arithmetic() -> None:
    groups: tuple[tuple[Any, ...], ...] = (
        INDEX_MAP_CASES,
        WEIGHTED_FAMILY_CASES,
        JOINT_DISTRIBUTION_CASES,
        KEY_MAP_CASES,
        WITNESS_CASES,
        WITNESS_LEG_FAILURES,
        VALIDATOR_CASES,
        RECONSTRUCTION_CASES,
        DECIDABILITY_COUNTS,
        CHAIN_CASES,
        GATE_CASES,
        FEASIBLE_SET_COMPARISONS,
        DIMENSION_ONE_EQUALITIES,
        CERTIFICATE_CASES,
        CONSISTENCY_CRITERION_CASES,
        BB84_CASES,
        CONJUGATION_BRANCHES,
    )
    seen: set[str] = set()
    for group in groups:
        for case in group:
            identifier = getattr(case, "case_id", None) or getattr(
                case, "branch_id", None
            )
            if identifier is None:
                identifier = case.alphabet
            assert identifier not in seen, identifier
            seen.add(identifier)
            assert len(case.arithmetic.strip()) > 120, identifier


@pytest.mark.contract
def test_every_frozen_number_is_exact() -> None:
    """No float anywhere: every scalar a Fraction, every matrix entry a pair."""

    def check(value: object, where: str) -> None:
        assert not isinstance(value, float), where
        if isinstance(value, tuple):
            for item in value:
                check(item, where)

    for case in (*WITNESS_CASES, *WITNESS_LEG_FAILURES):
        check(case.witness, case.case_id)
        check(case.tau_a, case.case_id)
        check(case.constraint_values, case.case_id)
    for weighted in WEIGHTED_FAMILY_CASES:
        check(weighted.emitted, weighted.case_id)
        check(weighted.weights, weighted.case_id)
    for joint in JOINT_DISTRIBUTION_CASES:
        check(joint.joint, joint.case_id)
        check(joint.phi_vector, joint.case_id)
    for bb84 in BB84_CASES:
        check(bb84.joint, bb84.case_id)
        check(bb84.alice_povm, bb84.case_id)
        check(bb84.bob_povm, bb84.case_id)
        check(bb84.phi_vector, bb84.case_id)
    for branch in CONJUGATION_BRANCHES:
        check(branch.emitted_element, branch.branch_id)
        check(branch.matched_basis_joint, branch.branch_id)
    for certificate in CERTIFICATE_CASES:
        check(certificate.tau_a, certificate.case_id)
        check(certificate.sr2_computed, certificate.case_id)


@pytest.mark.contract
def test_the_registry_imports_nothing_from_the_module_it_pins() -> None:
    """Self-containment. NOT an assertion that the package is absent on disk.

    THE MODULE THIS REGISTRY PINS IS `certiqs_key`, so the guard asserts that
    `certiqs_key` is not imported: the registry could otherwise have imported
    the code it tests and regenerated every expectation from it, and this test
    would have stayed green.

    IT RUNS OVER ALL THREE HALVES of the partition.
    """
    for half in (
        "registry_protocol_compiler.py",
        "registry_transmitter.py",
        "registry_instances_bb84.py",
    ):
        source = (Path(__file__).parent / half).read_text(encoding="utf-8")
        for line in source.splitlines():
            stripped = line.strip()
            if stripped.startswith(("import ", "from ")):
                assert "certiqs_key" not in stripped, (half, stripped)
                assert "instances" not in stripped, (half, stripped)


# ---------------------------------------------------------------------------
#  3. PC-A -- the label-to-index map
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_index_maps_are_bijections_onto_initial_segments_with_inverses() -> None:
    """Definition def:compile: nine alphabets, each onto an initial segment."""
    assert tuple(case.alphabet for case in INDEX_MAP_CASES) == INDEXED_ALPHABETS
    assert len(INDEX_MAP_CASES) == 9
    for case in INDEX_MAP_CASES:
        labels = case.labels
        assert len(set(labels)) == len(labels), case.alphabet
        forward = dict(case.forward)
        assert set(forward) == set(labels), case.alphabet
        indices = sorted(forward.values())
        # An INITIAL SEGMENT of the non-negative integers: 0..N-1, no gaps.
        assert indices == list(range(len(labels))), case.alphabet
        inverse = dict(case.inverse)
        assert len(inverse) == len(labels), case.alphabet
        for label, index in forward.items():
            assert inverse[index] == label, (case.alphabet, label)


# ---------------------------------------------------------------------------
#  4. PC-B -- weights, joint distributions, Phi fibres, block diagonality
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_weighted_families_are_complete_and_carry_the_weight_inside() -> None:
    """Lemma lem:weighted (i): the emitted elements already carry q_t."""
    for case in WEIGHTED_FAMILY_CASES:
        assert len(case.weights) == len(case.choices), case.case_id
        assert all(w > 0 for w in case.weights), case.case_id
        assert sum(case.weights) == 1, case.case_id
        assert len(case.emitted) == len(case.joint_alphabet), case.case_id
        assert len(case.choice_of) == len(case.joint_alphabet), case.case_id
        # The joint alphabet is the DISJOINT UNION: every element belongs to
        # exactly one declared choice, and every choice is represented.
        assert set(case.choice_of) == set(case.choices), case.case_id
        dimension = len(case.emitted[0])
        total = [
            [
                (
                    sum(m[i][j][0] for m in case.emitted),
                    sum(m[i][j][1] for m in case.emitted),
                )
                for j in range(dimension)
            ]
            for i in range(dimension)
        ]
        identity = [
            [
                (Fraction(1) if i == j else Fraction(0), Fraction(0))
                for j in range(dimension)
            ]
            for i in range(dimension)
        ]
        assert total == identity, case.case_id


@pytest.mark.contract
def test_the_two_sector_families_split_on_block_diagonality_only() -> None:
    """SECTOR-holds and SECTOR-fails are both POVMs; one is block-diagonal."""
    by_id = {case.case_id: case for case in WEIGHTED_FAMILY_CASES}
    holds, fails = by_id["SECTOR-holds"], by_id["SECTOR-fails"]
    assert holds.block_diagonal is True
    assert fails.block_diagonal is False
    assert len(holds.sector_projectors) == len(fails.sector_projectors) == 2
    # The failing family's offending entry, named exactly: Pi_{s0} F Pi_{s1}
    # picks out row in {0,1}, column 2, and it is 1/2 rather than 0.
    assert fails.emitted[0][0][2] == (Fraction(1, 2), Fraction(0))
    assert holds.emitted[0][0][2] == (Fraction(0), Fraction(0))


@pytest.mark.contract
def test_joint_distributions_sum_to_one_and_phi_equals_its_fibre_sums() -> None:
    """Theorem thm:measurements-and-statistics (iv), and Eq. eq:jointdist's second half."""  # noqa: E501
    for case in JOINT_DISTRIBUTION_CASES:
        cells = [value for row in case.joint for value in row]
        assert all(value >= 0 for value in cells), case.case_id
        assert sum(cells) == 1, case.case_id
        assert sum(case.phi_vector) == 1, case.case_id
        # Every fibre sum equals its Phi entry, and the fibres PARTITION X x V.
        covered: list[tuple[int, int]] = []
        for value, fibre in zip(case.phi_vector, case.phi_fibres, strict=True):
            assert sum(case.joint[x][v] for x, v in fibre) == value, case.case_id
            covered.extend(fibre)
        assert sorted(covered) == sorted(
            itertools.product(range(len(case.joint)), range(len(case.joint[0])))
        ), case.case_id


@pytest.mark.contract
def test_the_choice_mass_is_state_independent_and_equals_the_declared_weight() -> None:
    """Eq. eq:choicemass, at two states between which the joint table changes."""
    masses: dict[str, set[Fraction]] = {}
    for case in JOINT_DISTRIBUTION_CASES:
        for label, declared, computed in case.choice_mass:
            assert declared == computed, (case.case_id, label)
            masses.setdefault(label, set()).add(computed)
    # The same four numbers at both states -- that is the whole of PC3 (ii).
    assert {label: len(values) for label, values in masses.items()} == {
        "t0": 1,
        "t1": 1,
        "r0": 1,
        "r1": 1,
    }
    # And the two joint tables genuinely differ, so the agreement is not empty.
    first, second = JOINT_DISTRIBUTION_CASES[0], JOINT_DISTRIBUTION_CASES[1]
    assert first.joint != second.joint


# ---------------------------------------------------------------------------
#  5. PC-C / PC-E -- sifting, party computability, the validator
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_key_map_cases_are_total_and_the_r_hold_extensions_agree() -> None:
    for case in KEY_MAP_CASES:
        pairs = {(x, v) for x, v, _ in case.announcement}
        assert pairs == set(
            itertools.product(
                range(len(case.alice_alphabet)), range(len(case.bob_alphabet))
            )
        ), case.case_id
        # varsigma is TOTAL on K (Definition def:spec (d)).
        assert {k for k, _ in case.sifting} == set(case.announcement_classes), (
            case.case_id
        )
        assert all(v in {"pass", "fail"} for _, v in case.sifting), case.case_id
        # Eq. eq:rdef: r = perp exactly on the failing classes, when r is built.
        sifting = dict(case.sifting)
        announcement = {(x, v): k for x, v, k in case.announcement}
        if case.case_id == "KEY-MINI":
            for x, v, value in case.key_map:
                expected_perp = sifting[announcement[(x, v)]] == "fail"
                assert (value == PERP) is expected_perp, (case.case_id, x, v)
        if not case.r_hold_eq_rhold:
            continue
        # Both extensions are TOTAL on O_h x K.
        domain = set(itertools.product(case.holder_readouts, case.announcement_classes))
        by_eq = {(o, k): value for o, k, value in case.r_hold_eq_rhold}
        by_recon = {(o, k): value for o, k, value in case.r_hold_reconstructed}
        assert set(by_eq) == domain, case.case_id
        assert set(by_recon) == domain, case.case_id
        # They agree on every REALIZED pair -- both are r(x, v) there.
        for pair in case.realized_pairs:
            assert by_eq[pair] == by_recon[pair], (case.case_id, pair)
    # And on KEY-MINI they DIFFER somewhere off the realized set, which is the
    # freedom the proof of Theorem thm:validator-soundness calls immaterial.
    mini = next(c for c in KEY_MAP_CASES if c.case_id == "KEY-MINI")
    by_eq_mini = {(o, k): v for o, k, v in mini.r_hold_eq_rhold}
    by_recon_mini = {(o, k): v for o, k, v in mini.r_hold_reconstructed}
    assert by_eq_mini != by_recon_mini


@pytest.mark.contract
def test_v5_and_v8_are_independent_on_the_frozen_data() -> None:
    """Neither check subsumes the other, shown by a case each way."""
    by_id = {case.case_id: case for case in KEY_MAP_CASES}
    sidecond, v8 = by_id["KEY-SIDECOND"], by_id["KEY-V8"]
    assert (sidecond.v5_passes, sidecond.v8_passes) == (False, True)
    assert (v8.v5_passes, v8.v8_passes) == (True, False)
    # Remark rem:vacuous: read against the joint pair the condition is vacuous.
    assert v8.joint_pair_reading_passes is True
    assert v8.v8_passes is False


@pytest.mark.contract
def test_each_validator_case_names_a_distinct_check_and_only_v7_is_one_sided() -> None:
    checks = [case.check for case in VALIDATOR_CASES if case.check is not None]
    assert checks == ["V1", "V2", "V3", "V4", "V5", "V6", "V7", "V8"]
    assert len(set(checks)) == 8
    conditions = [
        case.target_condition for case in VALIDATOR_CASES if case.check is not None
    ]
    assert conditions == [
        "D(i)",
        "D(ii)",
        "D(iii)",
        "D(iv)",
        "D(v)",
        "D(vi)",
        "D(vii)",
        "D(viii)",
    ]
    refusing = [case for case in VALIDATOR_CASES if case.refuses]
    assert len(refusing) == 8
    # Exactly one refusal is of a WELL-FORMED declaration, and it is V7.
    one_sided = [case for case in refusing if not case.genuine_violation]
    assert [case.check for case in one_sided] == ["V7"]
    assert one_sided[0].well_formed is True
    # Every other refusal names a real defect (Theorem thm:validator-soundness (ii)).
    for case in refusing:
        if case.check != "V7":
            assert case.genuine_violation is True, case.case_id
            assert case.well_formed is False, case.case_id
    # And exactly one case passes everything.
    passing = [case for case in VALIDATOR_CASES if not case.refuses]
    assert [case.case_id for case in passing] == ["ALLPASS-MINI"]
    assert passing[0].well_formed is True


@pytest.mark.contract
def test_the_reconstructions_differ_only_off_the_realized_set() -> None:
    by_id = {case.case_id: case for case in RECONSTRUCTION_CASES}
    assert by_id["RECON-varsigma-MINI"].agree_everywhere is True
    assert by_id["RECON-varsigma-unrealized"].agree_everywhere is False
    assert by_id["RECON-rhold-MINI"].agree_everywhere is False
    for case in RECONSTRUCTION_CASES:
        disagreements = [row for row in case.rows if row[1] != row[2]]
        assert (not disagreements) is case.agree_everywhere, case.case_id


@pytest.mark.contract
def test_the_decidability_counts_instantiate_the_formulas() -> None:
    """Theorem thm:validator-soundness (iv), written out at two instances."""
    for case in DECIDABILITY_COUNTS:
        sectors, m = case.sector_count, case.constraint_count
        expected_blocks = case.v_size * sectors * (sectors - 1) + m * sectors * (
            sectors - 1
        )
        assert case.block_conditions == expected_blocks, case.case_id
        assert case.v4_pairs == case.x_size * case.v_size, case.case_id
        assert case.ordered_pairs == (case.x_size * case.v_size) ** 2, case.case_id
    counts = {case.case_id: case for case in DECIDABILITY_COUNTS}
    assert counts["COUNT-MINI"].block_conditions == 0
    assert counts["COUNT-SECTOR"].block_conditions == 8


# ---------------------------------------------------------------------------
#  6. PC-D -- the witness legs
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_each_leg_case_fails_exactly_one_verification_leg() -> None:
    """Theorem thm:feasibility (ii) names five legs; one case fails each, alone."""
    legs = (
        "leg_positive",
        "leg_trace_one",
        "leg_sector_blocks",
        "leg_marginal",
        "leg_constraints",
    )
    failed_by: dict[str, list[str]] = {leg: [] for leg in legs}
    for case in WITNESS_LEG_FAILURES:
        failing = [leg for leg in legs if getattr(case, leg) is False]
        assert len(failing) == 1, case.case_id
        failed_by[failing[0]].append(case.case_id)
        assert case.v7_passes is False, case.case_id
    assert all(len(ids) == 1 for ids in failed_by.values()), failed_by
    assert len(WITNESS_LEG_FAILURES) == 5


@pytest.mark.contract
def test_the_default_witness_cases_and_the_one_sided_counterexample() -> None:
    by_id = {case.case_id: case for case in WITNESS_CASES}
    # Both source modes, at named dimensions, all legs passing.
    for case_id in (
        "WIT-default-trusted-maxmixed",
        "WIT-default-trusted-singular",
        "WIT-default-untrusted-twosector",
        "WIT-default-satisfies-list",
    ):
        case = by_id[case_id]
        assert case.is_default_witness is True, case_id
        assert case.v7_passes is True, case_id
        assert case.refusal_reason is None, case_id
    assert by_id["WIT-default-trusted-maxmixed"].source_mode == "trusted"
    assert by_id["WIT-default-untrusted-twosector"].source_mode == "untrusted"
    assert by_id["WIT-default-untrusted-twosector"].sector_dims == (2, 1)
    # The default satisfies one m >= 1 list and fails the next; a supplied
    # witness rescues the second.
    satisfied = by_id["WIT-default-satisfies-list"]
    rescued = by_id["WIT-supplied-rescues"]
    assert satisfied.constraint_values == (Fraction(1, 2),)
    assert satisfied.constraint_values[0] >= _scalar_bound(satisfied)
    assert rescued.is_default_witness is False
    assert rescued.constraint_values == (Fraction(1),)
    assert rescued.constraint_values[0] >= _scalar_bound(rescued)
    # The Theorem thm:validator-soundness (iii) counterexample: well formed, and
    # refused.
    counterexample = by_id["WIT-pc6iii-counterexample"]
    assert counterexample.v7_passes is False
    assert counterexample.refusal_reason == "no_feasibility_witness"
    assert counterexample.constraint_values == (Fraction(1, 2),)
    assert counterexample.constraint_values[0] < _scalar_bound(counterexample)
    assert counterexample.leg_constraints is False


# ---------------------------------------------------------------------------
#  7. PC-F -- the reduction chain
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_chain_cases_name_at_most_one_failing_condition() -> None:
    conditions = (
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
    for case in CHAIN_CASES:
        verdicts = dict(case.verdicts)
        assert tuple(verdicts) == conditions, case.case_id
        assert all(
            value in {"holds", "fails", "vacuous", "not checked"}
            for value in verdicts.values()
        ), case.case_id
        failing = [name for name, value in verdicts.items() if value == "fails"]
        assert len(failing) <= 1, case.case_id
        assert case.refuses is bool(failing), case.case_id
        if failing:
            assert case.failing_condition == failing[0], case.case_id
        else:
            assert case.failing_condition is None, case.case_id
        # (X1) is NEVER the failing condition: Theorem thm:chain-consumption (i) says it
        # is not decided, being the type of the record.
        assert verdicts["X1"] == "holds", case.case_id
        # An empty source segment makes (S1)-(S4) vacuous, and only then.
        if case.l_s == 0:
            assert all(
                verdicts[name] == "vacuous" for name in ("S1", "S2", "S3", "S4")
            ), case.case_id
        assert case.l_r >= 1, case.case_id
        assert len(case.receiver_segment) == case.l_r, case.case_id
        assert len(case.source_segment) == case.l_s, case.case_id
        for link in (*case.source_segment, *case.receiver_segment):
            assert link.status in LINK_STATUS_VOCABULARY, case.case_id
            # Every link carries BOTH slots, empty or not (req:chain-record-slots).
            assert link.license_slot_present is True, case.case_id


@pytest.mark.contract
def test_not_checked_appears_exactly_where_the_data_run_out() -> None:
    """(C4) and (S3) only; and where A-LINK is named, nothing is refused."""
    for case in CHAIN_CASES:
        verdicts = dict(case.verdicts)
        not_checked = {
            name for name, value in verdicts.items() if value == "not checked"
        }
        assert not_checked <= {"C2", "C4", "S2", "S3"}, case.case_id
    named = [case for case in CHAIN_CASES if case.named_assumption is not None]
    assert [case.case_id for case in named] == ["CHAIN-not-decided-C4-S3"]
    case = named[0]
    assert case.named_assumption == "A-LINK"
    assert case.refuses is False
    verdicts = dict(case.verdicts)
    # The two conditions are NOT CHECKED and are certainly not `holds'.
    assert verdicts["C4"] == "not checked"
    assert verdicts["S3"] == "not checked"
    assert all(
        not link.channel_supplied
        for link in (*case.source_segment, *case.receiver_segment)
    )


@pytest.mark.contract
def test_the_band_a_chain_record_is_the_one_slice_one_consumes() -> None:
    band_a = next(case for case in CHAIN_CASES if case.case_id == "CHAIN-bandA")
    assert band_a.l_s == 0
    assert band_a.l_r == 1
    assert band_a.source_segment == ()
    link = band_a.receiver_segment[0]
    assert link.status == "exact"
    assert link.channel_supplied is True
    assert link.transported_constraints == ()
    assert link.license_slot_present is True
    assert link.license_slot_empty is True
    assert link.source_descriptor == link.target_descriptor
    # gamma is the identity bijection on V = V^ph.
    assert band_a.physical_alphabet == band_a.emitted_alphabet
    assert all(w == v for w, v in band_a.gamma)
    assert band_a.refuses is False


@pytest.mark.contract
def test_the_coarse_graining_correspondence_is_a_total_surjection() -> None:
    """(C2): physical -> emitted, non-injective allowed, and only that way."""
    proper = next(case for case in CHAIN_CASES if case.case_id == "CHAIN-coarse-proper")
    domain = [w for w, _ in proper.gamma]
    image = {v for _, v in proper.gamma}
    assert sorted(domain) == sorted(proper.physical_alphabet)
    assert image == set(proper.emitted_alphabet)
    assert len(domain) > len(image)  # genuinely non-injective
    wrong = next(
        case for case in CHAIN_CASES if case.case_id == "CHAIN-coarse-wrong-direction"
    )
    assert wrong.failing_condition == "C2"
    assert wrong.refuses is True
    # The reversed correspondence maps the EMITTED alphabet onto the physical.
    assert sorted(w for w, _ in wrong.gamma) == sorted(wrong.emitted_alphabet)


# ---------------------------------------------------------------------------
#  8. PC-G -- the enumeration is TOTAL and MUTUALLY EXCLUSIVE
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_the_gate_enumeration_is_total_and_mutually_exclusive() -> None:
    """Every point of the seven-axis product is excluded once or matched once.

    This is the band's top-risk assertion. Nothing is computed about the
    compiler: each point is tested for membership in a frozen pattern.
    """
    axis_names = [name for name, _ in GATE_AXES]
    axis_values = [values for _, values in GATE_AXES]
    assert len(axis_names) == 7
    total = 1
    for values in axis_values:
        total *= len(values)
    assert total == 192

    excluded = 0
    matched = 0
    per_case: dict[str, int] = {case.case_id: 0 for case in GATE_CASES}
    per_rule: dict[str, int] = {rule.rule_id: 0 for rule in GATE_CONSISTENCY_RULES}

    for point in itertools.product(*axis_values):
        assignment = dict(zip(axis_names, point, strict=True))
        hits = [
            rule
            for rule in GATE_CONSISTENCY_RULES
            if all(assignment[axis] in values for axis, values in rule.pattern)
        ]
        if hits:
            excluded += 1
            for rule in hits:
                per_rule[rule.rule_id] += 1
            continue
        cases = [
            case
            for case in GATE_CASES
            if all(assignment[axis] in values for axis, values in case.axes)
        ]
        assert len(cases) == 1, (assignment, [c.case_id for c in cases])
        matched += 1
        per_case[cases[0].case_id] += 1

    assert excluded + matched == total
    assert excluded == 106
    assert matched == 86
    # No case is dead: every one of the sixteen is reached.
    assert all(count > 0 for count in per_case.values()), per_case
    # No consistency rule is dead either.
    assert all(count > 0 for count in per_rule.values()), per_rule
    assert per_case["G-VALIDATOR-FAIL"] == 48


@pytest.mark.contract
def test_gate_verdicts_use_only_the_three_valued_vocabulary() -> None:
    """No fourth token is written anywhere, including on a refusal."""
    for case in GATE_CASES:
        assert tuple(name for name, _, _ in case.gates) == ("G1", "G2", "G3a", "G3b")
        for name, engaged, verdict in case.gates:
            if verdict is not None:
                assert verdict in GATE_VERDICT_VOCABULARY, (case.case_id, name)
                assert engaged is True, (case.case_id, name)
            else:
                assert engaged in (False, None), (case.case_id, name)
        assert case.outcome in {"refusal", "emission"}, case.case_id
        if case.outcome == "refusal":
            assert case.emitted_mode is None, case.case_id
            assert case.key_length_eligible is None, case.case_id
            assert case.named_check is not None, case.case_id
            assert case.emits_source_replacement_license is False, case.case_id
            # On a refusal the gates of Definition def:eligible have no subject.
            gates = {name: engaged for name, engaged, _ in case.gates}
            assert gates["G3a"] is None, case.case_id
            assert gates["G3b"] is None, case.case_id
        else:
            assert case.emitted_mode in {"trusted", "untrusted"}, case.case_id
            assert isinstance(case.key_length_eligible, bool), case.case_id
            assert case.named_check is None, case.case_id


@pytest.mark.contract
def test_key_length_eligibility_matches_the_gates_that_are_engaged() -> None:
    """KLE is true exactly when no ENGAGED gate of the emission failed.

    The one apparent exception is Table tab:gateoutcome row 2, where (G2) is
    reported failed FOR THE REQUEST and the row says in as many words that KLE
    is "decided by the remaining gates". That case is singled out here rather
    than smoothed over.
    """
    for case in GATE_CASES:
        if case.outcome != "emission":
            continue
        failed = {name for name, _, verdict in case.gates if verdict == "failed"}
        if case.fallback_recorded:
            assert case.case_id == "G-T-D2-NOCERT-M0-FALLBACK"
            assert failed == {"G2"}
            assert case.key_length_eligible is True
            continue
        assert case.key_length_eligible is (not failed), case.case_id
    # Exactly one case records the fallback, and it is the only mode change.
    fallbacks = [case for case in GATE_CASES if case.fallback_recorded]
    assert [case.case_id for case in fallbacks] == ["G-T-D2-NOCERT-M0-FALLBACK"]
    assert fallbacks[0].emitted_mode == "untrusted"


@pytest.mark.contract
def test_the_two_vacuous_passes_and_the_single_genuine_g3a_pass() -> None:
    """Remark rem:degenerate, turned into a countable fact about the space."""
    verdicts = {
        case.case_id: {name: verdict for name, _, verdict in case.gates}
        for case in GATE_CASES
    }
    vacuous = {cid for cid, g in verdicts.items() if g["G3a"] == "passed vacuously"}
    assert vacuous == {
        "G-U-M1-LIC",
        "G-U-M1-NOLIC",
        "G-T-D1-M1-LIC",
        "G-T-D1-M1-NOLIC",
    }
    # A GENUINE (non-vacuous) pass occurs in exactly ONE corner of the case
    # space -- trusted mode at d_A >= 2 with a verified certificate and a
    # non-empty licensed list -- which is TWO cases differing only in the
    # licence axis.
    genuine = {cid for cid, g in verdicts.items() if g["G3a"] == "passed"}
    assert genuine == {
        "G-T-D2-CERT-M1-LIC-LICENCE",
        "G-T-D2-CERT-M1-LIC-NOLICENCE",
    }
    for case_id in genuine:
        axes = dict(next(c for c in GATE_CASES if c.case_id == case_id).axes)
        assert axes["request"] == ("trusted",)
        assert axes["alice_dim"] == (">=2",)
        assert axes["certificate"] == ("present_passing",)
        assert axes["m"] == (">=1",)
        assert axes["list"] == ("licensed",)
    failed = {cid for cid, g in verdicts.items() if g["G3a"] == "failed"}
    assert failed == {
        "G-T-D2-CERT-M1-UNLIC-LICENCE",
        "G-T-D2-CERT-M1-UNLIC-NOLICENCE",
    }
    # Every remaining case leaves (G3)(a) without a verdict: it is not engaged.
    assert {cid for cid, g in verdicts.items() if g["G3a"] is None} == set(
        verdicts
    ) - vacuous - genuine - failed


@pytest.mark.contract
def test_the_d_a_one_certificate_failure_is_taken_from_def_compile() -> None:
    """The corner Table tab:gateoutcome deliberately does not cover."""
    case = next(c for c in GATE_CASES if c.case_id == "G-T-D1-CERTFAIL")
    assert case.outcome == "refusal"
    assert "def:compile" in case.derives_from
    assert "NOT a row" in case.derives_from
    # And the d_A >= 2 companion IS a table row.
    companion = next(c for c in GATE_CASES if c.case_id == "G-T-D2-CERTFAIL")
    assert "row 3" in companion.derives_from


@pytest.mark.contract
def test_source_replacement_license_is_emitted_exactly_where_section_2_2_says() -> None:
    """Trusted mode emitted at d_A >= 2, and nowhere else."""
    for case in GATE_CASES:
        dims = dict(case.axes)["alice_dim"]
        expected = (
            case.outcome == "emission"
            and case.emitted_mode == "trusted"
            and dims == (">=2",)
        )
        assert case.emits_source_replacement_license is expected, case.case_id
    # And the (SR3) record never carries an assertion by this module.
    for _, _, _, asserted, note in SR3_RECORD:
        assert asserted is False
        assert note.strip()


@pytest.mark.contract
def test_the_conservative_fallback_is_an_inclusion_and_it_is_strict() -> None:
    by_id = {case.case_id: case for case in FEASIBLE_SET_COMPARISONS}
    inside = by_id["CONSERVATIVE-inside"]
    assert (inside.in_trusted_set, inside.in_untrusted_set) == (True, True)
    # The proof's trace step, on the frozen values: tr of the trusted left-hand
    # side is the untrusted left-hand side, and tr(c tau_A) = c.
    trusted_value = inside.trusted_values[0]
    trace = sum(trusted_value[i][i][0] for i in range(len(trusted_value)))
    assert trace == inside.untrusted_values[0]
    assert inside.untrusted_values[0] >= inside.licensed_entries[0][3]
    strict = by_id["CONSERVATIVE-strict"]
    assert (strict.in_trusted_set, strict.in_untrusted_set) == (False, True)
    assert strict.state_marginal != strict.tau_a
    # Remark rem:notfallback: at d_A >= 2, 1_A/d_A is strictly stronger than
    # nomarg (at d_A = 1 it is [1] and excludes nothing; rem:da1).
    anti = by_id["NOTFALLBACK-anti-case"]
    assert (anti.in_trusted_set, anti.in_untrusted_set) == (False, True)
    assert anti.licensed_entries == ()


@pytest.mark.contract
def test_at_dimension_one_the_two_feasible_sets_coincide() -> None:
    """Remark rem:dA1, in both directions."""
    for case in DIMENSION_ONE_EQUALITIES:
        # S_=(A) = {[1]} at d_A = 1: a 1x1 matrix holding the exact scalar 1.
        assert case.tau_a == (((Fraction(1), Fraction(0)),),), case.case_id
        assert case.marginal == (((case.trace, Fraction(0)),),), case.case_id
        # The two conditions coincide, so the two verdicts must agree.
        assert case.marginal_equals_tau is case.trace_is_one, case.case_id
        assert case.in_trusted_set is case.in_untrusted_set, case.case_id
    verdicts = {case.case_id: case.in_trusted_set for case in DIMENSION_ONE_EQUALITIES}
    assert verdicts == {"DA1-normalized": True, "DA1-subnormalized": False}


# ---------------------------------------------------------------------------
#  9. PC-H -- the certificate
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_certificate_vectors_are_unit_vectors_and_sr1_matches_its_verdict() -> None:
    for case in CERTIFICATE_CASES:
        # The unnormalized Gaussian-INTEGER vector and its squared norm.
        assert case.psi_squared_norm == sum(
            amplitude**2 for _, amplitude in case.psi_integer_amplitudes
        ), case.case_id
        assert case.psi_squared_norm > 0, case.case_id
        # (SR1): tau_A is what the partial trace gives, or it is not.
        assert (case.tau_a == case.sr1_computed) is case.sr1_holds, case.case_id
        # (SR1) => tau_A in S_=(A): the computed marginal has trace one.
        trace = sum(case.sr1_computed[i][i][0] for i in range(len(case.sr1_computed)))
        assert trace == 1, case.case_id
        assert all(entry[1] == 0 for entry in _entries(case.sr1_computed)), case.case_id
        # (SR2), entry by entry against p_x rho^v_x.
        expected = tuple(
            tuple(
                tuple((weight * value[0], weight * value[1]) for value in row)
                for row in state
            )
            for weight, state in zip(
                case.virtual_weights, case.virtual_states, strict=True
            )
        )
        assert (case.sr2_computed == expected) is case.sr2_holds, case.case_id
        assert len(case.povm) == len(case.virtual_weights), case.case_id
        assert sum(case.virtual_weights) == 1, case.case_id
    by_id = {case.case_id: case for case in CERTIFICATE_CASES}
    # Both shapes verify, at two different d_A.
    assert by_id["CERT-canonical-with-shield"].canonical_form is True
    assert by_id["CERT-canonical-with-shield"].alice_dim == 4
    assert by_id["CERT-noncanonical-bb84"].canonical_form is False
    assert by_id["CERT-noncanonical-bb84"].alice_dim == 2
    for case_id in ("CERT-canonical-with-shield", "CERT-noncanonical-bb84"):
        assert by_id[case_id].sr1_holds and by_id[case_id].sr2_holds
    # The two conditions fail independently.
    assert (by_id["CERT-sr1-fails"].sr1_holds, by_id["CERT-sr1-fails"].sr2_holds) == (
        False,
        True,
    )
    assert (by_id["CERT-sr2-fails"].sr1_holds, by_id["CERT-sr2-fails"].sr2_holds) == (
        True,
        False,
    )


@pytest.mark.contract
def test_the_consistency_criterion_is_an_equivalence_on_the_frozen_data() -> None:
    """Theorem thm:certificate-sufficiency (ii): the criterion and the identity stand or fall together."""  # noqa: E501
    for case in CONSISTENCY_CRITERION_CASES:
        assert (case.projected_sum == case.pi_s) is case.criterion_holds, case.case_id
        assert (
            case.average_virtual_state == case.psi_signal_marginal
        ) is case.identity_holds, case.case_id
        # The equivalence itself, on frozen verdicts.
        assert case.criterion_holds is case.identity_holds, case.case_id
        # A POVM makes it hold outright.
        if case.is_povm:
            assert case.criterion_holds is True, case.case_id
    by_id = {case.case_id: case for case in CONSISTENCY_CRITERION_CASES}
    # The POVM property is SUFFICIENT and NOT NECESSARY: one non-POVM fails the
    # criterion and one passes it.
    assert by_id["CONS-nonpovm-fails"].is_povm is False
    assert by_id["CONS-nonpovm-fails"].criterion_holds is False
    assert by_id["CONS-nonpovm-holds"].is_povm is False
    assert by_id["CONS-nonpovm-holds"].criterion_holds is True
    # The passing non-POVM is the one with a SINGULAR tau_A, which is what makes
    # Pi_S a proper projector rather than the identity.
    assert by_id["CONS-nonpovm-holds"].pi_s != by_id["CONS-povm-holds"].pi_s


# ---------------------------------------------------------------------------
#  10. PC-I / PC-J -- BB84 and the conjugation branch pair
# ---------------------------------------------------------------------------

#: |<a^b|y^b'>|^2, from the proof of Theorem thm:pc12 (v): delta_{ay} on matched
#: bases and 1/2 on mismatched ones. A frozen fact of that proof, substituted
#: into Eq. eq:bb84stats below and not recomputed here.
_OVERLAP: dict[tuple[str, str], str] = {
    ("Z", "Z"): "delta",
    ("X", "X"): "delta",
    ("Z", "X"): "half",
    ("X", "Z"): "half",
}


@pytest.mark.contract
def test_bb84_alphabet_cardinalities_and_the_nine_element_class_set() -> None:
    sizes = {name: len(labels) for name, labels in BB84_ALPHABETS}
    assert sizes == {
        "X": 4,
        "V": 4,
        "C_A": 3,
        "C_B": 3,
        "Chat": 4,
        "Z_perp": 3,
    }
    # |K| = |C_A| |C_B| = 9, and phi is TOTAL on it.
    assert sizes["C_A"] * sizes["C_B"] == 9
    assert len(BB84_PHI) == 9
    assert len({(a, b) for a, b, _ in BB84_PHI}) == 9
    assert {value for _, _, value in BB84_PHI} == {"gen", "ok", "err", "disc"}
    # Chat_key = {gen}: the only PASSING class is (Z, Z) and phi sends it there.
    passing = ("Z", "Z")
    key_live = {value for a, b, value in BB84_PHI if (a, b) == passing}
    assert key_live == {"gen"}


@pytest.mark.contract
def test_bb84_key_map_is_eq_rdef_on_all_sixteen_cells() -> None:
    assert len(BB84_KEY_MAP) == 16
    alphabet = dict(BB84_ALPHABETS)["X"]
    assert {(x, v) for x, v, _ in BB84_KEY_MAP} == set(
        itertools.product(alphabet, alphabet)
    )
    for x, v, value in BB84_KEY_MAP:
        matched_z = x.startswith("(Z") and v.startswith("(Z")
        if matched_z:
            # r = a, Alice's bit, which is the second component of x.
            assert value == int(x[3]), (x, v)
        else:
            assert value == PERP, (x, v)
    assert sum(1 for _, _, value in BB84_KEY_MAP if value == PERP) == 12


@pytest.mark.contract
def test_bb84_statistics_match_eq_bb84stats_and_phi_matches_its_closed_form() -> None:
    alphabet = dict(BB84_ALPHABETS)["X"]
    for case in BB84_CASES:
        p_a = {"Z": case.alice_weights[0], "X": case.alice_weights[1]}
        p_b = {"Z": case.bob_weights[0], "X": case.bob_weights[1]}
        assert sum(case.alice_weights) == 1, case.case_id
        assert sum(case.bob_weights) == 1, case.case_id
        for i, x in enumerate(alphabet):
            for j, v in enumerate(alphabet):
                basis_a, bit_a = x[1], int(x[3])
                basis_b, bit_b = v[1], int(v[3])
                overlap = _OVERLAP[(basis_a, basis_b)]
                if overlap == "delta":
                    squared = Fraction(1) if bit_a == bit_b else Fraction(0)
                else:
                    squared = Fraction(1, 2)
                expected = Fraction(1, 2) * p_a[basis_a] * p_b[basis_b] * squared
                assert case.joint[i][j] == expected, (case.case_id, x, v)
        cells = [value for row in case.joint for value in row]
        assert sum(cells) == 1, case.case_id
        assert case.phi_total == 1, case.case_id
        # Eq. eq:bb84stats' four-entry Phi vector, in closed form.
        assert case.phi_vector == (
            p_a["Z"] * p_b["Z"],
            p_a["X"] * p_b["X"],
            Fraction(0),
            p_a["Z"] * p_b["X"] + p_a["X"] * p_b["Z"],
        ), case.case_id
        assert sum(case.phi_vector) == 1, case.case_id
        # The err entry is ZERO: the noiseless limit.
        assert case.phi_vector[2] == 0, case.case_id
        # Remark rem:bb84checks: the basis marginals are the weights, exactly.
        assert case.bob_basis_marginals == (p_b["Z"], p_b["X"]), case.case_id
        assert case.alice_basis_marginals == (p_a["Z"], p_a["X"]), case.case_id
        columns = [sum(case.joint[i][j] for i in range(4)) for j in range(4)]
        assert columns[0] + columns[1] == p_b["Z"], case.case_id
        assert columns[2] + columns[3] == p_b["X"], case.case_id
        rows = [sum(case.joint[i]) for i in range(4)]
        assert rows[0] + rows[1] == p_a["Z"], case.case_id
        assert rows[2] + rows[3] == p_a["X"], case.case_id


@pytest.mark.contract
def test_bb84_certificate_values_and_the_three_weight_regimes() -> None:
    for case in BB84_CASES:
        assert case.sr2_values == case.sr2_expected, case.case_id
        # tau_A = 1_A/2 at EVERY weight pair: (SR1) does not see the weights.
        assert case.tau_a == (
            ((Fraction(1, 2), Fraction(0)), (Fraction(0), Fraction(0))),
            ((Fraction(0), Fraction(0)), (Fraction(1, 2), Fraction(0))),
        ), case.case_id
        # Alice's family is complete: the four elements sum to 1_A.
        for i in range(2):
            for j in range(2):
                total = sum(m[i][j][0] for m in case.alice_povm)
                assert total == (1 if i == j else 0), (case.case_id, i, j)
                total_b = sum(m[i][j][0] for m in case.bob_povm)
                assert total_b == (1 if i == j else 0), (case.case_id, i, j)
    dyadic = {case.case_id: case.dyadic for case in BB84_CASES}
    assert dyadic == {
        "BB84-w1-symmetric-dyadic": True,
        "BB84-w2-asymmetric-dyadic": True,
        "BB84-w3-non-dyadic": False,
    }
    # The non-dyadic case genuinely has an odd denominator somewhere.
    non_dyadic = next(case for case in BB84_CASES if not case.dyadic)
    denominators = {value.denominator for row in non_dyadic.joint for value in row}
    assert any(d % 2 == 1 for d in denominators), denominators
    # The asymmetric case genuinely has the two parties' biases differ.
    asymmetric = next(
        case for case in BB84_CASES if case.case_id == "BB84-w2-asymmetric-dyadic"
    )
    assert asymmetric.alice_weights != asymmetric.bob_weights
    assert asymmetric.alice_weights[0] != asymmetric.alice_weights[1]


@pytest.mark.contract
def test_bb84_d_verdicts_and_gate_verdicts() -> None:
    conditions = tuple(name for name, _, _ in BB84_D_VERDICTS)
    assert conditions == (
        "D(i)",
        "D(ii)",
        "D(iii)",
        "D(iv)",
        "D(v)",
        "D(vi)",
        "D(vii)",
        "D(viii)",
    )
    assert all(holds for _, holds, _ in BB84_D_VERDICTS)
    for name, _, route in BB84_D_VERDICTS:
        assert len(route.strip()) > 40, name
    gates = {
        name: (engaged, verdict) for name, engaged, verdict, _ in BB84_GATE_VERDICTS
    }
    assert gates["G1"] == (True, "passed")
    assert gates["G2"] == (True, "passed")
    assert gates["G3a"] == (False, None)
    assert gates["G3b"] == (False, None)
    for _, _, verdict, note in BB84_GATE_VERDICTS:
        if verdict is not None:
            assert verdict in GATE_VERDICT_VOCABULARY
        assert note.strip()
    # The instance lands in exactly one case of the PC-G enumeration.
    case = next(c for c in GATE_CASES if c.case_id == "G-T-D2-CERT-M0")
    enumerated = {name: verdict for name, _, verdict in case.gates}
    assert enumerated["G2"] == "passed"
    assert case.emits_source_replacement_license is True


@pytest.mark.contract
def test_the_bb84_elements_are_real_so_the_conjugation_is_invisible() -> None:
    """Remark rem:bb84checks: this instance CANNOT catch a reversed convention."""
    for case in BB84_CASES:
        for matrix in (*case.alice_povm, *case.bob_povm):
            for real, imaginary in _entries(matrix):
                assert imaginary == 0, case.case_id
                assert isinstance(real, Fraction), case.case_id
    # A real matrix equals its own entrywise complex conjugate, so the two
    # conventions emit the SAME element here and no test built on this instance
    # can discriminate. That is why Group PC-J exists.


@pytest.mark.contract
def test_the_conjugation_branches_genuinely_differ() -> None:
    """Example ex:conj: THE BRANCH PAIR IS THE POINT."""
    assert len(CONJUGATION_BRANCHES) == 2
    contract_branch, omitted = CONJUGATION_BRANCHES
    assert contract_branch.convention == "contract"
    assert omitted.convention == "omitted"
    # 1. The emitted elements differ -- and only in the imaginary parts.
    assert contract_branch.emitted_element != omitted.emitted_element
    for (r1, i1), (r2, i2) in zip(
        _entries(contract_branch.emitted_element),
        _entries(omitted.emitted_element),
        strict=True,
    ):
        assert r1 == r2
        assert i1 == -i2
    # The signal is GENUINELY COMPLEX, which the BB84 set is not.
    assert any(i != 0 for _, i in _entries(contract_branch.emitted_element))
    # 2. The (SR2) verdicts differ, and each matches its own computation.
    assert contract_branch.sr2_holds is True
    assert omitted.sr2_holds is False
    assert contract_branch.sr2_computed == contract_branch.sr2_expected
    assert omitted.sr2_computed != omitted.sr2_expected
    # Both branches are checked against the SAME requirement.
    assert contract_branch.sr2_expected == omitted.sr2_expected
    # 3. The matched-basis joint distributions differ: diagonal against
    #    anti-diagonal -- a noiseless channel at error rate one.
    correct = contract_branch.matched_basis_joint
    reversed_ = omitted.matched_basis_joint
    assert correct != reversed_
    assert correct[0][0] == reversed_[0][1]
    assert correct[0][1] == reversed_[0][0]
    assert correct[0][1] == 0 and correct[1][0] == 0
    assert reversed_[0][0] == 0 and reversed_[1][1] == 0
    for table in (correct, reversed_):
        assert sum(sum(row) for row in table) == Fraction(1, 4)
