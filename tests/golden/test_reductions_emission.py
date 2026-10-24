"""The request-to-artifact machine, end to end, against the FROZEN registry.

Every case here runs :func:`certiqs_key.reductions.emit.reduce` on a DECLARATION --
the three groups of Section 2.1 -- and checks what came out against the frozen
values. The declaration that carries the file is ``RC2-shaped``: the
receiver declaration whose weight route the registry freezes as ``RC2``, on
the flat instance (one branch, a one-dimensional register). The emitted
weights must be ``29/300`` and ``29/600`` with total ``29/200``, which is the
frozen ``eq:weightroute`` result reached through the whole pipeline rather
than through the predicate alone. A two-letter declaration over the same
pipeline carries the total-weight refusal.

SUPERSEDED FROZEN SYMBOLS
=========================
Two frozen symbols are marked ``superseded`` in the registry,
both of kind ``vocabulary``, and each is replaced here by its named
``*_0_2_0`` replacement:

* ``OUTPUT_KEYS`` -- SEVENTEEN keys, with ``operator_tolerance_record`` absent.
  Replaced by ``OUTPUT_KEYS_0_2_0``, EIGHTEEN, the new key sitting immediately
  before ``mathematical_spec_version``. THE KEY IS PRESENT EVEN AT
  ``eps_op = 0``, carrying ``null``: the presence rule is about the VALUE and
  not about the key.
* ``REFUSAL_REASONS`` -- the 24-string vocabulary over 21 rows. Replaced by
  ``REFUSAL_REASONS_0_2_0``, 26 strings over 24 rows. "NONE REMOVED, AND NONE
  INVENTED WHERE AN EXISTING ONE CARRIES THE REFUSAL", so the 24 are a subset
  of the 26 and the supersession is a widening.

One test is read against the replacement: the conditional-completeness
refusal, which 0.1.3 emitted under ``no_block_structure`` and 0.2.0 emits under
``declaration_outside_tolerance``. Section 4.14 splits the row -- "THIS ROW IS
THE STRUCTURAL HALF ONLY. THE NUMERICAL HALF IS THE NEXT ROW" -- and the
declaration, the datum and the verdict are the same; only the reason differs.
"""
from __future__ import annotations

from fractions import Fraction

import pytest
from reductions_support import RECEIVER_LEDGER_KEYS, RETIRED_RECEIVER_KEYS
from reductions_support import reduce_flat_call as reduce
from registry_reductions import (
    ASSUMPTION_COUNT_1_0_0,
    ASSUMPTION_KEYS_REMOVED_1_0_0,
    ASSUMPTION_LEDGER_0_2_0,
    CHAIN_WELL_FORMED,
    FAIL_CLOSED_ROW_COUNT_0_2_0,
    FAIL_CLOSED_ROW_COUNT_0_3_0,
    FAIL_CLOSED_ROW_COUNT_1_0_0,
    INHERITED_RECEIVER_KEYS_NEW_AT_1_0_0,
    NEVER_VERIFIED_1_0_0,
    OUTPUT_KEYS,
    OUTPUT_KEYS_0_2_0,
    OUTPUT_KEYS_1_0_0,
    PR_R1,
    PR_R6,
    REFUSAL_REASONS,
    REFUSAL_REASONS_0_2_0,
    REFUSAL_REASONS_0_3_0,
    REFUSAL_REASONS_1_0_0,
    REFUSAL_REASONS_ADDED_1_0_0,
    SPEC_VERSION_0_2_0,
    SPEC_VERSION_0_3_0,
    SUPERSESSIONS,
)

from certiqs_key.foundations.exact import (
    Cx,
    Matrix,
    direct_sum,
    identity,
    is_positive_semidefinite,
    matrix,
)
from certiqs_key.reductions import MATHEMATICAL_SPEC_VERSION
from certiqs_key.reductions.artifact import ONE_ARTEFACT_ONLY_KEYS
from certiqs_key.reductions.artifact import OUTPUT_KEYS as MODULE_OUTPUT_KEYS
from certiqs_key.reductions.inputs import (
    BoundQuantifierDomain,
    ChannelGrading,
    CoarseGraining,
    HighPhotonBound,
    InheritedAssumption,
    LinkDeclaration,
    ProbeDeclaration,
    ProtocolDeclaration,
    ReceiverArtifactRows,
    ReductionRequest,
    canonical_coarse_graining,
    patterns,
    product_form_dark_counts,
)
from certiqs_key.reductions.reasons import (
    LINK_KINDS_DEFERRED,
    LinkKind,
    LinkStage,
    LinkStatus,
    RefusalReason,
    SourceMode,
)

KAPPA_FIXTURE: int = 12

F = Fraction

# The fixture's receiver version is the receiver's accepted one, which STATES
# the per-setting weights; the wpfss slot row refuses an artifact of a
# version that does not (req:supplier-version). Fixture data, not an oracle
# value.
ACCEPTED = ("receiver@0.9.0",)

def _real(frozen: tuple[tuple[Fraction, ...], ...]) -> Matrix:
    """Return a band-5 REAL matrix in the module's representation.

    Band 5 freezes its matrices as plain rationals; bands 1-4 freeze theirs as
    ``(re, im)`` pairs, which :func:`m` converts. Both are the same object in
    two spellings and neither is a number this file chooses.
    """
    return matrix([list(row) for row in frozen])

def m(frozen: object) -> Matrix:
    """Convert a frozen registry matrix into the module's representation."""
    rows = frozen  # type: ignore[assignment]
    return matrix([[Cx(entry[0], entry[1]) for entry in row] for row in rows])  # type: ignore[index,union-attr]

RC2_COARSE = canonical_coarse_graining(
    2,
    empty_letter="y_empty",
    single_letters={1: "y_1", 2: "y_2"},
    multiclick_letter="y_mc",
)

RC2_SETTINGS = ("t_off", "t_on")

RC2_JOINT = tuple(
    (letter, setting) for setting in RC2_SETTINGS for letter in RC2_COARSE.letters
)

SUPPLIER_LEDGER = tuple(
    InheritedAssumption(machine_key=key) for key in RECEIVER_LEDGER_KEYS
)

PR_R1_DARK_RATES = {1: F(3, 16), 2: F(1, 4)}

def rc2_artifact(**overrides: object) -> ReceiverArtifactRows:
    """Return the receiver rows band 5 freezes as ``PR_R1``."""
    blocks = {
        (letter, setting): (matrix([[dict(PR_R1.declared_blocks)[letter]]]),)
        for letter in RC2_COARSE.letters
        for setting in RC2_SETTINGS
    }
    defaults: dict[str, object] = {
        "mathematical_spec_version": "receiver@0.9.0",
        "detection_alphabet": RC2_COARSE.letters,
        "photon_blocks": blocks,
        "high_photon_bounds": (
            HighPhotonBound.uniform(
                RC2_COARSE.fibre("y_mc"),
                dict(PR_R1.slot_weights)["y_mc"],
                RC2_SETTINGS,
            ),
        ),
        "bound_quantifier_domain": BoundQuantifierDomain(
            cutoff=0, settings=RC2_SETTINGS
        ),
        "dark_count_channel": product_form_dark_counts(2, PR_R1_DARK_RATES),
        "outcome_coarse_graining": RC2_COARSE,
        "bound_evaluation": "floating_point",
        "channel_grading": ChannelGrading(block_dimensions=(1,)),
        # The three data below carry no default and are stated here.
        "validation_results_present": True,
        "declared_device_family": (),
        "occupation_basis_order": (),
        "inherited_assumption_ledger": SUPPLIER_LEDGER,
    }
    defaults.update(overrides)
    return ReceiverArtifactRows(**defaults)  # type: ignore[arg-type]

def rc2_declaration(**overrides: object) -> ProtocolDeclaration:
    """Return the protocol declaration beside :func:`rc2_artifact`."""
    defaults: dict[str, object] = {
        "probe_declaration": ProbeDeclaration(
            settings=RC2_SETTINGS,
            weights=dict(PR_R1.probe_weights),
        ),
        "detection_alphabet": RC2_COARSE.letters,
        "photon_cutoff": 0,
        "source_mode": SourceMode.UNTRUSTED,
        "joint_alphabet": RC2_JOINT,
    }
    defaults.update(overrides)
    return ProtocolDeclaration(**defaults)  # type: ignore[arg-type]

def rc2_request(**overrides: object) -> ReductionRequest:
    """Return the canonical v1 chain: the squashing link, then the pinching."""
    defaults: dict[str, object] = {
        "link_declarations": (
            LinkDeclaration(stage=LinkStage.RECEIVER, kind=LinkKind.WPFSS),
            LinkDeclaration(stage=LinkStage.RECEIVER, kind=LinkKind.PINCHING),
        ),
        "route": "encoded",
        "accepted_receiver_versions": ACCEPTED,
        "requested_assurance": "estimate",
        "lattice_exponent": KAPPA_FIXTURE,
    }
    defaults.update(overrides)
    return ReductionRequest(**defaults)  # type: ignore[arg-type]

