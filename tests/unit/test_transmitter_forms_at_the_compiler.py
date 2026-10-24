"""What the protocol compiler does with the two block-presented certificate forms.

``transmitter/def:srcert`` gives the source-replacement certificate a pure
form, a block form and an ensemble presentation. ``protocol-compiler``'s gate
(G2) consumes each by its declared form (``def:eligible``, "(G2) by form of the
certificate"; ``rem:gate-by-certificate-form``):

* AN ENSEMBLE PRESENTATION IS CONSUMED. It declares no ``Psi`` and no
  ``{M_x}``, and (G2) decides what it declares: (E1), (E2) and (E3) on the
  declared weighted ensemble, and that the emitted declaration is in ensemble
  form with each ``N^(t)_x`` entry for entry the transpose of the declared
  block ``sigma^{v,(t)}_x``. A presentation meeting them compiles to a
  key-length-eligible declaration; one whose Alice slots are not those
  transposes is refused at row 3 of the gate outcome table
  (``def:gate-outcome-table``), naming the condition.
* A BLOCK-FORM CERTIFICATE IS REFUSED BY ITS FORM, whatever its blocks, at row
  3, with the refusal record ``gate_g2_failed`` naming the form
  (``thm:gates`` (ii'), Step 5), wherever its licence record is present. At
  ``d_A = 1`` the transmitter emits no record in any form
  (``transmitter/req:licence-scope``), Step 5's premise is not met, and the
  artefact compiles as a pure-form one does there.

Every artefact here is emitted by the transmitter (``emit_artifact``) from the
qubit BB84 ensemble and handed to the compiler in the BB84 specification of
``instances/bb84/specification.py``, in place of that specification's
pure-form artefact. The one artefact edited by hand is the negative
presentation case, because the transmitter forms ``{N_x}`` from the
presentation and so never emits slots that are not its transposes.
"""

from __future__ import annotations

from dataclasses import replace
from fractions import Fraction as F

import pytest

from certiqs_key.foundations.blocks import BlockKind, SectorStructure
from certiqs_key.foundations.exact import scale
from certiqs_key.protocol_compiler.compile import (
    CompilationResult,
    compile_specification,
)
from certiqs_key.protocol_compiler.gates import (
    CertificateState,
    GateCaseId,
    GateId,
    GateInputs,
    GateVerdict,
    resolve_gates,
)
from certiqs_key.protocol_compiler.reasons import RefusalReason
from certiqs_key.protocol_compiler.spec import ProtocolSpecification, SourcePart
from certiqs_key.protocol_compiler.transcript import PredicateSource
from certiqs_key.transmitter.artifact import (
    SourceSpecification,
    TransmitterArtifact,
    emit_artifact,
)
from certiqs_key.transmitter.certificate import BlockFormCertificate
from certiqs_key.transmitter.presentation import EnsemblePresentation
from certiqs_key.transmitter.reasons import CertificateForm, SourceMode

pytestmark = pytest.mark.contract

ONE_SECTOR = SectorStructure(
    labels=("A",), dims=(2,), block_kind=BlockKind.PROOF_SECTOR
)

#: The slot identity of def:eligible's ensemble clause, as the transcript names it.
SLOT_IDENTITY = "N^(t)_x = (sigma^{v,(t)}_x)^T"


def _bb84() -> ProtocolSpecification:
    from instances.bb84.specification import bb84_specification

    return bb84_specification(F(1, 2), F(1, 2), F(1, 2), F(1, 2))


def _with_artifact(
    spec: ProtocolSpecification, artifact: TransmitterArtifact
) -> ProtocolSpecification:
    """Return ``spec`` reading ``artifact``, with no Alice choice record.

    The choice record is a second presentation of ``{M_x}``; an artefact in
    another form either declares no ``{M_x}`` (a presentation) or its own
    blocks (a block form), so the source reads the artefact alone.
    """
    return replace(spec, source=SourcePart(artifact=artifact, alice_choices=None))


def _ensemble_specification() -> ProtocolSpecification:
    """Return BB84 with its source emitted from a one-sector ensemble presentation."""
    spec = _bb84()
    pure = spec.source.artifact
    presentation = EnsemblePresentation(
        virtual_sectors=ONE_SECTOR,
        weighted_blocks={
            label: (
                scale(
                    pure.virtual_ensemble_weights[label],
                    pure.virtual_ensemble_states[label],
                ),
            )
            for label in pure.signal_alphabet
        },
    )
    artifact = emit_artifact(
        SourceSpecification(
            signal_alphabet=pure.signal_alphabet,
            transmitted_dim=pure.virtual_transmitted_system,
            signal_weights=dict(pure.virtual_ensemble_weights),
            signal_states=dict(pure.virtual_ensemble_states),
            source_mode_request=SourceMode.TRUSTED,
            ensemble_presentation=presentation,
        )
    ).require()
    assert artifact.certificate_form is CertificateForm.ENSEMBLE_PRESENTATION
    assert artifact.alice_povm == {}
    return _with_artifact(spec, artifact)


