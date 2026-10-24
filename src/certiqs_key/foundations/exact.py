"""THE EXACT SUBSTRATE: Gaussian rationals, decided and never measured.

WHERE IT LIVES AND WHY. spec/architecture.md 2.9 puts ``foundations/exact.py``
at the floor every package may import: the exact island is one substrate, and
the protocol compiler, the transmitter, ``reductions`` and ``meat-core`` read
the same ``Cx`` and ``Matrix`` rather than declaring the pair once per package,
which would be needed only because no module could import a sibling.

FIVE EXTRAS LIVE HERE TOO -- ``lattice_step``, ``spectral_bounds``,
``linear_relations``, ``span_dimension`` and ``RoundsNowhere`` -- rather than
in a ``reductions/numbers.py``, because splitting them costs more than it buys:
``span_dimension`` and ``linear_relations`` share the private ``_row_reduce``
with nothing else, so a split would have to export a private helper;
``RoundsNowhere`` is the RETURN TYPE of ``sum_rounds_nowhere``, so a split
would put a function and its result in two packages; and ``lattice_step`` is
one of the four lattice primitives. None of the five says anything about
reductions: they are exact linear algebra over the rationals.
spec/architecture.md 2.9 decides nothing against it -- what it fixes is that
the decisions live here and take no tolerance.

WHICH CLAIMS THIS FILE MAY CITE
===============================
``foundations/`` is the floor: every package may import it and it imports none
(PRINCIPLES.md section 4, spec/architecture.md 2.9). SO IT NAMES NO CLAIM OF A
SUBMODULE THAT MAY BE DELETED -- in a literal or in prose, a docstring pointing
at a claim a deletion removes being a pointer to nothing. Where an example is
wanted, it is the core's generic claim that says the same thing:
``def:reduction-instance`` for the sector-block form,
``cor:register-instance`` for a register product, and the core interface's
``subsystem_order`` convention for the order of a tensor factor.

WHAT THE INTERFACE SAYS ABOUT THE SUBSTRATE
===========================================
The reductions interface records the numeric substrate as an open implementation choice
and declined to decide it: "THE CONTRACT FIXES NO NUMERIC TYPE, NO TOLERANCE
AND NO ROUNDING RULE for any emitted matrix ... The choice of substrate is
therefore code's." Deciding it in a YAML file would hide proof-relevant
behaviour outside the source, which is why it is decided here, in one module,
through which every matrix the reductions module accepts, compares or emits is
built. Nothing in that package performs arithmetic on any other
representation, and none of them imports ``numpy``.

THE DECISION: EXACT GAUSSIAN RATIONALS
======================================
A scalar is a :class:`Cx` -- an exact pair of :class:`fractions.Fraction`, real
and imaginary part. A matrix is a tuple of tuples of those. No ``float``, no
built-in ``complex``, no tolerance and no array library appears anywhere in
this module. Five reasons, in the order of their weight.

1. **The contract characterizes itself as exact, and says so about the very
   comparisons the reductions module makes.** It "states NO CLAIM WHOSE PROOF
   DEPENDS ON A FLOATING-POINT COMPUTATION: every statement is AN OPERATOR
   IDENTITY OR INEQUALITY BETWEEN EXACTLY DECLARED QUANTITIES, and the places a
   number is compared against a threshold -- the total weight ``p < 1``, the
   per-outcome weights ``p_v >= 0`` -- ARE REFUSAL TESTS, NOT BOUNDS." Every
   fail-closed rule is an equality or an order test: ``sum_v F_v = 1_Q``,
   ``blk M^{>N}_v >= p_v 1``, ``R^cg_{y_i|y_i} = 1``,
   ``Lambda^dagger(O^_k) >= 0``, ``O_i = cg^{-1}(y_i)``, ``sum_t q_t = 1``. A
   floating substrate turns each of them into an approximate comparison and
   needs a tolerance -- and a tolerance is precisely what the contract does not
   fix, so choosing one here would decide in code what the contract leaves
   open. Exactness is the reading that decides nothing.

2. **The one place the contract does speak about rounding says which way, and
   only in a future that has not arrived.** IF the receiver module ever emitted
   an exact or interval evaluation, the reductions module "MUST ROUND
   ``p_(y_i,t)`` TOWARD ZERO", because "a round-to-nearest result can exceed
   the true value, which would falsify ``eq:certweights`` -- the failure
   Assumption A-RECV's ledger row calls A SECURITY BREAK". Over exact
   rationals the single arithmetic evaluation ``eq:weightroute`` is exact, so
   the rule is never engaged and no rounding of any kind occurs. The direction
   is nonetheless recorded here, as :data:`WEIGHT_ROUNDING_DIRECTION`, so that
   the future change is a stated rule rather than a rediscovery.

3. **The upstream evaluation is floating point, and that is an argument FOR
   exactness here, not against it.** The receiver module's evaluation model
   (``receiver/def:evaluation-model``) makes the
   weights floating-point quantities, and the reductions module "PROPAGATES THE
   UPSTREAM ``bound_evaluation`` VALUE UNCHANGED AND NEVER UPGRADES IT". A
   binary64 value converts to a :class:`~fractions.Fraction` exactly and
   losslessly -- it IS a dyadic rational -- so an exact substrate costs the
   floating-point supplier nothing and loses no information it had. What it
   buys is that every downstream comparison is decided rather than
   approximated: the ``p < 1`` refusal test, the ``sum_i p_i <= 1`` input
   validation, and the ``blk M^{>N}_v >= p_v 1`` certificate become exact
   statements about the number the supplier actually emitted.

4. **The numbers are natively complex, and the distinction between Hermitian
   and symmetric is load-bearing.** Eq. ``eq:pairing`` and the uniqueness
   clause of Lemma ``lem:statistics`` are statements about Hermitian operators;
   a real-only representation would pass every real instance and silently
   conflate the two. Carrying the real and imaginary parts as separate exact
   rationals makes "is this quantity real?" a decided question, which is what
   Corollary ``cor:pullback`` (i) needs before ``tr[O^_k sigma]`` may be
   compared with ``c_k in R``. There is no site at which a complex value is
   silently narrowed: :func:`real_part` raises rather than drops, so the
   repository-wide ``filterwarnings = ["error"]`` has nothing to catch here.

5. **The frozen evidence is exact and is deliberately non-dyadic.** The oracle
   registries freeze every value as a Gaussian rational -- "NO FLOAT ANYWHERE"
   -- and chose "DELIBERATELY NON-DYADIC values ... so that the exact-to-machine
   conversion boundary is forced into the open rather than hidden behind
   fixtures that happen to convert without loss". With this substrate the
   frozen values are reproduced exactly and NO COMPARISON IN THE GOLDEN SUITE
   NEEDS A TOLERANCE.

WHY A ``float`` IS REFUSED AT THE BOUNDARY RATHER THAN CONVERTED
================================================================
:func:`as_scalar` accepts ``int``, :class:`~fractions.Fraction` and
:class:`Cx`, and refuses ``float`` and built-in ``complex`` with
:class:`~certiqs_key.foundations.errors.MalformedInputError`. Point 3 above says a
binary64 value converts exactly, so accepting it would violate nothing the
contract states. What it WOULD do is decide, silently and on the caller's
behalf, which of two rationals the caller meant: ``0.1`` read as ``1/10`` is
wrong by ``1/10 - Fraction(0.1)``, and on a certified weight an error in that
direction is exactly the security break Assumption A-RECV's ledger row names.
The caller converts explicitly -- ``Fraction(1, 10)`` for the intended value,
``Fraction(0.1)`` for the machine number the supplier actually holds -- and
that conversion is the caller SAYING which rational it means. A receiver
artifact whose numbers arrive as floats is docked by converting each with
``Fraction(value)``, which is lossless and is the caller's statement that the
machine number is the datum.

WHAT IS DECIDED EXACTLY, AND THE ONE THING THAT IS NOT
======================================================
Positivity is decided by an exact rational ``LDL^*`` with the zero-pivot rule
(:func:`is_positive_semidefinite`): no eigenvalue is computed and no threshold
appears, so a SINGULAR operator is accepted -- which every rank-one flag
projector and every tight instance of Eq. ``eq:certweights`` requires -- and
one with a negative eigenvalue is refused, with nothing in between. Rank, span
dimension and the space of linear relations among a family of operators
(:func:`span_dimension`, :func:`linear_relations`) are exact row reductions.

THE ONE THING THAT IS NOT DECIDED EXACTLY IS AN EIGENVALUE. Lemma
``lem:obstructions`` (i) is stated with ``inf spec X`` and ``sup spec X``,
which are real algebraic numbers and in general irrational.
:func:`spectral_bounds` returns a RATIONAL enclosing pair with a flag saying
whether it is tight, and :mod:`certiqs_key.reductions.validation` uses it in
the only direction that is sound: a refusal is issued only on a rational
certificate ``a 1 <= X <= b 1`` that the pull-back violates, so the rendering
of (i) refuses a strict subset of what (i) forbids and never refuses something
(i) permits. The site says so in full.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from fractions import Fraction
from itertools import combinations
from typing import Final

from certiqs_key.foundations.errors import HypothesisError, MalformedInputError

__all__ = [
    "BINARY64_OVERFLOW_THRESHOLD",
    "LATTICE_EXPONENT_MAX",
    "LATTICE_EXPONENT_MIN",
    "ONE",
    "WEIGHT_ROUNDING_DIRECTION",
    "ZERO",
    "Binary64Value",
    "Cx",
    "Matrix",
    "RoundsNowhere",
    "SpectralBounds",
    "SummationVerdict",
    "TraceVerdict",
    "Vector",
    "add",
    "addition_rounds_nowhere",
    "adjoint_from_kraus",
    "all_principal_minors_nonnegative",
    "as_rational",
    "as_scalar",
    "basis_projector",
    "conjugate_transpose",
    "deserialize_matrix",
    "diagonal",
    "dimension",
    "direct_sum",
    "equal",
    "factor_form",
    "identity",
    "inverse",
    "is_binary64",
    "is_diagonal",
    "is_hermitian",
    "is_positive_semidefinite",
    "is_square",
    "kron",
    "lattice_floor",
    "lattice_round",
    "lattice_round_matrix",
    "lattice_step",
    "linear_relations",
    "loewner_ge",
    "matmul",
    "matrix",
    "matrix_is_binary64",
    "on_lattice",
    "on_lattice_scalar",
    "outer_projector",
    "partial_trace_first",
    "partial_trace_second",
    "rank_factorisation",
    "real_part",
    "round_to_binary64",
    "scalar_is_binary64",
    "scale",
    "serialize_matrix",
    "span_dimension",
    "spectral_bounds",
    "subtract",
    "sum_in_declared_order",
    "sum_rounds_nowhere",
    "support_projector",
    "trace",
    "trace_in_row_order",
    "vector",
    "zeros",
]

#: The reductions module's conditional rounding rule, recorded as a DIRECTION
#: and never
#: exercised. It binds only if ``receiver-povm`` ever emits an exact or interval
#: ``bound_evaluation``; over this substrate ``eq:weightroute`` is exact, so no
#: value this module produces is ever rounded. See reason 2 in the module
#: docstring, and :mod:`certiqs_key.reductions.wpfss.weights`, which computes the one
#: arithmetic evaluation the rule is about.
WEIGHT_ROUNDING_DIRECTION: Final[str] = "toward_zero"


@dataclass(frozen=True, slots=True)
class Cx:
    """One exact Gaussian-rational scalar, as the pair (real, imaginary)."""

    re: Fraction
    im: Fraction

    def __add__(self, other: Cx) -> Cx:
        """Return the sum of two exact scalars."""
        return Cx(self.re + other.re, self.im + other.im)

    def __sub__(self, other: Cx) -> Cx:
        """Return the difference of two exact scalars."""
        return Cx(self.re - other.re, self.im - other.im)

    def __neg__(self) -> Cx:
        """Return the additive inverse."""
        return Cx(-self.re, -self.im)

    def __mul__(self, other: Cx) -> Cx:
        """Return the product of two exact scalars."""
        return Cx(
            self.re * other.re - self.im * other.im,
            self.re * other.im + self.im * other.re,
        )

    def conjugate(self) -> Cx:
        """Return the complex conjugate."""
        return Cx(self.re, -self.im)

    def over(self, divisor: Fraction) -> Cx:
        """Return the quotient by a non-zero RATIONAL divisor."""
        if divisor == 0:
            raise MalformedInputError("division by zero in the exact substrate")
        return Cx(self.re / divisor, self.im / divisor)

    @property
    def is_real(self) -> bool:
        """Whether the imaginary part vanishes exactly."""
        return self.im == 0

    @property
    def is_zero(self) -> bool:
        """Whether both parts vanish exactly."""
        return self.re == 0 and self.im == 0

    @property
    def squared_modulus(self) -> Fraction:
        """Return ``|z|^2 = x^2 + y^2``, which is always rational and exact.

        The modulus itself is the square root of this and is irrational for
        most Gaussian rationals, so every comparison of moduli in this
        repository is made here instead -- the ordering by squared modulus is
        the ordering by modulus, both being non-negative. The "THE MODULUS
        PROBLEM" section of :mod:`certiqs_key.foundations.exact_admission` is
        the argument for it; :mod:`certiqs_key.foundations.snap` reads it too,
        to report a lattice displacement without forming an irrational number.
        """
        return self.re * self.re + self.im * self.im

    def __str__(self) -> str:
        """Return the pair as ``re+im i`` with exact rational parts."""
        return f"{self.re}{'+' if self.im >= 0 else '-'}{abs(self.im)}i"


ZERO: Final[Cx] = Cx(Fraction(0), Fraction(0))
ONE: Final[Cx] = Cx(Fraction(1), Fraction(0))

#: A matrix is a tuple of rows; a vector is a tuple of entries.
Matrix = tuple[tuple[Cx, ...], ...]
Vector = tuple[Cx, ...]

_Scalar = int | Fraction | Cx


def as_scalar(value: object) -> Cx:
    """Return ``value`` as an exact :class:`Cx`.

    Accepts ``int``, :class:`~fractions.Fraction` and :class:`Cx`. Refuses
    ``float``, built-in ``complex`` and ``bool`` -- see the module docstring for
    why the refusal is the fail-closed reading and the conversion is the
    caller's.
    """
    if isinstance(value, Cx):
        return value
    if isinstance(value, bool):
        # bool is an int subclass; accepting it would let True mean 1 silently.
        raise MalformedInputError("a bool is not a presentation of a matrix entry")
    if isinstance(value, int):
        return Cx(Fraction(value), Fraction(0))
    if isinstance(value, Fraction):
        return Cx(value, Fraction(0))
    raise MalformedInputError(
        f"{type(value).__name__} is not an exact Gaussian rational; present an "
        "int, a Fraction or a Cx (certiqs_key.foundations.exact). A float converts "
        "exactly with Fraction(value); make that conversion explicitly so that "
        "the caller says which rational it means"
    )


def as_rational(value: object) -> Fraction:
    """Return ``value`` as an exact :class:`~fractions.Fraction`.

    The companion of :func:`as_scalar` for the quantities the contract types as
    REAL -- the weights ``p_v``, the probe weights ``q_t``, the stochastic
    entries ``R_{S|S'}``, the constants ``c_k``. Same refusal, same reason.
    """
    scalar = as_scalar(value)
    if not scalar.is_real:
        raise MalformedInputError("a real quantity was expected, not a complex one")
    return scalar.re


def matrix(rows: object) -> Matrix:
    """Return a matrix from an iterable of iterables of presentable entries.

    Refuses a ragged presentation: a matrix whose rows differ in length
    enumerates no operator, so no rule of the fail-closed table can be read against it.
    """
    if not isinstance(rows, tuple | list):
        raise MalformedInputError("a matrix is presented as a sequence of rows")
    built: list[tuple[Cx, ...]] = []
    width: int | None = None
    for row in rows:
        if not isinstance(row, tuple | list):
            raise MalformedInputError("each row of a matrix is a sequence of entries")
        entries = tuple(as_scalar(entry) for entry in row)
        if width is None:
            width = len(entries)
        elif len(entries) != width:
            raise MalformedInputError("ragged matrix: rows differ in length")
        built.append(entries)
    if width is None:
        raise MalformedInputError("a matrix has at least one row")
    return tuple(built)


def vector(entries: object) -> Vector:
    """Return a vector from an iterable of presentable entries."""
    if not isinstance(entries, tuple | list):
        raise MalformedInputError("a vector is presented as a sequence of entries")
    if not entries:
        raise MalformedInputError("a vector has at least one entry")
    return tuple(as_scalar(entry) for entry in entries)


def diagonal(values: Sequence[_Scalar]) -> Matrix:
    """Return the diagonal matrix with the given diagonal."""
    entries = [as_scalar(value) for value in values]
    n = len(entries)
    if n == 0:
        raise MalformedInputError("a diagonal matrix has at least one entry")
    return tuple(
        tuple(entries[i] if i == j else ZERO for j in range(n)) for i in range(n)
    )


def is_square(m: Matrix) -> bool:
    """Whether ``m`` has as many columns as rows."""
    return all(len(row) == len(m) for row in m)


def dimension(m: Matrix) -> int:
    """Return the dimension of a square matrix, refusing a non-square one."""
    if not is_square(m):
        raise MalformedInputError("a square matrix was expected")
    return len(m)


def zeros(rows: int, cols: int | None = None) -> Matrix:
    """Return the zero matrix of the given shape (square when ``cols`` is None)."""
    width = rows if cols is None else cols
    return tuple(tuple(ZERO for _ in range(width)) for _ in range(rows))


def identity(n: int) -> Matrix:
    """Return the identity operator on an ``n``-dimensional space."""
    if n < 1:
        raise MalformedInputError("the identity needs a positive dimension")
    return tuple(tuple(ONE if i == j else ZERO for j in range(n)) for i in range(n))


def basis_projector(n: int, index: int) -> Matrix:
    """Return ``|index><index|`` on an ``n``-dimensional space.

    The projector of a one-dimensional scalar sector is of this form -- a flag
    sector's ``|v><v|_Flag`` (``def:reduction-instance`` (I2)) -- and a branch
    projector of a register instance is the sum of the ones in its block
    (``cor:register-instance`` (i)).
    """
    if not 0 <= index < n:
        raise MalformedInputError("basis index outside the declared dimension")
    return tuple(
        tuple(ONE if (i == index and j == index) else ZERO for j in range(n))
        for i in range(n)
    )


def _same_shape(a: Matrix, b: Matrix) -> None:
    if len(a) != len(b) or any(len(x) != len(y) for x, y in zip(a, b, strict=True)):
        raise MalformedInputError("matrix shapes differ")


def add(a: Matrix, b: Matrix) -> Matrix:
    """Return ``a + b``."""
    _same_shape(a, b)
    return tuple(
        tuple(x + y for x, y in zip(ra, rb, strict=True))
        for ra, rb in zip(a, b, strict=True)
    )


def subtract(a: Matrix, b: Matrix) -> Matrix:
    """Return ``a - b``."""
    _same_shape(a, b)
    return tuple(
        tuple(x - y for x, y in zip(ra, rb, strict=True))
        for ra, rb in zip(a, b, strict=True)
    )


def scale(factor: _Scalar, m: Matrix) -> Matrix:
    """Return ``factor * m``."""
    value = as_scalar(factor)
    return tuple(tuple(value * entry for entry in row) for row in m)


def matmul(a: Matrix, b: Matrix) -> Matrix:
    """Return the matrix product ``a b``."""
    if len(a[0]) != len(b):
        raise MalformedInputError("inner dimensions differ in a matrix product")
    inner = len(b)
    return tuple(
        tuple(_sum(a[i][k] * b[k][j] for k in range(inner)) for j in range(len(b[0])))
        for i in range(len(a))
    )


def _sum(terms: Iterable[Cx]) -> Cx:
    total = ZERO
    for term in terms:
        total = total + term
    return total


def conjugate_transpose(m: Matrix) -> Matrix:
    """Return ``m^dagger``."""
    return tuple(
        tuple(m[j][i].conjugate() for j in range(len(m))) for i in range(len(m[0]))
    )


def equal(a: Matrix, b: Matrix) -> bool:
    """Whether two matrices are equal ENTRY FOR ENTRY, exactly."""
    if len(a) != len(b) or any(len(x) != len(y) for x, y in zip(a, b, strict=True)):
        return False
    return all(
        x == y for ra, rb in zip(a, b, strict=True) for x, y in zip(ra, rb, strict=True)
    )


def is_hermitian(m: Matrix) -> bool:
    """Whether ``m`` is Hermitian, decided exactly."""
    return is_square(m) and equal(m, conjugate_transpose(m))


def is_diagonal(m: Matrix) -> bool:
    """Whether every off-diagonal entry of ``m`` vanishes exactly."""
    return all(
        m[i][j].is_zero for i in range(len(m)) for j in range(len(m[0])) if i != j
    )


def trace(m: Matrix) -> Cx:
    """Return the trace of a square matrix."""
    return _sum(m[i][i] for i in range(dimension(m)))


def real_part(value: Cx, what: str) -> Fraction:
    """Return the real part of ``value``, refusing a genuinely complex one.

    Used where the contract compares a quantity with a real number -- the
    expectations of Corollary ``cor:pullback``, the diagonal entries of a flag
    block in Eq. ``eq:WPadjoint``. A dropped imaginary part would be a silent
    narrowing, so this raises instead.
    """
    if not value.is_real:
        raise HypothesisError(f"{what} is not real: {value}")
    return value.re


def kron(a: Matrix, b: Matrix) -> Matrix:
    """Return the Kronecker product ``a (x) b``, ``a`` the MAJOR factor.

    The order is the ``subsystem_order`` convention of the reductions core
    interface, whose locator is ``def:joint-family`` (a): on a product of a
    system with a register the system is MAJOR and the register MINOR, which is
    how the core's register instance writes its model,
    ``M_v = sum_j M_{v|j} (x) N_j`` on ``B = B_0 D``
    (``cor:register-instance``, Eq. ``eq:register-model``), and how its
    transport writes ``Lambda_j^dagger(Pi_s) (x) N_j``
    (Eq. ``eq:register-transport``). The same convention fixes the order on the
    target side.
    """
    rows_a, cols_a = len(a), len(a[0])
    rows_b, cols_b = len(b), len(b[0])
    return tuple(
        tuple(
            a[i // rows_b][j // cols_b] * b[i % rows_b][j % cols_b]
            for j in range(cols_a * cols_b)
        )
        for i in range(rows_a * rows_b)
    )


def direct_sum(blocks: Sequence[Matrix]) -> Matrix:
    """Return the block-diagonal direct sum of square blocks, in order.

    This is the ``(+)`` of Eq. ``eq:instance-target`` -- a reduction instance's
    target assembled one sector block at a time
    (``def:reduction-instance`` (I2)) -- and the order of the blocks IS the
    subsystem order of the conventions block.
    """
    if not blocks:
        raise MalformedInputError("a direct sum has at least one block")
    dims = [dimension(block) for block in blocks]
    total = sum(dims)
    offsets: list[int] = []
    running = 0
    for dim in dims:
        offsets.append(running)
        running += dim
    rows: list[tuple[Cx, ...]] = []
    for block_index, block in enumerate(blocks):
        offset = offsets[block_index]
        for i in range(dims[block_index]):
            row = [ZERO] * total
            for j in range(dims[block_index]):
                row[offset + j] = block[i][j]
            rows.append(tuple(row))
    return tuple(rows)


def adjoint_from_kraus(kraus: Sequence[Matrix], x: Matrix) -> Matrix:
    """Return ``Lambda^dagger(X) = sum_K K^dagger X K``.

    Eq. ``eq:pairing`` read through a Kraus set: for
    ``Lambda(rho) = sum_K K rho K^dagger`` the pairing
    ``tr[X Lambda(rho)] = tr[Lambda^dagger(X) rho]`` gives exactly this sum, and
    unitality ``Lambda^dagger(1_Q) = 1_B`` is Kraus completeness
    ``sum_K K^dagger K = 1_B``.

    Only the instances whose Kraus operators are Gaussian-rational can be given
    this way; the outputs table records that the emitted ``squashing_channel`` is "a
    SYMBOLIC CONSTRUCTOR RECORD, NOT EVALUABLE DATA" because the supplier emits
    no above-cutoff block. The closed-form adjoints of
    :mod:`certiqs_key.reductions.channels` are what the contract's statements
    are about; this function exists so that a closed form can be checked against
    an explicit realization where one is available.
    """
    if not kraus:
        raise MalformedInputError("a Kraus set has at least one operator")
    out = zeros(len(kraus[0][0]))
    for operator in kraus:
        out = add(out, matmul(matmul(conjugate_transpose(operator), x), operator))
    return out


def is_positive_semidefinite(m: Matrix) -> bool:
    """Whether a Hermitian ``m`` is positive semidefinite, decided EXACTLY.

    The reference method is a rational ``LDL^*`` with the zero-pivot rule, run
    on Gaussian rationals: at each step the pivot must be non-negative, and a
    zero pivot forces its whole remaining row to vanish (by Cauchy-Schwarz,
    ``|m_kj|^2 <= m_kk m_jj = 0``). No eigenvalue is computed and no threshold
    appears, so a SINGULAR operator is accepted -- which every rank-one flag
    projector is, and which the tight end of Eq. ``eq:certweights`` needs -- and
    one with a negative eigenvalue is refused, with nothing in between.

    A non-Hermitian argument raises
    :class:`~certiqs_key.foundations.errors.HypothesisError`
    rather than returning ``False``: positivity is a property of a Hermitian
    operator, and a ``False`` here would report a failed certificate where none
    was tested.
    """
    if not is_hermitian(m):
        raise HypothesisError(
            "positive semidefiniteness is a property of a Hermitian operator; "
            "test Hermiticity first"
        )
    n = len(m)
    work = [list(row) for row in m]
    for k in range(n):
        pivot = work[k][k]
        # Hermiticity is preserved by the Schur update, so the pivot is real.
        if pivot.im != 0 or pivot.re < 0:
            return False
        if pivot.re == 0:
            if any(not work[k][j].is_zero for j in range(k + 1, n)):
                return False
            continue
        for i in range(k + 1, n):
            if work[i][k].is_zero:
                continue
            for j in range(k + 1, n):
                work[i][j] = work[i][j] - (work[i][k] * work[k][j]).over(pivot.re)
    return True


def is_positive_definite(m: Matrix) -> bool:
    """Whether a Hermitian ``m`` is positive definite, decided EXACTLY.

    The same rational ``LDL^*`` as :func:`is_positive_semidefinite`, with every
    pivot required to be strictly positive: a Hermitian matrix is positive
    definite exactly when its symmetric elimination meets no pivot ``<= 0``
    (Sylvester's criterion read through the elimination). It is the decision
    ``foundations/lem:enclosure-psd`` (i), last clause, takes on
    ``C - rho 1``.

    A non-Hermitian argument raises
    :class:`~certiqs_key.foundations.errors.HypothesisError`, as for
    :func:`is_positive_semidefinite`.
    """
    if not is_hermitian(m):
        raise HypothesisError(
            "positive definiteness is a property of a Hermitian operator; "
            "test Hermiticity first"
        )
    n = len(m)
    work = [list(row) for row in m]
    for k in range(n):
        pivot = work[k][k]
        if pivot.im != 0 or pivot.re <= 0:
            return False
        for i in range(k + 1, n):
            if work[i][k].is_zero:
                continue
            for j in range(k + 1, n):
                work[i][j] = work[i][j] - (work[i][k] * work[k][j]).over(pivot.re)
    return True


def is_complete_at(family: Sequence[Matrix], constant: Fraction) -> bool:
    """Whether ``sum_j F_j = c 1`` holds exactly, entry for entry.

    The completeness of ``foundations/def:exact-admissibility`` and
    ``foundations/def:exact-reference`` at a constant ``c`` that need not be
    one (a class-weighted family is complete at its weight). The exact sum,
    not the binary64 accumulation; whether that accumulation rounds nowhere is
    :func:`sum_rounds_nowhere`'s question.
    """
    if not family:
        raise MalformedInputError(
            "completeness is a statement about a non-empty family"
        )
    n = dimension(family[0])
    target = Cx(Fraction(constant), Fraction(0))
    for i in range(n):
        for j in range(n):
            total = _sum(element[i][j] for element in family)
            if total != (target if i == j else ZERO):
                return False
    return True


def loewner_ge(a: Matrix, b: Matrix) -> bool:
    """Whether ``a >= b`` in the Loewner order, i.e. whether ``a - b`` is PSD.

    The order is defined on Hermitian operators; a comparison whose left-hand
    side is not Hermitian has no truth value rather than the value ``False``, so
    a non-Hermitian argument raises. This is the comparison
    Eq. ``eq:certweights`` and Eq. ``eq:certificate`` are written in.
    """
    if not is_hermitian(a) or not is_hermitian(b):
        raise HypothesisError(
            "the Loewner order compares Hermitian operators; test Hermiticity first"
        )
    return is_positive_semidefinite(subtract(a, b))


@dataclass(frozen=True, slots=True)
class SpectralBounds:
    """A RATIONAL enclosure of the spectrum of a Hermitian operator.

    ``lower <= inf spec X`` and ``sup spec X <= upper``, both exact rationals,
    with ``tight`` recording whether the enclosure is the spectrum's own hull.

    WHY AN ENCLOSURE AND NOT THE SPECTRUM. Lemma ``lem:obstructions`` (i) is
    stated with ``inf spec X`` and ``sup spec X``, which are real algebraic
    numbers and in general irrational; there is no exact rational
    representation of them, and the contract fixes no numeric type in which one
    could be approximated (open implementation choice 1). What IS exact, and is
    all the lemma's PROOF uses, is the operator inequality
    ``lower 1 <= X <= upper 1``: the proof reads "applying the positive unital
    map ``Lambda^dagger`` preserves both inequalities". So an enclosure with a
    rational certificate transports exactly, and a violation of the transported
    enclosure is a rational proof that no channel realizes the relation.

    ``tight`` is ``True`` exactly when ``X`` is diagonal, where the enclosure is
    the set of diagonal entries and therefore the spectrum itself. Every target
    a reduction instance emits is sector-block-diagonal by construction
    (``def:reduction-instance`` (I2), second consequence)
    and every sector of the emitted flag space is one-dimensional, so the flag
    part of an emitted target is diagonal; a preserved photon-number block of
    dimension above one need not be.
    """

    lower: Fraction
    upper: Fraction
    tight: bool


def spectral_bounds(m: Matrix) -> SpectralBounds:
    """Return an exact rational enclosure of the spectrum of Hermitian ``m``.

    Diagonal ``m``: the minimum and maximum diagonal entry, which IS the
    spectrum, so ``tight`` is ``True``.

    Otherwise the Gershgorin enclosure, which is exact and rational: every
    eigenvalue lies in some disc centred at a diagonal entry with radius the sum
    of the moduli of that row's off-diagonal entries. The moduli are square
    roots and are not rational, so the radius used is the exact rational
    upper bound ``|z| <= |Re z| + |Im z|``; that widens the enclosure and never
    narrows it, which is the safe direction for a necessary condition whose
    violation is a refusal.
    """
    if not is_hermitian(m):
        raise HypothesisError("spectral bounds are read off a Hermitian operator")
    n = len(m)
    if is_diagonal(m):
        diag = [m[i][i].re for i in range(n)]
        return SpectralBounds(min(diag), max(diag), tight=True)
    lower = None
    upper = None
    for i in range(n):
        radius = sum(
            (abs(m[i][j].re) + abs(m[i][j].im) for j in range(n) if j != i),
            start=Fraction(0),
        )
        low = m[i][i].re - radius
        high = m[i][i].re + radius
        lower = low if lower is None or low < lower else lower
        upper = high if upper is None or high > upper else upper
    if lower is None or upper is None:  # pragma: no cover - n >= 1 always
        raise HypothesisError("a Hermitian operator has at least one row")
    return SpectralBounds(lower, upper, tight=False)


def _row_reduce(rows: Sequence[Sequence[Cx]]) -> list[list[Cx]]:
    """Return the row-echelon form of a rectangular Gaussian-rational array."""
    work = [list(row) for row in rows]
    if not work:
        return work
    width = len(work[0])
    pivot_row = 0
    for col in range(width):
        candidate = next(
            (r for r in range(pivot_row, len(work)) if not work[r][col].is_zero),
            None,
        )
        if candidate is None:
            continue
        work[pivot_row], work[candidate] = work[candidate], work[pivot_row]
        pivot = work[pivot_row][col]
        scale_re = pivot.re * pivot.re + pivot.im * pivot.im
        inverse = pivot.conjugate().over(scale_re)
        work[pivot_row] = [inverse * entry for entry in work[pivot_row]]
        for r in range(len(work)):
            if r == pivot_row or work[r][col].is_zero:
                continue
            factor = work[r][col]
            work[r] = [work[r][c] - factor * work[pivot_row][c] for c in range(width)]
        pivot_row += 1
        if pivot_row == len(work):
            break
    return work


def span_dimension(operators: Sequence[Matrix]) -> int:
    """Return ``dim span{operators}`` over the REALS, decided exactly.

    Lemma ``lem:obstructions`` (ii) compares ``dim span{M_v}`` with
    ``dim span{F_v}``. The span is the real linear span -- the lemma's linear
    combinations ``sum_v a_v F_v`` have real coefficients ``a_v`` -- so each
    operator is flattened into the real vector of its entries' real and
    imaginary parts and the rank is a rational row reduction.
    """
    if not operators:
        return 0
    flattened = [
        [
            Cx(part, Fraction(0))
            for row in operator
            for entry in row
            for part in (entry.re, entry.im)
        ]
        for operator in operators
    ]
    reduced = _row_reduce(flattened)
    return sum(1 for row in reduced if any(not entry.is_zero for entry in row))


def linear_relations(
    operators: Sequence[Matrix], identity_operator: Matrix
) -> tuple[tuple[Fraction, ...], ...]:
    """Return a basis of the real solutions ``(a_v, c)`` of ``sum_v a_v F_v = c 1``.

    Lemma ``lem:obstructions`` (ii)'s second clause: "every linear relation
    ``sum_v a_v F_v = c 1_Q`` FORCES ``sum_v a_v M_v = c 1_B``". Deciding the
    clause needs the relations themselves, and they are the null space of the
    real linear map ``(a, c) -> sum_v a_v F_v - c 1_Q``, computed exactly.

    Each returned tuple has ``len(operators) + 1`` entries, the last being ``c``.
    """
    columns = [*operators, scale(-1, identity_operator)]
    # One equation per matrix entry and per real/imaginary part; one unknown per
    # column, the last unknown being c.
    rows: list[list[Cx]] = [
        [
            Cx(
                operator[i][j].re if part == 0 else operator[i][j].im,
                Fraction(0),
            )
            for operator in columns
        ]
        for i in range(len(identity_operator))
        for j in range(len(identity_operator))
        for part in (0, 1)
    ]
    reduced = _row_reduce(rows)
    width = len(columns)
    pivots: list[int] = []
    for row in reduced:
        pivot = next((c for c in range(width) if not row[c].is_zero), None)
        if pivot is not None:
            pivots.append(pivot)
    free = [c for c in range(width) if c not in pivots]
    basis: list[tuple[Fraction, ...]] = []
    for column in free:
        solution = [Fraction(0)] * width
        solution[column] = Fraction(1)
        for index, pivot in enumerate(pivots):
            solution[pivot] = -reduced[index][column].re
        basis.append(tuple(solution))
    return tuple(basis)


def serialize_matrix(m: Matrix) -> list[list[list[str]]]:
    """Return a matrix as nested lists of exact decimal-free string pairs.

    Each entry becomes ``[str(re), str(im)]`` -- ``"3/4"``, ``"0"``, ``"-1/2"``
    -- which :func:`deserialize_matrix` reads back with
    :class:`~fractions.Fraction`'s own parser, exactly and without loss. The
    contract fixes no encoding for any emitted matrix, so this is a
    serialization decision with no proof-relevant content; what it buys is that
    an artifact a key-rate run logs can be re-read without a numeric conversion.
    """
    return [[[str(entry.re), str(entry.im)] for entry in row] for row in m]


def deserialize_matrix(payload: Sequence[Sequence[Sequence[str]]]) -> Matrix:
    """Return the matrix :func:`serialize_matrix` wrote, exactly."""
    return matrix(
        [
            [Cx(Fraction(entry[0]), Fraction(entry[1])) for entry in row]
            for row in payload
        ]
    )


def all_principal_minors_nonnegative(m: Matrix) -> bool:
    """Whether every principal minor of Hermitian ``m`` is non-negative.

    An independent second decision procedure for positive semidefiniteness,
    kept beside :func:`is_positive_semidefinite` because the two are proved
    equivalent and neither is derived from the other. The enumeration is
    ``2^n - 1`` minors and is exponential, so it is used only where ``n`` is
    small -- the property tests compare the two on random small operators.
    """
    if not is_hermitian(m):
        raise HypothesisError("principal minors are read off a Hermitian operator")
    n = len(m)
    for size in range(1, n + 1):
        for idx in combinations(range(n), size):
            minor = tuple(tuple(m[i][j] for j in idx) for i in idx)
            value = _determinant(minor)
            if value.im != 0 or value.re < 0:
                return False
    return True


def _determinant(m: Matrix) -> Cx:
    n = len(m)
    if n == 0:
        return ONE
    if n == 1:
        return m[0][0]
    total = ZERO
    for j in range(n):
        minor = tuple(tuple(m[i][k] for k in range(n) if k != j) for i in range(1, n))
        term = m[0][j] * _determinant(minor)
        total = total + term if j % 2 == 0 else total - term
    return total


# ---------------------------------------------------------------------------
#  The declared lattice: Eq. eq:latinv, Eq. eq:latdown and def:emitnorm (2)
# ---------------------------------------------------------------------------
#
#  Four primitives and one predicate, all of them exact and none of them carrying a
#  tolerance, a window or a ladder. THIS MODULE HAS NO TOLERANCE (the conventions block,
#  `numerical_model`; interface.yaml, numerical_model), so nothing below takes one; and
#  kappa "fixes a SET of representable numbers and DECIDES NO PREDICATE ABOUT HOW NEAR
#  ONE NUMBER IS TO ANOTHER" (the inputs table, `lattice_exponent`).
#
#  THE TWO ROUNDINGS ARE DIFFERENT MECHANISMS AND ARE DELIBERATELY TWO
#  FUNCTIONS. :func:`lattice_round` is def:emitnorm (2) -- TO NEAREST, WITH
#  TIES TO EVEN -- and acts on OPERATOR ENTRIES this module computed.
#  :func:`lattice_floor` is Eq. eq:latdown -- DOWNWARD, a floor, with no tie to
#  break -- and acts on the CERTIFIED WEIGHTS of Eq. eq:weightroute. Their
#  safety arguments are different and neither may be used for the other's job:
#  the floor is safe because "lowering a certified weight PRESERVES
#  eq:certweights and raising one DESTROYS it", and to-nearest is correct
#  because it is odd-symmetric and therefore carries a Hermitian block to a
#  Hermitian one.

#: Eq. eq:latinv's bounds on the declared exponent: ``1 <= kappa <= 53``. The
#: upper bound is the binary64 significand: "such an x is exactly a binary64
#: number, its significand carrying at most kappa <= 53 bits".
LATTICE_EXPONENT_MIN: Final[int] = 1
LATTICE_EXPONENT_MAX: Final[int] = 53


def lattice_step(kappa: int) -> Fraction:
    """Return ``2^-kappa``, the spacing of the declared lattice.

    Args:
        kappa: the declared exponent, ``1 <= kappa <= 53``.

    Raises:
        MalformedInputError: if ``kappa`` is outside Eq. eq:latinv's bounds.
            A value outside them is not a lattice exponent at all; the
            REFUSAL that a caller receives for one is the fail-closed table's
            ``lattice_exponent_not_declared`` row, decided in
            :mod:`certiqs_key.reductions.validation` before this is reached.
    """
    if kappa < LATTICE_EXPONENT_MIN or kappa > LATTICE_EXPONENT_MAX:
        raise MalformedInputError(
            f"kappa = {kappa} is outside Eq. eq:latinv's 1 <= kappa <= 53; the "
            "declared exponent is validated by the fail-closed table's lattice row "
            "before any arithmetic reads it"
        )
    return Fraction(1, 1 << kappa)


def on_lattice_scalar(value: Fraction, kappa: int) -> bool:
    """Whether one real part satisfies Eq. eq:latinv: ``2^k x in Z`` and ``|x| <= 1``.

    BOTH CONJUNCTS, and the second is not a convenience: eq:latinv is
    ``2^kappa x in Z``, ``|x| <= 1``, ``1 <= kappa <= 53`` -- the modulus bound
    is what makes the value's significand fit in kappa bits and therefore what
    makes it "exactly a binary64 number".
    """
    return (value * (1 << kappa)).denominator == 1 and abs(value) <= 1


def on_lattice(m: Matrix, kappa: int) -> bool:
    """Whether every entry of ``m`` satisfies Eq. eq:latinv.

    Definition ``def:exactadm`` (b), last sentence, and it is read exactly as
    written: "A COMPLEX ENTRY SATISFIES eq:latinv WHEN ITS REAL AND IMAGINARY
    PARTS DO." So the test is ``|Re z| <= 1`` and ``|Im z| <= 1`` **part by
    part**, and NOT ``|z| <= 1`` on the modulus of the entry.

    THE DISTINCTION IS NOT COSMETIC. A binary64 snapping kernel deciding the
    same invariant with ``entry.squared_modulus > 1`` would refuse
    ``0.75 + 0.75i`` -- both parts on the lattice and both of modulus at most
    one, so ADMISSIBLE under def:exactadm (b). Such a divergence would be in
    the refusing direction, on a condition the contract fixes. The kernel
    :mod:`certiqs_key.foundations.snap` has an ``is_on_lattice`` that agrees
    with this predicate, part by part, as ``foundations/req:declared-lattice``
    states it.
    """
    step = 1 << kappa
    for row in m:
        for entry in row:
            if (entry.re * step).denominator != 1 or abs(entry.re) > 1:
                return False
            if (entry.im * step).denominator != 1 or abs(entry.im) > 1:
                return False
    return True


def lattice_round(value: Fraction, kappa: int) -> Fraction:
    """Round one exact rational to the nearest multiple of ``2^-kappa``, TIES TO EVEN.

    Definition ``def:emitnorm`` (2) **as amended at contract version 1.0.1**:
    "every real and imaginary part of every entry to the nearest integer
    multiple of ``2^-kappa``, WITH TIES TO EVEN --- a part lying exactly
    halfway between two multiples goes to the one whose integer numerator is
    even."

    THE TIE IS EXACT AND THE RULE IS NOT INHERITED FROM ANYWHERE. The contract
    says so in terms: "this step is carried out in the rational substrate of
    Lemma ``lem:exactpsd`` ON NUMBERS THAT ARE EXACT RATIONALS, so a halfway
    part is AN EXACT EQUALITY rather than a floating-point near-miss, and
    IEEE 754's own tie rule governs binary64 OPERATIONS and decides nothing
    about a rounding this contract defines on the rationals." So the arithmetic
    below is integer arithmetic on ``2^kappa * value`` and never touches a
    float, and Python's own ``round`` is not called: it would agree here, but
    agreeing is not the same as being the rule.

    WHY TIES TO EVEN AND NOT AWAY FROM ZERO -- the contract's own argument, and
    it is what licenses the ORDER of the steps: ties to even "IS
    ODD-SYMMETRIC", so "the rounded value of a negated part is the negative of
    the rounded value of the part", the step "THEREFORE COMMUTES WITH
    A -> A-dagger" and "a Hermitian block comes out Hermitian". Hence "STEP (1)
    IS NOT RE-RUN AFTER STEP (2)". A tie rule that is not odd-symmetric would
    require it to be, and this implementation would then be wrong in its step
    order rather than merely in one entry.

    Args:
        value: an exact rational, of any denominator.
        kappa: the declared exponent.

    Returns:
        The nearest integer multiple of ``2^-kappa``, ties to even.
    """
    scale_up = 1 << kappa
    scaled = value * scale_up
    floor_numerator = scaled.numerator // scaled.denominator
    remainder = scaled - floor_numerator
    if remainder * 2 > 1:
        chosen = floor_numerator + 1
    elif remainder * 2 < 1:
        chosen = floor_numerator
    else:
        # An EXACT tie: the part lies exactly halfway between two multiples.
        # Take the one whose integer numerator is even (def:emitnorm (2)).
        chosen = floor_numerator if floor_numerator % 2 == 0 else floor_numerator + 1
    return Fraction(chosen, scale_up)


def lattice_round_matrix(m: Matrix, kappa: int) -> Matrix:
    """Apply :func:`lattice_round` to every real and imaginary part of ``m``.

    Definition ``def:emitnorm`` (2), on a whole block. The entries are rounded
    part by part, which is what makes the step commute with the adjoint and
    what lets ``def:emitnorm`` skip re-running step (1).
    """
    return tuple(
        tuple(
            Cx(lattice_round(entry.re, kappa), lattice_round(entry.im, kappa))
            for entry in row
        )
        for row in m
    )


def lattice_floor(value: Fraction, kappa: int) -> Fraction:
    """Return ``lat(x) = 2^-kappa floor(2^kappa x)`` -- Eq. ``eq:latdown``.

    "The LARGEST integer multiple of ``2^-kappa`` that is AT MOST ``x`` --- the
    DOWNWARD rounding onto the declared lattice, computed exactly on the
    rational ... and equal to it whenever it is already a lattice number."

    A FLOOR HAS NO TIE TO BREAK, which is why this function takes no tie rule
    and why ``interface.yaml`` records the rounding tie of ``def:emitnorm`` (2)
    as biting "NOT on eq:latdown". It is also why it may not be reused for
    ``def:emitnorm`` (2): rounding an operator entry down would break the
    odd-symmetry that carries a Hermitian block to a Hermitian one.

    THE DIRECTION IS THE WHOLE OF WHAT MAKES THE EMITTED WEIGHT SAFE:
    Eq. eq:certweights "IS PRESERVED WHEN A CERTIFIED WEIGHT IS LOWERED AND
    DESTROYED WHEN ONE IS RAISED, and lat(.) ONLY LOWERS" (Prop. prop:route,
    Rem. rem:weightfree; spec/architecture.md 2.9, condition (D-DIR)).

    ``p >= 0`` needs no clamp: "the largest lattice number at most a
    non-negative rational is itself non-negative" (the receiver-consumption block (d)).
    """
    scale_up = 1 << kappa
    scaled = value * scale_up
    return Fraction(scaled.numerator // scaled.denominator, scale_up)


# ---------------------------------------------------------------------------
#  SEVEN FUNCTIONS THE PROTOCOL COMPILER READS
#
#  The exact substrate is declared once, here, because no module can import a
#  sibling: the two partial traces, the rank-one projector taken without a
#  square root, the support projector, the exact inverse, the binary64 rounding
#  and the entrywise binary64 predicate on a matrix. Nothing of it is declared
#  twice.
# ---------------------------------------------------------------------------


def _check_composite(m: Matrix, first_dim: int, second_dim: int) -> None:
    """Refuse a matrix that is not an operator on the declared composite."""
    if dimension(m) != first_dim * second_dim:
        raise MalformedInputError(
            f"a matrix of dimension {dimension(m)} is not an operator on a "
            f"{first_dim} x {second_dim} composite system"
        )


def partial_trace_second(m: Matrix, first_dim: int, second_dim: int) -> Matrix:
    """Return ``tr_2 m`` on the FIRST factor -- the ``A``-marginal ``omega_A``.

    With the ``subsystem_order`` convention putting ``A`` first, this is the
    partial trace over the second factor that the compiler's ``def:feasible``
    marginal condition and the trusted line of ``eq:feas-modes`` read.
    """
    _check_composite(m, first_dim, second_dim)
    return tuple(
        tuple(
            _sum(m[i * second_dim + q][j * second_dim + q] for q in range(second_dim))
            for j in range(first_dim)
        )
        for i in range(first_dim)
    )


def partial_trace_first(m: Matrix, first_dim: int, second_dim: int) -> Matrix:
    """Return ``tr_1 m`` on the SECOND factor.

    This is ``tr_A`` of (SR2) and ``tr_{A''}`` of (SR1) -- the certificate
    conditions of ``transmitter/def:srcert``, whose operator lives on ``A A''``
    with ``A`` first.
    """
    _check_composite(m, first_dim, second_dim)
    return tuple(
        tuple(
            _sum(m[i * second_dim + q][i * second_dim + r] for i in range(first_dim))
            for r in range(second_dim)
        )
        for q in range(second_dim)
    )


def outer_projector(amplitudes: Vector, squared_norm: Fraction) -> Matrix:
    """Return ``|Psi><Psi|`` for ``|Psi> = amplitudes / sqrt(squared_norm)``.

    THE SQUARE ROOT IS NEVER TAKEN. A certificate asks for a UNIT vector, and
    the unit vectors this repository exhibits -- ``|Phi^+>`` first among them
    -- have irrational amplitudes and PERFECTLY RATIONAL PROJECTORS. Carrying
    the vector as an exact unnormalized Gaussian-rational ``v`` together with
    its exact squared norm ``N = v^dag v`` keeps both the normalization
    condition and the projector ``v v^dag / N`` inside the substrate. That is
    the representation the frozen registries use, for the same reason.
    """
    if squared_norm <= 0:
        raise MalformedInputError("the squared norm of a unit vector is positive")
    computed = _sum(entry.conjugate() * entry for entry in amplitudes)
    if computed != Cx(squared_norm, Fraction(0)):
        raise MalformedInputError(
            f"the declared squared norm {squared_norm} is not v^dag v = {computed}"
        )
    return tuple(
        tuple(
            (amplitudes[i] * amplitudes[j].conjugate()).over(squared_norm)
            for j in range(len(amplitudes))
        )
        for i in range(len(amplitudes))
    )


def _quotient(numerator: Cx, denominator: Cx) -> Cx:
    """Return ``numerator / denominator`` for a non-zero Gaussian rational."""
    modulus = denominator.re * denominator.re + denominator.im * denominator.im
    if modulus == 0:
        raise MalformedInputError("division by zero in the exact substrate")
    return (numerator * denominator.conjugate()).over(modulus)


def _pivot_columns(m: Matrix) -> tuple[int, ...]:
    """Return the pivot column indices of the row-echelon form of ``m``."""
    rows = [list(row) for row in m]
    pivots: list[int] = []
    row_index = 0
    for col in range(len(m[0])):
        pivot_row = next(
            (r for r in range(row_index, len(rows)) if not rows[r][col].is_zero),
            None,
        )
        if pivot_row is None:
            continue
        rows[row_index], rows[pivot_row] = rows[pivot_row], rows[row_index]
        head = rows[row_index][col]
        for r in range(len(rows)):
            if r == row_index or rows[r][col].is_zero:
                continue
            factor = rows[r][col]
            for c in range(len(rows[r])):
                rows[r][c] = rows[r][c] - _quotient(factor * rows[row_index][c], head)
        pivots.append(col)
        row_index += 1
        if row_index == len(rows):
            break
    return tuple(pivots)


def inverse(m: Matrix) -> Matrix:
    """Return the inverse of a non-singular square matrix, exactly."""
    n = dimension(m)
    work = [list(row) + list(identity(n)[i]) for i, row in enumerate(m)]
    for col in range(n):
        pivot_row = next((r for r in range(col, n) if not work[r][col].is_zero), None)
        if pivot_row is None:
            raise MalformedInputError("a singular matrix has no inverse")
        work[col], work[pivot_row] = work[pivot_row], work[col]
        head = work[col][col]
        work[col] = [_quotient(entry, head) for entry in work[col]]
        for r in range(n):
            if r == col or work[r][col].is_zero:
                continue
            factor = work[r][col]
            work[r] = [
                entry - factor * pivot_entry
                for entry, pivot_entry in zip(work[r], work[col], strict=True)
            ]
    return tuple(tuple(row[n:]) for row in work)


def support_projector(m: Matrix) -> Matrix:
    """Return ``Pi_S``, the orthogonal projector onto the range of Hermitian ``m``.

    ``transmitter/thm:certificate-sufficiency`` (ii) states its consistency criterion on
    ``Pi_S (sum_x M_x) Pi_S = Pi_S`` with ``S = supp tau_A``, and the projector
    is what makes that an ``if and only if`` rather than a sufficient
    condition. It is computed exactly and WITHOUT a square root: take a maximal
    independent set ``B`` of columns of ``m``, whose span is the range, and
    form ``B (B^dag B)^{-1} B^dag``. The Gram matrix is non-singular exactly
    because the columns are independent, and every entry of the result is a
    Gaussian rational.
    """
    n = dimension(m)
    if not is_hermitian(m):
        raise HypothesisError("the support projector is defined for Hermitian data")
    pivots = _pivot_columns(m)
    if not pivots:
        return zeros(n, n)
    basis = tuple(tuple(m[i][c] for c in pivots) for i in range(n))
    basis_dag = conjugate_transpose(basis)
    gram = matmul(basis_dag, basis)
    return matmul(matmul(basis, inverse(gram)), basis_dag)


def rank_factorisation(m: Matrix) -> tuple[Matrix, Matrix]:
    """Return ``(B, C)`` with ``m = B C`` exactly, both of rank ``rank m``.

    ``B`` is ``m``'s pivot columns (full column rank) and ``C`` the non-zero
    rows of its reduced row-echelon form (full row rank): the exactly formed
    rank factorisation ``meat-core/frank-wolfe/req:certified-evaluation``
    (iii)(a) asks of an exact listing. A zero ``m`` gives ``B`` with no
    columns and no ``C``.
    """
    pivots = _pivot_columns(m)
    reduced = _row_reduce(m)[: len(pivots)]
    basis = tuple(tuple(row[c] for c in pivots) for row in m)
    return basis, tuple(tuple(row) for row in reduced)


def factor_form(m: Matrix) -> tuple[Matrix, Matrix] | None:
    """Return ``(E, X)`` with ``m = E^dagger X E``, ``E`` of full row rank, ``X`` PD.

    ``foundations/cor:least-eigenvalue-over-enclosure`` (iii) on exact data:
    ``P`` the pivot columns of ``m``, ``X = m[P, P]`` (decided positive
    definite exactly) and ``E = X^{-1} m[P, :]``, whose columns ``P`` are the
    identity. Then ``E^dagger X E = m[:, P] X^{-1} m[P, :] = m`` because
    ``rank m = |P|`` and ``X`` is invertible, so ``m`` is positive
    semidefinite with support ``ran E^dagger``. ``None`` for the zero matrix.

    Raises:
        HypothesisError: ``m`` is not Hermitian or ``m[P, P]`` is not positive
            definite, so ``m`` is not positive semidefinite.
    """
    pivots = _pivot_columns(m)
    if not pivots:
        return None
    core = tuple(tuple(m[i][j] for j in pivots) for i in pivots)
    if not is_hermitian(m) or not is_positive_definite(core):
        raise HypothesisError("a factor form E^dagger X E needs a PSD Hermitian m")
    return matmul(inverse(core), tuple(m[i] for i in pivots)), core


def scalar_is_binary64(value: Cx) -> bool:
    """Whether both parts of a Gaussian rational are binary64 numbers.

    Implements ``foundations/def:binary64`` (i): membership in ``B_C``.
    """
    return is_binary64(value.re) and is_binary64(value.im)


def matrix_is_binary64(m: Matrix) -> bool:
    """Whether every entry of ``m`` is a binary64 number, part by part."""
    return all(scalar_is_binary64(entry) for row in m for entry in row)


#: A value of ``fl`` on real input: an element of ``B`` as the exact rational
#: it is, or a signed infinity (``foundations/def:binary64`` (ii)). The
#: infinity is a ``float`` because no :class:`~fractions.Fraction` is one; a
#: finite ``float`` never appears as a value of :func:`round_to_binary64`.
type Binary64Value = Fraction | float

#: ``foundations/def:binary64`` (ii): ``fl(x)`` is a signed infinity for
#: ``|x| >= 2^1024 - 2^970``, the midpoint between the largest element
#: ``(2^53 - 1) 2^971`` of ``B`` and ``2^1024``, where IEEE 754 rounding to
#: nearest overflows.
BINARY64_OVERFLOW_THRESHOLD: Final[Fraction] = Fraction((1 << 1024) - (1 << 970))


def round_to_binary64(value: Fraction | float) -> Binary64Value:
    """Return ``fl(value)`` of ``foundations/def:binary64`` (ii).

    Round-to-nearest, ties to even, for ``|value| < 2^1024 - 2^970``,
    delegated to the platform's correctly rounded conversion; a signed
    infinity at and beyond that threshold, decided here on the exact rational
    so that an overflow is a VALUE and never an ``OverflowError``; and
    ``fl(+-inf + y) = +-inf``, which is why an infinite ``float`` argument is
    returned unchanged. A finite ``float`` argument is the binary64 number it
    is, and is read exactly.
    """
    if isinstance(value, float):
        if math.isinf(value):
            return value
        if math.isnan(value):
            raise MalformedInputError("fl is not defined at NaN (def:binary64 (ii))")
        value = Fraction(value)
    if abs(value) >= BINARY64_OVERFLOW_THRESHOLD:
        return math.inf if value > 0 else -math.inf
    return Fraction(float(value))


def addition_rounds_nowhere(left: Cx, right: Cx) -> bool:
    """Whether the binary64 addition ``left + right`` would be exact.

    Both operands are assumed to be on the lattice -- which is what the callers
    decide first. The sum is exact exactly when the true sum is itself on the
    lattice.
    """
    return is_binary64(left.re + right.re) and is_binary64(left.im + right.im)


@dataclass(frozen=True)
class SummationVerdict:
    """The verdict of one sum in the declared order of ``eq:declorder``.

    ``total`` is the EXACT total, which is the sum of the declared numbers.
    Where ``rounds_nowhere`` is true it is also the computed binary64 total,
    and condition (S) is exactly the statement that makes those two the same
    object; where it is false the two may differ -- or may not, the 0.9/0.1
    case of the BB84 instance reaching a computed total of exactly ``1_A``
    through four inexact additions.
    """

    #: The exact total ``Sigma`` of ``eq:declorder``, of the DECLARED NUMBERS.
    total: Matrix
    #: The total the binary64 accumulation of ``eq:declorder`` produces, each
    #: partial sum rounded to the lattice. Condition (C) of ``def:exact`` is
    #: read on THIS, and (S) is what makes it the same object as ``total``:
    #: "(C) alone says that the COMPUTED sum is the identity, and NOT that
    #: sum_j a_j = 1 holds OF THE DECLARED NUMBERS." ``None`` when a part of an
    #: entry of the computed accumulation overflowed to a signed infinity
    #: (``foundations/def:binary64`` (ii)): the computed total is then no
    #: matrix over ``B_C``, equals no declared matrix, and (S) fails. Read it
    #: through :meth:`computed_total_equals`.
    computed_total: Matrix | None
    #: (S): every one of the ``|J|`` entrywise additions was exact.
    rounds_nowhere: bool
    #: 1-based index IN THE DECLARED ORDER of the first element whose addition
    #: was inexact, or ``None`` where (S) holds.
    first_inexact_index: int | None
    #: Every ``(1-based element index, flat entry index)`` at which an addition
    #: was inexact, in the order the accumulation meets them.
    inexact_sites: tuple[tuple[int, int], ...]
    #: The partial sums ``Sigma_1, ..., Sigma_{|J|}``, exactly.
    partial_sums: tuple[Matrix, ...]

    def computed_total_equals(self, expected: Matrix) -> bool:
        """Whether the computed total is ``expected``, entry for entry.

        False when the computed accumulation overflowed: a signed infinity
        equals no declared value.
        """
        return self.computed_total is not None and equal(self.computed_total, expected)


def sum_in_declared_order(terms: Sequence[Matrix]) -> SummationVerdict:
    """Accumulate ``terms`` left to right, entrywise, deciding (S) as it goes.

    ``eq:declorder``: ``Sigma_0 = 0``, ``Sigma_i = Sigma_{i-1} + a_{j_i}``,
    "formed left to right, entrywise, with no re-ordering and no
    re-association". The caller presents ``terms`` IN THE DECLARED ORDER; this
    function does not know what that order is and must not be given a set.

    The first addition is ``Sigma_0 + a_{j_1}`` with ``Sigma_0 = 0``, which is
    exact for any binary64 operand, so element 1 never appears among the
    inexact sites.

    THE COMPUTED ACCUMULATION IS ``foundations/def:declared-order``'S, WITH
    ITS ``fl``: each computed partial sum is ``fl`` of the previous one plus
    the next term (:func:`round_to_binary64`, part by part), so a part that
    reaches ``|x| >= 2^1024 - 2^970`` becomes a signed infinity and stays one
    (``fl(+-inf + y) = +-inf``). An addition is exact when the partial sum it
    starts from is finite and the true sum is a binary64 number; one that
    overflows is not, so the accumulation does not round nowhere, and the
    verdict says so rather than raising. The computed total is then ``None``.

    THIS IS THE ONE IMPLEMENTATION OF THE ROUNDS-NOWHERE DECISION IN THIS
    REPOSITORY, and :func:`sum_rounds_nowhere` is a READING of its verdict
    rather than a second accumulation: two implementations would answer the
    same question with two index conventions.
    """
    if not terms:
        raise HypothesisError(
            "a sum in the declared order is over a NON-EMPTY declared "
            "alphabet; the empty family has no Sigma_{|J|}"
        )
    rows = len(terms[0])
    cols = len(terms[0][0]) if rows else 0
    running = zeros(rows, cols)
    # The computed partial sum, part by part: a value of fl, so an element of
    # B as an exact rational or a signed infinity.
    computed: list[list[tuple[Binary64Value, Binary64Value]]] = [
        [(Fraction(0), Fraction(0)) for _ in range(cols)] for _ in range(rows)
    ]
    partials: list[Matrix] = []
    sites: list[tuple[int, int]] = []
    for position, term in enumerate(terms, start=1):
        _same_shape(running, term)
        for i in range(rows):
            for j in range(cols):
                re, im = computed[i][j]
                addend = term[i][j]
                if not (
                    isinstance(re, Fraction)
                    and isinstance(im, Fraction)
                    and is_binary64(re + addend.re)
                    and is_binary64(im + addend.im)
                ):
                    sites.append((position, i * cols + j))
                computed[i][j] = (
                    round_to_binary64(re + addend.re),
                    round_to_binary64(im + addend.im),
                )
        running = add(running, term)
        partials.append(running)
    first = sites[0][0] if sites else None
    return SummationVerdict(
        total=running,
        computed_total=_finite_matrix(computed),
        rounds_nowhere=not sites,
        first_inexact_index=first,
        inexact_sites=tuple(sites),
        partial_sums=tuple(partials),
    )


def _finite_matrix(
    parts: Sequence[Sequence[tuple[Binary64Value, Binary64Value]]],
) -> Matrix | None:
    """Return the matrix of finite parts, or ``None`` if any part is infinite."""
    out: list[tuple[Cx, ...]] = []
    for row in parts:
        entries: list[Cx] = []
        for re, im in row:
            if not (isinstance(re, Fraction) and isinstance(im, Fraction)):
                return None
            entries.append(Cx(re, im))
        out.append(tuple(entries))
    return tuple(out)


@dataclass(frozen=True)
class TraceVerdict:
    """The verdict of one trace accumulated over the row index.

    ``def:exact``: "the trace of a matrix is likewise accumulated over its row
    index in increasing order, which is the order of the emitted array" -- and
    it is "read as an IDENTITY OF REAL NUMBERS exactly as a completeness sum
    is", so (S) applies to it in the same words.
    """

    #: The exact trace.
    value: Cx
    #: Every one of the row additions forming it was exact.
    rounds_nowhere: bool
    #: 1-based row index of the first inexact addition, or ``None``.
    first_inexact_row: int | None
    #: The partial sums, one per row, in increasing row order.
    partial_sums: tuple[Cx, ...]


def trace_in_row_order(m: Matrix) -> TraceVerdict:
    """Accumulate ``tr m`` over the row index in increasing order.

    THE TRACE WRAPPER of the rounds-nowhere decision: the same
    question as :func:`sum_in_declared_order` asked of the diagonal, with the
    row index as the declared order.
    """
    if not is_square(m):
        raise HypothesisError("a trace is accumulated over a SQUARE array")
    running = ZERO
    partials: list[Cx] = []
    first: int | None = None
    for row in range(len(m)):
        if first is None and not addition_rounds_nowhere(running, m[row][row]):
            first = row + 1
        running = running + m[row][row]
        partials.append(running)
    return TraceVerdict(
        value=running,
        rounds_nowhere=first is None,
        first_inexact_row=first,
        partial_sums=tuple(partials),
    )


@dataclass(frozen=True, slots=True)
class RoundsNowhere:
    """The verdict of :func:`sum_rounds_nowhere`, with the first failure named."""

    #: Whether every entrywise binary64 addition of the accumulation is exact.
    ok: bool
    #: Index in the DECLARED ORDER of the element whose addition first left the
    #: binary64 lattice, or ``None`` when :attr:`ok`.
    first_inexact_index: int | None = None
    #: ``(row, column)`` of the entry that first left it, scanned row-major.
    first_inexact_entry: tuple[int, int] | None = None


def sum_rounds_nowhere(blocks: Sequence[Matrix]) -> RoundsNowhere:
    """Condition (e) of Definition ``def:exactadm``, decided exactly.

    "EVERY ENTRYWISE BINARY64 ADDITION OF THAT ACCUMULATION, TAKEN IN THE
    DECLARED SUMMATION ORDER, IS EXACT, so that the COMPUTED sum IS the sum of
    (d)" -- the order being the one the ``summation_order`` convention fixes.

    The partial sums are formed left to right, entrywise, with no re-ordering
    and no re-association, and each one is tested against the binary64 lattice.
    An addition of two binary64 numbers is exact exactly when its real result
    is itself binary64, so this decides the real question rather than a proxy.

    THE ACCUMULATION IS :func:`sum_in_declared_order`'S AND THIS
    FUNCTION IS A READING OF ITS VERDICT. A second implementation of the same
    decision under a second index convention is avoided; the richer record is
    the one kept, because the compiler's checks report the computed total and
    the partial sums beside the verdict. The answers agree entry for entry: a
    loop returning at the FIRST inexact addition agrees up to that point, the
    exact and the rounded accumulations being the same numbers.

    WHY IT IS A CONDITION AND NOT A REMARK ABOUT ONE, in the contract's own
    words, which it attributes to the consumer: "a vanishing completeness
    DEFECT says the computed sum is the identity and DOES NOT SAY that
    ``sum_v A_v = 1`` holds OF THE NUMBERS, which is why the condition is
    stated ON THE ADDITIONS". The counterexample is deliberately not
    reproduced here: "what this contract carries is the obligation rather than the
    argument for it".

    Lemma ``lem:latsum`` is why the condition is satisfiable rather than one
    that would refuse every family: under Eq. eq:latsumcond,
    ``kappa + ceil(log2 L) <= 53``, every partial sum of lattice values is
    itself binary64 and every addition is exact. The fail-closed table's lattice row
    decides that inequality, so a conforming declaration reaches this function
    already knowing the answer -- and it is decided anyway, because the row
    bounds the ALPHABET and this decides the ADDITIONS.

    Args:
        blocks: the family on ONE sector, IN THE DECLARED ORDER. The order is
            part of the datum: binary64 addition is commutative but not
            associative, so re-ordering asks a different question.
    """
    if not blocks:
        raise MalformedInputError(
            "condition (e) of def:exactadm is about the accumulation of a "
            "non-empty family; an empty one has no additions to decide"
        )
    verdict = sum_in_declared_order(blocks)
    if verdict.rounds_nowhere:
        return RoundsNowhere(True)
    position, flat = verdict.inexact_sites[0]
    cols = len(blocks[0][0]) if blocks[0] else 0
    # The two records differ ONLY in how they spell the same failure: this one
    # counts elements from zero and names the entry as (row, column), the
    # verdict counts from one and names it by its flat index.
    return RoundsNowhere(False, position - 1, divmod(flat, cols) if cols else (0, 0))


#: Binary64 has 53 significant bits, smallest positive value 2^-1074,
#: and largest finite value (2^53 - 1) * 2^971. The predicate also serves
#: general declared inputs, not only eq:latinv's bounded lattice values.
_SIGNIFICAND_BITS: Final[int] = 53


def is_binary64(value: Fraction) -> bool:
    """Whether an exact rational is exactly a binary64 number.

    Strip the numerator's trailing zero bits to write a nonzero dyadic as
    ``odd_significand * 2^exponent``. Its significand must fit in 53 bits,
    its least significant bit must be at least 2^-1074 (including the
    subnormal spacing), and its leading bit may not exceed 2^1023. These
    integer decisions also reject overflow without forming a float.
    """
    if value == 0:
        return True
    denominator = value.denominator
    if denominator & (denominator - 1) != 0:
        return False
    numerator = abs(value.numerator)
    trailing_zeros = (numerator & -numerator).bit_length() - 1
    significand_bits = numerator.bit_length() - trailing_zeros
    exponent = trailing_zeros - (denominator.bit_length() - 1)
    return (
        significand_bits <= _SIGNIFICAND_BITS
        and exponent >= -1074
        and exponent + significand_bits - 1 <= 1023
    )