@pytest.mark.contract
@pytest.mark.oracle
def test_the_pipeline_reproduces_the_frozen_rc2_weight_route() -> None:
    """Eq. ``eq:weightroute`` THEN Eq. ``eq:latdown``, through the whole path.

    THE ONE PLACE IN THE SUITE WHERE THE 1.0.0 LOWERING IS VISIBLE END TO END.
    ``eq:weightroute`` gives ``p^`` and ``eq:latdown`` emits
    ``p = 2^-kappa floor(2^kappa p^)``, and at PRR-1 the two differ at BOTH
    settings: ``p^ = 279/2048`` against the emitted ``187/2048`` and
    ``183/4096``. "THE EMITTED WEIGHT IS ``p_(y_i,t)`` AND NOT ``p^_(y_i,t)``,
    and THE DIRECTION OF THAT ROUNDING IS THE WHOLE OF WHAT MAKES IT SAFE ...
    ``lat(.)`` ONLY LOWERS" (Prop. ``prop:route``), so both are asserted and the
    inequality between them is asserted too.
    """
    outcome = reduce(rc2_artifact(), rc2_declaration(), rc2_request())
    assert outcome.emitted, outcome.refusal
    artifact = outcome.artifact
    assert artifact is not None
    weights = dict(
        zip(artifact.wpfss_data.flag_basis, artifact.wpfss_data.weights, strict=True)
    )
    frozen = dict(PR_R1.emitted_weights)
    for outcome_label, weight in weights.items():
        assert weight == frozen.get(outcome_label, F(0)), outcome_label
    assert artifact.wpfss_data.total == PR_R1.total_weight == F(557, 4096)
    # THE ROUTED WEIGHT BEFORE THE ROUNDING, and that lat() strictly lowered it.
    routed = dict(PR_R1.routed_weights_hat)
    assert PR_R1.total_weight_hat == F(279, 2048)
    for outcome_label, before in routed.items():
        after = frozen[outcome_label]
        assert after < before, outcome_label
        assert (after * 2**PR_R1.kappa).denominator == 1
    # Every rule was DECIDED and passed. TWENTY-SEVEN ROWS ON THE FLAT PATH:
    # the frozen twenty-eight LESS the branching model's row, which is a
    # removable submodule's and is reported only where a branching model is
    # declared. The rows a reduction reports are the core's plus the ones its
    # INSTANCE BUILDER declares, so the count is a property of the path and not
    # a constant of the module; the frozen twenty-eight is the union and is
    # asserted as such.
    # The live count is the frozen twenty-eight less the branching model's row.
    assert (
        len(artifact.verification_report.outcomes)
        == FAIL_CLOSED_ROW_COUNT_1_0_0 - 1
        == 27
    )
    assert FAIL_CLOSED_ROW_COUNT_0_2_0 == 24
    assert FAIL_CLOSED_ROW_COUNT_0_3_0 == 25
    assert FAIL_CLOSED_ROW_COUNT_1_0_0 == 28
    # The licensed-route Hermiticity row is SCOPED to the `licensed` route and
    # PRR-1 is on the encoded one, so it is recorded NOT DECIDED rather than
    # passed -- the honest record Section 4.14's preamble asks for.
    undecided = {str(row.rule) for row in artifact.verification_report.undecided}
    assert undecided == {"licensed_hermiticity"}
    assert all(
        row.passed
        for row in artifact.verification_report.outcomes
        if str(row.rule) != "licensed_hermiticity"
    )

@pytest.mark.contract
@pytest.mark.oracle
def test_the_emitted_artifact_carries_all_eighteen_keys() -> None:
    """The outputs tables: EIGHTEEN machine keys, in the interface's own order.

    ``emission_record`` stands immediately before
    ``mathematical_spec_version``. It records what this module DID TO ITS OWN
    CONSTRUCTION before declaring it, so the key is ALWAYS PRESENT.

    THE EXPECTED KEY LIST IS WRITTEN BY HAND. The frozen ``OUTPUT_KEYS_1_0_0``
    is eighteen keys and is not regenerated from the code; what this
    repository emits is that list with ``douglas_data`` REMOVED and ``route``
    PUT IN ITS PLACE.

    * ``douglas_data`` is not emitted: the
      interface lists it under ``not_carried`` because a key whose value is
      always ``null`` is a hand-maintained mirror of a deferral
      (PRINCIPLES.md section 7).
    * ``route`` is an OUTPUT ROW of ``wpfss/interface.yaml`` -- "always, for
      an artifact emitted from the flat instance; the single value the request
      carried" -- and was carried as a field of the artifact without reaching
      the record. The two routes run on DIFFERENT CHANNELS
      (``wpfss/rem:tworoutes``), so a record that did not say which one
      produced it would leave a consumer to infer it.

    The RELATION between the two lists is asserted rather than a new literal
    written, so the freeze still decides every other key and its position.

    THE MODULE'S VOCABULARY HAS ``factor_emission`` AND THIS
    RECORD DOES NOT. That row is "PRESENT EXACTLY WHEN THE CALL DECLARES MORE
    THAN ONE INSTANCE -- one per measuring party. ABSENT FOR A ONE-FACTOR
    EMISSION, which is every emission of version 1, and nothing else in this
    file changes there", and what it carries is the ordered list of the
    FACTORS' artefacts with the combination rule -- a record about several
    artefacts and a field of none. So what this emission logs is
    ``ONE_ARTEFACT_ONLY_KEYS``.
    """
    outcome = reduce(rc2_artifact(), rc2_declaration(), rc2_request())
    artifact = outcome.artifact
    assert artifact is not None
    record = artifact.as_machine_record()
    assert tuple(record) == ONE_ARTEFACT_ONLY_KEYS
    # TWENTY: `reference_companion` (reductions/req:reference-companion (v),
    # (vi)) after `emission_record`, and `receiver_row_omitted_on_provenance`
    # (reductions/req:recv-row-provenance) after `assumption_ledger`, empty
    # here: the call carries no receiver provenance.
    assert len(record) == 20
    assert record["receiver_row_omitted_on_provenance"] == []
    assert "factor_emission" not in record
    retired, added = ("douglas_data",), ("route",)
    assert set(OUTPUT_KEYS_1_0_0) - set(MODULE_OUTPUT_KEYS) == set(retired)
    assert set(MODULE_OUTPUT_KEYS) - set(OUTPUT_KEYS_1_0_0) == {
        *added,
        "factor_emission",
        "reference_companion",
        "receiver_row_omitted_on_provenance",
    }
    assert tuple(
        key
        for key in ONE_ARTEFACT_ONLY_KEYS
        if key not in ("reference_companion", "receiver_row_omitted_on_provenance")
    ) == tuple(
        "route" if key == "douglas_data" else key for key in OUTPUT_KEYS_1_0_0
    )
    # The 0.1.3 tuple is a SUBSEQUENCE of the 0.2.0 one: nothing is removed or
    # reordered, one key is inserted. The mark says so and this checks it.
    assert [key for key in OUTPUT_KEYS_0_2_0 if key in OUTPUT_KEYS] == list(OUTPUT_KEYS)
    assert "route" not in OUTPUT_KEYS_0_2_0
    mark = next(record_ for record_ in SUPERSESSIONS if record_.symbol == "OUTPUT_KEYS")
    assert mark.kind == "vocabulary"
    assert mark.replacement == ("OUTPUT_KEYS_0_2_0",)
    # THE RENAME AND RE-TYPE, as the 1.0.0 mark states it: the old key is
    # absent and its successor is present, carrying kappa and the six condition
    # outcomes.
    assert "operator_tolerance_record" not in record
    assert record["emission_record"] is not None
    assert artifact.emission_record.lattice_exponent == KAPPA_FIXTURE
    assert record["mathematical_spec_version"] == MATHEMATICAL_SPEC_VERSION
    # The two presence rules the interface states, and the absent key.
    assert "douglas_data" not in record
    assert record["status"] == "exact"
    # THE DEFAULT PARTY PARTITION IS EMITTED WITH THE SECTOR MAP
    # (def:reduction-instance (I2); thm:emit (ii)): the consuming declaration
    # places its well-formedness conditions on A PARTY's side and reads the
    # partition, which the five conditions of def:exactadm say nothing about.
    partition = record["target_descriptor"]["party_partition"]
    assert partition == artifact.target_descriptor.party_partition
    assert "Bob" in partition
    assert record["attack_set_license"] is None
    # sec:conventions bullet 13: the string
    # is `proof-reductions@<contract_version>` OF THE ACCEPTED CONTRACT.
    # ``SPEC_VERSION_0_2_0`` is marked ``superseded`` for exactly this
    # value, and is asserted here as a superseded value.
    assert record["mathematical_spec_version"] == MATHEMATICAL_SPEC_VERSION
    assert SPEC_VERSION_0_3_0 == "proof-reductions@0.3.0"
    assert SPEC_VERSION_0_2_0 == "proof-reductions@0.2.0"
    assert record["mathematical_spec_version"] != SPEC_VERSION_0_2_0
    assert record["constraint_list"] == []

@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("kind", LINK_KINDS_DEFERRED, ids=lambda k: k.value)
def test_each_deferred_link_kind_is_refused_end_to_end(kind: LinkKind) -> None:
    """Section 1.3: declared, reserved and REFUSED in version 1."""
    outcome = reduce(
        rc2_artifact(),
        rc2_declaration(),
        rc2_request(
            link_declarations=(LinkDeclaration(stage=LinkStage.RECEIVER, kind=kind),)
        ),
    )
    assert not outcome.emitted
    assert outcome.artifact is None
    assert outcome.refusal is not None
    assert outcome.refusal.reason is RefusalReason.LINK_KIND_DEFERRED

