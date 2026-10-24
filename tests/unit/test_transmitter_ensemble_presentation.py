"""The ensemble presentation: what it decides, what it defines, what it refuses.

``transmitter/def:srcert`` (the third form, conditions (E1) to (E3)) and
``transmitter/lem:ensemble-presentation`` (the objects Eq. ``eq:enspres``
defines and what part (v) gives a consumer).

EVERY TEST HERE IS A `contract` TEST: each exercises a condition or a conclusion
of one of those two claims and would fail if it were false. The two halves the
file keeps apart, because the claims do:

* WHAT IS DECIDED -- (E1), (E2), (E3) -- one refusal test each;
* WHAT IS A THEOREM -- (SR1), (SR2), positivity of ``Psi_t``, the POVM condition
  and purity -- which is tested by asserting that NOTHING decides them: the
  verification record carries no field for them and the emitted artefact carries
  no ``{M_x}``.

THE DEGENERATE CASE IS THE LAST TEST AND IT IS THE ONE THAT TIES THE BATCH TO
THE ACCEPTED INSTANCE: today's qubit BB84 pure-form declaration, re-declared as
an ensemble presentation, gives the same ``tau_A`` and
``N_x = tau_A^{1/2} M_x tau_A^{1/2}`` entry for entry.
"""

from __future__ import annotations

import json
from fractions import Fraction as F

import pytest

from certiqs_key.foundations.blocks import BlockKind, SectorStructure
from certiqs_key.foundations.errors import MalformedInputError
from certiqs_key.foundations.exact import (
    deserialize_matrix,
    equal,
    identity,
    is_hermitian,
    matrix,
    scale,
)
from certiqs_key.transmitter.artifact import (
    SourceSpecification,
    TransmitterResult,
    emit_artifact,
)
from certiqs_key.transmitter.presentation import (
    EnsemblePresentation,
    alice_marginal_blocks,
    alice_operators,
    sector_sums,
    transpose,
    verify_ensemble_presentation,
)
from certiqs_key.transmitter.reasons import (
    CertificateForm,
    RefusalReason,
    SourceMode,
)

pytestmark = pytest.mark.contract

HALF = F(1, 2)
QUARTER = F(1, 4)

P_Z0 = matrix(((1, 0), (0, 0)))
P_Z1 = matrix(((0, 0), (0, 1)))
P_X0 = matrix(((HALF, HALF), (HALF, HALF)))
P_X1 = matrix(((HALF, -HALF), (-HALF, HALF)))

ALPHABET = ("(Z,0)", "(Z,1)", "(X,0)", "(X,1)")
STATES = {"(Z,0)": P_Z0, "(Z,1)": P_Z1, "(X,0)": P_X0, "(X,1)": P_X1}
WEIGHTS = dict.fromkeys(ALPHABET, QUARTER)

#: The one-sector structure, which is the DEFAULT of ``def:source-spec`` and the
#: structure of the degenerate case. A presentation may declare one sector: the
#: form is about what is DECLARED (the ensemble) and not about how many sectors
#: there are.
ONE_SECTOR = SectorStructure(
    labels=("A",), dims=(2,), block_kind=BlockKind.PROOF_SECTOR
)

#: Two sectors, so that the per-sector conditions are exercised on a structure
#: that has more than one of them: a qubit sector and a one-dimensional flag.
TWO_SECTORS = SectorStructure(
    labels=("q", "flag"), dims=(2, 1), block_kind=BlockKind.PROOF_SECTOR
)


def _degenerate(**overrides: object) -> EnsemblePresentation:
    """Return the one-sector presentation of the qubit BB84 ensemble."""
    fields: dict[str, object] = {
        "virtual_sectors": ONE_SECTOR,
        "weighted_blocks": {
            label: (scale(WEIGHTS[label], STATES[label]),) for label in ALPHABET
        },
    }
    fields.update(overrides)
    return EnsemblePresentation(**fields)  # type: ignore[arg-type]


