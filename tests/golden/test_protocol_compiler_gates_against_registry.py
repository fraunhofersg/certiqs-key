"""The emission gates against the FROZEN exhaustive enumeration (PC9).

``tests/oracles/registry_protocol_compiler.py`` calls Group PC-G "THE BAND'S
TOP-RISK ITEM", and says why: "The claim being frozen is not that some cases
behave as stated but that THE CASE SPACE IS COVERED: every point of the
seven-axis product is either ruled out by a NAMED consistency rule derived from
the contract, or matched by EXACTLY ONE case."

This file is the other half of that claim. The registry's own integrity test
proves the FROZEN cases total over the 192 product points; these tests prove
that :func:`certiqs_key.protocol_compiler.gates.resolve_gates` -- the CODE -- agrees
with
the frozen case at every one of the 86 reachable points, and that the code is
itself total there. A disagreement is a finding against this code, never
against the registry.

WHAT IS ASSERTED PER POINT
==========================
The outcome kind, the emitted source mode, ``key_length_eligible``, whether the
source-replacement licence is emitted, whether the fallback is recorded, and
the FULL four-entry gate report -- engagement and verdict per gate, with the
three-valued vocabulary and no fourth token. Not a summary of the report: the
report IS an output key of Section 2.2, and a test that checked only the flag
would leave the most misleading combination in the enumeration unchecked
(``G-T-D1-M1-NOLIC``, where three of four lines read well and the only
substantive gate is the one that failed).
"""

from __future__ import annotations

import itertools
from fractions import Fraction as F

import pytest
from protocol_blocks import (
    as_blocks,
    family_as_blocks,
    joint_as_blocks,
)
from registry_protocol_compiler import (
    DIMENSION_ONE_EQUALITIES,
    FEASIBLE_SET_COMPARISONS,
    GATE_AXES,
    GATE_CASES,
    GATE_CONSISTENCY_RULES,
    GATE_VERDICT_VOCABULARY,
    GateCase,
    GateConsistencyRule,
)

from certiqs_key.domain.constraints import ConstraintEntry, Relation, RhsTag
from certiqs_key.foundations.blocks import BlockKind, BlockOperator, SectorStructure
from certiqs_key.foundations.errors import MalformedInputError
from certiqs_key.foundations.exact import equal, matrix, scale
from certiqs_key.protocol_compiler import (
    CertificateState,
    EmissionOutcome,
    GateId,
    GateInputs,
    GateVerdict,
    SourceMode,
    licensed_for_the_emitted_mode,
    resolve_gates,
)
from certiqs_key.protocol_compiler.feasibility import trusted_rhs

#: The block kind every fixture below declares: the shared format's
#: ``proof_sector`` (:class:`~certiqs_key.foundations.blocks.BlockKind`,
#: spec/architecture.md 2.9, a frozen type of the shared format). The contract
#: NAMES the datum and the format FIXES the values, so open choice
#: ``OC-sector-block-kind`` is narrowed within that alphabet and still not
#: decided. ``proof_sector`` is the member these fixtures ARE: their
#: decomposition is "justified by dephasing or SOURCE REPLACEMENT", not photon
#: number (``physical_sector``) and not solver sparsity (``numerical_block``).
#: See :func:`instances.bb84.specification.band_a_block_kind` for the reading.
FIXTURE_BLOCK_KIND = BlockKind.PROOF_SECTOR

#: The ``d_A = 1`` fixture's map: one sector of dimension one.
_UNIT_MAP = SectorStructure(labels=("s0",), dims=(1,), block_kind=FIXTURE_BLOCK_KIND)

#: The qubit fixture's map.
_QUBIT_MAP = SectorStructure(labels=("s0",), dims=(2,), block_kind=FIXTURE_BLOCK_KIND)

pytestmark = [pytest.mark.contract, pytest.mark.oracle]


