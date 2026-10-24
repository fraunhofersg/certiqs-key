"""The transmitter artefact: the seam the protocol compiler reads the source from.

SMALL ON PURPOSE. The compiler is not handed a ``SourcePart`` plus a
certificate to decide ``def:source-spec``'s conditions inline: those objects and
those decisions are this module's, and
spec/modules/transmitter/interface.yaml types what it emits; this file is that
outputs table as a frozen record, together with the decision that produces it
and the refusals that interface names. The compiler's ``transmitter_artifact``
input row binds to :class:`TransmitterArtifact` and to nothing else.

WHAT IT DECIDES (``def:source-spec``, ``def:srcert``, ``def:source-segment``)
============================================================================
The declared alphabet and its order; every ``M_x`` Hermitian and positive
semidefinite; ``sum_x M_x = 1_A`` as an identity of the declared numbers AND
accumulated in the declared order of ``X`` without rounding; the ensemble
weights non-negative and summing to one in the declared order without rounding;
every state in ``S_=``; in trusted mode ``tau_A in S_=(A)`` with its trace
accumulated over the row index without rounding; the certificate's five
conditions (:mod:`certiqs_key.transmitter.certificate`); and the source-link
admission conditions of C4. Unknown kinds and raw attempts to supply an
admitted segment are refused under their specific admission conditions.

THE ONE SLOT THIS MODULE EVER FILLS, and it is argued rather than defaulted.
``rem:da1`` with ``req:marginal-fill``: at ``d_A = 1`` the only marginal a
trusted specification can carry is ``tau_A = [1]``, "the unique element of
``S_=(A)``", so a trusted request that leaves the slot empty there IS SERVED
with that value. The artefact
RECORDS the fill (:attr:`TransmitterArtifact.marginal_slot_filled`) "so that
nothing is filled silently and a consumer can tell the two apart". At every
other dimension a trusted request without a certificate is REFUSED with
``trusted_mode_without_certificate``; ``tau_A = 1_A/d_A`` is never substituted
at any dimension, being "a strictly stronger claim than nomarg, not a neutral
one".

WHAT IT NEVER DOES. It asserts (SR3) of no apparatus -- the licence record is a
PASS-THROUGH and :class:`~certiqs_key.transmitter.certificate.SourceReplacementLicense`
refuses to be constructed otherwise -- it emits no receiver-side object, and it
emits no second carrier of the source mode: the mode IS the presence of the
marginal slot and is read off it (``rem:source-mode`` (a)).

SOURCE ADMISSION. C4 retires the empty-segment assumption. The core does
not admit a nonempty segment supplied as a raw specification: admitted source
links travel through their declaring submodule's artifact path, with A1--A3
and the registry conditions preserved. The compiler verifies that supplier
path rather than inferring admission from copied link data.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
from typing import Final

from certiqs_key.domain.bindings import (
    Bindings,
    LedgerBindings,
    exact,
    ledger_bindings_record,
)
from certiqs_key.domain.families import AliceForm
from certiqs_key.foundations.blocks import (
    BlockKind,
    Label,
    SectorStructure,
    single_alice_sector,
)
from certiqs_key.foundations.errors import MalformedInputError
from certiqs_key.foundations.exact import (
    Cx,
    Matrix,
    dimension,
    direct_sum,
    equal,
    identity,
    is_binary64,
    is_hermitian,
    is_positive_semidefinite,
    sum_in_declared_order,
    trace_in_row_order,
)
from certiqs_key.transmitter.certificate import (
    BlockFormCertificate,
    CertificateVerification,
    SourceReplacementCertificate,
    SourceReplacementLicense,
    verify_block_certificate,
    verify_certificate,
)
from certiqs_key.transmitter.links import (
    SOUNDNESS_REGISTRY,
    SoundnessRegistryEntry,
    SourceLink,
    check_source_link,
)
from certiqs_key.transmitter.presentation import (
    EnsemblePresentation,
    alice_marginal_blocks,
    alice_operators,
    verify_ensemble_presentation,
)
from certiqs_key.transmitter.reasons import (
    ASSUMPTION_MACHINE_KEYS,
    AssumptionId,
    CertificateForm,
    Refusal,
    RefusalReason,
    SourceMode,
)

__all__ = [
    "MATHEMATICAL_SPEC_VERSION",
    "SECTOR_BLOCK_KIND",
    "SourceSpecification",
    "TransmitterArtifact",
    "TransmitterResult",
    "alice_marginal_shape",
    "alice_measurement_shape",
    "emit_artifact",
    "source_replacement_bindings",
    "source_segment_from_admitting_module",
]

#: The ACCEPTED version this artefact pins: ``transmitter@`` followed by an
#: accepted ``version`` of spec/modules/transmitter/module.yaml.
#:
#: IT MOVES WITH THE CODE AND NOT WITH THE CLAIMS ALONE. An artefact "may not
#: claim a draft version" (PRINCIPLES.md section 6), and equally it may not
#: claim a version whose conditions it does not implement. Nothing numeric
#: moves with the string and no key rate reads it.
MATHEMATICAL_SPEC_VERSION: Final[str] = "transmitter@0.13.0"

#: The block kind an Alice-side sector structure of this module carries. It is
#: ``proof_sector`` at every site: what the decomposition records is WHY it may
#: be read off the declaration -- the certificate, the marginal and the POVM are
#: block diagonal by their presentation -- and not a physical decomposition of
#: the device (spec/architecture.md 2.3; ``def:source-link`` (e);
#: ``decoy/def:tagged-source`` (T5)).
SECTOR_BLOCK_KIND: Final[BlockKind] = BlockKind.PROOF_SECTOR

#: The unique element of ``S_=(A)`` at ``d_A = 1``, and the ONLY value this
#: module ever puts into an empty slot (``req:marginal-fill``).
_UNIT_MARGINAL: Final[Matrix] = ((Cx(Fraction(1), Fraction(0)),),)


@dataclass(frozen=True)
class SourceSpecification:
    """What a declaration hands this module: the inputs table, typed.

    ``source_mode_request`` IS an input key here and is not one of the
    compiler's: "a request not being an emission" (the interface's
    ``source_mode`` convention). The compiler reads the EMITTED mode off the
    artefact's marginal slot and serves no request of its own.
    """

    signal_alphabet: tuple[Label, ...]
    transmitted_dim: int
    signal_weights: Mapping[Label, Fraction]
    #: ``rho_x`` on ``A'``, or ``None`` where the specified ensemble is declared
    #: BY A SOURCE MODEL and not as matrices (``def:source-spec`` (b)). Such a
    #: specification "is presented WITH A NON-EMPTY SOURCE SEGMENT", so nothing
    #: of it is decided on matrices it does not have.
    signal_states: Mapping[Label, Matrix] | None = None
    #: ``d_A``, or ``None`` IN AN ENSEMBLE PRESENTATION, where ``A`` is not
    #: declared at all but defined as ``(+)_t A_t`` with ``A_t`` a copy of
    #: ``S_t`` (``def:srcert``; ``lem:ensemble-presentation``).
    alice_dim: int | None = None
    #: ``{M_x}`` as matrices -- the one-sector presentation, in which "the block
    #: list ``M_x`` IS the matrix ``M_x``". ``None`` in an ensemble
    #: presentation, where the POVM is defined and the POVM condition is a
    #: theorem, and at more than one sector, where
    #: :attr:`alice_povm_blocks` carries the presentation instead.
    alice_povm: Mapping[Label, Matrix] | None = None
    #: ``T``, ``{Pi^A_t}``, ``d_{A_t}``. ``None`` means THE ONE-SECTOR
    #: STRUCTURE, which is the default of ``def:source-spec`` and at which
    #: "every condition of this definition is the condition it was before
    #: sectors were declared".
    alice_sectors: SectorStructure | None = None
    #: ``{M_x}`` as block lists against :attr:`alice_sectors`. Exactly one of
    #: this and :attr:`alice_povm` is declared: two carriers of one family are
    #: two families that can disagree, and the dense ``M_x`` this module emits
    #: is then the DIRECT SUM of the blocks, which "is what the list MEANS, not
    #: a condition on it".
    alice_povm_blocks: Mapping[Label, tuple[Matrix, ...]] | None = None
    source_mode_request: SourceMode = SourceMode.UNTRUSTED
    #: ``tau_A``, where the request declares one. At ``d_A = 1`` a trusted
    #: request may leave it empty and is served (``req:marginal-fill``).
    alice_marginal: Matrix | None = None
    certificate: SourceReplacementCertificate | None = None
    #: The BLOCK form of ``def:srcert``. AT MOST ONE OF THE THREE CERTIFICATE
    #: SLOTS IS FILLED, and which one is filled IS the declared form.
    block_certificate: BlockFormCertificate | None = None
    #: The ENSEMBLE PRESENTATION of ``def:srcert``: the third form, and the only
    #: one in which ``A``, ``{M_x}`` and ``tau_A`` are not declared.
    ensemble_presentation: EnsemblePresentation | None = None
    #: ``Ch_src``. A non-empty raw specification requires admitting-module
    #: provenance and is refused here; an entry is
    #: either a declared link KIND, so that the refusal names what arrived, or a
    #: typed :class:`~certiqs_key.transmitter.links.SourceLink` a submodule
    #: built -- the kind is read off either
    #: (:func:`~certiqs_key.transmitter.links.source_link_kinds`).
    source_segment: tuple[str | SourceLink, ...] = ()

    def __post_init__(self) -> None:
        """Refuse a presentation that fills two certificate slots, or two POVM slots.

        NOT A REFUSAL BUT A HARD ERROR, for the reason every hard error of this
        repository is one: a specification filling two of the three certificate
        slots is not a presentation of an input ``def:source-spec`` types -- the
        declared form IS which slot is filled -- so no rule can be read against
        it and refusing it would have to invent a reason string. The same holds
        of a family declared twice, as matrices and as block lists.
        """
        declared = [
            name
            for name, value in (
                ("certificate", self.certificate),
                ("block_certificate", self.block_certificate),
                ("ensemble_presentation", self.ensemble_presentation),
            )
            if value is not None
        ]
        if len(declared) > 1:
            raise MalformedInputError(
                "a certificate is declared in ONE of the three forms of "
                f"def:srcert; this specification fills {declared}, and which "
                "slot is filled is what the declared form IS"
            )
        if self.alice_povm is not None and self.alice_povm_blocks is not None:
            raise MalformedInputError(
                "Alice's family is declared EITHER as matrices (the one-sector "
                "presentation, where the block list is the matrix) OR as block "
                "lists against the declared sector structure; two carriers of "
                "one family are two families that can disagree"
            )

    @property
    def declared_form(self) -> CertificateForm:
        """Return which form of ``def:srcert`` this specification declares.

        DERIVED FROM THE FILLED SLOT, exactly as the source mode is derived from
        the marginal slot, so that the form has no second carrier. A
        specification with no certificate at all reads as ``pure``: the pure
        form is the one-sector, no-sector-structure case, and an untrusted
        specification declares no certificate in any form.
        """
        if self.ensemble_presentation is not None:
            return CertificateForm.ENSEMBLE_PRESENTATION
        if self.block_certificate is not None:
            return CertificateForm.BLOCK
        return CertificateForm.PURE


@dataclass(frozen=True)
class TransmitterArtifact:
    """The emitted artefact: the outputs table of the transmitter's interface.

    EVERY FIELD IS A ROW OF THAT TABLE and carries the table's own key name,
    because the compiler reads them under those names. The mode is NOT a field:
    :attr:`source_mode` derives it from the marginal slot, which is where
    ``rem:source-mode`` (a) puts it.
    """

    signal_alphabet: tuple[Label, ...]
    alice_dim: int
    #: ``tau_A`` in trusted mode; ``None`` -- the machine value null, spelling
    #: nomarg -- in untrusted mode. ITS PRESENCE IS THE EMITTED MODE.
    alice_marginal: Matrix | None
    alice_povm: Mapping[Label, Matrix]
    #: ``A^v``, as its dimension. Equal to the specified transmitted system at
    #: ``L_s = 0``.
    virtual_transmitted_system: int
    virtual_ensemble_weights: Mapping[Label, Fraction]
    #: ``rho^v_x`` -- THE NORMALISED states, which only the PURE form declares.
    #: EMPTY in the block form and in an ensemble presentation, where the
    #: ensemble is emitted by its weighted members in
    #: :attr:`virtual_ensemble_blocks`: there ``rho^v_x = sigma^v_x / p_x`` is a
    #: QUOTIENT of declared numbers, need not be a binary64 number at all, and
    #: is formed by nobody. The interface's ``virtual_ensemble`` output row: it
    #: "is emitted by its WEIGHTED MEMBERS, like every ensemble of this module",
    #: and "in a presentation it is the declared blocks themselves".
    virtual_ensemble_states: Mapping[Label, Matrix]
    #: ``Ch_src``, ALWAYS EMITTED "so that a consumer composing a chain reads
    #: a segment and not a silence". EMPTY from :func:`emit_artifact`; NON-EMPTY
    #: -- typed ``SourceLink`` records -- in the artefact the decoy submodule
    #: emits (``DecoySourceDeclaration.as_transmitter_artifact``), admitted by
    #: kind under ``def:source-segment``.
    source_segment: tuple[str | SourceLink, ...] = ()
    #: Emitted in trusted mode at ``d_A >= 2`` only; vacuous at ``d_A = 1``
    #: and then NOT EMITTED AND NOT DEMANDED (``rem:da1``;
    #: ``req:licence-scope``).
    source_replacement_license: SourceReplacementLicense | None = None
    #: Whether the emitted ``alice_marginal`` is THIS MODULE'S value rather
    #: than a declared datum. True only in the ``d_A = 1`` case of
    #: ``req:marginal-fill``.
    marginal_slot_filled: bool = False
    assumption_ledger: tuple[str, ...] = ()
    mathematical_spec_version: str = MATHEMATICAL_SPEC_VERSION
    #: WHICH FORM THE CERTIFICATE WAS DECLARED IN, because which conditions were
    #: decided depends on it. ``pure`` for every artefact emitted from a
    #: pure-form or certificate-less declaration.
    certificate_form: CertificateForm = CertificateForm.PURE
    #: ``T``, ``{Pi^A_t}`` in the declared order, with block kind
    #: ``proof_sector``. ``None`` MEANS THE ONE-SECTOR STRUCTURE, which
    #: :attr:`alice_sectors` returns built from :attr:`alice_dim`.
    #:
    #: IT IS EMITTED AS A PRESENTATION DATUM: it says how ``{M_x}``, ``tau_A``
    #: and the certificate are presented and NOTHING about any joint state.
    #: What the states REACHED from a block-form certificate satisfy is
    #: ``lem:matched-pinching``; a restriction of a consumer's feasible set is
    #: not in it, and a consumer that minimises over block-diagonal operators
    #: does so under a theorem of its own module (``rem:boundary``).
    alice_sector_map: SectorStructure | None = None
    #: The MATCHED structure on ``A^v``, where a block form or a presentation
    #: declared one. ``None`` otherwise.
    virtual_sector_map: SectorStructure | None = None
    #: ``N^{(t)}_x = (sigma^{v,(t)}_x)^T`` of ``lem:ensemble-presentation`` (v):
    #: what a consumer reads of Alice's side in an ensemble presentation, where
    #: ``{M_x}`` is not declared and is formed by nobody. ``None`` in the two
    #: declared forms. THE CONSUMER THAT READS IT DOES NOT EXIST YET,
    #: which is why an ensemble presentation has no consumer today.
    alice_ensemble_operators: Mapping[Label, tuple[Matrix, ...]] | None = None
    #: ``sigma^{v,(t)}_x``: the virtual ensemble BY ITS WEIGHTED MEMBERS, block
    #: by block, in the block form and in an ensemble presentation. ``None`` in
    #: the pure form, where the declared ``rho^v_x`` travel instead.
    virtual_ensemble_blocks: Mapping[Label, tuple[Matrix, ...]] | None = None
    #: THE CLOSED LIST OF ADMITTED SOURCE-LINK KINDS, emitted verbatim with
    #: every artefact and never supplied by a request: it is a datum of the
    #: module VERSION that emitted the artefact (``def:source-segment`` (A1)).
    soundness_registry: tuple[SoundnessRegistryEntry, ...] = SOUNDNESS_REGISTRY
    #: THE BINDINGS OF THE ROWS A SOURCE MODEL SUPPLIES, by machine key: the
    #: physical-source assumption a submodule declares in the place of A-ENS
    #: (``def:source-spec`` (b); A-WCP for the decoy submodule), whose values
    #: (intensities, polarisations) are the model's and are not fields of this
    #: record. Empty for every artefact of the core. The core's own rows are
    #: bound from this record's fields (:attr:`assumption_bindings`).
    source_model_bindings: LedgerBindings = ()

    @property
    def assumption_bindings(self) -> LedgerBindings:
        """Return the declared values each ledger row binds, one entry per row.

        Beside each row of
        :attr:`assumption_ledger`, in its order, the declared values the
        row's assumption's clauses are about (:mod:`certiqs_key.domain.bindings`
        for the shape). READ OFF THIS RECORD'S OWN FIELDS, so an artefact an
        instance builds directly carries them as one :func:`emit_artifact`
        emits does:

        * A-ENS (``ass:ens``): ``source_ensemble`` -- the alphabet ``X``, the
          weights ``p_x`` of (i) and the transmitted system the states of (ii)
          act on. The row is emitted only for an ensemble declared as matrices,
          whose segment is empty, so the virtual ensemble this record carries
          IS the specified one (``def:srcert``, "One reading at every L_s").
          The states are operators and are not inlined.
        * A-SEQ (``ass:seq``): nothing. Its clauses are about the order of the
          physical protocol's steps, which no input of this module declares.
        * A-SRC (``ass:src``): :func:`source_replacement_bindings` -- the
          mode and the marginal of the premise, and the measurement of (ii).
        * a row a source model supplies: :attr:`source_model_bindings`.

        A key this record does not know binds nothing.
        """
        own: dict[str, Bindings] = {
            ASSUMPTION_MACHINE_KEYS[AssumptionId.A_ENS]: (
                (
                    "source_ensemble",
                    (
                        ("signal_alphabet", tuple(self.signal_alphabet)),
                        (
                            "weights",
                            tuple(
                                (label, exact(self.virtual_ensemble_weights[label]))
                                for label in self.signal_alphabet
                                if label in self.virtual_ensemble_weights
                            ),
                        ),
                        ("transmitted_dim", self.virtual_transmitted_system),
                    ),
                ),
            ),
            ASSUMPTION_MACHINE_KEYS[AssumptionId.A_SEQ]: (),
            ASSUMPTION_MACHINE_KEYS[AssumptionId.A_SRC]: source_replacement_bindings(
                source_mode=self.source_mode,
                alphabet=self.signal_alphabet,
                alice_dim=self.alice_dim,
                sectors=self.alice_sectors,
                form=(
                    AliceForm.ENSEMBLE
                    if self.certificate_form is CertificateForm.ENSEMBLE_PRESENTATION
                    else AliceForm.POVM
                ),
            ),
        }
        own.update(dict(self.source_model_bindings))
        return tuple((key, own.get(key, ())) for key in self.assumption_ledger)

    @property
    def source_mode(self) -> SourceMode:
        """Return the EMITTED mode, derived from the marginal slot alone.

        "Its presence is the emitted mode", and there is no second carrier of
        it anywhere in this record -- which is what stops the two from ever
        disagreeing.
        """
        return (
            SourceMode.UNTRUSTED
            if self.alice_marginal is None
            else SourceMode.TRUSTED
        )

    @property
    def alice_sectors(self) -> SectorStructure:
        """Return the emitted structure of ``A``, THE ONE-SECTOR MAP BY DEFAULT.

        ``def:source-spec`` makes the one-sector structure the default and says
        that at one sector "every condition of this definition is the condition
        it was before sectors were declared", so an artefact that declared none
        answers with :func:`~certiqs_key.foundations.blocks.single_alice_sector` --
        the degenerate case said in the general shape, which is the shared
        format's own reading of it.
        """
        if self.alice_sector_map is not None:
            return self.alice_sector_map
        return single_alice_sector(self.alice_dim, SECTOR_BLOCK_KIND)

    @property
    def is_degenerate_presentation(self) -> bool:
        """Whether this artefact is the degenerate case, ENTRY FOR ENTRY.

        The pure form, no declared sector structure and an empty segment: the
        plain shape, which the general module reproduces
        unchanged. :meth:`as_machine_record` reads it.
        """
        return (
            self.certificate_form is CertificateForm.PURE
            and self.alice_sector_map is None
            and self.virtual_sector_map is None
            and self.alice_ensemble_operators is None
            and self.virtual_ensemble_blocks is None
            and not self.source_segment
        )

    def as_machine_record(self) -> dict[str, object]:
        """Return the artefact as a machine record, under the table's keys.

        THE DEGENERATE CASE'S RECORD IS THE RECORD IT WAS, KEY FOR KEY, and the
        keys of the general declaration appear only where the declaration uses
        what they carry. Two rules meet here and this is how they are reconciled.

        The interface types ``alice_sector_map`` and ``soundness_registry``
        with presence "always", the sector map "the one-sector structure by
        default". The design rule is that "today's declaration is
        the one-sector, pure-form, empty-segment case of the amended one, ENTRY
        FOR ENTRY, so no frozen refusal string and no accepted instance moves" --
        and an accepted instance's record is what a run manifest digests
        (:func:`certiqs_key.runs.flow.artefact_digest`), so a record that gained
        keys for a structure the declaration does not declare would move an
        accepted instance.

        THE READING TAKEN, and it is the conservative one: an absent key MEANS
        its default, as an absent ``alice_marginal`` already means untrusted
        mode -- the one-sector structure for the map, ``pure`` for the form, and
        for the registry the fact that decides nothing where the segment is
        empty, no triple then being compared. :attr:`soundness_registry` and
        :attr:`alice_sectors` are always present ON THE RECORD OBJECT, which is
        what a consumer in this process reads; the wire form gains them the
        moment a declaration uses them, which is also the moment they decide
        something.

        ``assumption_bindings`` IS ON EVERY RECORD, like ``assumption_ledger``
        beside which it stands:
        it is no structure of the general declaration but the declared values
        each ledger row binds, and every artefact has a ledger. It is on the
        record of every artefact, the degenerate one included.
        """
        licence = self.source_replacement_license
        record: dict[str, object] = {
            "signal_alphabet": list(self.signal_alphabet),
            "alice_dim": self.alice_dim,
            "alice_marginal": self.alice_marginal,
            "alice_marginal_slot_filled": self.marginal_slot_filled,
            "alice_povm": dict(self.alice_povm),
            "virtual_transmitted_system": self.virtual_transmitted_system,
            "virtual_ensemble": {
                "weights": dict(self.virtual_ensemble_weights),
                "states": dict(self.virtual_ensemble_states),
            },
            "source_segment": [
                link if isinstance(link, str) else link.as_machine_record()
                for link in self.source_segment
            ],
            "source_replacement_license": (
                None if licence is None else licence.as_machine_record()
            ),
            "assumption_ledger": list(self.assumption_ledger),
            "assumption_bindings": ledger_bindings_record(self.assumption_bindings),
            "mathematical_spec_version": self.mathematical_spec_version,
        }
        if self.is_degenerate_presentation:
            return record
        sectors = self.alice_sectors
        record["certificate_form"] = str(self.certificate_form)
        record["alice_sector_map"] = {
            "sector_index_set": list(sectors.labels),
            "sector_dims": list(sectors.dims),
            "sector_block_kind": str(sectors.block_kind),
            "matched_virtual_dims": (
                None
                if self.virtual_sector_map is None
                else list(self.virtual_sector_map.dims)
            ),
        }
        record["soundness_registry"] = [
            {
                "kind": str(entry.kind),
                "soundness_claim": entry.soundness_claim,
                "assumptions": list(entry.assumptions),
            }
            for entry in self.soundness_registry
        ]
        if self.alice_ensemble_operators is not None:
            record["alice_ensemble_operators"] = {
                label: list(blocks)
                for label, blocks in self.alice_ensemble_operators.items()
            }
        if self.virtual_ensemble_blocks is not None:
            record["virtual_ensemble_weighted_members"] = {
                label: list(blocks)
                for label, blocks in self.virtual_ensemble_blocks.items()
            }
        return record


def alice_measurement_shape(
    alphabet: Sequence[Label], alice_dim: int, form: AliceForm
) -> tuple[tuple[str, object], ...]:
    """Return Alice's measurement ``{M_x}`` as a binding binds it: by its shape.

    The form of (DX4) -- ``povm`` where ``{M_x}`` is declared, ``ensemble``
    in an ensemble presentation, where it is defined and not declared
    (``lem:ensemble-presentation``) -- the alphabet ``X`` that indexes it and
    the dimension of ``A``. Its matrices stay in the artefact
    (:mod:`certiqs_key.domain.bindings`: an operator is never inlined).
    """
    return (
        ("form", str(form)),
        ("alphabet", tuple(alphabet)),
        ("dimension", alice_dim),
    )


def alice_marginal_shape(
    alice_dim: int, sectors: SectorStructure
) -> tuple[tuple[str, object], ...]:
    """Return ``tau_A`` as a binding binds it: ``A``'s dimension and sectors."""
    return (
        ("dimension", alice_dim),
        ("sector_dims", tuple(sectors.dims)),
    )


