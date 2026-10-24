"""Exact dyadic matrices and a rigorous least-eigenvalue lower bound.

``foundations/lem:least-eigenvalue-bound`` and the exact arithmetic it runs on,
a certification of the exact island (``foundations/def:exact-island`` (iii)).

WHY DYADIC AND NOT :mod:`certiqs_key.foundations.exact`. Every binary64 number
is a dyadic rational, and every matrix formed from binary64 data by sums,
products, Kronecker products and halvings is dyadic again -- which is what a
certification on the exact island (``def:exact-island`` (iii)) of a solver's
binary64 output forms. Such a matrix is held here EXACTLY as two integer
matrices over one power of two, ``(re + i im) / 2**shift``, so that a product
is an integer matrix product with no gcd; the Gaussian-rational substrate of
:mod:`~certiqs_key.foundations.exact` would hold the same numbers as
``Fraction`` pairs and reduce every entry of every product. NumPy only proposes
the eigenbasis: soundness never depends on what it returns.

THE BOUND (the lemma, (ii)). In the real embedding ``Rr = [[Re R, -Im R], [Im
R, Re R]]`` with any real ``V``: ``B = V^T Rr V``, ``E = V^T V - 1``, ``theta
>= ||E||_F`` (an integer square root rounded up) and ``gamma`` the Gershgorin
bound of ``B`` give ``lambda_min(R) >= gamma / (1 + theta)``, or ``gamma / (1 -
theta)`` where ``gamma < 0``, provided ``theta < 1``. ``V`` decides tightness
only; the identity (``theta = 0``) is always admissible and is what the bound
falls back to wherever a proposed basis is unusable.

THE BASIS (two devices). ``V`` is built from the
COMPLEX eigenvectors ``u = a + ib`` of ``R`` as the column pairs ``[a; b]``,
``[-b; a]``, which are exactly orthogonal and decoupled in ``B``, so the
doubled spectrum of the embedding costs nothing. One Ogita-Aishima refinement
step, computed from the exact ``B`` and ``V^T V`` after each eigenvalue cluster
is rotated by an eigenbasis of its shifted sub-block, brings the off-diagonal
coupling and the orthogonality defect from about ``eps`` to about ``2^-100``;
without it a block of norm 300 loses about ``6e-12``.
"""

from __future__ import annotations

import itertools
import math
from collections.abc import Sequence
from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Literal

import numpy as np
import numpy.typing as npt

__all__ = [
    "DyadicMatrix",
    "ceil_sqrt",
    "dyadic_upper",
    "enclosure_eigenvalue_bounds",
    "float_down",
    "largest_eigenvalue_bound",
    "least_eigenvalue_bound",
]

#: Relative gap (to the largest entry of ``B``) below which two eigenvalue
#: estimates are one cluster in the refinement. Tightness only.
CLUSTER_TOL = 1e-6
#: The grids, as exponents of two: the float eigenbasis and cluster rotations
#: are rounded to ``2^-P_BASIS``, the refinement factor to ``2^-P_NEWTON``, the
#: final basis to ``2^-P_FINAL``. Tightness only.
P_BASIS = 60
P_NEWTON = 100
P_FINAL = 120

type IntMatrix = npt.NDArray[np.object_]


def _ints(rows: Any) -> IntMatrix:
    array = np.asarray(rows)
    flat = np.empty(array.size, dtype=object)
    flat[:] = [int(x) for x in array.ravel()]
    return flat.reshape(array.shape)


def _zeros(rows: int, cols: int) -> IntMatrix:
    out = np.empty((rows, cols), dtype=object)
    out.fill(0)
    return out


def _eye(n: int, scale: int = 1) -> IntMatrix:
    out = _zeros(n, n)
    for index in range(n):
        out[index, index] = scale
    return out


def _dyadic_parts(value: float | int | Fraction) -> tuple[int, int]:
    """Return ``(numerator, k)`` with ``value = numerator / 2**k`` exactly."""
    if isinstance(value, Fraction):
        numerator, denominator = value.numerator, value.denominator
    elif isinstance(value, (int, np.integer)):
        return int(value), 0
    else:
        number = float(value)
        if not math.isfinite(number):
            raise ValueError(f"a non-finite entry {value!r} is no dyadic rational")
        numerator, denominator = number.as_integer_ratio()
    k = denominator.bit_length() - 1
    if denominator != 1 << k:
        raise ValueError(f"{value!r} is not a dyadic rational")
    return numerator, k