# ---------------------------------------------------------------------------
#  The seven axes, and the translation from a frozen axis value to an input
# ---------------------------------------------------------------------------

AXIS_NAMES = tuple(name for name, _ in GATE_AXES)


def _point_to_inputs(point: dict[str, str]) -> GateInputs:
    """Return the :class:`GateInputs` one product point denotes.

    THE FROZEN `request` AXIS BECOMES THE EMITTED MODE. There is no
    `source_mode_request` input: the mode is read off the
    transmitter artefact's marginal slot, and what the artefact emits
    for a given point is -- trusted when the request was
    trusted AND either a certificate is present or d_A = 1, where the
    transmitter fills the slot with the unique marginal
    (transmitter/rem:da1). THE FROZEN AXIS IS NOT EDITED; it is READ
    one step further along the pipeline.
    """
    trusted_request = point["request"] == "trusted"
    certificate = CertificateState(point["certificate"])
    alice_dim = 1 if point["alice_dim"] == "1" else 2
    emitted_trusted = trusted_request and (
        certificate is not CertificateState.ABSENT or alice_dim == 1
    )
    return GateInputs(
        validator_passed=point["validator"] == "pass",
        emitted_mode=(
            SourceMode.TRUSTED if emitted_trusted else SourceMode.UNTRUSTED
        ),
        alice_dim=alice_dim,
        certificate=certificate,
        has_constraint_entries=point["m"] == ">=1",
        list_licensed=point["list"] == "licensed",
        license_present=point["license"] == "present",
    )


def _excluded_by(point: dict[str, str]) -> GateConsistencyRule | None:
    """Return the consistency rule that rules a point out, or ``None``."""
    for rule in GATE_CONSISTENCY_RULES:
        if all(point[axis] in values for axis, values in rule.pattern):
            return rule
    return None


def _matching_case(point: dict[str, str]) -> GateCase | None:
    """Return the single frozen case a point matches, or ``None``."""
    matches = [
        case
        for case in GATE_CASES
        if all(point[axis] in values for axis, values in case.axes)
    ]
    if not matches:
        return None
    assert len(matches) == 1, (point, [case.case_id for case in matches])
    return matches[0]


def _all_points() -> list[dict[str, str]]:
    """Return the full seven-axis product: 2*2*2*3*2*2*2 = 192 points."""
    values = [values for _, values in GATE_AXES]
    return [
        dict(zip(AXIS_NAMES, combination, strict=True))
        for combination in itertools.product(*values)
    ]


#: THE TWO FROZEN CASES THAT THE ABSENCE OF A FALLBACK MAKES UNREACHABLE.
#: Both stood on a TRUSTED-MODE REQUEST at d_A >= 2 whose certificate
#: was ABSENT -- row 2 of the gate outcome table, served by an
#: untrusted emission with the fallback recorded, and row 4, refused.
#: The transmitter refuses such a request BEFORE AN ARTEFACT EXISTS
#: (`trusted_mode_without_certificate`), so no artefact this module
#: receives satisfies their premise and neither row is reachable
#: (req:gate-outcomes).
#:
#: THE FROZEN CASES ARE NOT EDITED AND NOT DELETED. They are correct
#: evidence of what the frozen contract said, and the registry
#: is never regenerated from the code it tests (PRINCIPLES.md section
#: 2.3). They are SUPERSEDED BY SCOPE, exactly as the d_A = 1 vacuous
#: pass already is in the same enumeration, and
#: :func:`test_the_unreachable_cases_are_refused_and_say_so` is
#: where that is asserted rather than assumed.
UNREACHABLE_CASES = (
    "G-T-D2-NOCERT-M0-FALLBACK",
    "G-T-D2-NOCERT-M1-REFUSE",
)

REACHABLE = [
    (point, case)
    for point in _all_points()
    if _excluded_by(point) is None
    and (case := _matching_case(point)) is not None
    and case.case_id not in UNREACHABLE_CASES
]


