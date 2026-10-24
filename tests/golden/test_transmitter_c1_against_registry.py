"""The transmitter against the hand-derived registry ``registry_transmitter_c1``.

The registry was derived from the claim files with a pencil and this file is the
only place it is compared with the implementation. Nothing here recomputes an
expectation: every expected value is read from the registry and every computed
value from the module, and the two are compared ENTRY FOR ENTRY over the exact
Gaussian rationals, with no tolerance.

THE DECOY CASE IS THE ONE THAT WOULD CATCH A REAL ERROR. Its index set is the
one place where "the index set is a function of the declared weights" turns into
an ORDER and a set of DIMENSIONS, its tail weights are the one formed quantity of
(T2), and its ``tau_A`` is the only object ``lem:ensemble-presentation`` forms as
numbers -- so a wrong accumulation order, a flag split by intensity or a
compressed sector would each show up in a different field.
"""

from __future__ import annotations

from fractions import Fraction as F

import pytest
from decoy_support import declaration_input, tagged_declaration
from registry_transmitter_c1 import (
    BLOCK_CERTIFICATE_CASES,
    DECOY_CASES,
    PRESENTATION_CASES,
    TAGGING_REGISTRY_TRIPLE,
    BlockCertificateCase,
    DecoyCase,
    PresentationCase,
)

from certiqs_key.foundations.blocks import BlockKind, SectorStructure
from certiqs_key.foundations.exact import Matrix, matrix, trace
from certiqs_key.transmitter.certificate import (
    BlockFormCertificate,
    verify_block_certificate,
)
from certiqs_key.transmitter.decoy import TAGGING_OBLIGATION
from certiqs_key.transmitter.links import SOUNDNESS_REGISTRY, SourceLinkKind
from certiqs_key.transmitter.presentation import (
    EnsemblePresentation,
    alice_marginal_blocks,
    alice_operators,
)

pytestmark = [pytest.mark.contract, pytest.mark.oracle]


def _as_exact(rows: tuple[tuple[F, ...], ...]) -> Matrix:
    """Return a registry matrix in the module's exact substrate."""
    return matrix(rows)


def _entries(value: Matrix) -> tuple[tuple[F, ...], ...]:
    """Return the REAL parts of an exact matrix, refusing an imaginary one.

    The registry writes real entries only, so an imaginary part appearing here is
    a disagreement and not a presentation difference.
    """
    for row in value:
        for entry in row:
            assert entry.im == 0, value
    return tuple(tuple(entry.re for entry in row) for row in value)


# ---------------------------------------------------------------------------
#  Group TX-C1-A
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("case", PRESENTATION_CASES, ids=lambda c: c.case_id)
def test_the_presentation_forms_the_derived_marginal_and_operators(
    case: PresentationCase,
) -> None:
    """``lem:ensemble-presentation`` (iii) and (v), against the derivation."""
    sectors = SectorStructure(
        labels=tuple(label for label, _ in case.sectors),
        dims=tuple(dim for _, dim in case.sectors),
        block_kind=BlockKind.PROOF_SECTOR,
    )
    presentation = EnsemblePresentation(
        virtual_sectors=sectors,
        weighted_blocks={
            label: tuple(_as_exact(block) for block in blocks)
            for label, blocks in zip(case.alphabet, case.weighted_blocks, strict=True)
        },
    )
    assert presentation.alice_dim == case.alice_dim
    formed = alice_marginal_blocks(presentation, case.alphabet)
    for computed, expected in zip(
        formed, case.alice_marginal_blocks, strict=True
    ):
        assert _entries(computed) == expected
    operators = alice_operators(presentation)
    for label, expected_blocks in zip(
        case.alphabet, case.alice_operators, strict=True
    ):
        for computed, expected in zip(
            operators[label], expected_blocks, strict=True
        ):
            assert _entries(computed) == expected


