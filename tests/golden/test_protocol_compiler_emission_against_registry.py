"""The EMITTED side against the frozen registry: every B1 deferral, closed.

The candidate-side pass replayed every frozen entry whose subject is a
predicate on data, and deferred the ones whose subject is an EMISSION --
Definition ``def:compile`` filling Eq. ``eq:declaration``, and the worked
instances whose matrices that map produces. This file closes each of them, and
the difference from the candidate-side file is the direction of the arrow:

    THERE the frozen matrices were INPUT DATA to a predicate.
    HERE they are EXPECTED VALUES of a derivation the code performs.

WHAT IS CLOSED, ENTRY BY ENTRY
==============================
``O-PC-TYPING``       the emitted declaration of the hand-built specification
                      MINI, slot by slot, against the derivation the registry
                      writes out; plus its nine label-to-index bijections and
                      its Eq. ``eq:rdef`` key map, now BUILT by the compilation
                      map rather than supplied to a checker.
``O-PC-BB84``         Eq. ``eq:bb84data`` derived from Definition
                      ``def:bb84spec`` at all three frozen weight pairs -- the
                      emitted ``tau_A``, ``{M_x}`` and ``{F_v}`` compared to
                      the frozen matrices -- with the cardinalities, the key
                      map, the statistics and ``BB84_GATE_VERDICTS``.
``SR3_RECORD``        the EMITTED column of all three rows, which the
                      candidate-side pass could not reach because whether the
                      licence is emitted is a gate decision.
``O-PC-CONJUGATION``  the emitted element of BOTH branches, derived by applying
                      the conjugation of Section 2.5 to the declared signal
                      set -- and the refusal the omitted branch earns.
"""

from __future__ import annotations

from fractions import Fraction as F

import pytest
from instances.bb84.specification import (
    ConjugationConvention,
    bb84_specification,
    conjugation_example_specification,
)
from protocol_blocks import as_blocks, source_part
from registry_instances_bb84 import (
    BB84_ALPHABETS,
    BB84_CASES,
    BB84_D_VERDICTS,
    BB84_GATE_VERDICTS,
    BB84_KEY_MAP,
    BB84_PHI,
    CONJUGATION_BRANCHES,
    BB84Case,
)
from registry_protocol_compiler import INDEX_MAP_CASES
from registry_transmitter import SR3_RECORD

from certiqs_key.domain.constraints import ConstraintEntry, Relation
from certiqs_key.foundations.blocks import BlockKind, BlockOperator, SectorStructure
from certiqs_key.foundations.errors import MalformedInputError
from certiqs_key.foundations.exact import Cx, Matrix, equal, identity, matrix, scale
from certiqs_key.protocol_compiler import (
    DirectPovm,
    GateId,
    GateVerdict,
    Party,
    ProtocolSpecification,
    PublicPart,
    ReceiverPart,
    Sifting,
    SpecConstraints,
    compile_specification,
    default_party_partition,
    joint_distribution,
    phi_distribution,
    resolve_povm,
)
from certiqs_key.protocol_compiler.chain import (
    ChainLink,
    LinkStage,
    LinkStatus,
    ReductionChain,
    Side,
    SystemDescriptor,
    identity_channel,
)
from certiqs_key.transmitter import (
    RetentionAttestation,
    SourceMode,
    SourceReplacementCertificate,
)

pytestmark = [pytest.mark.contract, pytest.mark.oracle]


def reg(frozen: object) -> Matrix:
    """Return a frozen registry matrix in the implementation's substrate."""
    assert isinstance(frozen, tuple)
    return tuple(
        tuple(Cx(entry[0], entry[1]) for entry in row)  # type: ignore[index]
        for row in frozen
    )


P_Z0 = matrix(((1, 0), (0, 0)))
P_Z1 = matrix(((0, 0), (0, 1)))

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

_QUBIT_MAP = SectorStructure(labels=("s0",), dims=(2,), block_kind=FIXTURE_BLOCK_KIND)
Q_DESCRIPTOR = SystemDescriptor("Q", 2, Side.RECEIVER, (("s0", 2),), FIXTURE_BLOCK_KIND)


