"""The emitted decoy declaration: the tagged ensemble itself, and nothing else.

spec/modules/transmitter/decoy/: Corollary ``cor:emitted-decoy``, with
Proposition ``prop:decoy-cert`` for the blocks ``eq:decoy-blocks`` and
Proposition ``prop:tagging`` for the source identity the link's obligation names.

WHAT IS DECLARED, IN THE COROLLARY'S OWN LIST: the alphabet with its order and
the weights ``p_x``; the matched sector structure -- the sectors some letter puts
positive weight on, each with its declared orthonormal basis; the weighted blocks
``sigma^{v,(t)}_x = p_x w_{x,t} |phi_{x,t}><phi_{x,t}|``; and the specified
ensemble as the source model, the segment with its one tagging link and its
obligation record, and the assumption ledger. Requirement
``decoy/req:decoy-emission``: the artefact is that declaration "AND NOTHING
ELSE: the engine declares no retained system, no measurement, no marginal and no
certificate, and it ROUNDS OR OTHERWISE ALTERS NO DECLARED NUMBER."

WHAT IS FORMED BEFORE ANY BLOCK. The lower end of the enclosure of each
Poisson weight, from the declared intensity at the index ``K_mu``
(``req:sector-weight-bound``, :mod:`certiqs_key.transmitter.decoy.enclosure`),
which (T2) is decided against; and the entries of the signal dyads, by the
construction of ``cor:emitted-decoy`` (iv)(b) (``req:signal-dyads``). Neither
is read from a request.

WHAT IS DECIDED ON A PARTICULAR DECLARATION (the corollary's part (iv)) -- and
this list is all of it: (E1) to (E3) on the declared blocks, by the core's
:func:`~certiqs_key.transmitter.presentation.verify_ensemble_presentation`
(``decoy/req:decoy-ensemble-conditions`` for (E1) and (E2),
``decoy/req:exact-decoy-blocks`` for (E3)), and whether every FORMED entry of a
block is a binary64 number. Requirement ``decoy/req:exact-decoy-blocks`` fixes
the second: an entry that is not one IS REFUSED (``formed_entry_not_declarable``)
and IS NEVER ROUNDED, because rounding an entry of a declared block would change
which ensemble is declared and so which ensemble the source identity of (ii) is
asserted of.

WHY THERE IS NO ROUNDING HELPER HERE, AND WHOSE SIDE IT WOULD BE ON. A declarer
whose product ``p_x ptilde(n|mu)`` is not representable "removes the refusal by
declaring on a coarser dyadic grid" (``decoy/req:exact-decoy-blocks``), and
"choosing the ``p_x`` and the ``ptilde`` with few enough significant bits makes
every product exact, and LOWERING a ``ptilde`` is permitted by
``eq:weightineq`` and yields again a tagged source declaration by (v)"
(``cor:emitted-decoy`` (iv)(a)). That is a declarer's act on data it is about
to declare: neither
interface names such a helper among this submodule's inputs or outputs, the
submodule's ``rounding`` convention says rounding happens "DOWN, for a sector
weight, and nowhere else" as a property of a DIFFERENT declaration rather than as
an operation this module performs, and building one here would put the choice of
grid inside the module that decides the result. It belongs to the instance.

THE CONSUMER PATH. C4 admits the tagging link through
``DecoySourceDeclaration.as_transmitter_artifact`` after revalidating the
declaration and presentation. The raw ``as_source_specification`` view is
data, not an admission token: the core refuses that path under A3. The
compiler consumes the ensemble form directly, with no reconstructed POVM.
"""

from __future__ import annotations

import numbers
from collections.abc import Mapping
from dataclasses import dataclass, fields
from fractions import Fraction
from typing import Any, ClassVar, Final, cast

from certiqs_key.domain.bindings import (
    Bindings,
    LedgerBindings,
    exact,
    ledger_bindings_record,
)
from certiqs_key.domain.families import AliceForm
from certiqs_key.foundations.blocks import Label, SectorStructure
from certiqs_key.foundations.errors import MalformedInputError
from certiqs_key.foundations.exact import (
    Cx,
    Matrix,
    dimension,
    equal,
    is_hermitian,
    matmul,
    matrix_is_binary64,
    scale,
    trace_in_row_order,
)
from certiqs_key.transmitter.artifact import (
    SourceSpecification,
    TransmitterArtifact,
    _emit_from_presentation,
    source_replacement_bindings,
)
from certiqs_key.transmitter.decoy.bases import exhibited_overlap
from certiqs_key.transmitter.decoy.enclosure import poisson_enclosures, poisson_index
from certiqs_key.transmitter.decoy.reasons import (
    DECOY_ASSUMPTION_MACHINE_KEYS,
    DecoyAssumptionId,
    DecoyRefusal,
    DecoyRefusalReason,
    FlagFamily,
)
from certiqs_key.transmitter.decoy.tagged import (
    SectorKind,
    TaggedSourceDeclaration,
)
from certiqs_key.transmitter.links import (
    AliceSideDescriptor,
    ObligationRecord,
    SourceLink,
    SourceLinkKind,
    SourceLinkStatus,
    check_source_link,
)
from certiqs_key.transmitter.presentation import EnsemblePresentation
from certiqs_key.transmitter.presentation import (
    verify_ensemble_presentation as _verify_presentation,
)
from certiqs_key.transmitter.reasons import (
    ASSUMPTION_MACHINE_KEYS,
    AssumptionId,
    CertificateForm,
    RefusalReason,
    SourceMode,
)