@pytest.mark.contract
@pytest.mark.oracle
def test_a_non_exact_status_request_is_refused_end_to_end() -> None:
    """Theorem ``thm:transfer`` has NO PENALTY SLOT."""
    for status in ("certified_outer", "exploratory_numeric"):
        outcome = reduce(
            rc2_artifact(),
            rc2_declaration(),
            rc2_request(
                link_declarations=(
                    LinkDeclaration(
                        stage=LinkStage.RECEIVER,
                        kind=LinkKind.WPFSS,
                        requested_status=status,
                    ),
                )
            ),
        )
        assert not outcome.emitted
        assert outcome.refusal is not None
        assert outcome.refusal.reason is RefusalReason.APPROXIMATE_SQUASHING_UNSUPPORTED
    assert LinkStatus.EXACT.value == "exact"

@pytest.mark.contract
@pytest.mark.oracle
def test_the_emitted_chain_is_the_frozen_two_link_one() -> None:
    """``CHAIN-wpfss-pinching``: composable, tuple-chained, stage-ordered."""
    outcome = reduce(rc2_artifact(), rc2_declaration(), rc2_request())
    artifact = outcome.artifact
    assert artifact is not None
    chain = artifact.reduction_chain
    assert len(chain.links) == 2
    kinds = [link.kind.value for link in chain.links]
    assert kinds == ["wpfss", "pinching"]
    conditions = chain.conditions()
    assert conditions.composable is CHAIN_WELL_FORMED.composable
    assert conditions.tuple_chained is CHAIN_WELL_FORMED.tuple_chained
    assert conditions.stage_ordered is CHAIN_WELL_FORMED.stage_ordered
    assert conditions.holds
    assert chain.composite_status() is LinkStatus.EXACT
    assert str(chain.composite_status()) == CHAIN_WELL_FORMED.composite_status
    # THE ORDER IS DATA: later links act later.
    assert chain.composite_order() == ("L1-wpfss", "L2-pinching")
    assert "Lambda_Chain" in chain.composite_witness().equation

@pytest.mark.contract
@pytest.mark.oracle
def test_a_source_stage_link_after_a_receiver_link_is_refused_end_to_end() -> None:
    """Remark ``rem:ordering``: (C3) is a rule with a reason, not a convention."""
    outcome = reduce(
        rc2_artifact(),
        rc2_declaration(),
        rc2_request(
            link_declarations=(
                LinkDeclaration(stage=LinkStage.RECEIVER, kind=LinkKind.WPFSS),
                LinkDeclaration(stage=LinkStage.SOURCE, kind=LinkKind.IDENTITY),
            )
        ),
    )
    assert not outcome.emitted
    assert outcome.refusal is not None
    assert outcome.refusal.reason is RefusalReason.SOURCE_LINK_AFTER_RECEIVER_LINK

@pytest.mark.contract
@pytest.mark.oracle
def test_the_verification_report_carries_every_row_with_its_outcome() -> None:
    """Section 2.3: "every validation rule of Section 4.14 WITH ITS OUTCOME"."""
    outcome = reduce(rc2_artifact(), rc2_declaration(), rc2_request())
    artifact = outcome.artifact
    assert artifact is not None
    report = artifact.verification_report
    # TWENTY-SEVEN ON THE FLAT PATH: the frozen twenty-eight less the
    # branching model's row, reported only where a branching model is declared
    # (there is no domination submodule).
    assert len(report.outcomes) == FAIL_CLOSED_ROW_COUNT_1_0_0 - 1 == 27
    spanned = {
        reason
        for row in report.outcomes
        for reason in (str(r) for r in _reasons_of(row))
    }
    # THE VOCABULARY IS 1.0.0's: 30 strings over 28 rows. Every earlier
    # supersession was a pure widening -- "NONE REMOVED, AND NONE INVENTED WHERE
    # AN EXISTING ONE CARRIES THE REFUSAL" -- and 1.0.0 is not: it adds four
    # strings and REMOVES one, ``declaration_outside_tolerance``, with the
    # tolerance apparatus. So the 0.3.0 vocabulary is not a subset, and that is
    # asserted rather than glossed.
    # THE FLAT PATH SPANS TWENTY-EIGHT OF THE THIRTY: the removable branching
    # submodule's own string is spanned only where its row is reported.
    # ONE STRING IS RENAMED --
    # ``requested_assurance_shelved`` is ``requested_assurance_unknown``, so
    # that the row's subject is a tier that is not one of the live ones.
    assert spanned == (
        set(REFUSAL_REASONS_1_0_0)
        - {"blinding_model_ill_formed", "requested_assurance_shelved"}
    ) | {"requested_assurance_unknown"}
    assert (
        set(REFUSAL_REASONS) < set(REFUSAL_REASONS_0_2_0) < set(REFUSAL_REASONS_0_3_0)
    )
    assert len(REFUSAL_REASONS_0_2_0) - len(REFUSAL_REASONS) == 2
    assert len(REFUSAL_REASONS_0_3_0) - len(REFUSAL_REASONS_0_2_0) == 1
    assert not set(REFUSAL_REASONS_0_3_0) <= set(REFUSAL_REASONS_1_0_0)
    assert set(REFUSAL_REASONS_0_3_0) - set(REFUSAL_REASONS_1_0_0) == {
        "declaration_outside_tolerance"
    }
    assert set(REFUSAL_REASONS_ADDED_1_0_0) <= set(REFUSAL_REASONS_1_0_0)
    assert len(REFUSAL_REASONS_1_0_0) == 30
    # The dependency identity, referenced and never re-derived.
    assert report.receiver_spec_version == "receiver@0.9.0"
    assert report.receiver_bound_evaluation == "floating_point"
    # bound_evaluation is PROPAGATED UNCHANGED and never upgraded.
    assert report.receiver_bound_evaluation != "exact"

def _reasons_of(row: object) -> tuple[object, ...]:
    from certiqs_key.reductions.reasons import fail_closed_rules

    return fail_closed_rules()[row.rule]  # type: ignore[attr-defined,index]