def _two_sector() -> EnsemblePresentation:
    """Return a two-sector presentation: half the weight quantum, half on a flag."""
    return EnsemblePresentation(
        virtual_sectors=TWO_SECTORS,
        weighted_blocks={
            label: (
                scale(WEIGHTS[label] / 2, STATES[label]),
                matrix(((WEIGHTS[label] / 2,),)),
            )
            for label in ALPHABET
        },
    )


# ---------------------------------------------------------------------------
#  (E1), (E2), (E3): the three decided conditions, one refusal each
# ---------------------------------------------------------------------------


def test_e1_refuses_a_block_that_is_not_positive_semidefinite() -> None:
    """(E1): "every block Hermitian and positive semidefinite, decided exactly"."""
    presentation = _degenerate(
        weighted_blocks={
            **{label: (scale(WEIGHTS[label], STATES[label]),) for label in ALPHABET},
            "(Z,0)": (matrix(((QUARTER, HALF), (HALF, QUARTER))),),
        }
    )
    refusal = verify_ensemble_presentation(
        presentation, ALPHABET, WEIGHTS
    ).refusal()
    assert refusal is not None
    assert refusal.reason is RefusalReason.ENSEMBLE_PRESENTATION_NOT_ADMISSIBLE
    # THE REPORT NAMES THE SECTOR AND THE LETTER, which is what the row asks of
    # a per-sector condition.
    assert "(E1)" in refusal.detail
    assert "'A'" in refusal.detail
    assert "'(Z,0)'" in refusal.detail


def test_e1_accepts_a_singular_block() -> None:
    """A rank-one weighted member is SINGULAR and is admissible.

    The exact positivity decision "is decided at zero and at no window", so a
    singular operator is accepted -- which every declared block of a flag sector
    and every rank-one signal dyad is.
    """
    verification = verify_ensemble_presentation(_degenerate(), ALPHABET, WEIGHTS)
    assert verification.passes
    assert verification.e1_failures == ()


def test_e2_refuses_a_block_trace_sum_that_is_not_the_declared_weight() -> None:
    """(E2): ``p_x = sum_t tr sigma^{v,(t)}_x`` for every ``x``.

    It is what ties the declared weights to the declared blocks: without it a
    presentation could declare the blocks of one ensemble and the weights of
    another, and no other condition of the form would see it.
    """
    presentation = _degenerate()
    verification = verify_ensemble_presentation(
        presentation, ALPHABET, {**WEIGHTS, "(X,1)": F(1, 8)}
    )
    refusal = verification.refusal()
    assert refusal is not None
    assert refusal.reason is RefusalReason.ENSEMBLE_PRESENTATION_NOT_ADMISSIBLE
    assert "(E2)" in refusal.detail


def test_e2_refuses_weights_that_do_not_sum_to_one() -> None:
    """(E2)'s second half: ``sum_x p_x = 1`` in the declared order."""
    blocks = {
        label: (scale(F(1, 8), STATES[label]),) for label in ALPHABET
    }
    verification = verify_ensemble_presentation(
        _degenerate(weighted_blocks=blocks),
        ALPHABET,
        {label: F(1, 8) for label in ALPHABET},
    )
    refusal = verification.refusal()
    assert refusal is not None
    assert "sum to 1/2" in refusal.detail


def test_e3_refuses_a_sector_sum_that_rounds() -> None:
    """(E3): the entrywise sum over ``X`` per sector ROUNDS NOWHERE.

    THE WITNESS PUTS THE ROUNDING IN AN OFF-DIAGONAL ENTRY, which is what makes
    it a test of (E3) rather than of (E2): every declared entry is a binary64
    number, every block trace is exact, the weights accumulate exactly to one,
    and only the ENTRYWISE sum at position ``(0,1)`` rounds --
    ``1/4 + 2^-55 = (2^53 + 1)/2^55`` needs 54 significand bits. So (E1) and
    (E2) hold and (E3) is the one condition that fails, which is what the report
    must name.
    """
    tiny = F(1, 2**55)
    alphabet = ("a", "b", "c")
    weights = {"a": HALF, "b": QUARTER, "c": QUARTER}
    eighth = F(1, 8)
    presentation = EnsemblePresentation(
        virtual_sectors=SectorStructure(
            labels=("s",), dims=(2,), block_kind=BlockKind.PROOF_SECTOR
        ),
        weighted_blocks={
            "a": (matrix(((QUARTER, QUARTER), (QUARTER, QUARTER))),),
            "b": (matrix(((eighth, tiny), (tiny, eighth))),),
            "c": (matrix(((eighth, 0), (0, eighth))),),
        },
    )
    verification = verify_ensemble_presentation(presentation, alphabet, weights)
    assert verification.e1_failures == ()
    assert verification.e2_holds
    refusal = verification.refusal()
    assert refusal is not None
    assert refusal.reason is RefusalReason.ENSEMBLE_PRESENTATION_NOT_ADMISSIBLE
    assert "(E3)" in refusal.detail
    assert verification.e3_failures == ("s",)


