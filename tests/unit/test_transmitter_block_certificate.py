"""The BLOCK form of ``def:srcert``: per-block conditions, and NO purity.

``transmitter/def:srcert`` (the block form, Eq. ``eq:srblock``) and
``transmitter/thm:certificate-sufficiency`` (i), which lists what is decided of it: "per
block, one comparison of ``(d_{A_t} dim S_t)^2`` entries for Hermiticity and one exact
decision of positive semidefiniteness -- a symmetric elimination over the
Gaussian rationals in which A NEGATIVE PIVOT REFUSES THE BLOCK AND A ZERO PIVOT
REQUIRES ITS WHOLE ROW AND COLUMN TO VANISH -- and one accumulated trace over
all blocks".

THE WORKED CERTIFICATE. Two sectors of weights one half each, which is the
smallest case in which "the source that first draws ``t`` with probability
``tr Psi_t`` and then prepares ``Psi_t / tr Psi_t``" is not a pure state on the
whole space: a qubit sector carrying half the weight on the maximally entangled
operator, and a one-dimensional flag sector carrying the other half. Every entry
is dyadic, which is the declarability the form exists for.

WHAT IS NOT TESTED HERE BECAUSE IT IS NOT A CONDITION: purity, globally or per
block. ``def:srcert``: "There is no idempotence condition there and no consumer
may add one." The structural test for that is at the bottom.
"""

from __future__ import annotations

import json
from dataclasses import replace
from fractions import Fraction as F

import pytest

