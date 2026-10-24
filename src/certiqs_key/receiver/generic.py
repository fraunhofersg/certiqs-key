"""The receiver construction, generic over the number type.

ONE PIPELINE, THREE ARITHMETICS
===============================
The receiver construction is generic over the number type -- binary64 for evaluation,
enclosures for the reference. Every function here takes a :class:`Field` and computes
with its elements through ``+``, ``-``, ``*``, unary ``-`` and ``conjugate()`` alone,
plus the field's own leaves (square roots, cosines and sines, reciprocals):

* :class:`FloatField` -- ``complex``, the binary64 evaluation of
  Definition ``def:evaluation-model``;
* :class:`BallField` -- :class:`~certiqs_key.receiver.enclosure.Ball`, the
  complex enclosures of Definition ``def:complex-enclosure`` carried by the
  rules of Lemma ``lem:enclosure-arithmetic``, which is what makes the result
  an enclosure (Theorem ``thm:enclosed-blocks``);
* :class:`~certiqs_key.receiver.radicals.RadicalField` -- exact arithmetic in
  ``Q(i)`` adjoined square roots, in which Requirement
  ``req:exact-route-decision`` (ii) compiles the instrument matrix and the
  port Grams exactly.

The steps are the claims' own: the catalogue entries
(``component-catalogue/def:catalogue-entries``) and their compilation
(``def:compile``), the port Grams (Eq. ``eq:gramdef``), the lifted no-click
operators read in the occupation basis through permanents
(``lem:fock-permanent``), inclusion and exclusion (Eq. ``eq:blockMS``) over
the no-click pairs of a setting family (Definition ``def:setting-family``),
and the dark-composed family (``detector-imperfections/def:dark-composed``).
The pairs of the probe-free receiver are :func:`unconditioned_pairs`; those of
a setting family a submodule constructs are that submodule's, reached through
:func:`certiqs_key.receiver.settings.setting_construction`, and the
helpers below are the arithmetic it is written in.

WHY THE EMITTED BINARY64 BLOCKS DO NOT GO THROUGH THIS FILE
===========================================================
The artifact's binary64 blocks keep their NumPy evaluation
(:mod:`certiqs_key.receiver.povm`, :mod:`certiqs_key.receiver.fock`): the
formulas here are equal to those as exact expressions but not as sequences of
roundings -- the catalogue entries are written with double angles, the lifted
blocks through permanents rather than a symmetrizer -- so routing the emitted
numbers through them would move every key rate at the last binary place,
and the binary64 evaluation keeps its numbers unchanged. The :class:`FloatField`
instance of this pipeline is what the tests compare the NumPy evaluation against, so the
two cannot drift apart unseen.

WRITTEN WITH DOUBLE ANGLES
==========================
The catalogue writes the retarder and the polarizer with ``cos^2 theta``,
``sin^2 theta`` and ``sin theta cos theta``. Here they are written with
``(1 + cos 2 theta)/2``, ``(1 - cos 2 theta)/2`` and ``(sin 2 theta)/2``, an
exact identity, because the exact route represents ``cos`` and ``sin`` of a
multiple of ``pi/4`` and an axis angle of ``pi/8`` then stays on it
(Requirement ``req:exact-route-decision`` (ii) lists axis angles that are
multiples of ``pi/8``; its lead-in names the ``cos`` and ``sin`` of multiples
of ``pi/4`` the entries involve). The phase ``exp(-i delta / 2)`` of a
retarder is read at the angle ``delta / 2``, "again a rational or a rational
multiple of pi" (the same requirement, item (iii)).
"""

from __future__ import annotations

import math
from collections.abc import Callable, Iterator, Mapping, Sequence
from fractions import Fraction
from itertools import combinations
from typing import Final, Protocol, Self

import numpy as np

