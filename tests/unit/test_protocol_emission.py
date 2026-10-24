"""The emission pipeline's structural guarantees, asserted of the CODE alone.

No registry import here: these are properties of the implementation that must
hold whatever the frozen cases say, and a unit test that reached for the oracle
would only be a slower copy of the golden suite. What is held fixed:

* the gate mapping is TOTAL over the seven axes, with no combination reaching
  the end unhandled and no combination producing a fourth token;
* ``passed vacuously`` never collapses into a boolean anywhere on the surface;
* a refusal emits NO declaration, structurally and not by convention;
* on the EMISSION paths -- which is where they could still go wrong --
  no default is substituted, no entry is dropped and no licence is synthesized;
* ``docking`` is not reachable from the package surface.
"""

from __future__ import annotations

import itertools
from dataclasses import replace
from fractions import Fraction as F

import pytest
from instances.bb84.specification import (
    ConjugationConvention,
    bb84_specification,
    conjugation_example_specification,
)
from protocol_blocks import source_part

from certiqs_key.domain.chain import (
    ChainLink,
    LinkStage,
    LinkStatus,
    ReductionChain,
    Side,
    SystemDescriptor,
)
from certiqs_key.domain.constraints import AttackSetLicense, ConstraintEntry, Relation
from certiqs_key.foundations.blocks import BlockKind, BlockOperator, SectorStructure
from certiqs_key.foundations.errors import HypothesisError, MalformedInputError
from certiqs_key.foundations.exact import matrix
from certiqs_key.protocol_compiler import (
    DECLARATION_SLOT_KEYS,
    CandidateDeclaration,
    CertificateState,
    CompilationResult,
    DirectPovm,
    EmissionOutcome,
    GateEntry,
    GateId,
    GateInputs,
    GateReport,
    GateVerdict,
    Party,
    PublicChoices,
    Refusal,
    RefusalReason,
    SourceMode,
    SpecConstraints,
    compile_specification,
    decide_emission,
    emitted_constraint_list,
    resolve_gates,
    resolve_povm,
    weighted_family,
)
from certiqs_key.protocol_compiler.chain import identity_channel
from certiqs_key.protocol_compiler.declared_premises import is_band_a
from certiqs_key.protocol_compiler.spec import (
    ProtocolSpecification,
    PublicPart,
    ReceiverPart,
    Sifting,
    SourcePart,
    default_party_partition,
)
from certiqs_key.transmitter import (
    RetentionAttestation,
    SourceReplacementCertificate,
    SourceSpecification,
    emit_artifact,
)

pytestmark = pytest.mark.contract


def _inputs(
    validator_passed: bool,
    emitted_mode: SourceMode,
    alice_dim: int,
    certificate: CertificateState,
    has_entries: bool,
    licensed: bool,
    licence: bool,
) -> GateInputs | None:
    """Return the inputs, or ``None`` where the contract's typing excludes them."""
    try:
        return GateInputs(
            validator_passed=validator_passed,
            emitted_mode=emitted_mode,
            alice_dim=alice_dim,
            certificate=certificate,
            has_constraint_entries=has_entries,
            list_licensed=licensed,
            license_present=licence,
        )
    except MalformedInputError:
        return None


ALL_POINTS = list(
    itertools.product(
        (True, False),
        (SourceMode.TRUSTED, SourceMode.UNTRUSTED),
        (1, 2),
        tuple(CertificateState),
        (True, False),
        (True, False),
        (True, False),
    )
)


# ---------------------------------------------------------------------------
#  The gate mapping is total
# ---------------------------------------------------------------------------


def test_the_gate_mapping_is_total_over_the_seven_axes() -> None:
    """Every expressible combination reaches exactly one outcome."""
    assert len(ALL_POINTS) == 192
    expressible = 0
    excluded = 0
    for point in ALL_POINTS:
        inputs = _inputs(*point)
        if inputs is None:
            excluded += 1
            continue
        expressible += 1
        resolution = resolve_gates(inputs, "V1")
        assert resolution.outcome in tuple(EmissionOutcome)
        assert len(resolution.report.entries) == 4
        assert tuple(entry.gate for entry in resolution.report.entries) == tuple(GateId)
    assert expressible + excluded == 192
    assert expressible > 0
    assert excluded > 0


def test_no_combination_produces_a_fourth_token() -> None:
    for point in ALL_POINTS:
        inputs = _inputs(*point)
        if inputs is None:
            continue
        for entry in resolve_gates(inputs, "V1").report.entries:
            assert entry.verdict is None or entry.verdict in tuple(GateVerdict)


def test_a_refusal_never_carries_an_eligibility_flag() -> None:
    for point in ALL_POINTS:
        inputs = _inputs(*point)
        if inputs is None:
            continue
        resolution = resolve_gates(inputs, "V1")
        if resolution.outcome is EmissionOutcome.REFUSAL:
            assert resolution.key_length_eligible is None
            assert resolution.refusal is not None
            assert resolution.emits_source_replacement_license is False
        else:
            assert resolution.key_length_eligible is not None
            assert resolution.refusal is None


def test_a_gate_with_no_subject_carries_no_verdict() -> None:
    """Definition ``def:eligible`` is stated on an EMITTED declaration."""
    for point in ALL_POINTS:
        inputs = _inputs(*point)
        if inputs is None:
            continue
        for entry in resolve_gates(inputs, "V1").report.entries:
            if entry.engaged is None:
                assert entry.verdict is None
            if entry.verdict is not None:
                assert entry.engaged is True


# ---------------------------------------------------------------------------
#  The third token does not collapse
# ---------------------------------------------------------------------------


def test_passed_vacuously_is_not_passed_anywhere() -> None:
    assert GateVerdict.PASSED_VACUOUSLY is not GateVerdict.PASSED
    assert str(GateVerdict.PASSED_VACUOUSLY) != str(GateVerdict.PASSED)
    assert not hasattr(GateEntry, "passed")
    for point in ALL_POINTS:
        inputs = _inputs(*point)
        if inputs is None:
            continue
        report = resolve_gates(inputs, "V1").report
        record = report.as_machine_record()
        gates = record["gates"]
        assert isinstance(gates, list)
        for line in gates:
            assert isinstance(line, dict)
            if line["verdict"] == "passed vacuously":
                # The machine record keeps the third token, and carries the
                # degeneration record beside it.
                assert line["degeneration"] is not None
            else:
                assert line["degeneration"] is None