def test_a_block_entry_that_is_not_binary64_is_refused_and_never_rounded() -> None:
    """``formed_entry_not_declarable``: refused, and the entry is not moved.

    ``cor:emitted-decoy`` (iv): an entry that is not a binary64 number "is
    REFUSED WHEN IT IS NOT; it is never rounded, because rounding an entry of a
    declared block would change which ensemble is declared and so which ensemble
    the source identity of (ii) is asserted of".
    """
    presentation = EnsemblePresentation(
        virtual_sectors=SectorStructure(
            labels=("s",), dims=(1,), block_kind=BlockKind.PROOF_SECTOR
        ),
        weighted_blocks={"a": (matrix(((F(1, 3),),)),)},
    )
    refusal = verify_ensemble_presentation(
        presentation, ("a",), {"a": F(1, 3)}
    ).refusal()
    assert refusal is not None
    assert refusal.reason is RefusalReason.FORMED_ENTRY_NOT_DECLARABLE
    # NOT ROUNDED: the declared entry is still 1/3 after the refusal.
    assert presentation.weighted_blocks["a"][0][0][0].re == F(1, 3)


# ---------------------------------------------------------------------------
#  What is a THEOREM is decided by nothing
# ---------------------------------------------------------------------------


def test_the_verification_record_carries_no_verdict_on_a_theorem() -> None:
    """(SR1), (SR2), the POVM condition and purity are decided by NOTHING.

    ``def:srcert``: "an implementation that re-decides them on formed numbers is
    introducing the rounding the form exists to avoid". The structural check is
    that the record has no field for them; a field would be a decision taken.
    """
    from certiqs_key.transmitter.presentation import EnsemblePresentationVerification

    fields = set(EnsemblePresentationVerification.__dataclass_fields__)
    for forbidden in ("sr1", "sr2", "povm", "purity", "idempotent"):
        assert not any(forbidden in name for name in fields), fields


def test_a_presentation_declares_no_psi_no_povm_and_no_marginal() -> None:
    """The three absent slots of ``def:srcert``'s third form, structurally."""
    fields = set(EnsemblePresentation.__dataclass_fields__)
    assert fields == {
        "virtual_sectors",
        "weighted_blocks",
        "retention_attestation",
    }


def test_a_specification_may_not_declare_a_marginal_beside_a_presentation() -> None:
    """``tau_A`` is FORMED, not declared: a declared one is a second carrier."""
    with pytest.raises(MalformedInputError, match="TRANSPOSE OF"):
        emit_artifact(
            SourceSpecification(
                signal_alphabet=ALPHABET,
                transmitted_dim=2,
                signal_weights=WEIGHTS,
                signal_states=STATES,
                source_mode_request=SourceMode.TRUSTED,
                ensemble_presentation=_degenerate(),
                alice_marginal=scale(HALF, identity(2)),
            )
        )


def test_a_specification_may_not_declare_a_povm_beside_a_presentation() -> None:
    """``{M_x}`` is DEFINED and the POVM condition is a theorem."""
    with pytest.raises(MalformedInputError, match="declares no POVM"):
        emit_artifact(
            SourceSpecification(
                signal_alphabet=ALPHABET,
                transmitted_dim=2,
                signal_weights=WEIGHTS,
                signal_states=STATES,
                source_mode_request=SourceMode.TRUSTED,
                ensemble_presentation=_degenerate(),
                alice_povm=dict(STATES),
            )
        )