__all__ = [
    "DECOY_ASSUMPTION_LEDGER",
    "MATHEMATICAL_SPEC_VERSION",
    "TAGGING_OBLIGATION",
    "DecoyResult",
    "DecoySourceDeclaration",
    "artifact_admits_source_segment",
    "emit_decoy_declaration",
    "wcp_bindings",
]

#: ``tr |phi><phi| = 1`` as the exact scalar the dyad's trace is compared with.
_ONE: Final[Cx] = Cx(Fraction(1), Fraction(0))

#: ``transmitter/decoy@<version>`` of the ACCEPTED contract: an accepted
#: ``version`` of spec/modules/transmitter/decoy/module.yaml.
MATHEMATICAL_SPEC_VERSION: Final[str] = "transmitter/decoy@0.8.0"


@dataclass(frozen=True)
class _DecoyTransmitterArtifact(TransmitterArtifact):
    """Private carrier proving construction through the decoy emitter path."""

    admitting_module_version: ClassVar[str] = MATHEMATICAL_SPEC_VERSION


def artifact_admits_source_segment(artifact: TransmitterArtifact) -> bool:
    """Decide whether this is the decoy-owned carrier for its tagging segment."""
    if type(artifact) is not _DecoyTransmitterArtifact:
        return False
    return (
        bool(artifact.source_segment)
        and all(
            isinstance(link, SourceLink) and link.kind is SourceLinkKind.TAGGING
            for link in artifact.source_segment
        )
        and artifact.certificate_form is CertificateForm.ENSEMBLE_PRESENTATION
        and artifact.alice_ensemble_operators is not None
        and artifact.admitting_module_version == MATHEMATICAL_SPEC_VERSION
    )

#: The obligation record of the one link this submodule emits: the TRIPLE
#: ``(tagging, transmitter/decoy/prop:tagging, [A-WCP])`` of
#: ``cor:emitted-decoy`` (ii), which is this submodule's entry in the core's
#: closed ``soundness_registry`` and is what a consumer decides the link against.
#:
#: WHERE EACH HALF OF THE THIRD COMPONENT COMES FROM. "the assumption closure of
#: Proposition prop:tagging -- what ``python -m harness.check_claims
#: --assumptions transmitter/decoy/prop:tagging`` computes -- IS EMPTY, that
#: proposition being an identity among the states of def:wcp-model and assuming
#: no attestation; and A-WCP is carried for the other reason
#: def:source-segment (A1) gives, as the physical-source assumption this
#: submodule declares for the model that proposition is stated over. A-WCP IS NO
#: PREMISE OF prop:tagging AND IS NOT MADE ONE."
#:
#: THE FAMILY MEMBER IS THE IDENTITY OF THE THING WITH ITSELF: the emitted
#: descriptor IS a tagged source declaration, and the declared family of that
#: proposition is "every tagged source declaration over every
#: weak-coherent-pulse model". It is asserted here and decided by no one.
TAGGING_OBLIGATION: Final[ObligationRecord] = ObligationRecord(
    kind=SourceLinkKind.TAGGING,
    soundness_claim="transmitter/decoy/prop:tagging",
    assumptions=("A-WCP",),
    family_member=(
        "the emitted tagged source declaration itself (def:tagged-source (T6): "
        "the declared family is every tagged source declaration over every "
        "weak-coherent-pulse model)"
    ),
)

#: The d_A >= 2 trusted decoy ledger. A-WCP replaces A-ENS, A-SEQ is
#: unconditional, and the emitter removes A-SRC at d_A=1.
DECOY_ASSUMPTION_LEDGER: Final[tuple[str, ...]] = (
    DECOY_ASSUMPTION_MACHINE_KEYS[DecoyAssumptionId.A_WCP],
    ASSUMPTION_MACHINE_KEYS[AssumptionId.A_SEQ],
    ASSUMPTION_MACHINE_KEYS[AssumptionId.A_SRC],
)


def wcp_bindings(declaration: TaggedSourceDeclaration) -> Bindings:
    """Return the declared values A-WCP (``ass:wcp``) binds.

    The premise fixes the tagged source declaration "with the cutoffs, the
    weights and the polarisations it declares", and the clauses are about the
    source against the model's declared data: ``signal_alphabet`` -- each
    letter ``x = (a, mu, z)`` with its polarisation, intensity and round
    type, the letter of (i) and the round type of (vi); ``signal_weights`` --
    the ``p_x`` of (vii); ``intensities`` -- each ``mu`` by name and declared
    value, "exactly", (ii); ``polarisations`` -- the declared ``|a>`` of
    (iv); and ``entropy_cutoff`` and ``source_cutoff`` -- ``N_ent`` and
    ``N_src`` of ``def:tagged-source`` (T1), the cutoffs the premise names.
    No clause truncates the state of (i) at a cutoff (it is the full phase
    average of ``def:wcp-model``); the cutoffs are bound because the premise
    fixes the declaration by them.
    """
    model = declaration.model
    return (
        (
            "signal_alphabet",
            tuple(
                (
                    letter.label,
                    (
                        ("polarisation", letter.polarisation),
                        ("intensity", letter.intensity),
                        ("round_type", str(letter.round_type)),
                    ),
                )
                for letter in model.alphabet
            ),
        ),
        (
            "signal_weights",
            tuple(
                (letter.label, exact(model.weights[letter.label]))
                for letter in model.alphabet
            ),
        ),
        (
            "intensities",
            tuple((name, exact(value)) for name, value in model.intensities.items()),
        ),
        ("polarisations", tuple(model.polarisations)),
        ("entropy_cutoff", declaration.entropy_cutoff),
        ("source_cutoff", declaration.source_cutoff),
    )