from certiqs_key.receiver.catalogue import (
    Beamsplitter,
    Component,
    GenericBlock,
    Loss,
    Mirror,
    ModeRouting,
    PhaseShifter,
    Polarizer,
    PolarizingBeamsplitter,
    Retarder,
    Rotator,
)
from certiqs_key.receiver.enclosure import (
    DEFAULT_BITS,
    Ball,
    angle_enclosure,
    exact_angle,
)
from certiqs_key.receiver.enclosure import sqrt_enclosure as _sqrt_enclosure
from certiqs_key.receiver.errors import HypothesisError
from certiqs_key.receiver.fock import occupation_vectors
from certiqs_key.receiver.graph import ElementGraph
from certiqs_key.receiver.numerics import Angle, Matrix, PiMultiple, Scalar

__all__ = [
    "Arithmetic",
    "BallField",
    "Field",
    "FloatField",
    "GenericMatrix",
    "NoClickPairs",
    "NoEnclosure",
    "RecordingField",
    "compile_instrument",
    "dark_composed_blocks",
    "element_blocks",
    "element_matrix",
    "fock_block",
    "port_grams_of",
    "unconditioned_pairs",
]

_ZERO: Final[Fraction] = Fraction(0)
_HALF: Final[Fraction] = Fraction(1, 2)


class Arithmetic(Protocol):
    """What a number type offers the pipeline: ring operations and conjugation."""

    def __add__(self, other: Self, /) -> Self:
        """Return the sum."""
        ...

    def __sub__(self, other: Self, /) -> Self:
        """Return the difference."""
        ...

    def __mul__(self, other: Self, /) -> Self:
        """Return the product."""
        ...

    def __neg__(self) -> Self:
        """Return the additive inverse."""
        ...

    def conjugate(self) -> Self:
        """Return the complex conjugate."""
        ...


#: A matrix over a field, row-major.
type GenericMatrix[N] = list[list[N]]


class NoEnclosure(Exception):
    """A reciprocal that receives no enclosure (Lem. lem:enclosure-arithmetic (iii))."""


class Field[N: Arithmetic](Protocol):
    """The leaves and constants of one arithmetic."""

    def zero(self) -> N:
        """Return ``0``."""
        ...

    def one(self) -> N:
        """Return ``1``."""
        ...

    def gaussian(self, re: Fraction, im: Fraction = ...) -> N:
        """Return the Gaussian rational ``re + i im``."""
        ...

    def rational(self, value: Fraction) -> N:
        """Return a rational."""
        ...

    def sqrt(self, value: Fraction) -> N:
        """Return the square root of a non-negative rational (a leaf)."""
        ...

    def cos_sin(self, angle: Angle) -> tuple[N, N]:
        """Return ``cos`` and ``sin`` of a declared angle (a leaf)."""
        ...

    def reciprocal(self, value: N) -> N:
        """Return ``1 / value``, or raise :class:`NoEnclosure`."""
        ...

    def is_zero(self, value: N) -> bool:
        """Return whether ``value`` is EXACTLY zero (for an enclosure: radius 0 too)."""
        ...


class FloatField:
    """Binary64 complex arithmetic: the evaluation of Def. ``def:evaluation-model``."""

    def zero(self) -> complex:
        """Return ``0``."""
        return 0j

    def one(self) -> complex:
        """Return ``1``."""
        return 1 + 0j

    def gaussian(self, re: Fraction, im: Fraction = _ZERO) -> complex:
        """Return ``re + i im`` rounded to binary64."""
        return complex(float(re), float(im))

    def rational(self, value: Fraction) -> complex:
        """Return a rational rounded to binary64."""
        return complex(float(value))

    def sqrt(self, value: Fraction) -> complex:
        """Return ``sqrt value`` in binary64."""
        return complex(math.sqrt(float(value)))

    def cos_sin(self, angle: Angle) -> tuple[complex, complex]:
        """Return ``cos`` and ``sin`` of the angle's binary64 evaluation."""
        value = exact_angle(angle)
        number = (
            float(value.coefficient) * math.pi
            if isinstance(value, PiMultiple)
            else float(value)
        )
        return complex(math.cos(number)), complex(math.sin(number))

    def reciprocal(self, value: complex) -> complex:
        """Return ``1 / value``."""
        return 1 / value

    def is_zero(self, value: complex) -> bool:
        """Return whether ``value`` is the floating-point zero."""
        return value == 0