def test_a_vacuous_verdict_without_its_record_is_refused() -> None:
    """Section 2.2: the record accompanies the third token 'where it applies'."""
    with pytest.raises(MalformedInputError):
        GateEntry(gate=GateId.G3A, engaged=True, verdict=GateVerdict.PASSED_VACUOUSLY)
    with pytest.raises(MalformedInputError):
        GateEntry(
            gate=GateId.G3A,
            engaged=True,
            verdict=GateVerdict.PASSED,
            degeneration="not applicable here",
        )
    with pytest.raises(MalformedInputError):
        GateEntry(gate=GateId.G2, engaged=None, verdict=GateVerdict.PASSED)


def test_the_report_names_every_gate_and_can_be_read_by_name() -> None:
    report = resolve_gates(
        GateInputs(
            validator_passed=True,
            emitted_mode=SourceMode.UNTRUSTED,
            alice_dim=2,
            certificate=CertificateState.ABSENT,
            has_constraint_entries=True,
            list_licensed=True,
            license_present=False,
        )
    ).report
    assert isinstance(report, GateReport)
    for gate in GateId:
        assert report.entry(gate).gate is gate
    with pytest.raises(KeyError):
        report.entry("G4")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
#  A refusal emits no declaration -- structurally
# ---------------------------------------------------------------------------


def test_a_result_carries_a_declaration_or_a_refusal_and_never_both() -> None:
    declaration = _emitted()
    refusal = Refusal(reason=RefusalReason.CHECK_V3_FAILED, detail="a defect")
    common: dict[str, object] = {
        "key_length_eligible": None,
        "gate_report": None,
        "reduction_chain_record": {},
        "validation": None,
        "chain": compile_specification(
            bb84_specification(F(1, 2), F(1, 2), F(1, 2), F(1, 2))
        ).chain,
        "gates": None,
        "certificate": None,
        "source_replacement_license": None,
        "verified_witness": None,
    }
    with pytest.raises(MalformedInputError):
        CompilationResult(declaration=declaration, refusal=refusal, **common)  # type: ignore[arg-type]
    with pytest.raises(MalformedInputError):
        CompilationResult(declaration=None, refusal=None, **common)  # type: ignore[arg-type]
    with pytest.raises(MalformedInputError):
        CompilationResult(
            declaration=None,
            refusal=refusal,
            **{**common, "key_length_eligible": True},  # type: ignore[arg-type]
        )


def test_a_refused_compilation_emits_no_declaration_slot() -> None:
    result = compile_specification(
        conjugation_example_specification(ConjugationConvention.OMITTED)
    )
    assert result.refuses is True
    assert result.declaration is None
    record = result.as_machine_record()
    from certiqs_key.protocol_compiler import DECLARATION_SLOT_KEYS

    for key in DECLARATION_SLOT_KEYS:
        assert record[key] is None, key
    assert record["label_index_map"] is None
    assert record["key_length_eligible"] is None
    assert record["refusal"] is not None


def test_the_machine_record_carries_all_twenty_three_keys_at_both_outcomes() -> None:
    from certiqs_key.protocol_compiler import OUTPUT_KEYS

    emission = compile_specification(
        bb84_specification(F(1, 2), F(1, 2), F(1, 2), F(1, 2))
    ).as_machine_record()
    refusal = compile_specification(
        conjugation_example_specification(ConjugationConvention.OMITTED)
    ).as_machine_record()
    # TWENTY-ONE OUTPUT KEYS AT 0.1.4, TWENTY-THREE AT 0.3.0: `sector_block_kind`
    # and `constraint_rhs_tag` are new, NO EXISTING KEY IS REMOVED OR RENAMED,
    # and what is superseded is the COUNT (`SUPERSEDED_BY_SCOPE_0_3_0`, the key
    # tuples read as complete lists).
    #
    # The record carries TWENTY-SEVEN keys: the twenty-three of `OUTPUT_KEYS`
    # -- the frozen tuple -- plus the four interface.yaml fixes on its own and
    # says "travel with them". The frozen twenty-three are therefore asserted
    # as a SUBSET and the four additions BY NAME, which a count would not
    # catch; the next test asserts their values. The fourth addition is
    # `assumption_bindings`, the declared values each ledger row binds, which
    # the interface fixes beside `assumption_ledger`.
    additions = {
        "choice_weighting_record",
        "assumption_ledger",
        "assumption_bindings",
        "mathematical_spec_version",
    }
    for record in (emission, refusal):
        assert set(OUTPUT_KEYS) <= set(record)
        assert set(record) - set(OUTPUT_KEYS) == additions
        assert len(record) == 27
    assert emission["refusal"] is None
    assert emission["key_length_eligible"] is True
    assert refusal["gate_report"] is not None


def test_the_emitted_record_carries_its_ledger_and_its_version() -> None:
    """PRINCIPLES.md 2.1; the outputs table's three ``fixed_here`` rows.

    "Every key rate carries its assumptions ... a machine-generated manifest
    of the assumption IDs, module versions and claim graph it rests on", and
    both sibling modules emit one.
    """
    from certiqs_key.protocol_compiler import MATHEMATICAL_SPEC_VERSION

    result = compile_specification(
        bb84_specification(F(1, 2), F(1, 2), F(1, 2), F(1, 2))
    )
    record = result.as_machine_record()
    # HAND-EDITED FROZEN EXPECTATION: the emitted pin is an accepted version of
    # spec/modules/protocol-compiler/module.yaml. AN ARTEFACT MAY NOT CLAIM A
    # DRAFT VERSION. Written by hand when the pin moves, never
    # regenerated from the code.
    assert record["mathematical_spec_version"] == "protocol-compiler@0.23.0"
    assert record["mathematical_spec_version"] == MATHEMATICAL_SPEC_VERSION

    ledger = record["assumption_ledger"]
    assert isinstance(ledger, list)
    # THE ALWAYS ROWS. A-SPEC's key is ``specification_describes_apparatus``.
    for key in (
        "specification_describes_apparatus",
        "round_homogeneity_declaration",
    ):
        assert key in ledger, key
    # A-LINK: everywhere but Band A, thm:band-a (v) proving every clause of the
    # identity link, which req:band-a-identity-link decides the one link is
    # (channel as data, gamma the identity, (C4) decided); this instance is
    # Band A. There is no A-BLOCK row
    # (rem:block-restriction).
    assert "reduction_chain_sound" not in ledger
    assert "block_diagonal_feasible_set" not in ledger
    # A-COIN: a public choice IS declared on Alice's side at this instance.
    assert "public_choice_weights" in ledger
    # A-IDEAL: BAND A ONLY, and this instance is Band A. A-RECV is no row of
    # this ledger on any route (assumption_ledger.a_recv_not_emitted_note).
    assert "ideal_qubit_receiver" in ledger
    assert "receiver_artifact_accepted" not in ledger
    # There is no A-PRESENT: the physical family's exact admissibility is
    # def:well-formed-spec (iv), decided on every route, and no ledger carries a
    # key for it.
    assert "presented_receiver_family" not in ledger
    # A-ALICE-MEAS: wherever no source-replacement certificate is demanded
    # (untrusted-source mode, or d_A = 1). This instance is trusted at
    # d_A = 2, where the certificate is demanded, so the row is absent.
    assert result.declaration.alice_dim == 2
    assert "alice_measurement_as_declared" not in ledger
    # A-LIC: not engaged at an empty CList (thm:band-a (iii)).
    assert result.declaration is not None
    assert result.declaration.constraint_list == ()
    assert "attack_set_license" not in ledger
    # THE INHERITED KEYS ARE THE TRANSMITTER ARTEFACT'S OWN LEDGER, read off it
    # and not re-derived.
    artifact_ledger = list(
        bb84_specification(
            F(1, 2), F(1, 2), F(1, 2), F(1, 2)
        ).source.artifact.assumption_ledger
    )
    assert artifact_ledger
    assert ledger[-len(artifact_ledger) :] == artifact_ledger
    # No key twice: a ledger with a repeated key would be a manifest that
    # double-counts an assumption.
    assert len(ledger) == len(set(ledger))