def source_replacement_bindings(
    *,
    source_mode: SourceMode,
    alphabet: Sequence[Label],
    alice_dim: int,
    sectors: SectorStructure,
    form: AliceForm,
) -> Bindings:
    """Return the declared values A-SRC (``ass:src``) binds.

    The premise is "a source specification in trusted-source mode, which
    fills the marginal slot with ``tau_A``": ``source_mode`` and
    ``alice_marginal``. Clause (ii) names "her declared measurement
    ``{M_x}``": ``alice_povm``. Clause (i), that ``A`` is retained, is about
    the laboratory and binds no further declared value. Shared with the decoy
    submodule, whose artefact carries A-SRC from the same premise.
    """
    return (
        ("source_mode", str(source_mode)),
        ("alice_marginal", alice_marginal_shape(alice_dim, sectors)),
        ("alice_povm", alice_measurement_shape(alphabet, alice_dim, form)),
    )


def source_segment_from_admitting_module(artifact: TransmitterArtifact) -> bool:
    """Whether the artifact has the exact supplier type that admits its links.

    The core artifact type is deliberately not evidence of (A3): callers may
    construct it and may copy a link tuple onto it.  Each admitting submodule
    owns its private emitted subtype and its structural recheck.  This core
    dispatcher recognizes only registered link kinds and exact supplier types;
    an unknown, mixed or generic carrier therefore returns ``False``.
    """
    if not artifact.source_segment:
        return False
    from certiqs_key.transmitter.decoy.emit import artifact_admits_source_segment

    return artifact_admits_source_segment(artifact)