#: One readable id per reachable point, precomputed: pytest resolves an ``ids``
#: CALLABLE per argument, and a dict argument has no id of its own.
REACHABLE_IDS = [
    f"{case.case_id}.{'-'.join(point[axis] for axis in AXIS_NAMES)}"
    for point, case in REACHABLE
]


# ---------------------------------------------------------------------------
#  The enumeration is what it says it is
# ---------------------------------------------------------------------------


def test_the_product_partitions_into_excluded_and_matched_points() -> None:
    points = _all_points()
    assert len(points) == 192
    excluded = [point for point in points if _excluded_by(point) is not None]
    matched = [
        point
        for point in points
        if _excluded_by(point) is None and _matching_case(point) is not None
    ]
    unaccounted = [
        point
        for point in points
        if _excluded_by(point) is None and _matching_case(point) is None
    ]
    assert unaccounted == []
    assert len(excluded) == 106
    assert len(matched) == 86
    assert len(excluded) + len(matched) == 192
    assert len(GATE_CASES) == 16
    # THE PARTITION IS THE FROZEN ONE: what differs
    # is which of the sixteen cases a REAL ARTEFACT can
    # present, not how the seven axes partition. The two cases of
    # UNREACHABLE_CASES are matched here and unreachable below.
    retired = [
        point
        for point in points
        if _excluded_by(point) is None
        and (case := _matching_case(point)) is not None
        and case.case_id in UNREACHABLE_CASES
    ]
    assert len(REACHABLE) + len(retired) == len(matched)


# ---------------------------------------------------------------------------
#  The code agrees with the frozen case at every reachable point
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(("point", "case"), REACHABLE, ids=REACHABLE_IDS)
def test_the_gate_mapping_matches_the_frozen_case(
    point: dict[str, str], case: GateCase
) -> None:
    resolution = resolve_gates(_point_to_inputs(point), "V3")

    assert str(resolution.case) == case.case_id
    assert str(resolution.outcome) == case.outcome
    if case.emitted_mode is None:
        assert resolution.emitted_mode is None
    else:
        assert resolution.emitted_mode is not None
        assert str(resolution.emitted_mode) == case.emitted_mode
    assert resolution.key_length_eligible == case.key_length_eligible
    # NO RESOLUTION RECORDS A FALLBACK and none of the
    # reachable frozen cases claims one: the only case that does is in
    # UNREACHABLE_CASES. GateReport has no such field,
    # and its absence is asserted rather than assumed.
    assert case.fallback_recorded is False
    assert not hasattr(resolution.report, "fallback")
    assert not hasattr(resolution, "fallback_recorded")
    assert (
        resolution.emits_source_replacement_license
        is case.emits_source_replacement_license
    )
    assert (resolution.refusal is not None) is (case.outcome == "refusal")

    for gate, engaged, verdict in case.gates:
        entry = resolution.report.entry(GateId(gate))
        assert entry.engaged == engaged, gate
        if (
            gate == "G3a"
            and verdict == "passed vacuously"
            and point["alice_dim"] == "1"
            and point["request"] == "trusted"
        ):
            # THE d_A = 1 VACUOUS PASS IS WITHDRAWN AT 0.3.0 and this frozen
            # cell is superseded BY SCOPE (`SUPERSEDED_BY_SCOPE_0_3_0`,
            # GATE_CASES). Remark ``rem:degenerate``: "Under the operator form
            # of 0.1.4--0.2.0 it WAS vacuous there ...; UNDER THE DECLARED TAG
            # IT IS NOT, because an entry tagged `general` DECLARES A MATRIX
            # AND FAILS A TYPE CHECK AT EVERY DIMENSION ... THIS MODULE TAKES
            # THE STRICTER READING." So the gate is genuinely decided at
            # d_A = 1 and `passed vacuously` survives IN UNTRUSTED-SOURCE MODE
            # ONLY. The withdrawal is fail-closed -- it can only emit
            # KLE = false where the other reading emits true.
            assert entry.verdict is not None, gate
            assert str(entry.verdict) in {"passed", "failed"}, gate
            assert entry.degeneration is None, gate
            continue
        if verdict is None:
            assert entry.verdict is None, gate
        else:
            assert entry.verdict is not None, gate
            assert str(entry.verdict) == verdict, gate


