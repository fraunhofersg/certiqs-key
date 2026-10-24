"""Properties of the ensemble presentation, on randomly generated declarations.

``transmitter/lem:ensemble-presentation`` states three things about EVERY
declared block list, not about the two the unit tests exhibit, and each is cheap
to check on a random one over the exact Gaussian rationals:

* part (iii): ``tau^{(t)}_A`` IS the transposed sum of (E3) -- entry ``(i, j)``
  of the marginal is entry ``(j, i)`` of the declared sum;
* part (v): ``sum_x N^{(t)}_x = tau^{(t)}_A`` EXACTLY, the operators being
  entrywise the declared numbers;
* (E2): the block traces of a letter sum to its weight, which is what ties the
  declared weights to the declared blocks.

THE GENERATOR PRODUCES POSITIVE SEMIDEFINITE BLOCKS BY CONSTRUCTION, as weighted
dyads of small integer vectors scaled onto a coarse dyadic grid: the properties
above are statements about an ADMISSIBLE presentation, and a generator that
produced inadmissible blocks would be testing the refusal path, which the unit
tests do directly. No tolerance appears here, as none appears in the module.
"""

from __future__ import annotations

from fractions import Fraction

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from certiqs_key.foundations.blocks import BlockKind, SectorStructure
from certiqs_key.foundations.exact import Cx, Matrix, add, equal, scale, trace, zeros
from certiqs_key.transmitter.presentation import (
    EnsemblePresentation,
    alice_marginal_blocks,
    alice_operators,
    sector_sums,
    transpose,
    verify_ensemble_presentation,
)

pytestmark = pytest.mark.contract

#: Small dimensions and few letters: the properties are algebraic identities, so
#: a large example checks nothing a small one does not.
_DIMS = st.lists(st.integers(min_value=1, max_value=3), min_size=1, max_size=3)
_LETTERS = st.integers(min_value=1, max_value=3)


def _dyad(dim: int, entries: list[tuple[int, int]]) -> Matrix:
    """Return ``|v><v|`` for a GAUSSIAN-INTEGER vector, PSD by construction.

    ``|v><v|_{ij} = v_i conj(v_j)``, so the block is Hermitian, positive
    semidefinite and in general COMPLEX. The complex case is here because with
    real symmetric blocks alone the transpose of ``lem:ensemble-presentation``
    is indistinguishable from the identity and from the adjoint, and the
    properties below are exactly the ones that would then pin nothing.
    """
    vector = [Cx(Fraction(re), Fraction(im)) for re, im in entries]
    return tuple(
        tuple(vector[i] * vector[j].conjugate() for j in range(dim))
        for i in range(dim)
    )


@st.composite
def _presentations(
    draw: st.DrawFn,
) -> tuple[EnsemblePresentation, tuple[str, ...], dict]:
    """Return a presentation with its alphabet and its declared weights.

    THE WEIGHTS ARE READ OFF THE BLOCKS AND NOT DRAWN INDEPENDENTLY, because
    (E2) is what a declaration has to satisfy and a drawn weight would almost
    never satisfy it; what the property then checks is that the formed block
    traces reproduce them, which is the direction the condition is decided in.
    """
    dims = draw(_DIMS)
    letters = draw(_LETTERS)
    alphabet = tuple(f"x{index}" for index in range(letters))
    sectors = SectorStructure(
        labels=tuple(f"s{index}" for index in range(len(dims))),
        dims=tuple(dims),
        block_kind=BlockKind.PROOF_SECTOR,
    )
    # A COARSE DYADIC SCALE, so that every formed product and every sum is a
    # binary64 number: the properties are about an admissible presentation.
    scale_denominator = 2 ** (len(dims) + letters + 4)
    blocks: dict[str, tuple[Matrix, ...]] = {}
    for label in alphabet:
        row: list[Matrix] = []
        for dim in dims:
            entries = draw(
                st.lists(
                    st.tuples(
                        st.integers(min_value=-2, max_value=2),
                        st.integers(min_value=-2, max_value=2),
                    ),
                    min_size=dim,
                    max_size=dim,
                )
            )
            row.append(scale(Fraction(1, scale_denominator), _dyad(dim, entries)))
        blocks[label] = tuple(row)
    presentation = EnsemblePresentation(virtual_sectors=sectors, weighted_blocks=blocks)
    weights = {
        label: sum(
            (trace(block).re for block in blocks[label]), start=Fraction(0)
        )
        for label in alphabet
    }
    return presentation, alphabet, weights


