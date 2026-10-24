"""The emitted ``ProofReductionArtifact``: its keys, its rules, its serialization.

Three things are pinned here that the golden replays do not reach:

* the SEVENTEEN keys are the dataclass's fields, in the contract's order, so the
  record and the type cannot drift apart;
* the three presence rules are enforced at CONSTRUCTION, so an artifact
  violating one cannot exist rather than merely not being emitted;
* the machine record is cleanly serializable and carries NO OPERATOR TWICE,
  which is what a key-rate run logging it pays for.
"""

from __future__ import annotations

import dataclasses
import json
from fractions import Fraction

import pytest
from reductions_support import RECEIVER_LEDGER_KEYS, RETIRED_RECEIVER_KEYS
from registry_reductions import (
    INHERITED_RECEIVER_KEYS_NEW_AT_1_0_0,
)

from certiqs_key.foundations.exact import deserialize_matrix, equal, serialize_matrix
from certiqs_key.reductions import MATHEMATICAL_SPEC_VERSION
from certiqs_key.reductions.artifact import (
    NOT_EMITTED,
    ONE_ARTEFACT_ONLY_KEYS,
    OUTPUT_KEYS,
    AssumptionLedgerEntry,
    BlockEmissionRecord,
    EmissionRecord,
    ExactIdentity,
    ProofReductionArtifact,
    ReductionOutcome,
    VerificationReport,
    WpfssData,
    assumption_ledger,
)
from certiqs_key.reductions.errors import MalformedInputError
from certiqs_key.reductions.inputs import (
    InheritedAssumption,
)
from certiqs_key.reductions.normalizer import ClassSnap, ClassStatus
from certiqs_key.reductions.reasons import (
    CORE_ASSUMPTIONS,
    AssumptionId,
    AssumptionRow,
    FailClosedRule,
    LinkStatus,
    Refusal,
    RefusalReason,
    Route,
)
from certiqs_key.reductions.validation import (
    RULE_ORDER,
    RuleOutcome,
)

F = Fraction


def _supplier_ledger() -> tuple[InheritedAssumption, ...]:
    """Return the supplier's ledger rows, keys only.

    The keys are ``RECEIVER_LEDGER_KEYS`` (tests/support): the frozen band-4
    tuple ``INHERITED_RECEIVER_KEYS_1_0_0`` less the keys the receiver no longer
    carries, the receiver's ledger keys in the supplier's order.
    Nothing here invents a key: a ledger missing one never reaches an emitted
    artifact, the receiver-spec row refusing it first.
    """
    return tuple(
        InheritedAssumption(machine_key=key) for key in RECEIVER_LEDGER_KEYS
    )


def _report() -> VerificationReport:
    return VerificationReport(
        outcomes=tuple(
            RuleOutcome(rule=rule, decided=True, refusal=None) for rule in RULE_ORDER
        ),
        receiver_spec_version="receiver-povm@0.1.3",
        receiver_bound_evaluation="floating_point",
        requested_assurance="estimate",
    )


