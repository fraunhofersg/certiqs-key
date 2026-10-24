"""The exact Gaussian-rational substrate of :mod:`certiqs_key.foundations.exact`.

``interface.yaml`` leaves the numeric substrate open (choice 8 of 8) and
``exact.py`` is the one named site where it is decided. These tests hold the
decision's OBSERVABLE CONSEQUENCES fixed: a ``float`` is refused rather than
converted, positivity is decided with no threshold so a singular operator is
accepted and a negative eigenvalue refused, the partial traces respect
``subsystem_order``, and a matrix survives serialization exactly.
"""

from __future__ import annotations

from fractions import Fraction as F

import pytest

from certiqs_key.foundations.errors import HypothesisError, MalformedInputError
from certiqs_key.foundations.exact import (
    Cx,
    conjugate_transpose,
    deserialize_matrix,
    equal,
    identity,
    inverse,
    is_hermitian,
    is_positive_semidefinite,
    kron,
    loewner_ge,
    matmul,
    matrix,
    outer_projector,
    partial_trace_first,
    partial_trace_second,
    scale,
    serialize_matrix,
    support_projector,
    trace,
    vector,
)

pytestmark = pytest.mark.contract


def test_a_float_is_refused_rather_than_converted() -> None:
    """A float carries no record of which of two rationals its author meant."""
    with pytest.raises(MalformedInputError):
        matrix(((0.5, 0), (0, 0.5)))
    with pytest.raises(MalformedInputError):
        matrix(((complex(1, 0), 0), (0, 0)))
    with pytest.raises(MalformedInputError):
        matrix(((True, 0), (0, 0)))
    # The explicit conversion the caller must perform is accepted.
    assert equal(matrix(((F(1, 2), 0), (0, F(1, 2)))), scale(F(1, 2), identity(2)))


def test_a_ragged_presentation_is_malformed_and_not_a_refusal() -> None:
    with pytest.raises(MalformedInputError):
        matrix(((1, 0), (0,)))
    with pytest.raises(MalformedInputError):
        matrix(())
    with pytest.raises(MalformedInputError):
        vector(())


def test_positivity_is_decided_with_no_threshold() -> None:
    singular = matrix(((1, 0), (0, 0)))
    negative = matrix(((2, 0), (0, -1)))
    assert is_positive_semidefinite(singular) is True
    assert is_positive_semidefinite(negative) is False
    assert trace(negative) == Cx(F(1), F(0))
    # A tiny negative eigenvalue is refused with no tolerance separating it.
    almost = matrix(((1, 0), (0, F(-1, 10**12))))
    assert is_positive_semidefinite(almost) is False
    # A zero pivot with a non-zero row is refused (the Cauchy-Schwarz rule).
    assert is_positive_semidefinite(matrix(((0, 1), (1, 0)))) is False
    assert is_positive_semidefinite(matrix(((0, 0), (0, 1)))) is True


def test_positivity_of_a_complex_hermitian_operator() -> None:
    y_projector = (
        (Cx(F(1, 2), F(0)), Cx(F(0), F(-1, 2))),
        (Cx(F(0), F(1, 2)), Cx(F(1, 2), F(0))),
    )
    assert is_hermitian(y_projector) is True
    assert is_positive_semidefinite(y_projector) is True
    assert is_positive_semidefinite(scale(-1, y_projector)) is False


def test_positivity_refuses_a_non_hermitian_argument_as_a_hypothesis_error() -> None:
    with pytest.raises(HypothesisError):
        is_positive_semidefinite(matrix(((0, 1), (0, 0))))
    with pytest.raises(HypothesisError):
        loewner_ge(matrix(((0, 1), (0, 0))), identity(2))


def test_the_loewner_order_on_named_operators() -> None:
    left = matrix(((F(3, 4), 0), (0, F(1, 4))))
    right = matrix(((F(3, 16), 0), (0, F(1, 16))))
    assert loewner_ge(left, right) is True
    assert loewner_ge(right, left) is False
    assert loewner_ge(left, left) is True


def test_subsystem_order_puts_the_a_factor_first() -> None:
    alice = matrix(((1, 0), (0, 0)))
    bob = matrix(((0, 0), (0, 1)))
    joint = kron(alice, bob)
    # |0><0|_A (x) |1><1|_Q has its single entry at the composite index
    # (0, 1) -> 0 * 2 + 1 = 1.
    assert joint[1][1] == Cx(F(1), F(0))
    assert equal(partial_trace_second(joint, 2, 2), alice)
    assert equal(partial_trace_first(joint, 2, 2), bob)
    assert kron(bob, alice) != joint


def test_the_certificate_projector_never_takes_a_square_root() -> None:
    phi_plus = outer_projector(vector([1, 0, 0, 1]), F(2))
    assert equal(
        phi_plus,
        matrix(
            (
                (F(1, 2), 0, 0, F(1, 2)),
                (0, 0, 0, 0),
                (0, 0, 0, 0),
                (F(1, 2), 0, 0, F(1, 2)),
            )
        ),
    )
    assert trace(phi_plus) == Cx(F(1), F(0))
    with pytest.raises(MalformedInputError):
        outer_projector(vector([1, 0, 0, 1]), F(3))
    with pytest.raises(MalformedInputError):
        outer_projector(vector([1, 0]), F(0))


def test_the_support_projector_of_a_singular_marginal() -> None:
    singular = matrix(((1, 0), (0, 0)))
    assert equal(support_projector(singular), singular)
    full = scale(F(1, 2), identity(2))
    assert equal(support_projector(full), identity(2))
    rank_one = matrix(((F(1, 2), F(1, 2)), (F(1, 2), F(1, 2))))
    projector = support_projector(rank_one)
    assert equal(projector, rank_one)
    assert equal(matmul(projector, projector), projector)


def test_the_inverse_and_the_conjugate_transpose() -> None:
    operator = ((Cx(F(1), F(0)), Cx(F(0), F(1))), (Cx(F(0), F(0)), Cx(F(1), F(0))))
    assert equal(matmul(operator, inverse(operator)), identity(2))
    assert equal(
        conjugate_transpose(operator),
        ((Cx(F(1), F(0)), Cx(F(0), F(0))), (Cx(F(0), F(-1)), Cx(F(1), F(0)))),
    )
    with pytest.raises(MalformedInputError):
        inverse(matrix(((1, 1), (1, 1))))


def test_a_matrix_survives_serialization_exactly() -> None:
    original = (
        (Cx(F(2, 3), F(-1, 5)), Cx(F(0), F(0))),
        (Cx(F(0), F(4, 7)), Cx(F(-11, 13), F(0))),
    )
    payload = serialize_matrix(original)
    assert payload[0][0] == ["2/3", "-1/5"]
    assert equal(deserialize_matrix(payload), original)