@pytest.mark.parametrize(("point", "case"), REACHABLE, ids=REACHABLE_IDS)
def test_no_fourth_token_and_no_orphan_degeneration(
    point: dict[str, str], case: GateCase
) -> None:
    """Section 2.2 fixes exactly three tokens; rem:degenerate fixes the record."""
    resolution = resolve_gates(_point_to_inputs(point), "V3")
    for entry in resolution.report.entries:
        if entry.verdict is not None:
            assert str(entry.verdict) in GATE_VERDICT_VOCABULARY
        # The degeneration record accompanies the third token and nothing else.
        assert (entry.degeneration is not None) is (
            entry.verdict is GateVerdict.PASSED_VACUOUSLY
        )
    assert case.case_id  # the frozen case is what the parametrization named


# ---------------------------------------------------------------------------
#  The consistency rules are respected BY THE CODE, not only by the registry
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("rule", GATE_CONSISTENCY_RULES, ids=lambda r: r.rule_id)
def test_the_input_typing_rules_are_enforced_or_unreachable(
    rule: GateConsistencyRule,
) -> None:
    """CR1 and CR2 are refused as input typing; CR3a-c are unreachable in fact."""
    points = [
        point
        for point in _all_points()
        if all(point[axis] in values for axis, values in rule.pattern)
    ]
    assert points, rule.rule_id
    if rule.rule_id in {"CR1", "CR2"}:
        # An input-typing fact: no clause can be read against such a point, so
        # GateInputs refuses it rather than giving it an outcome.
        for point in points:
            with pytest.raises(MalformedInputError):
                _point_to_inputs(point)
        return
    # CR3a-c are facts about what the DATA can be, conditional on the validator
    # passing, and each is stated on a region CR1/CR2 may also touch -- CR3a
    # does not constrain the certificate axis, for instance. On the points that
    # remain EXPRESSIBLE the code still answers, which is totality, and the
    # answer is the one the enumeration gives that region.
    expressible = 0
    for point in points:
        if _excluded_by(point) is not None and _excluded_by(point).rule_id in {
            "CR1",
            "CR2",
        }:
            with pytest.raises(MalformedInputError):
                _point_to_inputs(point)
            continue
        expressible += 1
        resolution = resolve_gates(_point_to_inputs(point), "V3")
        assert resolution.outcome in tuple(EmissionOutcome)
    assert expressible > 0, rule.rule_id