def _band_a(
    alphabet: tuple[str, ...], povm: dict[str, Matrix], dim: int = 2
) -> ReductionChain:
    """Return a Band-A chain carrying its target descriptor and POVM."""
    descriptor = SystemDescriptor(
        "Q", dim, Side.RECEIVER, (("s0", dim),), FIXTURE_BLOCK_KIND
    )
    sector_map = SectorStructure(
        labels=("s0",), dims=(dim,), block_kind=FIXTURE_BLOCK_KIND
    )
    blocks = {
        label: BlockOperator.of(sector_map, (element,))
        for label, element in povm.items()
    }
    return ReductionChain(
        source_segment=(),
        receiver_segment=(
            ChainLink(
                link_id="Lambda_1",
                segment=LinkStage.RECEIVER,
                link_type="squashing (identity)",
                source_descriptor=descriptor,
                target_descriptor=descriptor,
                status=LinkStatus.EXACT,
                channel=identity_channel(dim),
                target_alphabet=alphabet,
                target_povm=blocks,
            ),
        ),
        outcome_correspondence={label: label for label in alphabet},
    )


# ---------------------------------------------------------------------------
#  O-PC-TYPING: the emitted declaration of MINI, slot by slot
# ---------------------------------------------------------------------------


def _mini_specification() -> ProtocolSpecification:
    """Return MINI, in the five parts of Definition ``def:spec``.

    The specification of the registry's Group PC-A header comment: untrusted
    source, two Z-basis outcomes a side, the default party partition, matched
    announcements, and one untrusted constraint entry.
    """
    alphabet = ("x0", "x1")
    v_alphabet = ("v0", "v1")
    classes = [(c_a, c_b) for c_a in ("alpha0", "alpha1") for c_b in ("beta0", "beta1")]
    matched = {("alpha0", "beta0"), ("alpha1", "beta1")}
    public = PublicPart(
        partition=default_party_partition(alphabet, v_alphabet),
        announce_alice={"x0": "alpha0", "x1": "alpha1"},
        announce_bob={"v0": "beta0", "v1": "beta1"},
        alice_announcement_alphabet=("alpha0", "alpha1"),
        bob_announcement_alphabet=("beta0", "beta1"),
        sifting={
            kappa: (Sifting.PASS if kappa in matched else Sifting.FAIL)
            for kappa in classes
        },
        key_rule={
            (readout, kappa): index
            for index, readout in enumerate(alphabet)
            for kappa in classes
        },
        holder=Party.ALICE,
        key_alphabet=(0, 1),
        acceptance_alphabet=("g", "d"),
        accept_statistic={
            kappa: ("g" if kappa in matched else "d") for kappa in classes
        },
    )
    receiver = DirectPovm(alphabet=v_alphabet, elements={"v0": P_Z0, "v1": P_Z1})
    return ProtocolSpecification(
        source=source_part(
            alphabet=alphabet,
            alice_dim=2,
            alice_povm=DirectPovm(alphabet=alphabet, elements={"x0": P_Z0, "x1": P_Z1}),
            transmitted_dim=2,
            signal_weights={"x0": F(1, 2), "x1": F(1, 2)},
            signal_states={"x0": P_Z0, "x1": P_Z1},
        ),
        receiver=ReceiverPart(physical_dim=2, physical_povm=receiver),
        public=public,
        sectors=_QUBIT_MAP,
        chain=_band_a(v_alphabet, dict(receiver.elements)),
        constraints=SpecConstraints(
            entries=(
                ConstraintEntry(
                    operator=as_blocks(_QUBIT_MAP, P_Z0),
                    relation=Relation.GE,
                    rhs=F(1, 4),
                ),
            )
        ),
    )