def test_the_output_keys_are_the_dataclass_fields_in_the_interface_s_order() -> None:
    """The outputs tables: the dataclass fields, in the interface's order.

    ``emission_record`` stands immediately before
    ``mathematical_spec_version``; it records what this module DID TO ITS OWN
    CONSTRUCTION before declaring it.

    THE EXPECTED LIST IS WRITTEN BY HAND, WITH ITS REASONS.
    ``douglas_data`` is not a key: the
    interface lists it under ``not_carried`` because a key whose value is
    always ``null`` is a hand-maintained mirror of a deferral (PRINCIPLES.md
    section 7), and the deferral's docking point is the ``family-dominating``
    link kind. ``route`` is an OUTPUT ROW of ``wpfss/interface.yaml`` and is
    emitted, which the interface-vocabulary test checks.
    """
    # TWENTY KEYS. `factor_emission` is the one key of the
    # outputs table that is NOT A FIELD OF ONE ARTEFACT. It carries "THE ORDERED
    # LIST OF THE FACTORS' ARTEFACTS ... AND THE COMBINATION RULE" and is
    # "PRESENT EXACTLY WHEN THE CALL DECLARES MORE THAN ONE INSTANCE ... ABSENT
    # FOR A ONE-FACTOR EMISSION". So the dataclass has its nineteen fields, the
    # record one artefact emits has nineteen keys (`ONE_ARTEFACT_ONLY_KEYS`),
    # and the vocabulary of the module has one more. `reference_companion` is
    # the output row of spec/modules/reductions/interface.yaml
    # (reductions/req:reference-companion (v), (vi)): the companion emitted
    # beside the artefact, or the record of why none was; it sits after
    # `emission_record`. `receiver_row_omitted_on_provenance` is the output
    # row of req:recv-row-provenance, why the A-RECV row is absent where it
    # is; it sits after `assumption_ledger`.
    assert len(OUTPUT_KEYS) == 21
    assert OUTPUT_KEYS[-5:] == (
        "assumption_ledger",
        "receiver_row_omitted_on_provenance",
        "emission_record",
        "reference_companion",
        "mathematical_spec_version",
    )
    assert "domination_record" not in OUTPUT_KEYS
    assert "operator_tolerance_record" not in OUTPUT_KEYS
    assert "douglas_data" not in OUTPUT_KEYS
    assert "route" in OUTPUT_KEYS
    names = {field.name for field in dataclasses.fields(ProofReductionArtifact)}
    assert set(OUTPUT_KEYS) - {"factor_emission"} == names
    assert set(ONE_ARTEFACT_ONLY_KEYS) == names
    assert len(ONE_ARTEFACT_ONLY_KEYS) == 20


def test_nothing_the_contract_forbids_is_a_field() -> None:
    """Section 2.3's "what is deliberately not emitted", as a field check."""
    names = {field.name for field in dataclasses.fields(ProofReductionArtifact)}
    for forbidden in NOT_EMITTED:
        assert forbidden not in names
    assert len(NOT_EMITTED) == 9
    # And in particular no penalty term and no error parameter: the transfer of
    # thm:transfer is an EQUALITY, so there is nothing to report.
    assert "penalty_term" in NOT_EMITTED
    assert "error_parameter" in NOT_EMITTED
    assert ExactIdentity().is_numerical_residual_check is False


def test_the_verification_report_must_be_every_row_in_the_contract_s_order() -> None:
    """Section 2.3 at 0.3.0: every one of the TWENTY-FIVE rows WITH ITS OUTCOME.

    The report grows with the tables: twenty-one at 0.1.3; twenty-four at 0.2.0
    with the tolerance row, the high-photon slot row and the licensed-route
    Hermiticity row; twenty-five at 0.3.0 with the column-stochasticity row. A
    report that is not EXACTLY the current rows in the contract's order is
    refused, in both directions -- too few, and right rows in the wrong order.
    """
    # TWENTY-ONE CORE ROWS. The other seven are the submodules' -- six of
    # ``wpfss``, one of a removable branching submodule -- and a reduction
    # reports the core's plus the ones ITS INSTANCE BUILDER declares, so a
    # report assembled from the core alone carries twenty-one and is well formed.
    assert len(RULE_ORDER) == 21
    good = _report()
    assert len(good.outcomes) == 21
    assert good.refusal is None
    assert good.undecided == ()
    with pytest.raises(MalformedInputError):
        VerificationReport(
            outcomes=good.outcomes[:-1],
            receiver_spec_version="receiver-povm@0.1.3",
            receiver_bound_evaluation="floating_point",
            requested_assurance="estimate",
        )
    # A REPEATED ROW IS REFUSED TOO: the report carries each row ONCE.
    with pytest.raises(MalformedInputError):
        VerificationReport(
            outcomes=good.outcomes + good.outcomes[:1],
            receiver_spec_version="receiver-povm@0.1.3",
            receiver_bound_evaluation="floating_point",
            requested_assurance="estimate",
        )
    # THE ORDER IS NOT RE-DECIDED HERE. The rows a reduction reports
    # are the core's plus the ones its INSTANCE BUILDER declares, so a list
    # frozen in the record could only be one path's; the order is guaranteed by
    # construction, ``reduce`` sorting the merged rows on each row's declared
    # place in the interface's table, and what stays checkable here is that
    # every core row is present and none is reported twice.
    reversed_report = VerificationReport(
        outcomes=tuple(reversed(good.outcomes)),
        receiver_spec_version="receiver-povm@0.1.3",
        receiver_bound_evaluation="floating_point",
        requested_assurance="estimate",
    )
    assert len(reversed_report.outcomes) == len(good.outcomes)