@dataclass(frozen=True)
class TransmitterResult:
    """An artefact or a refusal. NEVER BOTH AND NEVER NEITHER.

    The ``fail_closed`` convention: "Each is a REFUSAL with a machine-readable
    reason and no artefact." A result carrying both would be a half-emission
    this module has no shape for.
    """

    artifact: TransmitterArtifact | None
    refusal: Refusal | None
    #: The certificate's verdicts, where one was presented and decided. Kept so
    #: that the consumer's gate (G2) can be compared against the decision taken
    #: here without re-deriving it; the gate re-decides the five ANYWAY, on the
    #: emitted data, which is the ``decide_never_infer`` rule.
    certificate_verification: CertificateVerification | None = None

    def __post_init__(self) -> None:
        """Refuse a result that emits and refuses, or does neither."""
        if (self.artifact is None) == (self.refusal is None):
            raise MalformedInputError(
                "a transmitter result carries an artefact or a refusal and "
                "never both and never neither (the fail_closed convention)"
            )

    def require(self) -> TransmitterArtifact:
        """Return the artefact, for a caller that has already handled refusal."""
        if self.artifact is None:
            raise MalformedInputError(
                "this specification was refused; there is no artefact to take"
            )
        return self.artifact


def _refuse(reason: RefusalReason, detail: str) -> TransmitterResult:
    return TransmitterResult(artifact=None, refusal=Refusal(reason, detail))


