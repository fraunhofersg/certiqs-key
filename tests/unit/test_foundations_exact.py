"""The numeric substrate of ``proof-reductions``: exact Gaussian rationals.

Open implementation choice 1 of 10 is decided in
:mod:`certiqs_key.foundations.exact`, and these are the tests of the decision. Two
things are asserted throughout and nowhere relaxed: NO TOLERANCE APPEARS, and a
``float`` is REFUSED at the boundary rather than converted, so that the caller
says which rational it means.
"""

from __future__ import annotations

from fractions import Fraction

import pytest

from certiqs_key.foundations.exact import (
    ONE,
    WEIGHT_ROUNDING_DIRECTION,
    ZERO,
    Cx,
    add,
    adjoint_from_kraus,
    all_principal_minors_nonnegative,
    as_rational,
    as_scalar,
    basis_projector,
    conjugate_transpose,
    deserialize_matrix,
    diagonal,
    dimension,
    direct_sum,
    equal,
    identity,
    is_diagonal,
    is_hermitian,
    is_positive_semidefinite,
    kron,
    linear_relations,
    loewner_ge,
    matmul,
    matrix,
    real_part,
    scale,
    serialize_matrix,
    span_dimension,
    spectral_bounds,
    subtract,
    trace,
    zeros,
)
from certiqs_key.reductions.errors import HypothesisError, MalformedInputError

F = Fraction


def test_a_float_is_refused_at_the_boundary_and_not_converted() -> None:
    """The refusal is the fail-closed reading; the conversion is the caller's."""
    with pytest.raises(MalformedInputError):
        as_scalar(0.1)
    with pytest.raises(MalformedInputError):
        as_scalar(complex(1, 2))
    with pytest.raises(MalformedInputError):
        as_scalar(True)
    # The caller's explicit conversion is accepted and is lossless: a binary64
    # value IS a dyadic rational, and Fraction(value) is exactly it.
    assert as_scalar(Fraction(0.1)) == Cx(Fraction(0.1), F(0))
    assert Fraction(0.1) != F(1, 10)
    # Which is the whole point: 0.1 read as 1/10 would be wrong by the
    # difference, and on a certified weight that is the unsafe direction.
    assert as_scalar(F(1, 10)) == Cx(F(1, 10), F(0))
    assert as_scalar(3) == Cx(F(3), F(0))


def test_a_ragged_matrix_enumerates_no_operator() -> None:
    """No rule of Section 4.14 can be read against it, so it is not refused."""
    with pytest.raises(MalformedInputError):
        matrix([[1, 2], [3]])
    with pytest.raises(MalformedInputError):
        matrix([])
    with pytest.raises(MalformedInputError):
        matrix("not a matrix")


def test_gaussian_rational_arithmetic_is_exact() -> None:
    a = Cx(F(3, 5), F(4, 5))
    b = Cx(F(4, 5), F(-3, 5))
    assert a * b == Cx(F(12, 25) + F(12, 25), F(-9, 25) + F(16, 25))
    assert a.conjugate() == Cx(F(3, 5), F(-4, 5))
    assert (a + b) - b == a
    assert (-a) + a == ZERO
    assert a.over(F(2)) == Cx(F(3, 10), F(2, 5))
    with pytest.raises(MalformedInputError):
        a.over(F(0))
    assert ONE.is_real and not a.is_real
    assert ZERO.is_zero and not ONE.is_zero
    assert str(a) == "3/5+4/5i"


def test_hermiticity_and_positivity_are_decided_exactly() -> None:
    """A singular operator is accepted; a negative eigenvalue is refused."""
    projector = matrix([[F(1), F(0)], [F(0), F(0)]])
    assert is_hermitian(projector)
    assert is_positive_semidefinite(projector)  # SINGULAR, and admissible.
    assert all_principal_minors_nonnegative(projector)
    negative = diagonal([F(1), F(-1, 1000000)])
    assert not is_positive_semidefinite(negative)
    assert not all_principal_minors_nonnegative(negative)
    # No threshold separates them: an arbitrarily small negative eigenvalue is
    # still refused, which is what "a refusal test, not a bound" means.
    assert not is_positive_semidefinite(diagonal([F(1), F(-1, 10**30)]))
    non_hermitian = matrix([[F(0), F(1)], [F(0), F(0)]])
    assert not is_hermitian(non_hermitian)
    with pytest.raises(HypothesisError):
        is_positive_semidefinite(non_hermitian)
    with pytest.raises(HypothesisError):
        loewner_ge(non_hermitian, identity(2))


def test_the_two_positivity_procedures_agree_on_a_complex_instance() -> None:
    """The exact ``LDL^*`` and the full principal-minor enumeration."""
    operator = matrix(
        [
            [F(19, 40), Cx(F(0), F(-3, 10))],
            [Cx(F(0), F(3, 10)), F(13, 20)],
        ]
    )
    assert is_hermitian(operator)
    assert is_positive_semidefinite(operator)
    assert all_principal_minors_nonnegative(operator)
    shifted = subtract(operator, scale(F(9, 10), identity(2)))
    assert is_positive_semidefinite(shifted) is (
        all_principal_minors_nonnegative(shifted)
    )


def test_the_loewner_order_is_the_comparison_the_contract_writes() -> None:
    """``eq:certweights`` and ``eq:certificate`` are stated in this order."""
    block = matrix(
        [
            [F(19, 40), Cx(F(0), F(-3, 10))],
            [Cx(F(0), F(3, 10)), F(13, 20)],
        ]
    )
    assert loewner_ge(block, scale(F(1, 4), identity(2)))
    assert not loewner_ge(block, scale(F(1, 2), identity(2)))
    # Tight: the minimum eigenvalue of this block is exactly 1/4.
    assert is_positive_semidefinite(subtract(block, scale(F(1, 4), identity(2))))