def test_the_mini_declaration_is_emitted_slot_by_slot() -> None:
    """O-PC-TYPING's derivation, now produced by Definition ``def:compile``."""
    result = compile_specification(_mini_specification())
    assert result.refuses is False
    declaration = result.declaration
    assert declaration is not None

    # A, d_A <- S_src.
    assert declaration.alice_dim == 2
    # tau_A <- nomarg. UNTRUSTED mode, and NO THIRD VALUE IS EMITTED.
    assert declaration.alice_marginal is None
    assert declaration.is_trusted_mode is False
    # Q, S, (d_s) <- the last link of R_rec.
    assert declaration.sectors.labels == ("s0",)
    assert declaration.sectors.dims == (2,)
    assert declaration.q_dim == 2
    # {M_x} <- S_src ; {F_v} <- the last link's target POVM.
    assert declaration.alice_alphabet == ("x0", "x1")
    assert equal(declaration.alice_povm["x0"], P_Z0)
    assert equal(declaration.alice_povm["x1"], P_Z1)
    assert declaration.bob_alphabet == ("v0", "v1")
    assert equal(declaration.bob_povm["v0"].dense(), P_Z0)
    assert equal(declaration.bob_povm["v1"].dense(), P_Z1)
    # P, a_A, a_B, phi, h <- VERBATIM from S_pub.
    assert declaration.announce_alice == {"x0": "alpha0", "x1": "alpha1"}
    assert declaration.announce_bob == {"v0": "beta0", "v1": "beta1"}
    assert declaration.key_holder is Party.ALICE
    assert declaration.acceptance_alphabet == ("g", "d")
    # CList <- S_con's entries, the two segments contributing none.
    assert len(declaration.constraint_list) == 1
    assert declaration.constraint_list[0].rhs == F(1, 4)
    # r <- BUILT by Eq. eq:rdef, cell by cell.
    assert declaration.key_map == {
        ("x0", "v0"): 0,
        ("x0", "v1"): "perp",
        ("x1", "v0"): "perp",
        ("x1", "v1"): 1,
    }
    # THE CARDINALITIES the derivation writes out.
    assert len(declaration.alice_alphabet) == 2
    assert len(declaration.bob_alphabet) == 2
    assert len(declaration.partition.alice_readout_alphabet) == 2
    assert len(declaration.partition.bob_readout_alphabet) == 2
    assert len(declaration.alice_announcement_alphabet) == 2
    assert len(declaration.bob_announcement_alphabet) == 2
    assert declaration.sectors.count == 1
    assert len(declaration.acceptance_alphabet) == 2
    assert len(declaration.raw_key_alphabet) == 3
    assert len(declaration.announcement_classes()) == 4
    # D(i), D(ii), D(iv), D(vi) via the soundness half of thm:validator-soundness (i).
    assert result.validation is not None
    assert result.validation.passed is True


def test_the_mini_index_map_is_emitted_over_the_nine_alphabets() -> None:
    """``idx`` <- the nine bijections, now built by the compilation map."""
    result = compile_specification(_mini_specification())
    assert result.declaration is not None
    index_map = result.declaration.label_index_map
    assert index_map is not None
    for case in INDEX_MAP_CASES:
        forward = {
            label: index_map.index_of(case.alphabet, label) for label in case.labels
        }
        assert tuple(forward.items()) == case.forward
        assert sorted(forward.values()) == list(range(len(case.labels)))


def test_mini_lands_in_the_frozen_untrusted_gate_case() -> None:
    result = compile_specification(_mini_specification())
    assert result.gates is not None
    # Untrusted, m >= 1, licence ABSENT: row 6 -- emission with KLE = false.
    assert str(result.gates.case) == "G-U-M1-NOLIC"
    assert result.key_length_eligible is False
    report = result.gate_report
    assert report is not None
    assert report.entry(GateId.G3A).verdict is GateVerdict.PASSED_VACUOUSLY
    assert report.entry(GateId.G3B).verdict is GateVerdict.FAILED


# ---------------------------------------------------------------------------
#  O-PC-BB84: Eq. eq:bb84data derived at all three weight pairs
# ---------------------------------------------------------------------------