def test_a_refusal_carries_an_empty_ledger_and_still_names_its_version() -> None:
    """There is no declaration to rest on anything, and the module is named.

    The same reading the seventeen declaration slots take on a refusal: the
    ledger is what the EMITTED declaration rests on, so a refusal carries
    none. The version is the module's and identifies what refused.
    """
    from certiqs_key.protocol_compiler import MATHEMATICAL_SPEC_VERSION

    record = compile_specification(
        conjugation_example_specification(ConjugationConvention.OMITTED)
    ).as_machine_record()
    assert record["refusal"] is not None
    assert record["assumption_ledger"] == []
    assert record["assumption_bindings"] == {}
    assert record["mathematical_spec_version"] == MATHEMATICAL_SPEC_VERSION


# ---------------------------------------------------------------------------
#  Two presence rules where a wrong ledger understates
#
#  A wrong answer is in the UNDERSTATING direction -- a ledger that names fewer
#  assumptions than the declaration rests on -- which is what PRINCIPLES.md
#  section 2.1 is about.
# ---------------------------------------------------------------------------

#: A two-sector emitted structure: two one-dimensional
#: proof sectors, so that `def:banda` (a)'s singleton clause is FALSE while
#: (b)'s chain clause stays true.
TWO_SECTORS = SectorStructure(
    labels=("s0", "s1"), dims=(1, 1), block_kind=BlockKind.PROOF_SECTOR
)
#: The same chain read against a singleton, which isolates the
#: sector conjunct of Band A: one chain, two sector sets, two answers.
ONE_SECTOR = SectorStructure(
    labels=("s0",), dims=(2,), block_kind=BlockKind.PROOF_SECTOR
)
_Z0 = matrix(((1, 0), (0, 0)))
_Z1 = matrix(((0, 0), (0, 1)))
_ONE = matrix(((1,),))
_NIL = matrix(((0,),))
_TWO_SECTOR_V = ("v0", "v1")


def _two_sector_identity_specification() -> ProtocolSpecification:
    """Return a compilable specification that is ``def:banda`` (b) and not (a).

    The chain is Band A's -- empty source segment, one exact identity link,
    no transported constraint, empty licence slot -- and the EMITTED SECTOR SET
    is ``{s_0, s_1}``, so ``def:banda``'s conjunction fails on (a). Every
    operator is diagonal in that grading, which is what lets the specification
    compile rather than refuse at the block-diagonality checks: the point of
    the fixture is the LEDGER of a successful emission.
    """
    descriptor = SystemDescriptor(
        "Q", 2, Side.RECEIVER, (("s0", 1), ("s1", 1)), BlockKind.PROOF_SECTOR
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
                target_alphabet=_TWO_SECTOR_V,
                target_povm={
                    "v0": BlockOperator.of(TWO_SECTORS, (_ONE, _NIL)),
                    "v1": BlockOperator.of(TWO_SECTORS, (_NIL, _ONE)),
                },
            ),
        ),
        outcome_correspondence=dict(zip(_TWO_SECTOR_V, _TWO_SECTOR_V, strict=True)),
    )
    x_alphabet = ("x0", "x1")
    announcements = tuple(f"b_{label}" for label in _TWO_SECTOR_V)
    classes = [(c_a, c_b) for c_a in ("a0", "a1") for c_b in announcements]
    public = PublicPart(
        partition=default_party_partition(x_alphabet, _TWO_SECTOR_V),
        announce_alice={"x0": "a0", "x1": "a1"},
        announce_bob=dict(zip(_TWO_SECTOR_V, announcements, strict=True)),
        alice_announcement_alphabet=("a0", "a1"),
        bob_announcement_alphabet=announcements,
        sifting=dict.fromkeys(classes, Sifting.PASS),
        key_rule={
            (readout, kappa): index
            for index, readout in enumerate(x_alphabet)
            for kappa in classes
        },
        holder=Party.ALICE,
        key_alphabet=(0, 1),
        acceptance_alphabet=("g",),
        accept_statistic=dict.fromkeys(classes, "g"),
    )
    return ProtocolSpecification(
        source=source_part(
            alphabet=x_alphabet,
            alice_dim=2,
            alice_povm=DirectPovm(alphabet=x_alphabet, elements={"x0": _Z0, "x1": _Z1}),
            transmitted_dim=2,
            signal_weights={"x0": F(1, 2), "x1": F(1, 2)},
            signal_states={"x0": _Z0, "x1": _Z1},
        ),
        receiver=ReceiverPart(
            physical_dim=2,
            physical_povm=DirectPovm(
                alphabet=_TWO_SECTOR_V, elements={"v0": _Z0, "v1": _Z1}
            ),
        ),
        public=public,
        sectors=TWO_SECTORS,
        chain=chain,
        constraints=SpecConstraints(),
    )


def test_a_bob_side_public_choice_alone_puts_a_coin_in_the_ledger() -> None:
    """A-COIN is EITHER FORM, and there is one such record PER PARTY.

    The presence rule is "whenever a public choice of either form is
    declared", and ``inputs.public_choices`` types "ONE SUCH RECORD PER PARTY,
    either possibly absent". ``def:spec`` (b) admits the receiver's own family
    "POSSIBLY PRESENTED AS A CHOICE-WEIGHTED FAMILY", which is the
    setting-INDEPENDENT form of ``def:weighted`` declared on Bob's side and the
    shape of the one instance in this tree. A presence
    test that read Alice's record and the route-C weighting only would let a
    specification whose ONLY public choice is Bob's emit a declaration built
    from weighted elements and a manifest that does not name the assumption
    making those weights a CHOICE.
    """
    base = bb84_specification(F(1, 2), F(1, 2), F(1, 2), F(1, 2))
    assert isinstance(base.receiver.physical_povm, PublicChoices)
    assert isinstance(base.source.alice_povm, PublicChoices)

    only_bob = replace(base, source=replace(base.source, alice_choices=None))
    assert not isinstance(only_bob.source.alice_povm, PublicChoices)
    assert only_bob.receiver.choice_weighting is None

    record = compile_specification(only_bob).as_machine_record()
    assert record["refusal"] is None
    assert "public_choice_weights" in record["assumption_ledger"]