@dataclass(frozen=True)
class DecoySourceDeclaration:
    """What ``cor:emitted-decoy`` declares, and it declares nothing else.

    EVERY FIELD IS AN ITEM OF THE COROLLARY'S LIST. There is no certificate
    field, no marginal field, no POVM field and no compression record: "NOTHING
    OF THE KIND IS EMITTED, because nothing is compressed and nothing is
    snapped" (the interface's ``not_outputs`` item "a support-compression
    record").
    """

    declaration: TaggedSourceDeclaration
    #: The ensemble presentation the core decides (E1) to (E3) of: the matched
    #: sector structure and the weighted blocks, and nothing else.
    presentation: EnsemblePresentation
    #: ``({Pi^A_t}, {Pi^v_t})`` in the declared order of ``T``, block kind
    #: ``proof_sector``: ONE STRUCTURE READ ON BOTH SIDES, ``A_t`` a copy of
    #: ``S_t`` (T5).
    alice_sector_map: tuple[SectorStructure, SectorStructure]
    #: ``Ch_src = (Xi_tag)``: EXACTLY ONE LINK, of kind ``tagging``, its witness
    #: a theorem constructor, its entry list empty, no licence record, status
    #: ``exact``, with :data:`TAGGING_OBLIGATION`.
    source_segment: tuple[SourceLink, ...]
    #: The ledger of the artefact this declaration would produce once the
    #: segment opens; see :data:`DECOY_ASSUMPTION_LEDGER` on why it is not in
    #: force today.
    assumption_ledger: tuple[str, ...] = DECOY_ASSUMPTION_LEDGER
    mathematical_spec_version: str = MATHEMATICAL_SPEC_VERSION

    def __post_init__(self) -> None:
        """Refuse an EMITTED record whose dyads the emission would have refused.

        THIS IS ON THE RECORD THAT CARRIES THE OBLIGATION. A caller could build
        this record by hand around a declaration whose quantum sector lies
        outside the construction of ``cor:emitted-decoy`` (iv)(b), or around a
        presentation whose blocks are not the declaration's, which the
        emission refuses or never forms and which a hand-built record would
        carry into a link asserting membership of ``prop:tagging``'s family.
        Both are re-decided here: the construction and the exact guard of
        ``req:signal-dyads`` on the formed dyads, and then EVERY BLOCK THIS
        RECORD CARRIES against ``eq:decoy-blocks``
        (:func:`_decide_presented_blocks`). The conditions RAISE rather than
        return a refusal, because a refusal is what the emission returns
        instead of a record and a record that exists has passed it.
        """
        refusal, formed = _formed_signal_dyads(self.declaration)
        if refusal is None:
            _decide_presented_blocks(self.declaration, self.presentation, formed)
        if refusal is not None:
            raise MalformedInputError(
                "this emitted decoy declaration carries a signal dyad the "
                f"emission refuses: {refusal.detail}. cor:emitted-decoy's "
                "declaration is what emit_decoy_declaration returns, and a "
                "record built around data that emission would refuse would "
                "carry an obligation asserting membership of prop:tagging's "
                "family for an ensemble it does not describe"
            )
        ledger = DECOY_ASSUMPTION_LEDGER
        if self.presentation.alice_dim == 1:
            ledger = tuple(
                key for key in ledger
                if key != ASSUMPTION_MACHINE_KEYS[AssumptionId.A_SRC]
            )
        object.__setattr__(self, "assumption_ledger", ledger)

    @property
    def poisson_indices(self) -> dict[Label, int]:
        """Return ``K_mu`` per intensity, in the declared order of ``Int``.

        ``req:sector-weight-bound``: the summation index of the enclosure each
        intensity's weights were decided against, which the artefact records.
        """
        return {
            name: poisson_index(value)
            for name, value in self.declaration.model.intensities.items()
        }

    @property
    def assumption_bindings(self) -> LedgerBindings:
        """Return the declared values each ledger row binds, one entry per row.

        A-WCP: :func:`wcp_bindings`. A-SEQ: nothing, as in the core. A-SRC,
        where the ledger carries it: the core's
        :func:`~certiqs_key.transmitter.artifact.source_replacement_bindings`
        of this trusted-source declaration, Alice's measurement being the one
        the ensemble presentation defines (``form`` ``ensemble``). The artefact
        :meth:`as_transmitter_artifact` emits binds the same values, the
        A-WCP row through its ``source_model_bindings``.
        """
        presentation = self.presentation
        rows: dict[str, Bindings] = {
            DECOY_ASSUMPTION_MACHINE_KEYS[DecoyAssumptionId.A_WCP]: wcp_bindings(
                self.declaration
            ),
            ASSUMPTION_MACHINE_KEYS[AssumptionId.A_SEQ]: (),
            ASSUMPTION_MACHINE_KEYS[AssumptionId.A_SRC]: source_replacement_bindings(
                source_mode=SourceMode.TRUSTED,
                alphabet=self.declaration.model.signal_alphabet,
                alice_dim=presentation.alice_dim,
                sectors=presentation.alice_sectors,
                form=AliceForm.ENSEMBLE,
            ),
        }
        return tuple((key, rows.get(key, ())) for key in self.assumption_ledger)

    def as_transmitter_artifact(self) -> TransmitterArtifact:
        """Emit through the admitting module, rechecking the tagged declaration.

        A core SourceSpecification is not this provenance. Rebuilding from the
        underlying declaration checks all source-weight and dyad obligations;
        supplied record fields cannot substitute a different presentation/link.
        No normalized POVM or inverse is formed on the ensemble path.
        """
        checked = emit_decoy_declaration(self.declaration).require()
        for link in checked.source_segment:
            refusal = check_source_link(
                link,
                assumption_ledger=("A-WCP", "A-SEQ") + (
                    ("A-SRC",) if checked.presentation.alice_dim >= 2 else ()
                ),
                from_admitting_module=True,
            )
            if refusal is not None:
                raise MalformedInputError(refusal.detail)
        spec = checked.as_source_specification()
        emitted = _emit_from_presentation(
            spec, tuple(spec.signal_alphabet), checked.presentation
        ).require()
        values = {field.name: getattr(emitted, field.name) for field in fields(emitted)}
        values.update(
            source_segment=checked.source_segment,
            assumption_ledger=checked.assumption_ledger,
            source_model_bindings=(
                (
                    DECOY_ASSUMPTION_MACHINE_KEYS[DecoyAssumptionId.A_WCP],
                    wcp_bindings(checked.declaration),
                ),
            ),
        )
        admitted: TransmitterArtifact = cast(Any, _DecoyTransmitterArtifact)(
            **values
        )
        return admitted

    @property
    def link(self) -> SourceLink:
        """Return the one link of the segment (T6)."""
        return self.source_segment[0]

    def as_source_specification(self) -> SourceSpecification:
        """Return the raw source specification, without admitting provenance.

        The physical ensemble is model-declared, the segment is nonempty,
        and the certificate is an ensemble presentation. This view describes
        the data of ``cor:emitted-decoy``; passing it to the core emitter
        yields ``source_segment_not_from_admitting_module``. Use
        :meth:`as_transmitter_artifact` for the admitted supplier path.
        """
        return SourceSpecification(
            signal_alphabet=self.declaration.model.signal_alphabet,
            transmitted_dim=self.presentation.virtual_sectors.total_dim,
            signal_weights=dict(self.declaration.model.weights),
            signal_states=None,
            source_mode_request=SourceMode.TRUSTED,
            ensemble_presentation=self.presentation,
            source_segment=self.source_segment,
        )

    def as_machine_record(self) -> dict[str, object]:
        """Return the declaration as a machine record, under the interface's keys."""
        return {
            "signal_alphabet": list(self.declaration.model.signal_alphabet),
            "weights": dict(self.declaration.model.weights),
            # int(): a numpy integer cutoff is admitted (numbers.Integral) and
            # the record carries the same integer as a plain int.
            "entropy_cutoff": int(self.declaration.entropy_cutoff),
            "source_cutoff": int(self.declaration.source_cutoff),
            # The weight table, per intensity, with the summation index K_mu of
            # the enclosure its weights were decided against
            # (req:sector-weight-bound).
            "sector_weights": {
                name: {
                    "poisson_index": index,
                    "weights": [
                        self.declaration.sector_weights[(photon_number, name)]
                        for photon_number in range(
                            int(self.declaration.source_cutoff) + 1
                        )
                    ],
                }
                for name, index in self.poisson_indices.items()
            },
            "source_specification": self.presentation.as_machine_record(),
            "virtual_ensemble": {
                label: list(blocks)
                for label, blocks in self.presentation.weighted_blocks.items()
            },
            "alice_sector_map": {
                "sector_index_set": list(self.alice_sector_map[0].labels),
                "sector_dims": list(self.alice_sector_map[0].dims),
                "sector_block_kind": str(self.alice_sector_map[0].block_kind),
            },
            "source_segment": [
                {
                    "kind": str(self.link.kind),
                    "status": str(self.link.status),
                    "witness": str(self.link.witness_kind),
                    "constraint_entries": list(self.link.constraint_entries),
                    "licence": self.link.licence,
                }
            ],
            "link_obligation_record": TAGGING_OBLIGATION.as_machine_record(),
            "assumption_ledger": list(self.assumption_ledger),
            "assumption_bindings": ledger_bindings_record(self.assumption_bindings),
            "mathematical_spec_version": self.mathematical_spec_version,
        }


