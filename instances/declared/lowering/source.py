"""The source layer: an ensemble, an untrusted source, a WCP source.

Part of the lowering package (:mod:`instances.declared.lowering`).
"""

from __future__ import annotations

from collections.abc import Mapping
from fractions import Fraction
from typing import TYPE_CHECKING, Any

from certiqs_key.foundations import exact
from certiqs_key.protocol_compiler.spec import (
    Party,
    PublicChoices,
    SourcePart,
)
from certiqs_key.protocol_compiler.weights import (
    weighted_family,
)
from certiqs_key.transmitter.artifact import SourceSpecification, emit_artifact
from certiqs_key.transmitter.certificate import (
    BlockFormCertificate,
    RetentionAttestation,
    SourceReplacementCertificate,
)
from certiqs_key.transmitter.decoy import emit_decoy_declaration
from certiqs_key.transmitter.presentation import EnsemblePresentation
from certiqs_key.transmitter.reasons import SourceMode
from instances.declared.errors import DocumentError, DocumentReason, pointer
from instances.declared.lowering.base import (
    _DECLARED,
    _fraction,
    _LoweringBase,
    _ordered,
    _sectors,
    _Source,
)
from instances.declared.model import (
    AlicePovm,
    Attestation,
    BlockCertificate,
    ChoiceFamily,
    PresentationCertificate,
    PureCertificate,
    TrustedEnsemble,
    Untrusted,
    WcpDecoy,
)
from instances.declared.rules import placeholders as template_names
from instances.declared.rules import render as render_template

if TYPE_CHECKING:  # pragma: no cover - typing only
    pass


