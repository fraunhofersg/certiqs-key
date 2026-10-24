"""``transmitter``: the source part of a protocol, decided and emitted once.

The module spec/modules/transmitter/ owns, in its own words: the declared
source specification (``def:source-spec``), the source-replacement certificate
and what a verified one buys (``def:srcert``, ``thm:certificate-sufficiency``,
``cor:noncanonical``, ``rem:boundary``), the source segment of a reduction
chain (``def:source-segment``, ``def:source-link``), and the ``d_A = 1`` rule
(``rem:da1``).

THE SEAM. :mod:`certiqs_key.transmitter.artifact` is the
whole point of the module boundary: the compiler's ``transmitter_artifact`` input row
binds to :class:`~certiqs_key.transmitter.artifact.TransmitterArtifact`, and
the compiler reads the emitted source mode off that record's marginal slot --
it serves no source-mode request of its own, the request being an input of THIS
module, and takes no fallback.

WHAT THIS PACKAGE MAY NOT DO. It may not import
:mod:`certiqs_key.protocol_compiler`: imports point downward only
(PRINCIPLES.md section 4) and the compiler depends on this module. That is why
the five certificate refusals are spelled in
:mod:`certiqs_key.transmitter.reasons` and the compiler's gate (G2) REUSES
those five strings rather than the other way round. And it may never assert
(SR3) of an apparatus (``req:attestation-record``): the licence record is a
pass-through,
structurally.

THE SURFACE. Two declared forms of the certificate and the type around the
source segment:
:mod:`certiqs_key.transmitter.certificate` has the BLOCK FORM,
:mod:`certiqs_key.transmitter.presentation` is the ENSEMBLE PRESENTATION with
the objects ``lem:ensemble-presentation`` defines from it, and
:mod:`certiqs_key.transmitter.links` holds the source-link tuple, the obligation
triple and the closed soundness registry. The submodule
:mod:`certiqs_key.transmitter.decoy` declares the weak-coherent-pulse source.

NONE OF THE THREE CHANGES WHAT A PURE-FORM DECLARATION DECIDES OR EMITS. The
one-sector, pure-form, empty-segment declaration is the degenerate case of the
general module entry for entry, which is the design rule.
"""

from __future__ import annotations

from certiqs_key.transmitter.artifact import (
    MATHEMATICAL_SPEC_VERSION,
    SECTOR_BLOCK_KIND,
    SourceSpecification,
    TransmitterArtifact,
    TransmitterResult,
    emit_artifact,
)
from certiqs_key.transmitter.certificate import (
    BlockCertificateVerification,
    BlockFormCertificate,
    CertificateVerification,
    ConsistencyCriterion,
    PurityConditions,
    RetentionAttestation,
    SourceReplacementCertificate,
    SourceReplacementLicense,
    alice_outcome_distribution,
    certificate_projector,
    check_purity,
    check_sr1,
    check_sr2,
    consistency_criterion,
    verify_block_certificate,
    verify_certificate,
)
from certiqs_key.transmitter.links import (
    DECLARED_KINDS_WITHOUT_A_SOUNDNESS_CLAIM,
    SOUNDNESS_REGISTRY,
    AliceSideDescriptor,
    ObligationRecord,
    SoundnessRegistryEntry,
    SourceLink,
    SourceLinkKind,
    SourceLinkStatus,
    WitnessKind,
    check_source_link,
)
from certiqs_key.transmitter.presentation import (
    EnsemblePresentation,
    EnsemblePresentationVerification,
    alice_marginal_blocks,
    alice_operators,
    verify_ensemble_presentation,
)
from certiqs_key.transmitter.reasons import (
    ASSUMPTION_MACHINE_KEYS,
    CERTIFICATE_CONDITION_REASONS,
    NEVER_VERIFIED,
    REFUSAL_REASONS_CARRIED_VERBATIM,
    AssumptionId,
    CertificateForm,
    Refusal,
    RefusalReason,
    SourceMode,
)

__all__ = [
    "ASSUMPTION_MACHINE_KEYS",
    "CERTIFICATE_CONDITION_REASONS",
    "DECLARED_KINDS_WITHOUT_A_SOUNDNESS_CLAIM",
    "MATHEMATICAL_SPEC_VERSION",
    "NEVER_VERIFIED",
    "REFUSAL_REASONS_CARRIED_VERBATIM",
    "SECTOR_BLOCK_KIND",
    "SOUNDNESS_REGISTRY",
    "AliceSideDescriptor",
    "AssumptionId",
    "BlockCertificateVerification",
    "BlockFormCertificate",
    "CertificateForm",
    "CertificateVerification",
    "ConsistencyCriterion",
    "EnsemblePresentation",
    "EnsemblePresentationVerification",
    "ObligationRecord",
    "PurityConditions",
    "Refusal",
    "RefusalReason",
    "RetentionAttestation",
    "SoundnessRegistryEntry",
    "SourceLink",
    "SourceLinkKind",
    "SourceLinkStatus",
    "SourceMode",
    "SourceReplacementCertificate",
    "SourceReplacementLicense",
    "SourceSpecification",
    "TransmitterArtifact",
    "TransmitterResult",
    "WitnessKind",
    "alice_marginal_blocks",
    "alice_operators",
    "alice_outcome_distribution",
    "certificate_projector",
    "check_purity",
    "check_source_link",
    "check_sr1",
    "check_sr2",
    "consistency_criterion",
    "emit_artifact",
    "verify_block_certificate",
    "verify_certificate",
    "verify_ensemble_presentation",
]