def test_a_presentation_is_trusted_mode_only() -> None:
    """A certificate in ANY form belongs to the trusted mode alone."""
    with pytest.raises(MalformedInputError, match="TRUSTED MODE ONLY"):
        emit_artifact(
            SourceSpecification(
                signal_alphabet=ALPHABET,
                transmitted_dim=2,
                signal_weights=WEIGHTS,
                signal_states=STATES,
                ensemble_presentation=_degenerate(),
            )
        )


# ---------------------------------------------------------------------------
#  lem:ensemble-presentation: what is formed, and what a consumer reads
# ---------------------------------------------------------------------------


def test_tau_a_is_the_transposed_sum_entry_for_entry() -> None:
    """Part (iii): the marginal is the transposed sum, entry for entry.

    "the entry ``(i, j)`` of ``tau^{(t)}_A`` is the entry ``(j, i)`` of the
    declared sum ``tau^{(t)}_S``".
    """
    presentation = _two_sector()
    sums = sector_sums(presentation, ALPHABET)
    formed = alice_marginal_blocks(presentation, ALPHABET)
    for verdict, block in zip(sums, formed, strict=True):
        assert equal(block, transpose(verdict.total))


def test_alice_sectors_are_a_copy_of_the_virtual_ones_and_nothing_is_compressed() -> (
    None
):
    """(T5) and ``prop:decoy-cert`` (iii): ``dim A_t = dim S_t`` whatever the rank.

    The two-sector presentation's first sector has a RANK-TWO marginal in a
    two-dimensional space and its second a rank-one marginal in a
    one-dimensional one; neither dimension is read off a rank.
    """
    presentation = _two_sector()
    assert presentation.alice_sectors.dims == presentation.virtual_sectors.dims
    assert presentation.alice_sectors.labels == presentation.virtual_sectors.labels
    assert presentation.alice_dim == 3


def test_the_operators_a_consumer_reads_are_the_transposed_declared_blocks() -> None:
    """Part (v): ``N^{(t)}_x`` is "entrywise the declared numbers"."""
    presentation = _two_sector()
    operators = alice_operators(presentation)
    for label in ALPHABET:
        for declared, read in zip(
            presentation.weighted_blocks[label], operators[label], strict=True
        ):
            assert equal(read, transpose(declared))


def test_the_transpose_is_not_the_adjoint() -> None:
    """The lemma's fact (c) needs the two to be different maps, and they are."""
    from certiqs_key.foundations.exact import Cx, conjugate_transpose

    complex_block = ((Cx(F(0), F(1)),),)
    assert not equal(transpose(complex_block), conjugate_transpose(complex_block))


def test_tau_a_is_the_transpose_and_neither_the_sum_nor_its_adjoint() -> None:
    """``tau^{(t)}_A`` is the TRANSPOSE of the sum, and the test can tell.

    A REAL and SYMMETRIC witness would let :func:`transpose` be replaced by the
    identity -- or by the adjoint -- with the whole suite green, and the one
    operation ``lem:ensemble-presentation`` performs on numbers would be pinned
    by nothing.

    A HERMITIAN COMPLEX BLOCK SEPARATES ALL THREE. For
    ``sigma = [[1/2, i/4], [-i/4, 1/2]]`` -- Hermitian, positive semidefinite
    (its eigenvalues are ``1/2 +/- 1/4``), of unit trace, every entry a binary64
    Gaussian rational -- the transpose is ``[[1/2, -i/4], [i/4, 1/2]]``, which
    is neither ``sigma`` itself nor its adjoint, the adjoint of a Hermitian
    operator being itself. Eq. ``eq:enspres`` takes the transpose "in these
    bases", and part (iii) makes entry ``(i, j)`` of the marginal entry
    ``(j, i)`` of the sum; a consumer handed the sum where the transpose was
    written would read a different operator.
    """
    from certiqs_key.foundations.exact import (
        Cx,
        conjugate_transpose,
        is_positive_semidefinite,
    )

    quarter_i = Cx(F(0), F(1, 4))
    half = Cx(F(1, 2), F(0))
    block = ((half, quarter_i), (-quarter_i, half))
    assert is_hermitian(block)
    assert is_positive_semidefinite(block)
    presentation = EnsemblePresentation(
        virtual_sectors=ONE_SECTOR,
        weighted_blocks={"only": (block,)},
    )
    verification = verify_ensemble_presentation(presentation, ("only",), {"only": F(1)})
    assert verification.passes
    formed = alice_marginal_blocks(presentation, ("only",))[0]
    assert equal(formed, transpose(block))
    # NEITHER THE SUM ITSELF nor its adjoint: each would pass a test written on
    # a real symmetric witness, and neither is what eq:enspres writes.
    assert not equal(formed, block)
    assert not equal(formed, conjugate_transpose(block))
    # AND PART (v) SEPARATES THEM TOO, on the same block.
    assert equal(alice_operators(presentation)["only"][0], transpose(block))