def _to_float(value: int, shift: int) -> float:
    """Approximate ``value / 2**shift`` (for proposals only, never for a bound)."""
    bits = abs(value).bit_length()
    if bits > 1000:
        drop = bits - 64
        return math.ldexp(float(value >> drop), drop - shift)
    return math.ldexp(float(value), -shift)


def _float_matrix(values: IntMatrix, shift: int) -> npt.NDArray[np.float64]:
    flat = [_to_float(int(x), shift) for x in values.ravel()]
    return np.array(flat, dtype=np.float64).reshape(values.shape)


def _grid(values: npt.ArrayLike, bits: int) -> IntMatrix:
    """``round(x * 2**bits)`` entrywise as integers; refuses non-finite input."""
    scaled = np.rint(np.asarray(values, dtype=float) * float(2**bits))
    if not np.all(np.isfinite(scaled)):
        raise ArithmeticError("a proposed basis is not finite")
    return _ints(scaled)


def _ceil_isqrt(n: int) -> int:
    root = math.isqrt(n)
    return root if root * root == n else root + 1


@dataclass(frozen=True)
class DyadicMatrix:
    """A complex matrix ``(re + i im) / 2**shift``, held exactly.

    ``re`` and ``im`` are integer matrices (NumPy object arrays of Python
    integers). Every operation below is exact.
    """

    re: IntMatrix
    im: IntMatrix
    shift: int

    @staticmethod
    def from_array(values: npt.ArrayLike) -> DyadicMatrix:
        """Return the exact copy of a binary64 array, real or complex."""
        array = np.asarray(values)
        if array.ndim == 0:
            array = array.reshape(1, 1)
        if array.ndim != 2:
            raise ValueError("a dyadic matrix is two-dimensional")
        complex_array = np.asarray(array, dtype=np.complex128)
        if not np.array_equal(complex_array, array):
            raise ValueError("an entry is not a binary64 number")
        if complex_array.shape == (1, 1):  # one entry: Python's exact ratios
            real, imag = complex_array[0, 0].real, complex_array[0, 0].imag
            (rn, rk), (im_n, ik) = (
                _dyadic_parts(float(real)),
                _dyadic_parts(float(imag)),
            )
            top = max(rk, ik)
            real_part = np.empty((1, 1), dtype=object)
            imag_part = np.empty((1, 1), dtype=object)
            real_part[0, 0] = rn << (top - rk)
            imag_part[0, 0] = im_n << (top - ik)
            return DyadicMatrix(real_part, imag_part, top)
        parts = np.stack([complex_array.real, complex_array.imag])
        if not np.all(np.isfinite(parts)):
            raise ValueError("a non-finite entry is no dyadic rational")
        # x = m 2^e with m in [1/2, 1) (frexp, exact), so x = (m 2^53) / 2^(53 - e)
        # with m 2^53 an integer below 2^53 in modulus: exact in int64.
        mantissa, exponent = np.frexp(parts)
        numerators = [int(n) for n in (mantissa * 2.0**53).astype(np.int64).ravel()]
        powers = [53 - int(e) for e in exponent.ravel()]
        # Each non-zero entry in lowest terms is (n / 2^t) / 2^(k - t), t the
        # trailing zeros of n; the least common shift keeps the integers short.
        reduced = [
            k - ((n & -n).bit_length() - 1)
            for n, k in zip(numerators, powers, strict=True)
            if n
        ]
        if not reduced:
            return DyadicMatrix.zeros(*array.shape)
        shift = max(0, max(reduced))
        flat = np.empty(len(numerators), dtype=object)
        for index, (n, k) in enumerate(zip(numerators, powers, strict=True)):
            move = shift - k
            flat[index] = (n << move) if move >= 0 else (n >> -move)
        grid = flat.reshape(parts.shape)
        return DyadicMatrix(grid[0], grid[1], shift)

    @staticmethod
    def zeros(rows: int, cols: int | None = None) -> DyadicMatrix:
        """Return the zero matrix."""
        width = rows if cols is None else cols
        return DyadicMatrix(_zeros(rows, width), _zeros(rows, width), 0)

    @staticmethod
    def identity(n: int, scale: Fraction | int = 1) -> DyadicMatrix:
        """Return ``scale`` times the identity, ``scale`` dyadic."""
        numerator, k = _dyadic_parts(Fraction(scale))
        return DyadicMatrix(_eye(n, numerator), _zeros(n, n), k)

    @property
    def shape(self) -> tuple[int, int]:
        """Return the matrix shape."""
        rows, cols = self.re.shape
        return int(rows), int(cols)

    def _aligned(self, other: DyadicMatrix) -> tuple[IntMatrix, ...]:
        shift = max(self.shift, other.shift)
        up, down = 1 << (shift - self.shift), 1 << (shift - other.shift)
        return self.re * up, self.im * up, other.re * down, other.im * down

    def __add__(self, other: DyadicMatrix) -> DyadicMatrix:
        """Return the exact sum."""
        a, b, c, d = self._aligned(other)
        return DyadicMatrix(a + c, b + d, max(self.shift, other.shift))

    def __sub__(self, other: DyadicMatrix) -> DyadicMatrix:
        """Return the exact difference."""
        a, b, c, d = self._aligned(other)
        return DyadicMatrix(a - c, b - d, max(self.shift, other.shift))

    def __neg__(self) -> DyadicMatrix:
        """Return the negation."""
        return DyadicMatrix(-self.re, -self.im, self.shift)

    def __matmul__(self, other: DyadicMatrix) -> DyadicMatrix:
        """Return the exact product."""
        a, b, c, d = self.re, self.im, other.re, other.im
        return DyadicMatrix(a @ c - b @ d, a @ d + b @ c, self.shift + other.shift)

    def scale(self, factor: Fraction | int) -> DyadicMatrix:
        """Return ``factor`` times the matrix, ``factor`` dyadic."""
        numerator, k = _dyadic_parts(Fraction(factor))
        return DyadicMatrix(self.re * numerator, self.im * numerator, self.shift + k)

    @property
    def adjoint(self) -> DyadicMatrix:
        """Return the conjugate transpose."""
        return DyadicMatrix(self.re.T.copy(), -self.im.T.copy(), self.shift)

    def hermitian_part(self) -> DyadicMatrix:
        """Return ``(M + M^dagger) / 2``, exactly."""
        return DyadicMatrix(self.re + self.re.T, self.im - self.im.T, self.shift + 1)

    def kron(self, other: DyadicMatrix) -> DyadicMatrix:
        """Return the Kronecker product, ``self`` the slower factor."""

        def product(x: IntMatrix, y: IntMatrix) -> IntMatrix:
            m, n = x.shape
            p, q = y.shape
            return np.multiply.outer(x, y).transpose(0, 2, 1, 3).reshape(m * p, n * q)

        a, b, c, d = self.re, self.im, other.re, other.im
        shift = self.shift + other.shift
        if a.shape == (1, 1):  # a scalar times the other factor
            x, y = int(a[0, 0]), int(b[0, 0])
            return DyadicMatrix(c * x - d * y, d * x + c * y, shift)
        if c.shape == (1, 1):
            x, y = int(c[0, 0]), int(d[0, 0])
            return DyadicMatrix(a * x - b * y, b * x + a * y, shift)
        return DyadicMatrix(
            product(a, c) - product(b, d), product(a, d) + product(b, c), shift
        )

    def permuted(self, dims: Sequence[int], axes: Sequence[int]) -> DyadicMatrix:
        """Return the matrix with its row and column tensor factors permuted.

        ``dims`` are the row factors' dimensions (the column factors' are the
        same), and ``axes`` permutes the ``2 len(dims)`` tensor indices.
        """
        size = self.shape[0]

        def move(x: IntMatrix) -> IntMatrix:
            return x.reshape(*dims, *dims).transpose(*axes).reshape(size, size)

        return DyadicMatrix(move(self.re), move(self.im), self.shift)

    def trace(self) -> Fraction:
        """Return the real part of the trace."""
        return Fraction(
            int(sum(self.re[i, i] for i in range(self.shape[0]))), 1 << self.shift
        )

    def pairing(self, other: DyadicMatrix) -> Fraction:
        """Return ``Re tr(self other)``, both square of one size."""
        total = int(np.sum(self.re * other.re.T) - np.sum(self.im * other.im.T))
        return Fraction(total, 1 << (self.shift + other.shift))

    def is_hermitian(self) -> bool:
        """Return whether the matrix is exactly Hermitian."""
        return bool(np.all(self.re == self.re.T) and np.all(self.im == -self.im.T))

    def entry(self, row: int, col: int) -> tuple[Fraction, Fraction]:
        """Return one entry's real and imaginary parts."""
        scale = 1 << self.shift
        return (
            Fraction(int(self.re[row, col]), scale),
            Fraction(int(self.im[row, col]), scale),
        )

    def frobenius_upper(self) -> Fraction:
        """Return a dyadic upper bound on the Frobenius norm (isqrt rounded up)."""
        squares = int(np.sum(self.re * self.re) + np.sum(self.im * self.im))
        return Fraction(_ceil_isqrt(squares), 1 << self.shift)

    def to_complex(self) -> npt.NDArray[np.complex128]:
        """Return a binary64 approximation (for proposals, never for a bound)."""
        return _float_matrix(self.re, self.shift) + 1j * _float_matrix(
            self.im, self.shift
        )

    def real_embedding(self) -> IntMatrix:
        """Return ``[[Re, -Im], [Im, Re]]`` as integers, at ``self.shift``."""
        top = np.concatenate([self.re, -self.im], axis=1)
        bottom = np.concatenate([self.im, self.re], axis=1)
        return np.concatenate([top, bottom], axis=0)