@pytest.mark.contract
@pytest.mark.oracle
def test_the_assumption_ledger_names_the_nine_and_inherits_by_version() -> None:
    """Section 2.3 and Section 5, including the inherited receiver assumptions.

    NINE ROWS AT 1.0.0, FROM TEN: "A-OPTOL is REMOVED and NOTHING REPLACES IT --
    what it hypothesized is NOW DECIDED", the declared operator tolerance having
    left the contract with its apparatus. The never-verified set drops from
    three to two.

    AND THE INHERITED SET IS THIRTEEN MACHINE KEYS, FROM NINE PROSE PHRASES:
    "the supplier's own machine keys read from the receiver artifact's ledger --
    ALL THIRTEEN OF THEM ... A PROSE LIST IS NOT A KEY AND DOES NOT COMPOSE"
    (``sec:outputs``). Four of them "did not cross the docking boundary at all"
    before 1.0.0 and are asserted present by name.
    """
    outcome = reduce(rc2_artifact(), rc2_declaration(), rc2_request())
    artifact = outcome.artifact
    assert artifact is not None
    ledger = artifact.assumption_ledger
    # EIGHT ROWS ON THE FLAT PATH: the frozen nine LESS the branching
    # submodule's row, which its builder adds where a branching model is
    # declared. A-ROUND is ``A-ROUND-SQ`` here: short ids and machine
    # keys are repository-wide and the receiver module already owns ``A-ROUND``
    # with the key ``round_homogeneity``, which this ledger INHERITS from it as
    # the supplier's own, so the two are distinguished rather than namespaced.
    # This fixture takes the flat path and emits no constraint entries; the
    # licensed run below emits two and carries the same rows.
    assert artifact.constraint_list == ()
    # THE ORACLE IS NEVER REGENERATED FROM THE CODE. THE FLAT PATH'S LEDGER IS
    # EIGHT ROWS (seven plus A-SNAP):
    #
    # A-NOSRC has no row. No claim of this module rests on the source
    # segment being empty -- def:chain defines the chain at every
    # length and its composite as the PAIR, thm:chain (i)-(iv) read the receiver
    # composite alone, and rem:ordering's inclusion is lem:precomposition -- so
    # the key is in the closure of no claim producing the artefact, and the
    # emitted ledger, being the declared row list under its presence rules
    # (req:assumption-ledger), declares no row for it. Whether the segment is
    # empty is DATA in the emitted reduction_chain.
    #
    # A-SEQ IS HERE. def:protocol declares the transmitter's ass:seq
    # -- the round's public messages follow every measurement of the round --
    # and every claim on the emission path uses def:protocol, so the key is in
    # the closure of every emitting claim and the row is declared with no
    # presence condition. It is emitted UNCONDITIONALLY: the number of measuring
    # parties is not a datum def:protocol reads, and with one measuring party
    # the key is the assumption it always was.
    #
    # A-SRC is ABSENT HERE and from every artefact emitted: it is present only
    # where the emitted chain's source segment is NON-EMPTY, and every chain
    # this module emits has an empty one.
    #
    # A-DIM IS GONE: its setting half is def:system-setting, a definition and
    # no row, and its adversary half, the finite dimension of the adversary's
    # registers that lem:sep reads, is the round model's
    # (foundations/def:round-model) and no row either; meat-core's A-EVE-DIM
    # (key adversary_registers_finite) is superseded, and the engine lifts the
    # security statement to an adversary of any memory
    # (meat-core/lem:memory-lift).
    #
    # PRR-1's emission classes are moved (derived by hand in
    # PRR1_NORMALIZER), so its data sectors are named provisionally as resting
    # on A-SNAP and the ledger carries foundations' A-SNAP row under its
    # presence rule (req:emission-record): six rows plus that one.
    #
    # A-CONST (ass:constdecl) is emitted "only where the
    # emitted constraint list is non-empty" (req:assumption-ledger): its
    # statement is a condition on the constants of emitted entries and holds
    # vacuously of an empty list. This fixture emits none, so its ledger is
    # SIX rows plus A-SNAP; the licensed run below emits two entries and
    # carries A-CONST.
    snap_rows = [entry for entry in ledger if entry.assumption_id == "A-SNAP"]
    assert len(snap_rows) == 1
    assert snap_rows[0].machine_key == "snapped_measurement"
    assert snap_rows[0].never_verifiable is True
    assert dict(snap_rows[0].constrains)["resting_blocks"]
    ledger = tuple(entry for entry in ledger if entry.assumption_id != "A-SNAP")
    assert len(ledger) == ASSUMPTION_COUNT_1_0_0 - 3 == 6
    by_id = {str(entry.assumption_id): entry for entry in ledger}
    assert set(by_id) == {
        "A-MEAS",
        "A-ROUND-SQ",
        "A-RECV",
        "A-PROBE",
        "A-TSM",
        "A-SEQ",
    }
    assert "A-CONST" not in by_id
    assert "A-NOSRC" not in by_id
    assert "A-SRC" not in by_id
    assert by_id["A-SEQ"].machine_key == "sequential_round_model"
    assert "A-EVE-DIM" not in by_id
    assert "A-SOUND" not in by_id
    assert "A-DIM" not in by_id
    assert by_id["A-ROUND-SQ"].machine_key == "round_homogeneity_squashing"
    # The frozen 0.2.0 ledger is this one PLUS A-OPTOL and the branching row, under the
    # frozen spelling of the round-homogeneity row -- AND PLUS A-NOSRC, whose
    # row is not in this module's ledger for the reason above -- AND PLUS
    # A-DIM -- AND PLUS A-CONST at this empty list (the frozen 0.2.0 tuple is
    # untouched).
    assert {row.assumption_id for row in ASSUMPTION_LEDGER_0_2_0} - set(by_id) == {
        "A-OPTOL",
        "A-BLIND",
        "A-ROUND",
        "A-NOSRC",
        "A-DIM",
        "A-CONST",
    }
    assert set(ASSUMPTION_KEYS_REMOVED_1_0_0) == {"A-OPTOL"}
    never = {key for key, entry in by_id.items() if entry.never_verifiable}
    # The frozen 1.0.0 core member A-RECV, PLUS A-MEAS and A-ROUND-SQ
    # (req:never-verified-assumptions). The frozen tuple is not edited.
    assert set(NEVER_VERIFIED_1_0_0) - {"A-BLIND"} == {"A-RECV"}
    # FROZEN UNION ADDED, and here that is every row of this emission: A-PROBE,
    # A-TSM (their `verification` field is `never`) and the transmitter's A-SEQ,
    # which carries its owner's mark. A-CONST is no row of this empty-list
    # emission; it is asserted never-verified on the licensed run below.
    added = {"A-PROBE", "A-TSM", "A-SEQ"}
    assert never == {"A-RECV", "A-MEAS", "A-ROUND-SQ"} | added == set(by_id)

    # --- A RUN THAT EMITS ENTRIES CARRIES THE SAME ROWS ---------------------
    # The same reduction on the licensed route, which emits two constraint
    # entries. There is no A-SOUND (constraints_sound) row: that every
    # emitted entry is sound for the chain is a conclusion of thm:chain,
    # cor:entries and thm:licence (rem:sound-and-atk), not a ledger row, so the
    # two ledgers are the same rows and neither side names the key.
    licensed = reduce(
        rc2_artifact(),
        rc2_declaration(),
        rc2_request(
            route="licensed",
            link_declarations=(
                LinkDeclaration(stage=LinkStage.RECEIVER, kind=LinkKind.FSS),
                LinkDeclaration(stage=LinkStage.RECEIVER, kind=LinkKind.PINCHING),
            ),
        ),
    ).artifact
    assert licensed is not None
    assert licensed.constraint_list
    licensed_by_id = {
        str(entry.assumption_id): entry for entry in licensed.assumption_ledger
    }
    # The licensed artefact's data sectors rest on A-SNAP as the encoded
    # one's do, so it carries the same A-SNAP row beside the seven, and
    # A-CONST, present because this run's emitted list is non-empty
    # (req:assumption-ledger), with its never-verified mark.
    assert set(licensed_by_id) == set(by_id) | {"A-SNAP", "A-CONST"}
    assert licensed_by_id["A-CONST"].machine_key == "declared_constants"
    assert licensed_by_id["A-CONST"].never_verifiable is True
    assert "constraints_sound" not in {
        entry.machine_key for entry in licensed.assumption_ledger
    }
    from certiqs_key.meat_core.reasons import INHERITED_KEYS, assumption_ledger

    assert "A-SOUND" not in INHERITED_KEYS
    engine = assumption_ledger(
        trusted_source=False,
        alice_dim=2,
        alice_party="A",
        constraint_entries=len(licensed.constraint_list),
        key_length_wanted=True,
        key_length_reported=False,
        first_order=False,
    )
    assert "constraints_sound" not in engine
    # A-RECV names the artifact BY VERSION and carries THE SUPPLIER'S OWN
    # MACHINE KEYS, passed through as supplied -- here the receiver's ten
    # (the frozen thirteen less three) -- not nine English phrases, and none namespaced.
    recv = by_id["A-RECV"]
    assert recv.inherited_from == "receiver@0.9.0"
    assert recv.inherited == RECEIVER_LEDGER_KEYS
    assert len(recv.inherited) == 10
    assert all(":" not in item and " " not in item for item in recv.inherited)
    for key in INHERITED_RECEIVER_KEYS_NEW_AT_1_0_0:
        assert (key in recv.inherited) is (key not in RETIRED_RECEIVER_KEYS)
    # A-PROBE carries the declared q_t values, which are band 5's dyadic ones.
    assert dict(by_id["A-PROBE"].constrains) == {
        "q_t_off": "43/64",
        "q_t_on": "21/64",
    }
    assert dict(by_id["A-TSM"].constrains)["test_statistics_model"] == "output_state"

@pytest.mark.contract
@pytest.mark.oracle
def test_a_non_absorbing_bounded_letter_refuses_the_whole_artifact() -> None:
    """Remark ``rem:absorbneeded``, end to end: no artifact, and no weights."""
    rows = rc2_artifact(
        dark_count_channel=product_form_dark_counts(2, {1: F(0), 2: F(1, 4)}),
        high_photon_bounds=(
            HighPhotonBound.uniform(RC2_COARSE.fibre("y_1"), F(1, 5), RC2_SETTINGS),
        ),
    )
    outcome = reduce(rows, rc2_declaration(), rc2_request())
    assert not outcome.emitted
    assert outcome.artifact is None
    assert outcome.refusal is not None
    assert outcome.refusal.reason is RefusalReason.BOUNDED_LETTER_NOT_ABSORBING
    # The weight row could not be decided, and says so rather than passing.
    undecided = {str(row.rule) for row in outcome.verification_report.undecided}
    assert "total_weight" in undecided

@pytest.mark.contract
@pytest.mark.oracle
def test_a_draft_receiver_version_refuses_before_anything_is_emitted() -> None:
    """Assumption A-RECV: a draft version may not back an emitted artifact."""
    outcome = reduce(
        rc2_artifact(mathematical_spec_version="receiver-povm@0.1.3-draft"),
        rc2_declaration(),
        rc2_request(),
    )
    assert not outcome.emitted
    assert outcome.refusal is not None
    assert outcome.refusal.reason is RefusalReason.RECEIVER_SPEC_NOT_ACCEPTED

@pytest.mark.contract
@pytest.mark.oracle
def test_a_declared_relation_that_lem_obstructions_forbids_is_refused() -> None:
    """Section 4.14's obstruction row, on a relation THE CALLER declares."""
    physical = (
        matrix([[F(1), F(0)], [F(0), F(0)]]),
        matrix([[F(0), F(0)], [F(0), F(1)]]),
    )
    half = matrix([[F(1, 2), F(0)], [F(0), F(1, 2)]])
    outcome = reduce(
        rc2_artifact(),
        rc2_declaration(),
        rc2_request(declared_relations=((physical, (half, half)),)),
    )
    assert not outcome.emitted
    assert outcome.refusal is not None
    assert outcome.refusal.reason is RefusalReason.DECLARED_RELATION_IMPOSSIBLE