from certiqs_key.foundations.blocks import BlockKind, SectorStructure
from certiqs_key.foundations.errors import MalformedInputError
from certiqs_key.foundations.exact import (
    Cx,
    deserialize_matrix,
    direct_sum,
    equal,
    matrix,
    scale,
)
from certiqs_key.transmitter.artifact import SourceSpecification, emit_artifact
from certiqs_key.transmitter.certificate import (
    BlockFormCertificate,
    verify_block_certificate,
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
ALPHABET = ("x0", "x1")

SECTORS = SectorStructure(
    labels=("q", "flag"), dims=(2, 1), block_kind=BlockKind.PROOF_SECTOR
)

#: ``Psi_q = (1/2) |Phi+><Phi+|``: the maximally entangled operator carrying
#: HALF the weight. Every entry is ``1/4`` and is a binary64 number, which is
#: what ``def:srcert``'s operator-not-vector paragraph is about.
PSI_Q = matrix(
    (
        (QUARTER, 0, 0, QUARTER),
        (0, 0, 0, 0),
        (0, 0, 0, 0),
        (QUARTER, 0, 0, QUARTER),
    )
)
PSI_FLAG = matrix(((HALF,),))

POVM_BLOCKS = {
    "x0": (P_Z0, matrix(((HALF,),))),
    "x1": (P_Z1, matrix(((HALF,),))),
}

VIRTUAL_BLOCKS = {
    "x0": (scale(QUARTER, P_Z0), matrix(((QUARTER,),))),
    "x1": (scale(QUARTER, P_Z1), matrix(((QUARTER,),))),
}
VIRTUAL_WEIGHTS = {"x0": HALF, "x1": HALF}


def _certificate(**overrides: object) -> BlockFormCertificate:
    fields: dict[str, object] = {
        "alice_sectors": SECTORS,
        "virtual_sectors": SECTORS,
        "alice_marginal_blocks": (scale(QUARTER, matrix(((1, 0), (0, 1)))), PSI_FLAG),
        "psi_blocks": (PSI_Q, PSI_FLAG),
        "virtual_weights": dict(VIRTUAL_WEIGHTS),
        "virtual_blocks": {label: tuple(VIRTUAL_BLOCKS[label]) for label in ALPHABET},
    }
    fields.update(overrides)
    return BlockFormCertificate(**fields)  # type: ignore[arg-type]


def _specification(certificate: BlockFormCertificate) -> SourceSpecification:
    """Return the specification the certificate belongs to, segment EMPTY.

    At ``L_s = 0`` the virtual ensemble IS the specified one, so ``rho_x`` is the
    normalised direct sum of the certificate's own virtual blocks.
    """
    states = {
        label: direct_sum(
            [scale(1 / VIRTUAL_WEIGHTS[label], block) for block in blocks]
        )
        for label, blocks in certificate.virtual_blocks.items()
    }
    return SourceSpecification(
        signal_alphabet=ALPHABET,
        transmitted_dim=3,
        signal_weights=dict(VIRTUAL_WEIGHTS),
        signal_states=states,
        alice_dim=3,
        alice_sectors=SECTORS,
        alice_povm_blocks=dict(POVM_BLOCKS),
        source_mode_request=SourceMode.TRUSTED,
        block_certificate=certificate,
    )


# ---------------------------------------------------------------------------
#  The conditions, one at a time
# ---------------------------------------------------------------------------


def test_the_worked_block_certificate_verifies() -> None:
    """(SR1) and (SR2) of Eq. ``eq:srblock``, block by block, and the total trace."""
    verification = verify_block_certificate(_certificate(), ALPHABET, POVM_BLOCKS)
    assert verification.passes
    assert verification.refusal() is None
    assert verification.sr1_failures == ()
    assert verification.sr2_failures == ()
    assert verification.trace_is_one


@pytest.mark.parametrize(
    ("override", "fragment"),
    [
        pytest.param(
            {
                "psi_blocks": (
                    matrix(
                        (
                            (QUARTER, 1, 0, 0),
                            (0, 0, 0, 0),
                            (0, 0, 0, 0),
                            (0, 0, 0, QUARTER),
                        )
                    ),
                    PSI_FLAG,
                )
            },
            "not Hermitian",
            id="hermiticity",
        ),
        pytest.param(
            {
                "psi_blocks": (
                    matrix(
                        (
                            (QUARTER, HALF, 0, 0),
                            (HALF, QUARTER, 0, 0),
                            (0, 0, 0, 0),
                            (0, 0, 0, 0),
                        )
                    ),
                    PSI_FLAG,
                )
            },
            "not positive semidefinite",
            id="positivity",
        ),
        pytest.param(
            {"psi_blocks": (PSI_Q, matrix(((QUARTER,),)))},
            "sum to",
            id="total-trace",
        ),
        pytest.param(
            {"alice_marginal_blocks": (scale(QUARTER, P_Z0), PSI_FLAG)},
            "(SR1)",
            id="sr1",
        ),
        pytest.param(
            {
                "virtual_blocks": {
                    "x0": (scale(QUARTER, P_Z1), matrix(((QUARTER,),))),
                    "x1": (scale(QUARTER, P_Z1), matrix(((QUARTER,),))),
                }
            },
            "(SR2)",
            id="sr2",
        ),
    ],
)
def test_each_block_condition_refuses_with_one_reason_naming_the_sector(
    override: dict[str, object], fragment: str
) -> None:
    """ONE REASON, AND THE REPORT NAMES THE SECTOR (the interface's own rule).

    "The block form's conditions are decided PER SECTOR, so the report must name
    the sector to be useful, and one reason with the sector and the condition in
    its report says more than five reasons without them." The five pure-form
    strings are NOT reused.
    """
    verification = verify_block_certificate(
        _certificate(**override), ALPHABET, POVM_BLOCKS
    )
    refusal = verification.refusal()
    assert refusal is not None
    assert refusal.reason is RefusalReason.CERTIFICATE_BLOCK_NOT_ADMISSIBLE
    assert fragment in refusal.detail
    if fragment != "sum to":
        # EVERY PER-SECTOR CONDITION NAMES ITS SECTOR. The total trace is the
        # one condition of the form that is NOT per sector -- it is
        # ``sum_t tr Psi_t = 1`` over all of them -- so it names none, and a
        # report that invented one would name a sector the condition is not
        # about.
        assert "'q'" in refusal.detail or "'flag'" in refusal.detail
    # AND NO PURE-FORM REASON IS REUSED FOR A BLOCK.
    assert refusal.reason is not RefusalReason.CERTIFICATE_NOT_IDEMPOTENT


def test_a_zero_pivot_with_a_non_zero_row_is_refused() -> None:
    """The zero-pivot rule of ``thm:certificate-sufficiency`` (i)'s proof, on a declared block.

    "A zero pivot requires its whole row and column to vanish, the block being
    refused otherwise, which decides that every principal minor is
    non-negative." The witness is ``[[0, 1], [1, 0]]``: Hermitian, first pivot
    zero, first row not.
    """  # noqa: E501
    certificate = _certificate(
        psi_blocks=(
            matrix(((0, HALF, 0, 0), (HALF, 0, 0, 0), (0, 0, 0, 0), (0, 0, 0, 0))),
            PSI_FLAG,
        )
    )
    verification = verify_block_certificate(certificate, ALPHABET, POVM_BLOCKS)
    assert verification.not_positive_semidefinite == ("q",)


def test_a_non_hermitian_block_reports_its_own_trace_and_no_fictitious_verdict() -> (
    None
):
    """No number the declaration does not carry.

    A non-Hermitian block ends its sector's decisions -- positivity "is a
    property of a Hermitian operator" and its decision RAISES on any other
    argument rather than answering ``False``, and (SR1), (SR2) there would
    compare partial traces of an operator the form does not admit. What the
    record must NOT do is invent a verdict or a number: such a block must not
    contribute a FICTITIOUS ZERO to the accumulated trace, or ``total_trace``
    would be a quantity no declaration carried and a reader could not tell a
    block of trace zero from a block that was never traced.
    """
    broken = matrix(
        ((QUARTER, 1, 0, 0), (0, 0, 0, 0), (0, 0, 0, 0), (0, 0, 0, QUARTER))
    )
    verification = verify_block_certificate(
        _certificate(psi_blocks=(broken, PSI_FLAG)), ALPHABET, POVM_BLOCKS
    )
    assert verification.not_hermitian == ("q",)
    assert verification.undecided_sectors == ("q",)
    # THE TRACE IS THE DECLARED BLOCK'S: 1/4 + 0 + 0 + 1/4 = 1/2, plus the
    # flag's 1/2, which is one -- and the record says so rather than reporting
    # 1/2 from a zero it made up.
    assert verification.total_trace == Cx(F(1), F(0))
    assert verification.trace_is_one
    # AND NO LATER VERDICT IS CLAIMED AT THAT SECTOR, in either direction.
    assert "q" not in verification.not_positive_semidefinite
    assert "q" not in verification.sr1_failures
    assert not [sector for sector, _ in verification.sr2_failures if sector == "q"]
    # It still refuses, and the refusal says the decisions were not taken.
    refusal = verification.refusal()
    assert refusal is not None
    assert "NOT DECIDED" in refusal.detail
    assert not verification.passes


def test_a_singular_block_is_admissible() -> None:
    """No threshold and no eigenvalue: a SINGULAR block passes.

    ``PSI_Q`` has rank one in a four-dimensional joint space and ``PSI_FLAG`` is
    a one-dimensional block; both are singular as operators on their sectors'
    joint spaces and neither is refused.
    """
    verification = verify_block_certificate(_certificate(), ALPHABET, POVM_BLOCKS)
    assert verification.not_positive_semidefinite == ()


def test_a_block_form_carries_no_idempotence_condition() -> None:
    """A block form carries NO purity condition, globally or per block.

    ``def:srcert``: "There is no idempotence condition there and no consumer
    may add one."

    Structural: the verification record has no purity field, and the worked
    certificate -- whose blocks are NOT projectors, ``Psi_q^2 = Psi_q / 2`` --
    passes.
    """
    from certiqs_key.transmitter.certificate import BlockCertificateVerification

    fields = set(BlockCertificateVerification.__dataclass_fields__)
    assert not any(
        word in name for name in fields for word in ("purity", "idempot", "pure")
    )
    assert verify_block_certificate(_certificate(), ALPHABET, POVM_BLOCKS).passes


def test_an_unmatched_sector_pair_is_not_a_presentation_of_the_form() -> None:
    """The matched pair is the TYPE: same ordered index set, ``S_t`` against ``A_t``."""
    with pytest.raises(MalformedInputError, match="MATCHED sector structures"):
        _certificate(
            virtual_sectors=SectorStructure(
                labels=("other", "flag"),
                dims=(2, 1),
                block_kind=BlockKind.PROOF_SECTOR,
            )
        )


# ---------------------------------------------------------------------------
#  The emission
# ---------------------------------------------------------------------------


def test_the_emitted_artefact_carries_the_form_the_map_and_the_weighted_members() -> (
    None
):
    """What a block-form emission puts on the wire, and what it does not."""
    artifact = emit_artifact(_specification(_certificate())).require()
    assert artifact.certificate_form is CertificateForm.BLOCK
    assert artifact.alice_sector_map == SECTORS
    assert artifact.virtual_sector_map == SECTORS
    assert artifact.alice_dim == 3
    # tau_A REACHES THE EMITTED DATA THROUGH THE CERTIFICATE, as a direct sum.
    assert artifact.alice_marginal is not None
    assert equal(
        artifact.alice_marginal,
        direct_sum(list(_certificate().alice_marginal_blocks)),
    )
    # The POVM is emitted as the direct sum of the declared blocks, which "is
    # what the list MEANS, not a condition on it".
    assert equal(artifact.alice_povm["x0"], direct_sum(list(POVM_BLOCKS["x0"])))
    # rho^v_x IS NOT EMITTED: it is a quotient. The weighted members are.
    assert artifact.virtual_ensemble_states == {}
    assert artifact.virtual_ensemble_blocks is not None


def test_the_block_form_licence_record_is_json_as_emitted() -> None:
    """The licence names the block form and carries its blocks as JSON.

    The transmitter interface's ``wire_form``: matrices written by
    ``serialize_matrix`` and weights as ``"p/q"``, read back without loss.
    """
    artifact = emit_artifact(_specification(_certificate())).require()
    licence = artifact.as_machine_record()["source_replacement_license"]
    assert isinstance(licence, dict)
    assert json.loads(json.dumps(licence)) == licence
    assert licence["form"] == "block"
    block = licence["block_certificate"]
    assert [deserialize_matrix(m) for m in block["psi_blocks"]] == [PSI_Q, PSI_FLAG]
    assert block["virtual_weights"] == {"x0": "1/2", "x1": "1/2"}
    for label in ALPHABET:
        read = [deserialize_matrix(m) for m in block["virtual_blocks"][label]]
        assert all(
            equal(got, want)
            for got, want in zip(read, VIRTUAL_BLOCKS[label], strict=True)
        ), label


def test_more_than_one_sector_needs_one_of_the_two_block_presented_forms() -> None:
    """More than one sector needs a block form or an ensemble presentation.

    ``def:source-spec``: such a structure is declared "only in trusted-source
    mode and only together with a certificate in block form or an ensemble
    presentation".
    """
    certificate = _certificate()
    specification = replace(_specification(certificate), block_certificate=None)
    with pytest.raises(MalformedInputError, match="more than one sector"):
        emit_artifact(specification)


def test_a_block_form_is_trusted_mode_only() -> None:
    """A certificate in any form belongs to the trusted mode alone."""
    specification = replace(
        _specification(_certificate()), source_mode_request=SourceMode.UNTRUSTED
    )
    with pytest.raises(MalformedInputError, match="TRUSTED MODE ONLY"):
        emit_artifact(specification)


def test_the_virtual_ensembles_own_conditions_are_decided_before_the_certificate() -> (
    None
):
    """The virtual ensemble's own conditions come first.

    The ``ensemble_state_not_admissible`` row: "decided BEFORE the five
    conditions on the certificate and not among them".

    The witness fails BOTH: a virtual block that is not positive semidefinite,
    which also breaks (SR2). The reason reported is the ensemble's.
    """
    certificate = _certificate(
        virtual_blocks={
            "x0": (
                matrix(((QUARTER, HALF), (HALF, QUARTER))),
                matrix(((QUARTER,),)),
            ),
            "x1": (scale(QUARTER, P_Z1), matrix(((QUARTER,),))),
        }
    )
    result = emit_artifact(_specification(certificate))
    assert result.artifact is None
    assert result.refusal is not None
    assert result.refusal.reason is RefusalReason.ENSEMBLE_STATE_NOT_ADMISSIBLE


# ---------------------------------------------------------------------------
#  The declared members against the block lists (def:srcert, block form)
# ---------------------------------------------------------------------------


def test_a_member_with_entries_between_sectors_is_refused_naming_the_pair() -> None:
    """``def:srcert``: every ``sigma^v_x`` block diagonal along the matched sectors.

    The audit's counter-scenario: ``rho^v_x = |+-><+-|`` on two one-dimensional
    sectors. Its pinched blocks are ``1/4`` each, and the certificate
    ``Psi_t = [1/2]``, ``tau_A = diag(1/2, 1/2)``, ``M_x = diag(1/2, 1/2)``
    satisfies ``eq:srblock`` at both sectors; but ``p_x rho_x`` carries the
    entries ``+-1/4`` between them, so (SR2) fails as an identity of operators
    and the certificate is refused under ``certificate_block_not_admissible``,
    the report naming the pair of sectors (``req:failing-certificate``).
    """
    sectors = SectorStructure(
        labels=("a", "b"), dims=(1, 1), block_kind=BlockKind.PROOF_SECTOR
    )
    alphabet = ("plus", "minus")
    weights = {"plus": HALF, "minus": HALF}
    certificate = BlockFormCertificate(
        alice_sectors=sectors,
        virtual_sectors=sectors,
        alice_marginal_blocks=(matrix(((HALF,),)), matrix(((HALF,),))),
        psi_blocks=(matrix(((HALF,),)), matrix(((HALF,),))),
        virtual_weights=dict(weights),
        virtual_blocks={
            label: (matrix(((QUARTER,),)), matrix(((QUARTER,),)))
            for label in alphabet
        },
    )
    povm_blocks = {
        label: (matrix(((HALF,),)), matrix(((HALF,),))) for label in alphabet
    }
    assert verify_block_certificate(certificate, alphabet, povm_blocks).passes
    specification = SourceSpecification(
        signal_alphabet=alphabet,
        transmitted_dim=2,
        signal_weights=dict(weights),
        signal_states={
            "plus": matrix(((HALF, HALF), (HALF, HALF))),
            "minus": matrix(((HALF, -HALF), (-HALF, HALF))),
        },
        alice_dim=2,
        alice_sectors=sectors,
        alice_povm_blocks=povm_blocks,
        source_mode_request=SourceMode.TRUSTED,
        block_certificate=certificate,
    )
    result = emit_artifact(specification)
    assert result.artifact is None
    assert result.refusal is not None
    assert result.refusal.reason is RefusalReason.CERTIFICATE_BLOCK_NOT_ADMISSIBLE
    assert "'a'" in result.refusal.detail and "'b'" in result.refusal.detail
    assert "block diagonal" in result.refusal.detail

    # THE SAME CERTIFICATE AGAINST THE PINCHED MEMBERS IS ADMITTED: the
    # condition is on the declared members, not on the blocks.
    pinched = replace(
        specification,
        signal_states={label: matrix(((HALF, 0), (0, HALF))) for label in alphabet},
    )
    assert emit_artifact(pinched).refusal is None


def test_a_diagonal_block_other_than_the_declared_one_is_not_a_presentation() -> None:
    """Two carriers of one datum, as the pure form's ``_virtual_pair_diverges``.

    At ``L_s = 0`` the declared block list of ``sigma^v_x`` and the diagonal
    blocks of ``p_x rho_x`` are one datum carried twice. A specification whose
    ``rho_x`` differs on a diagonal block from the certificate's block list,
    the certificate internally consistent, is not a presentation of an input
    the module types, and raises.
    """
    certificate = _certificate()
    specification = _specification(certificate)
    swapped = dict(specification.signal_states or {})
    swapped["x0"], swapped["x1"] = swapped["x1"], swapped["x0"]
    with pytest.raises(MalformedInputError, match="differs from the diagonal block"):
        emit_artifact(replace(specification, signal_states=swapped))


@pytest.mark.parametrize("change", ["short", "long", "wrong-dimension"])
def test_a_block_list_not_one_block_per_sector_is_not_a_presentation(
    change: str,
) -> None:
    """Each letter's weighted member is one block per matched sector (F-4).

    A list one block too short or too long, or a block of another dimension,
    is no block list along the matched sectors, and raises
    ``MalformedInputError`` when the certificate is built rather than an
    untyped error later.
    """
    blocks = {label: list(VIRTUAL_BLOCKS[label]) for label in ALPHABET}
    if change == "short":
        blocks["x0"] = blocks["x0"][:1]
    elif change == "long":
        blocks["x0"] = [*blocks["x0"], matrix(((0,),))]
    else:
        blocks["x0"][1] = matrix(((QUARTER, 0), (0, 0)))
    with pytest.raises(MalformedInputError, match="block"):
        _certificate(
            virtual_blocks={label: tuple(row) for label, row in blocks.items()}
        )
