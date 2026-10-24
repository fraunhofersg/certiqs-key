"""Ball arithmetic for the certified tier: matrix enclosures and matrix functions.

``foundations/def:tiers`` (iii): a computation is *rigorously enclosed* when each
operation returns a set containing its exact result at every value its inputs'
sets contain. Every routine here is such an operation, on complex matrices of
Arb balls (python-flint, the optional extra ``certify``). The library is
implementation, not a premise: no assumption is stated for it, and its version
goes into the run record.

THE ONLY MODULE THAT IMPORTS python-flint, guarded (:data:`AVAILABLE`); the
engine imports it only where it certifies, so a run with the evaluation off
never loads the library. Here: :class:`Ball`; the Cholesky factor and the
triangular inverse; the matrix functions of
``foundations/lem:matrix-function-perturbation``; and :func:`least_eigenvalue`,
``foundations/cor:least-eigenvalue-over-enclosure`` (i), (ii) on
:mod:`~certiqs_key.foundations.dyadic`; and :func:`log2_enclosure`, the
enclosure of ``log2(1/tau)`` that ``meat-core/req:unreachable-acceptance-set``
(iv) compares the pass cap's exponent with. The pitfalls: Arb's ``x ** 2`` of a
ball containing 0 is NaN, so squares are products; flint's rigorous ``eig``
fails on exact multiplicities, so its approximate eigenvectors are a proposal
and the enclosure is Weyl's (:func:`spectral`); close points' divided
differences take the second-order expansion.
"""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from fractions import Fraction
from typing import Any

import numpy as np

from certiqs_key.foundations.dyadic import DyadicMatrix, enclosure_eigenvalue_bounds
from certiqs_key.foundations.exact import Cx

try:
    import flint

    #: Whether the optional extra is installed (a test sets it false).
    AVAILABLE = True
except ImportError:  # pragma: no cover - the optional extra `certify` is absent
    AVAILABLE = False

__all__ = [
    "AVAILABLE",
    "Ball",
    "NotCertified",
    "Spectral",
    "arithmetic_library",
    "cholesky_upper",
    "deriv_power",
    "inverse_upper",
    "least_eigenvalue",
    "log2_enclosure",
    "power",
    "precision",
    "real",
    "spectral",
    "trace_power",
    "upper",
]


class NotCertified(ArithmeticError):
    """A quantity that must be positive is not certified positive; the cause."""


def arithmetic_library() -> str | None:
    """Return ``"python-flint <version>"``, or ``None`` without the extra."""
    return f"python-flint {flint.__version__}" if AVAILABLE else None


@contextmanager
def precision(bits: int) -> Iterator[None]:
    """Run the block at a working precision of ``bits`` bits, then restore it."""
    old, flint.ctx.prec = flint.ctx.prec, bits
    try:
        yield
    finally:
        flint.ctx.prec = old


def real(value: Fraction | int | float) -> Any:
    """Return the ball of an exact rational (a binary64 number is one)."""
    f = Fraction(value)
    return flint.arb(flint.fmpq(f.numerator, f.denominator))


def _scalar(value: Any) -> Any:
    if isinstance(value, Cx):
        return flint.acb(real(value.re), real(value.im))
    z = value if isinstance(value, (Fraction, int)) else complex(value)
    return flint.acb(real(z.real), real(z.imag))


def _exact(x: Any) -> Fraction:
    """Return the exact value of an exact Arb number (a midpoint or a radius)."""
    man, exp = (int(v) for v in x.man_exp())
    return Fraction(man << exp) if exp >= 0 else Fraction(man, 1 << -exp)


def upper(x: Any) -> Fraction:
    """Return an exact rational at least every member of a real ball."""
    return _exact(x.mid()) + _exact(x.rad())