#: PRR-1 THROUGH THE FIDELITY-FIRST NORMALIZER, DERIVED BY HAND
#: (not regenerated from the code). Units of ``2^-17``;
#: the lattice step at ``kappa = 12`` is 32 units.
#:
#: t_off, ``q_t = 43/64 = 88064`` units; handed datum y_empty 28509, y_1 16899,
#: y_2 20683, y_mc 21973 (sum 88064), none a multiple of 32, so the class is
#: not kept: MOVED by step (2) at ``w = 0`` (1x1 blocks, no off-diagonal).
#: Rounded to nearest: 28509/32 = 890.9 -> 28512, 16899/32 = 528.1 -> 16896,
#: 20683/32 = 646.3 -> 20672, 21973/32 = 686.7 -> 21984 (no tie); sum 88064,
#: residue 0, so no component and no host; every block non-negative -- the
#: frozen emitted family, ``Delta_s`` = 11 units.
#:
#: t_on, ``q_t = 21/64 = 43008`` units; 13923, 8253, 10101, 10731. Rounded
#: to nearest: 435.1 -> 13920, 257.9 -> 8256, 315.7 -> 10112, 335.3 -> 10720;
#: sum 43008, residue 0, no host -- the frozen emitted family.
PRR1_NORMALIZER: dict[str, dict[str, object]] = {
    "t_off": {"step": "snap_for_fidelity", "mixing": F(0), "hosts": ()},
    "t_on": {"step": "snap_for_fidelity", "mixing": F(0), "hosts": ()},
}


@pytest.mark.contract
@pytest.mark.oracle
def test_the_preserved_blocks_of_the_emitted_target_are_the_post_processed_ones() -> (
    None
):
    """Section 2.2 steps 1-2, THEN ``def:emitnorm``, in the preserved block.

    THE TEST THAT GAINS MOST FROM THE 1.0.0 AMENDMENT. At 0.3.0 the emitted
    preserved block WAS the constructed one; at 1.0.0 it is the family
    ``def:emitnorm`` produces from it -- "THOSE NUMBERS **ARE** THE PRESERVED
    SECTORS OF THE EMITTED TARGET, so they are this module's own declaration to
    its consumer; and where the exact arithmetic has left the declared lattice
    they are RE-ESTABLISHED ON IT, per block".

    BOTH FAMILIES ARE ASSERTED, from band 5's ``PR_R1.emission``: the
    CONSTRUCTED value at each letter, which is ``R^cg``'s row over the columns
    times ``q_t`` and lands off the ``2^-12`` lattice, and the EMITTED value,
    which is step (2)'s rounding of it. Asserting only one of them would let the
    normalizer become the identity, or become anything else, unnoticed.

    AND WHAT THE NORMALIZER DID -- DERIVED BY HAND. The
    frozen record pins a procedure of round to nearest, absorb a
    residue, lift: its designated element ``None`` and lift ``None`` are not
    fields of ``def:emitnorm``, which keeps or snaps for fidelity.
    The EMITTED numbers and ``Delta_s`` are the frozen ones, and the derivation is
    :data:`PRR1_NORMALIZER`'s: at both settings the class is moved by step
    (2) at ``w = 0`` -- rounding to nearest, whose residue is zero -- which is
    the frozen emitted family.
    """
    outcome = reduce(rc2_artifact(), rc2_declaration(), rc2_request())
    artifact = outcome.artifact
    assert artifact is not None
    record = artifact.emission_record.blocks[0]
    for setting, constructed, emitted, residue, designated, delta in PR_R1.emission:
        for letter, value in constructed:
            # THE CONSTRUCTED FAMILY: R^cg's row over the columns times q_t,
            # formed exactly. It is NOT what is emitted.
            expected = dict(PR_R1.probe_weights)[setting] * sum(
                (
                    dict(rows)[letter] * dict(PR_R1.declared_blocks)[column]
                    for column, rows in PR_R1.descended_matrix
                ),
                start=F(0),
            )
            assert expected == value, (setting, letter)
        for letter, value in emitted:
            # THE EMITTED FAMILY: step (2)'s rounding of it, on the lattice.
            # READ PER SECTOR BLOCK: the artifact carries the list, and this
            # instance's ONE data sector is its first block.
            element = artifact.target_povm[(letter, setting)]
            block = element[0]
            assert block[0][0].re == value, (setting, letter)
            assert block[0][0].im == 0
            assert (value * 2**PR_R1.kappa).denominator == 1
            assert all(
                is_positive_semidefinite(each) for each in element
            ), (setting, letter)
        # The frozen record: no residue, no designation.
        assert residue == 0
        assert designated is None
        # The normalizer's record, derived by hand above.
        expected = PRR1_NORMALIZER[setting]
        snap = record.classes[setting]
        assert str(snap.status) == "moved"
        assert str(snap.step) == expected["step"]
        assert snap.mixing_weight == expected["mixing"]
        assert snap.hosts == expected["hosts"]
        assert not snap.support_not_preserved
        # Eq. eq:displacement, as the exact square the substrate holds.
        assert record.displacement_squared == delta * delta
        assert delta == F(11, 131072)
    assert PR_R1.lift_weight is None
    assert record.already_on_lattice is False
    # Moved classes: the sector is named provisionally as resting on A-SNAP
    # (req:emission-record), disclosed and not refused (strict is off).
    assert artifact.emission_record.moved_sectors
    assert artifact.emission_record.snapped_measurement_assumption is not None

@pytest.mark.contract
def test_requested_assurance_is_read_never_defaulted_and_never_upgraded() -> None:
    """Section 2.1 `requested_assurance`; Section 1.4; Section 2.5 fail_closed."""
    # foundations/def:tiers lists `certified` and the reductions interface's
    # `requested_assurance` row admits the three tiers and refuses only an
    # unknown value, which receives the machine-readable reason
    # ``requested_assurance_unknown``; `certified` is not a refused request.
    for asked in ("garbage",):
        outcome = reduce(
            rc2_artifact(),
            rc2_declaration(),
            rc2_request(requested_assurance=asked),
        )
        assert outcome.artifact is None
        assert outcome.refusal is not None
        assert outcome.refusal.reason is RefusalReason.REQUESTED_ASSURANCE_UNKNOWN
        assert outcome.verification_report.requested_assurance == asked
        assert (
            outcome.verification_report.receiver_bound_evaluation
            == "floating_point"
        )
    # No default is substituted for a missing datum (Section 2.5): the field is
    # required.
    with pytest.raises(TypeError):
        ReductionRequest(link_declarations=(), route="encoded")  # type: ignore[call-arg]

@pytest.mark.contract
def test_an_artifact_without_validation_results_is_refused_and_has_no_default() -> None:
    """Section 4.14 closing paragraph, the CR-B2 reading; Section 2.5 fail_closed."""
    import dataclasses

    outcome = reduce(
        rc2_artifact(validation_results_present=False), rc2_declaration(), rc2_request()
    )
    assert not outcome.emitted
    assert outcome.refusal is not None
    assert outcome.refusal.reason is RefusalReason.RECEIVER_SPEC_NOT_ACCEPTED
    fields = {f.name: f for f in dataclasses.fields(ReceiverArtifactRows)}
    assert fields["validation_results_present"].default is dataclasses.MISSING

@pytest.mark.contract
def test_the_echoed_quantifier_settings_must_agree_with_the_probe_alphabet() -> None:
    """Section 2.1 bound_quantifier_domain: "for all t in T" is the artifact's T."""
    rows = rc2_artifact(
        bound_quantifier_domain=BoundQuantifierDomain(cutoff=0, settings=("t_off",))
    )
    outcome = reduce(rows, rc2_declaration(), rc2_request())
    assert not outcome.emitted
    assert outcome.refusal is not None
    assert outcome.refusal.reason is RefusalReason.ALPHABET_OR_ORDER_MISMATCH

@pytest.mark.contract
def test_blocks_that_do_not_complete_the_conditional_family_are_refused() -> None:
    """``def:exactadm`` (d) through :func:`reduce`, on the supplier's blocks.

    THE DATUM AND THE VERDICT ARE UNCHANGED SINCE 0.1.3; THE ROW AND THE REASON
    HAVE MOVED TWICE. 0.1.3 refused this declaration under
    ``no_block_structure``; 0.2.0 split that row -- "BLOCK DIAGONALITY BELOW THE
    CUTOFF IS CARRIED BY THE DECLARED TYPE ... WHICH IS WHY THIS ROW IS THE
    STRUCTURAL HALF ONLY. THE NUMERICAL HALF IS THE NEXT ROW" -- and the
    numerical half was the tolerance row. 1.0.0 REMOVED THAT ROW AND ITS STRING
    WITH THE TOLERANCE APPARATUS, and the numerical half is now
    ``def:exactadm`` (d), "exactly complete over Y at each (t, m) WITH THAT SUM
    ROUNDING NOWHERE IN THE DECLARED ORDER", refused
    ``declaration_not_exactly_admissible``.

    ``declaration_outside_tolerance`` IS NOT IN THE VOCABULARY and this
    test asserts that too: swapping the string would not show that the OLD one
    is absent, and its absence is what makes the new row the only decider.

    The declaration is band 5's ``PR_R6`` and its numbers are the 0.3.0 ones --
    every block ``1/4`` with ``(y_mc, t_on)`` at ``1/2``, so the family sums to
    ``5/4`` at ``t_on`` -- which were ALREADY dyadic. Only the reason string
    moved.
    """
    case = PR_R6
    changed = dict(case.changed_data)
    blocks = {
        (letter, setting): (matrix([[changed["block at every (y, t)"]]]),)
        for letter in RC2_COARSE.letters
        for setting in RC2_SETTINGS
    }
    # sum over y at t_on is 5/4, which no rounding of the declared order repairs
    blocks[("y_mc", "t_on")] = (matrix([[changed["block at (y_mc, t_on)"]]]),)
    outcome = reduce(
        rc2_artifact(photon_blocks=blocks), rc2_declaration(), rc2_request()
    )
    assert not outcome.emitted
    assert outcome.refusal is not None
    assert str(outcome.refusal.reason) == case.refusal_reason
    assert outcome.refusal.reason is RefusalReason.DECLARATION_NOT_EXACTLY_ADMISSIBLE
    assert outcome.refusal.rule == case.rule
    assert "def:exactadm" in outcome.refusal.detail
    # THE STRING THAT DECIDED THIS AT 0.3.0 IS GONE FROM THE VOCABULARY.
    assert not hasattr(RefusalReason, "DECLARATION_OUTSIDE_TOLERANCE")
    assert "declaration_outside_tolerance" not in REFUSAL_REASONS_1_0_0
    # THE STRUCTURAL ROW PASSED: the blocks are declared for every v at every
    # m <= N and of the declared dimension. It is the numbers that fail.
    rows = {str(row.rule): row for row in outcome.verification_report.outcomes}
    assert rows["block_structure"].passed
    # And every other row the freeze names as admitting this declaration does.
    for name in case.admitting_rows:
        assert rows[name].passed is True, name


