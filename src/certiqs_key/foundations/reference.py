"""A reference of a measurement family: exact, or known through enclosures.

WHAT THIS MODULE IS FOR
=======================
A snap moves a declared measurement family onto the ``2^-k`` lattice
(``foundations/def:snap``). ``meat-core/prop:optol-nobound`` shows that an
entrywise small move can still change the key rate without bound, so no claim
relates a snapped family to the model it replaced. A run that holds a
**reference** of the family (``foundations/def:exact-reference``) hands it
beside the snap (``foundations/def:evaluated-off-snap`` (i)) and evaluates the
numbers its key length rests on with the reference in place of the snap
(``meat-core/frank-wolfe/req:bracket-on-reference``); the snap itself runs on
the centres of the blocks known exactly (``foundations/req:snap-reference``
(ii)). This module holds the reference and the decisions taken on it, and
nothing that decides how a family is snapped (that is
:mod:`certiqs_key.foundations.snap`):

* :class:`Enclosure`, :class:`ReferenceBlock`, :class:`Reference` -- per
  block and outcome a Hermitian Gaussian-rational centre and symmetric
  rational radii, radius zero meaning known exactly; :meth:`Reference.decide`
  takes the decisions ``foundations/req:snap-reference`` (i) asks of a
  declarer's reference;
* :func:`enclosure_psd` and :func:`enclosure_pd` -- the sufficient condition
  of ``foundations/lem:enclosure-psd`` (i), decided by the exact ``LDL^*`` of
  :mod:`certiqs_key.foundations.exact`; :func:`scaled_enclosure` and
  :func:`inverse_sqrt_enclosure` -- item (ii), the enclosure of a block
  ``D^-1 S D^-1`` with ``D = diag(sqrt n_i)``;
* :class:`FactorEnclosure` -- ``foundations/def:factor-enclosure``, a block
  known as ``L W L^dagger`` with ``L`` in a box of columns and ``W`` an exact
  positive diagonal core, carried beside a block's entrywise enclosure
  (:attr:`Enclosure.factor`); :func:`fixes_rank` -- the rank it fixes,
  ``foundations/cor:rank-over-factor-enclosure``, decided exactly.

THE EXACT ISLAND
================
Every decision here is an exact rational ``LDL^*`` or an exact comparison of
rationals (``foundations/def:exact-island``); nothing is computed in binary64.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from fractions import Fraction

from certiqs_key.foundations.errors import HypothesisError, MalformedInputError
from certiqs_key.foundations.exact import (
    Cx,
    Matrix,
    as_rational,
    as_scalar,
    is_complete_at,
    is_hermitian,
    is_positive_definite,
    is_positive_semidefinite,
)

__all__ = [
    "Enclosure",
    "FactorEnclosure",
    "Radii",
    "Reference",
    "ReferenceBlock",
    "ReferenceIdentity",
    "ReferenceKind",
    "ReferenceVerdict",
    "enclosure_pd",
    "enclosure_psd",
    "fixes_rank",
    "gram_radius",
    "inverse_sqrt_enclosure",
    "scaled_enclosure",
]

#: The rationals of a radius matrix, row by row.
Radii = tuple[tuple[Fraction, ...], ...]


class ReferenceKind(StrEnum):
    """The reference kind a snap record names per block (``req:who-snaps``).

    ``exact``: every radius zero; ``enclosed``: some radius not zero, recorded
    with its largest radius; ``none``: no reference, recorded with its cause
    (``foundations/req:snap-reference`` (iii)(a)).
    """

    EXACT = "exact"
    ENCLOSED = "enclosed"
    NONE = "none"


# ---------------------------------------------------------------------------
#  Small exact helpers
# ---------------------------------------------------------------------------

def _shift(m: Matrix, amount: Fraction) -> Matrix:
    """Return ``m - amount * 1``, exactly."""
    shift = Cx(amount, Fraction(0))
    return tuple(
        tuple(entry - shift if i == j else entry for j, entry in enumerate(row))
        for i, row in enumerate(m)
    )


def _square_dimension(m: Matrix, what: str) -> int:
    """Return the dimension of a non-empty square exact matrix, or raise."""
    if not m or any(len(row) != len(m) for row in m):
        raise MalformedInputError(f"{what} is not a non-empty square matrix")
    if not all(isinstance(entry, Cx) for row in m for entry in row):
        raise MalformedInputError(
            f"{what} has an entry that is not an exact Gaussian rational (Cx)"
        )
    return len(m)


# ---------------------------------------------------------------------------
#  lem:enclosure-psd (i): the sufficient condition, decided exactly
# ---------------------------------------------------------------------------


def _row_sum_radius(radii: Radii) -> Fraction:
    """Return ``rho = max_i sum_l r_il`` (``foundations/lem:enclosure-psd`` (i))."""
    return max((sum(row, Fraction(0)) for row in radii), default=Fraction(0))


def enclosure_psd(
    centre: Matrix,
    radii: Radii,
    *,
    margin: Fraction = Fraction(0),
) -> bool:
    """Decide ``X_c - (rho + mu) 1 >= 0`` exactly; True implies ``X >= mu 1``.

    Implements ``foundations/lem:enclosure-psd`` (i) at the radius
    ``rho = max_i sum_l r_il``, for every Hermitian ``X`` with
    ``|X_il - (X_c)_il| <= r_il``. The decision is the rational ``LDL^*`` of
    :func:`certiqs_key.foundations.exact.is_positive_semidefinite`; at radius
    zero and margin zero it **is** the exact decision of ``X_c >= 0``.

    It is a sufficient condition only. ``False`` says nothing about ``X``: a
    matrix whose least eigenvalue is below its enclosure's uncertainty is in
    general not established, and a finer enclosure is the remedy.

    Args:
        centre: the Hermitian Gaussian-rational centre ``X_c``.
        radii: the non-negative rationals ``r_il``, same shape.
        margin: ``mu >= 0``.

    Raises:
        MalformedInputError: on a ragged argument or a negative margin.
        HypothesisError: if the centre is not Hermitian.
    """
    dimension = _square_dimension(centre, "the centre")
    if len(radii) != dimension or any(len(row) != dimension for row in radii):
        raise MalformedInputError("the radii do not have the centre's shape")
    mu = as_rational(margin)
    if mu < 0:
        raise MalformedInputError(f"margin {mu} is negative (lem:enclosure-psd (i))")
    return is_positive_semidefinite(_shift(centre, _row_sum_radius(radii) + mu))


def enclosure_pd(centre: Matrix, radii: Radii) -> bool:
    """Decide that ``X_c - rho 1`` is positive definite; True implies ``X > 0``.

    The last clause of ``foundations/lem:enclosure-psd`` (i), at
    ``rho = max_i sum_l r_il``. At radius zero it is the exact decision that
    ``X_c`` is positive definite.
    """
    dimension = _square_dimension(centre, "the centre")
    if len(radii) != dimension or any(len(row) != dimension for row in radii):
        raise MalformedInputError("the radii do not have the centre's shape")
    return is_positive_definite(_shift(centre, _row_sum_radius(radii)))


# ---------------------------------------------------------------------------
#  def:factor-enclosure and cor:rank-over-factor-enclosure
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FactorEnclosure:
    """A factor enclosure ``(L_c, t, W)`` of one block: ``def:factor-enclosure``.

    Implements ``foundations/def:factor-enclosure``. ``centre`` is the centre
    ``L_c`` of the matrix box, ``d`` rows of ``k`` Gaussian rationals (``d``
    empty rows where ``k = 0``); ``radii`` its radii ``t``, of the same shape;
    ``core`` the ``k`` diagonal entries of ``W``. A factor is a complex
    ``d x k`` matrix ``L`` with ``|L_im - (L_c)_im| <= t_im``, and the members
    are the matrices ``L W L^dagger``; with no column the one member is ``0``.

    WHAT IS DECIDED HERE. That the centre has entries in ``Q(i)`` holds by
    type; that the radii are non-negative and the core positive is
    :meth:`failures`, the declarer's decisions of
    ``foundations/req:snap-reference`` (i) -- a factor enclosure failing one is
    not carried. That a block is a MEMBER is the constructing module's claim
    and is never decided here (the same requirement; (H-FAC) of
    ``meat-core/frank-wolfe/lem:certified-bracket-enclosed``).
    """

    centre: Matrix
    radii: Radii
    core: tuple[Fraction, ...]

    def __post_init__(self) -> None:
        """Refuse a ragged or non-exact presentation; the rest is :meth:`failures`."""
        if not self.centre:
            raise MalformedInputError("a factor enclosure has d >= 1 rows")
        k = len(self.core)
        if (
            len(self.radii) != len(self.centre)
            or any(len(row) != k for row in self.centre)
            or any(len(row) != k for row in self.radii)
        ):
            raise MalformedInputError(
                "a factor enclosure's centre and radii are d x k, k its core's length"
            )
        if not all(isinstance(entry, Cx) for row in self.centre for entry in row):
            raise MalformedInputError(
                "a factor enclosure's centre has Gaussian-rational (Cx) entries"
            )
        if not all(
            isinstance(value, Fraction)
            for value in (*self.core, *(r for row in self.radii for r in row))
        ):
            raise MalformedInputError(
                "a factor enclosure's radii and core are exact rationals (Fraction)"
            )

    @classmethod
    def no_column(cls, dimension: int) -> FactorEnclosure:
        """Return the factor enclosure with no column of a ``d x d`` block."""
        empty: tuple[tuple[Cx, ...], ...] = tuple(() for _ in range(dimension))
        return cls(empty, tuple(() for _ in range(dimension)), ())

    @property
    def dimension(self) -> int:
        """The block dimension ``d``."""
        return len(self.centre)

    @property
    def columns(self) -> int:
        """Its number of columns ``k``."""
        return len(self.core)

    @property
    def largest_radius(self) -> Fraction:
        """The largest radius of the box."""
        return max((r for row in self.radii for r in row), default=Fraction(0))

    def failures(self) -> tuple[str, ...]:
        """Return the decisions of ``req:snap-reference`` (i) that fail here."""
        out: list[str] = []
        if any(r < 0 for row in self.radii for r in row):
            out.append("factor_radius_negative")
        if any(w <= 0 for w in self.core):
            out.append("factor_core_not_positive")
        return tuple(out)

    def as_record(self) -> dict[str, object]:
        """JSON-ready: exact rationals as strings, never floats."""
        return {
            "centre": [[str(entry) for entry in row] for row in self.centre],
            "radii": [[str(r) for r in row] for row in self.radii],
            "core": [str(w) for w in self.core],
        }


def _upper_sqrt(value: Fraction, bits: int = 64) -> Fraction:
    """Return a rational at least ``sqrt(value)``, within ``2^-bits`` relative."""
    if value <= 0:
        return Fraction(0)
    size = value.numerator.bit_length() - value.denominator.bit_length()
    shift = max(0, bits - size // 2 + 1)
    scaled = value * (1 << (2 * shift))
    ceiling = -(-scaled.numerator // scaled.denominator)
    root = math.isqrt(ceiling)
    if root * root < ceiling:
        root += 1
    return Fraction(root, 1 << shift)


def gram_radius(factor: FactorEnclosure) -> Fraction:
    """Return ``rho``, ``||L^dagger L - L_c^dagger L_c||_F <= rho`` for every factor.

    ``foundations/cor:rank-over-factor-enclosure`` (iii): with
    ``a_im = |Re (L_c)_im| + |Im (L_c)_im|``, ``s_ml = sum_i (a_im t_il +
    t_im a_il + t_im t_il)`` (Eq. ``eq:gram-radius``), every rational ``rho``
    with ``rho^2 >= sum_ml s_ml^2`` qualifies; this one is the least such
    rational on a grid ``2^-64`` relative below the square root.
    """
    d, k = factor.dimension, factor.columns
    a = [
        [abs(entry.re) + abs(entry.im) for entry in row] for row in factor.centre
    ]
    t = factor.radii
    total = Fraction(0)
    for m in range(k):
        for col in range(k):
            s = sum(
                (
                    a[i][m] * t[i][col] + t[i][m] * a[i][col] + t[i][m] * t[i][col]
                    for i in range(d)
                ),
                Fraction(0),
            )
            total += s * s
    return _upper_sqrt(total)


def fixes_rank(factor: FactorEnclosure) -> bool:
    """Decide that a Gram floor fixes the rank ``k`` at every member, exactly.

    ``foundations/cor:rank-over-factor-enclosure`` (ii) with its part (iii)'s
    choice: ``G = L_c^dagger L_c`` (Hermitian, entries in ``Q(i)``) and
    ``rho`` of :func:`gram_radius`. Some rational ``l <= lambda_min(G)`` with
    ``l - rho > 0`` exists exactly when ``G - rho 1`` is positive definite,
    which the exact ``LDL^*`` of
    :func:`~certiqs_key.foundations.exact.is_positive_definite` decides: a
    comparison of rationals, no eigenvalue computed. ``True`` gives, at every
    member ``X = L W L^dagger``, ``X = E^dagger W E`` with ``E = L^dagger`` of
    rank ``k``, so ``rank X = k`` and ``X != 0``. With no column, or more
    columns than rows (then ``G`` is singular and the decision would fail
    anyway), it is ``False``; part (i), no column, is the zero member, decided
    by the caller from :attr:`FactorEnclosure.columns`.
    """
    d, k = factor.dimension, factor.columns
    if k == 0 or k > d:
        return False
    rho = gram_radius(factor)
    zero = Fraction(0)
    gram = tuple(
        tuple(
            sum(
                (factor.centre[i][m].conjugate() * factor.centre[i][col]
                 for i in range(d)),
                Cx(zero, zero),
            )
            - (Cx(rho, zero) if m == col else Cx(zero, zero))
            for col in range(k)
        )
        for m in range(k)
    )
    return is_positive_definite(gram)


# ---------------------------------------------------------------------------
#  def:exact-reference: enclosures, blocks, references
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Enclosure:
    """An entrywise enclosure ``(X_c, r)`` of one block of one element.

    ``foundations/def:exact-reference``: a Hermitian centre with entries in
    ``Q(i)`` and symmetric non-negative rational radii with
    ``|X_il - (X_c)_il| <= r_il``. The radius zero means known exactly. That
    the centre is Hermitian and the radii symmetric and non-negative is
    DECIDED by :meth:`failures` before a snap uses the enclosure
    (``foundations/req:snap-reference`` (i)); that the enclosure encloses the
    model is a claim of the module that constructs it, never decided here.

    An entry is **structurally zero** (``foundations/def:snap``) exactly when
    its centre and its radius are both zero; an entry with centre zero and a
    radius that is not is not structurally zero.

    ``factor`` is the factor enclosure the reference carries on this element's
    block besides its entrywise enclosure (``foundations/def:factor-enclosure``,
    last paragraph), or ``None``: an addition to the enclosure, never a
    replacement of it, of the block's dimension.
    """

    centre: Matrix
    radii: Radii
    factor: FactorEnclosure | None = None

    def __post_init__(self) -> None:
        """Refuse a ragged or non-exact presentation; the rest is :meth:`failures`."""
        dimension = _square_dimension(self.centre, "the centre of an enclosure")
        if len(self.radii) != dimension or any(
            len(row) != dimension for row in self.radii
        ):
            raise MalformedInputError(
                "the radii of an enclosure have the centre's shape"
            )
        if not all(isinstance(r, Fraction) for row in self.radii for r in row):
            raise MalformedInputError(
                "every radius of an enclosure is an exact rational (Fraction); "
                "use Enclosure.of to convert ints"
            )
        if self.factor is not None and self.factor.dimension != dimension:
            raise MalformedInputError(
                "a factor enclosure carried on a block has the block's dimension"
            )

    @classmethod
    def of(
        cls, centre: Sequence[Sequence[object]], radii: Sequence[Sequence[object]]
    ) -> Enclosure:
        """Build an enclosure from presentable entries (int, Fraction, Cx)."""
        return cls(
            tuple(tuple(as_scalar(entry) for entry in row) for row in centre),
            tuple(tuple(as_rational(r) for r in row) for row in radii),
        )

    @classmethod
    def exact(cls, centre: Matrix) -> Enclosure:
        """Return the enclosure of a block known exactly: every radius zero."""
        dimension = _square_dimension(centre, "the centre of an enclosure")
        zero = tuple(
            tuple(Fraction(0) for _ in range(dimension)) for _ in range(dimension)
        )
        return cls(centre, zero)

    @property
    def dimension(self) -> int:
        """The block dimension ``d_s``."""
        return len(self.centre)

    @property
    def is_exact(self) -> bool:
        """Whether every radius is zero."""
        return all(r == 0 for row in self.radii for r in row)

    @property
    def rho(self) -> Fraction:
        """``rho = max_i sum_l r_il``, the radius of every decision on this element."""
        return _row_sum_radius(self.radii)

    @property
    def largest_radius(self) -> Fraction:
        """The largest single radius."""
        return max((r for row in self.radii for r in row), default=Fraction(0))

    def is_structurally_zero_at(self, i: int, j: int) -> bool:
        """Whether entry ``(i, j)`` has centre and radius both zero (def:snap)."""
        return self.centre[i][j].is_zero and self.radii[i][j] == 0

    @property
    def structural_support(self) -> frozenset[int]:
        """The indices whose row or column holds an entry not structurally zero."""
        n = self.dimension
        return frozenset(
            i
            for i in range(n)
            if any(
                not self.is_structurally_zero_at(i, j)
                or not self.is_structurally_zero_at(j, i)
                for j in range(n)
            )
        )

    @property
    def is_structurally_zero(self) -> bool:
        """Whether every entry is structurally zero."""
        return not self.structural_support

    def failures(self) -> tuple[str, ...]:
        """Return the decisions of ``req:snap-reference`` (i) that fail here."""
        out: list[str] = []
        if not is_hermitian(self.centre):
            out.append("centre_not_hermitian")
        if any(r < 0 for row in self.radii for r in row):
            out.append("radius_negative")
        n = self.dimension
        if any(
            self.radii[i][j] != self.radii[j][i] for i in range(n) for j in range(n)
        ):
            out.append("radii_not_symmetric")
        return tuple(out)

    def as_record(self) -> dict[str, object]:
        """JSON-ready: exact rationals as strings, never floats; any factor carried."""
        record: dict[str, object] = {
            "centre": [[str(entry) for entry in row] for row in self.centre],
            "radii": [[str(r) for r in row] for row in self.radii],
        }
        if self.factor is not None:
            record["factor"] = self.factor.as_record()
        return record


def inverse_sqrt_enclosure(n: object, bits: int) -> tuple[Fraction, Fraction]:
    """Return rationals ``(a, e)`` with ``|a - n^(-1/2)| <= e``, ``0 <= e <= a``.

    The rational bound of ``foundations/lem:enclosure-psd`` (ii),
    Eq. ``eq:sqrt-enclosure``: ``(a-e)^2 n <= 1 <= (a+e)^2 n``, which this
    function DECIDES before returning, so that the enclosure is established by
    the lemma and not by this computation. Where ``n`` is the square of a
    rational, ``e = 0`` and ``a`` is exact.

    Args:
        n: a positive rational.
        bits: ``e <= 2^-(bits+1)`` where ``n^(-1/2)`` is irrational.
    """
    value = as_rational(n)
    if value <= 0:
        raise MalformedInputError(f"n = {value} is not a positive rational")
    if bits < 1:
        raise MalformedInputError(f"bits = {bits} is not a positive precision")
    p, q = value.numerator, value.denominator
    root_p, root_q = math.isqrt(p), math.isqrt(q)
    if root_p * root_p == p and root_q * root_q == q:
        return Fraction(root_q, root_p), Fraction(0)
    # n^(-1/2) = sqrt(q / p); 2^bits n^(-1/2) = sqrt(q 4^bits / p) =: sqrt(y).
    # floor(sqrt(y)) = isqrt(floor(y)), so L <= sqrt(y) < L + 1.
    lower = math.isqrt((q << (2 * bits)) // p)
    a = Fraction(2 * lower + 1, 1 << (bits + 1))
    e = Fraction(1, 1 << (bits + 1))
    if not ((a - e) ** 2 * value <= 1 <= (a + e) ** 2 * value and 0 <= e <= a):
        raise HypothesisError(  # pragma: no cover - the floor identity above
            "the rational bound of n^(-1/2) fails eq:sqrt-enclosure"
        )
    return a, e


def scaled_enclosure(s: Matrix, n: Sequence[object], *, bits: int) -> Enclosure:
    """Return the enclosure of ``D^-1 S D^-1``, ``D = diag(sqrt n_i)``.

    ``foundations/lem:enclosure-psd`` (ii): with ``|a_i - n_i^(-1/2)| <= e_i``
    from :func:`inverse_sqrt_enclosure`, the centre is ``A S A`` and the
    radii are ``sigma_il (a_i e_l + e_i a_l + e_i e_l)``,
    ``sigma_il = |Re S_il| + |Im S_il|`` (Eq. ``eq:scaled-radii``). An entry
    ``S_il = 0`` gives centre and radius zero, so a structural zero of ``S``
    stays structurally zero. Where every ``n_i`` is a rational square the
    enclosure is exact.

    Raises:
        MalformedInputError: on a ragged ``S`` or a wrong number of ``n_i``.
        HypothesisError: if ``S`` is not Hermitian.
    """
    dimension = _square_dimension(s, "S")
    if not is_hermitian(s):
        raise HypothesisError("S of lem:enclosure-psd (ii) is Hermitian")
    if len(n) != dimension:
        raise MalformedInputError(
            f"{len(n)} values n_i for a block of dimension {dimension}"
        )
    bounds = [inverse_sqrt_enclosure(value, bits) for value in n]
    centre = tuple(
        tuple(
            Cx(
                s[i][j].re * bounds[i][0] * bounds[j][0],
                s[i][j].im * bounds[i][0] * bounds[j][0],
            )
            for j in range(dimension)
        )
        for i in range(dimension)
    )
    radii = tuple(
        tuple(
            (abs(s[i][j].re) + abs(s[i][j].im))
            * (
                bounds[i][0] * bounds[j][1]
                + bounds[i][1] * bounds[j][0]
                + bounds[i][1] * bounds[j][1]
            )
            for j in range(dimension)
        )
        for i in range(dimension)
    )
    return Enclosure(centre, radii)


@dataclass(frozen=True)
class ReferenceIdentity:
    """What a snap record names as the reference (``foundations/req:who-snaps``).

    The model, the exact parameters from which it is formed, and -- where any
    radius is not zero -- the claims of the constructing module that establish
    that the enclosures enclose it and that it is positive semidefinite and
    complete (``foundations/req:snap-reference`` (i)). An enclosed reference
    whose identity names no establishing claim is neither used nor handed
    (cause ``reference_failed``).
    """

    model: str
    parameters: Mapping[str, str] = field(default_factory=dict)
    establishing_claims: tuple[str, ...] = ()

    def as_record(self) -> dict[str, object]:
        """JSON-ready."""
        return {
            "model": self.model,
            "parameters": dict(self.parameters),
            "establishing_claims": list(self.establishing_claims),
        }


@dataclass(frozen=True)
class ReferenceBlock:
    """One block ``s`` of a reference: an enclosure per outcome, in declared order.

    ``input_radius`` is the largest radius of the enclosures of the irrational
    inputs (square roots, trigonometric values) from which the constructing
    module computed the centres exactly, as its claims state it -- the
    "largest primitive radius" ``foundations/req:who-snaps`` records beside
    ``rho``. ``None`` where the constructing module states none (an exact
    block has none).
    """

    label: str
    elements: tuple[Enclosure, ...]
    input_radius: Fraction | None = None

    def __post_init__(self) -> None:
        """Refuse an empty block, mixed dimensions or a negative input radius."""
        if not self.elements:
            raise MalformedInputError(f"reference block {self.label!r} has no element")
        dimensions = {element.dimension for element in self.elements}
        if len(dimensions) != 1:
            raise MalformedInputError(
                f"reference block {self.label!r} mixes dimensions {sorted(dimensions)}"
            )
        radius: object = self.input_radius
        if radius is not None and (not isinstance(radius, Fraction) or radius < 0):
            raise MalformedInputError("an input radius is a non-negative Fraction")

    @property
    def dimension(self) -> int:
        """The block dimension ``d_s``."""
        return self.elements[0].dimension

    @property
    def kind(self) -> ReferenceKind:
        """``exact`` when every radius of the block is zero, else ``enclosed``."""
        if all(element.is_exact for element in self.elements):
            return ReferenceKind.EXACT
        return ReferenceKind.ENCLOSED

    @property
    def rhos(self) -> tuple[Fraction, ...]:
        """The radius ``rho_j`` of each outcome's decisions."""
        return tuple(element.rho for element in self.elements)

    @property
    def rho(self) -> Fraction:
        """The largest ``rho_j`` on the block."""
        return max(self.rhos)

    @property
    def centres(self) -> tuple[Matrix, ...]:
        """The centres ``C_j``, in declared order."""
        return tuple(element.centre for element in self.elements)