def test_cr3_regions_are_unreachable_from_real_declarations() -> None:
    """The three CR3 rules are consequences of the licensing test, not stipulations."""
    tau = matrix(((F(3, 4), 0), (0, F(1, 4))))
    scalar_entry = ConstraintEntry(
        operator=matrix(((1, 0), (0, 0))), relation=Relation.GE, rhs=F(1, 4)
    )
    licensed_entry = ConstraintEntry(
        operator=matrix(((1, 0), (0, 0))),
        relation=Relation.GE,
        rhs=scale(F(1, 4), tau),
    )
    # CR3a: in untrusted mode a scalar-typed list is licensed by construction.
    assert licensed_for_the_emitted_mode(None, (scalar_entry,)) is True
    # AT d_A = 1 A `general`-TAGGED ENTRY IS STILL UNLICENSED AT 0.3.0, and
    # that is the withdrawal Remark ``rem:degenerate`` states: "an entry tagged
    # `general` DECLARES A MATRIX AND FAILS A TYPE CHECK AT EVERY DIMENSION."
    # Through 0.2.0 this returned True because every 1x1 Hermitian entry is a
    # multiple of tau_A = [1] -- a NUMERICAL argument the type check does not
    # make (`SUPERSEDED_BY_SCOPE_0_3_0`, GATE_CASES and O-PC-GATES).
    unit = matrix(((1,),))
    one_by_one = ConstraintEntry(
        operator=BlockOperator.of(_UNIT_MAP, (matrix(((1,),)),)),
        relation=Relation.GE,
        rhs=matrix(((F(7, 3),),)),
    )
    assert one_by_one.tag is RhsTag.GENERAL
    assert licensed_for_the_emitted_mode(unit, (one_by_one,)) is False
    # AND THE SCALAR FORM IS LICENSED AT EVERY d_A, which is the other half of
    # the contract: "A REAL SCALAR RIGHT-HAND SIDE IS ACCEPTED IN
    # TRUSTED-SOURCE MODE AT EVERY d_A, and is the LICENSED FORM there."
    homogeneous = ConstraintEntry(
        operator=BlockOperator.of(_UNIT_MAP, (matrix(((1,),)),)),
        relation=Relation.GE,
        rhs=F(7, 3),
    )
    assert homogeneous.tag is RhsTag.HOMOGENEOUS
    assert licensed_for_the_emitted_mode(unit, (homogeneous,)) is True
    # CR3c IS UNREACHABLE AND IS NOT ASSERTED OF THE CODE.
    # It reads "a trusted REQUEST with no tau_A cannot license a non-empty
    # list", and it is the ONE corner for which a licensing
    # test would take the request as well as the slot. The transmitter refuses a
    # trusted-mode request without a certificate at d_A >= 2 before an
    # artefact exists, so there is no trusted emission with no tau_A for the
    # question to be asked of, and `licensed_for_the_emitted_mode` reads the
    # emitted slot alone. What IS
    # true, and is what the licensed_entry exhibits, is that a matrix-tagged
    # entry is unlicensed whatever the slot holds.
    assert licensed_entry.tag is RhsTag.GENERAL
    assert licensed_for_the_emitted_mode(tau, (licensed_entry,)) is False
    assert licensed_for_the_emitted_mode(None, (licensed_entry,)) is False
    # CR1: the empty list is licensed vacuously, in every mode.
    assert licensed_for_the_emitted_mode(None, ()) is True
    assert licensed_for_the_emitted_mode(tau, ()) is True


def test_the_unreachable_cases_are_refused_and_say_so() -> None:
    """Rows 2 and 4: refused by the transmitter, refused by type here.

    There is no fallback, so what is asserted is its absence: an artefact
    claiming trusted mode at ``d_A >= 2`` with no certificate is not a
    presentation of an input this module types, and no clause of
    ``def:eligible`` can be read against it.
    """
    with pytest.raises(MalformedInputError) as raised:
        GateInputs(
            validator_passed=True,
            emitted_mode=SourceMode.TRUSTED,
            alice_dim=2,
            certificate=CertificateState.ABSENT,
            has_constraint_entries=False,
            list_licensed=True,
            license_present=False,
        )
    assert "trusted_mode_without_certificate" in str(raised.value)
    assert "UNREACHABLE" in str(raised.value)
    # And no resolution this module can produce carries either case id.
    produced = {str(resolve_gates(_point_to_inputs(point), "V3").case) for point, _ in
    REACHABLE}
    assert produced.isdisjoint(UNREACHABLE_CASES)
    # The two cases ARE in the frozen enumeration, which is not edited.
    assert set(UNREACHABLE_CASES) <= {case.case_id for case in GATE_CASES}


# ---------------------------------------------------------------------------
#  Remark rem:degenerate: the two vacuous passes, and where (G3)(a) is genuine
# ---------------------------------------------------------------------------