def _g2_line(result: CompilationResult) -> GateVerdict | None:
    assert result.gate_report is not None
    return result.gate_report.entry(GateId.G2).verdict


def test_an_emitted_ensemble_presentation_compiles_and_is_eligible() -> None:
    """(G2)'s ensemble clause decides (E1)-(E3) and the slot identity, and both hold."""
    result = compile_specification(_ensemble_specification())
    assert result.refusal is None, result.refusal
    assert result.declaration is not None
    assert result.key_length_eligible is True
    assert _g2_line(result) is GateVerdict.PASSED
    assert result.gate_report is not None
    g2 = result.gate_report.transcript.for_source(PredicateSource.G2)
    conditions = [o for o in g2 if o.predicate == "(E1) to (E3)"]
    slots = [o for o in g2 if o.predicate == SLOT_IDENTITY]
    assert [o.outcome for o in conditions] == [True]
    assert len(slots) == len(result.declaration.alice_alphabet)
    assert all(o.outcome for o in slots)
    licence = result.source_replacement_license
    assert licence is not None
    assert licence.form is CertificateForm.ENSEMBLE_PRESENTATION


def test_a_presentation_whose_slots_are_not_its_transposes_is_refused() -> None:
    """The negative case: two letters' ``N_x`` swapped, so the transposes differ.

    The swap keeps every check of (G1) satisfied -- each ``N_x`` stays Hermitian
    and positive semidefinite and their sum is still ``tau_A`` -- so the refusal
    is (G2)'s slot identity and nothing earlier: row 3, ``gate_g2_failed``,
    with the failing letter in the detail and in the transcript.
    """
    spec = _ensemble_specification()
    artifact = spec.source.artifact
    operators = artifact.alice_ensemble_operators
    assert operators is not None
    swapped = {
        **operators,
        "(Z,0)": operators["(Z,1)"],
        "(Z,1)": operators["(Z,0)"],
    }
    result = compile_specification(
        _with_artifact(spec, replace(artifact, alice_ensemble_operators=swapped))
    )
    assert result.declaration is None
    assert result.refusal is not None
    assert result.refusal.reason is RefusalReason.GATE_G2_FAILED
    assert "(Z,0)" in result.refusal.detail
    assert _g2_line(result) is GateVerdict.FAILED
    assert result.gate_report is not None
    failed = [
        o
        for o in result.gate_report.transcript.for_source(PredicateSource.G2)
        if o.predicate == SLOT_IDENTITY and not o.outcome
    ]
    assert {o.element for o in failed} == {"x = (Z,0)", "x = (Z,1)"}


def test_a_block_form_certificate_is_refused_by_its_form() -> None:
    """Row 3 by the declared form: ``gate_g2_failed``, naming the block form.

    The block form here is the pure BB84 certificate written as one block, so
    its one non-zero block is a rank-one projector and it meets all five
    pure-form conditions: the refusal rests on the form alone, which is what
    ``def:eligible`` says ("whatever its blocks"). It is a refusal record, not
    an exception, and no declaration is emitted.
    """
    spec = _bb84()
    pure = spec.source.artifact
    licence = pure.source_replacement_license
    assert licence is not None and licence.certificate is not None
    certificate = licence.certificate
    block = BlockFormCertificate(
        alice_sectors=ONE_SECTOR,
        virtual_sectors=ONE_SECTOR,
        alice_marginal_blocks=(certificate.alice_marginal,),
        psi_blocks=(certificate.psi,),
        virtual_weights=dict(certificate.virtual_weights),
        virtual_blocks={
            label: (
                scale(
                    certificate.virtual_weights[label],
                    certificate.virtual_states[label],
                ),
            )
            for label in pure.signal_alphabet
        },
    )
    artifact = emit_artifact(
        SourceSpecification(
            signal_alphabet=pure.signal_alphabet,
            transmitted_dim=pure.virtual_transmitted_system,
            signal_weights=dict(pure.virtual_ensemble_weights),
            signal_states=dict(pure.virtual_ensemble_states),
            alice_dim=pure.alice_dim,
            alice_sectors=ONE_SECTOR,
            alice_povm_blocks={
                label: (pure.alice_povm[label],) for label in pure.signal_alphabet
            },
            source_mode_request=SourceMode.TRUSTED,
            block_certificate=block,
        )
    ).require()
    assert artifact.certificate_form is CertificateForm.BLOCK

    result = compile_specification(_with_artifact(spec, artifact))
    assert result.declaration is None
    assert result.key_length_eligible is None
    assert result.source_replacement_license is None
    assert result.refusal is not None
    assert result.refusal.reason is RefusalReason.GATE_G2_FAILED
    assert "BLOCK FORM" in result.refusal.detail
    assert _g2_line(result) is GateVerdict.FAILED
    assert result.gates is not None
    assert "row 3" in result.gates.derives_from