class RecordingField(FloatField):
    """A binary64 field that records every rational whose square root is taken.

    Used once, before the exact computation, to build the
    :class:`~certiqs_key.receiver.radicals.RadicalField` with every radicand
    the element formulas need (that module's docstring, "THE BASE IS FIXED
    BEFORE ANY NUMBER IS FORMED").
    """

    def __init__(self) -> None:
        """Start with no radicand recorded."""
        self.radicands: set[Fraction] = set()

    def sqrt(self, value: Fraction) -> complex:
        """Record ``value`` and return its binary64 square root."""
        self.radicands.add(value)
        return super().sqrt(max(value, _ZERO))


class BallField:
    """Complex enclosures (Def. def:complex-enclosure, Lem. lem:enclosure-arithmetic).

    Every leaf is a square-root or angle enclosure at ``bits``; the largest
    radius of every leaf formed is kept in :attr:`largest_leaf`, the "largest
    radius of the enclosures of irrational inputs" a reference records
    (Requirement ``req:dark-composed-reference`` (iii)).
    """

    def __init__(self, bits: int = DEFAULT_BITS) -> None:
        """Start a field at a leaf precision of ``bits``."""
        self.bits = bits
        self.largest_leaf: Fraction = _ZERO

    def _leaf(self, ball: Ball) -> Ball:
        if ball.radius > self.largest_leaf:
            self.largest_leaf = ball.radius
        return ball

    def zero(self) -> Ball:
        """Return the exact ``0``."""
        return Ball(_ZERO)

    def one(self) -> Ball:
        """Return the exact ``1``."""
        return Ball(Fraction(1))

    def gaussian(self, re: Fraction, im: Fraction = _ZERO) -> Ball:
        """Return the exact enclosure of a Gaussian rational."""
        return Ball(re, im)

    def rational(self, value: Fraction) -> Ball:
        """Return the exact enclosure of a rational."""
        return Ball(value)

    def sqrt(self, value: Fraction) -> Ball:
        """Return a square-root enclosure (Def. ``def:complex-enclosure``)."""
        return self._leaf(_sqrt_enclosure(value, self.bits))

    def cos_sin(self, angle: Angle) -> tuple[Ball, Ball]:
        """Return an angle enclosure (Def. ``def:complex-enclosure``)."""
        cos, sin = angle_enclosure(angle, self.bits)
        return self._leaf(cos), self._leaf(sin)

    def reciprocal(self, value: Ball) -> Ball:
        """Return the enclosure of rule (iii), or raise :class:`NoEnclosure`."""
        result = value.reciprocal(self.bits)
        if result is None:
            raise NoEnclosure(
                "a reciprocal receives no enclosure: no rational l with "
                "l^2 <= |x_c|^2 exceeds the radius (lem:enclosure-arithmetic (iii))"
            )
        return result

    def is_zero(self, value: Ball) -> bool:
        """Return whether the enclosure is the exact zero."""
        return value.is_zero


# ---------------------------------------------------------------------------
#  Matrix helpers
# ---------------------------------------------------------------------------


def _identity[N: Arithmetic](field: Field[N], size: int) -> GenericMatrix[N]:
    return [
        [field.one() if row == column else field.zero() for column in range(size)]
        for row in range(size)
    ]


def _zeros[N: Arithmetic](field: Field[N], rows: int, columns: int) -> GenericMatrix[N]:
    return [[field.zero() for _ in range(columns)] for _ in range(rows)]