def test_a_multi_sector_identity_chain_is_not_band_a() -> None:
    """``def:banda`` is (a) AND (b), and (a) fixes ``S = {s_0}``.

    A-IDEAL is BAND A ONLY and the A-LINK row is emitted "everywhere but Band
    A" (the interface's emission rule; on Band A thm:band-a (v) proves every
    clause of the identity link), so outside Band A, with no chain provenance
    passed, A-LINK must be named. If
    :func:`is_band_a` decided (b) alone, this specification would be called
    Band A, A-IDEAL would be named on a chain that does not deserve it -- the
    conservative direction -- and A-LINK, a ``never_verified`` obligation a
    consumer matches keys against, would be OMITTED, which is not. No route
    carries A-RECV (assumption_ledger.a_recv_not_emitted_note).

    THE SAME CHAIN AGAINST A SINGLETON IS BAND A, which is what isolates the
    conjunct rather than the fixture.
    """
    specification = _two_sector_identity_specification()
    chain = specification.chain
    assert isinstance(chain, ReductionChain)
    assert not is_band_a(chain, specification.sectors)
    assert is_band_a(chain, ONE_SECTOR)

    record = compile_specification(specification).as_machine_record()
    assert record["refusal"] is None
    ledger = record["assumption_ledger"]
    assert "ideal_qubit_receiver" not in ledger
    assert "reduction_chain_sound" in ledger
    assert "receiver_artifact_accepted" not in ledger
    # AND THE BAND-A SIDE STILL HOLDS, on the instance the suite compiles
    # everywhere else: the two rows are complementary and neither is emitted
    # twice.
    band_a = bb84_specification(F(1, 2), F(1, 2), F(1, 2), F(1, 2))
    band_a_ledger = compile_specification(band_a).as_machine_record()[
        "assumption_ledger"
    ]
    assert "ideal_qubit_receiver" in band_a_ledger
    assert "reduction_chain_sound" not in band_a_ledger
    assert "receiver_artifact_accepted" not in band_a_ledger


def test_the_split_parts_of_a_spec_follow_their_own_emission_rules() -> None:
    """``ass:alice-meas``, the assumption part of A-SPEC's split.

    The interface's ``assumption_ledger.emission_rule``: A-ALICE-MEAS is
    emitted "wherever no source-replacement certificate is demanded
    (untrusted-source mode, or d_A = 1)", the complement of
    ``transmitter/req:licence-scope``, which demands one only in trusted-source
    mode at ``d_A >= 2``. It sits right after A-SPEC, which is emitted always,
    in the order of ``assumption_ledger.own_rows``. Three of the five
    specifications cover the cells of (Band A, mode) at ``d_A >= 2``: Band A
    trusted at ``d_A = 2`` (absent), Band A untrusted and not Band A untrusted
    (present).

    There is no A-PRESENT: its content is clause (iv) of
    ``def:well-formed-spec``, decided on every route
    (``req:physical-family-decision``), so the key ``presented_receiver_family``
    is on no ledger, Band A or not.

    TRUSTED AT ``d_A = 1``: no certificate is demanded there,
    so the row is emitted, and it is KEYED TO THE DEMAND, NOT TO WHETHER A
    CERTIFICATE IS PRESENT. Two specifications hold that: one whose marginal
    slot the transmitter filled with ``tau_A = [1]`` (no certificate), and one
    carrying a verifying certificate voluntarily.
    """
    spec_key = "specification_describes_apparatus"
    present_key = "presented_receiver_family"
    alice_key = "alice_measurement_as_declared"

    def ledger_of(specification: ProtocolSpecification) -> list[str]:
        record = compile_specification(specification).as_machine_record()
        assert record["refusal"] is None
        ledger = record["assumption_ledger"]
        assert isinstance(ledger, list)
        return ledger

    trusted_band_a = bb84_specification(F(1, 2), F(1, 2), F(1, 2), F(1, 2))
    assert trusted_band_a.source.source_mode is SourceMode.TRUSTED
    ledger = ledger_of(trusted_band_a)
    assert ledger[0] == spec_key
    assert present_key not in ledger
    assert alice_key not in ledger

    untrusted_band_a = ProtocolSpecification(
        **{
            **trusted_band_a.__dict__,
            "source": source_part(
                alphabet=trusted_band_a.source.alphabet,
                alice_dim=trusted_band_a.source.alice_dim,
                alice_povm=trusted_band_a.source.alice_povm,
                transmitted_dim=trusted_band_a.source.transmitted_dim,
                signal_weights=trusted_band_a.source.signal_weights,
                signal_states=trusted_band_a.source.signal_states,
            ),
        }
    )
    assert untrusted_band_a.source.source_mode is SourceMode.UNTRUSTED
    ledger = ledger_of(untrusted_band_a)
    assert ledger[:2] == [spec_key, alice_key]
    assert present_key not in ledger
    assert "receiver_artifact_accepted" not in ledger

    untrusted_not_band_a = _two_sector_identity_specification()
    assert untrusted_not_band_a.source.source_mode is SourceMode.UNTRUSTED
    ledger = ledger_of(untrusted_not_band_a)
    assert ledger[:2] == [spec_key, alice_key]
    assert present_key not in ledger
    # No route carries A-RECV in this ledger; the row is the reductions
    # artefact's own (reductions/req:recv-row-provenance).
    assert "receiver_artifact_accepted" not in ledger
    assert len(ledger) == len(set(ledger))

    voluntary = SourceReplacementCertificate(
        alice_marginal=_ONE,
        psi=_Z0,
        virtual_dim=2,
        virtual_weights={"x0": F(1)},
        virtual_states={"x0": _Z0},
    )
    for certificate, slot_filled in ((None, True), (voluntary, False)):
        trusted_dimension_one = _dimension_one_specification(
            SourceMode.TRUSTED, certificate
        )
        source = trusted_dimension_one.source
        assert source.source_mode is SourceMode.TRUSTED
        assert source.alice_dim == 1
        assert source.artifact.marginal_slot_filled is slot_filled
        # No licence at d_A = 1 either way: the demand is not engaged.
        assert source.licence is None
        ledger = ledger_of(trusted_dimension_one)
        # One letter here, so {M_x} is the identity and A-ALICE-MEAS is not
        # emitted; the demand alone does not decide it.
        assert len(source.alphabet) == 1
        assert ledger[0] == spec_key
        assert alice_key not in ledger
        assert present_key not in ledger
        assert len(ledger) == len(set(ledger))


