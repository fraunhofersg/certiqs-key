"""The transmitter artefact: what it decides, what it refuses, what it records.

``artifact.py`` is what the compiler's ``transmitter_artifact`` input row
binds to, and this file is its test.

WHAT IS EXERCISED AND WHY EACH ONE MATTERS.

* THE MODE IS THE MARGINAL SLOT AND NOTHING ELSE (``rem:source-mode`` (a)).
  There is no second carrier of it on the record, so the two cannot disagree;
  that is asserted structurally rather than by example.
* THE ONE SLOT THIS MODULE FILLS IS RECORDED (``req:marginal-fill``). At
  ``d_A = 1`` a trusted request may leave the marginal empty and is SERVED with
  ``[1]``, the unique element of ``S_=(A)``; the artefact says that the value
  is the module's and not a declared datum, so nothing is filled silently.
* ``trusted_mode_without_certificate`` IS THE REFUSAL THAT MAKES THE
  COMPILER'S GATE ROWS 2 AND 4 UNREACHABLE. It is the load-bearing refusal of
  this module and is exercised at every dimension above one.
* A CERTIFICATE PRESENT AND FAILING IS REFUSED AT EVERY ``d_A``, naming the
  condition, and the five conditions have five names -- which is what lets the
  compiler's gate (G2) reuse them rather than spell a second set.
* THE VIRTUAL PAIR AT ``L_s = 0`` IS THE SPECIFIED PAIR, and a certificate
  internally consistent against a DIFFERENT pair is a hard error rather than a
  refusal. That guard is this module's, because this module is the one that holds both
  pairs.
* A RAW SOURCE SEGMENT IS REFUSED BY ADMISSION AND NEVER SILENTLY EMPTIED.
* (SR3) IS NEVER ASSERTED, structurally: the licence record refuses to be
  constructed with ``asserted_by_this_module`` true, and the only constructor
  is the pass-through.
"""

from __future__ import annotations

import json
from fractions import Fraction as F

import pytest

from certiqs_key.foundations.blocks import (
    IMPLICIT_ALICE_SECTOR_LABEL,
    BlockKind,
    SectorStructure,
)
from certiqs_key.foundations.errors import MalformedInputError
from certiqs_key.foundations.exact import deserialize_matrix, equal, matrix, scale
from certiqs_key.transmitter import (
    BlockFormCertificate,
    RetentionAttestation,
    SourceMode,
    SourceReplacementCertificate,
    SourceReplacementLicense,
    SourceSpecification,
    TransmitterArtifact,
    emit_artifact,
)

pytestmark = pytest.mark.contract

P_Z0 = matrix(((1, 0), (0, 0)))
P_Z1 = matrix(((0, 0), (0, 1)))
HALF = F(1, 2)

#: ``|Phi+><Phi+|`` on ``A A^v``, DECLARED AS THE OPERATOR: every entry is 0 or
#: 1/2 and both are binary64, which is why ``def:srcert`` types the input as an
#: operator and never as a vector.
PHI_PLUS = matrix(
    (
        (HALF, 0, 0, HALF),
        (0, 0, 0, 0),
        (0, 0, 0, 0),
        (HALF, 0, 0, HALF),
    )
)

ALPHABET = ("x0", "x1")
SIGNAL_WEIGHTS = {"x0": HALF, "x1": HALF}
SIGNAL_STATES = {"x0": P_Z0, "x1": P_Z1}
ALICE_POVM = {"x0": P_Z0, "x1": P_Z1}


def _certificate(**overrides: object) -> SourceReplacementCertificate:
    fields: dict[str, object] = {
        "alice_marginal": scale(HALF, matrix(((1, 0), (0, 1)))),
        "psi": PHI_PLUS,
        "virtual_dim": 2,
        "virtual_weights": dict(SIGNAL_WEIGHTS),
        "virtual_states": dict(SIGNAL_STATES),
    }
    fields.update(overrides)
    return SourceReplacementCertificate(**fields)  # type: ignore[arg-type]


def _spec(**overrides: object) -> SourceSpecification:
    fields: dict[str, object] = {
        "signal_alphabet": ALPHABET,
        "alice_dim": 2,
        "alice_povm": dict(ALICE_POVM),
        "transmitted_dim": 2,
        "signal_weights": dict(SIGNAL_WEIGHTS),
        "signal_states": dict(SIGNAL_STATES),
    }
    fields.update(overrides)
    return SourceSpecification(**fields)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