def _matmul[N: Arithmetic](
    field: Field[N], left: GenericMatrix[N], right: GenericMatrix[N]
) -> GenericMatrix[N]:
    """Return ``left @ right``, the terms with an exactly zero factor omitted.

    Omitting them changes nothing: an exact zero times anything is the exact
    zero under every arithmetic here (Lemma ``lem:enclosure-arithmetic`` (ii)
    gives centre ``0`` and radius ``0``), and adding the exact zero leaves a
    number as it was (item (i)).
    """
    inner = len(right)
    columns = len(right[0]) if right else 0
    out: GenericMatrix[N] = []
    for row in left:
        used = [k for k in range(inner) if not field.is_zero(row[k])]
        out_row: list[N] = []
        for column in range(columns):
            total: N | None = None
            for k in used:
                factor = right[k][column]
                if field.is_zero(factor):
                    continue
                term = row[k] * factor
                total = term if total is None else total + term
            out_row.append(field.zero() if total is None else total)
        out.append(out_row)
    return out


def _add[N: Arithmetic](
    left: GenericMatrix[N], right: GenericMatrix[N]
) -> GenericMatrix[N]:
    return [
        [a + b for a, b in zip(ra, rb, strict=True)]
        for ra, rb in zip(left, right, strict=True)
    ]


def _sub[N: Arithmetic](
    left: GenericMatrix[N], right: GenericMatrix[N]
) -> GenericMatrix[N]:
    return [
        [a - b for a, b in zip(ra, rb, strict=True)]
        for ra, rb in zip(left, right, strict=True)
    ]


def _scale[N: Arithmetic](factor: N, matrix: GenericMatrix[N]) -> GenericMatrix[N]:
    return [[factor * entry for entry in row] for row in matrix]


def _diag[N: Arithmetic](field: Field[N], values: Sequence[N]) -> GenericMatrix[N]:
    size = len(values)
    return [
        [values[row] if row == column else field.zero() for column in range(size)]
        for row in range(size)
    ]


def _exp_i[N: Arithmetic](field: Field[N], angle: Fraction | PiMultiple) -> N:
    cos, sin = field.cos_sin(angle)
    return cos + field.gaussian(_ZERO, Fraction(1)) * sin


def _times(angle: Angle, factor: Fraction) -> Fraction | PiMultiple:
    value = exact_angle(angle)
    if isinstance(value, PiMultiple):
        return PiMultiple(value.coefficient * factor)
    return value * factor


def _declared(value: Scalar) -> Fraction:
    """Return a declared value as the rational it denotes (``def:binary64`` (iii))."""
    if isinstance(value, bool):
        raise HypothesisError("a boolean is not a declared numerical parameter")
    if isinstance(value, float) and not math.isfinite(value):
        raise HypothesisError(f"a declared value is finite, got {value}")
    return Fraction(value)


def _complex_entry[N: Arithmetic](field: Field[N], entry: complex) -> N:
    """Return a declared binary64 complex entry as the Gaussian rational it is."""
    return field.gaussian(Fraction(float(entry.real)), Fraction(float(entry.imag)))


# ---------------------------------------------------------------------------
#  The catalogue entries, generic
# ---------------------------------------------------------------------------


def _beamsplitter_core[N: Arithmetic](
    field: Field[N], transmittance: Fraction, phase: Angle
) -> GenericMatrix[N]:
    root_t = field.sqrt(transmittance)
    root_r = field.sqrt(1 - transmittance)
    phase_value = exact_angle(phase)
    forward = _exp_i(field, phase_value)
    return [
        [root_t, root_r * forward],
        [root_r * forward.conjugate(), -root_t],
    ]


def _half_angle_terms[N: Arithmetic](field: Field[N], angle: Angle) -> tuple[N, N, N]:
    """Return ``(cos^2 theta, sin^2 theta, sin theta cos theta)`` via ``2 theta``."""
    cos2, sin2 = field.cos_sin(_times(angle, Fraction(2)))
    half = field.rational(_HALF)
    one = field.one()
    return half * (one + cos2), half * (one - cos2), half * sin2


