"""Exact decisions on declared dyadic blocks: the admission boundary, once.

WHERE THIS FILE LIVES
=====================
It sits in :mod:`certiqs_key.foundations` because the lattice snapping table
(``foundations/snap.py``) is its second consumer, and a second copy of a
security-relevant decision procedure is the thing this module exists to
prevent. Two facts about its place:

* **the substrate is not duplicated.** The file uses ``foundations/exact.py``'s
  :class:`~certiqs_key.foundations.exact.Cx` and
  :func:`~certiqs_key.foundations.exact.is_positive_semidefinite` and carries no
  ``Cx`` class or rational ``LDL^*`` of its own;
* **the file is not folded into** ``foundations/exact.py``. That module is the
  exact substrate over :class:`~certiqs_key.foundations.exact.Cx` tuples; this
  one is the **admission boundary** over binary64 numpy arrays, and it is where
  a declared array becomes an exact decision. Two files over one substrate is
  the smaller change, and the input types say which is which at every call site.

WHY THE MODULE EXISTS AT ALL
============================
spec/architecture.md 2.8 and 2.9. This engine emits a key length only for
declared data that is EXACTLY admissible -- Hermitian and positive semidefinite
per sector block, complete per sector, with the declared-order completeness sum
rounding nowhere in binary64 (``def:declaration``, the exact-admissibility
paragraph and ``eq:declorder``) -- and ``prop:optol-nobound`` is why: no
consumer-side tolerance converts into a bound on the key, at any scale a
key-length claim could use. So the admission of declared operator data is not a
measurement compared against a window; it is A DECISION, and it is taken
exactly.

This module is the one implementation of that decision in this engine. It is
the second region of the exact island (spec/architecture.md 2.8): exact
arithmetic on sector blocks of dimension in the single digits costs
microseconds, which is what makes deciding rather than measuring affordable.

THE THREE RULES OF THIS MODULE
==============================
1. **Nothing here takes a tolerance.** There is no window, no ``tau``, no
   ``atol``. A predicate is true or it is false.
2. **Nothing here mutates its input.** Arrays are read and converted; the
   caller's array is untouched.
3. **A non-finite entry is refused, not converted.** ``Fraction(nan)`` raises
   anyway, but it raises the wrong thing; :class:`NonFiniteEntryError` says
   what happened and is catchable as a :class:`ValueError`.

The conversion itself is exact and needs no argument: ``Fraction(x)`` for a
finite ``float`` ``x`` is the rational that ``x`` **is**, not an approximation
of one, because a binary64 number is a dyadic rational. Nothing is rounded on
the way in, so nothing decided here is decided about a different matrix than
the one the caller holds.

THE TWO THINGS IT DOES NOT DECIDE FOR ITSELF
============================================
THE ROUNDS-NOWHERE CONDITION. :func:`sum_rounds_nowhere` is a READING of
:func:`certiqs_key.foundations.exact.sum_in_declared_order` and not a second
accumulation: that decision has ONE implementation in this repository and it is
``foundations/exact.py``'s. See that function for the argument that the two verdicts
agree and for where the two index conventions are reconciled.

POSITIVE SEMIDEFINITENESS. :func:`is_psd_exact` decides Hermiticity here -- so
that the refusal a caller catches is this module's
:class:`NotHermitianError` -- and then hands the exact matrix to
:func:`certiqs_key.foundations.exact.is_positive_semidefinite`, the one rational
``LDL^*`` with the zero-pivot rule in this repository.

WHAT :mod:`certiqs_key.foundations.numeric` IS FOR, NOW THAT THIS EXISTS
==================================================================
Both. They are not competitors and neither replaces the other:

* :mod:`~certiqs_key.foundations.numeric` **measures**, in binary64, and returns a
  number. That number is what an INSTANCE records as the pre-snap defect of
  what it declares, and what the instance's declared tolerance is the ceiling
  on (spec/architecture.md 2.9). It is the honest report of how far the device
  characterization was from the lattice.
* This module **decides**, exactly, whether the snapped result is admissible.
  THIS MODULE RECEIVES NO TOLERANCE AT ALL (spec/architecture.md 2.8: "Modules
  receive no tolerance to reason with"), and a decision at exactly zero needs
  no number to compare.

A worked case is in the tests: the family ``(1, 2^-60, 2^-60)``.
:func:`~certiqs_key.foundations.numeric.completeness_residue` measures its
completeness defect as ``0.0`` -- correctly, because the binary64 sum in the
declared order *is* the identity -- while
:func:`completeness_residue_squared_exact` reports ``(2^-59)^2``, because the
real sum is ``1 + 2^-59``. That gap is the entire subject of the round-nowhere
condition, and the two functions are both right about different questions.

THE MODULUS PROBLEM, AND HOW IT IS RESOLVED HERE
================================================
The platform's measuring vocabulary asks for a ``hermiticity_defect_exact(a)``
returning the exact entrywise maximum modulus of ``a - a^dag`` (a
``Fraction``; zero iff exactly Hermitian). **That number is not always a
Fraction.** The modulus of a
Gaussian rational ``x + iy`` is ``sqrt(x^2 + y^2)``, which is irrational for
most Gaussian rationals -- and ``a - a^dag`` is anti-Hermitian, not real, so
genuinely complex defect entries are the normal case rather than a corner one:
``a = [[0, 1+i], [0, 0]]`` has defect entry ``1+i`` of modulus ``sqrt(2)``.

Two shortcuts were available and both are rejected:

* reporting ``max(|x|, |y|)`` in place of the modulus. It is rational, it
  agrees with the modulus on real and on purely imaginary entries, and it is
  **wrong** -- it understates the modulus by up to ``sqrt(2)``, and a number
  that is only sometimes the quantity it is named after is worse than no
  number, because a reader cannot tell which case is in front of them;
* returning a rounded ``Fraction``. Rounding is exactly what this module exists
  not to do.

The resolution, which is what a caller should read the API against:

* :func:`is_hermitian_exact` is **the decision**, and it is total. Every
  consumer's admission rule is a decision, so this is the function the four
  admission rows of spec/architecture.md 2.9 actually need.
* :func:`hermiticity_defect_squared_exact` is **the total measurement**: the
  exact entrywise maximum of ``x^2 + y^2``, always a ``Fraction``, and zero
  exactly when the matrix is Hermitian. Comparisons of defects and the
  identification of the worst entry are done on squared moduli, where they are
  exact, and the ordering by squared modulus is the ordering by modulus.
* :func:`hermiticity_defect_exact` keeps the name and the "zero iff
  Hermitian" guarantee, returns the exact modulus **when that number is
  rational**, and raises :class:`IrrationalDefectError` when it is not, naming
  the squared function in the message. It never returns a number that is not
  the defect.

:func:`completeness_residue_exact` and :func:`completeness_residue_squared_exact`
stand in exactly the same relation, for the same reason, with
:func:`is_complete_exact` as the decision. :func:`trace_residue_exact` and
:func:`column_residue_exact` need no such pairing: both are defined on
quantities the format requires to be real, and this module refuses a complex
one rather than dropping its imaginary part.

WHAT IS NOT DECIDED HERE
========================
**The sector map.** The admission has five conditions and the first is the
SECTOR-MAP COMPARISON: the producer's block kind, block identifiers and their
ordering against the consumer's own (spec/architecture.md 2.9). That is a type
condition on metadata, decided and never measured, and it is the caller's --
this module never sees a block identifier.
:func:`certiqs_key.meat_core.declaration.admission.check_sector_map` is where
it is decided; :func:`admit_family_exact` runs the other four and says so.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from fractions import Fraction
from typing import Any

import numpy as np
import numpy.typing as npt

from certiqs_key.foundations.exact import (
    ONE,
    ZERO,
    Cx,
    is_binary64,
    is_hermitian,
    is_positive_semidefinite,
    sum_in_declared_order,
)
from certiqs_key.foundations.exact import Matrix as ExactMatrix

__all__ = [
    "ExactAdmission",
    "ExactInputError",
    "ExactMatrix",
    "IrrationalDefectError",
    "Matrix",
    "NonFiniteEntryError",
    "NotHermitianError",
    "RoundsNowhereResult",
    "ScalarPart",
    "admit_family_exact",
    "column_residue_exact",
    "completeness_residue_exact",
    "completeness_residue_squared_exact",
    "hermiticity_defect_exact",
    "hermiticity_defect_squared_exact",
    "is_complete_exact",
    "is_hermitian_exact",
    "is_psd_exact",
    "sum_rounds_nowhere",
    "to_exact",
    "trace_residue_exact",
]

#: A real or complex binary64 array, as this module reads one. Identical to
#: :data:`certiqs_key.foundations.numeric.Matrix` and deliberately so: the two modules
#: read the same declared data, one to measure it and one to decide it.
Matrix = npt.NDArray[Any]


# ---------------------------------------------------------------------------
#  Refusals
# ---------------------------------------------------------------------------


class ExactInputError(ValueError):
    """An argument this module cannot decide anything about.

    A :class:`ValueError` subclass, because every case is a bad argument value
    and a caller that already catches ``ValueError`` around the measuring
    kernel keeps working. Never raised to report that a predicate is false: a
    predicate that is false is reported by returning ``False``.
    """


class NonFiniteEntryError(ExactInputError):
    """An array carries a NaN or an infinity, so it has no exact conversion.

    Refused rather than converted, for the same fail-closed reason the
    measuring kernel refuses it: a non-finite entry compares ``False`` against
    every threshold, so a NaN admitted here would pass a decision it never met.
    """


class NotHermitianError(ExactInputError):
    """A positivity question was asked about a non-Hermitian operator.

    Positive semidefiniteness is a property of a Hermitian operator. Returning
    ``False`` would report a failed test where no test was run, so this raises;
    a caller decides Hermiticity first, with :func:`is_hermitian_exact`.
    """


class IrrationalDefectError(ExactInputError):
    """The exact defect is a real number that is not rational.

    See "THE MODULUS PROBLEM" in the module docstring. The squared defect is
    always rational and always exact; the function named in the message returns
    it.
    """


# ---------------------------------------------------------------------------
#  The substrate: ``foundations/exact.py``'s, not a second one
# ---------------------------------------------------------------------------
#
#  :class:`~certiqs_key.foundations.exact.Cx`, :data:`ZERO`, :data:`ONE` and the
#  exact matrix type are imported above. This module carries no copy of all
#  four and no second rational ``LDL^*``, because two implementations of one
#  security-relevant decision are exactly what a shared kernel exists to
#  prevent. What is here is the part that
#  is genuinely this module's: the conversion of DECLARED BINARY64 ARRAYS into
#  that substrate, and the four admission decisions taken on the result.

#  ``ExactMatrix`` is this module's spelling of
#  :data:`certiqs_key.foundations.exact.Matrix`, aliased on import and kept under
#  that name because ``Matrix`` here is the BINARY64 ARRAY a caller declares.
#  The two must not be confused: one is what is declared, the other is what the
#  decision is taken on.


class ScalarPart(StrEnum):
    """Which half of a Gaussian rational a report is about."""

    REAL = "real"
    IMAGINARY = "imaginary"


# ---------------------------------------------------------------------------
#  Conversion in
# ---------------------------------------------------------------------------
#
#  THE BINARY64 LATTICE TEST IS NOT HERE EITHER. This module carried an
#  ``is_binary64`` of its own, deciding ``x == Fraction(float(x))``;
#  :func:`certiqs_key.foundations.exact.is_binary64` decides the same predicate on
#  the integers, without forming a float at all, and is the one implementation
#  the repository keeps. It is imported above for
#  :func:`sum_rounds_nowhere`'s reading of which half of an entry left the
#  lattice.


def to_exact(a: Matrix) -> ExactMatrix:
    """Return the exact Gaussian-rational matrix of a binary64 array.

    Nothing is rounded: a finite binary64 number is a dyadic rational and
    ``Fraction`` of it is that rational exactly, so the returned matrix **is**
    the argument rather than an approximation of it.

    Args:
        a: a 2-D real or complex binary64 array. Rectangular shapes are
            admitted -- :func:`column_residue_exact` reads a coarse-graining
            matrix that need not be square -- and the functions that require a
            square argument say so themselves.

    Raises:
        NonFiniteEntryError: if any entry is NaN or infinite.
        ExactInputError: if ``a`` is not a 2-D floating-point array, or has a
            zero-length axis.
    """
    array = np.asarray(a)
    if array.ndim != 2:
        raise ExactInputError(
            f"an exact matrix is read from a 2-D array; this one has "
            f"{array.ndim} dimensions"
        )
    if array.dtype.kind not in "fc":
        raise ExactInputError(
            f"dtype {array.dtype!s} is not binary64; declared data is real or "
            "complex floating point (spec/architecture.md 2.8)"
        )
    if 0 in array.shape:
        raise ExactInputError(
            f"shape {tuple(array.shape)} has a zero-length axis; a "
            "zero-dimensional operator is not expressible in this format"
        )
    if not bool(np.all(np.isfinite(array))):
        raise NonFiniteEntryError(
            "the array carries a non-finite entry; a NaN has no exact rational "
            "and compares False against every decision it would be put to"
        )
    real: Any = np.real(array).astype(np.float64, copy=False).tolist()
    imag: Any = np.imag(array).astype(np.float64, copy=False).tolist()
    return tuple(
        tuple(Cx(Fraction(re), Fraction(im)) for re, im in zip(row, irow, strict=True))
        for row, irow in zip(real, imag, strict=True)
    )


# ---------------------------------------------------------------------------
#  Internal helpers on the exact form
# ---------------------------------------------------------------------------

def _square(m: ExactMatrix, name: str) -> ExactMatrix:
    """Return ``m``, or raise if it is not square."""
    if len(m) != len(m[0]):
        raise ExactInputError(
            f"{name} has shape {(len(m), len(m[0]))}; this decision is defined "
            "on a square matrix"
        )
    return m


def _adjoint(m: ExactMatrix) -> ExactMatrix:
    """Return ``m^dagger``."""
    return tuple(
        tuple(m[j][i].conjugate() for j in range(len(m))) for i in range(len(m[0]))
    )


def _max_squared_modulus(m: ExactMatrix) -> Fraction:
    """Return the largest ``|entry|^2`` over the whole matrix.

    The entrywise maximum modulus is the square root of this. Comparing squared
    moduli orders the entries exactly as comparing moduli does, both being
    non-negative, so the worst entry is identified here without ever forming an
    irrational number.
    """
    return max(entry.squared_modulus for row in m for entry in row)


def _rational_sqrt(value: Fraction) -> Fraction | None:
    """Return the exact square root of a non-negative rational, or ``None``.

    A rational in lowest terms has a rational square root exactly when its
    numerator and its denominator are both perfect squares, the two being
    coprime.
    """
    if value < 0:
        return None
    root_num = math.isqrt(value.numerator)
    root_den = math.isqrt(value.denominator)
    if root_num * root_num != value.numerator:
        return None
    if root_den * root_den != value.denominator:
        return None
    return Fraction(root_num, root_den)


def _exact_modulus(squared: Fraction, what: str, squared_function: str) -> Fraction:
    """Return the exact modulus from its square, or refuse to approximate it."""
    root = _rational_sqrt(squared)
    if root is None:
        raise IrrationalDefectError(
            f"the exact {what} is sqrt({squared}), which is irrational and is "
            f"therefore not a Fraction; call {squared_function} for the exact "
            "squared defect, or the matching is_* function for the decision "
            "(see 'THE MODULUS PROBLEM' in certiqs_key.foundations.exact_admission)"
        )
    return root


def _family(blocks: Sequence[Matrix], name: str) -> list[ExactMatrix]:
    """Convert a family of same-shaped blocks exactly, or raise.

    Args:
        blocks: the family ``{F_v}_v`` **on one sector**, in the declared
            order. spec/architecture.md 2.9 names this argument ``blocks`` and
            this module
            keeps the ADR's name so that the three contracts citing it read
            against the signature; the objects are the outcome-indexed elements
            of one sector's family, which is what eq:declorder sums.
        name: the function name, for the refusal message.
    """
    if not blocks:
        raise ExactInputError(
            f"{name} was given an empty family; a sum over no elements has no "
            "subject and its residue would be a vacuous 0 no caller could tell "
            "from a decided one"
        )
    exact = [to_exact(block) for block in blocks]
    shapes = {(len(block), len(block[0])) for block in exact}
    if len(shapes) != 1:
        raise ExactInputError(
            f"{name} was given elements of shapes {sorted(shapes)}; a family on "
            "one sector has one shape"
        )
    return exact


def _sum_exact(family: Sequence[ExactMatrix]) -> ExactMatrix:
    """Return the exact entrywise sum of a same-shaped family.

    Exact addition is associative, so the declared order does not change this
    number. Whether the *binary64* sum in the declared order equals it is a
    separate question and is :func:`sum_rounds_nowhere`.
    """
    rows = len(family[0])
    cols = len(family[0][0])
    return tuple(
        tuple(_add_all(block[i][j] for block in family) for j in range(cols))
        for i in range(rows)
    )


def _add_all(terms: Any) -> Cx:
    """Return the exact sum of an iterable of :class:`Cx`."""
    total = ZERO
    for term in terms:
        total = total + term
    return total


def _minus_identity(m: ExactMatrix) -> ExactMatrix:
    """Return ``m - 1`` for a square ``m``."""
    n = len(m)
    return tuple(
        tuple(m[i][j] - ONE if i == j else m[i][j] for j in range(n)) for i in range(n)
    )


def _minus_scaled_identity(m: ExactMatrix, constant: Fraction) -> ExactMatrix:
    """Return ``m - c 1`` for a square ``m`` and a rational ``c``."""
    n = len(m)
    shift = Cx(constant, Fraction(0))
    return tuple(
        tuple(m[i][j] - shift if i == j else m[i][j] for j in range(n))
        for i in range(n)
    )


# ---------------------------------------------------------------------------
#  Hermiticity
# ---------------------------------------------------------------------------


def is_hermitian_exact(a: Matrix) -> bool:
    """Whether ``a`` is exactly Hermitian (spec/architecture.md 2.9).

    **The decision**, and the one a consumer's admission rule is written in.
    Total: it never raises for a well-formed square binary64 matrix, and it
    never has to name a modulus.

    Raises:
        NonFiniteEntryError: if any entry is NaN or infinite.
        ExactInputError: if ``a`` is not a square 2-D binary64 array.
    """
    return is_hermitian(_square(to_exact(a), "a"))


def hermiticity_defect_squared_exact(a: Matrix) -> Fraction:
    """Return the exact entrywise maximum of ``|(a - a^dag)_ij|^2``.

    Always a ``Fraction``, always exact, and zero exactly when ``a`` is
    Hermitian. This is the total measurement; see "THE MODULUS PROBLEM" in the
    module docstring for why the unsquared one is not.

    Raises:
        NonFiniteEntryError: if any entry is NaN or infinite.
        ExactInputError: if ``a`` is not a square 2-D binary64 array.
    """
    m = _square(to_exact(a), "a")
    adjoint = _adjoint(m)
    n = len(m)
    difference = tuple(
        tuple(m[i][j] - adjoint[i][j] for j in range(n)) for i in range(n)
    )
    return _max_squared_modulus(difference)


def hermiticity_defect_exact(a: Matrix) -> Fraction:
    """Return the exact entrywise maximum modulus of ``a - a^dag`` (2.9).

    Zero exactly when ``a`` is Hermitian, which is the guarantee the ADR states
    and the only property its admission rule uses.

    Raises:
        IrrationalDefectError: if the defect is irrational, which is the normal
            case for a genuinely complex defect entry -- ``a - a^dag`` is
            anti-Hermitian, so its off-diagonal entries are unconstrained
            Gaussian rationals. Call :func:`hermiticity_defect_squared_exact`
            for the exact squared defect, or :func:`is_hermitian_exact` for the
            decision. This function will not return a rounded number.
        NonFiniteEntryError: if any entry is NaN or infinite.
        ExactInputError: if ``a`` is not a square 2-D binary64 array.
    """
    return _exact_modulus(
        hermiticity_defect_squared_exact(a),
        "Hermiticity defect",
        "hermiticity_defect_squared_exact",
    )


# ---------------------------------------------------------------------------
#  Positivity
# ---------------------------------------------------------------------------


def is_psd_exact(a: Matrix) -> bool:
    """Whether the exactly Hermitian ``a`` is positive semidefinite (2.9).

    Decided **exactly**, by symmetric Gaussian elimination -- a rational
    ``LDL^*`` -- with the zero-pivot rule: at each step the pivot must be
    non-negative; a zero pivot forces the whole remaining row and column to
    vanish, by Cauchy-Schwarz (``|m_kj|^2 <= m_kk m_jj = 0``). The pivot stays
    real because Hermiticity is preserved by the Schur update. The cost is
    cubic in the block dimension.

    THE ELIMINATION IS
    :func:`certiqs_key.foundations.exact.is_positive_semidefinite` and is not
    repeated here (no second copy of the same loop is carried). What this
    function adds is the conversion in and the Hermiticity refusal in **this**
    module's vocabulary: ``foundations.exact`` raises its own
    :class:`~certiqs_key.foundations.errors.HypothesisError` for a
    non-Hermitian argument, and a consumer of the admission boundary catches
    :class:`NotHermitianError`, so the hypothesis is decided here first and the
    elimination is only ever called on an operator that has it.

    No eigenvalue is computed and no threshold appears, which is the point. A
    **singular** operator is accepted -- every rank-one projector is one, and
    ``vv^dag`` for a dyadic ``v`` is exactly one, while
    :func:`numpy.linalg.eigvalsh` returns a slightly negative smallest
    eigenvalue for it. An operator with a genuinely negative eigenvalue is
    refused, however small: a computed minimum eigenvalue of
    ``-2.2e-16`` occurs at every ``N = 1`` point of the fig. 1 grid, and under a
    tolerance window that number decides nothing, while here it decides
    everything.

    Raises:
        NotHermitianError: if ``a`` is not exactly Hermitian. Positivity is a
            property of a Hermitian operator; ``False`` would report a failed
            test where none was run.
        NonFiniteEntryError: if any entry is NaN or infinite.
        ExactInputError: if ``a`` is not a square 2-D binary64 array.
    """
    return _is_psd(_square(to_exact(a), "a"))


def _is_psd(m: ExactMatrix) -> bool:
    """Decide positive semidefiniteness of an exact matrix, refusing first."""
    if not is_hermitian(m):
        raise NotHermitianError(
            "positive semidefiniteness is a property of a Hermitian operator; "
            "decide Hermiticity first, with is_hermitian_exact"
        )
    return is_positive_semidefinite(m)


# ---------------------------------------------------------------------------
#  Completeness
# ---------------------------------------------------------------------------


def is_complete_exact(blocks: Sequence[Matrix]) -> bool:
    """Whether ``sum_v F_v`` is exactly the identity on one sector (2.9).

    **The decision.** The sum is the exact one, so this says of the *numbers*
    what ``meat-core``'s ``dfC = 0`` is read as saying and, without condition
    (S), does not say (see :func:`sum_rounds_nowhere`).

    Args:
        blocks: the family ``{F_v}_v`` on one sector, in the declared order.

    Raises:
        NonFiniteEntryError: if any entry is NaN or infinite.
        ExactInputError: if the family is empty, ragged, or not square.
    """
    return completeness_residue_squared_exact(blocks) == 0


def completeness_residue_squared_exact(blocks: Sequence[Matrix]) -> Fraction:
    """Return the exact entrywise maximum of ``|(sum_v F_v - 1)_ij|^2``.

    Always a ``Fraction``, always exact, and zero exactly when the family is
    complete. The total measurement; :func:`completeness_residue_exact` is the
    ADR's name for its square root and is partial for the reason set out under
    "THE MODULUS PROBLEM".

    Args:
        blocks: the family ``{F_v}_v`` on one sector, in the declared order.

    Raises:
        NonFiniteEntryError: if any entry is NaN or infinite.
        ExactInputError: if the family is empty, ragged, or not square.
    """
    family = _family(blocks, "completeness_residue_squared_exact")
    _square(family[0], "blocks[0]")
    return _max_squared_modulus(_minus_identity(_sum_exact(family)))


def completeness_residue_exact(blocks: Sequence[Matrix]) -> Fraction:
    """Return the exact entrywise maximum modulus of ``sum_v F_v - 1`` (2.9).

    Zero exactly when the family is complete on the sector.

    Args:
        blocks: the family ``{F_v}_v`` on one sector, in the declared order.

    Raises:
        IrrationalDefectError: if the residue is irrational. Call
            :func:`completeness_residue_squared_exact` for the exact squared
            residue, or :func:`is_complete_exact` for the decision.
        NonFiniteEntryError: if any entry is NaN or infinite.
        ExactInputError: if the family is empty, ragged, or not square.
    """
    return _exact_modulus(
        completeness_residue_squared_exact(blocks),
        "completeness residue",
        "completeness_residue_squared_exact",
    )


# ---------------------------------------------------------------------------
#  Trace and column sums -- real by the format, so exact and total
# ---------------------------------------------------------------------------


def trace_residue_exact(a: Matrix) -> Fraction:
    """Return the exact ``|tr a - 1|`` (spec/architecture.md 2.9).

    Zero exactly when ``a`` has unit trace -- the normalisation half of a
    declared state.

    Raises:
        ExactInputError: if the trace has a non-zero imaginary part. A declared
            state has a real trace; dropping the imaginary part would narrow
            the claim silently, so this refuses instead. Also raised if ``a``
            is not a square 2-D binary64 array.
        NonFiniteEntryError: if any entry is NaN or infinite.
    """
    m = _square(to_exact(a), "a")
    total = _add_all(m[i][i] for i in range(len(m)))
    if not total.is_real:
        raise ExactInputError(
            f"the trace is {total}, which is not real; a declared state's trace "
            "is a real number and this module does not drop an imaginary part"
        )
    return abs(total.re - 1)


def column_residue_exact(m: Matrix) -> Fraction:
    """Return the exact largest ``|sum_r m[r, c] - 1|`` over columns (2.9).

    Zero exactly when every column sums to one -- the column-stochasticity half
    of a declared channel matrix. The rectangular case is admitted: a
    coarse-graining matrix maps one alphabet into another and need not be
    square.

    Raises:
        ExactInputError: if any entry has a non-zero imaginary part. A
            stochastic matrix is real, and refusing is the fail-closed reading;
            also raised if ``m`` is not a 2-D binary64 array.
        NonFiniteEntryError: if any entry is NaN or infinite.
    """
    exact = to_exact(m)
    if any(not entry.is_real for row in exact for entry in row):
        raise ExactInputError(
            "a column-stochastic matrix is real; this one has a complex entry "
            "and this module does not drop an imaginary part"
        )
    rows = len(exact)
    cols = len(exact[0])
    return max(
        abs(sum((exact[r][c].re for r in range(rows)), Fraction(0)) - 1)
        for c in range(cols)
    )


# ---------------------------------------------------------------------------
#  Condition (S): the declared-order sum rounds nowhere
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RoundsNowhereResult:
    """The verdict of :func:`sum_rounds_nowhere`, with the first failure named."""

    #: Whether every one of the ``|V|`` entrywise binary64 additions is exact.
    ok: bool
    #: Index in the declared order of the element whose addition first rounded,
    #: or ``None`` when :attr:`ok`. Zero-based, so ``1`` names the second
    #: element -- the first addition, onto the zero matrix, is always exact.
    first_inexact_index: int | None
    #: ``(row, column)`` of the entry that first rounded, scanned row-major
    #: within the offending addition so that the report is deterministic.
    first_inexact_entry: tuple[int, int] | None
    #: Which half of that entry left the lattice.
    first_inexact_part: ScalarPart | None

    def as_record(self) -> dict[str, object]:
        """Return the JSON-ready form a run record or a refusal reason carries."""
        return {
            "ok": self.ok,
            "first_inexact_index": self.first_inexact_index,
            "first_inexact_entry": (
                list(self.first_inexact_entry)
                if self.first_inexact_entry is not None
                else None
            ),
            "first_inexact_part": (
                str(self.first_inexact_part)
                if self.first_inexact_part is not None
                else None
            ),
        }


def sum_rounds_nowhere(blocks: Sequence[Matrix]) -> RoundsNowhereResult:
    """Whether the declared-order completeness sum is exact in binary64.

    ``eq:declorder`` forms the completeness sum left to right, entrywise, with
    no re-ordering and no re-association::

        S_0 = 0,   S_i = S_{i-1} + F_{v_i}   (1 <= i <= |V|)

    and asks that **every one of those additions be exact**.

    THIS IS A READING OF :func:`certiqs_key.foundations.exact.sum_in_declared_order`
    AND NOT A SECOND ACCUMULATION. The rounds-nowhere decision has ONE
    implementation in this repository, in ``foundations``, and that is a rule
    rather than a preference: two, one per package, answering the same question
    under two index conventions, could disagree. This function converts the
    declared binary64 blocks into that module's exact form -- LOSSLESSLY, a
    finite binary64 number being a dyadic rational -- calls it, and translates
    its verdict into the record the engine's refusals and its frozen registry
    are written against.

    THE TWO READINGS AGREE. A loop carrying the EXACT partial sum and returning
    at the FIRST inexact addition and ``sum_in_declared_order``, which carries
    the ROUNDED partial and collects every site, name the same site. Up to the
    first inexact addition the exact and the rounded accumulations are the same
    numbers, so the first site is the same element, the same entry and the same
    half. Within one element both scan the entries row-major, so the tie is
    broken the same way.

    THE TWO INDEX CONVENTIONS ARE RECONCILED HERE AND NOWHERE ELSE. The
    verdict counts elements from one; this record counts from zero and names
    the entry as ``(row, column)`` rather than by a flat index.

    WHICH HALF LEFT THE LATTICE is decided here and is not on the verdict:
    ``sum_in_declared_order`` records THAT an addition was inexact, and the
    engine's refusal names the part. It is read off the verdict's own exact
    partial sum at the named site, which at the FIRST inexact addition is the
    number such a loop would hold -- so this is one more reading of the
    same verdict and not a second decision.

    **Why the condition is not implied by exact completeness.** A vanishing
    completeness defect says the *computed* sum is the identity. The
    counterexample is one sector of dimension one carrying
    ``(1, 2^-60, 2^-60)``: every entry is representable and non-negative, and
    ``2^-60`` is below half an ulp of ``1``, so each addition returns its left
    operand, the computed sum is ``1``, and the family is admissible at every
    tolerance including zero -- while the real sum is ``1 + 2^-59``, the
    measurement is not an isometry and the key length is not defined for the
    declared numbers. Nothing recovers it from smallness. This function is what
    closes that window; the tests carry the counterexample.

    Args:
        blocks: the family ``{F_v}_v`` on one sector, **in the declared order**.
            The order is part of the datum: binary64 addition is commutative
            but not associative, so re-ordering the argument asks a different
            question.

    Returns:
        A :class:`RoundsNowhereResult` naming the FIRST offending element and
        not merely an offending one.

    Raises:
        NonFiniteEntryError: if any entry is NaN or infinite.
        ExactInputError: if the family is empty or ragged.
    """
    family = _family(blocks, "sum_rounds_nowhere")
    cols = len(family[0][0])
    verdict = sum_in_declared_order(family)
    if verdict.rounds_nowhere:
        return RoundsNowhereResult(True, None, None, None)
    position, flat = verdict.inexact_sites[0]
    row, column = divmod(flat, cols)
    entry = verdict.partial_sums[position - 1][row][column]
    part = (
        ScalarPart.REAL
        if not is_binary64(entry.re)
        else ScalarPart.IMAGINARY
    )
    return RoundsNowhereResult(False, position - 1, (row, column), part)


# ---------------------------------------------------------------------------
#  The consumer's admission of one sector's family
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ExactAdmission:
    """What :func:`admit_family_exact` decided, and which condition failed.

    Four of the five conditions of spec/architecture.md 2.9. The fifth -- condition (T),
    the sector map -- is metadata and is the caller's; nothing in this
    dataclass says anything about it, and :attr:`admissible` therefore means
    "admissible **given** an agreeing sector map".
    """

    #: Whether every element is exactly Hermitian.
    hermitian: bool
    #: Indices, in the declared order, of the elements that are not.
    non_hermitian: tuple[int, ...]
    #: Whether every element that is exactly Hermitian is exactly PSD.
    #: Positivity is not decided for a non-Hermitian element -- the question
    #: has no truth value there -- and such an element is already recorded in
    #: :attr:`non_hermitian`, so the family is refused either way.
    positive_semidefinite: bool
    #: Indices, in the declared order, of the Hermitian elements that are not
    #: positive semidefinite.
    indefinite: tuple[int, ...]
    #: Whether the exact sum is exactly ``c`` times the identity, ``c`` being
    #: :attr:`constant`.
    complete: bool
    #: The exact squared completeness residue against ``c 1``; zero iff
    #: :attr:`complete`.
    completeness_residue_squared: Fraction
    #: Condition (S), with its first failure named.
    rounds_nowhere: RoundsNowhereResult
    #: The declared constant ``c`` of condition (C), ``sum_j a_j = c 1``
    #: (``foundations/def:exact-admissibility``); ``1`` for a measurement.
    constant: Fraction = Fraction(1)

    @property
    def admissible(self) -> bool:
        """Whether all four decided conditions hold."""
        return (
            self.hermitian
            and self.positive_semidefinite
            and self.complete
            and self.rounds_nowhere.ok
        )

    @property
    def failures(self) -> tuple[str, ...]:
        """The machine-readable names of the conditions that failed, in order."""
        names = []
        if not self.hermitian:
            names.append("hermiticity")
        if not self.positive_semidefinite:
            names.append("positivity")
        if not self.complete:
            names.append("completeness")
        if not self.rounds_nowhere.ok:
            names.append("declared_order_sum")
        return tuple(names)

    def as_record(self) -> dict[str, object]:
        """Return the JSON-ready form a run record or a refusal reason carries.

        The residue is rendered as a string: it is an exact rational, and
        emitting it as a float would put back the rounding this module exists
        to keep out of the record.
        """
        return {
            "admissible": self.admissible,
            "failures": list(self.failures),
            "hermitian": self.hermitian,
            "non_hermitian": list(self.non_hermitian),
            "positive_semidefinite": self.positive_semidefinite,
            "indefinite": list(self.indefinite),
            "complete": self.complete,
            "completeness_residue_squared": str(self.completeness_residue_squared),
            "rounds_nowhere": self.rounds_nowhere.as_record(),
            "constant": str(self.constant),
        }


def admit_family_exact(
    blocks: Sequence[Matrix], *, constant: Fraction = Fraction(1)
) -> ExactAdmission:
    """Decide (H), (P), (C), (S) of ``def:exact-admissibility`` on one sector.

    The definition's five conditions are (T) the sector map, (H)
    Hermiticity, (P) positivity, (C) completeness with the declared constant
    ``c``, ``sum_j a_j^(s) = c 1_{d_s}`` as an identity of the declared
    numbers, and (S) that the sum in the declared order rounds nowhere. This
    decides the last four on the family of ONE block ``s``, with ``c`` the
    ``constant`` argument (``1``, a measurement, by default).

    (T) IS NOT DECIDED HERE, AND WHERE IT IS. This function receives arrays
    and no sector map. (T) is the agreement of two maps in block kind,
    identifiers, order and dimensions,
    :meth:`certiqs_key.foundations.blocks.SectorStructure.disagreement` (the
    comparison of ``def:sector-map``), which the compiler reads on its typed
    block lists, where :class:`~certiqs_key.foundations.blocks.BlockOperator`
    carries the dimension clause by type (the definition's lead-in allows
    that); ``meat-core`` compares kind, identifiers and order in
    :func:`certiqs_key.meat_core.declaration.admission.check_sector_map` and
    the block dimensions at the bundle boundary
    (:mod:`certiqs_key.domain.validation`). Within one call the blocks are
    all square of one size, which is refused otherwise.

    Nothing is refused here: the result **reports**, and the caller raises its
    own module's refusal with its own machine-readable reason. That is the same
    separation :mod:`certiqs_key.foundations.numeric` draws between measuring and
    deciding, one rung further along -- here the deciding is done and only the
    refusing is left.

    Args:
        blocks: the family ``{F_v}_v`` on **one sector**, in the declared
            order. A caller with several sectors calls this once per sector and
            names the sector in its own refusal.
        constant: the declared constant ``c`` of (C), a declared value
            (a binary64 number) read as the rational it is.

    Raises:
        NonFiniteEntryError: if any entry is NaN or infinite.
        ExactInputError: if the family is empty, ragged, or not square, or if
            ``constant`` is not a binary64 number.
    """
    if not is_binary64(constant):
        raise ExactInputError(
            f"the completeness constant {constant!r} is not a declared value; "
            "foundations/def:exact-admissibility reads c as a binary64 number"
        )
    family = _family(blocks, "admit_family_exact")
    _square(family[0], "blocks[0]")

    non_hermitian: list[int] = []
    indefinite: list[int] = []
    for index, element in enumerate(family):
        if not is_hermitian(element):
            non_hermitian.append(index)
        elif not _is_psd(element):
            indefinite.append(index)

    residue_squared = _max_squared_modulus(
        _minus_scaled_identity(_sum_exact(family), constant)
    )
    return ExactAdmission(
        hermitian=not non_hermitian,
        non_hermitian=tuple(non_hermitian),
        positive_semidefinite=not indefinite,
        indefinite=tuple(indefinite),
        complete=residue_squared == 0,
        completeness_residue_squared=residue_squared,
        rounds_nowhere=sum_rounds_nowhere(blocks),
        constant=constant,
    )