@dataclass(frozen=True)
class DecoyResult:
    """A declaration or a refusal. NEVER BOTH AND NEVER NEITHER.

    The submodule's ``fail_closed`` convention: "Every condition that fails is a
    REFUSAL with a machine-readable reason and no artefact. Nothing is repaired,
    nothing is snapped to make a condition pass, and NO DATUM IS FILLED."
    """

    declaration: DecoySourceDeclaration | None
    refusal: DecoyRefusal | None

    def __post_init__(self) -> None:
        """Refuse a result that both declares and refuses, or does neither."""
        if (self.declaration is None) == (self.refusal is None):
            raise MalformedInputError(
                "a decoy result carries a declaration or a refusal and never "
                "both and never neither (the fail_closed convention)"
            )

    def require(self) -> DecoySourceDeclaration:
        """Return the declaration, for a caller that has already handled refusal."""
        if self.declaration is None:
            raise MalformedInputError(
                "this tagged declaration was refused; there is nothing to take"
            )
        return self.declaration


def _is_integer_cutoff(value: object) -> bool:
    """Whether ``value`` is an integer cutoff of (T1): Integral, not a ``bool``."""
    return isinstance(value, numbers.Integral) and not isinstance(value, bool)


def emit_decoy_declaration(declaration: TaggedSourceDeclaration) -> DecoyResult:
    """Emit ``cor:emitted-decoy``'s declaration, or refuse naming a condition.

    THE ORDER OF THE REFUSALS IS THIS FILE'S and no claim fixes it; the
    requirements ``decoy/req:*`` list them and fix no ordering. What the claims
    do fix is that each is the negation of a stated condition, and that the
    arithmetic is decided on the formed blocks rather than repaired: the cutoffs
    (T1), the scope refusal at ``N_ent >= 3``, the flag family (T3), the weight
    obligation ``eq:weightineq`` and its inequality reading, the tail weight,
    the construction of the signal dyads, the formed entries, and (E1) to (E3).

    THE REQUIREMENTS IT IMPLEMENTS, by name: ``req:cutoff-order``,
    ``req:entropy-cutoff``, ``req:shared-flags``, ``req:sector-weight-bound``
    (the enclosure formed from the declared intensity at ``K_mu``, read from no
    request), ``req:signal-dyads`` (the dyads formed by the construction of
    ``cor:emitted-decoy`` (iv)(b), taken from no request),
    ``req:exact-decoy-blocks``, ``req:decoy-ensemble-conditions`` and
    ``req:decoy-emission``.
    """
    model = declaration.model
    # (T1) carries the integrality as well as the order, and
    # decoy/req:cutoff-order makes cutoffs_out_of_order the one refusal for
    # both. A cutoff is an integer when it is a numbers.Integral (a Python
    # int, a numpy integer); a bool is not one (it is Integral by accident of
    # the language), and neither is an integer-valued float or Fraction: a
    # value of another type is refused rather than converted.
    if (
        not _is_integer_cutoff(declaration.entropy_cutoff)
        or not _is_integer_cutoff(declaration.source_cutoff)
        or declaration.entropy_cutoff < 0
        or declaration.source_cutoff < declaration.entropy_cutoff
    ):
        return _refuse(
            DecoyRefusalReason.CUTOFFS_OUT_OF_ORDER,
            "the cutoffs are integers with 0 <= N_ent <= N_src, which is (T1); "
            f"this declaration carries N_ent = {declaration.entropy_cutoff!r} "
            f"and N_src = {declaration.source_cutoff!r}",
        )
    if declaration.entropy_cutoff >= 3:
        return _refuse(
            DecoyRefusalReason.ENTROPY_CUTOFF_ABOVE_TWO,
            f"N_ent = {declaration.entropy_cutoff} >= 3. A SCOPE REFUSAL WITH "
            "ITS OWN REASON, not a consequence of any claim: every claim of this "
            "submodule is stated for arbitrary N_ent, and what is missing is a "
            "construction of exactly admissible signal data on S_n at odd photon "
            "numbers from three -- the declared basis cor:emitted-decoy (iv)(b) "
            "exhibits at one and at two photons and does not exhibit above them",
        )
    if declaration.flag_family is not FlagFamily.SHARED:
        return _refuse(
            DecoyRefusalReason.FLAG_FAMILY_SPLIT_BY_INTENSITY,
            "the declaration requests the flag family "
            f"{declaration.flag_family.value!r}, which is finer than "
            "def:tagged-source (T3) declares: one polarisation flag per (n, a), "
            "SHARED by every intensity and both round types. Splitting gives up "
            "the relation that IS the decoy content of the declaration, and it "
            "would lose it silently if this emission did not refuse it "
            "(rem:no-intensity-split)",
        )
    if declaration.weight_obligation_presented_as_equality:
        return _refuse(
            DecoyRefusalReason.SECTOR_WEIGHT_AS_EQUALITY,
            "the declaration presents ptilde(n | mu) = P_mu(n) as a DECIDED "
            "EQUALITY, or asks for the Poisson weight to be represented "
            "exactly. The obligation of (T2) is an inequality and never an "
            "equality: its right-hand side is not a declared datum, and at a "
            "positive binary64 intensity it is a transcendental number (at "
            "mu = 0 it is 1 for n = 0 and 0 above), and no condition of this "
            "submodule compares the two for equality or reads one at a "
            "tolerance (req:sector-weight-bound)",
        )

    weight_refusal = _decide_weight_obligation(declaration)
    if weight_refusal is not None:
        return DecoyResult(declaration=None, refusal=weight_refusal)

    dyad_refusal, formed = _formed_signal_dyads(declaration)
    if dyad_refusal is not None:
        return DecoyResult(declaration=None, refusal=dyad_refusal)

    sectors = declaration.sector_index_set()
    if not sectors:
        raise MalformedInputError(
            "the declared index set eq:tset is empty: no letter puts positive "
            "weight on any sector, so there is no virtual transmitted system to "
            "declare. def:source-spec requires a non-empty alphabet and a "
            "sector of dimension at least one"
        )
    structure = declaration.sector_structure()

    blocks: dict[Label, tuple[Matrix, ...]] = {}
    for letter in model.alphabet:
        row: list[Matrix] = []
        for sector in sectors:
            weight = declaration.weight_in(sector, letter)
            # THE BLOCKS CARRY THE DYADS THE GUARD DECIDED: on a quantum sector
            # above the vacuum the matrix is the one _formed_signal_dyads
            # formed and checked, not a second copy.
            dyad = (
                formed[(sector.photon_number, letter.polarisation)]
                if sector.kind is SectorKind.QUANTUM and sector.photon_number
                else declaration.dyad_in(sector, letter)
            )
            if sector.kind is SectorKind.QUANTUM and len(dyad) != sector.dim:
                raise MalformedInputError(
                    f"the declared dyad at sector {sector.label!r} is not an "
                    f"operator on S_t of dimension {sector.dim}"
                )
            # eq:decoy-blocks, FORMED IN EXACT ARITHMETIC: the product
            # p_x * w_{x,t} * (a dyad entry). Every entry must be a binary64
            # number and is REFUSED, NEVER ROUNDED, when it is not.
            block = scale(model.weights[letter.label] * weight, dyad)
            if not matrix_is_binary64(block):
                return _refuse(
                    RefusalReason.FORMED_ENTRY_NOT_DECLARABLE,
                    f"the block of {letter.label!r} at sector "
                    f"{sector.label!r} carries an entry that is not a binary64 "
                    f"number: the product p_x * w_{{x,t}} is "
                    f"{model.weights[letter.label] * weight}. IT IS REFUSED AND "
                    "NEVER ROUNDED, because rounding an entry would change which "
                    "ensemble is declared and so which ensemble the source "
                    "identity is asserted of. A declarer removes the refusal by "
                    "declaring the p_x and the ptilde on a coarser dyadic grid, "
                    "lowering a ptilde being permitted by eq:weightineq and "
                    "giving again a tagged declaration (req:exact-decoy-blocks; "
                    "cor:emitted-decoy (iv), (v))",
                )
            row.append(block)
        blocks[letter.label] = tuple(row)

    presentation = EnsemblePresentation(
        virtual_sectors=structure,
        weighted_blocks=blocks,
        retention_attestation=declaration.retention_attestation,
    )
    verification = _verify_presentation(
        presentation, model.signal_alphabet, model.weights
    )
    presentation_refusal = verification.refusal()
    if presentation_refusal is not None:
        return DecoyResult(
            declaration=None,
            refusal=DecoyRefusal(
                reason=presentation_refusal.reason,
                detail=presentation_refusal.detail,
            ),
        )

    link = _tagging_link(declaration, presentation, model.weights)
    return DecoyResult(
        declaration=DecoySourceDeclaration(
            declaration=declaration,
            presentation=presentation,
            alice_sector_map=(structure, structure),
            source_segment=(link,),
        ),
        refusal=None,
    )