@dataclass(frozen=True)
class ReferenceVerdict:
    """The Reference row's decisions (``req:snap-reference`` (i)) on one reference."""

    usable: bool
    failures: tuple[str, ...] = ()


@dataclass(frozen=True)
class Reference:
    """A reference of a measurement family (``foundations/def:exact-reference``).

    Implements ``foundations/def:exact-reference``: a family over an alphabet
    with a declared order, against the blocks of a sector map (named by their
    labels, in the map's order), complete at the constant ``c``, read through
    an entrywise enclosure of every block of every element. It is an **exact
    reference** when every radius is zero (:attr:`kind` ``exact``), and
    ``enclosed`` otherwise; :attr:`block_kinds` gives the kind per block,
    which is what a snap record names (``foundations/req:who-snaps``).

    A reference is an object of its own beside the family declared from it,
    and it is never a binary64 evaluation: centres and radii are exact
    rationals, computed on the exact island by the module that constructs it.
    """

    alphabet: tuple[str, ...]
    blocks: tuple[ReferenceBlock, ...]
    constant: Fraction
    identity: ReferenceIdentity

    def __post_init__(self) -> None:
        """Refuse a malformed shape; the mathematical decisions are :meth:`decide`."""
        if not self.alphabet or len(set(self.alphabet)) != len(self.alphabet):
            raise MalformedInputError(
                "a reference's alphabet is non-empty and repeats no letter"
            )
        if not self.blocks:
            raise MalformedInputError("a reference has at least one block")
        labels = [block.label for block in self.blocks]
        if len(set(labels)) != len(labels):
            raise MalformedInputError(f"reference block labels repeat: {labels}")
        for block in self.blocks:
            if len(block.elements) != len(self.alphabet):
                raise MalformedInputError(
                    f"reference block {block.label!r} has {len(block.elements)} "
                    f"elements for an alphabet of {len(self.alphabet)}"
                )
        constant: object = self.constant
        if not isinstance(constant, Fraction) or constant <= 0:
            raise MalformedInputError(
                "the constant c of a reference is a positive Fraction"
            )

    @property
    def labels(self) -> tuple[str, ...]:
        """The block labels, in the sector map's order."""
        return tuple(block.label for block in self.blocks)

    def block(self, label: str) -> ReferenceBlock:
        """Return the block named ``label``."""
        for block in self.blocks:
            if block.label == label:
                return block
        raise KeyError(label)

    @property
    def kind(self) -> ReferenceKind:
        """``exact`` when every radius of every block is zero, else ``enclosed``."""
        if all(block.kind is ReferenceKind.EXACT for block in self.blocks):
            return ReferenceKind.EXACT
        return ReferenceKind.ENCLOSED

    @property
    def block_kinds(self) -> dict[str, ReferenceKind]:
        """The kind of every block."""
        return {block.label: block.kind for block in self.blocks}

    def decide(self) -> ReferenceVerdict:
        """Take the decisions ``req:snap-reference`` (i) asks of the declarer.

        Exactly: every centre Hermitian (its entries are Gaussian rationals by
        type), every radius a non-negative rational with ``r_il = r_li``; on a
        block known exactly, every element positive semidefinite and the
        elements summing to ``c 1``. Where a radius is not zero, enclosure,
        positivity and completeness are the constructing module's claims, and
        the reference is usable only if its identity names them.
        """
        failures: list[str] = []
        for block in self.blocks:
            for letter, element in zip(self.alphabet, block.elements, strict=True):
                failures.extend(
                    f"{block.label}/{letter}: {failure}"
                    for failure in element.failures()
                )
        if failures:
            return ReferenceVerdict(False, tuple(failures))
        for block in self.blocks:
            if block.kind is not ReferenceKind.EXACT:
                continue
            for letter, centre in zip(self.alphabet, block.centres, strict=True):
                if not is_positive_semidefinite(centre):
                    failures.append(
                        f"{block.label}/{letter}: not_positive_semidefinite"
                    )
            if not is_complete_at(block.centres, self.constant):
                failures.append(f"{block.label}: not_complete")
        if (
            self.kind is ReferenceKind.ENCLOSED
            and not self.identity.establishing_claims
        ):
            failures.append(
                "enclosed reference: no claim of its constructing module named as "
                "establishing its enclosures, positivity and completeness"
            )
        return ReferenceVerdict(not failures, tuple(failures))

    def as_record(self) -> dict[str, object]:
        """Return the reference's identity for a snap record (``req:who-snaps``).

        The enclosures are carried where any radius is not zero; an exact
        reference is identified by its model and parameters.
        """
        record: dict[str, object] = {
            **self.identity.as_record(),
            "kind": str(self.kind),
            "constant": str(self.constant),
            "alphabet": list(self.alphabet),
            "block_kinds": {
                label: str(kind) for label, kind in self.block_kinds.items()
            },
        }
        if self.kind is ReferenceKind.ENCLOSED:
            record["enclosures"] = {
                block.label: {
                    letter: element.as_record()
                    for letter, element in zip(
                        self.alphabet, block.elements, strict=True
                    )
                }
                for block in self.blocks
                if block.kind is ReferenceKind.ENCLOSED
            }
        return record