def dyadic_upper(value: Fraction, bits: int = 64) -> Fraction:
    """Return a dyadic rational at least ``value``, with about ``bits`` bits."""
    if value == 0:
        return Fraction(0)
    magnitude = abs(value.numerator).bit_length() - value.denominator.bit_length()
    precision = bits - magnitude
    if precision >= 0:
        scaled = value * (1 << precision)
        return Fraction(math.ceil(scaled), 1 << precision)
    scaled = value / (1 << -precision)
    return Fraction(math.ceil(scaled) * (1 << -precision))


def float_down(value: Fraction) -> float:
    """Return the largest binary64 number at most ``value`` (rounded toward -inf)."""
    try:
        nearest = float(value)
    except OverflowError:
        return -math.inf if value < 0 else float(np.finfo(np.float64).max)
    if math.isinf(nearest):
        return -math.inf if value < 0 else float(np.finfo(np.float64).max)
    if Fraction(nearest) > value:
        nearest = math.nextafter(nearest, -math.inf)
    return nearest


def _complex_pair_basis(vectors: npt.NDArray[np.complex128]) -> npt.NDArray[np.float64]:
    real, imag = vectors.real, vectors.imag
    n = vectors.shape[0]
    basis = np.zeros((2 * n, 2 * n))
    basis[:n, :n], basis[n:, :n] = real, imag
    basis[:n, n:], basis[n:, n:] = -imag, real
    return basis