def _refuse(
    reason: DecoyRefusalReason | RefusalReason, detail: str
) -> DecoyResult:
    """Return a refusal with no declaration."""
    return DecoyResult(
        declaration=None, refusal=DecoyRefusal(reason=reason, detail=detail)
    )


def _formed_signal_dyads(
    declaration: TaggedSourceDeclaration,
) -> tuple[DecoyRefusal | None, dict[tuple[int, Label], Matrix]]:
    """Form the signal dyads of ``req:signal-dyads`` ONCE, and decide them.

    THE DYADS ARE FORMED, NOT READ. At a quantum sector ``n in {1, 2}`` of the
    index set the dyad ``|n,a><n,a|`` of every polarisation of ``Pol`` is
    formed by
    :meth:`~certiqs_key.transmitter.decoy.tagged.TaggedSourceDeclaration.signal_dyad`,
    the construction of ``cor:emitted-decoy`` (iv)(b), and only where that
    construction applies: every polarisation declared as one of the four
    vectors of ``D``, distinct polarisations as distinct vectors, and
    ``|Pol| >= n + 1``. A declaration whose index set carries a quantum sector
    outside it is refused with ``quantum_sector_outside_construction``.

    The formed matrices are returned with the verdict, and the emission builds
    its blocks from THESE: the exact guard (:func:`_dyad_guard`) decides the
    dyads that enter the blocks, not a second copy of them.
    """
    model = declaration.model
    formed: dict[tuple[int, Label], Matrix] = {}
    for photon_number in declaration.quantum_photon_numbers():
        if photon_number == 0:
            continue
        outside = declaration.outside_construction(photon_number)
        if outside is not None:
            return (
                DecoyRefusal(
                    reason=DecoyRefusalReason.QUANTUM_SECTOR_OUTSIDE_CONSTRUCTION,
                    detail=outside,
                ),
                {},
            )
        dyads = {
            polarisation: declaration.signal_dyad(photon_number, polarisation)
            for polarisation in model.polarisations
        }
        refusal = _dyad_guard(declaration, photon_number, dyads)
        if refusal is not None:
            return refusal, {}
        for polarisation, dyad in dyads.items():
            formed[(photon_number, polarisation)] = dyad
    return None, formed