#  The emitted artefact, and the mode
# ---------------------------------------------------------------------------


def test_an_untrusted_specification_emits_nomarg_and_the_untrusted_mode() -> None:
    result = emit_artifact(_spec())
    assert result.refusal is None
    artifact = result.require()
    assert artifact.alice_marginal is None
    assert artifact.source_mode is SourceMode.UNTRUSTED
    assert artifact.marginal_slot_filled is False
    assert artifact.source_replacement_license is None
    assert artifact.source_segment == ()
    assert artifact.signal_alphabet == ALPHABET
    # EDITED BY HAND when the pin moves: an accepted version of
    # spec/modules/transmitter/module.yaml. "An artefact may
    # not claim a draft version" cuts both ways -- code may not pin a contract
    # whose conditions it does not implement.
    assert artifact.mathematical_spec_version == "transmitter@0.13.0"


def test_a_trusted_specification_with_a_verifying_certificate_emits_the_licence() -> (
    None
):
    result = emit_artifact(
        _spec(source_mode_request=SourceMode.TRUSTED, certificate=_certificate())
    )
    assert result.refusal is None
    artifact = result.require()
    assert artifact.source_mode is SourceMode.TRUSTED
    assert artifact.alice_marginal is not None
    licence = artifact.source_replacement_license
    assert licence is not None
    assert licence.sr1_holds is True
    assert licence.sr2_holds is True
    # THE CERTIFICATE TRAVELS WITH THE RECORD, so that a consumer can RE-DECIDE
    # the five conditions instead of taking this module's word for them.
    assert licence.certificate is not None
    assert equal(licence.certificate.psi, PHI_PLUS)
    assert "source_replacement_license" in artifact.assumption_ledger


def test_the_mode_has_no_second_carrier_on_the_record() -> None:
    """``rem:source-mode`` (a): the presence of the marginal IS the mode."""
    fields = set(TransmitterArtifact.__dataclass_fields__)
    assert "source_mode" not in fields
    assert "source_mode_request" not in fields
    # It is a derived property and nothing writes it.
    assert isinstance(TransmitterArtifact.source_mode, property)


def test_the_matrix_source_ledger_carries_a_seq_and_a_ens_without_a_nosrc() -> None:
    """The ``assumption_ledger`` row's emission rule, at both modes.

    A-ENS is in trusted-source mode only
    (``trusted_mode_matrix_declared_ensemble``).
    """
    untrusted = emit_artifact(_spec()).require()
    assert untrusted.assumption_ledger == ("sequential_round_model",)
    trusted = emit_artifact(
        _spec(source_mode_request=SourceMode.TRUSTED, certificate=_certificate())
    ).require()
    assert trusted.assumption_ledger[-1] == "source_replacement_license"
    assert trusted.assumption_ledger[0] == "source_ensemble"


# ---------------------------------------------------------------------------
#  req:marginal-fill: the one slot this module fills, and the fill is recorded
# ---------------------------------------------------------------------------


def test_a_trusted_request_at_dimension_one_is_served_and_the_fill_is_recorded() -> (
    None
):
    """``S_=(A) = {[1]}``, so the filled value is the only admissible one."""
    result = emit_artifact(
        _spec(
            alice_dim=1,
            alice_povm={"x0": matrix(((1,),)), "x1": matrix(((0,),))},
            source_mode_request=SourceMode.TRUSTED,
        )
    )
    assert result.refusal is None
    artifact = result.require()
    assert artifact.alice_marginal is not None
    assert equal(artifact.alice_marginal, matrix(((1,),)))
    # THE FILL IS RECORDED, which is what stops it being a silent default.
    assert artifact.marginal_slot_filled is True
    assert artifact.source_mode is SourceMode.TRUSTED
    # AND NO LICENCE IS EMITTED OR DEMANDED: at d_A = 1 it is VACUOUS.
    assert artifact.source_replacement_license is None
    assert "source_replacement_license" not in artifact.assumption_ledger