def test_the_two_vacuous_passes_and_the_one_genuine_pass() -> None:
    """The enumeration's own countable fact about (G3)(a), asserted of the CODE."""
    genuine: list[str] = []
    vacuous: list[str] = []
    failed: list[str] = []
    for point, case in REACHABLE:
        resolution = resolve_gates(_point_to_inputs(point), "V3")
        entry = resolution.report.entry(GateId.G3A)
        if entry.verdict is GateVerdict.PASSED:
            genuine.append(case.case_id)
        elif entry.verdict is GateVerdict.PASSED_VACUOUSLY:
            vacuous.append(case.case_id)
        elif entry.verdict is GateVerdict.FAILED:
            failed.append(case.case_id)
    # "A GENUINE (non-vacuous) (G3)(a) = `passed' occurs in exactly TWO of the
    # sixteen cases -- this one and G-T-D2-CERT-M1-LIC-NOLICENCE".
    # 0.3.0 MOVES FOUR CELLS FROM `passed vacuously` TO A GENUINE VERDICT: the
    # two d_A = 1 trusted rows now decide (G3)(a) as a type check on the tag
    # rather than passing it vacuously. The two that were genuine still are.
    assert set(genuine) == {
        "G-T-D2-CERT-M1-LIC-LICENCE",
        "G-T-D2-CERT-M1-LIC-NOLICENCE",
        "G-T-D1-M1-LIC",
        "G-T-D1-M1-NOLIC",
    }
    # "Everywhere else (G3)(a) is `passed vacuously' (four cases), `failed'
    # (two cases), or not engaged."
    # `passed vacuously` SURVIVES IN UNTRUSTED-SOURCE MODE ONLY: four cases at
    # 0.1.4, TWO at 0.3.0, the two trusted d_A = 1 rows having moved to a
    # genuine verdict with the withdrawal of the first degeneration.
    assert set(vacuous) == {"G-U-M1-LIC", "G-U-M1-NOLIC"}
    assert set(failed) == {
        "G-T-D2-CERT-M1-UNLIC-LICENCE",
        "G-T-D2-CERT-M1-UNLIC-NOLICENCE",
    }


def test_a_vacuous_pass_carries_its_degeneration_record_and_is_not_evidence() -> None:
    untrusted = resolve_gates(
        GateInputs(
            validator_passed=True,
            emitted_mode=SourceMode.UNTRUSTED,
            alice_dim=2,
            certificate=CertificateState.ABSENT,
            has_constraint_entries=True,
            list_licensed=True,
            license_present=True,
        )
    )
    dimension_one = resolve_gates(
        GateInputs(
            validator_passed=True,
            emitted_mode=SourceMode.TRUSTED,
            alice_dim=1,
            certificate=CertificateState.ABSENT,
            has_constraint_entries=True,
            list_licensed=True,
            license_present=True,
        )
    )
    # `passed vacuously` IS EMITTED IN UNTRUSTED-SOURCE MODE ONLY, at any d_A,
    # and NOT at d_A = 1 in trusted mode: the FIRST case of Remark
    # ``rem:degenerate`` is withdrawn at 0.3.0 and only the second survives.
    entry = untrusted.report.entry(GateId.G3A)
    assert entry.verdict is GateVerdict.PASSED_VACUOUSLY
    assert entry.degeneration is not None
    assert "second case" in entry.degeneration
    assert "NOT evidence of anything" in entry.degeneration
    dimension_one_entry = dimension_one.report.entry(GateId.G3A)
    assert dimension_one_entry.verdict is not GateVerdict.PASSED_VACUOUSLY
    assert dimension_one_entry.degeneration is None
    for resolution, marker in ((untrusted, "second case"),):
        entry = resolution.report.entry(GateId.G3A)
        assert entry.verdict is GateVerdict.PASSED_VACUOUSLY
        assert entry.degeneration is not None
        assert marker in entry.degeneration
        assert "NOT evidence of anything" in entry.degeneration
        # The token does not collapse into a boolean anywhere on the surface.
        assert not hasattr(entry, "passed")
        assert str(entry.verdict) != "passed"


