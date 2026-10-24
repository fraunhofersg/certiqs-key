"""The measuring kernel: one implementation of each operator predicate's DEFECT.

WHY THIS MODULE EXISTS AT ALL
=============================
spec/architecture.md 2.8: the engine
computes in binary64 and each instance
declares exactly ONE numerical tolerance ``tau`` that decides every operator
predicate the platform checks. That sentence is a statement about the code only
if there is one implementation of each predicate. Without this module there would be
several implementations of Hermiticity and of positivity across the tree,
each with its own tolerance argument and its own convention about what "the
defect" means -- different tolerances wearing one name.

So: one function per measurement, and **the function returns a number**.

THE ONE RULE OF THIS MODULE
===========================
**No function here takes a tolerance, returns a bool, or mutates its input.**

That is the whole design. The kernel is shared; the decision is not. A module
measures and then refuses on its own authority ("measure and refuse",
spec/architecture.md 2.8); an instance measures and then snaps on its own
authority (the snapping table of spec/architecture.md 2.9, which arrives with
``instances/``). Neither behaviour belongs to the
measurement, and a kernel that returned ``is_hermitian(a, tol)`` would be
handing every caller a decision it had no standing to make.

WHY :mod:`certiqs_key.domain.validation` COULD NOT BE REUSED
============================================================
``domain/validation.py`` measures **and decides**: it raises
:class:`~certiqs_key.domain._base.BundleValidationError` at the point of
measurement. That is right for what it is -- a structural check of a bundle as
data, where a malformed file is simply not a bundle -- and it is exactly why a
module cannot call it. A module that reused it would inherit a refusal decided
against ``validation.py``'s idea of "wrong" rather than against the tolerance
its own instance declared, and the decision would be taken in a package that
has no contract and no gates. The objection fits in one
line: *"``domain/validation.py`` objects to its own name."*

``validation.py`` is unchanged by this module and keeps its own callers: the
two coexist and neither reads the other.

THE FIVE MEASUREMENTS (spec/architecture.md 2.9, verbatim in their return values)
=================================================================================

===============================  ==========================================
Function                         Returns
===============================  ==========================================
:func:`hermiticity_defect`       the largest entrywise modulus of ``a - a^dag``
:func:`min_eigenvalue`           the smallest eigenvalue of the Hermitian part
:func:`completeness_residue`     the largest entrywise modulus of ``sum_v F_v - 1``
:func:`column_residue`           the largest ``|sum_r m[r, c] - 1|`` over columns
:func:`trace_residue`            ``|tr a - 1|``
===============================  ==========================================

The norm is the **entrywise maximum modulus** wherever the table says
"entrywise", and it is named here rather than left to a reader: it is not the
spectral norm that ``receiver``'s Definition ``def:residuals`` names for
its own residuals, and the two numbers differ by up to a factor of the
dimension. A caller comparing one of these numbers against ``tau`` is comparing
an entrywise defect, and the tolerance is sized on entrywise defects.

Each measurement has a **block-wise wrapper** returning a
:class:`BlockMeasurement`: the per-block vector *and* the one number a caller
compares against the tolerance, plus the identifier of the block that attained
it -- because a consumer that refuses must be able to say WHICH block failed
(spec/architecture.md 2.8).

WHAT THIS MODULE REFUSES, AND WHY THAT IS NOT A DECISION
========================================================
Three argument conditions raise :class:`ValueError`, and none of them is a
tolerance decision: a non-square argument where the measurement is defined only
on a square one, a zero-dimensional argument (the operator format's shapes are
``ge=1``, so a 0x0 block is not expressible and its "defect" would be a
vacuous 0.0 that a caller could not distinguish from a measured one), and a
**non-finite entry**. The last is fail-closed arithmetic rather than
pedantry: ``float('nan') > tau`` is ``False``, so a NaN defect returned as a
number would sail past every ``> tau`` refusal in the tree and every snap
guard. A NaN in, a hard error out.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

import numpy as np
import numpy.typing as npt

__all__ = [
    "Aggregate",
    "BlockMeasurement",
    "Matrix",
    "checked_matrix",
    "column_residue",
    "column_residue_by_block",
    "completeness_residue",
    "completeness_residue_by_block",
    "hermitian_part",
    "hermiticity_defect",
    "hermiticity_defect_by_block",
    "min_eigenvalue",
    "min_eigenvalue_by_block",
    "trace_residue",
    "trace_residue_by_block",
]

#: A real or complex binary64 array, as the kernel reads one. Deliberately
#: wider than the receiver's ``NDArray[np.complex128]``: the bundle
#: format's :class:`~certiqs_key.domain.arrays.Dtype` admits ``float64`` as well,
#: and a kernel that silently complexified a real declared operator would
#: change the object it was asked to measure.
Matrix = npt.NDArray[Any]


class Aggregate(StrEnum):
    """How a :class:`BlockMeasurement` reduces its per-block vector to one number.

    spec/architecture.md 2.8 says a wrapper returns "the per-block vector as well as the
    maximum". For the four DEFECT measurements the maximum is indeed the number
    a caller compares against ``tau``. For :func:`min_eigenvalue` it is not:
    the value a caller compares against ``-tau`` is the SMALLEST eigenvalue
    over the blocks, and reporting the maximum there would report the block
    that is furthest from failing. The aggregate is therefore recorded rather
    than assumed, so that a run record says which reduction produced the number
    it carries.
    """

    MAXIMUM = "maximum"
    MINIMUM = "minimum"


@dataclass(frozen=True)
class BlockMeasurement:
    """One predicate measured on every block of a sector-block operator.

    Under spec/architecture.md 2.9 an operator IS its list of sector blocks, so every
    operator predicate is per block and a refusal has a block to name.
    """

    #: Block identifier to its own measured value, in the order the blocks were
    #: given. The mapping IS the "per-block vector" of spec/architecture.md
    #: 2.9; it is keyed
    #: rather than positional because a positional block list is not a stable
    #: public contract (spec/architecture.md 2.3, the same reason
    #: :class:`~certiqs_key.foundations.blocks.BlockKind` exists).
    per_block: Mapping[str, float]
    #: Which reduction :attr:`worst` is. See :class:`Aggregate`.
    aggregate: Aggregate
    #: The identifier of the block attaining :attr:`worst`. Ties are broken by
    #: the order the blocks were given, so the answer is deterministic and a
    #: refusal names the same block on every run.
    worst_block: str
    #: The one number a caller compares against its declared tolerance.
    worst: float

    def as_record(self) -> dict[str, object]:
        """Return the JSON-ready form a run record or a refusal reason carries."""
        return {
            "per_block": dict(self.per_block),
            "aggregate": str(self.aggregate),
            "worst_block": self.worst_block,
            "worst": self.worst,
        }


def _checked(a: Matrix, name: str) -> npt.NDArray[Any]:
    """Return ``a`` as a 2-D finite float or complex array, or raise."""
    array = np.asarray(a)
    if array.ndim != 2:
        raise ValueError(
            f"{name} has {array.ndim} dimensions; a matrix measurement reads a "
            "2-D array"
        )
    if array.dtype.kind not in "fc":
        raise ValueError(
            f"{name} has dtype {array.dtype!s}; the engine's numbers are real "
            "or complex floating point (spec/architecture.md 2.8)"
        )
    if 0 in array.shape:
        raise ValueError(
            f"{name} has shape {tuple(array.shape)}; a zero-dimensional "
            "operator is not expressible in this format and its defect would "
            "be a vacuous 0.0 no caller could tell from a measured one"
        )
    if not bool(np.all(np.isfinite(array))):
        raise ValueError(
            f"{name} carries a non-finite entry; a NaN defect compares False "
            "against every tolerance and would pass a check it never met"
        )
    return array


#: The kernel's argument gate, as a public name. The snapping table of
#: spec/architecture.md 2.9 reads the same declared arrays this kernel measures
#: and must apply the same three refusals -- 2-D, floating point, finite -- and
#: it was importing ``_checked`` through the underscore to do so. One gate, one
#: implementation, one name a caller may say out loud.
checked_matrix = _checked


def _checked_square(a: Matrix, name: str) -> npt.NDArray[Any]:
    """Return ``a`` as a finite square matrix, or raise."""
    array = _checked(a, name)
    if array.shape[0] != array.shape[1]:
        raise ValueError(
            f"{name} has shape {tuple(array.shape)}; this measurement is "
            "defined on a square matrix"
        )
    return array


def _worst(
    per_block: Mapping[str, float], aggregate: Aggregate, name: str
) -> BlockMeasurement:
    """Reduce a per-block vector, naming the first block that attains it."""
    if not per_block:
        raise ValueError(
            f"{name} was given no blocks; an operator declares at least one "
            "(certiqs_key.domain.arrays.BlockDiagonalOperator)"
        )
    if aggregate is Aggregate.MAXIMUM:
        worst_block = max(per_block, key=lambda block: per_block[block])
    else:
        worst_block = min(per_block, key=lambda block: per_block[block])
    return BlockMeasurement(
        per_block=dict(per_block),
        aggregate=aggregate,
        worst_block=worst_block,
        worst=per_block[worst_block],
    )


def hermitian_part(a: Matrix) -> Matrix:
    """Return ``(a + a^dag) / 2``, preserving the argument's dtype family.

    NOT A MEASUREMENT AND NOT A REPAIR. It is the operator
    :func:`min_eigenvalue` is defined on, and it is the object
    the snapping table of spec/architecture.md 2.9 returns when an INSTANCE
    elects to snap its own declaration. It is exported so that the two callers
    share one expression; a module that substitutes it for the operator it was
    handed has repaired what it was handed, which spec/architecture.md 2.8
    forbids outside the instance.

    Raises:
        ValueError: if ``a`` is not a finite square matrix.
    """
    array = _checked_square(a, "a")
    return np.asarray(0.5 * (array + array.conj().T))


def hermiticity_defect(a: Matrix) -> float:
    """Return the largest entrywise modulus of ``a - a^dag`` (spec/architecture.md 2.8).

    Zero exactly when ``a`` is Hermitian.

    Raises:
        ValueError: if ``a`` is not a finite square matrix.
    """
    array = _checked_square(a, "a")
    return float(np.max(np.abs(array - array.conj().T)))


def min_eigenvalue(a: Matrix) -> float:
    """Return the smallest eigenvalue of the Hermitian part of ``a`` (2.9).

    The Hermitian part is taken because an eigenvalue of a non-Hermitian matrix
    is not a real number and there is nothing to compare against ``-tau``. The
    Hermiticity defect that was discarded in taking it is measured separately,
    by :func:`hermiticity_defect`, and a caller checking positivity of a
    declared operator checks both.

    Raises:
        ValueError: if ``a`` is not a finite square matrix.
    """
    return float(np.linalg.eigvalsh(hermitian_part(a))[0])


def completeness_residue(elements: Sequence[Matrix]) -> float:
    """Return the largest entrywise modulus of ``sum_v F_v - 1`` (2.9).

    Args:
        elements: the family ``{F_v}_v`` **on one block** -- one POVM element
            per outcome, all of the same square shape. spec/architecture.md
            2.9 names the
            argument ``blocks`` and then says "per block and then the maximum
            over blocks"; the per-block maximum is
            :func:`completeness_residue_by_block`, and THIS function is the one
            block it maximises over.

    Raises:
        ValueError: if the family is empty, if the elements disagree in shape,
            or if any element is not a finite square matrix.
    """
    if not elements:
        raise ValueError(
            "completeness is a statement about a non-empty family; an empty "
            "one sums to nothing and 'sum_v F_v - 1' has no subject"
        )
    arrays = [
        _checked_square(element, f"elements[{index}]")
        for index, element in enumerate(elements)
    ]
    shapes = {array.shape for array in arrays}
    if len(shapes) != 1:
        raise ValueError(
            f"the family carries elements of shapes {sorted(shapes)}; a POVM "
            "on one block has one dimension"
        )
    total = arrays[0]
    for array in arrays[1:]:
        total = total + array
    return float(np.max(np.abs(total - np.eye(total.shape[0]))))


def column_residue(m: Matrix) -> float:
    """Return the largest ``|sum_r m[r, c] - 1|`` over columns ``c`` (2.9).

    Zero exactly when every column of ``m`` sums to one -- the
    column-stochasticity half of a declared channel matrix. The rectangular
    case is admitted: a coarse-graining matrix maps one alphabet into another
    and need not be square.

    Raises:
        ValueError: if ``m`` is not a finite 2-D array.
    """
    array = _checked(m, "m")
    return float(np.max(np.abs(array.sum(axis=0) - 1.0)))


def trace_residue(a: Matrix) -> float:
    """Return ``|tr a - 1|`` (spec/architecture.md 2.8).

    Zero exactly when ``a`` has unit trace -- the normalisation half of a
    declared state.

    Raises:
        ValueError: if ``a`` is not a finite square matrix.
    """
    array = _checked_square(a, "a")
    return float(abs(complex(np.trace(array)) - 1.0))


def hermiticity_defect_by_block(blocks: Mapping[str, Matrix]) -> BlockMeasurement:
    """Measure :func:`hermiticity_defect` on every block, worst = the maximum.

    Raises:
        ValueError: if ``blocks`` is empty or a block is not a finite square
            matrix.
    """
    return _worst(
        {name: hermiticity_defect(block) for name, block in blocks.items()},
        Aggregate.MAXIMUM,
        "hermiticity_defect_by_block",
    )


def min_eigenvalue_by_block(blocks: Mapping[str, Matrix]) -> BlockMeasurement:
    """Measure :func:`min_eigenvalue` on every block, worst = the MINIMUM.

    The one wrapper whose aggregate is not the maximum; see :class:`Aggregate`.

    Raises:
        ValueError: if ``blocks`` is empty or a block is not a finite square
            matrix.
    """
    return _worst(
        {name: min_eigenvalue(block) for name, block in blocks.items()},
        Aggregate.MINIMUM,
        "min_eigenvalue_by_block",
    )


def completeness_residue_by_block(
    families: Mapping[str, Sequence[Matrix]],
) -> BlockMeasurement:
    """Measure :func:`completeness_residue` on every block, worst = the maximum.

    Args:
        families: block identifier to the family ``{F_v}_v`` on that block.
            Completeness holds per block under spec/architecture.md 2.9, so the outcome
            alphabet is the inner index and the block is the outer one.

    Raises:
        ValueError: if ``families`` is empty, or a family is empty, ragged or
            not finite.
    """
    return _worst(
        {name: completeness_residue(family) for name, family in families.items()},
        Aggregate.MAXIMUM,
        "completeness_residue_by_block",
    )


def column_residue_by_block(blocks: Mapping[str, Matrix]) -> BlockMeasurement:
    """Measure :func:`column_residue` on every block, worst = the maximum.

    Raises:
        ValueError: if ``blocks`` is empty or a block is not a finite 2-D array.
    """
    return _worst(
        {name: column_residue(block) for name, block in blocks.items()},
        Aggregate.MAXIMUM,
        "column_residue_by_block",
    )


def trace_residue_by_block(blocks: Mapping[str, Matrix]) -> BlockMeasurement:
    """Measure :func:`trace_residue` on every block, worst = the maximum.

    Raises:
        ValueError: if ``blocks`` is empty or a block is not a finite square
            matrix.
    """
    return _worst(
        {name: trace_residue(block) for name, block in blocks.items()},
        Aggregate.MAXIMUM,
        "trace_residue_by_block",
    )