def _weights_are_normalized(
    order: Sequence[Label], weights: Mapping[Label, Fraction]
) -> str | None:
    """Return why the weights are not a distribution, or ``None``.

    Non-negativity by SIGN, the sum exactly one IN THE DECLARED ORDER, and that
    sum required to round nowhere -- the three legs the
    ``ensemble_weights_not_normalized`` row names, decided separately so that
    the detail says which failed.
    """
    running = Fraction(0)
    rounds_nowhere = True
    for label in order:
        if label not in weights:
            return f"no declared weight for {label!r}"
        weight = weights[label]
        if weight < 0:
            return f"the declared weight of {label!r} is negative"
        running += weight
        if not is_binary64(running):
            rounds_nowhere = False
    if running != 1:
        return f"the declared weights sum to {running} and not to 1"
    if not rounds_nowhere:
        return "the weight sum, accumulated in the declared order of X, rounds"
    return None


def _virtual_pair_diverges(
    spec: SourceSpecification,
    certificate: SourceReplacementCertificate,
    signal_states: Mapping[Label, Matrix],
) -> str | None:
    """Return why the certificate's virtual pair is not the specified pair.

    ``def:srcert``'s "One reading at every ``L_s``": at ``L_s = 0`` the virtual
    system and ensemble ARE the specified ones, ``A^v = A'`` and
    ``rho^v_x = rho_x``, and the two pairs are LITERALLY EQUAL. This guard
    concerns that empty-segment case; an admitted nonempty segment instead
    carries the source-map relation described below.

    WHY IT NEEDS A GUARD AND NOT A CHECK, AND WHY THE GAP IS EASY TO MISS. At
    ``L_s >= 1`` the relation between the two pairs is decided by
    ``def:source-segment`` (S3), ``Xi(rho^v_x) = rho_x`` on the emitted
    matrices: they are MEANT to differ there and the source map is what relates
    them. At ``L_s = 0`` (S1)-(S4) are vacuous, and rightly so -- they quantify
    over an empty list of links -- but the equality does not thereby become
    unconstrained: it becomes DEFINITIONAL, carried by the input typing instead
    of by a check. A presentation whose certificate is internally consistent --
    (SR1) and (SR2) holding against its OWN virtual pair -- while that pair
    diverges from the specified one is otherwise checked by nothing at all, and
    emits a TRUSTED artefact describing a source other than the one the
    specification declares. That is the mis-specified-source hazard the
    compiler's gate outcome table row 3 exists to prevent, reached by a route
    no enumerated condition covers.

    THE CATEGORY IS :class:`~certiqs_key.foundations.errors.MalformedInputError` and
    not a refusal, for the reason every hard error of this repository is one:
    such a presentation is not a presentation of an input the interface types,
    so no rule can be read against it and refusing it would have to invent a
    reason string. The comparison is EXACT, with no tolerance -- a virtual
    state that differs from the specified one by any amount at all is a
    different state.

    THIS GUARD IS HERE AND NOT IN THE COMPILER because the transmitter owns
    both pairs and the compiler is handed ONE, the artefact's; what remains on the
    consumer's side is to re-decide that the certificate it receives is written against
    the pair the artefact emits.
    """
    if certificate.virtual_dim != spec.transmitted_dim:
        return (
            "at L_s = 0 the virtual transmitted system IS the specified one "
            "(def:srcert, 'One reading at every L_s': A^v = A'), but the "
            f"certificate declares dim H(A^v) = {certificate.virtual_dim} "
            f"against a transmitted system of dimension {spec.transmitted_dim}"
        )
    if set(certificate.virtual_weights) != set(spec.signal_weights) or set(
        certificate.virtual_states
    ) != set(signal_states):
        return (
            "at L_s = 0 the virtual ensemble IS the specified ensemble, but "
            "the certificate and the specification are indexed by different "
            "signal alphabets"
        )
    for label in spec.signal_alphabet:
        if certificate.virtual_weights[label] != spec.signal_weights[label]:
            return (
                "at L_s = 0 the virtual ensemble IS the specified ensemble "
                f"(rho^v_x = rho_x, with the weights p_x shared), but p_{label!r} "
                f"is {certificate.virtual_weights[label]} in the certificate "
                f"and {spec.signal_weights[label]} in the specification"
            )
        if not equal(certificate.virtual_states[label], signal_states[label]):
            return (
                "at L_s = 0 the virtual ensemble IS the specified ensemble "
                f"(rho^v_x = rho_x), but the certificate's rho^v_{label!r} "
                f"differs from the specified rho_{label!r}. A certificate "
                "internally consistent against a DIFFERENT pair would "
                "otherwise emit a trusted artefact describing a source other "
                "than the specified one"
            )
    return None


def _state_is_admissible(state: Matrix, dim: int) -> bool:
    """Whether ``state`` lies in ``S_=`` of a ``dim``-dimensional system."""
    if dimension(state) != dim:
        return False
    if not is_hermitian(state) or not is_positive_semidefinite(state):
        return False
    accumulated = trace_in_row_order(state)
    return accumulated.value == Cx(Fraction(1), Fraction(0))