def test_direct_sum_and_kron_carry_the_declared_orders() -> None:
    """``(+)`` is the block order of Section 2.5; ``(x)`` is C major, Bl minor."""
    summed = direct_sum([matrix([[F(2, 3)]]), diagonal([F(7, 8), F(1, 4)])])
    assert equal(summed, diagonal([F(2, 3), F(7, 8), F(1, 4)]))
    assert dimension(summed) == 3
    product = kron(diagonal([F(1), F(0)]), diagonal([F(9, 25), F(16, 25)]))
    assert equal(product, diagonal([F(9, 25), F(16, 25), F(0), F(0)]))
    with pytest.raises(MalformedInputError):
        direct_sum([])


def test_the_adjoint_from_a_kraus_set_is_unital_when_the_set_is_complete() -> None:
    """``sum_K K+ K = 1`` IS ``Lambda^dagger(1_Q) = 1_B``."""
    kraus = (
        matrix([[F(1), F(0)], [F(0), F(0)]]),
        matrix([[F(0), F(0)], [F(0), F(1)]]),
    )
    assert equal(adjoint_from_kraus(kraus, identity(2)), identity(2))
    with pytest.raises(MalformedInputError):
        adjoint_from_kraus((), identity(2))


def test_spectral_bounds_are_tight_on_a_diagonal_operator() -> None:
    """The enclosure IS the spectrum where the operator is diagonal."""
    bounds = spectral_bounds(diagonal([F(2, 3), F(7, 8), F(1, 4)]))
    assert bounds.tight is True
    assert (bounds.lower, bounds.upper) == (F(1, 4), F(7, 8))
    off_diagonal = matrix([[F(0), F(1)], [F(1), F(0)]])
    loose = spectral_bounds(off_diagonal)
    assert loose.tight is False
    # It ENCLOSES: the true spectrum is {-1, 1}.
    assert loose.lower <= -1
    assert loose.upper >= 1
    assert loewner_ge(scale(loose.upper, identity(2)), off_diagonal)
    assert loewner_ge(off_diagonal, scale(loose.lower, identity(2)))
    with pytest.raises(HypothesisError):
        spectral_bounds(matrix([[F(0), F(1)], [F(0), F(0)]]))


def test_span_dimension_and_linear_relations_are_exact() -> None:
    """Lemma ``lem:obstructions`` (ii)'s two ingredients."""
    assert span_dimension([diagonal([F(1), F(0)]), diagonal([F(0), F(1)])]) == 2
    half = scale(F(1, 2), identity(2))
    assert span_dimension([half, half]) == 1
    assert span_dimension([]) == 0
    relations = linear_relations([half, half], identity(2))
    # {(a0, a1, c) : (a0 + a1)/2 = c} is two-dimensional.
    assert len(relations) == 2
    for coefficients in relations:
        assert (coefficients[0] + coefficients[1]) / 2 == coefficients[2]
    # A family with no relation but the completeness one.
    povm = [diagonal([F(1), F(0)]), diagonal([F(0), F(1)])]
    trivial = linear_relations(povm, identity(2))
    assert len(trivial) == 1
    assert trivial[0][0] == trivial[0][1] == trivial[0][2]


def test_real_part_raises_rather_than_dropping_an_imaginary_part() -> None:
    """There is no site at which a complex value is silently narrowed."""
    assert real_part(Cx(F(3, 4), F(0)), "a weight") == F(3, 4)
    with pytest.raises(HypothesisError):
        real_part(Cx(F(3, 4), F(1, 4)), "a weight")
    with pytest.raises(MalformedInputError):
        as_rational(Cx(F(0), F(1)))


def test_serialization_round_trips_exactly() -> None:
    """``[str(re), str(im)]`` and back, with Fraction's own parser."""
    operator = matrix([[F(2, 3), Cx(F(0), F(-3, 10))], [Cx(F(0), F(3, 10)), F(13, 20)]])
    payload = serialize_matrix(operator)
    assert payload[0][0] == ["2/3", "0"]
    assert payload[0][1] == ["0", "-3/10"]
    assert equal(deserialize_matrix(payload), operator)


def test_the_rounding_rule_is_recorded_as_a_direction_and_never_exercised() -> None:
    """Section 1.4: round ``p_(y_i,t)`` TOWARD ZERO -- if upstream becomes exact."""
    assert WEIGHT_ROUNDING_DIRECTION == "toward_zero"


def test_matrix_helpers_refuse_shapes_no_rule_can_read() -> None:
    assert equal(zeros(2, 3), matrix([[0, 0, 0], [0, 0, 0]]))
    assert is_diagonal(diagonal([F(1), F(2)]))
    assert not is_diagonal(matrix([[F(0), F(1)], [F(1), F(0)]]))
    assert equal(basis_projector(3, 1), diagonal([F(0), F(1), F(0)]))
    with pytest.raises(MalformedInputError):
        basis_projector(3, 3)
    with pytest.raises(MalformedInputError):
        identity(0)
    with pytest.raises(MalformedInputError):
        add(identity(2), identity(3))
    with pytest.raises(MalformedInputError):
        matmul(identity(2), zeros(3, 3))
    with pytest.raises(MalformedInputError):
        dimension(zeros(2, 3))
    assert trace(diagonal([F(1, 3), F(2, 3)])) == ONE
    assert equal(conjugate_transpose(identity(2)), identity(2))

