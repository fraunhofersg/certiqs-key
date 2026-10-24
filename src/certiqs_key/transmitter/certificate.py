"""PC11 -- the source-replacement certificate (SR1)-(SR3), and its boundary.

spec/modules/transmitter/: Definition ``def:srcert``, Theorem
``thm:certificate-sufficiency`` (i)-(ii), Corollary ``cor:noncanonical``, Remark
``rem:boundary`` and Requirement ``req:attestation-record``.

WHERE THIS FILE SITS. The code lives HERE and not in the compiler: the seven
labels PC10-PC11 belong to the transmitter, so the code that decides them does.
The two input records ``SourceReplacementCertificate`` and
``RetentionAttestation`` are this module's; the exact substrate is
:mod:`certiqs_key.foundations.exact`; and the refusal reasons are this
module's five rather than the compiler's gate spelling, which a module the
compiler depends on may not import.

TWO CONDITIONS ARE CHECKED AND THE THIRD IS NEVER DECIDED
=========================================================
(SR1) ``tr_{A''} Psi = tau_A`` and
(SR2) ``tr_A[(M_x (x) 1_{A''}) Psi] = p_x rho^v_x`` are "finitely many
matrix identities on the emitted data" -- (SR1) compares ``d_A^2`` entries
after a partial trace, (SR2) compares ``|X|`` matrices of size
``dim H(A'')`` -- and both are decided here, exactly.

(SR3) IS AN ATTESTATION AND THIS MODULE MAY NEVER ASSERT IT. Theorem
``thm:certificate-sufficiency`` (i): it "is a statement about the APPARATUS, not about
matrices; NO MATRIX FUNCTION DECIDES IT". The compiler's ``thm:gates`` (i) says the same
of its consumer: "the compiler tests PRESENCE, NEVER TRUTH". Requirement
``req:attestation-record``: the engine "records the (SR3) attestation it
receives ... in the licence record ``source_replacement_license``, and PASSES
IT THROUGH: it NEVER VERIFIES IT and NEVER ASSERTS IT of any physical
apparatus".
:class:`SourceReplacementLicense` is that record, and its
``asserted_by_this_module`` field is ``False`` in every instance this module
can construct -- structurally, by :meth:`SourceReplacementLicense.pass_through`
being the only constructor and by ``__post_init__`` refusing any other value.
The field exists so that a reader of the artifact can see the answer rather
than infer it from an absence.

WHAT (SR1) BUYS, AND WHY IT IS NO ROUTE TO ``tau_A in S_=(A)``
==============================================================
``tau_A in S_=(A)`` is DECIDED ON THE DECLARED MATRIX and never inferred from
(SR1). Requirement ``req:marginal-decided`` binds this module:
:func:`~certiqs_key.transmitter.artifact.emit_artifact` decides it directly,
also where a certificate satisfies (SR1), and refuses with
``alice_marginal_not_admissible``. The proof of the compiler's ``thm:typing``,
D(ii) clause, says the same of the consumer: check V2 decides it on the
emitted matrix, and "this is the route, and it is the only one", so an emitted
declaration satisfies D(ii) even where a certificate is malformed. V2 lives in
:mod:`certiqs_key.protocol_compiler`. What (SR1) buys is a MODELLING statement
about the same matrix: it relates ``tau_A`` to ``tr_{A''} Psi``, and that is
what makes the emitted marginal THE CERTIFICATE'S marginal rather than an
independently declared number; it is not what makes D(ii) hold. The frozen
case ``CERT-sr1-fails`` is exactly a certificate V2 would pass and (SR1)
refuses.

THE CHECKER ACCEPTS BOTH THE CANONICAL AND THE NON-CANONICAL SHAPE
==================================================================
Fact ``fact:sr`` supplies ONE canonical source replacement -- one purification,
one measurement, ``Abar`` of dimension ``|X|`` -- and Remark ``rem:import``
says why that alone will not do: it would force ``d_A = |X|`` with a singular
marginal in every protocol whose signal states are not linearly independent,
"including BB84, where the canonical ``tau_Abar`` has RANK TWO IN A
FOUR-DIMENSIONAL SPACE". Corollary ``cor:noncanonical`` draws the conclusion,
and Theorem ``thm:certificate-sufficiency`` (iii) "applies to EVERY triple satisfying
(SR1)-(SR3)". SO NOTHING HERE TESTS CANONICITY: there is no
``is_canonical_form`` predicate and no code path that prefers one shape, and an
implementation that recognized only the canonical shape would refuse the very
instance the BB84 declaration of ``instances/bb84/`` emits.

WHERE THE BOUNDARY IS
=====================
Theorem ``thm:certificate-sufficiency`` (iii) is a statement ABOUT THE SOURCE -- that
the emitted entanglement-based description and the virtual prepare-and-measure
description agree on every register other than ``A``, against every channel that acts on
neither ``A`` nor the outcome register ``X``. Remark ``rem:boundary``: "It is
NOT a security reduction, and it does NOT say that the consuming engine's
optimization is sound". Nothing in this module asserts the reduction; what it
computes is Alice's outcome distribution, which is the one observable
(iii) makes a statement about and which Remark ``rem:xreg``'s
overwriting-channel refutation is stated on.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
from typing import Protocol

from certiqs_key.foundations.blocks import BlockKind, Label, SectorStructure
from certiqs_key.foundations.errors import HypothesisError, MalformedInputError
from certiqs_key.foundations.exact import (
    Cx,
    Matrix,
    add,
    dimension,
    equal,
    identity,
    is_hermitian,
    is_positive_semidefinite,
    is_square,
    kron,
    matmul,
    partial_trace_first,
    partial_trace_second,
    real_part,
    scale,
    serialize_matrix,
    sum_in_declared_order,
    support_projector,
    trace,
    trace_in_row_order,
    zeros,
)
from certiqs_key.transmitter.reasons import (
    CERTIFICATE_CONDITION_REASONS,
    AssumptionId,
    CertificateForm,
    Refusal,
    RefusalReason,
)

__all__ = [
    "BlockCertificateVerification",
    "BlockFormCertificate",
    "CertificateVerification",
    "ConsistencyCriterion",
    "PurityConditions",
    "RetentionAttestation",
    "SourceReplacementCertificate",
    "SourceReplacementLicense",
    "alice_outcome_distribution",
    "certificate_projector",
    "check_purity",
    "check_sr1",
    "check_sr2",
    "consistency_criterion",
    "verify_block_certificate",
    "verify_certificate",
]


@dataclass(frozen=True)
class RetentionAttestation:
    """(SR3), the retention attestation of Assumption ``ass:src``.

    A STATEMENT ABOUT AN APPARATUS AND NOT ABOUT MATRICES. Theorem
    ``thm:certificate-sufficiency`` (i): (SR3) "is decided by NO function of the emitted
    data". This record carries the supplier's provenance and its own text, and this
    module tests its PRESENCE and never its truth.
    """

    attested_by: str
    statement: str


@dataclass(frozen=True)
class SourceReplacementCertificate:
    """The ``source_replacement_certificate`` input record of ``def:srcert``.

    Written against the VIRTUAL pair ``(A^v, {p_x, rho^v_x})`` -- "the only
    pair a certificate is ever written against, at every length of the source
    segment". At ``L_s = 0`` that pair is the specified one, ``A^v = A'`` and
    ``rho^v_x = rho_x``.

    THE CERTIFICATE DECLARES THE OPERATOR ``Psi``, NOT A VECTOR. "No binary64
    number ``a`` satisfies ``a^2 = 1/2``, so a declared vector with entries
    ``fl(1/sqrt2)`` yields ``|Psi><Psi|`` with entries ``fl(1/sqrt2)^2 != 1/2``
    and (SR1) FAILS EXACTLY for the certificate as the instance declares it ...
    The OPERATOR ``|Phi+><Phi+|``, by contrast, has every entry equal to
    ``1/2``, WHICH IS A BINARY64 NUMBER; and every quantity (SR1), (SR2),
    Theorem thm:certificate-sufficiency and the compilation map read off the certificate
    is A FUNCTION OF ``Psi`` AND NEVER OF A VECTOR."

    THE UNIT VECTOR IS NEVER DECLARED and is not a field of this record: it
    "EXISTS BY ``Psi^2 = Psi`` and ``tr Psi = 1``", which are two exact
    identities on the declared matrix, "and is NEVER ITSELF DECLARED".
    """

    alice_marginal: Matrix
    #: ``Psi`` in ``L(A A^v)``, in the declared computational basis with ``A``
    #: first (the ``subsystem_order`` convention).
    psi: Matrix
    virtual_dim: int
    virtual_weights: Mapping[Label, Fraction]
    virtual_states: Mapping[Label, Matrix]
    retention_attestation: RetentionAttestation | None = None


def certificate_projector(certificate: SourceReplacementCertificate) -> Matrix:
    """Return the declared operator ``Psi`` on ``A (x) A''``.

    THIS IS THE DECLARED DATUM ITSELF and not something built from
    a vector: Definition ``def:srcert`` types the input as ``Psi in L(A A'')``.
    The function survives so that every reader of the certificate names the
    same object, and it decides nothing.
    """
    return certificate.psi


@dataclass(frozen=True)
class PurityConditions:
    """The three conditions on ``Psi`` that make it a rank-one projector.

    Definition ``def:srcert``: "``Psi`` Hermitian, ``Psi^2 = Psi`` and
    ``tr Psi = 1``, EACH DECIDED EXACTLY AND THE TRACE SUMMED WITHOUT ROUNDING,
    so that ``Psi = |psi><psi|`` for a unit vector ``|psi>``". They are DECIDED
    INDEPENDENTLY and recorded independently, because a ``Psi`` can pass two
    of them and fail the third -- ``1_4/4`` is Hermitian with trace one and is
    not idempotent, and (SR1) does not see that failure.
    """

    hermitian: bool
    idempotent: bool
    trace_is_one: bool
    #: (S) on ``tr Psi``, accumulated over the row index in increasing order.
    trace_rounds_nowhere: bool
    #: The partial sums of ``tr Psi`` in that order.
    trace_partial_sums: tuple[Cx, ...]
    #: THE 1-BASED ROW INDEX OF THE FIRST INEXACT ADDITION in that
    #: accumulation, or ``None`` where (S) holds. Carried because the
    #: consuming compiler's ``gate_report`` output row asks a failing (S)
    #: decision for "the index of the first inexact addition", and THE INDEX
    #: WAS DECIDED HERE: a consumer holding only :attr:`trace_partial_sums`
    #: would have to re-decide the additions to find it, which is the
    #: inference the ``decide_never_infer`` convention exists to prevent. A
    #: DEFAULTED FIELD, so that every existing construction site stays valid.
    trace_first_inexact_row: int | None = None

    @property
    def passes(self) -> bool:
        """Whether ``Psi`` is a rank-one projector, decided exactly."""
        return (
            self.hermitian
            and self.idempotent
            and self.trace_is_one
            and self.trace_rounds_nowhere
        )


def check_purity(certificate: SourceReplacementCertificate) -> PurityConditions:
    """Decide the three conditions on ``Psi``, exactly and independently."""
    psi = certificate.psi
    hermitian = is_hermitian(psi)
    idempotent = equal(matmul(psi, psi), psi)
    accumulated = trace_in_row_order(psi)
    return PurityConditions(
        hermitian=hermitian,
        idempotent=idempotent,
        trace_is_one=accumulated.value == Cx(Fraction(1), Fraction(0)),
        trace_rounds_nowhere=accumulated.rounds_nowhere,
        trace_partial_sums=accumulated.partial_sums,
        trace_first_inexact_row=accumulated.first_inexact_row,
    )


def check_sr1(certificate: SourceReplacementCertificate) -> tuple[bool, Matrix]:
    """(SR1): whether ``tr_{A''} Psi = tau_A``, with the computed value.

    Theorem ``thm:certificate-sufficiency`` (i) shows that (SR1) implies
    ``tau_A in S_=(A)``: the computed value is a partial trace of a positive
    operator, hence positive, and its trace is ``tr Psi = 1``. THAT IMPLICATION IS
    NEVER USED AS A CHECK: ``req:marginal-decided`` has the engine decide
    ``tau_A in S_=(A)`` on the declared matrix directly, which
    :func:`~certiqs_key.transmitter.artifact.emit_artifact` does before this
    function is reached, and the proof of the compiler's ``thm:typing`` makes V2
    on the emitted matrix the only route to D(ii).
    """
    declared = certificate.alice_marginal
    alice_dim = dimension(declared)
    computed = _trace_out_virtual(certificate, alice_dim)
    return equal(computed, declared), computed


def check_sr2(
    certificate: SourceReplacementCertificate,
    alphabet: tuple[Label, ...],
    povm: dict[Label, Matrix],
) -> tuple[bool, dict[Label, Matrix], dict[Label, Matrix]]:
    """(SR2): whether ``tr_A[(M_x (x) 1) Psi] = p_x rho^v_x`` for every ``x``.

    Returns the verdict, the computed values and the expected ones, both keyed
    by the outcome label, so that a mismatch names the index rather than the
    family. ONE INDEX IS ENOUGH TO REFUSE, the condition being universally
    quantified over ``x``.

    (SR2) is what ties Alice's DECLARED MEASUREMENT to the signal she is said
    to send: with two labels exchanged the emitted declaration describes a
    source that emits ``rho^v_{x1}`` whenever the specification says
    ``rho^v_{x0}``, and the marginal condition (SR1) cannot see it.
    """
    alice_dim = dimension(certificate.alice_marginal)
    virtual_dim = certificate.virtual_dim
    projector = certificate_projector(certificate)
    computed: dict[Label, Matrix] = {}
    expected: dict[Label, Matrix] = {}
    holds = True
    for label in alphabet:
        element = povm[label]
        if dimension(element) != alice_dim:
            raise HypothesisError(
                f"M_{label!r} is not an operator on A; (SR2) is stated for the "
                "declared measurement on the retained system"
            )
        joint = kron(element, identity(virtual_dim))
        value = partial_trace_first(matmul(joint, projector), alice_dim, virtual_dim)
        want = scale(
            certificate.virtual_weights[label],
            certificate.virtual_states[label],
        )
        computed[label] = value
        expected[label] = want
        if not equal(value, want):
            holds = False
    return holds, computed, expected


def _trace_out_virtual(
    certificate: SourceReplacementCertificate, alice_dim: int
) -> Matrix:
    """Return ``tr_{A''} Psi`` on ``A``."""
    return partial_trace_second(
        certificate_projector(certificate), alice_dim, certificate.virtual_dim
    )


@dataclass(frozen=True)
class CertificateVerification:
    """The verdicts of (SR1) and (SR2), with the values that produced them.

    NO VERDICT ON (SR3) APPEARS HERE, and none may be added: it is decided by
    no function of the emitted data.

    AND NO PER-PREDICATE TRANSCRIPT APPEARS HERE EITHER, WHICH IS AN IMPORT
    RULE AND NOT A PREFERENCE. The compiler's ``gate_report`` row asks for
    these five conditions' outcomes keyed by ``(source, element, block)`` under
    the sources ``SR1``, ``SR2`` and the gate ``(G2)`` that re-decides them,
    and the vocabulary of that key --
    :class:`~certiqs_key.protocol_compiler.transcript.PredicateSource`, whose
    members are the compiler's checks, gates and interface conditions -- is the
    COMPILER'S. This module is one the compiler depends on, and
    PRINCIPLES.md section 4 says imports point downward only, so a field of
    that type here would be an upward import; the same rule is why the refusal
    reasons here are this module's five and not the compiler's gate spelling.
    What this record carries instead is everything the transcript needs as
    DATA -- the four purity verdicts with the index of the first inexact
    addition, (SR1)'s verdict, and (SR2)'s verdict per label through
    :meth:`sr2_verdicts` -- and
    :func:`~certiqs_key.protocol_compiler.compile.compile_specification`,
    which is where gate (G2) re-decides them, is what keys them.
    """

    purity: PurityConditions
    sr1_holds: bool
    sr1_computed: Matrix
    sr2_holds: bool
    sr2_computed: dict[Label, Matrix]
    sr2_expected: dict[Label, Matrix]

    def sr2_verdicts(self) -> dict[Label, bool]:
        """Return (SR2)'s verdict PER SIGNAL LABEL, in the order it decided them.

        (SR2) is universally quantified over ``x`` and :attr:`sr2_holds` is the
        conjunction; the per-label verdicts are the comparisons that formed it,
        read back off the values this record carries. ONE SITE MAKES THEM: the
        detail string of :meth:`refusal` named the mismatched labels with an
        inline comparison of its own, and the consuming compiler's
        ``gate_report`` row wants the same verdicts per element ("the exact
        identities (SR1), (SR2) ... keyed by (source, element, block)"), so the
        two read one accessor rather than comparing the same matrices twice in
        two places.
        """
        return {
            label: equal(value, self.sr2_expected[label])
            for label, value in self.sr2_computed.items()
        }

    @property
    def passes(self) -> bool:
        """Whether all FIVE checkable conditions hold.

        The compiler's ``def:eligible`` (G2) is stated on all five -- the three
        on ``Psi`` and (SR1), (SR2) -- and "every other site that names (G2)
        QUOTES THESE FIVE AND ADDS NOTHING TO THEM". They are decided HERE
        first and RE-DECIDED there, on the emitted data.
        """
        return self.purity.passes and self.sr1_holds and self.sr2_holds

    def failing_conditions(self) -> tuple[str, ...]:
        """Return EVERY failing condition of the five, in the stated order.

        WHICH CONDITION THE REFUSAL NAMES IS NOT FIXED BY A CLAIM -- the
        compiler's gate outcome table, row 3, says "refusal, NAMING THE
        CONDITION" and fixes no ordering -- so this module names them ALL
        rather than choosing one. A certificate that fails two conditions
        records two.
        """
        verdicts = (
            ("Psi = Psi^dag", self.purity.hermitian),
            ("Psi^2 = Psi", self.purity.idempotent),
            ("tr Psi = 1", self.purity.trace_is_one),
            ("tr Psi rounds nowhere", self.purity.trace_rounds_nowhere),
            ("(SR1)", self.sr1_holds),
            ("(SR2)", self.sr2_holds),
        )
        return tuple(name for name, held in verdicts if not held)

    def refusal(self) -> Refusal | None:
        """Return the refusal a failing certificate produces, naming the condition.

        The compiler's gate outcome table, row 3: a present-but-failing
        certificate is a REFUSAL "naming the condition" -- "A certificate that
        does not verify is a defect in the supplied data, NOT A WEAKER CLAIM;
        silently demoting it would hide a mis-specified source." Requirement
        ``req:failing-certificate`` says the same of this module and adds the
        scope: AT EVERY ``d_A``, ``d_A = 1`` included.

        ONE REASON PER CONDITION, from :data:`CERTIFICATE_CONDITION_REASONS`.
        The transmitter
        interface's ``the_five_decided_conditions_are_five_reasons`` gives each
        of the five a name of its own, so a refusal names the condition without
        a reader having to parse the detail string.
        """
        failing = self.failing_conditions()
        if not failing:
            return None
        detail_suffix = f"Every failing condition: {', '.join(failing)}"
        first = failing[0]
        reason = CERTIFICATE_CONDITION_REASONS[first]
        if first in {"Psi = Psi^dag", "Psi^2 = Psi"}:
            return Refusal(
                reason=reason,
                detail=(
                    f"the declared Psi is not a rank-one projector: {first} "
                    "fails. The unit vector |psi> EXISTS BY Psi^2 = Psi AND "
                    "tr Psi = 1, so a Psi failing idempotence has no |psi> "
                    f"behind it at all. {detail_suffix}"
                ),
            )
        if first in {"tr Psi = 1", "tr Psi rounds nowhere"}:
            return Refusal(
                reason=reason,
                detail=(
                    f"the declared Psi is not a rank-one projector: {first} "
                    f"fails. {detail_suffix}"
                ),
            )
        if first == "(SR1)":
            return Refusal(
                reason=reason,
                detail=(
                    "tr_{A^v} Psi differs from the declared tau_A; the "
                    "emitted marginal would not be the certificate's "
                    f"marginal. {detail_suffix}"
                ),
            )
        mismatched = [
            label for label, holds in self.sr2_verdicts().items() if not holds
        ]
        return Refusal(
            reason=reason,
            detail=(
                f"tr_A[(M_x (x) 1) Psi] differs from p_x rho^v_x at "
                f"{mismatched}; the emitted declaration would describe a "
                f"different source from the specified one. {detail_suffix}"
            ),
        )


def verify_certificate(
    certificate: SourceReplacementCertificate,
    alphabet: tuple[Label, ...],
    povm: dict[Label, Matrix],
) -> CertificateVerification:
    """Decide all FIVE conditions of gate (G2). (SR3) IS NOT CHECKED.

    "The three on ``Psi`` above, (SR1) and (SR2) -- ARE EXACTLY WHAT CHECK (G2)
    of Definition def:eligible DECIDES." (SR3) "carries NO NUMBER and is
    decided by nothing"; Theorem ``thm:certificate-sufficiency`` (i): "NO MATRIX
    FUNCTION DECIDES IT."

    This is the pure form. In block form (i) decides (SR1) and (SR2) as
    ``eq:srblock`` together with the block diagonality of every weighted
    virtual member along the matched sectors: :func:`verify_block_certificate`
    decides the first, and
    :func:`certiqs_key.transmitter.artifact.emit_artifact` the second on the
    declared ``sigma^v_x``.
    """
    sr1_holds, sr1_computed = check_sr1(certificate)
    sr2_holds, computed, expected = check_sr2(certificate, alphabet, povm)
    return CertificateVerification(
        purity=check_purity(certificate),
        sr1_holds=sr1_holds,
        sr1_computed=sr1_computed,
        sr2_holds=sr2_holds,
        sr2_computed=computed,
        sr2_expected=expected,
    )


@dataclass(frozen=True)
class BlockFormCertificate:
    """The BLOCK FORM of ``def:srcert``: positive blocks, and NO purity condition.

    IT EXISTS FOR A DECLARABILITY REASON AND NOT A GENERALITY ONE. ``def:srcert``:
    "exact purity is not declarable for a source that draws a sector and then prepares a
    state in it. A globally pure ``Psi`` over sectors of weights ``g_t`` carries
    cross-sector amplitudes ``sqrt(g_t g_t')``, which need not be dyadic rationals, and
    a pure block whose marginal has the spectrum ``(1/2, 1/4, 1/4)`` carries the entry
    ``sqrt(1/8)``, which is not one. The direct sum of positive blocks is
    exactly declarable, it is the state of the source that first draws ``t``
    with probability ``tr Psi_t`` and then prepares ``Psi_t / tr Psi_t``."

    THE MATCHED PAIR IS THE TYPE AND NOT A CONDITION. ``A`` and ``A^v`` carry
    the SAME ordered index set, the sector ``S_t`` against ``A_t``, so a
    presentation whose two structures disagree is not a presentation of this
    form at all and ``__post_init__`` refuses it as malformed rather than
    inventing a refusal string for it.

    WHAT IS DECIDED OF IT (``thm:certificate-sufficiency`` (i)): per block Hermiticity
    and positive semidefiniteness, by an exact decision; the total trace; the
    block diagonality of every weighted virtual member ``sigma^v_x`` along the
    matched sectors, decided entry by entry on its declared entries (``def:srcert``;
    :func:`certiqs_key.transmitter.artifact.emit_artifact` decides it on the
    specified matrices, which at ``L_s = 0`` are the virtual ones, and holds the
    diagonal blocks to :attr:`virtual_blocks`); and (SR1), (SR2) block by block,
    Eq. ``eq:srblock``. The block diagonality and ``eq:srblock`` together are
    (SR1) and (SR2) of ``Psi``. THERE IS NO IDEMPOTENCE CONDITION HERE
    AND NO CONSUMER MAY ADD ONE -- ``def:srcert`` in terms: "There is no
    idempotence condition there and no consumer may add one." A consumer that
    demands purity of every certificate re-decides it and therefore REFUSES a
    block form, which is fail-closed and is what today's protocol compiler
    does.
    """

    #: ``T``, ``{Pi^A_t}``, ``d_{A_t}``. Block kind ``proof_sector``.
    alice_sectors: SectorStructure
    #: The MATCHED structure on ``A^v``: the same ordered index set, ``S_t``
    #: against ``A_t``.
    virtual_sectors: SectorStructure
    #: ``tau^{(t)}_A`` on ``A_t``, in the declared sector order.
    alice_marginal_blocks: tuple[Matrix, ...]
    #: ``Psi_t`` on ``A_t S_t``, of dimension ``d_{A_t} dim S_t`` with the
    #: ``A`` index MAJOR (the ``subsystem_order`` convention).
    psi_blocks: tuple[Matrix, ...]
    #: The virtual ensemble's weights, as everywhere else in this module.
    virtual_weights: Mapping[Label, Fraction]
    #: ``sigma^{v,(t)}_x`` on ``S_t``: the virtual ensemble by its WEIGHTED
    #: MEMBERS, block by block, which is the side Eq. ``eq:srblock`` compares.
    virtual_blocks: Mapping[Label, tuple[Matrix, ...]]
    retention_attestation: RetentionAttestation | None = None

    def __post_init__(self) -> None:
        """Refuse a presentation Eq. ``eq:srblock`` cannot be read against."""
        if self.alice_sectors.labels != self.virtual_sectors.labels:
            raise MalformedInputError(
                "the block form is written against MATCHED sector structures "
                "-- the same ordered index set, the sector S_t against A_t "
                "(def:srcert) -- and these carry "
                f"{list(self.alice_sectors.labels)} on A against "
                f"{list(self.virtual_sectors.labels)} on A^v"
            )
        for side, structure in (
            ("A", self.alice_sectors),
            ("A^v", self.virtual_sectors),
        ):
            if structure.block_kind is not BlockKind.PROOF_SECTOR:
                raise MalformedInputError(
                    f"the {side} sector structure of a block-form certificate "
                    "carries the block kind `proof_sector` (def:source-link "
                    f"(e)); this one carries {structure.block_kind.value!r}"
                )
        count = self.alice_sectors.count
        if len(self.psi_blocks) != count or len(self.alice_marginal_blocks) != count:
            raise MalformedInputError(
                f"a block list against {count} sectors carries that many "
                f"blocks; this certificate carries {len(self.psi_blocks)} "
                f"blocks of Psi and {len(self.alice_marginal_blocks)} of tau_A"
            )
        for position in range(count):
            joint = self.alice_sectors.dims[position] * self.virtual_sectors.dims[
                position
            ]
            block = self.psi_blocks[position]
            if not is_square(block) or dimension(block) != joint:
                raise MalformedInputError(
                    f"Psi at sector {self.alice_sectors.labels[position]!r} is "
                    f"not an operator on A_t S_t of dimension {joint}"
                )
            marginal = self.alice_marginal_blocks[position]
            if (
                not is_square(marginal)
                or dimension(marginal) != self.alice_sectors.dims[position]
            ):
                raise MalformedInputError(
                    f"tau_A at sector {self.alice_sectors.labels[position]!r} "
                    "is not an operator on A_t"
                )
        # ONE BLOCK PER MATCHED SECTOR, OF THAT SECTOR'S DIMENSION, for every
        # letter's weighted member: a list of another length or shape is not a
        # block list along (S_t)_t at all, so eq:srblock and the block
        # diagonality of def:srcert cannot be read against it.
        for label, blocks in self.virtual_blocks.items():
            if len(blocks) != count:
                raise MalformedInputError(
                    f"the weighted virtual member of {label!r} is a block list "
                    f"of {len(blocks)} blocks against {count} matched sectors; "
                    "a block list carries one block per sector (def:srcert)"
                )
            for position, member in enumerate(blocks):
                dim = self.virtual_sectors.dims[position]
                if not is_square(member) or dimension(member) != dim:
                    raise MalformedInputError(
                        f"the block of {label!r} at sector "
                        f"{self.virtual_sectors.labels[position]!r} is not an "
                        f"operator on S_t of dimension {dim} (def:srcert)"
                    )

    @property
    def alice_dim(self) -> int:
        """Return ``d_A = sum_t d_{A_t}``."""
        return self.alice_sectors.total_dim

    @property
    def virtual_dim(self) -> int:
        """Return ``dim H(A^v) = sum_t dim S_t``."""
        return self.virtual_sectors.total_dim


@dataclass(frozen=True)
class BlockCertificateVerification:
    """The verdicts of the block form, PER SECTOR, with what produced them.

    ONE REFUSAL REASON AND IT NAMES THE SECTOR, which is a deliberate asymmetry
    with the pure form's five: "The block form's conditions are decided PER
    SECTOR, so the report must name the sector to be useful, and one reason
    with the sector and the condition in its report says more than five reasons
    without them" (the interface's
    ``the_block_form_has_one_reason_and_names_the_sector``).

    NO PURITY VERDICT APPEARS HERE, and none may be added: the block form
    carries no idempotence condition, globally or per block.
    """

    #: Sectors at which the block is not Hermitian.
    not_hermitian: tuple[Label, ...]
    #: Sectors at which the block is not positive semidefinite, by the exact
    #: decision of ``thm:certificate-sufficiency`` (i)'s proof: "a symmetric elimination
    #: over the Gaussian rationals in which a negative pivot refuses the block and a
    #: zero pivot requires its whole row and column to vanish".
    not_positive_semidefinite: tuple[Label, ...]
    total_trace: Cx
    trace_is_one: bool
    trace_rounds_nowhere: bool
    #: Sectors at which (SR1) ``tr_{S_t} Psi_t = tau^{(t)}_A`` fails.
    sr1_failures: tuple[Label, ...]
    #: ``(sector, letter)`` at which (SR2) of Eq. ``eq:srblock`` fails.
    sr2_failures: tuple[tuple[Label, Label], ...]
    #: Sectors at which the later decisions WERE NOT TAKEN, and it is recorded
    #: rather than left to be read off an absence. Positive semidefiniteness "is
    #: a property of a Hermitian operator" and
    #: :func:`~certiqs_key.foundations.exact.is_positive_semidefinite` RAISES on a
    #: non-Hermitian argument rather than answering ``False``, "because a
    #: ``False`` here would report a failed certificate where none was tested";
    #: the same is true of (SR1) and (SR2) at such a sector, which compare a
    #: partial trace of an operator the form does not admit. So a non-Hermitian
    #: block ends this sector's decisions, its name appears here, and
    #: :attr:`not_positive_semidefinite`, :attr:`sr1_failures` and
    #: :attr:`sr2_failures` say nothing about it in either direction.
    #:
    #: ITS TRACE IS STILL RECORDED AND IS THE TRACE OF THE DECLARED BLOCK.
    #: ``tr Psi_t`` is a sum of diagonal entries and needs no Hermiticity to be
    #: formed, so the total this record carries is the total of the declared
    #: numbers. A non-Hermitian
    #: block does not contribute a FICTITIOUS ZERO to it, which would make
    #: :attr:`total_trace` a number no declaration carried.
    undecided_sectors: tuple[Label, ...] = ()

    @property
    def passes(self) -> bool:
        """Whether every condition ``def:srcert`` places on a block form holds."""
        return (
            not self.not_hermitian
            and not self.undecided_sectors
            and not self.not_positive_semidefinite
            and self.trace_is_one
            and self.trace_rounds_nowhere
            and not self.sr1_failures
            and not self.sr2_failures
        )

    def refusal(self) -> Refusal | None:
        """Return the refusal a failing block form produces, NAMING THE SECTOR."""
        if self.not_hermitian:
            return _block_refusal(
                f"the block at sector {self.not_hermitian[0]!r} is not Hermitian, "
                "and the later conditions were NOT DECIDED there: positivity is "
                "a property of a Hermitian operator, and (SR1), (SR2) would "
                "compare partial traces of an operator this form does not admit"
            )
        if self.not_positive_semidefinite:
            return _block_refusal(
                f"the block at sector {self.not_positive_semidefinite[0]!r} is "
                "not positive semidefinite by the exact decision (a symmetric "
                "elimination over the Gaussian rationals with the zero-pivot "
                "rule); no eigenvalue is computed and no threshold appears, so "
                "a SINGULAR block is admissible and this one is not"
            )
        if not self.trace_is_one:
            return _block_refusal(
                f"the block traces sum to {self.total_trace} and not to 1"
            )
        if not self.trace_rounds_nowhere:
            return _block_refusal(
                "the block traces, summed in the declared order of the sectors, "
                "do not round nowhere"
            )
        if self.sr1_failures:
            return _block_refusal(
                f"(SR1) fails at sector {self.sr1_failures[0]!r}: "
                "tr_{S_t} Psi_t differs from the declared tau^{(t)}_A"
            )
        if self.sr2_failures:
            sector, letter = self.sr2_failures[0]
            return _block_refusal(
                f"(SR2) fails at sector {sector!r} and letter {letter!r}: "
                "tr_{A_t}[(M^{(t)}_x (x) 1) Psi_t] differs from the declared "
                "sigma^{v,(t)}_x"
            )
        return None


def _block_refusal(detail: str) -> Refusal:
    """Return the block form's one refusal, with the sector and condition named."""
    return Refusal(
        reason=RefusalReason.CERTIFICATE_BLOCK_NOT_ADMISSIBLE,
        detail=(
            f"{detail}. The five pure-form reasons are not reused for a block: "
            "a block form carries no idempotence condition (def:srcert)"
        ),
    )


def verify_block_certificate(
    certificate: BlockFormCertificate,
    alphabet: Sequence[Label],
    povm_blocks: Mapping[Label, tuple[Matrix, ...]],
) -> BlockCertificateVerification:
    """Decide the block form's conditions, PER BLOCK and exactly. NO PURITY.

    ``thm:certificate-sufficiency`` (i): "in block form they are, per block, one
    comparison of ``(d_{A_t} dim S_t)^2`` entries for Hermiticity and one exact decision
    of positive semidefiniteness ... and one accumulated trace over all blocks";
    then (SR1) and (SR2) read block by block, Eq. ``eq:srblock``.

    TWO ACCUMULATIONS AND BOTH ARE DECIDED, WHICH IS THE READING TAKEN WHERE
    THE TEXT IS SHORT. ``def:srcert`` asks for "``sum_t tr Psi_t = 1``, the
    traces summed in the declared order without rounding". A per-block trace is
    itself an accumulation, over the row index, so "without rounding" is read
    here as binding on BOTH -- each block's own trace and the sum over the
    sectors -- because the alternative admits a total that rounds inside a
    block and reports it as exact, which is the failure the condition exists to
    catch. The stricter reading refuses more and is named here rather than
    taken silently.

    BLOCK BY BLOCK, AND SO NOT ALL OF (SR2). ``def:srcert``: ``eq:srblock``
    together with the block diagonality of every ``sigma^v_x`` along the
    matched sectors is (SR1) and (SR2) of ``Psi``; ``eq:srblock`` alone is (SR2)
    against the pinched members only. This function decides ``eq:srblock`` on
    :attr:`BlockFormCertificate.virtual_blocks`; the block diagonality is
    decided on the declared members by
    :func:`certiqs_key.transmitter.artifact.emit_artifact`, under the same
    reason ``certificate_block_not_admissible``.
    """
    not_hermitian: list[Label] = []
    not_psd: list[Label] = []
    sr1_failures: list[Label] = []
    sr2_failures: list[tuple[Label, Label]] = []
    traces: list[Matrix] = []
    trace_rounds_nowhere = True

    undecided: list[Label] = []

    for position, sector in enumerate(certificate.alice_sectors.labels):
        block = certificate.psi_blocks[position]
        # THE TRACE IS TAKEN FIRST AND OF THE DECLARED BLOCK, whatever else this
        # sector turns out to be: tr Psi_t is a sum of diagonal entries and
        # needs no Hermiticity, so the total is the total of the declared
        # numbers rather than of a repaired image of them.
        accumulated = trace_in_row_order(block)
        if not accumulated.rounds_nowhere:
            trace_rounds_nowhere = False
        traces.append(((accumulated.value,),))
        if not is_hermitian(block):
            # AND THE LATER DECISIONS ARE NOT TAKEN, AND SAY SO. Positivity is a
            # property of a Hermitian operator and its decision RAISES on any
            # other; (SR1) and (SR2) at this sector would compare partial traces
            # of an operator the form does not admit. Recording the sector as
            # undecided is what keeps `not_positive_semidefinite` a list of
            # blocks that were TESTED AND FAILED.
            not_hermitian.append(sector)
            undecided.append(sector)
            continue
        if not is_positive_semidefinite(block):
            not_psd.append(sector)

        alice_dim = certificate.alice_sectors.dims[position]
        virtual_dim = certificate.virtual_sectors.dims[position]
        if not equal(
            partial_trace_second(block, alice_dim, virtual_dim),
            certificate.alice_marginal_blocks[position],
        ):
            sr1_failures.append(sector)
        for label in alphabet:
            element = povm_blocks[label][position]
            if dimension(element) != alice_dim:
                raise HypothesisError(
                    f"M_{label!r} at sector {sector!r} is not an operator on "
                    "A_t; (SR2) is stated for the declared measurement on the "
                    "retained system"
                )
            value = partial_trace_first(
                matmul(kron(element, identity(virtual_dim)), block),
                alice_dim,
                virtual_dim,
            )
            if not equal(value, certificate.virtual_blocks[label][position]):
                sr2_failures.append((sector, label))

    total = sum_in_declared_order(traces)
    if not total.rounds_nowhere:
        trace_rounds_nowhere = False
    return BlockCertificateVerification(
        not_hermitian=tuple(not_hermitian),
        not_positive_semidefinite=tuple(not_psd),
        total_trace=total.total[0][0],
        trace_is_one=total.total[0][0] == Cx(Fraction(1), Fraction(0)),
        trace_rounds_nowhere=trace_rounds_nowhere,
        undecided_sectors=tuple(undecided),
        sr1_failures=tuple(sr1_failures),
        sr2_failures=tuple(sr2_failures),
    )


class _HasMachineRecord(Protocol):
    """Anything with a wire form, STRUCTURALLY, so that no import runs upward.

    The licence carries an ensemble presentation, whose type lives in
    :mod:`certiqs_key.transmitter.presentation` -- and that module imports
    :class:`RetentionAttestation` from this one, because (SR3) is the same
    attestation in all three forms. Naming the concrete type here would close
    that into an import cycle, so the field is typed by the one method the
    licence calls on it. A Protocol, not ``object``: the method the wire form
    needs is then checked rather than assumed.
    """

    def as_machine_record(self) -> dict[str, object]:
        """Return the object's wire form."""
        ...


@dataclass(frozen=True)
class SourceReplacementLicense:
    """The ``source_replacement_license`` record: a PASS-THROUGH, and nothing else.

    The ``source_replacement_license`` output row emits it "trusted mode at
    d_A >= 2 only", carrying (SR1)-(SR3); it is "VACUOUS AT ``d_A = 1`` and
    then NOT EMITTED AND NOT DEMANDED" (Remark ``rem:da1``; Requirement
    ``req:licence-scope``). WHETHER it is
    emitted is decided by :mod:`certiqs_key.transmitter.artifact`; WHAT it may
    say is, and the
    answer is: the two checkable conditions' verdicts, the attestation as
    supplied, and ``asserted_by_this_module = False``.

    ``asserted_by_this_module`` is not decoration. It is the difference between
    recording an attestation and making one, and Requirement
    ``req:attestation-record`` makes that difference the boundary of this
    module. IT IS FALSE IN EVERY INSTANCE AND THE CONSTRUCTOR REFUSES ANY OTHER
    VALUE.

    WHY THE CERTIFICATE ITSELF TRAVELS WITH THE RECORD. The
    protocol compiler's ``transmitter_artifact`` input row types this key as
    "the certificate record ``(tau_A, Psi, {p_x, rho^v_x})`` with its
    attestation (SR3)", and its gate (G2) RE-DECIDES the five conditions "on
    the emitted data" (``def:eligible`` (G2); the ``decide_never_infer``
    convention). A record carrying only two verdicts would leave the consumer
    nothing to re-decide them ON, so it would have to take this module's word
    for them -- which is the inference that convention forbids.
    """

    sr1_holds: bool
    sr2_holds: bool
    retention_attestation: RetentionAttestation | None
    #: The certificate the two verdicts were decided on, carried so that a
    #: consumer can re-decide them rather than infer them. ``None`` only for a
    #: record built by hand in a test, and for the two forms that declare no
    #: ``Psi`` -- where the datum a consumer re-decides on is
    #: :attr:`block_certificate` or :attr:`presentation` instead.
    certificate: SourceReplacementCertificate | None = None
    asserted_by_this_module: bool = False
    #: WHICH FORM WAS DECLARED, "because which conditions were decided depends
    #: on it" (the ``source_replacement_license`` output row). DERIVED from
    #: which slot a specification filled, never declared beside it.
    form: CertificateForm = CertificateForm.PURE
    #: The block-form certificate the per-sector verdicts were decided on.
    #: ``None`` in every other form.
    block_certificate: BlockFormCertificate | None = None
    #: The ensemble presentation (E1)-(E3) were decided on. WITH A PRESENTATION
    #: THE RECORD CARRIES THE DECLARED BLOCKS AND THE SECTOR STRUCTURE, AND NOT
    #: ``Psi`` OR ``{M_x}``: those are defined, carry square roots and
    #: quotients, and "are formed by no one", so a consumer re-decides (E1) to
    #: (E3) and nothing else (the ``source_replacement_license`` output row).
    #: Typed
    #: ``object`` so that :mod:`certiqs_key.transmitter.presentation` needs no
    #: import of this module; the concrete type is its ``EnsemblePresentation``.
    presentation: _HasMachineRecord | None = None

    def __post_init__(self) -> None:
        """Refuse any instance that would assert (SR3) of an apparatus."""
        if self.asserted_by_this_module:
            raise HypothesisError(
                "this module may NEVER assert (SR3) of a physical apparatus "
                "(Requirement req:attestation-record); it records the "
                "attestation it was given"
            )

    @property
    def attestation_supplied(self) -> bool:
        """Whether an (SR3) attestation was supplied at all."""
        return self.retention_attestation is not None

    @classmethod
    def pass_through(
        cls,
        verification: CertificateVerification,
        attestation: RetentionAttestation | None,
        certificate: SourceReplacementCertificate | None = None,
    ) -> SourceReplacementLicense:
        """Return the record for a verified certificate and a supplied attestation.

        THE ATTESTATION IS NEVER SYNTHESIZED (the ``fail_closed``
        convention). Where none was supplied the field is
        ``None`` and the record says so; nothing fills it.
        """
        return cls(
            sr1_holds=verification.sr1_holds,
            sr2_holds=verification.sr2_holds,
            retention_attestation=attestation,
            certificate=certificate,
        )

    @classmethod
    def pass_through_block(
        cls,
        verification: BlockCertificateVerification,
        attestation: RetentionAttestation | None,
        certificate: BlockFormCertificate,
    ) -> SourceReplacementLicense:
        """Return the record for a verified BLOCK-FORM certificate.

        The two verdicts are the block-by-block ones -- (SR1) and (SR2) of
        Eq. ``eq:srblock`` -- which is what (SR1) and (SR2) ARE for this form;
        there is no third verdict to carry, purity being no condition here. The
        record names the form and carries the certificate it was decided on, so
        that a consumer re-decides rather than infers.
        """
        return cls(
            sr1_holds=not verification.sr1_failures,
            sr2_holds=not verification.sr2_failures,
            retention_attestation=attestation,
            certificate=None,
            form=CertificateForm.BLOCK,
            block_certificate=certificate,
        )

    @classmethod
    def pass_through_presentation(
        cls,
        presentation: _HasMachineRecord,
        attestation: RetentionAttestation | None,
    ) -> SourceReplacementLicense:
        """Return the record for an ENSEMBLE PRESENTATION.

        (SR1) AND (SR2) ARE RECORDED AS HOLDING AND WERE DECIDED BY NOTHING,
        which is the one place this record says something it did not decide --
        and it is a theorem rather than a verdict. ``def:srcert``: "(SR1),
        (SR2), positivity of the blocks, the POVM condition and the purity of
        the blocks are THEOREMS of the presentation and are decided by nothing,
        there being no second declared datum they could be compared with."
        ``lem:ensemble-presentation`` (i) is what proves them, and
        :attr:`form` is what tells a consumer which of the two it is reading.
        What WAS decided is (E1) to (E3), on the declared blocks this record
        carries.
        """
        return cls(
            sr1_holds=True,
            sr2_holds=True,
            retention_attestation=attestation,
            certificate=None,
            form=CertificateForm.ENSEMBLE_PRESENTATION,
            presentation=presentation,
        )

    def as_machine_record(self) -> dict[str, object]:
        """Return the licence as a machine record, THE CERTIFICATE INCLUDED.

        THE CERTIFICATE TRAVELS ON THE WIRE. The ``source_replacement_license`` output
        row's ``certificate_travels_note`` says the emitted record carries the
        certificate itself -- ``tau_A``, ``Psi`` and the virtual pair -- "so
        that a consumer can re-decide the conditions on the emitted data rather
        than take this module's verdicts on trust", and PRINCIPLES.md section 9
        makes the SERIALISABLE artefact the module boundary. The object
        carries the certificate and gate (G2) re-decides on it, so the wire form
        carries it too, or a consumer reading the wire form could not do the
        thing the note says the record exists to let it do.

        THE RECORD IS JSON AS EMITTED. Every matrix is written by
        :func:`~certiqs_key.foundations.exact.serialize_matrix` -- nested lists
        of ``[re, im]`` exact-rational strings, which
        :func:`~certiqs_key.foundations.exact.deserialize_matrix` reads back
        without loss -- and every exact weight as its ``"p/q"`` string, so a
        consumer that writes the record to a file (the run tier's operator
        bundle) passes it through and converts nothing. The transmitter owns
        this record and therefore its wire form (PRINCIPLES.md section 9: a
        module boundary is a serialisable artefact). Nothing is rounded, so a
        consumer re-decides on exactly the numbers this module decided on.

        THE ATTESTATION IS NOT REPEATED INSIDE THE CERTIFICATE BLOCK. (SR3) is
        the licence's own ``sr3_attestation`` key, decided and recorded by this
        module; the certificate's optional copy of it is the SUPPLIED record
        and is the same object, so emitting both would put one datum on the
        wire twice.

        THE PURE FORM'S RECORD CARRIES NO KEY OF THE OTHER FORMS. The keys that
        carry the block form and the ensemble presentation appear ONLY where one
        of those two was declared: the design rule is that the plain
        declaration is the one-sector, pure-form, empty-segment case of the
        general one, ENTRY FOR ENTRY, and a wire record that carried two keys
        for a declaration that declares neither form would not be that. The
        absence of ``form`` therefore MEANS ``pure``, as the absence of
        ``alice_marginal`` means untrusted mode, and both readings are the
        artefact's own default rather than a silence.
        """
        attestation = self.retention_attestation
        certificate = self.certificate
        record: dict[str, object] = {
            "sr1_holds": self.sr1_holds,
            "sr2_holds": self.sr2_holds,
            "sr3_attestation_supplied": self.attestation_supplied,
            "sr3_asserted_by_this_module": self.asserted_by_this_module,
            "sr3_never_verified_assumption": str(AssumptionId.A_SRC),
            "sr3_attestation": (
                None
                if attestation is None
                else {
                    "attested_by": attestation.attested_by,
                    "statement": attestation.statement,
                }
            ),
            "certificate": (
                None
                if certificate is None
                else {
                    "alice_marginal": serialize_matrix(certificate.alice_marginal),
                    "psi": serialize_matrix(certificate.psi),
                    "virtual_dim": certificate.virtual_dim,
                    "virtual_weights": _weights_record(certificate.virtual_weights),
                    "virtual_states": {
                        label: serialize_matrix(state)
                        for label, state in certificate.virtual_states.items()
                    },
                }
            ),
        }
        if self.form is CertificateForm.PURE:
            return record
        record["form"] = str(self.form)
        block = self.block_certificate
        if block is not None:
            record["block_certificate"] = {
                "sector_index_set": list(block.alice_sectors.labels),
                "alice_sector_dims": list(block.alice_sectors.dims),
                "virtual_sector_dims": list(block.virtual_sectors.dims),
                "sector_block_kind": str(block.alice_sectors.block_kind),
                "alice_marginal_blocks": [
                    serialize_matrix(m) for m in block.alice_marginal_blocks
                ],
                "psi_blocks": [serialize_matrix(m) for m in block.psi_blocks],
                "virtual_weights": _weights_record(block.virtual_weights),
                "virtual_blocks": {
                    label: [serialize_matrix(m) for m in blocks]
                    for label, blocks in block.virtual_blocks.items()
                },
            }
        if self.presentation is not None:
            record["ensemble_presentation"] = self.presentation.as_machine_record()
        return record


def _weights_record(weights: Mapping[Label, Fraction]) -> dict[Label, str]:
    """Return exact weights in the record's JSON form: ``"p/q"`` per label."""
    return {label: str(weight) for label, weight in weights.items()}


@dataclass(frozen=True)
class ConsistencyCriterion:
    """Theorem ``thm:certificate-sufficiency`` (ii): the criterion and the identity it decides.

    ``Pi_S (sum_x M_x) Pi_S = Pi_S`` holds IF AND ONLY IF
    ``sum_x p_x rho^v_x = tr_A Psi``. The projector onto
    ``S = supp tau_A`` is what makes it an equivalence rather than a sufficient
    condition: a family whose defect lies entirely OUTSIDE that support passes
    it although it is not a POVM, because the Schmidt vectors of ``|Psi>`` span
    only the support and no matrix element sees the defect. The criterion is a
    CROSS-CHECK on check V3 and not a duplicate of it, and both are needed.
    """  # noqa: E501

    support_projector: Matrix
    family_sum: Matrix
    projected_sum: Matrix
    criterion_holds: bool
    average_virtual_state: Matrix
    psi_signal_marginal: Matrix
    identity_holds: bool


def consistency_criterion(
    certificate: SourceReplacementCertificate,
    alphabet: tuple[Label, ...],
    povm: dict[Label, Matrix],
) -> ConsistencyCriterion:
    """Return Theorem ``thm:certificate-sufficiency`` (ii)'s criterion and its identity, both decided.

    The virtual weights and states are read from the certificate, which is
    where Definition ``def:srcert`` puts them; the identity's left-hand side is
    ``sum_x p_x rho^v_x`` and its right-hand side is ``tr_A Psi``, the
    certificate vector's own signal-side marginal.
    """  # noqa: E501
    alice_dim = dimension(certificate.alice_marginal)
    virtual_dim = certificate.virtual_dim
    projector = support_projector(certificate.alice_marginal)

    total = zeros(alice_dim, alice_dim)
    for label in alphabet:
        total = add(total, povm[label])
    projected = matmul(matmul(projector, total), projector)

    average = zeros(virtual_dim, virtual_dim)
    for label in alphabet:
        average = add(
            average,
            scale(
                certificate.virtual_weights[label],
                certificate.virtual_states[label],
            ),
        )
    signal_marginal = partial_trace_first(
        certificate_projector(certificate), alice_dim, virtual_dim
    )
    return ConsistencyCriterion(
        support_projector=projector,
        family_sum=total,
        projected_sum=projected,
        criterion_holds=equal(projected, projector),
        average_virtual_state=average,
        psi_signal_marginal=signal_marginal,
        identity_holds=equal(average, signal_marginal),
    )


def alice_outcome_distribution(
    certificate: SourceReplacementCertificate,
    alphabet: tuple[Label, ...],
    povm: dict[Label, Matrix],
) -> dict[Label, Fraction]:
    """Return Alice's outcome distribution under Eq. ``eq:Nmsm``.

    ``N_A(xi) = sum_x tr[M_x xi] |x><x|_X`` applied to the certificate's
    ``A``-marginal, which is ``tau_A`` by (SR1). This is the one observable
    Theorem ``thm:certificate-sufficiency`` (iii) makes a statement about, and it is
    what Remark ``rem:xreg``'s refutation compares: a channel that OVERWRITES ``X`` with
    a fixed value produces a point distribution, while any composition in which
    it precedes the measurement leaves this distribution intact -- and one such
    channel is enough to refute a commutation asserted for EVERY channel.

    Nothing here asserts the commutation or the reduction. The distribution is
    computed from the emitted data and compared where a derivation needs it.
    """
    marginal = _trace_out_virtual(certificate, dimension(certificate.alice_marginal))
    return {
        label: real_part(
            trace(matmul(povm[label], marginal)),
            f"the outcome probability of {label!r}",
        )
        for label in alphabet
    }