def emit_artifact(spec: SourceSpecification) -> TransmitterResult:
    """Decide ``def:source-spec`` and emit the artefact, or refuse naming a rule.

    The order of the decisions is this file's and no claim fixes it; what the
    claims DO fix is that the virtual ensemble's own conditions are decided
    BEFORE the five conditions on the certificate and are not among them (the
    ``ensemble_state_not_admissible`` row), and that a certificate present and
    failing is refused AT EVERY ``d_A`` (``req:failing-certificate``). Both
    are respected below.
    """
    order = spec.signal_alphabet
    if not order or len(set(order)) != len(order):
        return _refuse(
            RefusalReason.SIGNAL_ALPHABET_EMPTY_OR_UNORDERED,
            "X is finite, non-empty, ordered and its labels pairwise distinct "
            f"(def:source-spec); the declared alphabet is {list(order)}",
        )

    sectors = _declared_sectors(spec)
    povm_blocks = _declared_povm_blocks(spec, sectors)

    # --- Alice's POVM: admissibility, completeness, and (S) on the sum, PER
    # --- BLOCK. AT THE DEFAULT ONE-SECTOR STRUCTURE THIS IS THE MATRIX
    # --- CONDITION IT WAS, "the block list M_x IS the matrix M_x", and the
    # --- detail strings are the strings they were. NOT DECIDED AT ALL in an
    # --- ensemble presentation, where {M_x} is not declared and the POVM
    # --- condition is a theorem (lem:ensemble-presentation (i)).
    if povm_blocks is not None:
        povm_refusal = _decide_povm(order, sectors, povm_blocks)
        if povm_refusal is not None:
            return povm_refusal

    # --- The SPECIFIED ensemble, before any certificate is read. -----------
    bad_weights = _weights_are_normalized(order, spec.signal_weights)
    if bad_weights is not None:
        return _refuse(
            RefusalReason.ENSEMBLE_WEIGHTS_NOT_NORMALIZED,
            f"the SPECIFIED ensemble: {bad_weights}",
        )
    specified_states = spec.signal_states
    if specified_states is None:
        # DECLARED BY A SOURCE MODEL (def:source-spec (b)): the weights and the
        # states are "mathematical objects and not matrices", so there is
        # nothing here to decide exactly and nothing is decided. Such a
        # specification "is presented WITH A NON-EMPTY SOURCE SEGMENT", and the
        # raw core path refuses it for missing admitting-module provenance. A
        # model-declared specification with an EMPTY segment is not a
        # presentation of the input def:source-spec types -- there would be no
        # route from the virtual ensemble back to the specified one at all.
        if not spec.source_segment:
            raise MalformedInputError(
                "a specification whose ensemble is declared by a source model "
                "is presented WITH A NON-EMPTY SOURCE SEGMENT (def:source-spec "
                "(b)), so that what a consumer receives is the finite "
                "dimensional virtual ensemble and never the model; this one "
                "declares no states and carries no segment"
            )
    else:
        for label in order:
            if label not in specified_states or not _state_is_admissible(
                specified_states[label], spec.transmitted_dim
            ):
                return _refuse(
                    RefusalReason.ENSEMBLE_STATE_NOT_ADMISSIBLE,
                    f"the SPECIFIED ensemble: rho_{label!r} is not in S_=(A')",
                )

    # Core specifications are not artifacts of an admitting submodule (A3).
    # The decoy emitter owns admission and returns its artifact directly.
    for link in spec.source_segment:
        kind = link if isinstance(link, str) else str(link.kind)
        if kind == "source-map":
            return _refuse(RefusalReason.LINK_KIND_DEFERRED,
                           "the source-map kind is declared but deferred")
        if kind not in {str(entry.kind) for entry in SOUNDNESS_REGISTRY}:
            return _refuse(RefusalReason.SOURCE_LINK_KIND_NOT_ADMITTED,
                           f"source link kind {kind!r} has no admitted registry entry")
        if isinstance(link, str):
            return _refuse(RefusalReason.SOURCE_SEGMENT_NOT_FROM_ADMITTING_MODULE,
                           "a kind string is not an admitting-submodule artifact")
        refusal = check_source_link(link, assumption_ledger=(),
                                    from_admitting_module=False)
        if refusal is not None:
            return TransmitterResult(artifact=None, refusal=refusal)

    if spec.ensemble_presentation is not None:
        return _emit_from_presentation(spec, order, spec.ensemble_presentation)

    # --- The mode, the marginal, and the one filled slot. -------------------
    trusted = spec.source_mode_request is SourceMode.TRUSTED
    if not trusted and spec.certificate is not None:
        # A CERTIFICATE IS TRUSTED MODE ONLY, and an untrusted request carrying
        # one is NOT A STATE OF AFFAIRS THIS MODULE ADMITS: def:source-spec
        # gives the certificate to the trusted mode alone ("it additionally
        # carries"), so no rule of this module can be read against such a
        # presentation and refusing it would have to invent a reason string.
        #
        # NO REFUSAL STRING FITS IT: `trusted_mode_without_certificate`, whose
        # interface condition is "trusted mode is requested at d_A >= 2 and the
        # certificate is absent", would say a certificate was missing when one
        # was supplied, and no other row of the interface's `refusal_reasons`
        # covers this condition. The COMPILER treats the symmetric case the same
        # way, with the same reasoning, at
        # :meth:`certiqs_key.protocol_compiler.gates.GateInputs.__post_init__`.
        raise MalformedInputError(
            "a source-replacement certificate is TRUSTED MODE ONLY "
            "(def:source-spec, 'it additionally carries'); an untrusted "
            "request carrying one is not a presentation of an input this "
            "module types, so no rule can be read against it"
        )
    if not trusted and spec.block_certificate is not None:
        # THE SAME GUARD AND THE SAME REASONING, for the block form: a
        # certificate is trusted mode only in EVERY form, so an untrusted
        # request carrying one is not a presentation of an input this module
        # types. The ensemble presentation is caught by the same rule in
        # :func:`_emit_from_presentation`.
        raise MalformedInputError(
            "a source-replacement certificate is TRUSTED MODE ONLY in every "
            "form (def:source-spec, 'it additionally carries'); an untrusted "
            "request carrying a BLOCK FORM is not a presentation of an input "
            "this module types, so no rule can be read against it"
        )
    alice_dim = spec.alice_dim
    assert alice_dim is not None  # _declared_sectors refuses a missing d_A
    if sectors.count > 1 and spec.block_certificate is None:
        # def:source-spec: "A sector structure with more than one sector is
        # declared only in trusted-source mode and only together with a
        # certificate in block form or an ensemble presentation." A structure
        # with two sectors and no such certificate is therefore not a
        # presentation of the input the definition types -- there is no form in
        # which it is declared at all -- and no refusal reason of the interface
        # names the condition, so the category is the hard one.
        raise MalformedInputError(
            f"the declared sector structure carries {sectors.count} sectors "
            f"{list(sectors.labels)} and no certificate in block form or "
            "ensemble presentation; more than one sector is declared only in "
            "trusted-source mode and only with one of those two forms "
            "(def:source-spec)"
        )
    marginal = spec.alice_marginal
    filled = False
    if trusted and spec.block_certificate is not None:
        # TAU_A REACHES THE EMITTED DATA THROUGH THE CERTIFICATE here too, and
        # in block form it reaches it as a BLOCK LIST: the emitted dense tau_A
        # is the direct sum of the declared blocks, which "is what the list
        # MEANS, not a condition on it". A separately declared matrix must be
        # that same matrix, for the reason the pure form's guard gives.
        block_marginal = direct_sum(list(spec.block_certificate.alice_marginal_blocks))
        if marginal is not None and not equal(marginal, block_marginal):
            raise MalformedInputError(
                "the declared alice_marginal and the direct sum of the block "
                "certificate's tau^{(t)}_A differ; tau_A reaches the emitted "
                "data through the certificate and a second carrier of it is a "
                "second source of truth"
            )
        marginal = block_marginal
    if trusted and spec.certificate is not None:
        # TAU_A REACHES THE EMITTED DATA THROUGH THE CERTIFICATE, which is what
        # makes the emitted marginal THE CERTIFICATE'S rather than an
        # independently declared number (the compiler's thm:gates, proof, Step 2;
        # def:srcert (SR1)). A specification may still declare it separately --
        # `alice_marginal` is an input row of this module -- and where it does,
        # THE TWO MUST BE THE SAME MATRIX: two carriers of one datum are two
        # data that can disagree, and (SR1) would then be decided against one
        # of them and emitted from the other.
        if marginal is not None and not equal(
            marginal, spec.certificate.alice_marginal
        ):
            raise MalformedInputError(
                "the declared alice_marginal and the certificate's differ; "
                "tau_A reaches the emitted data through the certificate and "
                "a second carrier of it is a second source of truth"
            )
        marginal = spec.certificate.alice_marginal
    if trusted and marginal is None and alice_dim == 1:
        # rem:da1: S_=(A) is a singleton here, so the filled value is the only
        # admissible one and the filled slot excludes nothing. IT IS RECORDED
        # (req:marginal-fill).
        marginal = _UNIT_MARGINAL
        filled = True
    if trusted:
        if marginal is None or not _state_is_admissible(marginal, alice_dim):
            if marginal is None:
                return _refuse(
                    RefusalReason.TRUSTED_MODE_WITHOUT_CERTIFICATE,
                    "trusted mode is requested at d_A >= 2 with no marginal "
                    "and no certificate to read one off; tau_A = 1_A/d_A is "
                    "NEVER substituted, being a strictly stronger claim than "
                    "nomarg and not a neutral one (ass:src)",
                )
            return _refuse(
                RefusalReason.ALICE_MARGINAL_NOT_ADMISSIBLE,
                "tau_A is not in S_=(A); a SINGULAR tau_A is admissible and "
                "tau_A = 0 is not, its trace being 0",
            )
        if not trace_in_row_order(marginal).rounds_nowhere:
            return _refuse(
                RefusalReason.ALICE_MARGINAL_TRACE_ROUNDS,
                "tr tau_A = 1 holds only as a computed sum: the trace, "
                "accumulated over the row index, rounds",
            )
    else:
        marginal = None

    # --- The certificate. Present and failing is refused AT EVERY d_A. -----
    verification: CertificateVerification | None = None
    licence: SourceReplacementLicense | None = None
    block = spec.block_certificate
    if spec.certificate is not None:
        assert povm_blocks is not None
        virtual_bad = _weights_are_normalized(
            order, spec.certificate.virtual_weights
        )
        if virtual_bad is not None:
            return _refuse(
                RefusalReason.ENSEMBLE_WEIGHTS_NOT_NORMALIZED,
                f"the VIRTUAL ensemble: {virtual_bad}",
            )
        for label in order:
            if label not in spec.certificate.virtual_states or (
                not _state_is_admissible(
                    spec.certificate.virtual_states[label],
                    spec.certificate.virtual_dim,
                )
            ):
                return _refuse(
                    RefusalReason.ENSEMBLE_STATE_NOT_ADMISSIBLE,
                    f"the VIRTUAL ensemble: rho^v_{label!r} is not in S_=(A^v)",
                )
        assert specified_states is not None  # a pure form declares its matrices
        divergence = _virtual_pair_diverges(spec, spec.certificate, specified_states)
        if divergence is not None:
            raise MalformedInputError(divergence)
        verification = verify_certificate(
            spec.certificate, order, _dense_povm(order, sectors, povm_blocks)
        )
        refusal = verification.refusal()
        if refusal is not None:
            return TransmitterResult(
                artifact=None,
                refusal=refusal,
                certificate_verification=verification,
            )
        if alice_dim >= 2:
            licence = SourceReplacementLicense.pass_through(
                verification,
                spec.certificate.retention_attestation,
                spec.certificate,
            )
    elif block is not None:
        assert povm_blocks is not None
        # A block form reaches this branch with an EMPTY source segment (a
        # non-empty one is refused above for its provenance, (A3)), so its
        # virtual ensemble IS the specified one and the specified matrices are
        # the declared entries of sigma^v_x = p_x rho_x.
        assert specified_states is not None and not spec.source_segment
        block_refusal = _decide_block_certificate(
            order, sectors, block, povm_blocks, spec, specified_states
        )
        if block_refusal is not None:
            return block_refusal
        # req:licence-scope, with interface.yaml's source_replacement_license
        # row ("trusted mode at d_A >= 2 only") and rem:da1 (the licence is
        # vacuous at d_A = 1): a verifying block certificate at d_A = 1 emits
        # none, as the pure form above and the ensemble presentation do.
        if alice_dim >= 2:
            licence = SourceReplacementLicense.pass_through_block(
                verify_block_certificate(block, order, povm_blocks),
                block.retention_attestation,
                block,
            )
    elif trusted and alice_dim >= 2:
        return _refuse(
            RefusalReason.TRUSTED_MODE_WITHOUT_CERTIFICATE,
            "trusted mode is requested at d_A >= 2 and the certificate is "
            "absent (ass:src is stated of trusted-source mode; "
            "req:licence-scope fixes the d_A >= 2 scope)",
        )

    if block is not None:
        virtual_dim = block.virtual_dim
        virtual_weights: Mapping[Label, Fraction] = block.virtual_weights
        # rho^v_x IS NOT EMITTED IN BLOCK FORM AND IS FORMED BY NOBODY: it is
        # sigma^v_x / p_x, a quotient of declared numbers that need not be a
        # binary64 number at all, and the interface's `virtual_ensemble` output
        # row emits every ensemble "by its WEIGHTED MEMBERS". Those travel in
        # `virtual_ensemble_blocks`.
        virtual_states: Mapping[Label, Matrix] = {}
        virtual_blocks: Mapping[Label, tuple[Matrix, ...]] | None = (
            block.virtual_blocks
        )
        virtual_sector_map: SectorStructure | None = block.virtual_sectors
    else:
        virtual_dim = (
            spec.transmitted_dim
            if spec.certificate is None
            else spec.certificate.virtual_dim
        )
        virtual_weights = (
            spec.signal_weights
            if spec.certificate is None
            else spec.certificate.virtual_weights
        )
        virtual_states = (
            (specified_states or {})
            if spec.certificate is None
            else spec.certificate.virtual_states
        )
        virtual_blocks = None
        virtual_sector_map = None

    # A-ENS IN TRUSTED-SOURCE MODE ONLY (the interface's emission_rule key
    # `trusted_mode_matrix_declared_ensemble`):
    # in untrusted-source mode no claim of a run's closure uses the declared
    # ensemble (thm:accumulated-entropy does not, and the compiler claims that
    # declare A-ENS without a mode condition do not use it there either), so
    # the row is not emitted. The mode is the marginal slot (rem:source-mode).
    ledger = [
        *(
            [ASSUMPTION_MACHINE_KEYS[AssumptionId.A_ENS]]
            if marginal is not None
            else []
        ),
        ASSUMPTION_MACHINE_KEYS[AssumptionId.A_SEQ],
    ]
    if licence is not None:
        ledger.append(ASSUMPTION_MACHINE_KEYS[AssumptionId.A_SRC])

    assert povm_blocks is not None
    return TransmitterResult(
        artifact=TransmitterArtifact(
            signal_alphabet=order,
            alice_dim=alice_dim,
            alice_marginal=marginal,
            alice_povm=_dense_povm(order, sectors, povm_blocks),
            virtual_transmitted_system=virtual_dim,
            virtual_ensemble_weights=dict(virtual_weights),
            virtual_ensemble_states=dict(virtual_states),
            virtual_ensemble_blocks=(
                None if virtual_blocks is None else dict(virtual_blocks)
            ),
            source_segment=(),
            source_replacement_license=licence,
            marginal_slot_filled=filled,
            assumption_ledger=tuple(ledger),
            certificate_form=spec.declared_form,
            alice_sector_map=spec.alice_sectors,
            virtual_sector_map=virtual_sector_map,
        ),
        refusal=None,
        certificate_verification=verification,
    )