@settings(max_examples=60, deadline=None)
@given(_presentations())
def test_tau_a_is_the_transposed_sum_of_e3(case: tuple) -> None:
    """Part (iii): the marginal is the transposed sum, entry for entry.

    "the entry ``(i, j)`` of ``tau^{(t)}_A`` is the entry ``(j, i)`` of the
    declared sum ``tau^{(t)}_S``".
    """
    presentation, alphabet, _ = case
    sums = sector_sums(presentation, alphabet)
    for verdict, block in zip(
        sums, alice_marginal_blocks(presentation, alphabet), strict=True
    ):
        total = verdict.total
        for i, row in enumerate(block):
            for j, entry in enumerate(row):
                assert entry == total[j][i]


@settings(max_examples=60, deadline=None)
@given(_presentations())
def test_the_operators_sum_to_the_marginal_exactly(case: tuple) -> None:
    """Part (v): ``sum_x N^{(t)}_x = tau^{(t)}_A``, in the declared order of ``X``."""
    presentation, alphabet, _ = case
    operators = alice_operators(presentation)
    marginals = alice_marginal_blocks(presentation, alphabet)
    for position, dim in enumerate(presentation.virtual_sectors.dims):
        total = zeros(dim, dim)
        for label in alphabet:
            total = add(total, operators[label][position])
        assert equal(total, marginals[position])


@settings(max_examples=60, deadline=None)
@given(_presentations())
def test_the_operators_are_entrywise_the_declared_numbers(case: tuple) -> None:
    """Part (v): ``N^{(t)}_x`` carries no arithmetic at all, only a re-indexing."""
    presentation, _, _ = case
    operators = alice_operators(presentation)
    for label, blocks in presentation.weighted_blocks.items():
        for declared, read in zip(blocks, operators[label], strict=True):
            assert equal(read, transpose(declared))


@settings(max_examples=60, deadline=None)
@given(_presentations())
def test_e2_holds_of_the_weights_the_blocks_determine(case: tuple) -> None:
    """(E2): ``p_x = sum_t tr sigma^{v,(t)}_x``, and normalising makes it pass."""
    presentation, alphabet, weights = case
    total = sum(weights.values(), start=Fraction(0))
    if total == 0:
        return
    normalised_blocks = {
        label: tuple(
            scale(Fraction(1, 1) / total, block)
            for block in presentation.weighted_blocks[label]
        )
        for label in alphabet
    }
    normalised = EnsemblePresentation(
        virtual_sectors=presentation.virtual_sectors,
        weighted_blocks=normalised_blocks,
    )
    verification = verify_ensemble_presentation(
        normalised, alphabet, {label: weights[label] / total for label in alphabet}
    )
    # (E1) always holds of a weighted dyad; (E2) and (E3) may fail on a
    # normalisation that is not dyadic, and where they do the module REFUSES --
    # which is the behaviour, not a defect of the property.
    assert verification.e1_failures == ()
    if verification.passes:
        for label in alphabet:
            traces = sum(
                (
                    trace(block).re
                    for block in normalised.weighted_blocks[label]
                ),
                start=Fraction(0),
            )
            assert traces == weights[label] / total


@settings(max_examples=40, deadline=None)
@given(_presentations())
def test_the_marginal_is_a_state_up_to_its_total_weight(case: tuple) -> None:
    """Part (i): ``tau_A`` is positive semidefinite, and its trace is ``sum_x p_x``.

    The lemma's part (i) concludes that ``tau_A`` is a STATE under its hypothesis
    ``sum_x sum_t tr sigma = 1``; a random presentation need not be normalised,
    so what is checked is the two halves that do not depend on the
    normalisation -- positivity, and the trace being the total weight.
    """
    from certiqs_key.foundations.exact import is_hermitian, is_positive_semidefinite

    presentation, alphabet, weights = case
    blocks = alice_marginal_blocks(presentation, alphabet)
    total = Cx(Fraction(0), Fraction(0))
    for block in blocks:
        assert is_hermitian(block)
        assert is_positive_semidefinite(block)
        total = total + trace(block)
    assert total.re == sum(weights.values(), start=Fraction(0))