def _dyad_guard(
    declaration: TaggedSourceDeclaration,
    photon_number: int,
    dyads: Mapping[Label, Matrix],
) -> DecoyRefusal | None:
    """Decide the exact guard of ``req:signal-dyads`` on the given dyads.

    Of each dyad, exactly: a rank-one projector on ``S_n`` -- dimension
    ``n + 1``, Hermitian, idempotent and of unit trace -- and of every pair
    ``tr[X_a X_b] = |<a|b>|^(2n)``, the value ``def:wcp-model`` (W3) gives;
    the right-hand side is formed from the one-photon overlaps of ``D``
    (:func:`~certiqs_key.transmitter.decoy.bases.exhibited_overlap`), not from
    the matrices it checks. A failure is ``quantum_sector_outside_construction``.
    """
    parts = declaration.model.polarisation_parts
    labels = [a for a in declaration.model.polarisations if a in dyads]
    for polarisation in labels:
        dyad = dyads[polarisation]
        if (
            dimension(dyad) != photon_number + 1
            or not is_hermitian(dyad)
            or not equal(matmul(dyad, dyad), dyad)
            or trace_in_row_order(dyad).value != _ONE
        ):
            return DecoyRefusal(
                reason=DecoyRefusalReason.QUANTUM_SECTOR_OUTSIDE_CONSTRUCTION,
                detail=(
                    f"the dyad formed at photon number {photon_number} for "
                    f"the polarisation {polarisation!r} is not a rank-one "
                    f"projector on S_n of dimension {photon_number + 1}: it "
                    "is not Hermitian, not idempotent or not of unit trace, "
                    "each decided exactly (req:signal-dyads)"
                ),
            )
    for first in range(len(labels)):
        for second in range(first, len(labels)):
            a, b = labels[first], labels[second]
            expected = exhibited_overlap(photon_number, parts[a], parts[b])
            computed = trace_in_row_order(matmul(dyads[a], dyads[b])).value
            if computed != Cx(expected, Fraction(0)):
                return DecoyRefusal(
                    reason=DecoyRefusalReason.QUANTUM_SECTOR_OUTSIDE_CONSTRUCTION,
                    detail=(
                        f"the dyads formed at photon number {photon_number} "
                        f"for the polarisations {a!r} and {b!r} carry "
                        f"tr[X_a X_b] = {computed}, and |<a|b>|^(2n) is "
                        f"{expected} (def:wcp-model (W3); req:signal-dyads)"
                    ),
                )
    return None