def _declared_sectors(spec: SourceSpecification) -> SectorStructure:
    """Return the declared structure of ``A``, or the one-sector default.

    IN AN ENSEMBLE PRESENTATION ``A`` IS NOT DECLARED and the structure is the
    virtual one read on the other side, ``A_t`` a copy of ``S_t``
    (``lem:ensemble-presentation``); a specification that declared both would
    carry two structures for one system.
    """
    presentation = spec.ensemble_presentation
    if presentation is not None:
        if spec.alice_sectors is not None or spec.alice_dim is not None:
            raise MalformedInputError(
                "an ensemble presentation declares neither A nor its sector "
                "structure: A_t is a COPY of S_t and the matched pair is the "
                "declared structure read on both sides (def:srcert; "
                "lem:ensemble-presentation). This specification declares one "
                "as well, which is a second carrier of one system"
            )
        return presentation.alice_sectors
    if spec.alice_dim is None:
        raise MalformedInputError(
            "a specification that is not an ensemble presentation DECLARES A "
            "with its dimension and its computational basis (def:source-spec); "
            "this one carries no d_A, and this module supplies none"
        )
    if spec.alice_sectors is None:
        return single_alice_sector(spec.alice_dim, SECTOR_BLOCK_KIND)
    if spec.alice_sectors.total_dim != spec.alice_dim:
        raise MalformedInputError(
            "the declared sector structure decomposes H(A), so "
            f"sum_t d_(A_t) = d_A; the structure totals "
            f"{spec.alice_sectors.total_dim} against d_A = {spec.alice_dim}"
        )
    return spec.alice_sectors