def element_matrix[N: Arithmetic](
    field: Field[N], component: Component
) -> GenericMatrix[N]:
    """Return the local element of a catalogue entry over ``field``.

    Implements ``receiver/component-catalogue/def:catalogue-entries`` (C1-C10)
    generically: in :class:`BallField` the result is an enclosure of the
    element obtained by the rules of ``receiver/lem:enclosure-arithmetic``
    from square-root and angle enclosures of its parameters (Requirement
    ``receiver/req:exact-route-decision`` (iii)); in a
    :class:`~certiqs_key.receiver.radicals.RadicalField` it is the element
    exactly. Rows are outputs, as in the catalogue.
    """
    if isinstance(component, Beamsplitter):
        core = _beamsplitter_core(
            field, _declared(component.transmittance), component.phase
        )
        attenuation = _diag(
            field,
            [
                field.sqrt(1 - _declared(component.loss_1)),
                field.sqrt(1 - _declared(component.loss_2)),
            ],
        )
        scaled = _matmul(field, attenuation, core)
        # core (x) id_2 on (p1H, p1V, p2H, p2V).
        out = _zeros(field, 4, 4)
        for row in range(2):
            for column in range(2):
                out[2 * row][2 * column] = scaled[row][column]
                out[2 * row + 1][2 * column + 1] = scaled[row][column]
        return out
    if isinstance(component, PolarizingBeamsplitter):
        core_h = _beamsplitter_core(
            field, _declared(component.transmittance_h), component.phase_h
        )
        core_v = _beamsplitter_core(
            field, _declared(component.transmittance_v), component.phase_v
        )
        block = _zeros(field, 4, 4)
        for row in range(2):
            for column in range(2):
                block[2 * row][2 * column] = core_h[row][column]
                block[2 * row + 1][2 * column + 1] = core_v[row][column]
        a1 = field.sqrt(1 - _declared(component.loss_1))
        a2 = field.sqrt(1 - _declared(component.loss_2))
        return _matmul(field, _diag(field, [a1, a1, a2, a2]), block)
    if isinstance(component, Retarder):
        cos_sq, sin_sq, cross = _half_angle_terms(field, component.angle)
        e = _exp_i(field, exact_angle(component.retardance))
        global_phase = _exp_i(field, _times(component.retardance, -_HALF))
        one = field.one()
        off = cross * (one - e)
        plate = [
            [cos_sq + e * sin_sq, off],
            [off, sin_sq + e * cos_sq],
        ]
        factor = field.sqrt(1 - _declared(component.loss)) * global_phase
        return _scale(factor, plate)
    if isinstance(component, Rotator):
        cos, sin = field.cos_sin(component.rotation_angle)
        return [[cos, -sin], [sin, cos]]
    if isinstance(component, Mirror):
        sign = -field.one() if component.handedness_flip else field.one()
        return _diag(
            field,
            [
                field.sqrt(_declared(component.reflectivity_h))
                * _exp_i(field, exact_angle(component.phase_h)),
                field.sqrt(_declared(component.reflectivity_v))
                * _exp_i(field, exact_angle(component.phase_v))
                * sign,
            ],
        )
    if isinstance(component, PhaseShifter):
        return _diag(
            field, [_exp_i(field, exact_angle(phase)) for phase in component.phases]
        )
    if isinstance(component, Loss):
        return _diag(
            field, [field.sqrt(_declared(value)) for value in component.efficiencies]
        )
    if isinstance(component, Polarizer):
        cos_sq, sin_sq, cross = _half_angle_terms(field, component.angle)
        root_t = field.sqrt(_declared(component.pass_transmittance))
        root_perp = field.sqrt(_declared(component.leak_transmittance))
        off = cross * (root_t - root_perp)
        return [
            [root_t * cos_sq + root_perp * sin_sq, off],
            [off, root_t * sin_sq + root_perp * cos_sq],
        ]
    if isinstance(component, ModeRouting):
        size = len(component.permutation)
        out = _zeros(field, size, size)
        for column, row in enumerate(component.permutation):
            out[row][column] = field.one()
        return out
    if isinstance(component, GenericBlock):
        return [
            [_complex_entry(field, entry) for entry in row] for row in component.block
        ]
    raise HypothesisError(  # pragma: no cover - the catalogue is closed
        f"no generic formula for catalogue entry {type(component).__name__}"
    )