BB84_X = dict(BB84_ALPHABETS)["X"]
BB84_V = dict(BB84_ALPHABETS)["V"]
BB84_CHAT = dict(BB84_ALPHABETS)["Chat"]
PHI_PLUS = matrix(
    (
        (F(1, 2), 0, 0, F(1, 2)),
        (0, 0, 0, 0),
        (0, 0, 0, 0),
        (F(1, 2), 0, 0, F(1, 2)),
    )
)


@pytest.mark.parametrize("case", BB84_CASES, ids=lambda c: c.case_id)
def test_the_bb84_declaration_is_derived_and_matches_the_frozen_matrices(
    case: BB84Case,
) -> None:
    """Eq. ``eq:bb84data``, produced by the CODE from Definition ``def:bb84spec``."""
    weights = (*case.alice_weights, *case.bob_weights)
    if not case.dyadic:
        # The raw constructor refuses this frozen row at compilation with
        # emitted_value_not_representable; the symmetric def:weighted input
        # guard refuses earlier, before constructing its weighted family.
        # No frozen matrix, statistic or number is affected. User-facing ordinary
        # inputs instead use default_config/preparation and record the snap
        # (tests/unit/test_runs_numeric_inputs.py); this is the raw core path.
        with pytest.raises(MalformedInputError, match="not a binary64 number"):
            bb84_specification(*weights)
        return
    specification = bb84_specification(*weights)
    result = compile_specification(specification)
    assert result.refuses is False
    declaration = result.declaration
    assert declaration is not None

    # THE ALPHABETS: Definition def:bb84spec's own spelling, choice first.
    assert declaration.alice_alphabet == BB84_X
    assert declaration.bob_alphabet == BB84_V
    assert declaration.acceptance_alphabet == BB84_CHAT
    assert len(declaration.announcement_classes()) == 9

    # tau_A = 1_A / 2, derived through (SR1) from the certificate.
    assert declaration.alice_marginal is not None
    assert equal(declaration.alice_marginal, reg(case.tau_a))
    assert equal(declaration.alice_marginal, scale(F(1, 2), identity(2)))

    # M_{(b,a)} = p^A_b |conj(a^b)><conj(a^b)| and F_{(b',y)} = p^B_{b'} |y><y|.
    for label, expected in zip(BB84_X, case.alice_povm, strict=True):
        assert equal(declaration.alice_povm[label], reg(expected)), label
    for label, expected in zip(BB84_V, case.bob_povm, strict=True):
        assert equal(declaration.bob_povm[label].dense(), reg(expected)), label

    # (SR1)/(SR2) on the DERIVED family.
    assert result.certificate is not None
    assert result.certificate.sr1_holds is True
    assert result.certificate.sr2_holds is True
    for label, expected in zip(BB84_X, case.sr2_values, strict=True):
        assert equal(result.certificate.sr2_computed[label], reg(expected)), label
    for label, expected in zip(BB84_X, case.sr2_expected, strict=True):
        assert equal(result.certificate.sr2_expected[label], reg(expected)), label

    # CList empty, and the key map of Eq. eq:rdef.
    assert declaration.constraint_list == ()
    for x, v, expected in BB84_KEY_MAP:
        assert declaration.key_map[(x, v)] == expected

    # phi of Eq. eq:bb84phi, total on the nine-element K.
    for c_a, c_b, value in BB84_PHI:
        assert declaration.accept_statistic[(c_a, c_b)] == value

    # Eq. eq:bb84stats and the four-entry Phi vector.
    joint = joint_distribution(declaration, PHI_PLUS)
    for x, row in zip(BB84_X, case.joint, strict=True):
        for v, expected_value in zip(BB84_V, row, strict=True):
            assert joint[(x, v)] == expected_value
    statistics = phi_distribution(declaration, PHI_PLUS)
    assert tuple(statistics.values[value] for value in BB84_CHAT) == case.phi_vector
    assert statistics.total == case.phi_total == 1