def test_a_complex_hermitian_block_is_admissible_data() -> None:
    """The exact substrate is the GAUSSIAN rationals, and (E1) to (E3) read them.

    Recorded beside the test above because the witness there depends on it: a
    declared block may be complex, so the transpose and the adjoint are two maps
    on admissible declared data and not only on a counterexample.
    """
    from certiqs_key.foundations.exact import Cx

    block = ((Cx(F(1, 2), F(0)), Cx(F(0), F(1, 4))),
             (Cx(F(0), F(-1, 4)), Cx(F(1, 2), F(0))))
    verification = verify_ensemble_presentation(
        EnsemblePresentation(
            virtual_sectors=ONE_SECTOR, weighted_blocks={"only": (block,)}
        ),
        ("only",),
        {"only": F(1)},
    )
    assert verification.e1_failures == ()
    assert verification.undeclarable_entries == ()
    assert verification.passes


# ---------------------------------------------------------------------------
#  The emitted artefact
# ---------------------------------------------------------------------------


def _two_sector_states() -> dict[str, object]:
    """Return ``rho_x`` on the three-dimensional ``A'`` of the two-sector case.

    THE SEGMENT IS EMPTY, SO ``A^v = A'`` AND ``rho^v_x = rho_x``: the specified
    ensemble a presentation with no source link is declared beside is the
    normalised direct sum of its own blocks. Here every entry of that quotient
    is dyadic, so the specification is declarable as matrices; that is a
    property of this fixture and not of the form -- ``rho^v_x = sigma^v_x/p_x``
    is a quotient in general, which is why the artefact emits weighted members.
    """
    from certiqs_key.foundations.exact import direct_sum

    return {
        label: direct_sum(
            [
                scale(F(1, 2), STATES[label]),
                matrix(((F(1, 2),),)),
            ]
        )
        for label in ALPHABET
    }


def _emit(presentation: EnsemblePresentation) -> TransmitterResult:
    two_sector = presentation.virtual_sectors.count > 1
    return emit_artifact(
        SourceSpecification(
            signal_alphabet=ALPHABET,
            transmitted_dim=presentation.virtual_sectors.total_dim,
            signal_weights=WEIGHTS,
            signal_states=_two_sector_states() if two_sector else STATES,
            source_mode_request=SourceMode.TRUSTED,
            ensemble_presentation=presentation,
        )
    )


def test_the_emitted_artefact_carries_the_form_the_sector_map_and_the_operators() -> (
    None
):
    """The three output rows of the general declaration, on a presentation."""
    artifact = _emit(_two_sector()).require()
    assert artifact.certificate_form is CertificateForm.ENSEMBLE_PRESENTATION
    assert artifact.alice_sector_map == TWO_SECTORS
    assert artifact.virtual_sector_map == TWO_SECTORS
    assert artifact.alice_ensemble_operators is not None
    # {M_x} IS NOT EMITTED: it is defined, carries square roots and quotients,
    # and is formed by no one.
    assert artifact.alice_povm == {}
    # Nor is rho^v_x, which is a quotient; the weighted members travel instead.
    assert artifact.virtual_ensemble_states == {}
    assert artifact.virtual_ensemble_blocks is not None
    assert artifact.source_mode is SourceMode.TRUSTED