def _refined_basis(matrix: DyadicMatrix, embedded: IntMatrix) -> tuple[IntMatrix, int]:
    """Return a proposed ``V`` (integers at ``2^-bits``) and ``bits``.

    The complex-pair eigenbasis, every cluster rotated by an eigenbasis of its
    shifted sub-block, then one Ogita-Aishima step. Every step only proposes;
    a failure raises and the caller falls back.
    """
    shift = matrix.shift
    approx = matrix.to_complex()
    approx = (approx + approx.conj().T) / 2
    _, vectors = np.linalg.eigh(approx)
    basis, bits = _grid(_complex_pair_basis(vectors), P_BASIS), P_BASIS
    size = basis.shape[0]
    gram_s = basis.T @ (embedded @ basis)
    gram_n = basis.T @ basis
    s_float = _float_matrix(gram_s, shift + 2 * bits)
    n_float = _float_matrix(gram_n, 2 * bits)
    estimates = np.diag(s_float) / np.diag(n_float)
    scale = max(float(np.max(np.abs(s_float))), 1e-300)
    order = np.argsort(estimates)
    label = np.empty(size, dtype=int)
    current = 0
    label[order[0]] = 0
    for low, high in itertools.pairwise(order):
        if estimates[high] - estimates[low] > CLUSTER_TOL * scale:
            current += 1
        label[high] = current
    clusters = [np.flatnonzero(label == c) for c in range(current + 1)]
    wide = [members for members in clusters if members.size > 2]
    if wide:
        rotation = np.eye(size)
        for members in wide:
            centre = Fraction(float(np.mean(estimates[members])))
            numerator, k = _dyadic_parts(centre)
            shifted = gram_s * (1 << k) - gram_n * (numerator << shift)
            block = _float_matrix(
                shifted[np.ix_(members, members)], shift + 2 * bits + k
            )
            _, local = np.linalg.eigh((block + block.T) / 2)
            rotation[np.ix_(members, members)] = local
        q = _grid(rotation, P_BASIS)
        basis = basis @ q
        gram_s = q.T @ (gram_s @ q)
        gram_n = q.T @ (gram_n @ q)
        bits += P_BASIS
        s_float = _float_matrix(gram_s, shift + 2 * bits)
    residual = _float_matrix(_eye(size, 1 << (2 * bits)) - gram_n, 2 * bits)
    estimates = np.diag(s_float) / (1.0 - np.diag(residual))
    correction = residual / 2.0
    for i in range(size):
        for j in range(size):
            if label[i] != label[j]:
                correction[i, j] = (s_float[i, j] + estimates[j] * residual[i, j]) / (
                    estimates[j] - estimates[i]
                )
    # 1 + E ON THE INTEGER GRID: 1 + 1e-17 is 1 in binary64.
    factor = _eye(size, 1 << P_NEWTON) + _grid(correction, P_NEWTON)
    refined = basis @ factor
    drop = bits + P_NEWTON - P_FINAL
    half = 1 << (drop - 1)
    return _ints([(int(x) + half) >> drop for x in refined.ravel()]).reshape(
        refined.shape
    ), P_FINAL