#: A TWO-LETTER ALPHABET: a coarse-graining on two ports and the joint
#: alphabet over it, which the total-weight test below needs.
TWO_LETTERS = ("a", "b")


def two_letter_coarse() -> CoarseGraining:
    """``cg`` with two fibres, so that BOTH letters carry a certified weight."""
    assignment = {}
    for pattern in patterns(2):
        assignment[pattern] = "a" if pattern in (frozenset(), frozenset({1})) else "b"
    return CoarseGraining(ports=2, letters=TWO_LETTERS, assignment=assignment)

@pytest.mark.contract
@pytest.mark.oracle
def test_a_declaration_reaching_total_weight_one_is_refused_end_to_end() -> None:
    """Lemma ``lem:ple1`` and Remark ``rem:peqone``: refused, never clipped."""
    coarse = two_letter_coarse()
    rows = rc2_artifact(
        detection_alphabet=TWO_LETTERS,
        photon_blocks={
            (letter, setting): (matrix([[F(1, 2)]]),)
            for letter in TWO_LETTERS
            for setting in RC2_SETTINGS
        },
        outcome_coarse_graining=coarse,
        dark_count_channel=product_form_dark_counts(2, {1: F(0), 2: F(0)}),
        high_photon_bounds=(
            HighPhotonBound.uniform(coarse.fibre("a"), F(1), RC2_SETTINGS),
        ),
    )
    joint = tuple(
        (letter, setting) for setting in RC2_SETTINGS for letter in TWO_LETTERS
    )
    outcome = reduce(
        rows,
        rc2_declaration(detection_alphabet=TWO_LETTERS, joint_alphabet=joint),
        rc2_request(),
    )
    assert not outcome.emitted
    assert outcome.refusal is not None
    assert outcome.refusal.reason is RefusalReason.TOTAL_WEIGHT_NOT_BELOW_ONE


@pytest.mark.contract
def test_both_live_rungs_reach_the_verification_report() -> None:
    """The ladder has TWO live rungs and the record carries whichever was asked.

    ``estimate`` is not the only value: ``first-order`` is the headline rung
    (PRINCIPLES.md section 2.1) and the requested-assurance row admits it, so a
    record that could only be ``estimate`` would have decided a tier the
    request declares. NEITHER CHANGES ANYTHING EMITTED: the artifact is the
    same object at both and the emitted ``status`` is ``exact``, which is what
    makes the record a record of the REQUEST and not of a result tier.
    """
    for rung in ("estimate", "first-order", "certified"):
        outcome = reduce(
            rc2_artifact(), rc2_declaration(), rc2_request(requested_assurance=rung)
        )
        assert outcome.artifact is not None, outcome.refusal
        assert outcome.artifact.verification_report.requested_assurance == rung
        assert str(outcome.artifact.status) == "exact"
    # And a rung the ladder does not have is REFUSED rather than demoted
    # (`certified` is a rung; def:tiers).
    refused = reduce(
        rc2_artifact(), rc2_declaration(), rc2_request(requested_assurance="garbage")
    )
    assert refused.artifact is None
    assert refused.refusal is not None
    assert str(refused.refusal.reason) == "requested_assurance_unknown"
    # AND THE DETAIL A CALLER READS SAYS WHAT THE LADDER SAYS. The row is a
    # MEMBERSHIP TEST over the live rungs, so its refusal may not use a
    # shelving vocabulary: no rung is shelved, and a rung outside the ladder
    # is simply not on it. The detail ECHOES THE CALLER'S OWN STRING, so
    # the vocabulary is checked on a request that does not spell it.
    off_ladder = reduce(
        rc2_artifact(),
        rc2_declaration(),
        rc2_request(requested_assurance="a rung this ladder does not have"),
    )
    assert off_ladder.refusal is not None
    assert str(off_ladder.refusal.reason) == "requested_assurance_unknown"
    detail = off_ladder.refusal.detail.lower()
    assert "shelv" not in detail
    # `certified` is a live rung (def:tiers), so the detail,
    # which lists the live rungs, names it.
    assert "spec/architecture.md 2.8" in off_ladder.refusal.detail
    assert "'estimate'" in detail and "'first-order'" in detail
    assert "'certified'" in detail


@pytest.mark.contract
def test_an_off_lattice_ge_constant_is_rounded_down_and_recorded() -> None:
    """cor:entries (iii): DOWN for >=, UP for <=, recorded per entry.

    NOT REFUSED FOR BEING OFF THE LATTICE: the corollary ROUNDS, because "a
    lower c enlarges the feasible set for >= and AttSet_CList only grows --
    which is the safe direction, a smaller admissible set being the one in
    which thm:licence's inclusion can fail". An EQUALITY is the one that is
    refused, and that half is already tested.

    THE CASE, BY HAND. The licensed route emits the entry
    ``O^ = F^FSS_o - p_o Pi_Flag`` at ``c = 0``. A caller re-requesting that
    same operator at ``c = 1/10000`` has declared a constant off the
    ``2^-12`` lattice: ``lat(1/10000) = 2^-12 floor(4096/10000) = 0``, so the
    rounding is DOWN to exactly ``0``, the certificate is discharged AT THE
    ROUNDED CONSTANT, and the entry is emitted at ``0``. The direction is
    recorded per entry in ``emission_record``, which is where thm:emit (iv)
    puts it.
    """
    from certiqs_key.reductions.inputs import CarriedOperatorRequest

    licensed = rc2_request(
        route="licensed",
        link_declarations=(
            LinkDeclaration(stage=LinkStage.RECEIVER, kind=LinkKind.FSS),
            LinkDeclaration(stage=LinkStage.RECEIVER, kind=LinkKind.PINCHING),
        ),
    )
    baseline = reduce(rc2_artifact(), rc2_declaration(), licensed).artifact
    assert baseline is not None
    module_built = baseline.constraint_list[0]
    assert module_built.constant == 0
    # The same operator, re-requested at a constant off the declared lattice.
    off_lattice = F(1, 10000)
    assert off_lattice * (1 << KAPPA_FIXTURE) != int(off_lattice * (1 << KAPPA_FIXTURE))
    asked = CarriedOperatorRequest(
        label="the same O^ at an off-lattice c",
        # A CALLER DECLARES ONE ARRAY -- the carried_operators row's own form
        # -- so the test forms the direct sum of the emitted entry's
        # sector-block list; the module splits it back against the sector map.
        operator=direct_sum(list(module_built.operator)),
        relation=module_built.relation,
        constant=off_lattice,
        certificate_kind=module_built.certificate_kind,
        certified_against=module_built.certified_against,
    )
    outcome = reduce(
        rc2_artifact(),
        rc2_declaration(),
        rc2_request(
            route="licensed",
            link_declarations=licensed.link_declarations,
            carried_operators=(asked,),
        ),
    )
    artifact = outcome.artifact
    assert artifact is not None, outcome.refusal
    emitted = next(
        entry for entry in artifact.constraint_list if entry.label == asked.label
    )
    # ROUNDED DOWN, and emitted at the rounded constant rather than at the
    # declared one -- "the entry is emitted at the constant its certificate is
    # discharged at".
    assert emitted.constant == 0
    assert emitted.constant < off_lattice
    # RECORDED PER ENTRY, in emission_record (thm:emit (iv)).
    directions = {
        label: (constant, direction)
        for label, constant, direction in (
            artifact.emission_record.constant_rounding_directions
        )
    }
    assert asked.label in directions
    constant, direction = directions[asked.label]
    assert constant == "0"
    assert direction.startswith("down")
    assert "cor:entries (iii)" in direction
    # AND NOTHING IS RECORDED FOR AN ENTRY THAT WAS NOT ROUNDED: the
    # module-built entry's constant is 0 and already on the lattice.
    assert module_built.label not in directions
    assert artifact.emission_record.as_machine_record()[
        "constant_rounding_directions"
    ] == [
        {"entry": asked.label, "constant": "0", "direction": direction},
    ]