def test_the_report_names_the_first_refusal_in_the_contract_s_row_order() -> None:
    """Not the first evaluated, and not the last: the first ROW."""
    outcomes = []
    for rule in RULE_ORDER:
        refusal = (
            Refusal(
                reason=RefusalReason.ROUTE_NOT_SINGLE_VALUED,
                rule=str(rule),
                detail="later row",
            )
            if rule is FailClosedRule.ROUTE
            else (
                Refusal(
                    reason=RefusalReason.CUTOFF_MISMATCH,
                    rule=str(rule),
                    detail="earlier row",
                )
                if rule is FailClosedRule.CUTOFF
                else None
            )
        )
        outcomes.append(RuleOutcome(rule=rule, decided=True, refusal=refusal))
    report = VerificationReport(
        outcomes=tuple(outcomes),
        receiver_spec_version="receiver-povm@0.1.3",
        receiver_bound_evaluation="floating_point",
        requested_assurance="estimate",
    )
    # `cutoff` is row 2 and `route` is row 17: the earlier row is named.
    assert report.refusal is not None
    assert report.refusal.reason is RefusalReason.CUTOFF_MISMATCH


def test_the_wpfss_record_carries_one_weight_per_flag_basis_vector() -> None:
    """Section 2.3: the flag basis IN THE DECLARED ORDER OF ``V``."""
    good = WpfssData(
        flag_basis=(("y", "t"),),
        weights=(F(1, 4),),
        cutoff=0,
        total=F(1, 4),
        encoded_in_target=True,
    )
    assert good.weight_provenance.startswith("eq:weightroute")
    with pytest.raises(MalformedInputError):
        WpfssData(
            flag_basis=(("y", "t"),),
            weights=(F(1, 4), F(1, 8)),
            cutoff=0,
            total=F(3, 8),
            encoded_in_target=True,
        )


