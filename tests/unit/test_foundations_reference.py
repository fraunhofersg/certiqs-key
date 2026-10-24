"""Contract tests of the reference claims of ``foundations``.

``foundations/lem:enclosure-psd`` and ``def:exact-reference``, with the
reference decisions of ``req:snap-reference`` (i), as
:mod:`certiqs_key.foundations.reference` implements them. Every expected value
is derived by hand in the comment beside it, from the claim's own statement;
nothing here is read back from the code under test.
"""

from __future__ import annotations

import json
from decimal import Decimal, getcontext
from fractions import Fraction as F

import pytest

from certiqs_key.foundations.errors import HypothesisError, MalformedInputError
from certiqs_key.foundations.exact import (
    Matrix,
    diagonal,
    identity,
    is_positive_definite,
    matrix,
)
from certiqs_key.foundations.reference import (
    Enclosure,
    Reference,
    ReferenceBlock,
    ReferenceIdentity,
    ReferenceKind,
    enclosure_pd,
    enclosure_psd,
    inverse_sqrt_enclosure,
    scaled_enclosure,
)

pytestmark = pytest.mark.contract


def diag(*values: int | F) -> Matrix:
    """Return the exact diagonal matrix with the given entries."""
    return diagonal([F(v) for v in values])


def zeros_radii(n: int) -> tuple[tuple[F, ...], ...]:
    """Return an ``n x n`` matrix of zero radii."""
    return tuple(tuple(F(0) for _ in range(n)) for _ in range(n))


def exact_reference(
    *families: tuple[str, list[Matrix]], alphabet: tuple[str, ...]
) -> Reference:
    """Return an exact reference with one block per ``(label, family)``."""
    return Reference(
        alphabet,
        tuple(
            ReferenceBlock(label, tuple(Enclosure.exact(m) for m in family))
            for label, family in families
        ),
        F(1),
        ReferenceIdentity("hand-derived test model"),
    )


# ---------------------------------------------------------------------------
#  lem:enclosure-psd
# ---------------------------------------------------------------------------


def test_enclosure_decision_is_the_exact_decision_at_radius_zero() -> None:
    """lem:enclosure-psd (i) at rho = 0, mu = 0 is the exact X_c >= 0."""
    singular = matrix([[1, 1], [1, 1]])  # rank one, PSD, eigenvalues 0 and 2
    assert enclosure_psd(singular, zeros_radii(2))
    assert not enclosure_pd(singular, zeros_radii(2))
    assert enclosure_pd(identity(2), zeros_radii(2))


def test_enclosure_never_certifies_a_matrix_that_is_not_psd() -> None:
    """lem:enclosure-psd (i), soundness: X = diag(-eps, 1) is not PSD.

    Its centre diag(0, 1) lies within radius eps entrywise, and the decision
    on X_c - rho 1 = diag(-eps, 1 - eps) (rho = eps, the largest row sum)
    refuses: the sufficient condition does not admit X.
    """
    eps = F(1, 1 << 30)
    radii = ((eps, F(0)), (F(0), F(0)))
    assert not enclosure_psd(diag(0, 1), radii)
    # Enough room: the centre diag(eps, 1) certifies X >= 0 for every X in its box.
    assert enclosure_psd(diag(eps, 1), radii)
    assert not enclosure_pd(diag(eps, 1), radii)
    assert enclosure_pd(diag(2 * eps, 1), radii)


def test_enclosure_margin() -> None:
    """lem:enclosure-psd (i): X_c - (rho + mu) 1 >= 0 gives X >= mu 1.

    X_c = diag(1, 1) with every radius 1/8 (rho = 1/4): decided at mu = 3/4,
    not at mu = 3/4 + 2^-20. Every X in the box has |off-diagonal| <= 1/8 and
    diagonal >= 7/8, so lambda_min(X) >= 7/8 - 1/8 = 3/4 indeed.
    """
    radii = tuple(tuple(F(1, 8) for _ in range(2)) for _ in range(2))
    assert enclosure_psd(identity(2), radii, margin=F(3, 4))
    assert not enclosure_psd(identity(2), radii, margin=F(3, 4) + F(1, 1 << 20))
    with pytest.raises(MalformedInputError):
        enclosure_psd(identity(2), radii, margin=F(-1))


def test_inverse_sqrt_enclosure_satisfies_its_inequality() -> None:
    """lem:enclosure-psd (ii), Eq. eq:sqrt-enclosure: (a-e)^2 n <= 1 <= (a+e)^2 n."""
    for n in (F(2), F(3), F(6), F(24), F(5, 7)):
        a, e = inverse_sqrt_enclosure(n, 40)
        assert 0 <= e <= a
        assert (a - e) ** 2 * n <= 1 <= (a + e) ** 2 * n
        assert e == F(1, 1 << 41)
    # A rational square root is exact: 1/sqrt(4/9) = 3/2.
    assert inverse_sqrt_enclosure(F(4, 9), 40) == (F(3, 2), F(0))
    assert inverse_sqrt_enclosure(F(1), 40) == (F(1), F(0))