def log2_enclosure(value: Fraction, bits: int = 128) -> tuple[Fraction, Fraction]:
    """Return exact rationals ``lo <= log2(value) <= hi`` for a rational ``value > 0``.

    The Arb ball of ``log(value) / log(2)`` at ``bits`` bits of working
    precision, its two ends read exactly: a rigorous enclosure in the sense
    of ``foundations/def:tiers`` (iii). Without the optional extra the
    enclosure is the integer one, ``[k, k + 1]`` with ``2^k <= value <
    2^(k+1)``, decided in integer arithmetic: as rigorous, only wider.
    """
    if not value > 0:
        raise ValueError(f"log2 of {value} is not defined")
    if not AVAILABLE:
        k = value.numerator.bit_length() - value.denominator.bit_length()
        if Fraction(2) ** k > value:
            k -= 1
        elif Fraction(2) ** (k + 1) <= value:
            k += 1
        return Fraction(k), Fraction(k + 1)
    with precision(bits):
        ball = real(value).log() / flint.arb(2).log()
        mid, rad = _exact(ball.mid()), _exact(ball.rad())
    return mid - rad, mid + rad


def _matrix(rows: int, cols: int, entry: Any) -> Any:
    out = flint.acb_mat(rows, cols)
    for i in range(rows):
        for j in range(cols):
            out[i, j] = entry(i, j)
    return out