@pytest.mark.parametrize("case", BB84_CASES, ids=lambda c: c.case_id)
def test_the_bb84_gate_verdicts_are_the_frozen_ones(case: BB84Case) -> None:
    """``BB84_GATE_VERDICTS``, and Theorem thm:pc12 (iii)'s D-verdicts."""
    weights = (*case.alice_weights, *case.bob_weights)
    if not case.dyadic:
        # The raw specification input is refused before any gate exists;
        # see the hand-listed boundary change in the preceding test.
        with pytest.raises(MalformedInputError, match="not a binary64 number"):
            bb84_specification(*weights)
        return
    result = compile_specification(bb84_specification(*weights))
    report = result.gate_report
    assert report is not None
    for gate, engaged, verdict, _why in BB84_GATE_VERDICTS:
        entry = report.entry(GateId(gate))
        assert entry.engaged == engaged, gate
        if verdict is None:
            assert entry.verdict is None, gate
        else:
            assert entry.verdict is not None and str(entry.verdict) == verdict, gate
    assert result.key_length_eligible is True
    assert result.gates is not None
    assert str(result.gates.case) == "G-T-D2-CERT-M0"
    # D(i)-D(viii) all hold, via the soundness half of thm:validator-soundness (i).
    assert result.validation is not None
    assert result.validation.passed is True
    assert all(holds for _, holds, _ in BB84_D_VERDICTS)


# ---------------------------------------------------------------------------
#  SR3_RECORD: the EMITTED column, which needed a gate decision
# ---------------------------------------------------------------------------


def _dimension_one_specification() -> ProtocolSpecification:
    """Return a trusted ``d_A = 1`` specification (Remark ``rem:dA1``'s shape)."""
    alphabet = ("x0",)
    v_alphabet = ("v0", "v1")
    classes = [("a", "b")]
    public = PublicPart(
        partition=default_party_partition(alphabet, v_alphabet),
        announce_alice={"x0": "a"},
        announce_bob=dict.fromkeys(v_alphabet, "b"),
        alice_announcement_alphabet=("a",),
        bob_announcement_alphabet=("b",),
        sifting=dict.fromkeys(classes, Sifting.PASS),
        key_rule={("x0", ("a", "b")): 0},
        holder=Party.ALICE,
        key_alphabet=(0,),
        acceptance_alphabet=("c",),
        accept_statistic=dict.fromkeys(classes, "c"),
    )
    receiver = DirectPovm(alphabet=v_alphabet, elements={"v0": P_Z0, "v1": P_Z1})
    return ProtocolSpecification(
        source=source_part(
            alphabet=alphabet,
            alice_dim=1,
            alice_povm=DirectPovm(alphabet=alphabet, elements={"x0": matrix(((1,),))}),
            transmitted_dim=2,
            signal_weights={"x0": F(1)},
            signal_states={"x0": P_Z0},
        ),
        receiver=ReceiverPart(physical_dim=2, physical_povm=receiver),
        public=public,
        sectors=_QUBIT_MAP,
        chain=_band_a(v_alphabet, dict(receiver.elements)),
        constraints=SpecConstraints(),
    )