def test_passed_vacuously_still_permits_eligibility_without_being_passed() -> None:
    """The one accessor that reads a vacuous pass, and what it is for."""
    resolution = resolve_gates(
        GateInputs(
            validator_passed=True,
            emitted_mode=SourceMode.UNTRUSTED,
            alice_dim=2,
            certificate=CertificateState.ABSENT,
            has_constraint_entries=True,
            list_licensed=True,
            license_present=True,
        )
    )
    entry = resolution.report.entry(GateId.G3A)
    assert entry.permits_eligibility is True
    assert entry.verdict is not GateVerdict.PASSED
    assert resolution.key_length_eligible is True


# ---------------------------------------------------------------------------
#  prop:conservative, which keeps its mathematics and is not a rule
#  of emission
# ---------------------------------------------------------------------------


def test_prop_conservative_pointwise_on_the_frozen_licensed_list() -> None:
    """The inclusion the fallback rests on, verified where the gate uses it."""
    from certiqs_key.foundations.blocks import SectorStructure
    from certiqs_key.protocol_compiler import CandidateDeclaration, Party
    from certiqs_key.protocol_compiler import in_feasible_set as feasible
    from certiqs_key.protocol_compiler.spec import default_party_partition

    def _declaration(
        marginal: object, entries: tuple[ConstraintEntry, ...]
    ) -> CandidateDeclaration:
        alphabet = ("x0", "x1")
        return CandidateDeclaration(
            alice_dim=2,
            alice_marginal=marginal,  # type: ignore[arg-type]
            sectors=SectorStructure(
                labels=("s0",), dims=(2,), block_kind=FIXTURE_BLOCK_KIND
            ),
            alice_alphabet=alphabet,
            alice_povm={
                "x0": matrix(((1, 0), (0, 0))),
                "x1": matrix(((0, 0), (0, 1))),
            },
            bob_alphabet=alphabet,
            bob_povm=family_as_blocks(
                _QUBIT_MAP,
                {
                    "x0": matrix(((1, 0), (0, 0))),
                    "x1": matrix(((0, 0), (0, 1))),
                },
            ),
            partition=default_party_partition(alphabet, alphabet),
            announce_alice=dict.fromkeys(alphabet, "a"),
            announce_bob=dict.fromkeys(alphabet, "b"),
            alice_announcement_alphabet=("a",),
            bob_announcement_alphabet=("b",),
            acceptance_alphabet=("c",),
            accept_statistic={("a", "b"): "c"},
            key_map={(x, v): 0 for x in alphabet for v in alphabet},
            key_alphabet=(0,),
            key_holder=Party.ALICE,
            constraint_list=entries,
        )

    for case in FEASIBLE_SET_COMPARISONS:
        if case.tau_a is None:
            continue
        tau = _reg(case.tau_a)
        # THE LICENSED TRUSTED-MODE ENTRY CARRIES THE SCALAR c_k AT 0.3.0, and
        # "the right-hand side it denotes is then CONSTRUCTED as
        # Theta_k := c_k tau_A from the declared c_k and the declared tau_A"
        # (Definition def:homog (a)). The frozen `trusted_rhs` matrix is
        # exactly that construction, and it is asserted below rather than
        # declared -- which is a STRONGER reading of the same frozen value.
        trusted_entries = tuple(
            ConstraintEntry(
                operator=as_blocks(_QUBIT_MAP, _reg(operator)),
                relation=Relation.GE,
                rhs=scalar,
            )
            for operator, _relation, _trusted_rhs, scalar in case.licensed_entries
        )
        untrusted_entries = tuple(
            ConstraintEntry(
                operator=as_blocks(_QUBIT_MAP, _reg(operator)),
                relation=Relation.GE,
                rhs=scalar,
            )
            for operator, _relation, _trusted_rhs, scalar in case.licensed_entries
        )
        trusted_declaration = _declaration(tau, trusted_entries)
        # The construction c_k tau_A, checked against the frozen matrix.
        for entry, (_op, _rel, frozen_rhs, _scalar) in zip(
            trusted_entries, case.licensed_entries, strict=True
        ):
            assert equal(trusted_rhs(trusted_declaration, entry), _reg(frozen_rhs))
        state = joint_as_blocks(_QUBIT_MAP, 2, _reg(case.state))
        assert feasible(trusted_declaration, state) is case.in_trusted_set
        assert feasible(_declaration(None, untrusted_entries), state) is (
            case.in_untrusted_set
        )
        # A LICENSED list, which is what prop:conservative requires.
        assert licensed_for_the_emitted_mode(tau, trusted_entries) is True