# ---------------------------------------------------------------------------
#  Group TX-C1-B
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("case", BLOCK_CERTIFICATE_CASES, ids=lambda c: c.case_id)
def test_the_block_certificate_verifies_against_the_derived_values(
    case: BlockCertificateCase,
) -> None:
    """``def:srcert``'s block form and Eq. ``eq:srblock``, against the derivation."""
    alice = SectorStructure(
        labels=tuple(label for label, _, _ in case.sectors),
        dims=tuple(alice_dim for _, alice_dim, _ in case.sectors),
        block_kind=BlockKind.PROOF_SECTOR,
    )
    virtual = SectorStructure(
        labels=alice.labels,
        dims=tuple(virtual_dim for _, _, virtual_dim in case.sectors),
        block_kind=BlockKind.PROOF_SECTOR,
    )
    povm_blocks = {
        label: tuple(_as_exact(block) for block in blocks)
        for label, blocks in zip(case.alphabet, case.povm_blocks, strict=True)
    }
    certificate = BlockFormCertificate(
        alice_sectors=alice,
        virtual_sectors=virtual,
        alice_marginal_blocks=tuple(
            _as_exact(block) for block in case.sr1_computed
        ),
        psi_blocks=tuple(_as_exact(block) for block in case.psi_blocks),
        virtual_weights=dict(zip(case.alphabet, case.weights, strict=True)),
        virtual_blocks={
            label: tuple(_as_exact(block) for block in blocks)
            for label, blocks in zip(case.alphabet, case.sr2_computed, strict=True)
        },
    )
    verification = verify_block_certificate(certificate, case.alphabet, povm_blocks)
    assert verification.passes
    assert verification.total_trace.re == case.total_trace
    for block, expected in zip(certificate.psi_blocks, case.block_traces, strict=True):
        assert trace(block).re == expected


# ---------------------------------------------------------------------------
#  Group TX-C1-C
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("case", DECOY_CASES, ids=lambda c: c.case_id)
def test_the_tagged_declaration_matches_the_derived_index_set_and_marginal(
    case: DecoyCase,
) -> None:
    """(T2), (T3), (T4) and ``cor:emitted-decoy`` (i), (iv), against the derivation."""
    declaration = declaration_input(
        entropy_cutoff=case.entropy_cutoff, source_cutoff=case.source_cutoff
    )
    assert declaration.model.polarisations == case.polarisations
    assert tuple(declaration.model.intensities.items()) == case.intensities
    for key, weight in case.sector_weights.items():
        assert declaration.sector_weights[key] == weight

    for intensity, expected in case.tail_weights.items():
        tail = declaration.tail_weight(intensity)
        assert tail.rounds_nowhere
        assert tail.value == expected

    structure = declaration.sector_structure()
    assert structure.entries == case.sector_index_set
    assert structure.total_dim == case.alice_dim
    assert structure.block_kind is BlockKind.PROOF_SECTOR

    emitted = tagged_declaration(
        entropy_cutoff=case.entropy_cutoff, source_cutoff=case.source_cutoff
    )
    presentation = emitted.presentation
    position_of = {label: index for index, (label, _) in enumerate(
        case.sector_index_set
    )}
    for letter, blocks in case.weighted_blocks.items():
        declared = presentation.weighted_blocks[letter]
        for sector, expected in blocks.items():
            assert _entries(declared[position_of[sector]]) == expected

    formed = alice_marginal_blocks(
        presentation, declaration.model.signal_alphabet
    )
    for sector, expected in case.alice_marginal_blocks.items():
        assert _entries(formed[position_of[sector]]) == expected


# ---------------------------------------------------------------------------
#  Group TX-C1-D
# ---------------------------------------------------------------------------


def test_the_registry_entry_and_the_emitted_obligation_are_the_derived_triple() -> None:
    """``def:source-segment`` (A1) and ``cor:emitted-decoy`` (ii).

    Two files must agree with one derivation: the core's closed registry, which a
    consumer decides against, and the submodule's emitted obligation.
    """
    entry = next(e for e in SOUNDNESS_REGISTRY if e.kind is SourceLinkKind.TAGGING)
    assert entry.triple == TAGGING_REGISTRY_TRIPLE
    assert TAGGING_OBLIGATION.triple == TAGGING_REGISTRY_TRIPLE
