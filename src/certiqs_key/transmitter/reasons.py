"""The machine vocabulary of the transmitter: refusal reasons and assumptions.

WHY THIS FILE EXISTS RATHER THAN A SHARED ONE. Every module of this repository
owns its reasons module -- :mod:`certiqs_key.receiver.reasons`,
:mod:`certiqs_key.reductions.reasons` -- and the transmitter is the third. It
could not be otherwise: imports point downward only
(PRINCIPLES.md section 4), so the module the compiler depends on may not reach
into the compiler for a string. EVERY STRING BELOW is the ``refusal_reasons``
table of spec/modules/transmitter/interface.yaml, which is written from the
claims and which records which it carries verbatim from the compiler's
vocabulary.

THE FIVE CERTIFICATE CONDITIONS GET FIVE REASONS, and that is the interface's
own rule: "so that a refusal NAMES THE CONDITION that failed ... A certificate
present at d_A = 1 and failing one of them is refused under the same reason:
the refusal is at every d_A." The protocol compiler REUSES these five at its
gate (G2) rather than spelling a second set -- its interface's
``fixed_by_this_file`` says so in as many words, because "the five conditions
are the same five on the same data, so a second vocabulary would be two names
for one refusal".

A REFUSAL IS A RECORD AND NEVER AN EXCEPTION, as everywhere else in this
repository: :class:`Refusal` is data returned instead of an artefact, and the
two hard errors of :mod:`certiqs_key.foundations.errors` are for arguments no rule
can be read against at all.

(SR3) HAS NO REASON AND CANNOT FAIL HERE. ``thm:certificate-sufficiency`` (i) says
it "is decided by no function of the declared data" and ``req:attestation-record``
forbids asserting it of an apparatus; what a missing certificate produces is
``trusted_mode_without_certificate``, which is about PRESENCE and not truth.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import Final

from certiqs_key.domain.claim_closure import never_verified

__all__ = [
    "ASSUMPTION_MACHINE_KEYS",
    "CERTIFICATE_CONDITION_REASONS",
    "NEVER_VERIFIED",
    "REFUSAL_REASONS_CARRIED_VERBATIM",
    "AssumptionId",
    "CertificateForm",
    "Refusal",
    "RefusalReason",
    "SourceMode",
]


class CertificateForm(StrEnum):
    """The three forms a source-replacement certificate is supplied in.

    ``def:srcert``: the PURE form, whose five conditions are fixed; the BLOCK form,
    positive blocks against matched sector structures with no purity condition; and the
    ENSEMBLE PRESENTATION, in which only the matched sector structure and the weighted
    virtual ensemble are declared and the certificate is what
    ``lem:ensemble-presentation`` defines from them.

    THE FORM IS A MACHINE VALUE BECAUSE WHICH CONDITIONS WERE DECIDED DEPENDS
    ON IT. The ``source_replacement_license`` output row: the record "NAMES THE
    DECLARED FORM, ``pure``, ``block`` or ``ensemble_presentation``, because
    which conditions were decided depends on it". It is DERIVED from which
    certificate slot a specification fills and is never a second declared
    datum, exactly as the source mode is derived from the marginal slot.
    """

    PURE = "pure"
    BLOCK = "block"
    ENSEMBLE_PRESENTATION = "ensemble_presentation"


class SourceMode(StrEnum):
    """The two emitted source modes. ITS PRESENCE IS THE EMITTED MODE.

    ``rem:source-mode`` (a): the mode is DERIVED from whether the marginal slot
    is filled and is "NEVER EMITTED AS A SECOND KEY: a second carrier of the
    mode would be a second source of truth". This enum is therefore a READING
    of the artefact's marginal slot and never a field beside it.
    """

    TRUSTED = "trusted"
    UNTRUSTED = "untrusted"


class RefusalReason(StrEnum):
    """Every machine-readable reason this module can emit.

    The table of spec/modules/transmitter/interface.yaml, in its own order.
    Three of them are carried verbatim from the compiler's vocabulary
    (:data:`REFUSAL_REASONS_CARRIED_VERBATIM`).
    """

    #: X empty, unordered, or with a repeated label (def:source-spec).
    SIGNAL_ALPHABET_EMPTY_OR_UNORDERED = "signal_alphabet_empty_or_unordered"
    #: Some M_x is not Hermitian or not positive semidefinite.
    ALICE_POVM_ELEMENT_NOT_ADMISSIBLE = "alice_povm_element_not_admissible"
    #: sum_x M_x != 1_A as an identity of the declared numbers.
    ALICE_POVM_NOT_COMPLETE = "alice_povm_not_complete"
    #: The completeness sum, in the declared order of X, does not round
    #: nowhere. VERBATIM from protocol-compiler 0.3.0, check V3.
    ALICE_POVM_SUMMATION_ROUNDS = "alice_povm_summation_rounds"
    #: Some p_x < 0, or sum_x p_x != 1 in the declared order, or that sum
    #: rounds. The report names WHICH ensemble.
    ENSEMBLE_WEIGHTS_NOT_NORMALIZED = "ensemble_weights_not_normalized"
    #: Some rho_x is not in S_=(A'), or some rho^v_x is not in S_=(A^v).
    ENSEMBLE_STATE_NOT_ADMISSIBLE = "ensemble_state_not_admissible"
    #: Trusted mode and tau_A is not in S_=(A). A SINGULAR tau_A is admissible
    #: and must not be refused; tau_A = 0 fails here, its trace being 0.
    ALICE_MARGINAL_NOT_ADMISSIBLE = "alice_marginal_not_admissible"
    #: tr tau_A = 1 holds only as a computed sum. VERBATIM from
    #: protocol-compiler 0.3.0, check V2.
    ALICE_MARGINAL_TRACE_ROUNDS = "alice_marginal_trace_rounds"
    #: Trusted mode at d_A >= 2 with the certificate absent, or a field of it
    #: absent. The compiler serves no untrusted-mode fallback for this case
    #: (protocol-compiler/rem:notfallback); the transmitter refuses it.
    TRUSTED_MODE_WITHOUT_CERTIFICATE = "trusted_mode_without_certificate"
    #: Psi != Psi^dagger.
    CERTIFICATE_NOT_HERMITIAN = "certificate_not_hermitian"
    #: Psi^2 != Psi, the product formed in exact arithmetic.
    CERTIFICATE_NOT_IDEMPOTENT = "certificate_not_idempotent"
    #: tr Psi != 1, or the accumulated trace rounds.
    CERTIFICATE_TRACE_NOT_ONE = "certificate_trace_not_one"
    #: (SR1) tr_{A^v} Psi != tau_A, as an exact matrix identity.
    CERTIFICATE_MARGINAL_IDENTITY_FAILS = "certificate_marginal_identity_fails"
    #: (SR2) tr_A[(M_x (x) 1) Psi] != p_x rho^v_x for some x. The report names
    #: the first x at which it fails.
    CERTIFICATE_SIGNAL_IDENTITY_FAILS = "certificate_signal_identity_fails"
    #: The kind is outside the admitted vocabulary. Historical versions used
    #: source_segment_not_empty; new records use this condition-specific name.
    SOURCE_LINK_KIND_NOT_ADMITTED = "source_link_kind_not_admitted"
    #: A source link of the one declared kind with no soundness claim,
    #: `source-map`, is present. The kind is declared, reserved and refused
    #: (def:source-link (a)). A frozen spelling.
    LINK_KIND_DEFERRED = "link_kind_deferred"
    #: A source link carries a non-empty list of transported constraint
    #: entries, or a licence record without one. NO CLAIM OF THIS REPOSITORY
    #: TRANSPORTS AN ALICE-SIDE ENTRY (def:source-link (f)).
    SOURCE_LINK_ENTRY_PRESENT = "source_link_entry_present"
    #: A DATA link's declared descriptor family does not contain its own
    #: declared source descriptor. For a CONSTRUCTOR link the condition is not
    #: decidable and this reason does not fire (def:source-link (d)).
    SOURCE_LINK_FAMILY_EXCLUDES_ITS_DESCRIPTOR = (
        "source_link_family_excludes_its_descriptor"
    )
    #: A constructor link's obligation triple matches no entry of the
    #: artefact's emitted soundness registry (def:source-segment (A1), (A2)).
    SOURCE_LINK_NOT_IN_REGISTRY = "source_link_not_in_registry"
    #: A constructor link's registry entry names an assumption short id that is
    #: not in the emitted assumption ledger (def:source-segment (A2)).
    SOURCE_LINK_ASSUMPTION_NOT_IN_LEDGER = "source_link_assumption_not_in_ledger"
    #: A non-empty source segment is presented other than inside an artefact
    #: emitted by the module that admits its links (def:source-segment (A3)).
    SOURCE_SEGMENT_NOT_FROM_ADMITTING_MODULE = (
        "source_segment_not_from_admitting_module"
    )
    #: A certificate declared in BLOCK form fails one of its conditions. ONE
    #: REASON, AND THE REPORT NAMES THE SECTOR: the block form's conditions are
    #: decided per sector, so a reason without the sector says less than a
    #: reason with it (the interface's
    #: `the_block_form_has_one_reason_and_names_the_sector`). A block form
    #: carries no idempotence condition and none of the five pure-form reasons
    #: is reused for it.
    CERTIFICATE_BLOCK_NOT_ADMISSIBLE = "certificate_block_not_admissible"
    #: A certificate supplied as an ENSEMBLE PRESENTATION fails (E1), (E2) or
    #: (E3). NOTHING ELSE IS DECIDED OF A PRESENTATION.
    ENSEMBLE_PRESENTATION_NOT_ADMISSIBLE = "ensemble_presentation_not_admissible"
    #: A quantity a declaration FORMS from its declared numbers is not
    #: admissible as declared data. REFUSED AND NEVER ROUNDED.
    FORMED_ENTRY_NOT_DECLARABLE = "formed_entry_not_declarable"
    # NO MEMBER FOR A SOURCE LINK WHOSE DESCRIPTOR IS NOT ALICE-SIDE: the
    # discipline holds by the type of
    # :class:`~certiqs_key.transmitter.links.AliceSideDescriptor`, and (S1) and
    # (S2) of a presented segment are the consuming compiler's to refuse
    # (interface.yaml, `the_alice_side_descriptor_discipline_has_no_reason`).


#: The three strings with frozen spellings, named here so that a reader can
#: tell a frozen spelling from a new one (interface.yaml,
#: `refusal_reasons.frozen_spellings`).
REFUSAL_REASONS_CARRIED_VERBATIM: Final[tuple[RefusalReason, ...]] = (
    RefusalReason.ALICE_MARGINAL_TRACE_ROUNDS,
    RefusalReason.ALICE_POVM_SUMMATION_ROUNDS,
    RefusalReason.LINK_KIND_DEFERRED,
)

#: The five conditions a consumer decides on a certificate, each with its own
#: reason, IN THE ORDER def:srcert STATES THEM. The protocol compiler's gate
#: (G2) re-decides the same five on the emitted data and reports through these
#: same five names.
CERTIFICATE_CONDITION_REASONS: Final[MappingProxyType[str, RefusalReason]] = (
    MappingProxyType(
        {
            "Psi = Psi^dag": RefusalReason.CERTIFICATE_NOT_HERMITIAN,
            "Psi^2 = Psi": RefusalReason.CERTIFICATE_NOT_IDEMPOTENT,
            "tr Psi = 1": RefusalReason.CERTIFICATE_TRACE_NOT_ONE,
            "tr Psi rounds nowhere": RefusalReason.CERTIFICATE_TRACE_NOT_ONE,
            "(SR1)": RefusalReason.CERTIFICATE_MARGINAL_IDENTITY_FAILS,
            "(SR2)": RefusalReason.CERTIFICATE_SIGNAL_IDENTITY_FAILS,
        }
    )
)


@dataclass(frozen=True, slots=True)
class Refusal:
    """The record a refusal IS: the machine reason and the offending datum.

    ``reason`` is the load-bearing field; ``detail`` names the datum in prose
    for a human reading a refusal. A refusal is emitted INSTEAD OF an artefact,
    never beside one.
    """

    reason: RefusalReason
    detail: str

    def as_machine_record(self) -> dict[str, str]:
        """Return the refusal as a machine record."""
        return {"reason": str(self.reason), "detail": self.detail}


class AssumptionId(StrEnum):
    """The four assumptions of this module's ledger, by their short ids.

    A-SRC is the one assumption behind the machine key
    ``source_replacement_license``.
    """

    A_ENS = "A-ENS"
    A_SEQ = "A-SEQ"
    A_SRC = "A-SRC"


#: The ledger's machine keys, one per assumption (the interface's
#: `assumption_ledger` rows).
ASSUMPTION_MACHINE_KEYS: Final[MappingProxyType[AssumptionId, str]] = MappingProxyType(
    {
        AssumptionId.A_ENS: "source_ensemble",
        AssumptionId.A_SEQ: "sequential_round_model",
        AssumptionId.A_SRC: "source_replacement_license",
    }
)

#: THE ASSUMPTIONS NO CODE PATH OF THIS MODULE DECIDES, in the ledger's order:
#: every member whose ``verification`` header field is ``never``
#: (spec/claim-format.md section 3.2), read from the shipped claim-closure
#: table by machine key and not listed here by hand (``ass:src``, ``ass:ens`` and
#: ``ass:seq`` all carry ``never``). Each is an
#: attestation about the sender and the protocol: A-ENS the emission of the
#: specified ensemble, A-SEQ the sequential round structure, and A-SRC's
#: (SR3) the retention of Alice's system -- ``req:attestation-record``: the
#: engine "passes it through: it never verifies it and never asserts it of
#: any physical apparatus". The conforming behaviour for A-SRC is a PRESENCE
#: TEST and a PASS-THROUGH. The interface's ``never_verified.own``.
NEVER_VERIFIED: Final[tuple[AssumptionId, ...]] = tuple(
    identifier
    for identifier in AssumptionId
    if never_verified(ASSUMPTION_MACHINE_KEYS[identifier])
)