def test_a_block_form_certificate_at_dimension_one_emits_no_licence() -> None:
    """``req:licence-scope``: no licence at ``d_A = 1``, in the block form too.

    The block-form branch has the same ``d_A >= 2`` guard as the pure form and
    the ensemble presentation: without it a verifying one-sector block
    certificate at ``d_A = 1`` would emit the licence and the
    ``source_replacement_license`` ledger key.
    """
    label = IMPLICIT_ALICE_SECTOR_LABEL
    kind = BlockKind.PROOF_SECTOR
    alice = SectorStructure(labels=(label,), dims=(1,), block_kind=kind)
    virtual = SectorStructure(labels=(label,), dims=(2,), block_kind=kind)
    half_p0 = scale(HALF, P_Z0)
    block = BlockFormCertificate(
        alice_sectors=alice,
        virtual_sectors=virtual,
        alice_marginal_blocks=(matrix(((1,),)),),
        psi_blocks=(P_Z0,),
        virtual_weights=dict(SIGNAL_WEIGHTS),
        virtual_blocks={"x0": (half_p0,), "x1": (half_p0,)},
    )
    result = emit_artifact(
        _spec(
            alice_dim=1,
            alice_povm={"x0": matrix(((HALF,),)), "x1": matrix(((HALF,),))},
            signal_states={"x0": P_Z0, "x1": P_Z0},
            source_mode_request=SourceMode.TRUSTED,
            block_certificate=block,
        )
    )
    assert result.refusal is None
    artifact = result.require()
    assert artifact.source_mode is SourceMode.TRUSTED
    assert artifact.source_replacement_license is None
    assert "source_replacement_license" not in artifact.assumption_ledger


def test_no_marginal_is_manufactured_above_dimension_one() -> None:
    """``tau_A = 1_A / d_A`` is a stronger claim than nomarg, not a neutral one."""
    for dim in (2, 3, 4):
        povm = {
            "x0": matrix(
                tuple(tuple(F(1) if i == j == 0 else F(0) for j in range(dim)) for i in
                range(dim))
            ),
            "x1": matrix(
                tuple(
                    tuple(F(1) if i == j and i > 0 else F(0) for j in range(dim))
                    for i in range(dim)
                )
            ),
        }
        result = emit_artifact(
            _spec(
                alice_dim=dim, alice_povm=povm, source_mode_request=SourceMode.TRUSTED
            )
        )
        assert result.artifact is None, dim
        assert result.refusal is not None, dim
        assert str(result.refusal.reason) == "trusted_mode_without_certificate", dim
        assert "NEVER substituted" in result.refusal.detail


# ---------------------------------------------------------------------------
#  The refusals, each naming its own condition
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("overrides", "reason"),
    [
        ({"signal_alphabet": ()}, "signal_alphabet_empty_or_unordered"),
        ({"signal_alphabet": ("x0", "x0")}, "signal_alphabet_empty_or_unordered"),
        (
            {"alice_povm": {"x0": matrix(((1, 1), (0, 0))), "x1": P_Z1}},
            "alice_povm_element_not_admissible",
        ),
        (
            {"alice_povm": {"x0": P_Z0, "x1": P_Z0}},
            "alice_povm_not_complete",
        ),
        (
            {"signal_weights": {"x0": F(1, 4), "x1": F(1, 4)}},
            "ensemble_weights_not_normalized",
        ),
        (
            {"signal_weights": {"x0": F(-1, 2), "x1": F(3, 2)}},
            "ensemble_weights_not_normalized",
        ),
        (
            {"signal_states": {"x0": matrix(((1, 0), (0, 1))), "x1": P_Z1}},
            "ensemble_state_not_admissible",
        ),
        (
            {"source_segment": ("source-map",)},
            "link_kind_deferred",
        ),
        (
            {"source_segment": ("some-other-kind",)},
            "source_link_kind_not_admitted",
        ),
    ],
)
def test_each_refusal_names_its_own_condition(
    overrides: dict[str, object], reason: str
) -> None:
    """One machine string per condition, and a refusal emits NO artefact."""
    result = emit_artifact(_spec(**overrides))
    assert result.artifact is None
    assert result.refusal is not None
    assert str(result.refusal.reason) == reason


def test_a_completeness_sum_that_rounds_is_refused_by_the_summation_leg() -> None:
    """``alice_povm_summation_rounds``.

    ``fl(0.9) + fl(0.1)`` is exactly one on the computed total and is
    ``1 + 2^-55`` exactly, so the accumulation rounds. It is (S) that refuses
    such a presentation and not (C): the COMPUTED sum IS the identity.
    """
    nine, one = F(0.9), F(0.1)
    povm = {"x0": scale(nine, matrix(((1, 0), (0, 1)))), "x1": scale(one, matrix(((1,
    0), (0, 1))))}
    result = emit_artifact(_spec(alice_povm=povm))
    assert result.artifact is None
    assert result.refusal is not None
    assert str(result.refusal.reason) == "alice_povm_summation_rounds"


