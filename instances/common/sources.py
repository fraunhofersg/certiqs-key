"""The BB84 qubit source part: four single-photon states from one certificate.

Optical BB84 and any instance compared with it send the same
four states from the same source-replacement certificate -- a second copy
would be a source that can drift from the one the comparison runs on -- and
a protocol document's trusted ensemble names the same construction. So it is
shared apparatus, here.

The conjugation convention is the qubit instance's
(:func:`instances.common.conjugation.conjugate_projector`, which
``instances/bb84/specification.py``, the compiler's worked declaration,
re-exports and whose convention it states once).
"""

from __future__ import annotations

from fractions import Fraction

from certiqs_key.foundations.blocks import Label
from certiqs_key.foundations.exact import Matrix, matrix, scale
from certiqs_key.protocol_compiler import Party, PublicChoices, SourcePart
from certiqs_key.protocol_compiler.weights import weighted_family
from certiqs_key.transmitter.artifact import TransmitterArtifact
from certiqs_key.transmitter.certificate import (
    SourceReplacementCertificate,
    SourceReplacementLicense,
    verify_certificate,
)
from instances.common.conjugation import conjugate_projector

__all__ = ["SIGNAL_ALPHABET", "bb84_qubit_source_part"]

#: Alice's four signal labels, in declared order.
SIGNAL_ALPHABET: tuple[Label, ...] = ("(Z,0)", "(Z,1)", "(X,0)", "(X,1)")

# The four BB84 signal states, exactly. Written here rather than imported from
# :mod:`instances.bb84.specification` because those are that module's private
# constants; the values are the same.
_P_Z0: Matrix = matrix(((1, 0), (0, 0)))
_P_Z1: Matrix = matrix(((0, 0), (0, 1)))
_P_X0: Matrix = scale(Fraction(1, 2), matrix(((1, 1), (1, 1))))
_P_X1: Matrix = scale(Fraction(1, 2), matrix(((1, -1), (-1, 1))))


def bb84_qubit_source_part(alice_z: Fraction, alice_x: Fraction) -> SourcePart:
    """Return the source-replacement source part. Identical to the qubit bb84's.

    Deliberately so: the exit condition compares the two slices in the limit, and
    a comparison whose two sides declare different sources compares two things.

    THE PART IS A READER OF A TRANSMITTER ARTEFACT.
    ``protocol-compiler``'s ``def:spec`` (a) is "a source specification in
    the sense of transmitter/def:source-spec, PRESENTED AS THE TRANSMITTER
    ARTEFACT in its declared mode", so the source's fields are
    projections of one record: the mode is read off the marginal slot and off
    nothing else. The declared numbers are ``tau_A = 1_A/2``, ``Psi``, the four
    signal states and weights and the conjugated conditional families, which is
    what the comparison against the qubit slice depends on.
    """
    signal_states = {
        "(Z,0)": _P_Z0,
        "(Z,1)": _P_Z1,
        "(X,0)": _P_X0,
        "(X,1)": _P_X1,
    }
    signal_weights = {
        "(Z,0)": alice_z / 2,
        "(Z,1)": alice_z / 2,
        "(X,0)": alice_x / 2,
        "(X,1)": alice_x / 2,
    }
    alice_choices = PublicChoices(
        party=Party.ALICE,
        choices=("Z", "X"),
        weights={"Z": alice_z, "X": alice_x},
        conditional_alphabets={"Z": ("0", "1"), "X": ("0", "1")},
        conditional_elements={
            "Z": {
                "0": conjugate_projector(_P_Z0),
                "1": conjugate_projector(_P_Z1),
            },
            "X": {
                "0": conjugate_projector(_P_X0),
                "1": conjugate_projector(_P_X1),
            },
        },
        joint_labels={
            (outcome, choice): f"({choice},{outcome})"
            for choice in ("Z", "X")
            for outcome in ("0", "1")
        },
    )
    certificate = SourceReplacementCertificate(
        alice_marginal=scale(Fraction(1, 2), matrix(((1, 0), (0, 1)))),
        # Psi = |Phi+><Phi+| ON A A'', DECLARED AS THE OPERATOR. The older
        # pair (psi_amplitudes, psi_squared_norm) is gone with the vector:
        # Definition ``def:srcert`` -- "No binary64 number a satisfies
        # a^2 = 1/2, so a declared vector with entries fl(1/sqrt2) yields
        # |Psi><Psi| with entries fl(1/sqrt2)^2 != 1/2 and (SR1) FAILS
        # EXACTLY". Every entry below is 0 or 1/2, and both are binary64. The
        # unit vector is never declared and is not needed: it exists by
        # Psi^2 = Psi and tr Psi = 1, two exact identities on this matrix.
        psi=scale(
            Fraction(1, 2),
            matrix(
                (
                    (1, 0, 0, 1),
                    (0, 0, 0, 0),
                    (0, 0, 0, 0),
                    (1, 0, 0, 1),
                )
            ),
        ),
        virtual_dim=2,
        virtual_weights=signal_weights,
        virtual_states=signal_states,
    )
    # THE CONSTRUCTION AND NOT THE DECISION, exactly as the qubit instance's
    # ``_trusted_artifact`` puts it: ``weighted_family`` applies
    # ``def:weighted``'s ``eq:weighted`` and takes no emission decision, which
    # is the compiler's on the compilation path where its refusal is DATA. The
    # choice record travels beside the artefact in ``alice_choices``.
    emitted = weighted_family(alice_choices)
    verification = verify_certificate(
        certificate, emitted.alphabet, dict(emitted.elements)
    )
    return SourcePart(
        artifact=TransmitterArtifact(
            signal_alphabet=SIGNAL_ALPHABET,
            alice_dim=2,
            alice_marginal=certificate.alice_marginal,
            alice_povm=dict(emitted.elements),
            virtual_transmitted_system=certificate.virtual_dim,
            virtual_ensemble_weights=dict(signal_weights),
            virtual_ensemble_states=dict(signal_states),
            source_segment=(),
            source_replacement_license=SourceReplacementLicense.pass_through(
                verification, certificate.retention_attestation, certificate
            ),
            marginal_slot_filled=False,
            assumption_ledger=(
                "source_ensemble",
                "sequential_round_model",
                "source_replacement_license",
            ),
        ),
        alice_choices=alice_choices,
    )