def _gershgorin_bound(
    embedded: IntMatrix, shift: int, basis: IntMatrix, bits: int
) -> Fraction | None:
    """Return the lemma's bound at ``V = basis / 2**bits``; ``None`` if theta >= 1."""
    size = basis.shape[0]
    b = basis.T @ (embedded @ basis)
    defect = basis.T @ basis - _eye(size, 1 << (2 * bits))
    theta = _ceil_isqrt(int(np.sum(defect * defect)))
    one = 1 << (2 * bits)
    if theta >= one:
        return None
    radii = np.sum(np.abs(b), axis=1) - np.abs(np.diagonal(b))
    gamma = min(int(x) for x in np.diagonal(b) - radii)
    denominator = (one + theta) if gamma >= 0 else (one - theta)
    return Fraction(gamma * one, denominator << (shift + 2 * bits))


def least_eigenvalue_bound(
    matrix: DyadicMatrix,
    *,
    basis: Literal["refined", "eigen", "identity"] = "refined",
) -> Fraction:
    """Return a rational lower bound on ``lambda_min`` of a Hermitian matrix.

    Implements ``foundations/lem:least-eigenvalue-bound`` (i)-(iii): the
    Gershgorin bound of the real embedding conjugated by a real ``V``, divided
    by ``1 + theta`` (or ``1 - theta`` for a negative bound), every quantity
    exact. ``basis`` chooses ``V`` and decides tightness only: ``refined``
    (the default) the complex-pair eigenbasis with one refinement step,
    ``eigen`` the same without the step, ``identity`` the identity
    (``theta = 0``). A proposed basis that is unusable -- not finite, or with
    ``theta >= 1`` -- is replaced by the identity, which the lemma always
    admits.

    Raises:
        ValueError: the matrix is not square or not exactly Hermitian.
    """
    rows, cols = matrix.shape
    if rows == cols == 1 and matrix.im[0, 0] == 0:
        return Fraction(int(matrix.re[0, 0]), 1 << matrix.shift)
    if rows != cols or not matrix.is_hermitian():
        raise ValueError("the least-eigenvalue bound takes an exactly Hermitian matrix")
    off_diagonal = matrix.re - np.diag(np.diagonal(matrix.re))
    if not np.any(off_diagonal) and not np.any(matrix.im):
        # A DIAGONAL MATRIX: the lemma at V = 1 (theta = 0, no Gershgorin
        # radius) gives its least diagonal entry, which is lambda_min itself.
        return Fraction(min(int(x) for x in np.diagonal(matrix.re)), 1 << matrix.shift)
    embedded = matrix.real_embedding()
    if basis != "identity":
        try:
            if basis == "refined":
                proposal, bits = _refined_basis(matrix, embedded)
            else:
                approx = matrix.to_complex()
                _, vectors = np.linalg.eigh((approx + approx.conj().T) / 2)
                proposal, bits = _grid(_complex_pair_basis(vectors), P_BASIS), P_BASIS
            bound = _gershgorin_bound(embedded, matrix.shift, proposal, bits)
            if bound is not None:
                return bound
        except (ArithmeticError, ValueError, np.linalg.LinAlgError):
            pass
    bound = _gershgorin_bound(embedded, matrix.shift, _eye(2 * rows), 0)
    assert bound is not None  # theta = 0 at the identity
    return bound


