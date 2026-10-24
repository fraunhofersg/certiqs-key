"""The ensemble presentation: declare the ensemble, define the certificate.

spec/modules/transmitter/: Definition ``def:srcert``, the third form, with its
conditions (E1) to (E3); Lemma ``lem:ensemble-presentation``, which defines
Alice's system, her marginal, her measurement and the certificate's blocks from
the declared weighted ensemble and proves them a block-form certificate with
pure blocks; Theorem ``thm:certificate-sufficiency`` (i), which says that for a
certificate given this way "the decided conditions are (E1) to (E3)".

WHY THE FORM EXISTS, IN ONE SENTENCE OF THE CLAIM. "Where even the blocks are
not declarable -- a pure block over non-orthogonal signal states carries square
roots of their weights -- the ensemble presentation is the form to use: it has
the purity and declares none of the numbers." The form unties a knot: a decoy
certificate needs the quotients ``p_x w_{x,t} / g_t`` and the amplitudes ``sqrt(g_t
g_t')``, binary64 holds neither, and snapping them leaves the family
``decoy/prop:tagging`` proves its identity for -- so the source identity would fail
ARITHMETICALLY, which no attestation can carry. So the route is to declare weighted
blocks.

WHAT IS DECIDED HERE AND WHAT IS A THEOREM
==========================================
DECIDED, and this list is all of it: (E1) every declared block Hermitian and
positive semidefinite, exactly; (E2) the block traces summing to ``p_x`` per
letter and the weights summing to one, in the declared orders and rounding
nowhere; (E3) the entrywise sum over ``X`` per sector rounding nowhere.

THEOREMS of the presentation, decided by NOTHING because there is no second
declared datum to compare them with: (SR1), (SR2), positivity of the blocks
``Psi_t``, the POVM condition and the purity of the blocks. ``def:srcert``:
"An implementation that 're-decides' (SR1) or the POVM condition on formed
numbers is re-deciding nothing and would introduce the rounding this form
exists to avoid." So NO FUNCTION OF THIS MODULE FORMS ``Psi_t`` OR
``M^{(t)}_x``, and none may be added: they carry square roots and quotients of
the declared numbers, and Lemma ``lem:ensemble-presentation`` (iii) says they
are "in general, not declarable".

WHAT IS FORMED AS NUMBERS. Exactly two objects, and both are transposes of
declared numbers, so both are exactly declarable whenever (E3) holds:

* ``tau^{(t)}_A``, the transpose of the sum of (E3)
  (:func:`alice_marginal_blocks`). Lemma (iii): "the entry ``(i, j)`` of
  ``tau^{(t)}_A`` is the entry ``(j, i)`` of the declared sum";
* ``N^{(t)}_x = (sigma^{v,(t)}_x)^T``, the transposed declared blocks
  (:func:`alice_operators`), which are "entrywise the declared numbers" and
  sum over ``x`` to ``tau^{(t)}_A`` -- Lemma (v). They are what a consumer
  reads of Alice's side WITHOUT a square root, and the declaration form that
  carries them instead of ``{M_x}`` is the consumer's.

(SR3) IS AN ATTESTATION IN THIS FORM AS IN EVERY OTHER. It is carried and
never decided; see :mod:`certiqs_key.transmitter.certificate`.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction

from certiqs_key.foundations.blocks import BlockKind, Label, SectorStructure
from certiqs_key.foundations.errors import MalformedInputError
from certiqs_key.foundations.exact import (
    Cx,
    Matrix,
    SummationVerdict,
    dimension,
    is_hermitian,
    is_positive_semidefinite,
    is_square,
    matrix_is_binary64,
    serialize_matrix,
    sum_in_declared_order,
    trace_in_row_order,
)
from certiqs_key.transmitter.certificate import RetentionAttestation
from certiqs_key.transmitter.reasons import Refusal, RefusalReason

__all__ = [
    "EnsemblePresentation",
    "EnsemblePresentationVerification",
    "alice_marginal_blocks",
    "alice_operators",
    "alice_sectors_of",
    "sector_sums",
    "transpose",
    "verify_ensemble_presentation",
]


def transpose(m: Matrix) -> Matrix:
    """Return ``m^T``, IN THE DECLARED BASIS and without conjugating.

    THE ONE OPERATION Lemma ``lem:ensemble-presentation`` PERFORMS ON NUMBERS.
    Its Eq. ``eq:enspres`` takes "transposition ``X -> X^T`` ... in these
    bases" -- the declared basis of ``S_t`` and the basis of the copy ``A_t``
    in the same order -- so the transpose is a RE-INDEXING of the declared
    entries and introduces no arithmetic at all, which is what makes
    ``tau^{(t)}_A`` exactly declarable whenever the declared sum is.

    IT IS NOT :func:`~certiqs_key.foundations.exact.conjugate_transpose`, and the
    difference is load-bearing: the lemma's proof uses ``(c)``, that
    transposition "commutes with the adjoint", precisely because the two are
    different maps. On a Hermitian block the transpose is the entrywise
    conjugate, and on a real one the two agree; on a general declared block
    they do not.

    WHY IT IS NOT IN :mod:`certiqs_key.foundations.exact`. The shared substrate
    exports the adjoint because every module needs it; the plain transpose is
    used by this one lemma and by nothing else in the tree, and that module's surface is
    fixed. Where a second module needs it, the move is a change to the shared format and
    not a second copy here.
    """
    if not m:
        raise MalformedInputError("a transpose is taken of a non-empty array")
    return tuple(tuple(m[j][i] for j in range(len(m))) for i in range(len(m[0])))


@dataclass(frozen=True)
class EnsemblePresentation:
    """The declared data of an ensemble presentation, AND NOTHING ELSE.

    ``def:srcert``: "the declared data are the matched sector structure
    ``(S_t)`` on ``A^v`` and the weighted virtual ensemble as block lists ...
    and NOTHING ELSE: no ``Psi``, no ``{M_x}``, no ``tau_A`` and no basis of
    ``A``". This record has three fields and two of them are those two; the
    third is the attestation (SR3), which every form carries and no form
    decides.

    THE ABSENT FIELDS ARE THE POINT. There is no ``psi_blocks`` slot, no
    ``alice_povm`` slot and no ``alice_marginal`` slot, so a declarer cannot
    supply one and an implementation cannot silently decide a condition against
    it. What a consumer reads instead is :func:`alice_marginal_blocks` and
    :func:`alice_operators`, both of which are transposes of the declared
    numbers.
    """

    #: ``(S_t)_{t in T}`` on ``A^v``, in the declared order, each with its
    #: declared orthonormal basis. Its block kind is ``proof_sector``: what it
    #: records is why a decomposition may be read off the declaration.
    virtual_sectors: SectorStructure
    #: ``sigma^{v,(t)}_x`` per letter, as a block list in the sector order.
    weighted_blocks: Mapping[Label, tuple[Matrix, ...]]
    #: (SR3) as supplied. Carried, never decided, never asserted: "(SR3) is the
    #: attestation it is in every form".
    retention_attestation: RetentionAttestation | None = None

    def __post_init__(self) -> None:
        """Refuse a presentation no condition of ``def:srcert`` can be read against."""
        if self.virtual_sectors.block_kind is not BlockKind.PROOF_SECTOR:
            raise MalformedInputError(
                "the sector structure of an ensemble presentation carries the "
                "block kind `proof_sector` (decoy/interface.yaml, the "
                "`sector_structure` row; def:source-link (e)); this one "
                f"carries {self.virtual_sectors.block_kind.value!r}"
            )
        for label, blocks in self.weighted_blocks.items():
            if len(blocks) != self.virtual_sectors.count:
                raise MalformedInputError(
                    f"the block list of {label!r} carries {len(blocks)} blocks "
                    f"against {self.virtual_sectors.count} declared sectors"
                )
            for position, (block, dim) in enumerate(
                zip(blocks, self.virtual_sectors.dims, strict=True)
            ):
                if not is_square(block) or dimension(block) != dim:
                    raise MalformedInputError(
                        f"the block of {label!r} at sector "
                        f"{self.virtual_sectors.labels[position]!r} is not a "
                        f"{dim} x {dim} array"
                    )

    @property
    def alice_sectors(self) -> SectorStructure:
        """Return the structure of ``A``, WHICH IS A COPY OF THE VIRTUAL ONE."""
        return alice_sectors_of(self)

    @property
    def alice_dim(self) -> int:
        """Return ``d_A = sum_t dim S_t``. ``A`` is not declared; this is defined."""
        return self.virtual_sectors.total_dim

    def as_machine_record(self) -> dict[str, object]:
        """Return the presentation as a machine record: THE DECLARED DATA ONLY.

        The sector structure and the weighted blocks, and nothing formed. It
        carries no ``tau_A``, no ``Psi`` and no ``{M_x}``: a consumer that wants
        the marginal forms it with :func:`alice_marginal_blocks` from these same
        declared numbers, which is the transpose of a sum and introduces
        nothing, and ``Psi`` and ``{M_x}`` are formed by nobody.

        JSON AS EMITTED: each block is written by
        :func:`~certiqs_key.foundations.exact.serialize_matrix`, exactly, so the
        licence that carries this record is serialisable as the transmitter
        emits it.
        """
        return {
            "virtual_sector_index_set": list(self.virtual_sectors.labels),
            "virtual_sector_dims": list(self.virtual_sectors.dims),
            "virtual_sector_block_kind": str(self.virtual_sectors.block_kind),
            "weighted_blocks": {
                label: [serialize_matrix(block) for block in blocks]
                for label, blocks in self.weighted_blocks.items()
            },
        }


def alice_sectors_of(presentation: EnsemblePresentation) -> SectorStructure:
    """Return the sector structure of ``A``, sector by sector a COPY of ``S_t``.

    ``lem:ensemble-presentation``: "For every ``t`` let ``A_t`` be a copy of
    ``S_t`` with basis in the same order", and ``A = (+)_t A_t``. So the
    matched pair is ONE structure read on both sides, which is what
    ``decoy/def:tagged-source`` (T5) means by "declared by being read off (T3)".

    NOTHING IS COMPRESSED AND NO RANK IS READ. ``prop:decoy-cert`` (iii):
    ``dim A_t = dim S_t`` "whatever the rank of the sector's marginal ... the
    retained system is as large as the declared virtual sector and no larger,
    and it is compressed by no one". An implementation that shrank ``A_t`` to
    the rank of ``tau^{(t)}_A`` would be performing a compression the
    contract does not make.
    """
    return presentation.virtual_sectors


def sector_sums(
    presentation: EnsemblePresentation, alphabet: Sequence[Label]
) -> tuple[SummationVerdict, ...]:
    """Return the (E3) accumulation per sector, in the declared order of ``X``.

    (E3): "for every ``t`` the sum ``sum_x sigma^{v,(t)}_x``, accumulated entry
    by entry in the declared order of ``X``, ROUNDS NOWHERE, so that its
    entries are binary64 numbers". The verdict carries both the exact total and
    the rounds-nowhere decision, and the caller reads the condition off it.
    """
    return tuple(
        sum_in_declared_order(
            [presentation.weighted_blocks[label][position] for label in alphabet]
        )
        for position in range(presentation.virtual_sectors.count)
    )


def alice_marginal_blocks(
    presentation: EnsemblePresentation, alphabet: Sequence[Label]
) -> tuple[Matrix, ...]:
    """Return ``tau^{(t)}_A``: THE TRANSPOSED SUM OF (E3), and nothing else.

    Eq. ``eq:enspres``: ``tau^{(t)}_S = sum_x sigma^{v,(t)}_x`` and
    ``tau^{(t)}_A = (tau^{(t)}_S)^T``. Lemma ``lem:ensemble-presentation``
    (iii) makes the entry ``(i, j)`` of the result the entry ``(j, i)`` of the
    declared sum, so THE ONLY OBJECT THIS FORM FORMS AS NUMBERS is exactly
    declarable whenever (E3) holds -- which is why (E3) is a decided condition
    and not an observation.

    IT IS NOT VALIDATED AGAINST ``S_=(A)`` HERE, and that is the interface's
    own rule rather than an omission: "IN AN ENSEMBLE PRESENTATION NONE OF THIS
    IS DECIDED: tau_A is not a declared datum there but the transpose of the
    sum of (E3), it is a state by lem:ensemble-presentation (i), and an
    implementation that validates it on formed numbers decides nothing while
    introducing a rounding" (the ``alice_marginal`` input row).
    """
    return tuple(
        transpose(verdict.total)
        for verdict in sector_sums(presentation, alphabet)
    )


def alice_operators(
    presentation: EnsemblePresentation,
) -> dict[Label, tuple[Matrix, ...]]:
    """Return ``N^{(t)}_x = (sigma^{v,(t)}_x)^T``: Alice's side WITHOUT a square root.

    Lemma ``lem:ensemble-presentation`` (v):
    ``(tau^{(t)}_A)^{1/2} M^{(t)}_x (tau^{(t)}_A)^{1/2} = (sigma^{v,(t)}_x)^T``
    "for every ``x`` and ``t``: the operators ``N^{(t)}_x`` are entrywise the
    declared numbers, and ``sum_x N^{(t)}_x = tau^{(t)}_A``".

    THESE ARE WHAT A CONSUMER RECEIVES INSTEAD OF ``{M_x}``, and the
    declaration form that carries them is the consuming module's. A consumer
    whose declaration carries ``{M_x}`` REFUSES a presentation -- which is
    fail-closed and is not a defect (``def:srcert``).
    """
    return {
        label: tuple(transpose(block) for block in blocks)
        for label, blocks in presentation.weighted_blocks.items()
    }


@dataclass(frozen=True)
class EnsemblePresentationVerification:
    """The verdicts of (E1), (E2) and (E3), with what produced them.

    NO VERDICT ON (SR1), (SR2), THE POVM CONDITION OR PURITY APPEARS HERE, and
    none may be added: they are theorems of the presentation
    (``lem:ensemble-presentation``), so a field here would report a decision
    that was not taken, on numbers that were not formed.
    """

    #: (E1) per ``(letter, sector position)`` that fails, in the order decided.
    e1_failures: tuple[tuple[Label, Label], ...]
    #: (E2) on the per-letter block-trace sums and on ``sum_x p_x``.
    e2_holds: bool
    e2_detail: str | None
    #: (E3) per sector, in the declared order.
    e3_verdicts: tuple[SummationVerdict, ...]
    #: The sectors at which the (E3) accumulation rounds.
    e3_failures: tuple[Label, ...]
    #: A declared block entry that is not a binary64 number, named
    #: ``(letter, sector)``. The number model of ``def:source-spec`` makes a
    #: DECLARED entry binary64 by definition; this catches a caller that hands
    #: over numbers it FORMED, which is the decoy emission's own refusal
    #: (``formed_entry_not_declarable``) taken one step earlier.
    undeclarable_entries: tuple[tuple[Label, Label], ...]

    @property
    def passes(self) -> bool:
        """Whether (E1), (E2) and (E3) all hold on the declared blocks."""
        return (
            not self.e1_failures
            and self.e2_holds
            and not self.e3_failures
            and not self.undeclarable_entries
        )

    def refusal(self) -> Refusal | None:
        """Return the refusal a failing presentation produces, NAMING THE SECTOR.

        Two strings and the division between them is the interface's, not a
        preference of this file. ``formed_entry_not_declarable`` is for a
        quantity a declaration FORMS that is not admissible as declared data;
        ``ensemble_presentation_not_admissible`` is for (E1), (E2) or (E3)
        failing on data that IS declarable.

        (E3) is decided here and reported as (E3),
        ``ensemble_presentation_not_admissible``, naming the sector;
        ``formed_entry_not_declarable`` is kept for the entries a declarer
        forms before it declares them (``decoy/req:exact-decoy-blocks``), which
        is where :mod:`certiqs_key.transmitter.decoy.emit` fires it.
        """
        if self.undeclarable_entries:
            letter, sector = self.undeclarable_entries[0]
            return Refusal(
                reason=RefusalReason.FORMED_ENTRY_NOT_DECLARABLE,
                detail=(
                    f"the block of {letter!r} at sector {sector!r} carries an "
                    "entry that is not a binary64 number; it is REFUSED AND "
                    "NEVER ROUNDED, rounding it would change which ensemble is "
                    "declared and with it the ensemble every identity of the "
                    "declaration is asserted of"
                ),
            )
        if self.e1_failures:
            letter, sector = self.e1_failures[0]
            return Refusal(
                reason=RefusalReason.ENSEMBLE_PRESENTATION_NOT_ADMISSIBLE,
                detail=(
                    f"(E1) fails: the declared block of {letter!r} at sector "
                    f"{sector!r} is not Hermitian and positive semidefinite by "
                    "an exact decision"
                ),
            )
        if not self.e2_holds:
            return Refusal(
                reason=RefusalReason.ENSEMBLE_PRESENTATION_NOT_ADMISSIBLE,
                detail=f"(E2) fails: {self.e2_detail}",
            )
        if self.e3_failures:
            return Refusal(
                reason=RefusalReason.ENSEMBLE_PRESENTATION_NOT_ADMISSIBLE,
                detail=(
                    f"(E3) fails at sector {self.e3_failures[0]!r}: the sum "
                    "over X, accumulated entry by entry in the declared order, "
                    "rounds, so its entries are not binary64 numbers"
                ),
            )
        return None


def verify_ensemble_presentation(
    presentation: EnsemblePresentation,
    alphabet: Sequence[Label],
    weights: Mapping[Label, Fraction],
) -> EnsemblePresentationVerification:
    """Decide (E1), (E2) and (E3). NOTHING ELSE IS DECIDED OF A PRESENTATION.

    ``thm:certificate-sufficiency`` (i): "For a certificate given by an ensemble
    presentation the decided conditions are (E1) to (E3) of Definition def:srcert,
    equally finite and exact, and the conditions of the block form hold of the defined
    certificate by Lemma lem:ensemble-presentation (i) WITHOUT BEING DECIDED."

    ``weights`` is the specification's declared ``p_x``. (E2) compares it with
    the sum of the block traces, which is where the declared weights and the
    declared blocks are tied together; without it a presentation could declare
    blocks of one ensemble and weights of another.
    """
    sectors = presentation.virtual_sectors
    e1_failures: list[tuple[Label, Label]] = []
    undeclarable: list[tuple[Label, Label]] = []
    for label in alphabet:
        if label not in presentation.weighted_blocks:
            raise MalformedInputError(
                f"the presentation declares no block list at {label!r}; the "
                "weighted virtual ensemble is indexed by the declared alphabet"
            )
        for position, block in enumerate(presentation.weighted_blocks[label]):
            sector = sectors.labels[position]
            if not matrix_is_binary64(block):
                undeclarable.append((label, sector))
                continue
            if not is_hermitian(block) or not is_positive_semidefinite(block):
                e1_failures.append((label, sector))

    e2_holds, e2_detail = _decide_e2(presentation, alphabet, weights)
    verdicts = sector_sums(presentation, alphabet)
    e3_failures = tuple(
        sectors.labels[position]
        for position, verdict in enumerate(verdicts)
        if not verdict.rounds_nowhere
    )
    return EnsemblePresentationVerification(
        e1_failures=tuple(e1_failures),
        e2_holds=e2_holds,
        e2_detail=e2_detail,
        e3_verdicts=verdicts,
        e3_failures=e3_failures,
        undeclarable_entries=tuple(undeclarable),
    )


def _decide_e2(
    presentation: EnsemblePresentation,
    alphabet: Sequence[Label],
    weights: Mapping[Label, Fraction],
) -> tuple[bool, str | None]:
    """Decide (E2): ``p_x = sum_t tr sigma^{v,(t)}_x`` and ``sum_x p_x = 1``.

    BOTH SUMS ARE ACCUMULATED IN THEIR DECLARED ORDERS AND BOTH MUST ROUND
    NOWHERE -- the sector order for the inner one, the declared order of ``X``
    for the outer -- which is what "the sums formed in the declared orders and
    rounding nowhere" says. A trace is itself an accumulation, over the row
    index, so it is taken with
    :func:`~certiqs_key.foundations.exact.trace_in_row_order` and its rounding
    decided too: the declared order of a trace is the row index everywhere in
    this module (the ``summation_order`` convention).
    """
    running = Fraction(0)
    weight_sum_rounds_nowhere = True
    for label in alphabet:
        if label not in weights:
            return False, f"no declared weight p_x at {label!r}"
        blocks = presentation.weighted_blocks[label]
        trace_total = Cx(Fraction(0), Fraction(0))
        for position, block in enumerate(blocks):
            accumulated = trace_in_row_order(block)
            if not accumulated.rounds_nowhere:
                sector = presentation.virtual_sectors.labels[position]
                return False, (
                    f"the trace of the block of {label!r} at sector "
                    f"{sector!r}, accumulated over the row index, rounds"
                )
            if not _addition_is_exact(trace_total, accumulated.value):
                return False, (
                    f"the sum over the sectors of the block traces of {label!r}, "
                    "accumulated in the declared sector order, rounds"
                )
            trace_total = trace_total + accumulated.value
        if trace_total != Cx(weights[label], Fraction(0)):
            return False, (
                f"p_{label!r} is the declared {weights[label]} while the block "
                f"traces sum to {trace_total}"
            )
        if not _addition_is_exact(
            Cx(running, Fraction(0)), Cx(weights[label], Fraction(0))
        ):
            weight_sum_rounds_nowhere = False
        running += weights[label]
    if running != 1:
        return False, f"the declared weights sum to {running} and not to 1"
    if not weight_sum_rounds_nowhere:
        return False, "the weight sum, accumulated in the declared order of X, rounds"
    return True, None


def _addition_is_exact(left: Cx, right: Cx) -> bool:
    """Whether the binary64 addition of two exact scalars is exact, part by part."""
    from certiqs_key.foundations.exact import addition_rounds_nowhere

    return addition_rounds_nowhere(left, right)