class Ball:
    """A complex matrix of balls; every operation is inclusion-isotone."""

    __slots__ = ("m",)

    def __init__(self, m: Any) -> None:
        """Wrap a python-flint ``acb_mat``."""
        self.m = m

    @staticmethod
    def of(rows: Sequence[Sequence[Any]]) -> Ball:
        """Return the balls of exact entries (``Cx``, rationals, binary64 numbers)."""
        width = len(rows[0]) if rows else 0
        return Ball(_matrix(len(rows), width, lambda i, j: _scalar(rows[i][j])))

    @staticmethod
    def from_dyadic(d: DyadicMatrix) -> Ball:
        """Return the balls of an exact dyadic matrix."""
        scale = Fraction(1, 1 << d.shift)
        return Ball(
            _matrix(
                *d.shape,
                lambda i, j: flint.acb(
                    real(int(d.re[i, j]) * scale), real(int(d.im[i, j]) * scale)
                ),
            )
        )

    @staticmethod
    def enclosure(centre: Sequence[Sequence[Cx]], radii: Any) -> Ball:
        """Return a box containing every ``X`` with ``|X_il - C_il| <= r_il``.

        Square or rectangular (a factor enclosure's box of columns,
        ``foundations/def:factor-enclosure``); the width is the first row's.
        """

        def entry(i: int, j: int) -> Any:
            halo = flint.arb(0, real(radii[i][j]))
            return flint.acb(real(centre[i][j].re) + halo, real(centre[i][j].im) + halo)

        width = len(centre[0]) if centre else 0
        return Ball(_matrix(len(centre), width, entry))

    @staticmethod
    def zeros(rows: int, cols: int | None = None) -> Ball:
        """Return the zero matrix."""
        return Ball(flint.acb_mat(rows, rows if cols is None else cols))

    @staticmethod
    def stack(parts: Sequence[Ball]) -> Ball:
        """Return the parts stacked row-wise; they share their number of columns."""
        rows = [(part, i) for part in parts for i in range(part.shape[0])]
        width = parts[0].shape[1] if parts else 0
        return Ball(_matrix(len(rows), width, lambda r, j: rows[r][0].m[rows[r][1], j]))

    @staticmethod
    def block_diagonal(parts: Sequence[Ball]) -> Ball:
        """Return the block-diagonal matrix of square parts, zero elsewhere."""
        out = Ball.zeros(sum(part.shape[0] for part in parts))
        offset = 0
        for part in parts:
            k = part.shape[0]
            for i in range(k):
                for j in range(k):
                    out.m[offset + i, offset + j] = part.m[i, j]
            offset += k
        return out

    @property
    def shape(self) -> tuple[int, int]:
        """Return the matrix shape."""
        return int(self.m.nrows()), int(self.m.ncols())

    def __add__(self, other: Ball) -> Ball:
        """Return the sum."""
        return Ball(self.m + other.m)

    def __sub__(self, other: Ball) -> Ball:
        """Return the difference."""
        return Ball(self.m - other.m)

    def __matmul__(self, other: Ball) -> Ball:
        """Return the product."""
        return Ball(self.m * other.m)

    def scale(self, factor: Any) -> Ball:
        """Return the matrix times a scalar ball."""
        return Ball(self.m * flint.acb(factor))

    @property
    def adjoint(self) -> Ball:
        """Return the conjugate transpose."""
        return Ball(self.m.transpose().conjugate())

    def hermitian_part(self) -> Ball:
        """Return ``(X + X^dagger)/2``, which contains every Hermitian member."""
        return Ball((self.m + self.m.transpose().conjugate()) * flint.acb(0.5))

    def kron(self, other: Ball) -> Ball:
        """Return the Kronecker product, ``self`` the slower factor."""
        (ra, ca), (rb, cb) = self.shape, other.shape
        return Ball(
            _matrix(
                ra * rb,
                ca * cb,
                lambda i, j: self.m[i // rb, j // cb] * other.m[i % rb, j % cb],
            )
        )

    def permuted(self, dims: Sequence[int], axes: Sequence[int]) -> Ball:
        """Return the matrix with its tensor factors permuted, as ``DyadicMatrix``."""
        n = self.shape[0]
        index = np.arange(n * n).reshape(*dims, *dims).transpose(*axes).reshape(n, n)
        return Ball(
            _matrix(
                n, n, lambda i, j: self.m[int(index[i, j]) // n, int(index[i, j]) % n]
            )
        )

    def block(self, rows: Sequence[int], cols: Sequence[int]) -> Ball:
        """Return the submatrix on the given rows and columns."""

        def entry(a: int, b: int) -> Any:
            return self.m[rows[a], cols[b]]

        return Ball(_matrix(len(rows), len(cols), entry))

    def congruence(self, d: Sequence[Any]) -> Ball:
        """Return ``diag(d) X diag(d)`` for real balls ``d``."""
        n = self.shape[0]
        return Ball(_matrix(n, n, lambda i, j: self.m[i, j] * (d[i] * d[j])))

    def trace_re(self) -> Any:
        """Return ``Re tr X``."""
        return sum((self.m[i, i].real for i in range(self.shape[0])), flint.arb(0))

    def pairing_re(self, other: Ball) -> Any:
        """Return ``Re tr(X Y)`` without forming the product."""
        n = self.shape[0]
        return sum(
            (self.m[i, k] * other.m[k, i] for i in range(n) for k in range(n)),
            flint.acb(0),
        ).real

    def beyond(self, i: int, j: int, centre: Cx, radius: Fraction) -> bool:
        """Whether entry ``(i, j)`` lies farther than ``radius`` from ``centre``.

        For every member, certainly: the lower end of ``|X_ij - centre|`` over
        the ball exceeds the rational ``radius``, so the ball and the disc of
        that radius around ``centre`` are disjoint. ``False`` decides nothing.
        """
        gap = abs(self.m[i, j] - _scalar(centre))
        return bool(gap > real(radius))

    def frobenius_upper(self) -> Any:
        """Return an exact ball at least ``||X||_F`` for every member."""
        tops = [
            abs(self.m[i, j]).upper()
            for i in range(self.shape[0])
            for j in range(self.shape[1])
        ]
        return sum((t * t for t in tops), flint.arb(0)).sqrt().upper()

    def entrywise(self) -> tuple[Any, Any]:
        """Return an entrywise enclosure: the midpoints and ``rad re + rad im``."""
        rows, cols = self.shape
        parts = [
            [(self.m[i, j].real, self.m[i, j].imag) for j in range(cols)]
            for i in range(rows)
        ]
        return (
            tuple(
                tuple(Cx(_exact(a.mid()), _exact(b.mid())) for a, b in row)
                for row in parts
            ),
            tuple(
                tuple(_exact(a.rad()) + _exact(b.rad()) for a, b in row)
                for row in parts
            ),
        )

    def radius(self) -> float:
        """Return the largest radius of a real or imaginary part (a diagnostic)."""
        rows, cols = self.shape
        return max(
            (
                float(part.rad())
                for i in range(rows)
                for j in range(cols)
                for part in (self.m[i, j].real, self.m[i, j].imag)
            ),
            default=0.0,
        )


def least_eigenvalue(matrix: Ball) -> Fraction:
    """Return a rational lower bound on ``lambda_min`` of every Hermitian member.

    ``foundations/cor:least-eigenvalue-over-enclosure`` (i), (ii) on the
    entrywise enclosure the balls are, made Hermitian-centred by
    ``foundations/lem:recentred-enclosure`` (iv)
    (:func:`~certiqs_key.foundations.dyadic.enclosure_eigenvalue_bounds`).
    """
    return enclosure_eigenvalue_bounds(*matrix.entrywise())[0]


def cholesky_upper(gram: Ball, what: str) -> Ball:
    """Return upper triangular ``R``, ``R^dagger R = G`` for every Hermitian member.

    A pivot not certified positive raises :class:`NotCertified`; where every
    pivot is, every member is positive definite, which is how a Gram matrix
    certifies an injective map (``req:certified-evaluation`` (iii)(a)).
    """
    n = gram.shape[0]
    r = flint.acb_mat(n, n)
    for k in range(n):
        pivot = gram.m[k, k].real - sum(
            (abs(r[i, k]) * abs(r[i, k]) for i in range(k)), flint.arb(0)
        )
        if not pivot > 0:
            raise NotCertified(f"{what}: Cholesky pivot {k} not certified positive")
        r[k, k] = flint.acb(pivot.sqrt())
        for j in range(k + 1, n):
            r[k, j] = (
                gram.m[k, j]
                - sum((r[i, k].conjugate() * r[i, j] for i in range(k)), flint.acb(0))
            ) / r[k, k]
    return Ball(r)


def inverse_upper(r: Ball) -> Ball:
    """Return the inverse of an upper triangular ball matrix (back substitution)."""
    n = r.shape[0]
    out = flint.acb_mat(n, n)
    for j in range(n):
        for i in range(j, -1, -1):
            known = (r.m[i, k] * out[k, j] for k in range(i + 1, j + 1))
            t = flint.acb(int(i == j)) - sum(known, flint.acb(0))
            out[i, j] = t / r.m[i, i]
    return Ball(out)


@dataclass(frozen=True)
class Spectral:
    """An enclosed spectral decomposition of a Hermitian ball matrix ``A``.

    ``u`` encloses one exactly unitary ``U``, ``lam`` are exact points and
    ``e >= ||U^dagger A* U - diag(lam)||_F`` for every member ``A*``, so by
    ``foundations/cor:least-eigenvalue-over-enclosure`` (i) the spectra of every
    member and of ``U diag(lam) U^dagger`` lie in ``[lo, hi]``.
    """

    u: Ball
    lam: tuple[Any, ...]
    e: Any
    lo: Any
    hi: Any


def _gram_schmidt(v: Any) -> Ball:
    """Return ball Gram-Schmidt of a POINT matrix: its exactly unitary image."""
    n = int(v.nrows())
    done: list[list[Any]] = []
    for k in range(n):
        w = [v[i, k] for i in range(n)]
        for u in done:
            proj = sum((u[i].conjugate() * w[i] for i in range(n)), flint.acb(0))
            w = [w[i] - proj * u[i] for i in range(n)]
        norm2 = sum((abs(x) * abs(x) for x in w), flint.arb(0))
        if not norm2 > 0:
            raise NotCertified("the proposed eigenbasis is degenerate")
        done.append([x / norm2.sqrt() for x in w])
    return Ball(_matrix(n, n, lambda i, k: done[k][i]))


def spectral(a: Ball) -> Spectral:
    """Return :class:`Spectral` of a Hermitian ball matrix, at any multiplicities.

    The midpoint's approximate eigenvectors (flint's QR, a proposal only; the
    identity where it fails) orthonormalised by :func:`_gram_schmidt`; ``lam``
    the midpoints of the diagonal of ``U^dagger A U``; ``e`` bounds the rest.
    """
    n = a.shape[0]
    point = Ball(_matrix(n, n, lambda i, j: a.m[i, j].mid())).hermitian_part().m
    try:
        _, vectors = point.eig(right=True, algorithm="approx")
        u = _gram_schmidt(_matrix(n, n, lambda i, j: vectors[i, j].mid()))
    except (ValueError, ArithmeticError):
        u = Ball.of([[int(i == j) for j in range(n)] for i in range(n)])
    rest = (u.adjoint @ a @ u).m
    lam = tuple(rest[i, i].real.mid() for i in range(n))
    for i in range(n):
        rest[i, i] -= lam[i]
    e = Ball(rest).frobenius_upper()
    # The extremes are chosen EXACTLY: two midpoints that round to one binary64
    # number tie under a float key, and min/max then return the first of them,
    # not the least or the largest.
    return Spectral(u, lam, e, min(lam, key=_exact) - e, max(lam, key=_exact) + e)


def _floor(sp: Spectral, what: str) -> Any:
    if not sp.lo > 0:
        raise NotCertified(f"{what}: floor {float(sp.lo.lower()):.3e} is not > 0")
    return sp.lo.lower()


def _widened(core: Ball, error: Any) -> Ball:
    """Return ``core`` with every entry's parts widened by ``error``."""
    halo = flint.arb(0, error.upper())
    return Ball(
        _matrix(
            *core.shape,
            lambda i, j: flint.acb(core.m[i, j].real + halo, core.m[i, j].imag + halo),
        )
    )


def _lipschitz(s: Any, lo: Any, hi: Any) -> Any:
    """Return ``s max{lo^(s-1), hi^(s-1)} >= |d/dx x^s|`` on ``[lo, hi]``: (i)."""
    return (s * lo ** (s - 1)).union(s * hi ** (s - 1)).upper()


def power(sp: Spectral, s: Any, what: str) -> Ball:
    """Return ``A*^s`` of every member, ``s > 0``: the lemma, (i) and (ii).

    ``U diag(lam^s) U^dagger`` with every entry widened by ``L e``.
    """
    lo, n = _floor(sp, what), len(sp.lam)
    diagonal = Ball(_matrix(n, n, lambda i, j: sp.lam[i] ** s if i == j else 0))
    core = sp.u @ diagonal @ sp.u.adjoint
    return _widened(core, _lipschitz(s, lo, sp.hi.upper()) * sp.e)


def trace_power(sp: Spectral, s: Any, what: str) -> Any:
    """Return ``tr A*^s`` of every member: ``sum lam^s +- sqrt(n) L e`` (i)."""
    lo = _floor(sp, what)
    error = _lipschitz(s, lo, sp.hi.upper()) * flint.arb(len(sp.lam)).sqrt() * sp.e
    return sum((x**s for x in sp.lam), flint.arb(0)) + flint.arb(0, error.upper())


def _divided(x: Any, y: Any, p: Any) -> Any:
    """Return ``f^[1](x, y)`` of ``f = t^p`` at exact ``x, y > 0``: (iii)(c), (iv)."""
    if x == y:
        return p * x ** (p - 1)
    if abs(float(x - y)) > 2.0 ** (-flint.ctx.prec / 3) * max(float(x), float(y)):
        return (x**p - y**p) / (x - y)
    d = x - y
    third = abs(p * (p - 1) * (p - 2)) * x.union(y).lower() ** (p - 3)
    return p * ((x + y) / 2) ** (p - 1) + flint.arb(0, (d * d / 24 * third).upper())


def deriv_power(sp: Spectral, p: Any, h: Ball, what: str) -> Ball:
    """Return ``D_{A*}[H*]`` of ``f = t^p``, ``0 < p < 1``, for every member: (iii).

    ``U (K o U^dagger H U) U^dagger``, ``K`` the divided differences at
    ``lam``, every entry widened by ``p (1 - p) a^(p - 2) e ||H||_F``.
    """
    lo, n = _floor(sp, what), len(sp.lam)
    rotated = (sp.u.adjoint @ h @ sp.u).m
    core = Ball(
        _matrix(n, n, lambda i, j: rotated[i, j] * _divided(sp.lam[i], sp.lam[j], p))
    )
    error = p * (1 - p) * lo ** (p - 2) * sp.e * h.frobenius_upper()
    return _widened(sp.u @ core @ sp.u.adjoint, error)