@pytest.mark.contract
def test_every_sector_projector_travels_with_the_transported_set() -> None:
    """def:reduction-instance (I3); cor:entries (i); prop:flat-instance (I3).

    "(Pi_s, >=, 0) travels with the transported set, ON EVERY ROUTE, which is
    where (I3) puts every sector projector and where the artifact records the
    certificate case per entry." THE CONSTRAINT LIST IS EMPTY ON THE
    ``encoded`` ROUTE and carries the instance's own flag-sector entries on the
    ``licensed`` one, so this row is the only place that certificate can be
    emitted.

    ``prop:flat-instance`` (I3) spells the flat instance's set out:
    ``{Pi_leq, Pi_flag} u {Pi_(m)}_{m<=N} u {Pi_(f)}_{f in V}`` -- the two SUMS
    the cutoff split transports besides, and every sector projector. LINEARITY
    DOES NOT RECOVER THE SECOND FROM THE FIRST: (I3) transports every real
    combination of what is DECLARED, and ``Pi_(m)`` is not a combination of
    ``Pi_leq`` and ``Pi_flag``.
    """
    licensed_links = (
        LinkDeclaration(stage=LinkStage.RECEIVER, kind=LinkKind.FSS),
        LinkDeclaration(stage=LinkStage.RECEIVER, kind=LinkKind.PINCHING),
    )
    for route in ("encoded", "licensed"):
        request = (
            rc2_request()
            if route == "encoded"
            else rc2_request(route="licensed", link_declarations=licensed_links)
        )
        outcome = reduce(rc2_artifact(), rc2_declaration(), request)
        artifact = outcome.artifact
        assert artifact is not None, outcome.refusal
        sectors = artifact.target_descriptor.sectors
        carried = {
            entry.target_operator for entry in artifact.transported_operators
        }
        for projector in sectors.projectors():
            assert projector in carried
        # And the sums the instance transports besides are still there.
        assert len(artifact.transported_operators) == len(sectors.labels) + 2
        assert [entry.label for entry in artifact.transported_operators][:2] == [
            "Pi_leq",
            "Pi_flag",
        ]
        for entry in artifact.transported_operators:
            assert str(entry.relation) == ">="
            assert entry.constant == 0
            assert str(entry.certificate_kind) == "positivity"
        # The certificate is emitted HERE and not as a constraint entry: the
        # list is empty on the encoded route and holds the flag-sector entries
        # on the licensed one, neither of them a sector projector.
        labels = {entry.label for entry in artifact.constraint_list}
        assert labels.isdisjoint(
            {entry.label for entry in artifact.transported_operators}
        )
        if route == "encoded":
            assert artifact.constraint_list == ()


@pytest.mark.contract
def test_a_constant_outside_the_band_is_refused_and_never_reported_as_rounded() -> None:
    """eq:latinv has TWO conjuncts and cor:entries (iii) restores both.

    ``|c| <= 1`` "is what makes the value's significand fit in kappa bits"
    (``foundations.exact.on_lattice_scalar``). A constant of modulus above one is
    ALREADY an integer multiple of ``2^-kappa``, so rounding onto the lattice
    moves nothing: the entry would be emitted off ``eq:latinv`` with a
    direction string for a value nothing moved. The band is therefore REFUSED
    under every relation, and ``rounded_constant`` never returns a value for
    which ``on_lattice_scalar`` is false.
    """
    from certiqs_key.foundations.exact import on_lattice_scalar
    from certiqs_key.reductions.constraints import rounded_constant
    from certiqs_key.reductions.errors import MalformedInputError
    from certiqs_key.reductions.inputs import CarriedOperatorRequest
    from certiqs_key.reductions.reasons import CertificateKind, Relation

    # (a) the helper: in the band it rounds and says which way; outside it, it
    # refuses to return a value at all rather than return one off eq:latinv.
    for relation in (Relation.GE, Relation.LE):
        for constant in (F(3, 2), F(-3, 2)):
            with pytest.raises(MalformedInputError):
                rounded_constant(constant, relation, KAPPA_FIXTURE)
        for constant in (F(1, 3), F(-1, 3), F(1), F(-1), F(1, 4)):
            value, direction = rounded_constant(constant, relation, KAPPA_FIXTURE)
            assert on_lattice_scalar(value, KAPPA_FIXTURE), (constant, relation)
            if value == constant:
                assert direction.startswith("unchanged")
            else:
                assert direction.startswith("down" if relation is Relation.GE else "up")

    # (a2) AND THE EQUALITY, which the same docstring says never reaches the
    # function either: an equality has NO LOOSENING DIRECTION, so moving its
    # constant produces a DIFFERENT constraint rather than a weaker one, which
    # is why cor:entries (iii) refuses that case rather than rounding it. The
    # guard was missing where the band's was present, so an exported symbol
    # enforced its stated contract for one of its two impossible inputs and not
    # the other.
    for constant in (F(1, 3), F(-1, 3), F(3, 2)):
        with pytest.raises(MalformedInputError):
            rounded_constant(constant, Relation.EQ, KAPPA_FIXTURE)
    # On the lattice it is returned unchanged under the equality too.
    for constant in (F(0), F(1), F(-1), F(1, 4)):
        value, direction = rounded_constant(constant, Relation.EQ, KAPPA_FIXTURE)
        assert value == constant
        assert direction.startswith("unchanged")

    # (b) end to end: the request is refused NAMING THE BAND, on the relation
    # the rounding rule would otherwise have taken.
    licensed = rc2_request(
        route="licensed",
        link_declarations=(
            LinkDeclaration(stage=LinkStage.RECEIVER, kind=LinkKind.FSS),
            LinkDeclaration(stage=LinkStage.RECEIVER, kind=LinkKind.PINCHING),
        ),
    )
    baseline = reduce(rc2_artifact(), rc2_declaration(), licensed).artifact
    assert baseline is not None
    module_built = baseline.constraint_list[0]
    for relation in (Relation.GE, Relation.LE, Relation.EQ):
        asked = CarriedOperatorRequest(
            label="the same O^ at a constant outside the band",
            operator=direct_sum(list(module_built.operator)),
            relation=relation,
            constant=F(3, 2),
            certificate_kind=CertificateKind.POSITIVITY,
            certified_against=module_built.certified_against,
        )
        outcome = reduce(
            rc2_artifact(),
            rc2_declaration(),
            rc2_request(
                route="licensed",
                link_declarations=licensed.link_declarations,
                carried_operators=(asked,),
            ),
        )
        assert outcome.artifact is None
        assert outcome.refusal is not None
        assert str(outcome.refusal.reason) == "constraint_without_certificate"
        assert "eq:latinv" in outcome.refusal.detail
        assert "modulus" in outcome.refusal.detail


@pytest.mark.contract
def test_a_builder_that_under_declares_the_transported_set_is_refused() -> None:
    """def:reduction-instance (I3) is decided of the BUILDER, not of a request.

    (I3) is a condition on the object a submodule hands the core, so no
    fail-closed row can decide it: a row decides a DECLARATION. The instance
    type decides it in ``__post_init__``, beside the (I4) locator check, and a
    builder that returns the two sums alone raises rather than emitting an artifact that
    carries
    fewer certified operators than the instance earns.
    """
    from dataclasses import replace

    from certiqs_key.reductions.emit import reduce as core_reduce
    from certiqs_key.reductions.errors import MalformedInputError
    from certiqs_key.reductions.inputs import ReductionCall
    from certiqs_key.reductions.instance import BuildContext, BuildOutcome
    from certiqs_key.reductions.wpfss.api import FlatInstanceBuilder

    class _UnderDeclaring:
        """The flat builder with the per-sector half of (I3) dropped."""

        def build(self, context: BuildContext) -> BuildOutcome:
            outcome = FlatInstanceBuilder().build(context)
            assert outcome.instance is not None
            return BuildOutcome(
                rows=outcome.rows,
                outcomes=outcome.outcomes,
                instance=replace(
                    outcome.instance,
                    transported=outcome.instance.transported[:2],
                ),
            )

    call = ReductionCall(rc2_artifact(), rc2_declaration(), rc2_request())
    with pytest.raises(MalformedInputError) as raised:
        core_reduce(call, _UnderDeclaring())
    assert "def:reduction-instance (I3)" in str(raised.value)
    # The honest builder is not refused, and the same call emits.
    assert core_reduce(call, FlatInstanceBuilder()).artifact is not None