def test_the_sr3_record_emitted_column_at_all_three_rows() -> None:
    """Whether the licence is EMITTED is a gate decision; here it is made."""
    rows = {row[0]: row for row in SR3_RECORD}

    # Row 1: supplied, trusted mode at d_A >= 2 -- EMITTED.
    supplied = bb84_specification(F(1, 2), F(1, 2), F(1, 2), F(1, 2))
    # THE CERTIFICATE TRAVELS INSIDE THE LICENCE RECORD, which
    # is what lets gate (G2) RE-DECIDE the five conditions on the emitted
    # data rather than take the transmitter's word for them.
    licence = supplied.source.artifact.source_replacement_license
    assert licence is not None
    certificate = licence.certificate
    assert certificate is not None
    with_attestation = ProtocolSpecification(
        **{
            **supplied.__dict__,
            "source": source_part(
                alphabet=supplied.source.alphabet,
                alice_dim=supplied.source.alice_dim,
                alice_povm=supplied.source.alice_povm,
                transmitted_dim=supplied.source.transmitted_dim,
                signal_weights=supplied.source.signal_weights,
                signal_states=supplied.source.signal_states,
                source_mode=SourceMode.TRUSTED,
                certificate=SourceReplacementCertificate(
                    **{
                        **certificate.__dict__,
                        "retention_attestation": RetentionAttestation(
                            attested_by="the supplier",
                            statement="A is retained",
                        ),
                    }
                ),
            ),
        }
    )
    result = compile_specification(with_attestation)
    description, is_supplied, emitted, asserted, _note = rows[
        "supplied, trusted mode at d_A >= 2"
    ]
    assert is_supplied is True
    assert emitted is True
    assert asserted is False
    licence = result.source_replacement_license
    assert licence is not None, description
    assert licence.attestation_supplied is True
    assert licence.asserted_by_this_module is False
    assert result.declaration is not None
    assert result.declaration.source_replacement_license is licence

    # Row 2: NOT supplied, trusted mode at d_A >= 2 -- NOT emitted.
    #
    # THERE IS NO FALLBACK to an untrusted emission (the frozen case id
    # `G-T-D2-NOCERT-M0-FALLBACK` and `fallback_recorded is True` are not
    # asserted): the transmitter refuses a
    # trusted-mode request at d_A >= 2 with no certificate BEFORE an artefact
    # exists, so rows 2 and 4 of the gate outcome table are unreachable through
    # the artefact and `GateInputs` refuses the combination as an input-typing
    # violation. The ROW'S CONTENT -- not supplied, not emitted, not asserted --
    # is what is asserted here, by way of
    # an UNTRUSTED artefact, which is what "no certificate at
    # d_A >= 2" means once the transmitter has had its say.
    _d, is_supplied, emitted, asserted, _n = rows[
        "not supplied, trusted mode at d_A >= 2"
    ]
    assert (is_supplied, emitted, asserted) == (False, False, False)
    without = ProtocolSpecification(
        **{
            **supplied.__dict__,
            "source": source_part(
                alphabet=supplied.source.alphabet,
                alice_dim=supplied.source.alice_dim,
                alice_povm=supplied.source.alice_povm,
                transmitted_dim=supplied.source.transmitted_dim,
                signal_weights=supplied.source.signal_weights,
                signal_states=supplied.source.signal_states,
            ),
        }
    )
    untrusted = compile_specification(without)
    assert untrusted.source_replacement_license is None
    assert untrusted.gates is not None
    assert str(untrusted.gates.case) == "G-U-M0"
    assert untrusted.declaration is not None
    assert untrusted.declaration.alice_marginal is None
    assert not hasattr(untrusted.gates.report, "fallback")




# ---------------------------------------------------------------------------
#  O-PC-CONJUGATION: the emitted element, derived
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("branch", CONJUGATION_BRANCHES, ids=lambda b: b.branch_id)
def test_the_conjugation_branches_emit_the_frozen_elements(branch: object) -> None:
    """Applying Section 2.5's conjugation to the declared Y-basis signal set."""
    assert hasattr(branch, "convention")
    convention = (
        ConjugationConvention.CONTRACT
        if branch.convention == "contract"  # type: ignore[attr-defined]
        else ConjugationConvention.OMITTED
    )
    specification = conjugation_example_specification(convention)
    resolution = resolve_povm(specification.source.alice_povm)
    # The emission decision passes on both branches: every entry of the Y-basis
    # projectors is +-1/2 or +-i/2 and every weight is 1/2, so every product is
    # a pure exponent shift. What separates the branches is (SR2), below.
    assert resolution.refusal is None
    emitted = resolution.require()
    assert equal(
        emitted.elements["(Y,0)"],
        reg(branch.emitted_element),  # type: ignore[attr-defined]
    )

    result = compile_specification(specification)
    if branch.sr2_holds:  # type: ignore[attr-defined]
        assert result.refuses is False
        assert result.declaration is not None
        assert equal(
            result.declaration.alice_povm["(Y,0)"],
            reg(branch.emitted_element),  # type: ignore[attr-defined]
        )
    else:
        # THE OMITTED BRANCH IS REFUSED, and this is the end-to-end proof that
        # the convention is load-bearing: gate (G2) fails at d_A = 2 on (SR2),
        # so the defect never reaches an emitted declaration.
        assert result.refuses is True
        assert result.refusal is not None
        # The frozen registry spells this refusal
        # `certificate_condition_sr2_failed`, a spelling invented under the rule
        # "<family>_<identifier>_failed".
        # The five certificate conditions are the TRANSMITTER's
        # and its interface spells them; the compiler's gate (G2)
        # RE-DECIDES the same five on the same data and REUSES those five
        # strings rather than spelling a second set (the compiler
        # interface's `fixed_by_this_file`: "a second vocabulary would be
        # two names for one refusal"). The CONDITION named is
        # (SR2), the signal identity -- and no registry value is edited: the
        # frozen enumeration fixes the naming obligation and the identity of
        # the named condition, never a spelling.
        assert str(result.refusal.reason) == "certificate_signal_identity_fails"
        assert result.declaration is None
    assert result.certificate is not None
    assert result.certificate.sr2_holds is branch.sr2_holds  # type: ignore[attr-defined]
    assert equal(
        result.certificate.sr2_computed["(Y,0)"],
        reg(branch.sr2_computed),  # type: ignore[attr-defined]
    )