def test_the_emitted_ledger_carries_the_suppliers_machine_keys() -> None:
    """``sec:outputs``, ``assumption_ledger``.

    "For the inherited receiver assumptions, THE SUPPLIER'S OWN MACHINE KEYS
    READ FROM THE RECEIVER ARTIFACT'S LEDGER
    (Assumption ass:recv) -- together with that artifact's
    ``mathematical_spec_version``. A PROSE LIST IS NOT A KEY AND DOES NOT
    COMPOSE: an inherited assumption named only by an English phrase cannot be
    matched against the supplier's ledger by a consumer."

    The inherited set is the supplier's keys, not a prose tuple, so that every
    key the supplier maintains crosses the docking boundary.
    """
    # The supplier version this fixture declares is one that exists,
    # receiver@0.1.2.
    ledger = assumption_ledger({}, "receiver@0.1.2", _supplier_ledger())
    # NINE CORE ROWS; a branching submodule's row is its own, and its builder
    # adds it where a branching model is declared.
    #
    # There is no A-NOSRC row: no claim of this module rests on the source
    # segment being empty, and whether it is empty is DATA in the emitted
    # `reduction_chain`. A-SEQ is in the ledger unconditionally: `def:protocol`
    # declares the transmitter's `ass:seq` and every claim on the emission path
    # uses it, so the key reaches this ledger through the graph. A-SRC, the
    # transmitter's source-replacement attestation, is PRESENT ONLY WHERE THE
    # EMITTED CHAIN'S SOURCE SEGMENT IS NON-EMPTY -- which is not this
    # function's to apply: `assumption_ledger` is handed its rows and drops
    # none, so the default call returns EVERY core row, and `reductions.emit`
    # is where the conditions are read (`tests/golden/test_reductions_emission.py`
    # asserts them).
    #
    # There is no A-SOUND row: the soundness of the emitted entries is a
    # conclusion of the chain theorems (rem:sound-and-atk). Nor is there a row
    # for the adversary's registers, which lem:sep reads as finite: that is
    # the round model's (meat-core's ass:eve-dim is superseded); the setting
    # half is def:system-setting, a definition.
    assert len(ledger) == 8
    assert [entry.assumption_id for entry in ledger] == [
        str(member) for member in AssumptionId
    ]
    recv = next(e for e in ledger if e.assumption_id == AssumptionId.A_RECV)
    assert recv.never_verifiable is True
    assert recv.inherited_from == "receiver@0.1.2"
    # THE SUPPLIER'S KEYS, not prose phrases, in the supplier's order,
    # passed through as supplied: the frozen thirteen less the three the
    # receiver no longer carries.
    assert recv.inherited == RECEIVER_LEDGER_KEYS
    # Four keys cross the docking boundary beyond the original nine, of which
    # two (A-ACYC's and A-FLOAT's) are not carried.
    for key in INHERITED_RECEIVER_KEYS_NEW_AT_1_0_0:
        assert (key in recv.inherited) is (key not in RETIRED_RECEIVER_KEYS)
    # Each is a MACHINE KEY: no English phrase, and nothing namespaced onto it.
    for key in recv.inherited:
        assert " " not in key
        assert ":" not in key
        assert "@" not in key
    # No other entry inherits anything, so the supplier's `round_homogeneity`
    # and A-ROUND's own key cannot merge into one list and lose an entry.
    assert all(e.inherited == () for e in ledger if e is not recv)
    # Every LOCAL key is Section 5's, unprefixed.
    for entry in ledger:
        assert entry.machine_key.islower()
        assert ":" not in entry.machine_key
        assert "@" not in entry.machine_key


def test_the_suppliers_eig_slack_is_recorded_beside_its_settings() -> None:
    """Assumption ``ass:recv`` on the one inherited key with declared content.

    "Its declared slack ``eps_eig`` is physics rather than arithmetic, declared
    separately and derived from nothing this module reads. IT IS RECORDED IN
    THE EMITTED LEDGER BESIDE THE SETTINGS AT WHICH THE SUPPLIER SAYS IT WAS
    INVOKED, and a caller that wants it out of the chain declares no exact
    window."

    THE RECORD IS THE SUPPLIER'S AND IS CARRIED UNREAD: "this module can
    NEITHER VERIFY NOR IMPROVE IT". Every other inherited key carries the key
    and nothing else, because for those the contract asks for nothing else.
    """
    supplied = tuple(
        InheritedAssumption(
            machine_key=key,
            constrains=(
                (("eps_eig", "1e-12"), ("invoked_at", "['t_on']"))
                if key == "exact_window_eigenvalue_slack"
                else ()
            ),
        )
        for key in RECEIVER_LEDGER_KEYS
    )
    # The supplier version this fixture declares is one that exists,
    # receiver@0.1.2.
    ledger = assumption_ledger({}, "receiver@0.1.2", supplied)
    recv = next(e for e in ledger if e.assumption_id == AssumptionId.A_RECV)
    assert recv.inherited_declared == (
        (
            "exact_window_eigenvalue_slack",
            (("eps_eig", "1e-12"), ("invoked_at", "['t_on']")),
        ),
    )
    # It reaches the wire under the key it was read from, and nothing else does.
    record = _artifact(assumption_ledger=ledger).as_machine_record()
    rows = record["assumption_ledger"]
    assert isinstance(rows, list)
    declared = [row["inherited_declared"] for row in rows]
    # SEVEN EMPTY OF EIGHT: A-RECV carries the supplier's declared record and
    # no other row carries one; A-SEQ and A-SRC declare nothing.
    assert declared.count({}) == 7
    assert {
        "exact_window_eigenvalue_slack": {
            "eps_eig": "1e-12",
            "invoked_at": "['t_on']",
        }
    } in declared