def compile_instrument[N: Arithmetic](
    field: Field[N],
    graph: ElementGraph,
    mode_count: int,
    order: Sequence[str],
    port_rows: Sequence[Sequence[int]],
    efficiencies: Sequence[Scalar],
) -> GenericMatrix[N]:
    """Return ``D_eta Gamma^sigma_G`` of Def. ``def:compile`` over ``field``.

    Implements ``receiver/def:compile`` generically: the embedded elements
    multiplied in the order of the linear extension ``order``, later elements
    from the left (Eq. ``eq:compile``), then the terminal detector-efficiency
    layer ``D_eta`` with ``sqrt(eta_k)`` on the rows of port ``k`` and ``1``
    elsewhere. Theorem ``thm:enclosed-blocks`` (i) in :class:`BallField`.
    """
    matrix = _identity(field, mode_count)
    for name in order:
        element = graph.element(name)
        local = element_matrix(field, element.component)
        # The embedding Gamma_Sigma (+) id (Eq. eq:embed) times `matrix`: rows
        # outside the support are the identity's and are kept as they are;
        # each row inside it is the local row applied to the support's rows.
        # This is the full product with its exact-zero terms and its products
        # by an exact one omitted, neither of which changes a number or an
        # enclosure (see `_matmul`).
        support_rows = [matrix[mode] for mode in element.support]
        updated = _matmul(field, local, support_rows)
        matrix = list(matrix)
        for position, mode in enumerate(element.support):
            matrix[mode] = updated[position]
    layer = [field.one() for _ in range(mode_count)]
    for rows, efficiency in zip(port_rows, efficiencies, strict=True):
        root = field.sqrt(_declared(efficiency))
        for row in rows:
            layer[row] = root
    return [[layer[row] * entry for entry in matrix[row]] for row in range(mode_count)]


def port_grams_of[N: Arithmetic](
    field: Field[N],
    gamma: GenericMatrix[N],
    input_columns: Sequence[int],
    port_rows: Sequence[Sequence[int]],
) -> tuple[GenericMatrix[N], ...]:
    """Return ``A_k = Gamma_Inp^dagger E_k Gamma_Inp`` -- Eq. ``eq:gramdef``.

    Implements Eq. ``eq:gramdef`` of ``receiver/def:gram`` generically, the
    columns taken in the subsystem order of the declared inputs.
    """
    grams: list[GenericMatrix[N]] = []
    for rows in port_rows:
        gram: GenericMatrix[N] = []
        for a in input_columns:
            gram_row: list[N] = []
            for b in input_columns:
                total = field.zero()
                for row in rows:
                    total = total + gamma[row][a].conjugate() * gamma[row][b]
                gram_row.append(total)
            gram.append(gram_row)
        grams.append(gram)
    return tuple(grams)


# ---------------------------------------------------------------------------
#  Lifted operators: lem:fock-permanent
# ---------------------------------------------------------------------------


def _tables(
    rows: Sequence[int], columns: Sequence[int]
) -> Iterator[tuple[tuple[int, ...], ...]]:
    """Yield the non-negative integer matrices with the given row and column sums."""
    if not rows:
        if all(c == 0 for c in columns):
            yield ()
        return
    first, rest = rows[0], rows[1:]

    def split(total: int, capacities: Sequence[int]) -> Iterator[tuple[int, ...]]:
        if len(capacities) == 1:
            if total <= capacities[0]:
                yield (total,)
            return
        for take in range(min(total, capacities[0]) + 1):
            for tail in split(total - take, capacities[1:]):
                yield (take, *tail)

    for row in split(first, columns):
        remaining = tuple(c - r for c, r in zip(columns, row, strict=True))
        for tail_rows in _tables(rest, remaining):
            yield (row, *tail_rows)