def test_rem_notfallback_no_module_substitutes_a_marginal() -> None:
    """``1_A / d_A`` is never manufactured, at any dimension above one.

    The slot is the transmitter artefact's and this module passes
    it through, filling nothing. So the assertion is about the module that
    owns the decision, and the compiler's half of it -- that it fills no slot
    -- is asserted beside it.
    """
    from certiqs_key.transmitter.artifact import emit_artifact

    for dim in (2, 3, 4):
        request = _trusted_request_without_a_certificate(dim)
        result = emit_artifact(request)
        assert result.artifact is None, dim
        assert result.refusal is not None, dim
        assert str(result.refusal.reason) == "trusted_mode_without_certificate", dim
    # At d_A = 1 the slot IS filled -- with the UNIQUE element of S_=(A),
    # which is not a substituted default (transmitter/rem:da1) -- AND THE FILL
    # IS RECORDED.
    served = emit_artifact(_trusted_request_without_a_certificate(1)).require()
    assert served.alice_marginal == matrix(((1,),))
    assert served.marginal_slot_filled is True
    assert str(served.source_mode) == "trusted"
    # THE COMPILER FILLS NO SLOT AND HAS NO FUNCTION THAT COULD.
    import certiqs_key.protocol_compiler.gates as gates_module

    assert not hasattr(gates_module, "emitted_marginal")


def _trusted_request_without_a_certificate(dim: int) -> object:
    """Return a trusted-mode request whose marginal slot is empty."""
    from certiqs_key.transmitter.artifact import SourceSpecification
    from certiqs_key.transmitter.reasons import SourceMode as TxSourceMode

    identity_element = tuple(
        tuple(F(1) if i == j else F(0) for j in range(dim)) for i in range(dim)
    )
    return SourceSpecification(
        signal_alphabet=("x0",),
        alice_dim=dim,
        alice_povm={"x0": matrix(identity_element)},
        transmitted_dim=2,
        signal_weights={"x0": F(1)},
        signal_states={"x0": matrix(((1, 0), (0, 0)))},
        source_mode_request=TxSourceMode.TRUSTED,
    )


def test_rem_da1_the_two_feasible_sets_coincide_at_dimension_one() -> None:
    """The registry's own d_A = 1 pair, asserted against the filled slot."""
    from certiqs_key.transmitter.artifact import emit_artifact

    served = emit_artifact(_trusted_request_without_a_certificate(1)).require()
    for case in DIMENSION_ONE_EQUALITIES:
        assert served.alice_marginal == _reg(case.tau_a)
        # The frozen verdicts coincide, which is what "the two feasible sets
        # are EQUAL" means (transmitter/rem:da1).
        assert case.in_trusted_set == case.in_untrusted_set


def _reg(frozen: object) -> object:
    """Return a frozen registry matrix in the implementation's substrate."""
    from certiqs_key.foundations.exact import Cx

    assert isinstance(frozen, tuple)
    return tuple(
        tuple(Cx(entry[0], entry[1]) for entry in row)  # type: ignore[index]
        for row in frozen
    )