def test_the_conjugation_example_is_a_well_formed_specification() -> None:
    """The Y basis is embedded in a COMPLETE family, and nothing else moves."""
    result = compile_specification(
        conjugation_example_specification(ConjugationConvention.CONTRACT)
    )
    assert result.refuses is False
    declaration = result.declaration
    assert declaration is not None
    assert result.validation is not None
    assert result.validation.passed is True
    # The Y rows are the frozen ones; the Z rows are the completion.
    assert declaration.alice_alphabet == ("(Z,0)", "(Z,1)", "(Y,0)", "(Y,1)")
    contract_branch = CONJUGATION_BRANCHES[0]
    assert equal(declaration.alice_povm["(Y,0)"], reg(contract_branch.emitted_element))
    # The matched-basis Y block of the joint table, at the noiseless state.
    joint = joint_distribution(declaration, PHI_PLUS)
    for a, row in enumerate(contract_branch.matched_basis_joint):
        for y, expected in enumerate(row):
            assert joint[(f"(Y,{a})", f"(Y,{y})")] == expected


def test_the_certificate_operator_is_the_one_the_instances_declare() -> None:
    """``Psi = |Phi+><Phi+|`` AS AN OPERATOR, in both, every entry binary64.

    Theorem ``thm:pc12`` (i) is why the type changed: the certificate "IS
    DECLARABLE ... the VECTOR |Phi+> having amplitudes 1/sqrt2 THAT NO BINARY64
    NUMBER SQUARES TO 1/2", while the OPERATOR "has every entry equal to 1/2,
    WHICH IS A BINARY64 NUMBER" (Definition ``def:srcert``).
    """
    from certiqs_key.foundations.exact import matrix_is_binary64

    expected = matrix(
        (
            (F(1, 2), 0, 0, F(1, 2)),
            (0, 0, 0, 0),
            (0, 0, 0, 0),
            (F(1, 2), 0, 0, F(1, 2)),
        )
    )
    for specification in (
        bb84_specification(F(1, 2), F(1, 2), F(1, 2), F(1, 2)),
        conjugation_example_specification(),
    ):
        # THE CERTIFICATE TRAVELS INSIDE THE LICENCE RECORD.
        licence = specification.source.artifact.source_replacement_license
        assert licence is not None
        certificate = licence.certificate
        assert certificate is not None
        assert equal(certificate.psi, expected)
        assert matrix_is_binary64(certificate.psi)
        # AND NO VECTOR IS DECLARED: "the unit vector |psi> with
        # Psi = |psi><psi| EXISTS BY Psi^2 = Psi and tr Psi = 1 and is NEVER
        # ITSELF DECLARED."
        assert not hasattr(certificate, "psi_amplitudes")
        assert not hasattr(certificate, "psi_squared_norm")