def _permanent_by_tables[N: Arithmetic](
    field: Field[N],
    rows: Sequence[int],
    columns: Sequence[int],
    powers: Callable[[int, int, int], N],
) -> N:
    """Return ``per X[m | m']`` grouped by the matrices of repeated entries.

    The permanent of ``X[m|m']`` is the sum over the permutations of the
    products of its entries (Lemma ``lem:fock-permanent``). A permutation of
    the word of ``m`` onto the word of ``m'`` uses entry ``X_ij`` some number
    ``T_ij`` of times, with row sums ``m_i`` and column sums ``m'_j``, and
    exactly ``prod_i m_i! prod_j m'_j! / prod_ij T_ij!`` permutations give
    each such ``T``; so the permanent is the sum over ``T`` of that integer
    times ``prod X_ij^T_ij``. The same sum of products of entries, grouped:
    an exact identity, and a finite expression to which Lemma
    ``lem:enclosure-arithmetic`` (iv) applies as it does to the ungrouped sum.
    """
    numerator = math.prod(math.factorial(m) for m in rows) * math.prod(
        math.factorial(m) for m in columns
    )
    total = field.zero()
    for table in _tables(rows, columns):
        weight = numerator
        product: N | None = None
        for i, row in enumerate(table):
            for j, count in enumerate(row):
                if count == 0:
                    continue
                weight //= math.factorial(count)
                term = powers(i, j, count)
                product = term if product is None else product * term
        value = field.rational(Fraction(weight))
        total = total + (value if product is None else value * product)
    return total


def fock_block[N: Arithmetic](
    field: Field[N], operator: GenericMatrix[N], photons: int
) -> GenericMatrix[N]:
    """Return ``Fock(X)^{(n)}`` in the occupation basis, by Eq. ``eq:fock-permanent``.

    Implements ``receiver/lem:fock-permanent`` (i): the entry
    ``(m, m')`` is ``per X[m|m'] * sqrt(1 / (m! m'!))``, the square root a
    square-root enclosure in :class:`BallField` (exact where ``m! m'!`` is a
    square, item (ii)). The basis order is the ascending lexicographic order
    of :func:`~certiqs_key.receiver.fock.occupation_vectors`, the one the
    emitted blocks use.
    """
    dimension = len(operator)
    vectors = occupation_vectors(dimension, photons)
    cache: dict[tuple[int, int, int], N] = {}

    def powers(i: int, j: int, count: int) -> N:
        key = (i, j, count)
        value = cache.get(key)
        if value is None:
            value = (
                operator[i][j]
                if count == 1
                else powers(i, j, count - 1) * operator[i][j]
            )
            cache[key] = value
        return value

    factorials = {
        vector: math.prod(math.factorial(m) for m in vector) for vector in vectors
    }
    roots: dict[int, N] = {}
    block: GenericMatrix[N] = []
    for m in vectors:
        row: list[N] = []
        for mp in vectors:
            product = factorials[m] * factorials[mp]
            root = roots.get(product)
            if root is None:
                root = field.sqrt(Fraction(1, product))
                roots[product] = root
            permanent = _permanent_by_tables(field, m, mp, powers)
            row.append(permanent * root)
        block.append(row)
    return block


# ---------------------------------------------------------------------------
#  No-click data, element blocks, dark composition
# ---------------------------------------------------------------------------

#: The pairs ``{(c_J, B_J)}_{J subset of [K]}``: prefactor and effective Gram.
type NoClickPairs[N] = dict[frozenset[int], tuple[N, GenericMatrix[N]]]