@pytest.mark.parametrize(
    ("overrides", "reason"),
    [
        (
            {"psi": matrix(((HALF, 0, 0, 0), (0, 0, 0, 0), (0, 0, 0, 0), (1, 0, 0,
            HALF)))},
            "certificate_not_hermitian",
        ),
        (
            {"psi": scale(F(1, 4), matrix(
                ((1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1))
            ))},
            "certificate_not_idempotent",
        ),
    ],
)
def test_each_certificate_condition_has_its_own_reason(
    overrides: dict[str, object], reason: str
) -> None:
    """``the_five_decided_conditions_are_five_reasons``, exercised.

    The compiler's gate (G2) re-decides the same five and REUSES these names
    rather than spelling a second set, which is why they have to be names of
    conditions and not of a gate.
    """
    result = emit_artifact(
        _spec(
            source_mode_request=SourceMode.TRUSTED,
            certificate=_certificate(**overrides),
        )
    )
    assert result.artifact is None
    assert result.refusal is not None
    assert str(result.refusal.reason) == reason
    # The verdicts are carried beside the refusal, so a caller sees WHY.
    assert result.certificate_verification is not None


def test_a_certificate_whose_sr1_fails_is_refused_by_the_marginal_identity() -> None:
    """(SR1): ``tr_{A^v} Psi = tau_A``, an exact matrix identity."""
    result = emit_artifact(
        _spec(
            source_mode_request=SourceMode.TRUSTED,
            certificate=_certificate(alice_marginal=P_Z0),
        )
    )
    assert result.refusal is not None
    assert str(result.refusal.reason) == "certificate_marginal_identity_fails"


def test_tau_a_is_decided_on_the_matrix_even_where_sr1_holds() -> None:
    """``req:marginal-decided``: never inferred from (SR1) => ``tau_A in S_=(A)``.

    A regression test. Here
    (SR1) holds -- ``tr_{A^v} Psi = tau_A`` exactly -- while ``tau_A`` has
    trace one and a negative eigenvalue, so it is no state. An implementation
    that inferred ``tau_A in S_=(A)`` from (SR1) would go on to the
    certificate and refuse with ``certificate_not_idempotent`` or another
    certificate reason instead of ``alice_marginal_not_admissible``.
    """
    tau = matrix(((F(3, 2), 0), (0, F(-1, 2))))
    psi = matrix(
        (
            (F(3, 2), 0, 0, 0),
            (0, 0, 0, 0),
            (0, 0, F(-1, 2), 0),
            (0, 0, 0, 0),
        )
    )
    result = emit_artifact(
        _spec(
            source_mode_request=SourceMode.TRUSTED,
            certificate=_certificate(alice_marginal=tau, psi=psi),
        )
    )
    assert result.artifact is None
    assert result.refusal is not None
    assert str(result.refusal.reason) == "alice_marginal_not_admissible"


def test_a_certificate_whose_sr2_fails_is_refused_by_the_signal_identity() -> None:
    """(SR2) is what ties Alice's DECLARED MEASUREMENT to the signal she sends.

    THE MUTATION IS ON THE MEASUREMENT AND NOT ON THE ENSEMBLE, and it has to
    be: swapping the certificate's virtual states would diverge from the
    specified pair and be caught by the typing stipulation one rule earlier.
    With the two labels of ``{M_x}`` exchanged the emitted artefact would
    describe a source that emits ``rho_x1`` whenever the specification says
    ``rho_x0``, and the marginal condition (SR1) cannot see it.
    """
    result = emit_artifact(
        _spec(
            alice_povm={"x0": P_Z1, "x1": P_Z0},
            source_mode_request=SourceMode.TRUSTED,
            certificate=_certificate(),
        )
    )
    assert result.artifact is None
    assert result.refusal is not None
    assert str(result.refusal.reason) == "certificate_signal_identity_fails"
    assert "'x0'" in result.refusal.detail