def _declared_povm_blocks(
    spec: SourceSpecification, sectors: SectorStructure
) -> dict[Label, tuple[Matrix, ...]] | None:
    """Return ``{M^{(t)}_x}`` as block lists, or ``None`` for a presentation.

    THE ONE-SECTOR CASE IS THE MATRIX CASE, said in the general shape:
    ``def:source-spec``, "With one sector the block list ``M_x`` is the matrix
    ``M_x``", so a declaration carrying matrices at one sector is turned into
    the singleton block list and every condition below is the condition it was.
    """
    if spec.ensemble_presentation is not None:
        if spec.alice_povm is not None or spec.alice_povm_blocks is not None:
            raise MalformedInputError(
                "an ensemble presentation declares no POVM: {M_x} is defined by "
                "eq:enspres and the POVM condition is a THEOREM "
                "(lem:ensemble-presentation (i)), so a declared family here "
                "would be a second carrier of it -- and the defined one carries "
                "square roots and quotients and is formed by no one"
            )
        return None
    if spec.alice_povm_blocks is not None:
        for label, blocks in spec.alice_povm_blocks.items():
            if len(blocks) != sectors.count:
                raise MalformedInputError(
                    f"the block list of M_{label!r} carries {len(blocks)} "
                    f"blocks against {sectors.count} declared sectors"
                )
        return dict(spec.alice_povm_blocks)
    if spec.alice_povm is None:
        raise MalformedInputError(
            "a specification that is not an ensemble presentation declares "
            "Alice's family, as matrices or as block lists (def:source-spec)"
        )
    if sectors.count != 1:
        raise MalformedInputError(
            "Alice's family is declared as MATRICES only at the one-sector "
            "structure, where 'the block list M_x is the matrix M_x'; this "
            f"specification declares {sectors.count} sectors and must present "
            "the family as block lists against them"
        )
    return {label: (element,) for label, element in spec.alice_povm.items()}


def _dense_povm(
    order: Sequence[Label],
    sectors: SectorStructure,
    povm_blocks: Mapping[Label, tuple[Matrix, ...]],
) -> dict[Label, Matrix]:
    """Return ``M_x = (+)_t M^{(t)}_x``, which IS WHAT THE BLOCK LIST MEANS.

    Not a second declaration and not a condition:
    :meth:`certiqs_key.foundations.blocks.BlockOperator.dense` says the direct sum
    "is what the list MEANS, not a condition on it", so nothing is decided here
    that was not already decided per block. At one sector the direct sum of a
    single block IS that block, entry for entry, which is what keeps the emitted
    ``alice_povm`` of every existing declaration the matrix it was.
    """
    if sectors.count == 1:
        return {label: povm_blocks[label][0] for label in order}
    return {label: direct_sum(list(povm_blocks[label])) for label in order}


def _decide_povm(
    order: Sequence[Label],
    sectors: SectorStructure,
    povm_blocks: Mapping[Label, tuple[Matrix, ...]],
) -> TransmitterResult | None:
    """Decide the POVM condition PER BLOCK, exactly, or return ``None``.

    ``def:source-spec``: "each block Hermitian and positive semidefinite, and
    ``sum_x M^{(t)}_x = 1_{A_t}`` FOR EVERY ``t`` WITH THE SUM TAKEN IN THE
    DECLARED ORDER OF ``X``". AT ONE SECTOR THE DETAIL STRINGS ARE THE STRINGS
    THEY WERE, which is what keeps a frozen refusal where it is; above one
    sector each names the sector, which is the only way the report is useful.
    """
    one_sector = sectors.count == 1

    def at(sector: Label) -> str:
        return "" if one_sector else f" at sector {sector!r}"

    for label in order:
        if label not in povm_blocks:
            return _refuse(
                RefusalReason.ALICE_POVM_ELEMENT_NOT_ADMISSIBLE,
                f"no declared M_x at {label!r}",
            )
        for position, dim in enumerate(sectors.dims):
            sector = sectors.labels[position]
            element = povm_blocks[label][position]
            if dimension(element) != dim:
                where = (
                    f" (d_A = {dim})" if one_sector else f"_t at sector {sector!r}"
                )
                return _refuse(
                    RefusalReason.ALICE_POVM_ELEMENT_NOT_ADMISSIBLE,
                    f"M_{label!r} is not an operator on A{where}",
                )
            if not is_hermitian(element) or not is_positive_semidefinite(element):
                return _refuse(
                    RefusalReason.ALICE_POVM_ELEMENT_NOT_ADMISSIBLE,
                    f"M_{label!r} is not Hermitian and positive "
                    f"semidefinite{at(sector)}",
                )
    for position, dim in enumerate(sectors.dims):
        sector = sectors.labels[position]
        povm_sum = sum_in_declared_order(
            [povm_blocks[label][position] for label in order]
        )
        if not povm_sum.computed_total_equals(identity(dim)):
            return _refuse(
                RefusalReason.ALICE_POVM_NOT_COMPLETE,
                "sum_x M_x is not 1_A as an identity of the declared "
                f"numbers{at(sector)}",
            )
        if not povm_sum.rounds_nowhere:
            return _refuse(
                RefusalReason.ALICE_POVM_SUMMATION_ROUNDS,
                "the completeness sum, accumulated in the declared order of X, "
                f"first rounds at element {povm_sum.first_inexact_index}"
                f"{at(sector)}",
            )
    return None


def _decide_block_certificate(
    order: Sequence[Label],
    sectors: SectorStructure,
    block: BlockFormCertificate,
    povm_blocks: Mapping[Label, tuple[Matrix, ...]],
    spec: SourceSpecification,
    specified_states: Mapping[Label, Matrix],
) -> TransmitterResult | None:
    """Decide a block-form certificate, the virtual ensemble's conditions FIRST.

    THE ORDER IS THE CLAIMS' AND NOT THIS FILE'S in one respect, and it is the
    same respect as in the pure form: "The virtual ensemble's own conditions are
    decided BEFORE the five conditions on the certificate and are not among
    them" (the ``ensemble_state_not_admissible`` row). In block form the virtual
    ensemble is declared by its weighted members block by block, so its own
    conditions are: the weights a distribution, and every block positive
    semidefinite with the block traces summing to ``p_x``.

    THEN THE DECLARED MEMBERS AGAINST THE BLOCK LISTS (``def:srcert``, block
    form; :func:`_block_members_diverge`): every weighted virtual member
    ``sigma^v_x`` block diagonal along the matched sectors, decided entry by
    entry on its declared entries, and its diagonal blocks the declared block
    list. Then Eq. ``eq:srblock`` block by block; the block diagonality and
    ``eq:srblock`` together are (SR1) and (SR2) of ``Psi``.
    """
    if block.alice_sectors.disagreement(sectors) is not None:
        raise MalformedInputError(
            "the block-form certificate is written against a different sector "
            f"structure from the declared one: {list(block.alice_sectors.labels)} "
            f"against {list(sectors.labels)}"
        )
    bad_weights = _weights_are_normalized(order, block.virtual_weights)
    if bad_weights is not None:
        return _refuse(
            RefusalReason.ENSEMBLE_WEIGHTS_NOT_NORMALIZED,
            f"the VIRTUAL ensemble: {bad_weights}",
        )
    for label in order:
        if label not in block.virtual_blocks:
            return _refuse(
                RefusalReason.ENSEMBLE_STATE_NOT_ADMISSIBLE,
                f"the VIRTUAL ensemble: no declared block list at {label!r}",
            )
        total = Cx(Fraction(0), Fraction(0))
        # The list's length and every block's dimension are the type's
        # (BlockFormCertificate.__post_init__).
        for position, member in enumerate(block.virtual_blocks[label]):
            sector = block.virtual_sectors.labels[position]
            if not is_hermitian(member) or not is_positive_semidefinite(member):
                return _refuse(
                    RefusalReason.ENSEMBLE_STATE_NOT_ADMISSIBLE,
                    f"the VIRTUAL ensemble: the weighted member of {label!r} at "
                    f"sector {sector!r} is not positive semidefinite",
                )
            total = total + trace_in_row_order(member).value
        if total != Cx(block.virtual_weights[label], Fraction(0)):
            return _refuse(
                RefusalReason.ENSEMBLE_STATE_NOT_ADMISSIBLE,
                f"the VIRTUAL ensemble: the block traces of {label!r} sum to "
                f"{total} and not to the declared p_x = "
                f"{block.virtual_weights[label]}",
            )
    off_block = _block_members_diverge(spec, block, specified_states)
    if off_block is not None:
        return _refuse(RefusalReason.CERTIFICATE_BLOCK_NOT_ADMISSIBLE, off_block)
    verification = verify_block_certificate(block, order, povm_blocks)
    refusal = verification.refusal()
    if refusal is not None:
        return TransmitterResult(artifact=None, refusal=refusal)
    return None