def test_scaled_enclosure_encloses_the_irrational_block() -> None:
    """lem:enclosure-psd (ii): |X_il - (ASA)_il| <= r_il for X = D^-1 S D^-1.

    Checked against a 60-digit decimal evaluation of S_il / sqrt(n_i n_l), far
    finer than the radii at 20 bits.
    """
    getcontext().prec = 60
    s = matrix(
        [
            [F(1, 2), F(1, 3), F(-1, 5)],
            [F(1, 3), F(1, 7), F(2, 9)],
            [F(-1, 5), F(2, 9), F(1)],
        ]
    )
    n = (F(2), F(1), F(6))
    enclosure = scaled_enclosure(s, n, bits=20)
    for i in range(3):
        for j in range(3):
            exact = Decimal(s[i][j].re.numerator) / Decimal(s[i][j].re.denominator)
            exact /= (Decimal(n[i].numerator) * Decimal(n[j].numerator)).sqrt()
            centre = enclosure.centre[i][j].re
            radius = enclosure.radii[i][j]
            gap = abs(exact - Decimal(centre.numerator) / Decimal(centre.denominator))
            assert gap <= Decimal(radius.numerator) / Decimal(radius.denominator)
    # n_2 = 1 is a square: row and column 2 are exact against each other.
    assert enclosure.radii[1][1] == 0


def test_scaled_enclosure_keeps_structural_zeros() -> None:
    """lem:enclosure-psd (ii): S_il = 0 gives centre and radius zero (def:snap)."""
    s = matrix([[1, 0], [0, 1]])
    enclosure = scaled_enclosure(s, (F(2), F(3)), bits=30)
    assert enclosure.is_structurally_zero_at(0, 1)
    assert enclosure.is_structurally_zero_at(1, 0)
    assert not enclosure.is_structurally_zero_at(0, 0)


def test_is_positive_definite_decides_by_strict_pivots() -> None:
    """The exact PD decision of lem:enclosure-psd (i): PSD singular is not PD."""
    assert is_positive_definite(matrix([[2, 1], [1, 2]]))
    assert not is_positive_definite(matrix([[1, 1], [1, 1]]))
    assert not is_positive_definite(matrix([[1, 2], [2, 1]]))
    with pytest.raises(HypothesisError):
        is_positive_definite(matrix([[1, 1], [0, 1]]))


# ---------------------------------------------------------------------------
#  def:exact-reference
# ---------------------------------------------------------------------------


def test_reference_kind_and_rho_per_block() -> None:
    """def:exact-reference: exact iff every radius is zero; rho is the max row sum."""
    r = F(1, 1 << 50)
    enclosed = Enclosure(diag(F(1, 2), F(1, 2)), ((r, r), (r, F(0))))
    assert enclosed.rho == 2 * r  # row 0: r + r; row 1: r + 0
    assert not enclosed.is_exact
    exact = Enclosure.exact(diag(F(1, 2), F(1, 2)))
    ref = Reference(
        ("a", "b"),
        (
            ReferenceBlock("m=0", (exact, exact)),
            ReferenceBlock("m=1", (enclosed, enclosed), input_radius=r),
        ),
        F(1),
        ReferenceIdentity("toy", {"eta": "1/2"}, ("receiver/thm:exact-blocks",)),
    )
    assert ref.kind is ReferenceKind.ENCLOSED
    assert ref.block_kinds == {
        "m=0": ReferenceKind.EXACT,
        "m=1": ReferenceKind.ENCLOSED,
    }
    assert ref.block("m=1").rho == 2 * r
    assert ref.decide().usable
    json.dumps(ref.as_record())


def test_structurally_zero_needs_centre_and_radius_zero() -> None:
    """def:snap: centre 0 with a positive radius is not structurally zero."""
    r = F(1, 1 << 50)
    enclosure = Enclosure(diag(1, 0), ((F(0), F(0)), (F(0), r)))
    assert enclosure.structural_support == frozenset({0, 1})
    exact = Enclosure.exact(diag(1, 0))
    assert exact.structural_support == frozenset({0})


def test_reference_row_failures_are_named() -> None:
    """req:snap-reference (i): the declarer decides the reference before the snap.

    An exact reference not complete at c; a non-Hermitian centre; asymmetric
    radii; an enclosed reference naming no establishing claim.
    """
    incomplete = exact_reference(
        ("m=0", [diag(F(1, 2)), diag(F(1, 4))]), alphabet=("a", "b")
    )
    verdict = incomplete.decide()
    assert not verdict.usable and "m=0: not_complete" in verdict.failures
    skew = Enclosure.of([[1, 1], [0, 1]], [[0, 0], [0, 0]])
    assert "centre_not_hermitian" in skew.failures()
    asym = Enclosure.of([[1, 0], [0, 1]], [[0, F(1, 4)], [0, 0]])
    assert "radii_not_symmetric" in asym.failures()
    r = F(1, 1 << 50)
    unclaimed = Reference(
        ("a",),
        (ReferenceBlock("m=0", (Enclosure(diag(1), ((r,),)),)),),
        F(1),
        ReferenceIdentity("no claim named"),
    )
    assert not unclaimed.decide().usable