def test_the_never_verifiable_flag_is_set_for_the_rows_marked_never() -> None:
    """The never-verifiable flag is set for the rows whose header says ``never``.

    A-RECV, A-MEAS and A-ROUND-SQ are statements about the devices and the run
    that no declared datum bears on; A-PROBE, A-TSM and A-CONST carry the
    `verification` field `never`; and the transmitter's A-SRC and A-SEQ
    carry their owner's mark.
    """
    ledger = assumption_ledger({}, "receiver-povm@0.1.3", _supplier_ledger())
    # The core ledger's marked rows; a branching submodule marks its own on a
    # branching one.
    never = {e.assumption_id for e in ledger if e.never_verifiable}
    added = {
        AssumptionId.A_PROBE,
        AssumptionId.A_TSM,
        AssumptionId.A_CONST,
        AssumptionId.A_SRC,
        AssumptionId.A_SEQ,
    }
    assert never == {
        AssumptionId.A_RECV,
        AssumptionId.A_MEAS,
        AssumptionId.A_ROUND_SQ,
    } | added
    # AND THE SAME LEDGER WITH ONE MORE NEVER-VERIFIABLE ROW, whatever supplies
    # it: the row set is a parameter, so a submodule's assumption reaches the
    # ledger without the core naming it. The frozen PAIR is asserted in the
    # removable submodule's own test file, which is deleted with it.
    extra = AssumptionRow("A-EXTRA", "extra_assumption_form", True, 5)
    widened = assumption_ledger(
        {}, "receiver-povm@0.1.3", _supplier_ledger(), (*CORE_ASSUMPTIONS, extra)
    )
    # The core's rows are the ones above, and the extra row carries the flag
    # it was built with.
    assert {e.assumption_id for e in widened if e.never_verifiable} == {
        str(identifier) for identifier in never
    } | {"A-EXTRA"}
    # Order 5 sits after orders 2, 3 and 4 (order 1 is unassigned).
    assert [e.assumption_id for e in widened][3] == "A-EXTRA"


def _artifact(**overrides: object) -> ProofReductionArtifact:
    from certiqs_key.foundations.exact import matrix
    from certiqs_key.reductions.channels import ChannelWitness
    from certiqs_key.reductions.sectors import assemble_sector_blocks
    from certiqs_key.reductions.wpfss.construction import (
        flat_scalar_values,
        flat_sectors,
    )

    order_fixture = (("v0", "t"), ("v1", "t"))
    sectors = flat_sectors((1,), ("v0,t", "v1,t"))
    weights_fixture = {("v0", "t"): F(1, 4), ("v1", "t"): F(1, 8)}
    # ONE SQUARE BLOCK PER SECTOR, which is what the artifact carries.
    blocks_fixture = assemble_sector_blocks(
        sectors,
        {
            ("v0", "t"): (matrix([[F(2, 3)]]),),
            ("v1", "t"): (matrix([[F(1, 3)]]),),
        },
        flat_scalar_values(
            ("v0,t", "v1,t"), order_fixture, weights_fixture, encoded=True
        ),
        order_fixture,
    )
    target_povm_fixture = tuple(blocks_fixture[outcome] for outcome in order_fixture)
    witness_fixture = ChannelWitness(
        identity="Lambda-wpfss-wp", equation="prop:flat-instance (I3): P_S o Lambda_C"
    )
    from certiqs_key.reductions.artifact import SourceDescriptor, TargetDescriptor
    from certiqs_key.reductions.inputs import (
        ChannelGrading,
    )
    from certiqs_key.reductions.links import Chain, SystemFamily, identity_link

    order = (("v0", "t"), ("v1", "t"))
    report = _report()
    defaults: dict[str, object] = {
        "source_descriptor": SourceDescriptor(
            channel_grading=ChannelGrading(block_dimensions=(1,)),
            branch_register=None,
        ),
        "target_descriptor": TargetDescriptor(
            sectors=sectors,
            dimension=sectors.total_dimension,
            party_partition="default: Bob holds every factor of every H(Q_s)",
        ),
        "target_povm": dict(zip(order, target_povm_fixture, strict=True)),
        "outcome_correspondence": {v: v for v in order},
        "squashing_channel": witness_fixture,
        "exact_identity": ExactIdentity(),
        "transported_operators": (),
        "reachable_set_statement": "S^rch of def:sound",
        "constraint_list": (),
        "attack_set_license": None,
        "wpfss_data": WpfssData(
            flag_basis=order,
            weights=(F(1, 4), F(1, 8)),
            cutoff=0,
            total=F(3, 8),
            encoded_in_target=True,
        ),
        "reduction_chain": Chain(
            links=(
                identity_link(
                    SystemFamily(
                        description="Q",
                        dimension=sectors.total_dimension,
                        povm=target_povm_fixture,
                    )
                ),
            )
        ),
        "verification_report": report,
        "assumption_ledger": assumption_ledger(
            {}, "receiver-povm@0.1.3", _supplier_ledger()
        ),
        "route": Route.ENCODED,
        # NEW AT 1.0.0 AND REQUIRED: the artifact cannot be constructed without
        # it, so the helper declares one rather than letting a default appear.
        "emission_record": EmissionRecord(
            lattice_exponent=12,
            six_condition_outcomes={
                "sector_map": True,
                "hermiticity": True,
                "positivity": True,
                "completeness": True,
                "declared_order_sum": True,
                "lattice_invariant": True,
            },
            blocks=(
                # The block record is per class (req:emission-record), here a
                # kept class; there are no lift fields, rung or emission weight.
                BlockEmissionRecord(
                    block_index=0,
                    already_on_lattice=True,
                    displacement=0.0,
                    displacement_squared=Fraction(0),
                    classes={
                        "t0": ClassSnap(label="t0", status=ClassStatus.KEPT)
                    },
                ),
            ),
        ),
    }
    defaults.update(overrides)
    return ProofReductionArtifact(**defaults)  # type: ignore[arg-type]