def test_the_licence_names_the_form_and_carries_the_declared_blocks() -> None:
    """The licence names the form and carries what was decided on.

    The ``source_replacement_license`` row: with a presentation the record
    carries the DECLARED BLOCKS and the sector structure, and not ``Psi``.
    """
    artifact = _emit(_two_sector()).require()
    licence = artifact.source_replacement_license
    assert licence is not None
    assert licence.form is CertificateForm.ENSEMBLE_PRESENTATION
    assert licence.certificate is None
    assert licence.block_certificate is None
    assert licence.presentation is not None
    record = licence.as_machine_record()
    assert record["form"] == "ensemble_presentation"
    assert "ensemble_presentation" in record
    assert record["certificate"] is None
    # JSON as emitted (the interface's ``wire_form``), the declared blocks
    # read back exactly.
    assert json.loads(json.dumps(record)) == record
    blocks = record["ensemble_presentation"]["weighted_blocks"]
    for label, declared in licence.presentation.weighted_blocks.items():
        read = [deserialize_matrix(block) for block in blocks[label]]
        assert all(
            equal(got, want) for got, want in zip(read, declared, strict=True)
        ), label


def test_the_ledger_is_the_cores_rule_in_force() -> None:
    """This matrix-specified trusted ensemble carries A-ENS/A-SEQ/A-SRC.

    A model-declared decoy instead carries A-WCP in place of A-ENS through its
    separate admitting-module path.
    """
    artifact = _emit(_two_sector()).require()
    assert artifact.assumption_ledger == (
        "source_ensemble",
        "sequential_round_model",
        "source_replacement_license",
    )


# ---------------------------------------------------------------------------
#  THE DEGENERATE CASE
# ---------------------------------------------------------------------------


def test_the_qubit_bb84_declaration_and_its_presentation_agree() -> None:
    """The pure-form BB84 declaration, re-declared as a presentation.

    THE TEST THE DESIGN RULE ASKS FOR. The accepted qubit instance
    declares ``tau_A = 1_A/2``, ``Psi = |Phi+><Phi+|`` and
    ``M_{(b,a)} = p^A_b |conj(a^b)><conj(a^b)|``; the same ensemble declared as
    weighted blocks gives, through ``lem:ensemble-presentation``:

    * the SAME ``tau_A``, exactly -- it is the transpose of ``sum_x p_x rho_x``,
      which is ``1_A/2``; and
    * ``N_x = tau_A^{1/2} M_x tau_A^{1/2}`` ENTRY FOR ENTRY, which part (v)
      asserts. The check is exact because ``tau_A`` is a MULTIPLE OF THE
      IDENTITY here: ``tau_A^{1/2} = 2^{-1/2} 1_A`` carries a square root, but
      the conjugation ``tau_A^{1/2} M tau_A^{1/2}`` is ``M/2``, which is exactly
      representable -- so the identity is decided on declared numbers and not on
      a rounded image of one.
    """
    from instances.bb84.specification import bb84_specification

    accepted = bb84_specification(HALF, HALF, HALF, HALF)
    artifact = accepted.source.artifact
    povm = dict(artifact.alice_povm)
    declared_marginal = artifact.alice_marginal
    assert declared_marginal is not None

    presentation = EnsemblePresentation(
        virtual_sectors=ONE_SECTOR,
        weighted_blocks={
            label: (
                scale(
                    artifact.virtual_ensemble_weights[label],
                    artifact.virtual_ensemble_states[label],
                ),
            )
            for label in artifact.signal_alphabet
        },
    )
    formed = alice_marginal_blocks(presentation, artifact.signal_alphabet)
    assert equal(formed[0], declared_marginal)
    assert equal(formed[0], scale(HALF, identity(2)))

    operators = alice_operators(presentation)
    for label in artifact.signal_alphabet:
        # tau_A^{1/2} M_x tau_A^{1/2} = M_x / 2, tau_A being 1_A/2.
        assert equal(operators[label][0], scale(HALF, povm[label]))