@pytest.mark.parametrize(
    ("alice_dim", "case", "g2"),
    [
        (2, GateCaseId.T_D2_CERTFAIL, GateVerdict.FAILED),
        (1, GateCaseId.T_D1_CERTFAIL, None),
    ],
)
def test_the_gate_refuses_a_block_form_at_row_3_at_every_dimension(
    alice_dim: int, case: GateCaseId, g2: GateVerdict | None
) -> None:
    """``resolve_gates`` on a block form: row 3, whose scope is every ``d_A``."""
    resolution = resolve_gates(
        GateInputs(
            validator_passed=True,
            emitted_mode=SourceMode.TRUSTED,
            alice_dim=alice_dim,
            certificate=CertificateState.PRESENT_FAILING,
            has_constraint_entries=False,
            list_licensed=True,
            license_present=False,
            certificate_form=CertificateForm.BLOCK,
        )
    )
    assert resolution.refuses
    assert resolution.case is case
    assert resolution.refusal is not None
    assert resolution.refusal.reason is RefusalReason.GATE_G2_FAILED
    # The refusal names the FORM (thm:gates Step 5), not the five conditions:
    # this line fails on the pre-O-2 gates.py, whose generic row-3 detail
    # reads "fails one of the FIVE decided conditions".
    assert "BLOCK FORM" in resolution.refusal.detail
    assert "FIVE decided conditions" not in resolution.refusal.detail
    assert resolution.report.entry(GateId.G2).verdict is g2
    assert resolution.emits_source_replacement_license is False


def test_a_block_form_at_dimension_one_carries_no_record_to_refuse() -> None:
    """d_A = 1: the transmitter emits no licence in any form (req:licence-scope).

    thm:gates Step 5 refuses a block form because "the record is present";
    at d_A = 1 it is not, so the declaration is emitted as the pure form's is,
    (G2) not engaged.
    """
    from tests.unit.test_protocol_emission import (
        _ONE,
        _Z0,
        _dimension_one_specification,
    )

    one = SectorStructure(labels=("A",), dims=(1,), block_kind=BlockKind.PROOF_SECTOR)
    two = SectorStructure(labels=("A",), dims=(2,), block_kind=BlockKind.PROOF_SECTOR)
    block = BlockFormCertificate(
        alice_sectors=one,
        virtual_sectors=two,
        alice_marginal_blocks=(_ONE,),
        psi_blocks=(_Z0,),
        virtual_weights={"x0": F(1)},
        virtual_blocks={"x0": (_Z0,)},
    )
    artifact = emit_artifact(
        SourceSpecification(
            signal_alphabet=("x0",),
            transmitted_dim=2,
            signal_weights={"x0": F(1)},
            signal_states={"x0": _Z0},
            alice_dim=1,
            alice_sectors=one,
            alice_povm_blocks={"x0": (_ONE,)},
            source_mode_request=SourceMode.TRUSTED,
            block_certificate=block,
        )
    ).require()
    assert artifact.certificate_form is CertificateForm.BLOCK
    assert artifact.source_replacement_license is None
    base = _dimension_one_specification(SourceMode.TRUSTED, None)
    result = compile_specification(_with_artifact(base, artifact))
    assert result.refusal is None, result.refusal
    assert result.key_length_eligible is True
    assert result.gates is not None
    assert result.gates.case is GateCaseId.T_D1_M0
    assert _g2_line(result) is None


@pytest.mark.parametrize(
    ("mode", "alice_dim"),
    [(SourceMode.TRUSTED, 1), (SourceMode.UNTRUSTED, 1), (SourceMode.UNTRUSTED, 2)],
)
@pytest.mark.parametrize(
    ("entries", "licence"), [(False, False), (True, False), (True, True)]
)
def test_the_gate_reads_a_block_form_without_a_record_as_the_pure_form(
    mode: SourceMode, alice_dim: int, entries: bool, licence: bool
) -> None:
    """``resolve_gates``: the form is decided only where a record is present.

    A block form whose state is ABSENT resolves to the case a pure form with
    no record resolves to, in either mode and with or without entries and
    licence, so the compile-side reading and the gate agree (thm:gates
    Step 5, "the record is present"; row 3 is scoped to trusted mode).
    """
    def inputs(form: CertificateForm) -> GateInputs:
        return GateInputs(
            validator_passed=True,
            emitted_mode=mode,
            alice_dim=alice_dim,
            certificate=CertificateState.ABSENT,
            has_constraint_entries=entries,
            list_licensed=True,
            license_present=licence,
            certificate_form=form,
        )

    block = resolve_gates(inputs(CertificateForm.BLOCK))
    pure = resolve_gates(inputs(CertificateForm.PURE))
    assert block.case is pure.case
    assert block.refusal is pure.refusal is None
    assert block.key_length_eligible is pure.key_length_eligible


def test_a_core_specification_is_not_an_admitting_submodule_artifact() -> None:
    """A3 refuses a core specification even when its link kind is admitted."""
    from decoy_support import tagged_declaration

    from certiqs_key.transmitter.reasons import RefusalReason as TransmitterReason

    result = emit_artifact(tagged_declaration().as_source_specification())
    assert result.artifact is None
    assert result.refusal is not None
    assert (
        result.refusal.reason
        is TransmitterReason.SOURCE_SEGMENT_NOT_FROM_ADMITTING_MODULE
    )