def _decide_presented_blocks(
    declaration: TaggedSourceDeclaration,
    presentation: EnsemblePresentation,
    formed: Mapping[tuple[int, Label], Matrix],
) -> None:
    """Decide that a presentation's blocks are exactly the declaration's.

    ``eq:decoy-blocks`` with the dyads of ``req:signal-dyads``: the
    presentation is written against the declaration's index set, its weighted
    blocks are indexed by exactly the alphabet's labels, one block per sector,
    and every block equals ``scale(p_x w_{x,t}, |phi_{x,t}><phi_{x,t}|)``
    exactly, with the formed dyad at a quantum sector ``n >= 1`` (``formed``,
    which passed the exact guard) and the number ``1`` on the vacuum and on
    every flag sector. A position of weight zero is therefore the zero block.
    Anything else is not the presentation of this declaration and raises
    :class:`~certiqs_key.foundations.errors.MalformedInputError`.
    """
    model = declaration.model
    structure = declaration.sector_structure()
    if presentation.virtual_sectors != structure:
        raise MalformedInputError(
            "this decoy declaration's presentation is written against the "
            f"sectors {list(presentation.virtual_sectors.labels)}, and its tagged "
            f"declaration's index set is {list(structure.labels)}; the "
            "presentation of cor:emitted-decoy is formed on the declaration's "
            "own index set"
        )
    labels = set(model.signal_alphabet)
    if set(presentation.weighted_blocks) != labels:
        raise MalformedInputError(
            "this decoy declaration's presentation carries weighted blocks for "
            f"{sorted(presentation.weighted_blocks)}, and its alphabet is "
            f"{sorted(labels)}; cor:emitted-decoy declares one block list per "
            "letter of X and no other"
        )
    sectors = declaration.sector_index_set()
    for letter in model.alphabet:
        row = presentation.weighted_blocks[letter.label]
        if len(row) != len(sectors):
            raise MalformedInputError(
                f"the block list of {letter.label!r} carries {len(row)} blocks "
                f"against {len(sectors)} sectors (cor:emitted-decoy)"
            )
        for sector, block in zip(sectors, row, strict=True):
            dyad = (
                formed[(sector.photon_number, letter.polarisation)]
                if sector.kind is SectorKind.QUANTUM and sector.photon_number
                else declaration.dyad_in(sector, letter)
            )
            factor = model.weights[letter.label] * declaration.weight_in(
                sector, letter
            )
            if not equal(block, scale(factor, dyad)):
                raise MalformedInputError(
                    f"the block of {letter.label!r} at sector {sector.label!r} "
                    "is not the block eq:decoy-blocks declares, p_x w_{x,t} "
                    "times the formed dyad (req:signal-dyads); a record built "
                    "around another block would carry an obligation asserting "
                    "membership of prop:tagging's family for an ensemble it "
                    "does not describe"
                )