def test_a_certificate_present_at_dimension_one_and_failing_is_still_refused() -> None:
    """``req:failing-certificate``: refused at EVERY ``d_A``, ``d_A = 1`` included."""
    unit = matrix(((1,),))
    result = emit_artifact(
        _spec(
            alice_dim=1,
            alice_povm={"x0": unit, "x1": matrix(((0,),))},
            source_mode_request=SourceMode.TRUSTED,
            certificate=SourceReplacementCertificate(
                alice_marginal=unit,
                psi=matrix(((HALF, 0), (0, HALF))),
                virtual_dim=2,
                virtual_weights=dict(SIGNAL_WEIGHTS),
                virtual_states=dict(SIGNAL_STATES),
            ),
        )
    )
    assert result.artifact is None
    assert result.refusal is not None
    assert str(result.refusal.reason).startswith("certificate_")


def test_a_certificate_in_untrusted_mode_is_not_a_state_of_affairs_admitted() -> None:
    """The reason a consumer reads must name THE CONDITION THAT FAILED.

    A REFUSAL carrying ``trusted_mode_without_certificate`` would be false of
    the data: its interface condition is "trusted mode is requested at d_A >= 2
    and the certificate is absent", so the machine-readable reason would say a
    certificate was MISSING when one was SUPPLIED, which is worse than
    inventing a string. No row of this module's refusal table
    covers "an untrusted request carrying a certificate", and
    ``def:source-spec`` gives the certificate to the trusted mode alone, so no
    rule can be read against such a presentation at all: it is
    :class:`MalformedInputError`, symmetrically with the compiler's
    ``GateInputs.__post_init__``, which refuses the mirror combination with the
    same reasoning. NO ROW IS ADDED TO ANOTHER MODULE'S INTERFACE.
    """
    with pytest.raises(MalformedInputError, match="TRUSTED MODE ONLY"):
        emit_artifact(_spec(certificate=_certificate()))
    # AND THE FALSE REASON IS NOT EMITTED BY THIS PATH: the only
    # condition `trusted_mode_without_certificate` names is its own.
    absent = emit_artifact(
        _spec(source_mode_request=SourceMode.TRUSTED)
    )
    assert absent.refusal is not None
    assert str(absent.refusal.reason) == "trusted_mode_without_certificate"


# ---------------------------------------------------------------------------
#  def:srcert, "One reading at every L_s": the two pairs at L_s = 0
# ---------------------------------------------------------------------------


def test_a_virtual_pair_that_diverges_from_the_specified_one_is_malformed() -> None:
    """The guard on the two pairs belongs to their owner, this module.

    A certificate internally consistent against a DIFFERENT pair -- (SR1) and
    (SR2) holding of its own virtual states -- would otherwise emit a TRUSTED
    artefact describing a source other than the one the specification declares,
    and no enumerated condition would see it.
    """
    with pytest.raises(MalformedInputError, match="virtual ensemble IS the specified"):
        emit_artifact(
            _spec(
                source_mode_request=SourceMode.TRUSTED,
                certificate=_certificate(
                    virtual_states={"x0": P_Z1, "x1": P_Z0},
                ),
            )
        )


def test_a_virtual_system_of_a_different_dimension_is_malformed() -> None:
    """``A^v = A'`` at ``L_s = 0``, and a certificate on a bigger space is not that.

    The virtual ensemble below is admissible ON ITS OWN SPACE -- three
    dimensions, unit trace, positive -- so it passes the ensemble rules and
    only the typing stipulation can catch the divergence.
    """
    three = {
        "x0": matrix(((1, 0, 0), (0, 0, 0), (0, 0, 0))),
        "x1": matrix(((0, 0, 0), (0, 1, 0), (0, 0, 0))),
    }
    with pytest.raises(MalformedInputError, match="virtual transmitted system"):
        emit_artifact(
            _spec(
                source_mode_request=SourceMode.TRUSTED,
                certificate=_certificate(virtual_dim=3, virtual_states=three),
            )
        )


# ---------------------------------------------------------------------------
#  req:attestation-record: (SR3) is recorded and never asserted
# ---------------------------------------------------------------------------