def _dimension_one_specification(
    mode: SourceMode, certificate: SourceReplacementCertificate | None
) -> ProtocolSpecification:
    """Return a ``d_A = 1`` specification on the two-sector identity chain.

    One letter ``x0`` with ``M_x0 = [1]`` and ``rho_x0 = |0><0|``. The source
    part is EMITTED BY THE TRANSMITTER (:func:`emit_artifact`), so a trusted
    request without a certificate has its slot filled with ``tau_A = [1]``
    (``req:marginal-fill``), and a certificate is decided there and carries
    the marginal.
    """
    base = _two_sector_identity_specification()
    announcements = tuple(f"b_{label}" for label in _TWO_SECTOR_V)
    classes = [("a0", c_b) for c_b in announcements]
    public = PublicPart(
        partition=default_party_partition(("x0",), _TWO_SECTOR_V),
        announce_alice={"x0": "a0"},
        announce_bob=dict(zip(_TWO_SECTOR_V, announcements, strict=True)),
        alice_announcement_alphabet=("a0",),
        bob_announcement_alphabet=announcements,
        sifting=dict.fromkeys(classes, Sifting.PASS),
        key_rule={("x0", kappa): 0 for kappa in classes},
        holder=Party.ALICE,
        key_alphabet=(0,),
        acceptance_alphabet=("g",),
        accept_statistic=dict.fromkeys(classes, "g"),
    )
    emitted = emit_artifact(
        SourceSpecification(
            signal_alphabet=("x0",),
            transmitted_dim=2,
            signal_weights={"x0": F(1)},
            signal_states={"x0": _Z0},
            alice_dim=1,
            alice_povm={"x0": _ONE},
            source_mode_request=mode,
            certificate=certificate,
        )
    )
    assert emitted.refusal is None
    assert emitted.artifact is not None
    return replace(
        base,
        source=SourcePart(alice_choices=None, artifact=emitted.artifact),
        public=public,
    )


# ---------------------------------------------------------------------------
#  The three fail-closed promises, on the EMISSION paths
# ---------------------------------------------------------------------------


def _emitted() -> CandidateDeclaration:
    result = compile_specification(
        bb84_specification(F(1, 2), F(1, 2), F(1, 2), F(1, 2))
    )
    assert result.declaration is not None
    return result.declaration


def test_no_default_is_substituted_for_a_missing_marginal() -> None:
    """``rem:notfallback``, on the compilation path rather than in the abstract.

    There is no fallback: an artefact with no marginal IS an untrusted
    artefact, which is what the transmitter emits for a source with no trusted
    description. What is asserted: no tau_A is manufactured, at any
    dimension, by any module.
    """
    specification = bb84_specification(F(1, 2), F(1, 2), F(1, 2), F(1, 2))
    without = ProtocolSpecification(
        **{
            **specification.__dict__,
            "source": source_part(
                alphabet=specification.source.alphabet,
                alice_dim=specification.source.alice_dim,
                alice_povm=specification.source.alice_povm,
                transmitted_dim=specification.source.transmitted_dim,
                signal_weights=specification.source.signal_weights,
                signal_states=specification.source.signal_states,
            ),
        }
    )
    result = compile_specification(without)
    assert result.refuses is False
    assert result.declaration is not None
    # NO tau_A IS MANUFACTURED: the slot holds nomarg and the mode is untrusted.
    assert result.declaration.alice_marginal is None
    assert result.declaration.is_trusted_mode is False
    assert result.gates is not None
    assert str(result.gates.case) == "G-U-M0"
    assert not hasattr(result.gates.report, "fallback")


def test_no_entry_is_dropped_by_the_compilation_map() -> None:
    """Theorem thm:gates (ii): the compiler never drops a constraint entry."""
    specification = bb84_specification(F(1, 2), F(1, 2), F(1, 2), F(1, 2))
    from certiqs_key.foundations.blocks import BlockOperator

    entries = tuple(
        ConstraintEntry(
            operator=BlockOperator.of(
                specification.sectors, (matrix(((1, 0), (0, 0))),)
            ),
            relation=Relation.GE,
            # A `homogeneous` entry, which is the LICENSED form in
            # trusted-source mode: "the right-hand side it denotes is then
            # CONSTRUCTED as Theta_k := c_k tau_A" (Definition def:homog (a)).
            rhs=F(1, 8) * (index + 1),
        )
        for index in range(3)
    )
    with_entries = ProtocolSpecification(
        **{
            **specification.__dict__,
            "constraints": SpecConstraints(entries=entries),
        }
    )
    assert emitted_constraint_list(with_entries, with_entries.chain) == entries  # type: ignore[arg-type]
    result = compile_specification(with_entries)
    assert result.declaration is not None
    assert result.declaration.constraint_list == entries
    assert len(result.declaration.constraint_list) == 3
    # And the entries are the SAME objects: nothing was rebuilt or coerced.
    for emitted, declared in zip(
        result.declaration.constraint_list, entries, strict=True
    ):
        assert emitted is declared


def test_no_licence_is_synthesized_on_any_emission_path() -> None:
    specification = bb84_specification(F(1, 2), F(1, 2), F(1, 2), F(1, 2))
    result = compile_specification(specification)
    assert result.declaration is not None
    # The attack-set licence was not supplied, so it is absent -- not invented.
    assert result.declaration.attack_set_license is None
    # The source-replacement licence IS emitted (trusted at d_A >= 2), and it
    # carries the attestation it was given, which is none.
    licence = result.source_replacement_license
    assert licence is not None
    assert licence.attestation_supplied is False
    assert licence.asserted_by_this_module is False

    # Supplying one makes it travel, unchanged.
    supplied = AttackSetLicense(supplier="proof-reductions", statement="attested")
    with_licence = ProtocolSpecification(
        **{
            **specification.__dict__,
            "constraints": SpecConstraints(attack_set_license=supplied),
        }
    )
    carried = compile_specification(with_licence)
    assert carried.declaration is not None
    assert carried.declaration.attack_set_license is supplied


