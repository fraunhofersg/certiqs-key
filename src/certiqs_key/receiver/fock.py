"""The second-quantization functor on the photon-number sectors.

Definition ``def:fock`` and Eq. ``eq:fockfunctor``, with Lemmas
``lem:fock-functor``, ``lem:fock-block-spectrum`` and ``lem:fock-monotone``.

    Fock(X) = (+)_{n>=0} (X^{(x)n})|_{Sym^n},   Fock(X)|_{Sym^0} = 1

Everything below is one photon-number BLOCK. Lemma ``lem:fock-functor`` (i) says
``Fock(X)`` commutes with every photon-number projector, so the blocks are
independent objects and nothing in this contract relates two of them.

THE BASIS ORDER IS THE TRAP
===========================
The ``subsystem_order`` convention (``interface.yaml`` ``conventions``) ends
"within a block, occupation vectors in lexicographic order of the occupation
vector", read as ASCENDING, which is what the unqualified term means. On two
modes that gives

    n = 0 :  [(0, 0)]
    n = 1 :  [(0, 1), (1, 0)]        -- the photon in the LAST mode first
    n = 2 :  [(0, 2), (1, 1), (2, 0)]

and the consequence is that the ONE-PHOTON block of ``Fock(X)`` is the matrix
of ``X`` in the REVERSED mode basis: for ``X = [[a, b], [c, d]]`` the block is
``[[d, c], [b, a]]``. An implementation that read the order the other way round
would agree with the contract on every symmetric matrix and disagree on a
triangular one.

HOW THE BLOCK IS BUILT, AND WHY THAT WAY
=========================================
Literally as Eq. ``eq:fockfunctor`` writes it: the tensor power ``X^{(x)n}`` is
formed and RESTRICTED to the symmetric subspace by the isometry whose rows are
the normalized symmetrized occupation vectors

    |m> = (1 / sqrt(N_m)) sum over the N_m = n! / prod_j(m_j!) distinct
          arrangements of m,

so that ``block = S X^{(x)n} S^T``. The ``sqrt2`` factors of the two-photon
block are exactly the normalization of ``|1,1>`` and appear here rather than in
a closed form transcribed from somewhere else. Nothing in this file is a
recurrence, a permanent formula or a generating function: the derivation the
contract gives is a restriction of a tensor power, and this is that.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from itertools import permutations, product

import numpy as np

from certiqs_key.receiver.errors import HypothesisError
from certiqs_key.receiver.numerics import Matrix, RealVector

__all__ = [
    "block_dimension",
    "block_spectrum_from_eigenvalues",
    "fock_block",
    "occupation_vectors",
    "symmetrizer",
]


def occupation_vectors(dimension: int, photons: int) -> tuple[tuple[int, ...], ...]:
    """Return the ``n``-photon occupation vectors, ASCENDING lexicographic.

    The ``subsystem_order`` convention, last clause, with the occupation basis
    of Definition ``def:fock``.
    """
    if dimension < 1:
        raise HypothesisError("an occupation vector needs at least one mode")
    if photons < 0:
        raise HypothesisError("a photon number is non-negative")
    vectors = [
        vector
        for vector in product(range(photons + 1), repeat=dimension)
        if sum(vector) == photons
    ]
    return tuple(sorted(vectors))


def block_dimension(dimension: int, photons: int) -> int:
    """Return ``binom(d + n - 1, n)`` -- ``interface.yaml`` ``block_dimensions``.

    The number of occupation vectors of weight ``n`` on ``d`` modes.
    """
    return math.comb(dimension + photons - 1, photons)


def symmetrizer(dimension: int, photons: int) -> Matrix:
    """Return the isometry from the occupation basis into ``(C^d)^{(x)n}``.

    Row ``m`` carries ``1 / sqrt(N_m)`` at every distinct arrangement of ``m``,
    with ``N_m = n! / prod_j(m_j!)``, which is the normalized symmetrized basis
    vector of Definition ``def:fock``.
    """
    vectors = occupation_vectors(dimension, photons)
    matrix = np.zeros((len(vectors), dimension**photons), dtype=np.complex128)
    for row, vector in enumerate(vectors):
        sequence: list[int] = []
        for mode, count in enumerate(vector):
            sequence.extend([mode] * count)
        arrangements = set(permutations(sequence))
        weight = 1.0 / math.sqrt(len(arrangements))
        for arrangement in arrangements:
            column = 0
            for index in arrangement:
                column = column * dimension + index
            matrix[row, column] = weight
    return matrix


def fock_block(operator: Matrix, photons: int) -> Matrix:
    """Return ``Fock(X)^{(n)}`` in the occupation basis of Def. ``def:fock``.

    Eq. ``eq:fockfunctor`` restricted to ``Sym^n``. At ``n = 0`` the block is
    the ``1 x 1`` identity, which is Definition ``def:fock``'s
    ``Fock(X)|_{Sym^0} = 1``.
    """
    if operator.ndim != 2 or operator.shape[0] != operator.shape[1]:
        raise HypothesisError("the Fock functor acts on a square operator")
    dimension = int(operator.shape[0])
    if photons == 0:
        return np.ones((1, 1), dtype=np.complex128)
    power: Matrix = np.ones((1, 1), dtype=np.complex128)
    for _ in range(photons):
        power = np.asarray(np.kron(power, operator), dtype=np.complex128)
    basis = symmetrizer(dimension, photons)
    return np.asarray(basis @ power @ basis.T, dtype=np.complex128)


def block_spectrum_from_eigenvalues(
    spectrum: Sequence[float], photons: int
) -> RealVector:
    """Return the block spectrum of Eq. ``eq:spectrum``, ascending.

    Lemma ``lem:fock-block-spectrum``: for ``0 <= A <= 1`` with eigenvalues
    ``lambda_j``, the ``n``-photon block of ``Fock(1 - A)`` has spectrum
    ``{prod_j (1 - lambda_j)^{m_j} : |m| = n}``. Eq. ``eq:blockbounds`` then
    reads ``(1 - lmax(A))^n <= block <= (1 - lmin(A))^n`` with BOTH bounds
    attained.
    """
    factors = [1.0 - value for value in spectrum]
    values = [
        math.prod(factor**count for factor, count in zip(factors, vector, strict=True))
        for vector in occupation_vectors(len(factors), photons)
    ]
    return np.asarray(sorted(values), dtype=np.float64)