@pytest.mark.contract
def test_no_full_space_array_is_emitted_anywhere_in_the_artifact() -> None:
    """The outputs table, ``target_povm`` and ``target_descriptor``; architecture 2.8.

    "F_v = (+)_s F_v^(s) IS WHAT THAT LIST MEANS, NOT AN OBJECT THE ARTIFACT
    CARRIES", and "NO FULL dim H(Q) x dim H(Q) ARRAY IS EMITTED, HERE OR
    ANYWHERE IN THIS ARTIFACT". So every ``Q``-operator in the record is a LIST
    OF SQUARES whose dimensions ARE the sector map's, and the dense rendering
    is something a reader may form and the producer never emits
    (spec/architecture.md 2.8-2.9).

    ASSERTED ON THE RECORD AND NOT ONLY ON THE OBJECT, because the record is
    what a key-rate run logs and what a consumer reads: at RC2 the sector map
    has nine one-dimensional sectors, so a dense rendering would put eighty
    zeros in every eighty-one entries.
    """
    outcome = reduce(rc2_artifact(), rc2_declaration(), rc2_request())
    artifact = outcome.artifact
    assert artifact is not None, outcome.refusal
    record = artifact.as_machine_record()
    descriptor = record["target_descriptor"]
    assert isinstance(descriptor, dict)
    dims = list(descriptor["sector_dimensions"])  # type: ignore[call-overload]
    total = descriptor["dimension"]
    assert sum(dims) == total and len(dims) > 1

    def block_dims(operator: object) -> list[int]:
        # ONE SQUARE BLOCK PER SECTOR: the serialized form is a list of
        # matrices, each a list of rows of [re, im] string pairs.
        assert isinstance(operator, list)
        out: list[int] = []
        for block in operator:
            assert isinstance(block, list)
            assert all(len(row) == len(block) for row in block)
            out.append(len(block))
        return out

    emitted = record["target_povm"]
    assert isinstance(emitted, dict)
    for element in emitted.values():
        assert block_dims(element) == dims, block_dims(element)
    transported = record["transported_operators"]
    assert isinstance(transported, list)
    for item in transported:
        assert block_dims(item["target_operator"]) == dims, item["label"]
    # And the objects behind the record carry the same list, so nothing is
    # assembled on the way out either.
    for element in artifact.target_povm.values():
        assert [len(block) for block in element] == dims
    for entry in artifact.transported_operators:
        assert [len(block) for block in entry.target_operator] == dims
    # AND THE CONSTRAINT LIST, on the route that has one: "NO FULL
    # dim H(Q) x dim H(Q) ARRAY IS EMITTED, HERE OR ANYWHERE IN THIS ARTIFACT"
    # is a statement about the whole record, and an entry's hat O_k is an
    # operator on Q like any other.
    licensed_links = (
        LinkDeclaration(stage=LinkStage.RECEIVER, kind=LinkKind.FSS),
        LinkDeclaration(stage=LinkStage.RECEIVER, kind=LinkKind.PINCHING),
    )
    licensed_outcome = reduce(
        rc2_artifact(),
        rc2_declaration(),
        rc2_request(route="licensed", link_declarations=licensed_links),
    )
    licensed = licensed_outcome.artifact
    assert licensed is not None, licensed_outcome.refusal
    entries = licensed.as_machine_record()["constraint_list"]
    assert isinstance(entries, list)
    assert entries, "the licensed route emits entries; the check needs them"
    for entry in entries:
        assert block_dims(entry["operator"]) == dims, entry["label"]
    for built in licensed.constraint_list:
        assert [len(block) for block in built.operator] == dims, built.label


@pytest.mark.contract
def test_a_declared_operator_outside_the_sector_blocks_is_refused_not_truncated() -> (
    None
):
    """The ``carried_operators`` row's admitted form, decided on the declaration.

    A CALLER'S ARRAY IS THE ONE PLACE A DENSE OPERATOR ENTERS THIS MODULE, and
    the row admits it in the form ``sum_v sum_s alpha_{v,s} Pi_s F_v Pi_s + Z``
    with ``Z`` a real combination of sector projectors -- every operator of
    which is sector-block-diagonal. The entry it becomes is carried as its
    SECTOR-BLOCK LIST, like every other operator on ``Q``, so the array is
    split against the sector map; an array with a nonzero entry OUTSIDE the
    blocks would be a different operator once split, and reading its diagonal
    blocks would emit an operator the caller did not declare.

    That truncation is the latent risk of carrying an entry densely, and
    spec/architecture.md 2.9's
    reasoning -- the off-sector part "cannot be constructed once a producer
    emits per sector" -- covers what a PRODUCER builds and not what a CALLER
    declares. So the one path that can still present one decides it and refuses
    fail-closed, naming the row; nothing is silently dropped.
    """
    from certiqs_key.reductions.inputs import CarriedOperatorRequest

    licensed = rc2_request(
        route="licensed",
        link_declarations=(
            LinkDeclaration(stage=LinkStage.RECEIVER, kind=LinkKind.FSS),
            LinkDeclaration(stage=LinkStage.RECEIVER, kind=LinkKind.PINCHING),
        ),
    )
    baseline = reduce(rc2_artifact(), rc2_declaration(), licensed).artifact
    assert baseline is not None
    module_built = baseline.constraint_list[0]
    honest = direct_sum(list(module_built.operator))
    # The same operator with ONE entry moved outside the blocks: the (0, 1)
    # entry couples the first sector to the second, and every sector of this
    # fixture is one-dimensional, so it lies in no block.
    rows = [list(row) for row in honest]
    rows[0][1] = Cx(F(1, 4), F(0))
    rows[1][0] = Cx(F(1, 4), F(0))
    off_block = tuple(tuple(row) for row in rows)

    def _ask(operator: Matrix, label: str) -> object:
        return reduce(
            rc2_artifact(),
            rc2_declaration(),
            rc2_request(
                route="licensed",
                link_declarations=licensed.link_declarations,
                carried_operators=(
                    CarriedOperatorRequest(
                        label=label,
                        operator=operator,
                        relation=module_built.relation,
                        constant=module_built.constant,
                        certificate_kind=module_built.certificate_kind,
                        certified_against=module_built.certified_against,
                    ),
                ),
            ),
        )

    outcome = _ask(off_block, "an O^ with an off-sector entry")
    assert outcome.artifact is None  # type: ignore[attr-defined]
    refusal = outcome.refusal  # type: ignore[attr-defined]
    assert refusal is not None
    assert str(refusal.reason) == "constraint_without_certificate"
    assert "OUTSIDE THE SECTOR BLOCKS" in refusal.detail
    assert "refused rather than truncated" in refusal.detail
    assert "(0, 1)" in refusal.detail
    # AND THE HONEST ARRAY IS NOT REFUSED: the same request with the declared
    # operator inside the blocks emits, so the refusal is the off-sector entry
    # and not the shape of the request.
    honest_outcome = _ask(honest, "the same O^, inside the blocks")
    assert honest_outcome.artifact is not None, honest_outcome.refusal  # type: ignore[attr-defined]
    # An array that is not an operator on Q at all is refused naming dim H(Q).
    wrong_size = _ask(identity(2), "an O^ of the wrong dimension")
    assert wrong_size.artifact is None  # type: ignore[attr-defined]
    assert "dim H(Q)" in wrong_size.refusal.detail  # type: ignore[attr-defined]


@pytest.mark.contract
def test_a_builder_that_declares_an_entry_without_a_locator_is_refused() -> None:
    """def:reduction-instance (I4), the TWIN of the (I3) gate above.

    (I4) asks that a module-built entry carry the INSTANCE'S OWN discharge
    locator: ``cor:entries`` (iii) emits an instance's own entry "at the
    constant its certificate is discharged at", and the certificate is the
    instance's -- so a module-built entry with no locator would reach the
    verification report attributed to nothing, or to another submodule's
    corollary. Like (I3) it is a condition on the object a submodule hands the
    core, so no fail-closed row can decide it, and the instance type decides it
    in ``__post_init__``.
    """
    from dataclasses import replace

    from certiqs_key.reductions.emit import reduce as core_reduce
    from certiqs_key.reductions.errors import MalformedInputError
    from certiqs_key.reductions.inputs import ReductionCall
    from certiqs_key.reductions.instance import BuildContext, BuildOutcome
    from certiqs_key.reductions.wpfss.api import FlatInstanceBuilder

    class _WithoutLocators:
        """The flat builder with the entries' discharge locators dropped."""

        def build(self, context: BuildContext) -> BuildOutcome:
            outcome = FlatInstanceBuilder().build(context)
            assert outcome.instance is not None
            return BuildOutcome(
                rows=outcome.rows,
                outcomes=outcome.outcomes,
                instance=replace(outcome.instance, module_built_locators={}),
            )

    # THE LICENSED ROUTE, because that is where an instance builds entries: on
    # the encoded route the list is empty and there is nothing to attribute.
    licensed_links = (
        LinkDeclaration(stage=LinkStage.RECEIVER, kind=LinkKind.FSS),
        LinkDeclaration(stage=LinkStage.RECEIVER, kind=LinkKind.PINCHING),
    )
    call = ReductionCall(
        rc2_artifact(),
        rc2_declaration(),
        rc2_request(route="licensed", link_declarations=licensed_links),
    )
    with pytest.raises(MalformedInputError) as raised:
        core_reduce(call, _WithoutLocators())
    assert "def:reduction-instance (I4)" in str(raised.value)
    # The honest builder is not refused, and the same call emits with every
    # entry attributed to the instance's own corollary.
    artifact = core_reduce(call, FlatInstanceBuilder()).artifact
    assert artifact is not None
    assert artifact.constraint_list
    certificate = next(
        outcome
        for outcome in artifact.verification_report.outcomes
        if str(outcome.rule) == "constraint_certificate"
    )
    assert "cor:fssinstance" in certificate.detail