def test_the_retention_attestation_is_carried_and_never_asserted() -> None:
    specification = bb84_specification(F(1, 2), F(1, 2), F(1, 2), F(1, 2))
    # THE CERTIFICATE TRAVELS INSIDE THE LICENCE RECORD.
    licence = specification.source.artifact.source_replacement_license
    assert licence is not None
    certificate = licence.certificate
    assert certificate is not None
    attestation = RetentionAttestation(attested_by="a supplier", statement="retained")
    attested = ProtocolSpecification(
        **{
            **specification.__dict__,
            "source": source_part(
                alphabet=specification.source.alphabet,
                alice_dim=specification.source.alice_dim,
                alice_povm=specification.source.alice_povm,
                transmitted_dim=specification.source.transmitted_dim,
                signal_weights=specification.source.signal_weights,
                signal_states=specification.source.signal_states,
                source_mode=SourceMode.TRUSTED,
                certificate=SourceReplacementCertificate(
                    **{
                        **certificate.__dict__,
                        "retention_attestation": attestation,
                    }
                ),
            ),
        }
    )
    result = compile_specification(attested)
    licence = result.source_replacement_license
    assert licence is not None
    assert licence.retention_attestation is attestation
    assert licence.asserted_by_this_module is False
    assert licence.as_machine_record()["sr3_asserted_by_this_module"] is False


# ---------------------------------------------------------------------------
#  The witness is verified and recorded, and is not a twenty-second key
# ---------------------------------------------------------------------------


def test_the_verified_witness_is_a_diagnostic_and_not_an_output_key() -> None:
    from certiqs_key.protocol_compiler import OUTPUT_KEYS

    result = compile_specification(
        bb84_specification(F(1, 2), F(1, 2), F(1, 2), F(1, 2))
    )
    assert result.verified_witness is not None
    record = result.as_machine_record()
    assert "feasibility_witness" not in record
    assert "feasibility_witness" not in OUTPUT_KEYS
    assert len(OUTPUT_KEYS) == 23


# ---------------------------------------------------------------------------
#  Docking stays off the surface
# ---------------------------------------------------------------------------


def test_docking_is_not_on_the_package_surface() -> None:
    import certiqs_key.protocol_compiler as package

    assert "docking" not in package.__all__
    for name in ("dock_declaration", "to_complex128", "sector_blocks"):
        assert name not in package.__all__
        assert not hasattr(package, name)


def test_importing_the_package_does_not_import_the_consuming_engine() -> None:
    """The surface stays free of NumPy and of the consuming engine.

    Both flags are asserted: the NUMPY flag and the meat flag the test is
    NAMED FOR. The engine's package is ``certiqs_key.meat``.
    """
    import subprocess
    import sys

    code = (
        "import sys; import certiqs_key.protocol_compiler; "
        "print('certiqs_key.meat' in sys.modules, 'numpy' in sys.modules)"
    )
    completed = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True
    )
    assert completed.stdout.strip() == "False False"


# ---------------------------------------------------------------------------
#  Definition def:weighted's emission decision, and condition (S) end to end
#
#  No registry import here: these are properties of the implementation, and the
#  frozen values that agree with them are driven separately, in
#  tests/golden/test_protocol_compiler_group_pc_m.py.
# ---------------------------------------------------------------------------


def test_the_decimal_literal_weight_list_is_refused_by_req_weight_list() -> None:
    """``req:weight-list``: the fl(0.9), fl(0.1) weight list is refused first.

    ``fl(0.9) + fl(0.1)`` is exactly ``1 + 2**-55`` and rounds to exactly
    ``1``: the exact sum is not 1 and the second addition of the declared-order
    accumulation rounds. The requirement refuses such a list with
    ``choice_weights_not_normalized`` and emits no declaration, and it decides
    the list on the declared weights, before any decision on the family they
    build -- so check V3 is not reached (the frozen case is
    ``S-ALICE-DECIMAL-LITERALS``).

    A REFUSAL RECORD AND NOT AN EXCEPTION: Section 2.5 (``fail_closed``)
    requires "a machine-readable reason and NO declaration".
    """
    result = compile_specification(
        bb84_specification(
            F(8106479329266893, 2**53),  # fl(0.9)
            F(3602879701896397, 2**55),  # fl(0.1)
            F(1, 2),
            F(1, 2),
        )
    )
    assert result.declaration is None
    assert result.refusal is not None
    assert result.refusal.reason is RefusalReason.CHOICE_WEIGHTS_NOT_NORMALIZED
    # The refusal names the party, the exact sum and the first rounding
    # addition of the weight list.
    assert "'A'" in result.refusal.detail
    assert "36028797018963969/36028797018963968, not 1" in result.refusal.detail
    assert "addition 2" in result.refusal.detail
    # No validator ran: the refusal is the compilation map's.
    assert result.validation is None


def test_a_receiver_weight_list_not_normalized_is_refused_before_the_chain() -> (
    None
):
    """``req:weight-list`` on the receiver's presentation, decided before (C4).

    The receiver's physical family is constructed from Bob's weight list before
    the chain stage reads it, so a list that is not normalized stops the
    compilation there: the refusal is ``choice_weights_not_normalized``, it
    names Bob's party, and no chain report exists because the chain stage
    never ran.
    """
    result = compile_specification(
        bb84_specification(
            F(1, 2),
            F(1, 2),
            F(8106479329266893, 2**53),  # fl(0.9)
            F(3602879701896397, 2**55),  # fl(0.1)
        )
    )
    assert result.declaration is None
    assert result.refusal is not None
    assert result.refusal.reason is RefusalReason.CHOICE_WEIGHTS_NOT_NORMALIZED
    assert "'B'" in result.refusal.detail
    assert "addition 2" in result.refusal.detail
    assert result.chain is None


def test_condition_s_and_not_c_refuses_the_same_family_presented_directly() -> None:
    """Rem. ``rem:bb84checks``: "IT IS (S) THAT REFUSES THAT PRESENTATION AND NOT (C)".

    The same matrices, presented as the transmitter artefact's own
    ``alice_povm`` with no public-choice record: no weight list is declared, so
    ``req:weight-list`` decides nothing, and the COMPUTED completeness sum is
    ``1_A`` so (C) passes, while (S) fails at element 3 of the declared order
    ``(Z,0), (Z,1), (X,0), (X,1)`` (the frozen case
    ``S-ALICE-DECIMAL-LITERALS-DIRECT``).
    """
    specification = bb84_specification(
        F(8106479329266893, 2**53),  # fl(0.9)
        F(3602879701896397, 2**55),  # fl(0.1)
        F(1, 2),
        F(1, 2),
    )
    result = compile_specification(
        replace(specification, source=replace(specification.source, alice_choices=None))
    )
    assert result.declaration is None
    assert result.refusal is not None
    assert result.refusal.reason is RefusalReason.ALICE_POVM_SUMMATION_ROUNDS
    # The refusal carries WHERE (S) first failed, which Section 2.3 requires:
    # "(S) additionally with the index of the first inexact addition".
    assert "element 3" in result.refusal.detail
    # AND IT IS V3 THAT REFUSED, on the sum and not on the completeness
    # identity. V3 is FIRST in the checks' own order, which is the one the
    # refusal names. (V7 fails downstream of it, the default candidate being
    # built from data V3 has already refused.)
    assert result.validation is not None
    assert result.validation.failing_checks[0] == "V3"