class _SourceLowering(_LoweringBase):
    """The source layer: a station's choice families and the source."""

    # -- the source ------------------------------------------------------------

    def choices(
        self,
        family: ChoiceFamily,
        party: Party,
        path: str,
        states: Mapping[str, exact.Matrix] | None = None,
    ) -> PublicChoices:
        """Return a choice family as ``PublicChoices`` (def:weighted's record)."""
        unknown = sorted(
            set(template_names(family.joint_label)) - {"choice", "outcome"}
        )
        if unknown:
            raise DocumentError(
                f"the joint label {family.joint_label!r} reads {unknown}; it may "
                "read {choice} and {outcome}",
                reason=DocumentReason.RULE_REFERENCE_UNKNOWN,
                path=path + pointer("joint_label"),
            )
        choices = tuple(family.choices)
        alphabets = {
            choice: tuple(family.conditional_alphabets.get(choice, ()))
            for choice in (*choices, *family.conditional_alphabets)
        }
        joint = {
            (outcome, choice): render_template(
                family.joint_label, {"choice": choice, "outcome": outcome}.get
            )
            for choice, outcomes in alphabets.items()
            for outcome in outcomes
        }
        elements: dict[str, dict[str, exact.Matrix]] = {}
        given = family.conditional_elements
        if given == "conjugate_states":
            # THE BAR IS APPLIED HERE, by the qubit instance's one function
            # (``conjugate_projector``, the ``conjugation_basis`` convention):
            # each conditional element is the entrywise conjugate of the state
            # its joint label names. A label with no declared state is left
            # out, for the compiler to refuse.
            from instances.common.conjugation import conjugate_projector

            for choice, outcomes in alphabets.items():
                elements[choice] = {
                    outcome: conjugate_projector(states[joint[(outcome, choice)]])
                    for outcome in outcomes
                    if states is not None and joint[(outcome, choice)] in states
                }
        else:
            for choice, by_outcome in given.items():
                elements[choice] = {
                    outcome: self.matrix(
                        node,
                        path + pointer("conditional_elements", choice, outcome),
                    )
                    for outcome, node in _ordered(
                        by_outcome, alphabets.get(choice, ())
                    ).items()
                }
        weights = {
            choice: _fraction(node, self.env, path + pointer("weights", choice))
            for choice, node in _ordered(family.weights, choices).items()
        }
        return PublicChoices(
            party=party,
            choices=choices,
            weights=weights,
            conditional_alphabets={
                choice: alphabets[choice] for choice in _ordered(alphabets, choices)
            },
            conditional_elements=_ordered(elements, choices),
            joint_labels=joint,
        )

    def attestation(self, node: Attestation | None) -> RetentionAttestation | None:
        if node is None:
            return None
        self.flag(
            "retention_attestation",
            "/source/retention_attestation",
            node.attested_by,
            f"The source's retention attestation, by {node.attested_by!r}. "
            f"{_DECLARED} The engine records it and never verifies it: the "
            "source-replacement licence rests on this statement (A-SRC). "
            f"Statement: {node.statement}",
        )
        return RetentionAttestation(
            attested_by=node.attested_by, statement=node.statement
        )

    def source(self) -> _Source:
        """Return the lowered source."""
        source = self.model.source
        if isinstance(source, WcpDecoy):
            return self._wcp(source)
        entries = self.alphabet(source.alphabet, "/source/alphabet")
        order = tuple(entry.label for entry in entries)
        weights = {
            label: _fraction(node, self.env, pointer("source", "weights", label))
            for label, node in _ordered(source.weights, order).items()
        }
        states = (
            None
            if source.states is None
            else {
                label: self.matrix(node, pointer("source", "states", label))
                for label, node in _ordered(source.states, order).items()
            }
        )
        if isinstance(source, Untrusted):
            povm = {
                label: self.matrix(node, pointer("source", "alice_povm", label))
                for label, node in _ordered(source.alice_povm, order).items()
            }
            specification = SourceSpecification(
                signal_alphabet=order,
                transmitted_dim=source.transmitted_dim,
                signal_weights=weights,
                signal_states=states,
                alice_dim=source.alice_dim,
                alice_povm=povm,
                source_mode_request=SourceMode.UNTRUSTED,
            )
            return _Source(
                SourcePart(artifact=self._emit(specification)),
                entries,
                source.alice_dim,
                "untrusted",
            )
        part, alice_dim = self._trusted(source, order, weights, states or {})
        return _Source(part, entries, alice_dim, "trusted")

    def _trusted(
        self,
        source: TrustedEnsemble,
        order: tuple[str, ...],
        weights: dict[str, Fraction],
        states: dict[str, exact.Matrix],
    ) -> tuple[SourcePart, int | None]:
        certificate = source.certificate
        attestation = self.attestation(source.retention_attestation)
        where = "/source/certificate"
        if isinstance(certificate, PresentationCertificate):
            presentation = EnsemblePresentation(
                virtual_sectors=_sectors(
                    certificate.virtual_sectors, where + "/virtual_sectors"
                ),
                weighted_blocks={
                    label: tuple(
                        self.matrix(node, where + pointer("weighted_blocks", label, i))
                        for i, node in enumerate(blocks)
                    )
                    for label, blocks in _ordered(
                        certificate.weighted_blocks, order
                    ).items()
                },
                retention_attestation=attestation,
            )
            specification = SourceSpecification(
                signal_alphabet=order,
                transmitted_dim=source.transmitted_dim,
                signal_weights=weights,
                signal_states=states,
                source_mode_request=SourceMode.TRUSTED,
                ensemble_presentation=presentation,
            )
            return SourcePart(artifact=self._emit(specification)), None
        # The model guarantees these three beside a certificate in pure or
        # block form (``TrustedEnsemble._presentation_without_alice``).
        assert source.alice is not None and source.alice_dim is not None
        assert source.alice_marginal is not None
        marginal = self.matrix(source.alice_marginal, "/source/alice_marginal")
        alice_choices: PublicChoices | None = None
        if isinstance(source.alice, AlicePovm):
            povm = {
                label: self.matrix(node, pointer("source", "alice", "povm", label))
                for label, node in _ordered(source.alice.povm, order).items()
            }
        else:
            alice_choices = self.choices(
                source.alice.choice_family,
                Party.ALICE,
                "/source/alice/choice_family",
                states,
            )
            # THE CONSTRUCTION AND NOT THE DECISION, as the qubit instance's
            # hand-built artefact does: def:weighted's weighting is applied
            # here to present {M_x}, and its emission decision is the
            # compiler's, which re-reads the choice record on SourcePart.
            povm = dict(weighted_family(alice_choices).elements)
        if isinstance(certificate, PureCertificate):
            pure = SourceReplacementCertificate(
                alice_marginal=marginal,
                psi=self.matrix(certificate.psi, where + "/psi"),
                virtual_dim=certificate.virtual_dim,
                virtual_weights=(
                    weights
                    if certificate.virtual_weights is None
                    else {
                        label: _fraction(
                            node, self.env, where + pointer("virtual_weights", label)
                        )
                        for label, node in _ordered(
                            certificate.virtual_weights, order
                        ).items()
                    }
                ),
                virtual_states=(
                    states
                    if certificate.virtual_states is None
                    else {
                        label: self.matrix(
                            node, where + pointer("virtual_states", label)
                        )
                        for label, node in _ordered(
                            certificate.virtual_states, order
                        ).items()
                    }
                ),
                retention_attestation=attestation,
            )
            specification = SourceSpecification(
                signal_alphabet=order,
                transmitted_dim=source.transmitted_dim,
                signal_weights=weights,
                signal_states=states,
                alice_dim=source.alice_dim,
                alice_povm=povm,
                source_mode_request=SourceMode.TRUSTED,
                alice_marginal=marginal,
                certificate=pure,
            )
        else:
            assert isinstance(certificate, BlockCertificate)
            block = self._block(certificate, order, attestation)
            # Alice's family is presented as matrices: at one sector "the block
            # list M_x IS the matrix M_x"; at several the transmitter refuses a
            # dense presentation, and that is its decision, not this layer's.
            specification = SourceSpecification(
                signal_alphabet=order,
                transmitted_dim=source.transmitted_dim,
                signal_weights=weights,
                signal_states=states,
                alice_dim=source.alice_dim,
                alice_povm=povm,
                alice_sectors=block.alice_sectors,
                source_mode_request=SourceMode.TRUSTED,
                alice_marginal=marginal,
                block_certificate=block,
            )
        part = SourcePart(
            artifact=self._emit(specification), alice_choices=alice_choices
        )
        return part, source.alice_dim

    def _block(
        self,
        certificate: BlockCertificate,
        order: tuple[str, ...],
        attestation: RetentionAttestation | None,
    ) -> BlockFormCertificate:
        where = "/source/certificate"
        return BlockFormCertificate(
            alice_sectors=_sectors(certificate.alice_sectors, where + "/alice_sectors"),
            virtual_sectors=_sectors(
                certificate.virtual_sectors, where + "/virtual_sectors"
            ),
            alice_marginal_blocks=tuple(
                self.matrix(node, where + pointer("alice_marginal_blocks", i))
                for i, node in enumerate(certificate.alice_marginal_blocks)
            ),
            psi_blocks=tuple(
                self.matrix(node, where + pointer("psi_blocks", i))
                for i, node in enumerate(certificate.psi_blocks)
            ),
            virtual_weights={
                label: _fraction(
                    node, self.env, where + pointer("virtual_weights", label)
                )
                for label, node in _ordered(certificate.virtual_weights, order).items()
            },
            virtual_blocks={
                label: tuple(
                    self.matrix(node, where + pointer("virtual_blocks", label, i))
                    for i, node in enumerate(blocks)
                )
                for label, blocks in _ordered(certificate.virtual_blocks, order).items()
            },
            retention_attestation=attestation,
        )

    def _emit(self, specification: SourceSpecification) -> Any:
        """Run the transmitter; its refusal is ``source_refused``."""
        result = emit_artifact(specification)
        if result.refusal is not None:
            raise DocumentError(
                f"the transmitter refused the source: {result.refusal.detail}",
                reason=DocumentReason.SOURCE_REFUSED,
                path="/source",
                module_reason=str(result.refusal.reason),
            )
        return result.artifact

    def _wcp(self, source: WcpDecoy) -> _Source:
        """Lower a ``wcp_decoy`` source through the decoy emission.

        The preparation record is appended to the configuration's
        ``input_preparation``, as decoy BB84 appends its own; the emission's
        refusal is ``source_refused`` with its own reason.
        """
        from instances.declared.wcp import lower_wcp

        attestation = self.attestation(source.retention_attestation)
        lowered = lower_wcp(
            source,
            self.env,
            tolerance=self.declared_tolerance,
            site=source.record_site or self.document_id,
            instance=source.record_label or f"{self.record_label}.source",
            attestation=attestation,
        )
        self.input_preparation.append(lowered.record)
        result = emit_decoy_declaration(lowered.tagged)
        if result.refusal is not None:
            raise DocumentError(
                f"the transmitter refused the source: {result.refusal.detail}",
                reason=DocumentReason.SOURCE_REFUSED,
                path="/source",
                module_reason=str(result.refusal.reason),
            )
        declaration = result.declaration
        assert declaration is not None  # DecoyResult's exclusive or
        part = SourcePart(
            declaration.as_transmitter_artifact(),
            source_links=declaration.source_segment,
        )
        return _Source(part, lowered.entries, None, "wcp_decoy", lowered)