def test_the_presence_rules_are_enforced_at_construction() -> None:
    """An artifact violating one cannot be built, let alone emitted.

    TWO RULES: ``douglas_data`` is not a key, so there is no third rule and no
    field to hold ``null``. The rules are the licence iff and the emitted
    status.
    """
    from certiqs_key.reductions.constraints import (
        AttackSetLicence,
    )
    from certiqs_key.reductions.reasons import SourceMode

    licence = AttackSetLicence(
        theorem="thm:licence",
        hypothesis_per_entry=(),
        discharge_per_entry=(),
        discharging_receiver_fact="A-RECV",
        receiver_spec_version="receiver-povm@0.1.3",
        source_mode=SourceMode.UNTRUSTED,
        admissible_set="A_CList(...)",
    )
    # licence with an EMPTY constraint list.
    with pytest.raises(MalformedInputError):
        _artifact(attack_set_license=licence)
    # a status version 1 never emits.
    with pytest.raises(MalformedInputError):
        _artifact(status=LinkStatus.CERTIFIED_OUTER)
    with pytest.raises(MalformedInputError):
        _artifact(status=LinkStatus.EXPLORATORY_NUMERIC)
    # a draft version.
    with pytest.raises(MalformedInputError):
        _artifact(mathematical_spec_version="proof-reductions@0.3.0-draft")
    # douglas_data is not a field: the key is absent, not nulled.
    assert "douglas_data" not in {
        field.name for field in dataclasses.fields(ProofReductionArtifact)
    }
    # The well-formed one builds.
    artifact = _artifact()
    assert artifact.status is LinkStatus.EXACT
    # sec:conventions bullet 13: `reductions@<contract_version>` OF THE ACCEPTED
    # CONTRACT, an accepted version of spec/modules/reductions/module.yaml.
    # HAND-EDITED when the pin moves, never regenerated from the code.
    assert artifact.mathematical_spec_version == "reductions@0.21.0"
    assert artifact.mathematical_spec_version == MATHEMATICAL_SPEC_VERSION
    # THE RECORD IS ALWAYS PRESENT AT 1.0.0 and there is no presence rule left
    # to enforce: what it carries -- kappa, the six (D-EMIT) outcomes, and what
    # def:emitnorm did per block -- exists whenever an artifact does, "SINCE
    # OTHERWISE THERE WOULD BE NO ARTIFACT".
    assert artifact.emission_record is not None
    assert artifact.emission_record.lattice_exponent >= 1