def test_the_attestation_is_passed_through_and_never_synthesized() -> None:
    attestation = RetentionAttestation(attested_by="a supplier", statement="retained")
    artifact = emit_artifact(
        _spec(
            source_mode_request=SourceMode.TRUSTED,
            certificate=_certificate(retention_attestation=attestation),
        )
    ).require()
    licence = artifact.source_replacement_license
    assert licence is not None
    assert licence.retention_attestation is attestation
    assert licence.attestation_supplied is True
    assert licence.asserted_by_this_module is False
    record = licence.as_machine_record()
    assert record["sr3_asserted_by_this_module"] is False
    assert record["sr3_never_verified_assumption"] == "A-SRC"


def test_no_licence_can_be_constructed_that_asserts_sr3() -> None:
    """Structurally, and not by convention: the constructor refuses."""
    from certiqs_key.foundations.errors import HypothesisError

    with pytest.raises(HypothesisError, match="NEVER assert"):
        SourceReplacementLicense(
            sr1_holds=True,
            sr2_holds=True,
            retention_attestation=None,
            asserted_by_this_module=True,
        )


# ---------------------------------------------------------------------------
#  The record's shape
# ---------------------------------------------------------------------------


def test_a_result_carries_an_artefact_or_a_refusal_and_never_both() -> None:
    from certiqs_key.transmitter.artifact import TransmitterResult

    with pytest.raises(MalformedInputError, match="never both and never neither"):
        TransmitterResult(artifact=None, refusal=None)


def test_the_machine_record_carries_the_outputs_table_keys() -> None:
    artifact = emit_artifact(
        _spec(source_mode_request=SourceMode.TRUSTED, certificate=_certificate())
    ).require()
    record = artifact.as_machine_record()
    # The record carries `assumption_bindings` beside `assumption_ledger`, on
    # every artefact.
    assert set(record) == {
        "signal_alphabet",
        "alice_dim",
        "alice_marginal",
        "alice_marginal_slot_filled",
        "alice_povm",
        "virtual_transmitted_system",
        "virtual_ensemble",
        "source_segment",
        "source_replacement_license",
        "assumption_ledger",
        "assumption_bindings",
        "mathematical_spec_version",
    }
    assert record["source_segment"] == []


def test_the_licence_carries_its_certificate_on_the_wire() -> None:
    """The ``source_replacement_license`` row's ``certificate_travels_note``.

    The note says the
    emitted record carries the certificate itself -- ``tau_A``, ``Psi`` and the
    virtual pair -- "so that a consumer can re-decide the conditions on the
    emitted data rather than take this module's verdicts on trust", and
    PRINCIPLES.md section 9 makes the SERIALISABLE artefact the module
    boundary: a consumer reading the wire form must be able to do the thing the
    note says the record exists for.

    THE TEST READS IT THROUGH THE ARTEFACT'S OWN RECORD, not through the
    licence object, because that is the boundary: the artefact is what a
    consumer is handed. The licence record is JSON as emitted (the interface's
    ``wire_form``): it survives a strict ``json`` round trip, and its matrices
    read back exactly through ``deserialize_matrix``.
    """
    declared = _certificate()
    result = emit_artifact(
        _spec(source_mode_request=SourceMode.TRUSTED, certificate=declared)
    )
    assert result.refusal is None
    record = result.require().as_machine_record()
    licence = record["source_replacement_license"]
    assert isinstance(licence, dict)
    assert json.loads(json.dumps(licence)) == licence
    certificate = licence["certificate"]
    assert isinstance(certificate, dict)

    # THE FIVE FIELDS def:srcert DECLARES, each read back exactly from its
    # wire form: matrices by foundations.exact.deserialize_matrix, weights as
    # "p/q" strings.
    assert equal(
        deserialize_matrix(certificate["alice_marginal"]), declared.alice_marginal
    )
    assert equal(deserialize_matrix(certificate["psi"]), declared.psi)
    assert certificate["virtual_dim"] == declared.virtual_dim
    assert {
        label: F(weight) for label, weight in certificate["virtual_weights"].items()
    } == dict(declared.virtual_weights)
    assert set(certificate["virtual_states"]) == set(declared.virtual_states)
    for label, state in declared.virtual_states.items():
        assert equal(
            deserialize_matrix(certificate["virtual_states"][label]), state
        ), label

    # AND THE CONSUMER CAN RE-DECIDE ON WHAT IT READ: the two verdicts are
    # beside the certificate and are not the only thing on the wire.
    assert licence["sr1_holds"] is True
    assert licence["sr2_holds"] is True
    assert licence["sr3_asserted_by_this_module"] is False