def largest_eigenvalue_bound(matrix: DyadicMatrix, **options: Any) -> Fraction:
    """Return a rational upper bound on ``lambda_max`` (the lemma, (iv))."""
    return -least_eigenvalue_bound(-matrix, **options)


def ceil_sqrt(value: Fraction, bits: int = 128) -> Fraction:
    """Return a dyadic ``rho >= 0`` with ``rho^2 >= value`` (a root rounded up)."""
    if value <= 0:
        return Fraction(0)
    size = value.numerator.bit_length() - value.denominator.bit_length()
    t = max(0, (bits - size) // 2)
    return Fraction(_ceil_isqrt(math.ceil(value * 4**t)), 1 << t)


def enclosure_eigenvalue_bounds(
    centre: Sequence[Sequence[Any]],
    radii: Sequence[Sequence[Fraction]],
    *,
    bits: int = 160,
) -> tuple[Fraction, Fraction]:
    """Return ``l <= lambda_min(X)`` and ``u >= lambda_max(X)`` over an enclosure.

    For every Hermitian ``X`` with ``|X_il - C_il| <= r_il``, ``C`` with
    rational ``.re`` and ``.im``: ``foundations/cor:least-eigenvalue-over-
    enclosure`` (i), (ii). The pair is made Hermitian-centred with symmetric
    radii (``foundations/lem:recentred-enclosure`` (iv)); the centre is
    rounded to a Hermitian dyadic ``M`` on a grid ``bits`` below its largest
    entry, each rounding added to its entry's radius, so ``M`` encloses ``X``
    as well; ``rho^2 >= sum r^2`` bounds ``||X - M||_F``; and ``l`` and ``u``
    are the bounds of ``foundations/lem:least-eigenvalue-bound`` (ii), (iv)
    on ``M`` less and plus ``rho``. Exact throughout.
    """
    n = len(centre)
    half = Fraction(1, 2)
    entries: dict[tuple[int, int], tuple[Fraction, Fraction]] = {
        (i, j): (
            (Fraction(centre[i][j].re) + Fraction(centre[j][i].re)) * half,
            (Fraction(centre[i][j].im) - Fraction(centre[j][i].im)) * half,
        )
        for i in range(n)
        for j in range(i, n)
    }
    largest = max(max(abs(a), abs(b)) for a, b in entries.values())
    size = largest.numerator.bit_length() - largest.denominator.bit_length()
    scale = 1 << max(0, bits - size)
    re, im = _zeros(n, n), _zeros(n, n)
    total = Fraction(0)
    for (i, j), (a, b) in entries.items():
        x, y = round(a * scale), (round(b * scale) if i != j else 0)
        re[i, j], im[i, j], re[j, i], im[j, i] = x, y, x, -y
        error = abs(a - Fraction(x, scale)) + abs(b - Fraction(y, scale))
        radius = (Fraction(radii[i][j]) + Fraction(radii[j][i])) * half
        total += (1 if i == j else 2) * (radius + error) ** 2
    middle = DyadicMatrix(re, im, scale.bit_length() - 1)
    rho = ceil_sqrt(total)
    return least_eigenvalue_bound(middle) - rho, largest_eigenvalue_bound(middle) + rho