def test_the_balanced_presentation_of_the_same_instance_compiles() -> None:
    """The other half of the frozen pair: every partial sum is a multiple of 1/4.

    Thm. ``thm:pc12`` (ii): (S) "holds at the balanced weights ... where EVERY
    PARTIAL SUM of Eq. eq:declorder IS A MULTIPLE OF 1/4 and every addition
    forming it is exact". Without this half the test above would pass on a
    module that refused everything.
    """
    result = compile_specification(
        bb84_specification(F(1, 2), F(1, 2), F(1, 2), F(1, 2))
    )
    assert result.refusal is None
    assert result.declaration is not None


def test_the_choice_weighted_path_takes_def_weighted_s_emission_decision() -> None:
    """Def. ``def:weighted``: the compiler decides BEFORE EMITTING ANYTHING.

    "The compiler decides, before emitting anything, that every entry of every
    ``N_{u,t}`` is a binary64 number ... If either decision fails, the compiler
    refuses -- with ``emitted_value_not_representable`` in the first case ... It
    does not round, and it does not snap its own emission."

    ``resolve_povm`` is "the ONLY path in this package from a public-choice
    record to emitted matrices", so the decision has to be taken ON it and not
    merely be available beside it. Before the Stage 2 fix band
    ``decide_emission`` had NO CALLER at all, so the row was unreachable through
    ``compile_specification`` (F-S2-pc-02).
    """
    a = F(2**52 + 1, 2**53)
    b = F(2**52 - 1, 2**53)
    conditional = {
        "u0": matrix(((a, 0), (0, b))),
        "u1": matrix(((b, 0), (0, a))),
    }
    choices = PublicChoices(
        party=Party.ALICE,
        choices=("t0", "t1"),
        weights={"t0": a, "t1": b},
        conditional_alphabets={"t0": ("u0", "u1"), "t1": ("u0", "u1")},
        conditional_elements={"t0": conditional, "t1": conditional},
    )
    # EVERY PRIOR DECISION PASSES, which is what isolates the finding. The
    # weight sum rounds nowhere -- q_1 + q_2 = 2**53 * 2**-53 = 1, exactly --
    # and both weights and every conditional entry are binary64. What leaves the
    # lattice is the PRODUCT, its numerator (2**52 + 1)**2 needing 105 bits
    # against binary64's 53.
    decision = decide_emission(weighted_family(choices))
    assert decision.weights_sum_rounds_nowhere is True
    assert decision.every_product_is_binary64 is False
    assert decision.refusal is not None
    assert decision.refusal.reason is RefusalReason.EMITTED_VALUE_NOT_REPRESENTABLE

    # AND THE RESOLUTION PATH TAKES IT. This is the assertion that failed before
    # the fix: `resolve_povm` returned the family and refused nothing.
    resolution = resolve_povm(choices)
    assert resolution.povm is None
    assert resolution.refusal is not None
    assert resolution.refusal.reason is RefusalReason.EMITTED_VALUE_NOT_REPRESENTABLE
    assert resolution.refusal == decision.refusal
    # A RESOLUTION IS A FAMILY OR A REFUSAL, never both and never neither
    # (Section 2.5, `fail_closed`), so a caller cannot read a family off a
    # refusing resolution by accident.
    with pytest.raises(HypothesisError):
        resolution.require()


def test_a_direct_povm_presentation_carries_no_emission_obligation() -> None:
    """Section 2.5 (``no_snapping``): what this module CONSTRUCTS, and only that.

    "AN EMITTED MATRIX ENTRY THAT THIS MODULE WAS HANDED IS THE ENTRY IT WAS
    HANDED ... THE ONE OBJECT THIS MODULE CONSTRUCTS rather than passes through
    is the choice-weighted family ``N_{u,t} = q_t N_{u|t}``." So the emission
    decision attaches to the weighted branch and to nothing else, and a
    ``DirectPovm`` resolves with no decision taken -- ``emission`` being
    ``None`` rather than a vacuous pass, so the two cases stay distinguishable.
    """
    handed = DirectPovm(
        alphabet=("0", "1"),
        elements={
            "0": matrix(((1, 0), (0, 0))),
            "1": matrix(((0, 0), (0, 1))),
        },
    )
    resolution = resolve_povm(handed)
    assert resolution.refusal is None
    assert resolution.emission is None
    assert resolution.require() is handed


def test_the_weight_sum_equality_is_decided_on_the_exact_total() -> None:
    """``req:weight-list``: both legs decided on the declared weights, one reason.

    "``sum_t q_t = 1`` exactly, with the sum accumulated in the declared order
    of ``T_pub`` ... and required to round nowhere. ... A weight list whose
    exact sum is not 1, or whose declared-order accumulation rounds at some
    addition, is refused with ``choice_weights_not_normalized``."

    The two legs separate in both directions, and each alone refuses:
    ``fl(0.9), fl(0.1)`` has exact sum ``1 + 2**-55`` and its second addition
    rounds; ``1/2, 1/4`` is exact at every addition and sums to ``3/4``;
    ``2**-54, 1/2, 1/2 - 2**-54`` sums to exactly 1 through a second addition
    that rounds. The family is tabulated in every case and carries the
    refusal, which :func:`decide_emission` returns before deciding any
    product.
    """
    conditional = {
        "u0": matrix(((1, 0), (0, 0))),
        "u1": matrix(((0, 0), (0, 1))),
    }

    def choices(weights: tuple[F, ...]) -> PublicChoices:
        labels = tuple(f"t{index}" for index in range(len(weights)))
        return PublicChoices(
            party=Party.ALICE,
            choices=labels,
            weights=dict(zip(labels, weights, strict=True)),
            conditional_alphabets=dict.fromkeys(labels, ("u0", "u1")),
            conditional_elements=dict.fromkeys(labels, conditional),
        )

    nine_tenths = F(8106479329266893, 2**53)
    one_tenth = F(3602879701896397, 2**55)
    assert nine_tenths + one_tenth == 1 + F(1, 2**55)  # NOT 1, exactly
    cases = (
        # (weights, exact sum is 1, first rounding addition)
        ((nine_tenths, one_tenth), False, 2),
        ((F(1, 2), F(1, 4)), False, None),
        ((F(1, 2**54), F(1, 2), F(1, 2) - F(1, 2**54)), True, 2),
    )
    for weights, sums_to_one, first_inexact in cases:
        presented = choices(weights)
        family = weighted_family(presented)
        # The family is BUILT, every product formed exactly ...
        assert len(family.alphabet) == 2 * len(weights)
        # ... and carries the refusal and both recorded legs.
        assert family.refusal is not None
        assert family.refusal.reason is RefusalReason.CHOICE_WEIGHTS_NOT_NORMALIZED
        assert family.weights_sum_rounds_nowhere is (first_inexact is None)
        recorded = {entry.predicate: entry for entry in family.predicates}
        assert recorded["sum_t q_t = 1"].outcome is sums_to_one
        assert recorded["(S)"].first_inexact_index == first_inexact
        if first_inexact is not None:
            assert f"addition {first_inexact}" in family.refusal.detail
        # decide_emission returns the refusal and decides no product.
        decision = decide_emission(family)
        assert decision.refusal == family.refusal
        assert decision.every_product_is_binary64 is None
        assert [entry.predicate for entry in decision.predicates] == [
            "sum_t q_t = 1",
            "(S)",
        ]
        # And the resolution path refuses with it: no family is emitted.
        resolution = resolve_povm(presented)
        assert resolution.povm is None
        assert resolution.refusal == family.refusal

    # A normalized list is admitted: exact sum 1, every addition exact.
    admitted = weighted_family(choices((F(1, 2), F(1, 4), F(1, 4))))
    assert admitted.refusal is None
    assert admitted.weights_sum_rounds_nowhere is True
    assert decide_emission(admitted).refusal is None