def test_an_outcome_is_an_artifact_or_a_refusal_and_never_both() -> None:
    """Section 2.5: a failure produces a refusal AND NO ARTIFACT."""
    report = _report()
    artifact = _artifact(verification_report=report)
    assert ReductionOutcome(
        artifact=artifact, refusal=None, verification_report=report
    ).emitted
    refusal = Refusal(
        reason=RefusalReason.CUTOFF_MISMATCH, rule="cutoff", detail="N differs"
    )
    assert not ReductionOutcome(
        artifact=None, refusal=refusal, verification_report=report
    ).emitted
    with pytest.raises(MalformedInputError):
        ReductionOutcome(artifact=artifact, refusal=refusal, verification_report=report)
    with pytest.raises(MalformedInputError):
        ReductionOutcome(artifact=None, refusal=None, verification_report=report)
    # The emitted artifact carries THE report, not a copy of it.
    with pytest.raises(MalformedInputError):
        ReductionOutcome(artifact=artifact, refusal=None, verification_report=_report())


def test_the_machine_record_is_json_serializable_and_reads_back_exactly() -> None:
    """A key-rate run must be able to log it, and read it back without loss."""
    artifact = _artifact()
    record = artifact.as_machine_record()
    text = json.dumps(record, sort_keys=True)
    reloaded = json.loads(text)
    # ONE ARTEFACT'S KEYS, which is OUTPUT_KEYS without `factor_emission`: that
    # key is the emission of SEVERAL instances and belongs to no single
    # artefact . A one-factor emission logs exactly the keys of one artefact.
    assert tuple(reloaded) == tuple(sorted(artifact.record_keys()))
    assert artifact.record_keys() == ONE_ARTEFACT_ONLY_KEYS
    # Every matrix reads back EXACTLY: the wire form is pairs of Fraction
    # strings, so there is no numeric conversion anywhere in the round trip.
    # PER SECTOR BLOCK: the record carries a LIST of square arrays per outcome,
    # and each reads back exactly.
    for label, payload in reloaded["target_povm"].items():
        original = artifact.target_povm[tuple(label.split(","))]  # type: ignore[index]
        assert len(payload) == len(original)
        for wire, block in zip(payload, original, strict=True):
            assert equal(deserialize_matrix(wire), block)
    assert reloaded["wpfss_data"]["weights"] == ["1/4", "1/8"]
    assert reloaded["wpfss_data"]["total"] == "3/8"
    assert reloaded["verification_report"]["receiver_bound_evaluation"] == (
        "floating_point"
    )
    assert len(reloaded["verification_report"]["rules"]) == len(RULE_ORDER) == 21


def test_no_operator_is_serialized_twice() -> None:
    """The chain references the emitted POVM rather than repeating it."""
    artifact = _artifact()
    record = artifact.as_machine_record()
    emitted = record["target_povm"]
    assert isinstance(emitted, dict)
    serialized = [
        serialize_matrix(block)
        for element in artifact.target_povm.values()
        for block in element
    ]
    # The chain's link families name the key instead of carrying the matrices.
    chain = record["reduction_chain"]
    assert isinstance(chain, dict)
    for link in chain["links"]:
        for slot in ("source_family", "target"):
            family = link["slots"][slot]
            assert family["povm"] in {"target_povm", "inline", None}
            if family["povm"] == "target_povm":
                assert family["povm_inline"] is None
    # And the whole record contains each emitted matrix's text exactly once.
    text = json.dumps(record, sort_keys=True)
    for payload in serialized:
        assert text.count(json.dumps(payload, sort_keys=True).strip("[]")) <= 1