def _block_members_diverge(
    spec: SourceSpecification,
    block: BlockFormCertificate,
    specified_states: Mapping[Label, Matrix],
) -> str | None:
    """Decide the declared ``sigma^v_x`` against the block form's block lists.

    ``def:srcert``, block form: "The weighted virtual members are required to
    be BLOCK DIAGONAL along ``(S_t)_t``: ``Pi^v_t sigma^v_x Pi^v_t' = 0`` for
    all ``t != t'`` and every ``x`` ... decided entry by entry on the declared
    entries of ``sigma^v_x``", and ``eq:srblock`` with that block diagonality
    is (SR1) and (SR2) of ``Psi``; without it, ``eq:srblock`` is (SR2) only
    against the pinched members. At ``L_s = 0`` the virtual ensemble IS the
    specified one ("One reading at every ``L_s``"), so the declared entries of
    ``sigma^v_x`` are those of ``p_x rho_x``, formed exactly from the specified
    matrices.

    TWO OUTCOMES, AS IN THE PURE FORM. A non-zero entry whose row lies in one
    sector and whose column in another fails a condition the block form
    decides, and is RETURNED as the detail of
    ``certificate_block_not_admissible`` naming the letter and the pair of
    sectors (``req:failing-certificate``). A diagonal block that differs from
    the declared block list, or a virtual system or weight that differs from
    the specified one, is the divergence of two carriers of one datum that
    :func:`_virtual_pair_diverges` handles for the pure form, and RAISES
    :class:`~certiqs_key.foundations.errors.MalformedInputError` for the same
    reason: such a presentation is not of an input this module types.
    """
    if block.virtual_dim != spec.transmitted_dim:
        raise MalformedInputError(
            "at L_s = 0 the virtual transmitted system IS the specified one "
            "(def:srcert, 'One reading at every L_s': A^v = A'), but the "
            f"block-form certificate's sectors have total dimension "
            f"{block.virtual_dim} against a transmitted system of dimension "
            f"{spec.transmitted_dim}"
        )
    if set(block.virtual_weights) != set(spec.signal_weights):
        raise MalformedInputError(
            "at L_s = 0 the virtual ensemble IS the specified ensemble, but "
            "the block-form certificate and the specification are indexed by "
            "different signal alphabets"
        )
    labels = block.virtual_sectors.labels
    dims = block.virtual_sectors.dims
    offsets = [sum(dims[:position]) for position in range(len(dims))]
    sector_of = [
        position for position, dim in enumerate(dims) for _ in range(dim)
    ]
    for label in spec.signal_alphabet:
        weight = spec.signal_weights[label]
        if block.virtual_weights[label] != weight:
            raise MalformedInputError(
                "at L_s = 0 the virtual ensemble IS the specified ensemble "
                f"(the weights p_x shared), but p_{label!r} is "
                f"{block.virtual_weights[label]} in the block-form certificate "
                f"and {weight} in the specification"
            )
        state = specified_states[label]
        for row in range(spec.transmitted_dim):
            for column in range(spec.transmitted_dim):
                if sector_of[row] == sector_of[column]:
                    continue
                if weight != 0 and not state[row][column].is_zero:
                    return (
                        f"the weighted virtual member sigma^v_{label!r} = p_x "
                        "rho_x carries a non-zero entry outside the diagonal "
                        f"blocks, between the sectors {labels[sector_of[row]]!r} "
                        f"and {labels[sector_of[column]]!r}; the block form "
                        "requires every sigma^v_x block diagonal along the "
                        "matched sectors, without which eq:srblock is (SR2) "
                        "against the pinched members only (def:srcert)"
                    )
        for position, member in enumerate(block.virtual_blocks[label]):
            start = offsets[position]
            stop = start + dims[position]
            diagonal = tuple(
                tuple(
                    Cx(weight * entry.re, weight * entry.im)
                    for entry in state[row][start:stop]
                )
                for row in range(start, stop)
            )
            if not equal(diagonal, member):
                raise MalformedInputError(
                    "at L_s = 0 the virtual ensemble IS the specified ensemble, "
                    f"but the declared block of sigma^v_{label!r} at sector "
                    f"{labels[position]!r} differs from the diagonal block of "
                    "p_x rho_x there. A certificate internally consistent "
                    "against a DIFFERENT pair would otherwise emit a trusted "
                    "artefact describing a source other than the specified one"
                )
    return None


def _emit_from_presentation(
    spec: SourceSpecification,
    order: tuple[Label, ...],
    presentation: EnsemblePresentation,
) -> TransmitterResult:
    """Emit an artefact from an ENSEMBLE PRESENTATION, deciding (E1) to (E3) only.

    ``thm:certificate-sufficiency`` (i): the decided conditions of this form are (E1) to
    (E3) "and the conditions of the block form hold of the defined certificate by
    Lemma lem:ensemble-presentation (i) WITHOUT BEING DECIDED". So nothing below
    re-decides (SR1), (SR2), the POVM condition, positivity of ``Psi_t`` or
    purity, and ``Psi_t`` and ``M^{(t)}_x`` are never formed.

    THE EMITTED ARTEFACT CARRIES ``{N_x}`` AND NOT ``{M_x}``, AND THAT IS
    FAIL-CLOSED: a consumer whose declaration carries Alice's POVM "cannot
    receive an ensemble presentation and refuses it" (``def:srcert``).
    ``alice_povm`` is emitted EMPTY rather than filled with something formed,
    which is what makes a consumer that needs ``{M_x}`` refuse instead of
    compiling a family nobody declared.
    """
    if spec.source_mode_request is not SourceMode.TRUSTED:
        raise MalformedInputError(
            "an ensemble presentation is a form of the source-replacement "
            "certificate and is therefore TRUSTED MODE ONLY (def:source-spec, "
            "the trusted-mode paragraph); an untrusted request carrying one is "
            "not a presentation of an input this module types"
        )
    if spec.alice_marginal is not None:
        raise MalformedInputError(
            "an ensemble presentation declares no tau_A: it is the TRANSPOSE OF "
            "THE SUM of (E3) and is formed, not declared (def:srcert; "
            "lem:ensemble-presentation (iii)). A declared marginal beside it is "
            "a second carrier of one datum"
        )
    verification = verify_ensemble_presentation(
        presentation, order, spec.signal_weights
    )
    refusal = verification.refusal()
    if refusal is not None:
        return TransmitterResult(artifact=None, refusal=refusal)

    sectors = presentation.alice_sectors
    marginal = direct_sum(list(alice_marginal_blocks(presentation, order)))
    operators = alice_operators(presentation)
    alice_dim = presentation.alice_dim
    licence = (
        SourceReplacementLicense.pass_through_presentation(
            presentation, presentation.retention_attestation
        )
        if alice_dim >= 2
        else None
    )
    # An ensemble presentation is a trusted-source specification (its marginal
    # is the presentation's own), so A-ENS is emitted (R2: trusted mode only).
    ledger = [
        ASSUMPTION_MACHINE_KEYS[AssumptionId.A_ENS],
        ASSUMPTION_MACHINE_KEYS[AssumptionId.A_SEQ],
    ]
    if licence is not None:
        ledger.append(ASSUMPTION_MACHINE_KEYS[AssumptionId.A_SRC])
    return TransmitterResult(
        artifact=TransmitterArtifact(
            signal_alphabet=order,
            alice_dim=alice_dim,
            alice_marginal=marginal,
            alice_povm={},
            virtual_transmitted_system=presentation.virtual_sectors.total_dim,
            virtual_ensemble_weights=dict(spec.signal_weights),
            virtual_ensemble_states={},
            virtual_ensemble_blocks={
                label: tuple(presentation.weighted_blocks[label]) for label in order
            },
            source_segment=(),
            source_replacement_license=licence,
            marginal_slot_filled=False,
            assumption_ledger=tuple(ledger),
            certificate_form=CertificateForm.ENSEMBLE_PRESENTATION,
            alice_sector_map=sectors,
            virtual_sector_map=presentation.virtual_sectors,
            alice_ensemble_operators=operators,
        ),
        refusal=None,
    )