def _subsets(port_count: int) -> Iterator[frozenset[int]]:
    ports = range(port_count)
    for size in range(port_count + 1):
        for chosen in combinations(ports, size):
            yield frozenset(chosen)


def unconditioned_pairs[N: Arithmetic](
    field: Field[N], grams: Sequence[GenericMatrix[N]]
) -> NoClickPairs[N]:
    """Return ``(1, A_J)`` for every ``J`` -- Thm. ``thm:click-povm`` (ii)."""
    dimension = len(grams[0])
    pairs: NoClickPairs[N] = {}
    for subset in _subsets(len(grams)):
        total = _zeros(field, dimension, dimension)
        for index in sorted(subset):
            total = _add(total, grams[index])
        pairs[subset] = (field.one(), total)
    return pairs


def element_blocks[N: Arithmetic](
    field: Field[N], pairs: NoClickPairs[N], port_count: int, photons: int
) -> dict[frozenset[int], GenericMatrix[N]]:
    r"""Return ``blk M_S^{(=n)}`` for every click pattern -- Eq. ``eq:blockMS``.

    ``M_S = sum_{T subset of S} (-1)^{|T|} Pvac(([K] \ S) union T)`` with
    ``Pvac(J)^{(n)} = c_J Fock(1 - B_J)^{(n)}`` (Theorem ``thm:click-povm``
    (ii) unconditioned; the prefactor form of Definition ``def:setting-family``
    (b) for a setting family a submodule constructs); the signs are exact.
    """
    every = frozenset(range(port_count))
    lifted: dict[frozenset[int], GenericMatrix[N]] = {}
    for subset, (prefactor, gram) in pairs.items():
        size = len(gram)
        lifted[subset] = _scale(
            prefactor, fock_block(field, _sub(_identity(field, size), gram), photons)
        )
    blocks: dict[frozenset[int], GenericMatrix[N]] = {}
    for pattern in _subsets(port_count):
        silent = every - pattern
        total: GenericMatrix[N] | None = None
        for size in range(len(pattern) + 1):
            for chosen in combinations(sorted(pattern), size):
                term = lifted[silent | frozenset(chosen)]
                if total is None:
                    total = [row[:] for row in term]
                elif size % 2:
                    total = _sub(total, term)
                else:
                    total = _add(total, term)
        assert total is not None
        blocks[pattern] = total
    return blocks


def dark_composed_blocks[N: Arithmetic](
    field: Field[N],
    blocks: Mapping[frozenset[int], GenericMatrix[N]],
    weights: Mapping[str, Mapping[frozenset[int], Fraction]],
    alphabet: Sequence[str],
) -> dict[str, GenericMatrix[N]]:
    """Return ``blk Ftilde_v^{(=n)} = sum_{S'} R_{cg^-1(v)|S'} blk M_{S'}^{(=n)}``.

    Implements Eq. ``eq:dark-composed`` of
    ``receiver/detector-imperfections/def:dark-composed`` generically;
    ``weights[v][S']`` is ``R_{cg^-1(v)|S'}``, a non-negative rational. In
    :class:`BallField` this is ``cor:exact-dark-composed`` (i): centre
    ``sum R C`` and radius ``sum R r``, exact where every term with a non-zero
    coefficient is.
    """
    any_block = next(iter(blocks.values()))
    size = len(any_block)
    composed: dict[str, GenericMatrix[N]] = {}
    for letter in alphabet:
        total = _zeros(field, size, size)
        for pattern, weight in weights[letter].items():
            if weight == 0:
                continue
            total = _add(total, _scale(field.rational(weight), blocks[pattern]))
        composed[letter] = total
    return composed


def as_complex_array(matrix: GenericMatrix[complex]) -> Matrix:
    """Return a :class:`FloatField` matrix as a ``complex128`` array (tests)."""
    return np.asarray(matrix, dtype=np.complex128)