def test_the_not_representable_row_is_reachable_through_compile_specification() -> None:
    """The row, driven through ``compile_specification`` and not ``resolve_povm``.

    F-S2-2-protocol-compiler-02. The Stage 2 fix band routed
    ``resolve_povm``'s refusal into a :class:`CompilationResult` at TWO sites --
    the receiver's choice-weighted family, resolved before the chain stage so
    that check (C4) is never given off-lattice numbers to compare, and Alice's,
    resolved when the slots are filled -- and tested the DECISION but not those
    two branches. A branch that no test enters is a branch that can be deleted
    without the suite noticing, and Definition ``def:weighted``'s
    ``emitted_value_not_representable`` is exactly the row F-S2-pc-02 found
    unreachable from a compilation in the first place.

    BOTH BRANCHES ARE ENTERED, and they are told apart by ``chain``: a refusal
    taken BEFORE the chain stage carries no chain report, and one taken after it
    carries the report the stage produced. "Before emitting anything" is
    therefore literal here and not a manner of speaking.

    All declared weights and conditional entries are binary64 and both sums
    are exactly one. Their products require more than 53 significant bits.
    This retains both product-refusal branches after off-lattice weights
    themselves become malformed input.
    """
    base = bb84_specification(F(1, 2), F(1, 2), F(1, 2), F(1, 2))
    a, b = F(2**52 + 1, 2**53), F(2**52 - 1, 2**53)

    def product_off_lattice(choices: PublicChoices) -> PublicChoices:
        return replace(
            choices,
            weights=dict(zip(choices.choices, (a, b), strict=True)),
            conditional_elements={
                t: dict(
                    zip(
                        choices.conditional_alphabets[t],
                        (matrix(((a, 0), (0, b))), matrix(((b, 0), (0, a)))),
                        strict=True,
                    )
                )
                for t in choices.choices
            },
        )

    assert isinstance(base.source.alice_choices, PublicChoices)
    assert isinstance(base.receiver.physical_povm, PublicChoices)
    # (a) ALICE'S FAMILY off the lattice, Bob's on it. Bob resolves first and
    #     passes, the chain runs, and the refusal comes from the slot-filling
    #     branch -- so a chain report exists beside it.
    alice_side = compile_specification(
        replace(
            base,
            source=replace(
                base.source,
                alice_choices=product_off_lattice(base.source.alice_choices),
            ),
        )
    )
    assert alice_side.refuses is True
    assert alice_side.declaration is None
    assert alice_side.refusal is not None
    assert alice_side.refusal.reason is RefusalReason.EMITTED_VALUE_NOT_REPRESENTABLE
    assert alice_side.chain is not None
    # A REFUSAL CARRIES NO ELIGIBILITY FLAG: there is no declaration for the
    # gates of Definition def:eligible to be about.
    assert alice_side.key_length_eligible is None
    assert alice_side.gate_report is None
    # And the reason names the offending element and entry, which Section 2.3
    # requires of every refusal.
    assert "q_t N_{u|t}" in alice_side.refusal.detail
    assert "declares no k" in alice_side.refusal.detail

    # (b) THE RECEIVER'S FAMILY off the lattice, Alice's on it. This refusal is
    #     taken BEFORE the chain stage -- the family is constructed only so that
    #     (C4) has something to compare -- so there is no chain report at all.
    #     `chain is None` is the observable that separates the two branches.
    receiver_side = compile_specification(
        replace(
            base,
            receiver=replace(
                base.receiver,
                physical_povm=product_off_lattice(base.receiver.physical_povm),
            ),
        )
    )
    assert receiver_side.refuses is True
    assert receiver_side.declaration is None
    assert receiver_side.refusal is not None
    assert receiver_side.refusal.reason is RefusalReason.EMITTED_VALUE_NOT_REPRESENTABLE
    assert receiver_side.chain is None
    assert receiver_side.key_length_eligible is None

    # THE MACHINE RECORD IS COMPLETE AT BOTH: every one of the twenty-three
    # output keys is present, the seventeen declaration slots are None BECAUSE
    # THERE IS NO DECLARATION, and `refusal` carries the record.
    for result in (alice_side, receiver_side):
        record = result.as_machine_record()
        assert set(record) >= set(DECLARATION_SLOT_KEYS)
        assert all(record[key] is None for key in DECLARATION_SLOT_KEYS)
        assert record["refusal"] == {
            "reason": "emitted_value_not_representable",
            "detail": result.refusal.detail,
        }

    # AND THE SAME INSTANCE COMPILES WHEN EVERY PRODUCT IS ON THE LATTICE, so
    # the pair is not passing because this specification never compiles.
    ok = compile_specification(bb84_specification(F(1, 2), F(1, 2), F(1, 2), F(1, 2)))
    assert ok.refusal is None
    assert ok.declaration is not None


@pytest.mark.parametrize("weight", [F(1, 3), F(1, 2**1075)])
def test_first_form_off_lattice_weights_are_malformed_before_sum(weight: F) -> None:
    """A non-binary64 summand cannot masquerade as (S) failing at index one."""
    conditional = {"u": matrix(((1,),))}
    choices = PublicChoices(
        party=Party.ALICE,
        choices=("t0", "t1"),
        weights={"t0": weight, "t1": 1 - weight},
        conditional_alphabets={"t0": ("u",), "t1": ("u",)},
        conditional_elements={"t0": conditional, "t1": conditional},
    )
    with pytest.raises(MalformedInputError, match="not a binary64 number"):
        weighted_family(choices)