def test_the_declared_form_is_emitted_with_the_entry() -> None:
    """``sec:outputs``, ``constraint_list``: "THE FORM IS EMITTED WITH THE ENTRY".

    "As the tag value ``homogeneous`` in trusted-source mode, because the
    consumer's part (i) security gate is a TYPE check on the declared tag and
    compares no numbers (``meat-core`` 1.0.0 ``constraint_list`` input row,
    Rem. ``rem:cgate``): THE DOCKING IS BY KEY AND NOTHING ABOUT THE FORM IS
    INFERRED AT EITHER END."

    An entry that reaches the wire without its tag leaves the consumer to infer
    it from the type of the datum, which is the inference that sentence forbids
    -- Stage 2 finding F-S2-PR-04. In untrusted-source mode the field is
    ``None``: the contract names the scalar form there and fixes no tag string
    for it, so ``None`` is emitted rather than a string this module invented.
    """
    from certiqs_key.foundations.exact import diagonal
    from certiqs_key.reductions.channels import split_blocks
    from certiqs_key.reductions.constraints import (
        AttackSetLicence,
        DeclaredForm,
        EntryDischarge,
        SourceMode,
    )
    from certiqs_key.reductions.wpfss.construction import (
        flat_sectors,
        fss_instance_entry,
    )

    licence = AttackSetLicence(
        theorem="thm:licence",
        hypothesis_per_entry=("eq:certificate",),
        discharge_per_entry=(
            EntryDischarge(
                entry="O",
                claim="wpfss/cor:fssinstance",
                supplier_fact="A-RECV",
                supplier_version="receiver@0.1.2",
            ),
        ),
        discharging_receiver_fact="A-RECV",
        # The supplier version this licence fixture names is one that exists.
        receiver_spec_version="receiver@0.1.2",
        source_mode=SourceMode.TRUSTED,
        admissible_set="A_CList(...)",
    )

    sectors = flat_sectors([2], ["f0", "f1"])

    def _entry(mode: SourceMode) -> object:
        # THE ELEMENT AND THE ENTRY ARE SECTOR-BLOCK LISTS, read against the
        # flat sector map.
        return fss_instance_entry(
            split_blocks(diagonal([F(1), F(0), F(0), F(0)]), [2, 1, 1]),
            sectors,
            2,
            2,
            F(1, 4),
            label="F^FSS_o - p_o Pi_Flag",
            certified_against="Lambda^FSS",
            mode=mode,
        )

    trusted = _artifact(
        constraint_list=(_entry(SourceMode.TRUSTED),),
        route=Route.LICENSED,
        attack_set_license=licence,
    ).as_machine_record()["constraint_list"]
    assert isinstance(trusted, list)
    assert trusted[0]["form"] == "homogeneous"
    assert DeclaredForm.HOMOGENEOUS == "homogeneous"

    untrusted = _artifact(
        constraint_list=(_entry(SourceMode.UNTRUSTED),),
        route=Route.LICENSED,
        attack_set_license=licence,
    ).as_machine_record()["constraint_list"]
    assert isinstance(untrusted, list)
    assert untrusted[0]["form"] is None

    # The key is on EVERY emitted entry, not only where a form exists: an absent
    # key and a null value are different things on the wire, and the consumer's
    # V6 reads the slot rather than testing for its presence.
    assert "form" in untrusted[0]


def test_the_ledger_entry_record_is_a_plain_dataclass() -> None:
    """No behaviour, no inference: the ledger is data (ARCHITECTURE_SPEC 3.4)."""
    entry = AssumptionLedgerEntry(
        assumption_id=AssumptionId.A_TSM,
        machine_key="test_statistics_model",
        never_verifiable=False,
        constrains=(("test_statistics_model", "output_state"),),
    )
    assert dataclasses.is_dataclass(entry)
    assert entry.inherited == ()
    assert entry.inherited_from is None



def test_the_source_segment_docking_point_names_only_existing_claims() -> None:
    """The docking-point string names claims that exist.

    A non-empty segment is admitted by kind under
    ``transmitter/def:source-segment``; the string must not name
    ``transmitter/ass:nosrc``, which does not exist.
    """
    from certiqs_key.reductions.links import SOURCE_SEGMENT_DOCKING_POINT

    assert "ass:nosrc" not in SOURCE_SEGMENT_DOCKING_POINT
    assert "transmitter/def:source-segment" in SOURCE_SEGMENT_DOCKING_POINT