def _decide_weight_obligation(
    declaration: TaggedSourceDeclaration,
) -> DecoyRefusal | None:
    """Decide (T2) against the formed enclosures, and the formed tail weight.

    ``req:sector-weight-bound``: ``0 <= ptilde(n|mu) <= P_mu(n)`` for every
    ``n <= N_src`` and every intensity. THE RIGHT-HAND SIDE IS NOT COMPARED
    AGAINST: the emission forms, from the declared ``mu`` and in exact rational
    arithmetic, the lower end of the enclosure of ``lem:poisson-enclosure`` at
    the index ``K_mu``
    (:func:`~certiqs_key.transmitter.decoy.enclosure.poisson_enclosures`), and
    compares the declared weight with it, which is what makes
    ``ptilde <= P_mu(n)`` follow. No enclosure is read from the request. The
    report names the FIRST ``(n, mu)`` at which it fails, in increasing ``n``
    and the declared order of the intensities.

    THE TAIL WEIGHT IS DECIDED TOO, AND TWICE. Its accumulation must round
    nowhere -- it is a formed quantity and an unrepresentable one is
    ``formed_entry_not_declarable``, never rounded -- and its value must be
    non-negative. ``wtilde_mu >= 0`` follows from (T2), since the weights lie
    at or below the Poisson weights, whose sum is at most one; it is decided
    here anyway, as a guard on the comparison above.
    """
    enclosures = {
        name: poisson_enclosures(value, int(declaration.source_cutoff))
        for name, value in declaration.model.intensities.items()
    }
    for photon_number in range(declaration.source_cutoff + 1):
        for intensity in declaration.model.intensities:
            key = (photon_number, intensity)
            if key not in declaration.sector_weights:
                raise MalformedInputError(
                    "the declaration carries no ptilde at photon number "
                    f"{photon_number} and intensity {intensity!r}; (T2) declares "
                    "one per n <= N_src and per intensity"
                )
            weight = declaration.sector_weights[key]
            table = enclosures[intensity]
            enclosure = table.enclosures[photon_number]
            if weight < 0 or weight > enclosure.lower:
                return DecoyRefusal(
                    reason=DecoyRefusalReason.SECTOR_WEIGHT_ABOVE_POISSON,
                    detail=(
                        f"at (n, mu) = ({photon_number}, {intensity!r}) the "
                        f"declared ptilde is {weight}, and the enclosure of "
                        "P_mu(n) formed from the declared mu at the index "
                        f"K_mu = {table.index} has the lower end "
                        f"{enclosure.lower} (lem:poisson-enclosure; "
                        "req:sector-weight-bound); the declared number is "
                        "negative or lies above it, so eq:weightineq is not "
                        "discharged. The comparison is against the LOWER end, "
                        "which is what makes ptilde <= P_mu(n) follow"
                    ),
                )
    for intensity in declaration.model.intensities:
        tail = declaration.tail_weight(intensity)
        if not tail.rounds_nowhere:
            return DecoyRefusal(
                reason=RefusalReason.FORMED_ENTRY_NOT_DECLARABLE,
                detail=(
                    f"the tail weight wtilde of the intensity {intensity!r} is "
                    "formed from the declared weights in increasing n "
                    "(eq:tailweight) and that accumulation ROUNDS, so the formed "
                    f"value {tail.value} is not admissible declared data. It is "
                    "refused and never rounded"
                ),
            )
        if tail.value < 0:
            return DecoyRefusal(
                reason=DecoyRefusalReason.SECTOR_WEIGHT_ABOVE_POISSON,
                detail=(
                    f"the tail weight of the intensity {intensity!r} is "
                    f"{tail.value} < 0, so the declared weights sum above one. "
                    "wtilde_mu >= 0 follows from eq:weightineq (T2), so the "
                    "declaration is refused rather than emitted"
                ),
            )
    return None


def _tagging_link(
    declaration: TaggedSourceDeclaration,
    presentation: EnsemblePresentation,
    weights: Mapping[Label, Fraction],
) -> SourceLink:
    """Return the one link ``Xi_tag`` of (T6), WITNESS AS A THEOREM CONSTRUCTOR.

    Source descriptor: ``(A^v, {p_x, rho^v_x})`` of (T3), (T4), read through its
    weighted members, which are the declared blocks. Target descriptor:
    ``(A', {p_x, rho_x})`` of the model -- THE FOCK SPACE, which carries no
    matrix and no dimension, which is exactly why the witness cannot be supplied
    as data and is supplied as ``prop:tagging`` instead. Empty entry list, no
    licence record, status ``exact``, and :data:`TAGGING_OBLIGATION`.

    THE DECLARED DESCRIPTOR FAMILY IS NOT DECIDABLE HERE AND IS NOT DECIDED:
    "the family is the extension of a hypothesis of a claim, the emitting module
    asserts that its descriptors satisfy it, and what a consumer decides instead
    is the triple against the registry and the provenance of the artefact"
    (``def:source-link`` (d)). The family is named, the membership is asserted in
    the obligation's fourth component, and no number is verified.
    """
    alphabet = declaration.model.signal_alphabet
    source_descriptor = AliceSideDescriptor(
        name="A^v (the tagged virtual transmitted system)",
        alphabet=alphabet,
        weights=dict(weights),
        system_dim=presentation.virtual_sectors.total_dim,
        weighted_members=None,
    )
    target_descriptor = AliceSideDescriptor(
        name="A' (the two-mode Fock space of def:wcp-model (W1))",
        alphabet=alphabet,
        weights=dict(weights),
        system_dim=None,
        weighted_members=None,
    )
    return SourceLink(
        kind=SourceLinkKind.TAGGING,
        source_descriptor=source_descriptor,
        target_descriptor=target_descriptor,
        channel_witness=None,
        declared_descriptor_family=(
            "every tagged source declaration over every weak-coherent-pulse "
            "model (def:tagged-source (T6); prop:tagging)",
        ),
        sector_map=(
            declaration.sector_structure(),
            declaration.sector_structure(),
        ),
        constraint_entries=(),
        licence=None,
        status=SourceLinkStatus.EXACT,
        obligation=TAGGING_OBLIGATION,
    )
