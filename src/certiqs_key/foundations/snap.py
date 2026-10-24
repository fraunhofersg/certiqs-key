"""The snapping table: the ONE licensed repair of declared data, and its record.

WHO MAY CALL THIS MODULE
========================
**Only whoever declares the data** -- an ``instances/`` package about its own
device, or a producer about **its own emission**. A module that snaps something
it was *handed* is a defect, caught by the import-direction rule of
PRINCIPLES.md section 4 and by review. The reason is not tidiness:

* spec/architecture.md 2.8 ("Who snaps") draws the line: "declared data is
  snapped by whoever declares it, once, by the documented table the snapping
  module owns, and the snap **produces exact admissibility**". An
  instance asserts something about its own device and may round that assertion
  to the nearest exactly admissible one, in the open. A module was handed an
  artefact by another module, and "no module repairs what it was handed";
* **a snap must happen exactly once on any one object.** If a consumer could
  snap too, it would repair data that had already been repaired, and the
  recorded pre-snap defect would stop being a measurement of anything real.

Its callers in this repository are the instances (``instances/bb84/declare.py``
and ``instances/common/honest/spdc_pair.py``, declared probability vectors and
port Grams; ``instances/common/declare.py``, the receiver's dark-composed
photon blocks through :func:`snap_measurement_family`) and the run tier's
input preparation (``runs/inputs.py``). ``reductions`` snaps its own
emission by the procedure its own claims state, inside its own package.

TWO PROCEDURES, BY WHAT IS SNAPPED
==================================
* **A measurement family** is snapped by :func:`snap_measurement_family`
  (``foundations/def:snap``, ``req:snap-reference``, ``req:support-safe-snap``,
  ``req:who-snaps``), BLOCK BY BLOCK. A block whose exact reference is a
  lattice family is kept and rests on nothing. Every other block is moved by
  ONE fidelity-first procedure, the support-safe rows on the centres of the
  block's exact reference (or on the data where it has none), with the
  uniform positivity lift only as the flagged last resort. A moved block rests
  on A-SNAP unless the run evaluates it off its snap on the reference
  companion; see the section "THE MEASUREMENT-FAMILY SNAP" below.
* **Data other than a measurement family** -- a probability vector, a
  channel matrix, a forbidden entry -- keep the table below
  (:func:`snap_family_exact`, :func:`snap_column_stochasticity`,
  :func:`snap_forbidden_entries`). Its Positivity row mixes every element with
  a uniform family and its Completeness row puts the residue into one element
  whatever its structural support, which ``foundations/req:support-safe-snap``
  forbids for a measurement family, so it never serves one.

WHAT THIS TABLE IS
==================
A table that merely *reduced* defects -- Hermitian part; column rescale;
completeness distributed over the family **by trace weight**; forbidden entries
zeroed; **positivity not snapped** -- would leave behind a completeness residue
of ``1.11e-16`` after every snap (down from ``4.46e-16``, and there it stops,
because the corrected sum re-rounds) and a computed minimum eigenvalue of
``-2.2e-16`` at every ``N = 1`` point of the fig. 1 grid.

``meat-core`` emits a key length only for declared data whose Hermiticity,
positivity and completeness defects are **exactly zero** and whose
declared-order completeness sum **rounds nowhere** in binary64
(``def:declaration``, its exact-admissibility paragraph and ``eq:declorder``);
``prop:optol-nobound`` proves that no consumer-side tolerance converts into a
bound on the key. Under a reducing table **no point of the fig. 1 grid would
carry a key length**. So the perturbation is absorbed where data is declared
and everything after it is exact until the optimizer.

So the table does not merely reduce a defect; it **produces exact
admissibility**, per sector block, or refuses.

THE TABLE (spec/architecture.md 2.9)
====================================

====================  =====================================  ==================
Step                  Rule                                   Recorded
====================  =====================================  ==================
Hermiticity           the Hermitian part ``(a + a^dag)/2``,  pre-snap
                      exact -- mirrored from the upper       ``hermiticity_
                      triangle, so the result is exactly     defect``
                      Hermitian as binary64 data
Lattice               every real and imaginary part          ``k``, the
                      rounded to the nearest integer         entrywise
                      multiple of ``2^-k`` (half to even)    displacement
Completeness          the exact residue ``1 - sum_v F_v``    pre-snap
                      on the lattice, absorbed into ONE      ``completeness_
                      designated element                     residue``, the
                                                             designated element
Positivity            decided **exactly** by                 the lift weight,
                      ``is_psd_exact``; a block failing by   the pre-snap
                      a rounding is lifted by mixing with    ``min_eigenvalue``,
                      a **dyadic** uniform family at the     and WHICH NUMBER
                      smallest weight of a fixed dyadic      DECIDED
                      ladder that restores exact
                      positivity, after which completeness
                      is re-established exactly
Column-stochasticity  exact on the lattice                   the pre-snap
and forbidden entry                                          residue or modulus,
                                                             plus ``k``
====================  =====================================  ==================

and then, **last**, the rounds-nowhere check
(:func:`~certiqs_key.foundations.exact_admission.sum_rounds_nowhere`) and the full
exact admission
(:func:`~certiqs_key.foundations.exact_admission.admit_family_exact`). It runs last
because the completeness absorb and any positivity lift change partial sums
from the touched element onward, and "sums exactly to the identity" is strictly
weaker than "every partial sum is on the lattice" (spec/architecture.md 2.9,
constraint (2)).

THE INVARIANT, WHICH IS WHAT MAKES A NUMBER BINARY64 (D-LAT)
============================================================
spec/architecture.md 2.9, block quote (D-LAT):

    Every entry of every declared or emitted operator is an integer multiple of
    ``2^-k`` for the one declared ``k <= 53``, and has modulus at most 1.

(``foundations/req:declared-lattice`` states the condition PART BY PART: "the
real and the imaginary part of the entry are integer multiples of ``2^-k``
and have modulus at most 1", with ``foundations/def:binary64`` (iv) and
``reductions/def:exactadm`` (b) in the same words. So ``0.75 + 0.75i`` is on
the lattice, and every decision below reads it that way.)

Such an entry **is** a binary64 number, by construction rather than by
measurement. The same section records what was measured: the lattice is the
wrong lever and the invariant is the right one, because every exact step of a
reduction *multiplies*, so a lattice chosen once at the instance is closed
under none of them and off the nominal point only 8 of 24 measured grid points
were representable at ``k = 40``. Re-establishing the invariant **at each
emission** as well as at the instance gives 24 of 24. That is why this module
is called by a producer on its own emission and not only by an instance.

``k`` **has no default here.** The value the architecture fixes is ``k = 40``,
and it is declared by the instance and passed in, for the same reason ``tau``
is: a defaulted ``k`` would decide the displacement of a declaration on
nobody's authority.

WHAT THE TOLERANCE DECIDES, AND WHAT IT DOES NOT
================================================
``tau`` is the **ceiling on the pre-snap defect a snap may repair**
(spec/architecture.md 2.8, "The tolerance datum"). Every function below
measures the un-snapped object first with the binary64 kernel
:mod:`certiqs_key.foundations.numeric` -- that is what ``tau`` is compared against
-- and raises :class:`SnapRefusedError` before touching a number if the defect
is above it. The comparison admits equality -- ``defect > tolerance`` refuses,
``defect == tolerance`` proceeds -- following ``reductions``'
``lem:exactpsd``'s standing rule that the tolerance inequalities of this
platform are non-strict on both sides.

``tau`` does **not** decide the lattice displacement. Rounding onto ``2^-k``
moves an entry by at most ``2^-(k+1)`` -- ``4.5e-13`` at ``k = 40``, which is
eight orders of magnitude below the ``1e-3`` residual budgets the receiver
declares -- and a ``tau`` of ``1e-15`` would refuse it. **The displacement a
snap introduces is a modelling act, not an error to minimize**: it is recorded,
and the declared family is the object every downstream claim is about.

WHY POSITIVITY IS IN THE TABLE
==============================
Under measure-and-refuse an eigenvalue above ``-tau`` would pass at every
consumer, so a positivity snap would buy nothing. A consumer decides positivity
**exactly**, so there is no window left for a rounding to pass through, and a
block that sits one rounding below the cone is refused rather than admitted.
The lift is therefore load-bearing.

It is decided exactly and never by a floating-point eigenvalue
(spec/architecture.md 2.9, (D-EMIT) (iii)). The two numbers **routinely
disagree in sign at the 1e-16 scale**, and the disagreement is not noise in one
direction only: ``np.linalg.eigvalsh`` reported up to ``9.06e-17`` of spurious
negativity on families that are positive semidefinite by two independent exact
decisions. So the record says **which number decided**
(spec/architecture.md 2.9, constraint (4)): ``is_psd_exact`` decides,
``min_eigenvalue`` is a float diagnostic carried beside it.

WHAT A SNAP IS NOT
==================
It is not a repair of a bundle. For data snapped by the table below it relates
the snapped object to the original one by **nothing at all** beyond its
recorded displacement: ``meat-core``'s ``prop:optol-nobound`` proves no bound
exists in general. What the run asserts afterwards is the snapped declaration,
and the :class:`SnapRecord` is what makes that visible: every step that changed
something is carried in the run record with its measured pre-snap defect and
its displacement, so a run that declared something says so. The same holds
of a measurement-family snap: no claim relates it to the model, and a run
that holds a reference reads the snapped family only to find points
(``foundations/def:evaluated-off-snap``).
"""

from __future__ import annotations

import math
from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass, field, replace
from enum import StrEnum
from fractions import Fraction
from typing import Any, Final

import numpy as np

from certiqs_key.foundations.errors import MalformedInputError
from certiqs_key.foundations.exact import (
    ONE,
    ZERO,
    Cx,
    equal,
    is_binary64,
    is_complete_at,
    is_hermitian,
    is_positive_semidefinite,
    lattice_round_matrix,
    on_lattice,
)
from certiqs_key.foundations.exact import Matrix as ExactMatrix
from certiqs_key.foundations.exact import sum_rounds_nowhere as exact_sum_rounds_nowhere
from certiqs_key.foundations.exact_admission import (
    ExactAdmission,
    admit_family_exact,
    is_hermitian_exact,
    is_psd_exact,
    sum_rounds_nowhere,
    to_exact,
)
from certiqs_key.foundations.numeric import (
    Matrix,
    checked_matrix,
    column_residue,
    completeness_residue,
    hermiticity_defect,
    min_eigenvalue,
)
from certiqs_key.foundations.reference import Reference, ReferenceBlock, ReferenceKind
from certiqs_key.foundations.resting import (
    RestingCause,
    RestingGroup,
    resting_fix,
    resting_group,
)
from certiqs_key.foundations.rungs import checked_lattice_exponent

__all__ = [
    "ASSUMPTION_CLAIM",
    "ASSUMPTION_ID",
    "ASSUMPTION_MACHINE_KEY",
    "LIFT_LADDER",
    "REFUSAL_REASONS",
    "BlockSnapRecord",
    "BlockStatus",
    "HandedBlock",
    "MeasurementSnap",
    "MeasurementSnapRecord",
    "SnapPredicate",
    "SnapRecord",
    "SnapRefusedError",
    "SnapRule",
    "SnapSettings",
    "SnapStep",
    "SupportSafeSnap",
    "decide_last",
    "designated_element_index",
    "dyadic_uniform_weights",
    "is_on_lattice",
    "snap_column_stochasticity",
    "snap_completeness",
    "snap_family_exact",
    "snap_forbidden_entries",
    "snap_hermiticity",
    "snap_measurement_family",
    "snap_positivity",
    "snap_to_lattice",
    "support_safe_snap_block",
    "verify_family_exact",
]


#: The dyadic ladder the positivity lift walks, smallest weight first. Taken
#: from the exact-emission normalizer, which restored exact
#: positivity on 24 of 24 grid points at every ``k`` tried; the measurement
#: is the one spec/architecture.md 2.9 records. Every rung is ``2^-t``, so
#: ``(1 - s)`` and ``s`` are both exact on any lattice at least as fine as
#: ``2^-t``, and the mixed family is re-rounded onto ``2^-k`` afterwards in any
#: case.
#:
#: The smallest rung is chosen, so the lift moves the declaration as little as
#: the ladder allows. A rung finer than the declared lattice is not skipped: it
#: is simply a rung at which the mixture rounds back to where it started, the
#: block is still not exactly PSD, and the loop proceeds to the next.
LIFT_LADDER: Final[tuple[Fraction, ...]] = tuple(
    Fraction(1, 2**exponent) for exponent in (36, 34, 32, 28, 24, 20, 16)
)

class SnapPredicate(StrEnum):
    """The predicate a snap restored. One member per row of the table.

    ``POSITIVITY`` and ``LATTICE`` are rows of spec/architecture.md 2.9;
    ``DECLARED_ORDER_SUM`` names condition (S), which is checked and never
    snapped -- there is no repair for it that is not one of the rows above.
    """

    HERMITICITY = "hermiticity"
    LATTICE = "lattice"
    COMPLETENESS = "completeness"
    POSITIVITY = "positivity"
    COLUMN_STOCHASTICITY = "column-stochasticity"
    FORBIDDEN_ENTRY = "forbidden-entry"
    DECLARED_ORDER_SUM = "declared-order-sum"
    #: The strict option of ``foundations/req:snap-reference`` (iv): a block
    #: that would rest on A-SNAP is refused, not snapped.
    STRICT_OPTION = "strict-option"


class SnapRule(StrEnum):
    """The rule a snap applied -- the table's middle column, machine-readable.

    Recorded rather than inferred from the predicate, because a reader of a run
    record from a later version must be able to tell WHICH rule produced the
    numbers in front of them. That is what
    :attr:`DISTRIBUTE_BY_TRACE_WEIGHT` is still doing here: it is a
    completeness rule **never applied by this module**, kept as a member so
    that run records that name it remain readable.
    """

    HERMITIAN_PART = "hermitian-part"
    ROUND_TO_LATTICE = "round-to-lattice"
    ABSORB_INTO_DESIGNATED_ELEMENT = "absorb-into-designated-element"
    MIX_WITH_DYADIC_UNIFORM = "mix-with-dyadic-uniform"
    DECIDED_EXACTLY = "decided-exactly"
    RESCALE_AND_ABSORB = "rescale-and-absorb"
    ZEROED = "zeroed"
    #: LEGACY. A completeness rule, superseded by
    #: :attr:`ABSORB_INTO_DESIGNATED_ELEMENT`, which closes the residue exactly
    #: where this one could only reduce it to ``1.11e-16``. Never produced.
    DISTRIBUTE_BY_TRACE_WEIGHT = "distribute-by-trace-weight"


#: Machine-readable reasons a snap declines.
#:
#: * ``defect_above_tolerance`` -- the table's own refusal: a pre-snap defect
#:   above ``tau`` is a modelling error and not noise;
#: * ``degenerate_column`` -- a column summing to zero cannot be rescaled to
#:   one;
#: * ``no_designated_element`` -- every element of the family is structurally
#:   zero, so the completeness residue has nowhere to go that the designated
#:   rule permits;
#: * ``part_modulus_above_one`` -- (D-LAT)'s second half fails, a real or an
#:   imaginary part of modulus above one, and no rounding
#:   repairs it;
#: * ``positivity_not_restored`` -- the whole of :data:`LIFT_LADDER` was walked
#:   and no rung produced an exactly positive semidefinite, exactly complete
#:   family;
#: * ``not_exactly_admissible`` -- the final exact verification failed. Every
#:   step above is meant to make this unreachable, which is exactly why it is
#:   checked: a snap that returned a family it had not verified would be
#:   asserting the one thing the caller cannot check for itself;
#: * ``strict_snaps`` -- a run that declares the strict option
#:   (run option ``strict_snaps``) refuses a measurement-family block
#:   that would rest on A-SNAP (``foundations/req:snap-reference`` (iv)), the
#:   flagged last resort of ``foundations/req:support-safe-snap`` (iv)
#:   included.
REFUSAL_REASONS: tuple[str, ...] = (
    "defect_above_tolerance",
    "degenerate_column",
    "no_designated_element",
    "part_modulus_above_one",
    "positivity_not_restored",
    "not_exactly_admissible",
    "strict_snaps",
)


class SnapRefusedError(Exception):
    """No snap was performed, and the caller must refuse rather than proceed.

    Deliberately NOT a :class:`~certiqs_key.domain._base.BundleError`: nothing
    here is about a file being malformed. It is a declaration a producer cannot
    make, and the producer turns it into its own refusal -- for
    ``optical_bb84`` today that is a
    :class:`~certiqs_key.runs.pipeline.AdapterRefusal`.
    """

    def __init__(
        self,
        message: str,
        *,
        reason: str,
        predicate: SnapPredicate,
        site: str,
        setting: str | None = None,
        block: str | None = None,
        defect: float | None = None,
        tolerance: float | None = None,
        detail: Mapping[str, Any] | None = None,
    ) -> None:
        """Record the machine-readable half of the refusal beside its message."""
        super().__init__(message)
        self.reason = reason
        self.predicate = predicate
        self.site = site
        self.setting = setting
        self.block = block
        self.defect = defect
        self.tolerance = tolerance
        self.detail: Mapping[str, Any] = dict(detail or {})


@dataclass(frozen=True)
class SnapRecord:
    """What one snap did, and to what. The run record carries all of them.

    Every field is a fact about THIS run's declaration. None of them is a bound
    on anything the declaration implies, and :attr:`defect` in particular is a
    measurement of the object BEFORE the snap and says nothing about the object
    after it.
    """

    #: Which row of the table was applied.
    predicate: SnapPredicate
    #: The rule that row names.
    rule: SnapRule
    #: Where in the declaration the snapped object sits, in the caller's own
    #: vocabulary -- for example ``"bob_povm"`` or ``"dark_count_channel"``.
    site: str
    #: The ``(setting, block)`` key of the table, split into its
    #: two halves so that either may be absent. A channel matrix has no setting; a
    #: declaration that is not blocked has no block.
    setting: str | None
    #: See :attr:`setting`.
    block: str | None
    #: The pre-snap defect, measured in binary64 by
    #: :mod:`certiqs_key.foundations.numeric`. A ``float`` and only ever a ``float``:
    #: the lattice exponent, the designated element, the lift weight and which
    #: number decided go in :attr:`detail` (spec/architecture.md 2.9, constraint (3)).
    defect: float
    #: The declared tolerance it was admitted under. Carried so that the record
    #: is readable without the run configuration beside it, since ``defect``
    #: alone does not say whether it was a comfortable snap or one at the edge
    #: of what the declarer permits.
    tolerance: float
    #: Rule-specific facts -- the lattice exponent, the displacement, the
    #: designated element, the lift weight, which number decided. JSON-ready:
    #: exact rationals appear as strings, never as floats, because rendering
    #: one as a float would put back the rounding this table exists to remove.
    detail: Mapping[str, Any] = field(default_factory=dict)

    def as_record(self) -> dict[str, object]:
        """Return the JSON-ready form the run record carries."""
        return {
            "predicate": str(self.predicate),
            "rule": str(self.rule),
            "site": self.site,
            "setting": self.setting,
            "block": self.block,
            "pre_snap_defect": self.defect,
            "declared_tolerance": self.tolerance,
            "detail": dict(self.detail),
        }


# ---------------------------------------------------------------------------
#  Argument gates
# ---------------------------------------------------------------------------


def _checked_tolerance(tolerance: float) -> float:
    """Return the declared tolerance, or raise if it is not one.

    ``tau`` has no default anywhere in this platform
    (spec/architecture.md 2.8), so there is nothing to fall back to -- but a
    caller may still pass a number that is not a tolerance, and a NaN one would
    admit every snap.
    """
    value = float(tolerance)
    if not np.isfinite(value) or value < 0.0:
        raise ValueError(
            f"tolerance {tolerance!r} is not a declared numerical tolerance; "
            "tau is finite and non-negative (spec/architecture.md 2.8)"
        )
    return value


def _checked_lattice_exponent(lattice_exponent: int) -> int:
    """Return the declared lattice exponent ``k``, or raise ``ValueError``.

    ``k`` has no default here (spec/architecture.md 2.9); the measured
    recommendation is ``40`` and the instance declares it. The range check
    ``1 <= k <= 53`` is :func:`~certiqs_key.foundations.rungs.
    checked_lattice_exponent`, held once; this
    adapter keeps the ``ValueError`` this module's callers and tests catch.
    """
    try:
        return checked_lattice_exponent(lattice_exponent)
    except MalformedInputError as error:
        raise ValueError(
            f"lattice_exponent: {error} (spec/architecture.md 2.9)"
        ) from error


def _admit(
    defect: float,
    tolerance: float,
    predicate: SnapPredicate,
    site: str,
    setting: str | None,
    block: str | None,
    *,
    detail: Mapping[str, Any] | None = None,
) -> None:
    """Raise unless the measured defect is within the declared tolerance."""
    if defect > tolerance:
        raise SnapRefusedError(
            f"{predicate} defect {defect!r} at {_where(site, setting, block)} "
            f"exceeds the declared tolerance {tolerance!r}; a defect above tau "
            "is a modelling error and not noise, so nothing is snapped and the "
            "declarer refuses",
            reason="defect_above_tolerance",
            predicate=predicate,
            site=site,
            setting=setting,
            block=block,
            defect=defect,
            tolerance=tolerance,
            detail=detail,
        )


def _where(site: str, setting: str | None, block: str | None) -> str:
    """Return the human half of a refusal's location."""
    where = site
    if setting is not None:
        where += f", setting {setting!r}"
    if block is not None:
        where += f", block {block!r}"
    return where


# ---------------------------------------------------------------------------
#  The exact substrate this table works over
#
#  Every step below that must land ON the lattice is computed in exact
#  Gaussian rationals and converted back once, at the end, by
#  :func:`_to_arrays`, which refuses anything that is not a binary64 number.
#  Doing the arithmetic in binary64 and hoping is what the old table did.
# ---------------------------------------------------------------------------


def _exact_family(blocks: Sequence[Matrix], name: str) -> list[ExactMatrix]:
    """Convert a family of same-shaped square blocks exactly, or raise."""
    if not blocks:
        raise ValueError(
            f"{name} was given an empty family; a sum over no elements has no "
            "subject and its residue would be a vacuous 0 no caller could tell "
            "from a measured one"
        )
    family = [to_exact(block) for block in blocks]
    shapes = {(len(element), len(element[0])) for element in family}
    if len(shapes) != 1:
        raise ValueError(
            f"{name} was given elements of shapes {sorted(shapes)}; a family on "
            "one sector has one shape"
        )
    rows, columns = shapes.pop()
    if rows != columns:
        raise ValueError(
            f"{name} was given elements of shape {(rows, columns)}; the family "
            "of one sector block is square"
        )
    return family


def _exact_sum(family: Sequence[ExactMatrix]) -> ExactMatrix:
    """Return the exact entrywise sum of a same-shaped family."""
    rows = len(family[0])
    columns = len(family[0][0])
    out: list[list[Cx]] = [[ZERO for _ in range(columns)] for _ in range(rows)]
    for element in family:
        for i in range(rows):
            for j in range(columns):
                out[i][j] = out[i][j] + element[i][j]
    return tuple(tuple(row) for row in out)


def _exact_completeness_residue(family: Sequence[ExactMatrix]) -> ExactMatrix:
    """Return ``1 - sum_v F_v``, exactly."""
    total = _exact_sum(family)
    size = len(total)
    return tuple(
        tuple(
            (ONE - total[i][j]) if i == j else (ZERO - total[i][j]) for j in range(size)
        )
        for i in range(size)
    )


def _exact_add(a: ExactMatrix, b: ExactMatrix) -> ExactMatrix:
    """Return the exact entrywise sum of two same-shaped matrices."""
    return tuple(
        tuple(a[i][j] + b[i][j] for j in range(len(a[0]))) for i in range(len(a))
    )


def _exact_trace(m: ExactMatrix) -> Fraction:
    """Return the real part of the exact trace.

    The family this rule chooses from is Hermitian by the time it is asked, so
    the trace is real and the real part is the whole of it; taking the real
    part rather than refusing keeps the choice total for a caller that asks
    before hermitizing, and matches
    :func:`certiqs_key.foundations.numeric.completeness_residue`'s own convention.
    """
    return sum((m[i][i].re for i in range(len(m))), Fraction(0))


def _exact_is_zero(m: ExactMatrix) -> bool:
    """Whether every entry of ``m`` vanishes exactly."""
    return all(entry.is_zero for row in m for entry in row)


def _round_part(x: Fraction, step: int) -> Fraction:
    """Round one rational to the nearest multiple of ``1/step``, halves to even."""
    return Fraction(round(x * step), step)


def _round_exact(m: ExactMatrix, lattice_exponent: int) -> ExactMatrix:
    """Round every real and imaginary part onto the ``2^-k`` lattice.

    Round-half-to-even, which is odd-symmetric, so a Hermitian matrix rounds to
    a Hermitian matrix: the two mirror entries have equal real parts and
    opposite imaginary parts before rounding and therefore after it.
    """
    step = 1 << lattice_exponent
    return tuple(
        tuple(
            Cx(_round_part(entry.re, step), _round_part(entry.im, step))
            for entry in row
        )
        for row in m
    )


def _to_arrays(
    family: Sequence[ExactMatrix],
    *,
    complex_output: bool,
    site: str,
    setting: str | None,
    block: str | None,
    predicate: SnapPredicate,
) -> tuple[Matrix, ...]:
    """Convert an exact family back to binary64, refusing anything that rounds.

    Every entry produced by this table is an integer multiple of ``2^-k`` of
    modulus at most one, so ``float`` of it is exact. This function is the
    place that says so out loud rather than assuming it.
    """
    out: list[Matrix] = []
    for index, element in enumerate(family):
        size = len(element)
        array = np.zeros(
            (size, size), dtype=np.complex128 if complex_output else np.float64
        )
        for i in range(size):
            for j in range(size):
                entry = element[i][j]
                if not is_binary64(entry.re) or not is_binary64(entry.im):
                    raise SnapRefusedError(
                        f"element {index} of {_where(site, setting, block)} has "
                        f"an entry ({i}, {j}) = {entry} that is not a binary64 "
                        "number, so (D-LAT) does not hold of the snapped family "
                        "(spec/architecture.md 2.9)",
                        reason="not_exactly_admissible",
                        predicate=SnapPredicate.LATTICE,
                        site=site,
                        setting=setting,
                        block=block,
                        detail={"element": index, "entry": [i, j]},
                    )
                if complex_output:
                    array[i, j] = complex(float(entry.re), float(entry.im))
                elif entry.im != 0:
                    raise SnapRefusedError(
                        f"element {index} of {_where(site, setting, block)} was "
                        f"declared real and its entry ({i}, {j}) acquired an "
                        "imaginary part; the snap does not silently complexify "
                        "a declaration",
                        reason="not_exactly_admissible",
                        predicate=predicate,
                        site=site,
                        setting=setting,
                        block=block,
                        detail={"element": index, "entry": [i, j]},
                    )
                else:
                    array[i, j] = float(entry.re)
        out.append(array)
    return tuple(out)


def _wants_complex(blocks: Sequence[Matrix]) -> bool:
    """Whether the snapped family is carried as ``complex128``.

    One dtype for the whole family, because the completeness residue is shared
    between its elements: a real element of a family with a complex one can
    receive a complex residue, and silently truncating it would change the
    object being declared.
    """
    return any(np.iscomplexobj(np.asarray(block)) for block in blocks)


# ---------------------------------------------------------------------------
#  (D-LAT), as a predicate
# ---------------------------------------------------------------------------


def is_on_lattice(a: Matrix, *, lattice_exponent: int) -> bool:
    """Whether ``a`` satisfies (D-LAT) for the given ``k`` (spec/architecture.md 2.9).

    That is: every real and every imaginary part is an integer multiple of
    ``2^-k`` of modulus at most one, PART BY PART, as
    ``foundations/req:declared-lattice`` states it (and
    :func:`certiqs_key.foundations.exact.on_lattice` decides it): ``0.75 + 0.75i``
    is on the lattice although its modulus exceeds one. An entry satisfying
    both **is** a binary64 number, by ``foundations/lem:binary64-lattice``
    (i), which is what the invariant is for.

    Args:
        a: a 2-D real or complex binary64 array.
        lattice_exponent: the declared ``k``.

    Returns:
        ``True`` when the invariant holds of every entry.

    Raises:
        ValueError: if ``k`` is not a lattice exponent.
        certiqs_key.foundations.exact_admission.ExactInputError: if ``a`` is not a
            2-D binary64 array, or carries a non-finite entry.
    """
    step = 1 << _checked_lattice_exponent(lattice_exponent)
    for row in to_exact(a):
        for entry in row:
            if (entry.re * step).denominator != 1 or abs(entry.re) > 1:
                return False
            if (entry.im * step).denominator != 1 or abs(entry.im) > 1:
                return False
    return True


# ---------------------------------------------------------------------------
#  Step 1 -- the Hermitian part, exactly
# ---------------------------------------------------------------------------


def _hermitian_part_exact(array: Matrix) -> Matrix:
    """Return ``(a + a^dag)/2``, mirrored so that the result IS Hermitian.

    :func:`certiqs_key.foundations.numeric.hermitian_part` computes the same numbers,
    and in binary64 they already come out exactly Hermitian: the two mirror
    entries are formed from the same two addends, whose real parts add
    identically and whose imaginary parts are exact negatives of one another.
    This builds the lower triangle from the upper one anyway, so that exact
    Hermiticity is a property of the construction rather than of a rounding
    argument a later reader has to re-derive.
    """
    half = np.asarray(0.5 * (array + array.conj().T))
    return np.asarray(np.triu(half) + np.triu(half, 1).conj().T)


def snap_hermiticity(
    a: Matrix,
    *,
    tolerance: float,
    site: str,
    setting: str | None = None,
    block: str | None = None,
) -> tuple[Matrix, SnapRecord]:
    """Replace ``a`` by its Hermitian part ``(a + a^dag)/2``, exactly.

    The result is **exactly Hermitian as binary64 data**:
    :func:`certiqs_key.foundations.exact_admission.is_hermitian_exact` is ``True``
    of it, not merely ``hermiticity_defect`` below some tolerance.

    Args:
        a: the declared operator. Not modified.
        tolerance: the declared ``tau``, the ceiling on the pre-snap defect.
        site: where in the declaration ``a`` sits.
        setting: the setting half of the record's key, where there is one.
        block: the block half of the record's key, where there is one.

    Returns:
        The snapped operator and its :class:`SnapRecord`, whose ``defect`` is
        the pre-snap :func:`~certiqs_key.foundations.numeric.hermiticity_defect`.

    Raises:
        SnapRefusedError: if that defect exceeds ``tolerance``.
        ValueError: if ``a`` is not a finite square matrix, or ``tolerance`` is
            not a tolerance.
    """
    admitted = _checked_tolerance(tolerance)
    array = checked_matrix(a, "a")
    if array.shape[0] != array.shape[1]:
        raise ValueError(
            f"a has shape {tuple(array.shape)}; the Hermitian part is defined "
            "on a square matrix"
        )
    defect = hermiticity_defect(array)
    _admit(defect, admitted, SnapPredicate.HERMITICITY, site, setting, block)
    return _hermitian_part_exact(array), SnapRecord(
        predicate=SnapPredicate.HERMITICITY,
        rule=SnapRule.HERMITIAN_PART,
        site=site,
        setting=setting,
        block=block,
        defect=defect,
        tolerance=admitted,
        detail={"exactly_hermitian": True},
    )


# ---------------------------------------------------------------------------
#  Step 2 -- the lattice
# ---------------------------------------------------------------------------


def snap_to_lattice(
    a: Matrix,
    *,
    lattice_exponent: int,
    tolerance: float,
    site: str,
    setting: str | None = None,
    block: str | None = None,
) -> tuple[Matrix, SnapRecord]:
    """Round every real and imaginary part onto the ``2^-k`` lattice (D-LAT).

    Round-half-to-even, entrywise, in exact arithmetic. Afterwards every entry
    is an integer multiple of ``2^-k`` of modulus at most one and is therefore
    exactly a binary64 number -- which is the whole purpose of the step, and
    what makes the declared-order completeness sum round nowhere.

    Hermiticity is preserved: the rounding is odd-symmetric, so mirror entries
    stay mirror entries.

    Args:
        a: the declared operator. Not modified.
        lattice_exponent: the declared ``k``. No default (spec/architecture.md 2.9); the
            measured recommendation is ``40``.
        tolerance: the declared ``tau``. **It does not decide this step** and is
            carried into the record only so that the record is readable on its
            own. The lattice displacement is bounded by ``2^-(k+1)`` -- at
            ``k = 40`` that is ``4.5e-13``, above every ``tau`` in the
            recommended band -- and it is a modelling act, not an error to
            minimize (spec/architecture.md 2.9).
        site: where in the declaration ``a`` sits.
        setting: the setting half of the record's key, where there is one.
        block: the block half of the record's key, where there is one.

    Returns:
        The rounded operator and its :class:`SnapRecord`, whose ``defect`` is
        the largest entrywise modulus of the displacement the rounding
        introduced and whose ``detail`` carries ``k``, the worst entry and how
        many entries moved.

    Raises:
        SnapRefusedError: if a real or imaginary part of any entry has modulus
            above one, before or after the rounding. (D-LAT)'s second half
            is not repairable by rounding.
        ValueError: if ``a`` is not a finite 2-D array, ``k`` is not a lattice
            exponent, or ``tolerance`` is not a tolerance.
    """
    admitted = _checked_tolerance(tolerance)
    exponent = _checked_lattice_exponent(lattice_exponent)
    array = checked_matrix(a, "a")
    exact = to_exact(array)
    _refuse_part_above_one(exact, "before", site, setting, block)
    rounded = _round_exact(exact, exponent)
    _refuse_part_above_one(rounded, "after", site, setting, block)

    displacement = 0.0
    worst: list[int] | None = None
    moved = 0
    for i, row in enumerate(rounded):
        for j, entry in enumerate(row):
            if entry != exact[i][j]:
                moved += 1
            gap = float((entry - exact[i][j]).squared_modulus) ** 0.5
            if gap > displacement:
                displacement, worst = gap, [i, j]

    snapped = _to_arrays(
        [rounded],
        complex_output=bool(np.iscomplexobj(array)),
        site=site,
        setting=setting,
        block=block,
        predicate=SnapPredicate.LATTICE,
    )[0]
    return snapped, SnapRecord(
        predicate=SnapPredicate.LATTICE,
        rule=SnapRule.ROUND_TO_LATTICE,
        site=site,
        setting=setting,
        block=block,
        defect=displacement,
        tolerance=admitted,
        detail={
            "lattice_exponent": exponent,
            "displacement": displacement,
            "entries_moved": moved,
            "worst_entry": worst,
        },
    )


def _refuse_part_above_one(
    m: ExactMatrix,
    when: str,
    site: str,
    setting: str | None,
    block: str | None,
) -> None:
    """Raise if any part breaks (D-LAT)'s modulus condition.

    Part by part, as ``foundations/req:declared-lattice`` states it: the real
    and the imaginary part of every entry have modulus at most one. The
    modulus of the entry is not bounded by the condition.
    """
    for i, row in enumerate(m):
        for j, entry in enumerate(row):
            if abs(entry.re) > 1 or abs(entry.im) > 1:
                raise SnapRefusedError(
                    f"entry ({i}, {j}) of {_where(site, setting, block)} has "
                    f"a real or imaginary part of modulus above one {when} "
                    "rounding; (D-LAT) admits only parts of modulus at most "
                    "one, and no rounding repairs "
                    "that (spec/architecture.md 2.9)",
                    reason="part_modulus_above_one",
                    predicate=SnapPredicate.LATTICE,
                    site=site,
                    setting=setting,
                    block=block,
                    detail={"entry": [i, j], "when": when},
                )


# ---------------------------------------------------------------------------
#  Step 3 -- completeness, absorbed into ONE designated element
# ---------------------------------------------------------------------------


def designated_element_index(blocks: Sequence[Matrix]) -> int:
    """Return the index of the element that absorbs the completeness residue.

    **The stated rule** (spec/architecture.md 2.9, constraint (1)): *the element of
    largest exact trace in the block*, ties broken by the declared order, and
    **never a structurally zero element**.

    The zero exclusion is the one property a trace-weight rule has that this
    table keeps. A zero element is usually zero for a structural
    reason -- an outcome that cannot occur in that photon-number block -- and
    an element that came back as a small non-zero operator with no physical
    meaning would then have to be adjudicated by a positivity check. Under this
    rule it comes back exactly zero, entry for entry.

    The trace is computed **exactly**, from the declared numbers, not from a
    binary64 sum of them: two elements whose float traces tie may have distinct
    exact ones, and the choice must be a function of the declaration.

    Args:
        blocks: the family ``{F_v}_v`` on one sector, in the declared order.

    Returns:
        The index, in the declared order, of the designated element.

    Raises:
        SnapRefusedError: if every element is structurally zero, so that no
            element the rule permits exists.
        ValueError: if the family is empty, ragged or not square.
        certiqs_key.foundations.exact_admission.ExactInputError: if an entry is
            not finite.
    """
    family = _exact_family(blocks, "designated_element_index")
    candidates = [
        index for index, element in enumerate(family) if not _exact_is_zero(element)
    ]
    if not candidates:
        raise SnapRefusedError(
            "every element of the family is structurally zero, so the "
            "completeness residue has no designated element to absorb it; the "
            "rule never nominates a zero element (spec/architecture.md 2.9, "
            "constraint (1))",
            reason="no_designated_element",
            predicate=SnapPredicate.COMPLETENESS,
            site="designated_element_index",
        )
    traces = [_exact_trace(family[index]) for index in candidates]
    best = max(range(len(candidates)), key=lambda position: traces[position])
    return candidates[best]


def snap_completeness(
    elements: Sequence[Matrix],
    *,
    tolerance: float,
    lattice_exponent: int,
    site: str,
    setting: str | None = None,
    block: str | None = None,
) -> tuple[tuple[Matrix, ...], SnapRecord]:
    """Absorb the exact completeness residue into ONE designated element.

    ``D = 1 - sum_v F_v`` is computed **exactly** on the lattice and added, in
    one piece, to the element :func:`designated_element_index` names. The
    family then sums **exactly** to the identity: every entry of ``D`` is an
    integer multiple of ``2^-k``, because every entry of every element is, so
    the addition is exact and the result is still on the lattice.

    This is not *distribute by trace weight*, which would share the residue in
    proportion to the traces and therefore multiply it by weights that are not
    dyadic: that rule leaves ``1.11e-16`` of residue after every snap and cannot
    do better, because the corrected sum re-rounds. It survives as
    :attr:`SnapRule.DISTRIBUTE_BY_TRACE_WEIGHT` so that run records that name it
    remain readable, and is never applied.

    Args:
        elements: the family ``{F_v}_v`` on one block, in the declared order.
            **Must already be on the ``2^-k`` lattice** -- the table's order is
            lattice, then completeness, and absorbing a residue that is not a
            multiple of ``2^-k`` would take the designated element off it. Not
            modified.
        tolerance: the declared ``tau``, the ceiling on the pre-snap residue.
        lattice_exponent: the declared ``k``.
        site: where in the declaration the family sits.
        setting: the setting half of the record's key, where there is one.
        block: the block half of the record's key, where there is one.

    Returns:
        The snapped family, in the order it was given, and its
        :class:`SnapRecord`, whose ``defect`` is the pre-snap
        :func:`~certiqs_key.foundations.numeric.completeness_residue` and whose
        ``detail`` names the designated element and its exact trace.

    Raises:
        SnapRefusedError: if that residue exceeds ``tolerance``, if every
            element is structurally zero, or if the absorb would put a part
            of modulus above one on the designated element.
        ValueError: if the family is empty, ragged or not square, if it is not
            on the declared lattice, if ``k`` is not a lattice exponent, or if
            ``tolerance`` is not a tolerance.
    """
    admitted = _checked_tolerance(tolerance)
    exponent = _checked_lattice_exponent(lattice_exponent)
    defect = completeness_residue(elements)
    _admit(defect, admitted, SnapPredicate.COMPLETENESS, site, setting, block)

    family = _exact_family(elements, "snap_completeness")
    _require_on_lattice(family, exponent, "snap_completeness")
    designated = designated_element_index(elements)
    absorbed, residue_entries = _absorb_completeness(family, designated)
    _refuse_part_above_one(absorbed[designated], "after", site, setting, block)

    snapped = _to_arrays(
        absorbed,
        complex_output=_wants_complex(elements),
        site=site,
        setting=setting,
        block=block,
        predicate=SnapPredicate.COMPLETENESS,
    )
    return snapped, SnapRecord(
        predicate=SnapPredicate.COMPLETENESS,
        rule=SnapRule.ABSORB_INTO_DESIGNATED_ELEMENT,
        site=site,
        setting=setting,
        block=block,
        defect=defect,
        tolerance=admitted,
        detail={
            "elements": len(family),
            "lattice_exponent": exponent,
            "designated_element": designated,
            "designated_element_trace": str(_exact_trace(family[designated])),
            "residue_entries_moved": residue_entries,
        },
    )


def _absorb_completeness(
    family: Sequence[ExactMatrix], designated: int
) -> tuple[list[ExactMatrix], int]:
    """Add the exact residue to the designated element; report entries moved."""
    residue = _exact_completeness_residue(family)
    moved = sum(1 for row in residue for entry in row if not entry.is_zero)
    out = list(family)
    out[designated] = _exact_add(out[designated], residue)
    return out, moved


def _require_on_lattice(
    family: Sequence[ExactMatrix], lattice_exponent: int, name: str
) -> None:
    """Raise unless every entry of the family is a multiple of ``2^-k``."""
    step = 1 << lattice_exponent
    for index, element in enumerate(family):
        for i, row in enumerate(element):
            for j, entry in enumerate(row):
                on = (entry.re * step).denominator == 1
                on = on and (entry.im * step).denominator == 1
                if not on:
                    raise ValueError(
                        f"{name} was given an element {index} whose entry "
                        f"({i}, {j}) is not a multiple of 2^-{lattice_exponent}; "
                        "the table rounds onto the lattice BEFORE it closes "
                        "completeness, and absorbing an off-lattice residue "
                        "would take the designated element off it too "
                        "(spec/architecture.md 2.9)"
                    )


# ---------------------------------------------------------------------------
#  Step 4 -- positivity, decided exactly and lifted dyadically
# ---------------------------------------------------------------------------


def dyadic_uniform_weights(count: int) -> tuple[Fraction, ...]:
    """Return a dyadic probability vector on ``count`` outcomes.

    The uniform family ``(1/|Y|) * 1`` is **not dyadic** for ``|Y| = 6`` --
    this single fact accounts for every representability failure at
    ``p_dc = 0``, twelve of twenty-four grid points at ``k = 40``. A lift with a
    non-dyadic weight takes the whole family off the
    lattice, which is the invariant this table exists to maintain.

    So the weights are dyadic by construction: each is ``1/2^b`` for the
    smallest ``2^b >= count``, and the leftover ``1 - count/2^b`` -- itself a
    multiple of ``1/2^b`` -- goes to the first outcome. For ``count = 6`` that
    is ``(3/8, 1/8, 1/8, 1/8, 1/8, 1/8)``: dyadic, summing exactly to one, so
    the mixture ``(1-s) F_v + s u_v 1`` still sums exactly to the identity
    before the re-rounding, and afterwards the completeness absorb closes it.

    Args:
        count: the number of outcomes, at least one.

    Returns:
        The weights, in outcome order, summing exactly to one.

    Raises:
        ValueError: if ``count`` is not positive.
    """
    if count < 1:
        raise ValueError(
            f"a probability vector on {count} outcomes has no subject; the "
            "family of one sector block carries at least one element"
        )
    base = 1 << max(count - 1, 1).bit_length() if count > 1 else 1
    weights = [Fraction(1, base)] * count
    weights[0] = weights[0] + (Fraction(1) - Fraction(count, base))
    return tuple(weights)


def snap_positivity(
    blocks: Sequence[Matrix],
    *,
    tolerance: float,
    lattice_exponent: int,
    site: str,
    setting: str | None = None,
    block: str | None = None,
    pre_snap_min_eigenvalue: float | None = None,
) -> tuple[tuple[Matrix, ...], SnapRecord | None]:
    """Decide positivity exactly; lift a family that fails by a rounding.

    **Not for a measurement family**: the uniform lift below adds support to
    every element, and on a measurement family ``foundations/req:support-safe-snap``
    admits it only as the flagged last resort of
    :func:`support_safe_snap_block`. It serves :func:`snap_family_exact`, whose
    callers snap data other than a measurement family.

    **Which number decides** (spec/architecture.md 2.9, constraint (4)):
    :func:`~certiqs_key.foundations.exact_admission.is_psd_exact` decides, and
    :func:`~certiqs_key.foundations.numeric.min_eigenvalue` is a float diagnostic
    carried beside it. The two routinely disagree in sign at the ``1e-16``
    scale, in both directions: a rank-deficient block that is positive
    semidefinite by two independent exact decisions is reported at
    ``-9.06e-17`` by :func:`numpy.linalg.eigvalsh`, and the defect that number
    was once attributed to was a non-dyadic lift weight and not a real
    negativity. Such a block is admitted **without a lift** here.

    Where the exact decision does refuse, the family is mixed with the dyadic
    uniform family of :func:`dyadic_uniform_weights` at the smallest weight of
    :data:`LIFT_LADDER` that restores exact positivity, re-rounded onto the
    lattice, and its completeness re-established exactly. Each rung is tried in
    turn and the first that yields an exactly PSD, exactly complete family
    wins.

    Args:
        blocks: the family ``{F_v}_v`` on one sector, in the declared order,
            **already exactly Hermitian and on the lattice**. Not modified.
        tolerance: the declared ``tau``. The pre-snap positivity defect
            ``max(0, -lambda_min)``, measured in binary64, is compared against
            it: a family further below the cone than ``tau`` is a modelling
            error and is refused rather than lifted (spec/architecture.md 2.8,
            "Positivity is the exception").
        lattice_exponent: the declared ``k``.
        site: where in the declaration the family sits.
        setting: the setting half of the record's key, where there is one.
        block: the block half of the record's key, where there is one.
        pre_snap_min_eigenvalue: the ``min_eigenvalue`` of the DECLARATION this
            family came from, when this step is one row of a larger table. The
            earlier rows have already moved the numbers, so measuring here
            would report the defect of an intermediate rather than of the
            declaration -- and a family that arrived far below the cone and was
            carried back onto it by the lattice rounding would then pass a
            ceiling it never met. :func:`snap_family_exact` passes the number
            it measured on its input; a direct caller may omit it and this
            function measures the family it was given.

    Returns:
        The family and its :class:`SnapRecord`, or the family unchanged and
        ``None`` when nothing was lifted **and** the float diagnostic agreed
        with the exact decision. When the two disagreed but no lift was needed,
        a record is returned with rule :attr:`SnapRule.DECIDED_EXACTLY` and no
        lift weight: nothing moved, but which number decided is exactly what a
        later reader of the run record needs to see.

    Raises:
        SnapRefusedError: if the pre-snap defect exceeds ``tolerance``, or if
            no rung of the ladder restores exact positivity.
        ValueError: if the family is empty, ragged, not square, not exactly
            Hermitian, or not on the declared lattice; or if ``k`` or
            ``tolerance`` is not what it should be.
    """
    admitted = _checked_tolerance(tolerance)
    exponent = _checked_lattice_exponent(lattice_exponent)
    family = _exact_family(blocks, "snap_positivity")
    _require_on_lattice(family, exponent, "snap_positivity")
    for index, element in enumerate(blocks):
        if not is_hermitian_exact(element):
            raise ValueError(
                f"snap_positivity was given an element {index} that is not "
                "exactly Hermitian; positive semidefiniteness is a property of "
                "a Hermitian operator, and the table takes the Hermitian part "
                "first (spec/architecture.md 2.9)"
            )

    smallest = (
        min(min_eigenvalue(element) for element in blocks)
        if pre_snap_min_eigenvalue is None
        else float(pre_snap_min_eigenvalue)
    )
    defect = max(0.0, -smallest)
    diagnostic: dict[str, Any] = {
        "lattice_exponent": exponent,
        "min_eigenvalue": smallest,
        "decided_by": "certiqs_key.foundations.exact_admission.is_psd_exact",
        "diagnostic": "certiqs_key.foundations.numeric.min_eigenvalue",
    }
    _admit(
        defect,
        admitted,
        SnapPredicate.POSITIVITY,
        site,
        setting,
        block,
        detail=diagnostic,
    )

    indefinite = [
        index for index, element in enumerate(blocks) if not is_psd_exact(element)
    ]
    if not indefinite:
        if smallest >= 0.0:
            return tuple(np.asarray(b).copy() for b in blocks), None
        return tuple(np.asarray(b).copy() for b in blocks), SnapRecord(
            predicate=SnapPredicate.POSITIVITY,
            rule=SnapRule.DECIDED_EXACTLY,
            site=site,
            setting=setting,
            block=block,
            defect=defect,
            tolerance=admitted,
            detail={
                **diagnostic,
                "lift_weight": None,
                "lift_exponent": None,
                "indefinite_elements": [],
                "float_diagnostic_disagreed": True,
            },
        )

    designated = designated_element_index(blocks)
    weights = dyadic_uniform_weights(len(family))
    for weight in LIFT_LADDER:
        lifted = _mix_with_dyadic_uniform(family, weight, weights)
        lifted = [_round_exact(element, exponent) for element in lifted]
        lifted, _ = _absorb_completeness(lifted, designated)
        if _is_exactly_admissible(lifted):
            snapped = _to_arrays(
                lifted,
                complex_output=_wants_complex(blocks),
                site=site,
                setting=setting,
                block=block,
                predicate=SnapPredicate.POSITIVITY,
            )
            return snapped, SnapRecord(
                predicate=SnapPredicate.POSITIVITY,
                rule=SnapRule.MIX_WITH_DYADIC_UNIFORM,
                site=site,
                setting=setting,
                block=block,
                defect=defect,
                tolerance=admitted,
                detail={
                    **diagnostic,
                    "lift_weight": str(weight),
                    "lift_exponent": weight.denominator.bit_length() - 1,
                    "indefinite_elements": indefinite,
                    "uniform_weights": [str(w) for w in weights],
                    "designated_element": designated,
                    "float_diagnostic_disagreed": smallest >= 0.0,
                },
            )

    raise SnapRefusedError(
        f"no weight of the dyadic lift ladder restores exact positivity at "
        f"{_where(site, setting, block)}; elements {indefinite} are not "
        "positive semidefinite by more than a rounding, which is a modelling "
        "error and not noise (spec/architecture.md 2.9)",
        reason="positivity_not_restored",
        predicate=SnapPredicate.POSITIVITY,
        site=site,
        setting=setting,
        block=block,
        defect=defect,
        tolerance=admitted,
        detail={
            **diagnostic,
            "indefinite_elements": indefinite,
            "ladder": [str(weight) for weight in LIFT_LADDER],
        },
    )


def _mix_with_dyadic_uniform(
    family: Sequence[ExactMatrix],
    weight: Fraction,
    weights: Sequence[Fraction],
) -> list[ExactMatrix]:
    """Return ``(1 - s) F_v + s u_v 1``, exactly, for every ``v``."""
    keep = Cx(Fraction(1) - weight, Fraction(0))
    size = len(family[0])
    out: list[ExactMatrix] = []
    for element, share in zip(family, weights, strict=True):
        lift = Cx(weight * share, Fraction(0))
        out.append(
            tuple(
                tuple(
                    keep * element[i][j] + (lift if i == j else ZERO)
                    for j in range(size)
                )
                for i in range(size)
            )
        )
    return out


def _is_exactly_admissible(family: Sequence[ExactMatrix]) -> bool:
    """Whether the exact family is exactly Hermitian, PSD and complete."""
    size = len(family[0])
    total = _exact_sum(family)
    for i in range(size):
        for j in range(size):
            expected = ONE if i == j else ZERO
            if total[i][j] != expected:
                return False
    for element in family:
        for i in range(size):
            for j in range(size):
                if element[i][j] != element[j][i].conjugate():
                    return False
    # THE ELIMINATION IS ``foundations/exact.py``'s AND IS NOT REPEATED HERE.
    # The candidate mixtures this predicate ranks are exact rationals, which
    # cannot be converted to binary64 until one of them has been accepted, and
    # the exact substrate's own
    # :func:`~certiqs_key.foundations.exact.is_positive_semidefinite` is public
    # and takes exactly this type, so no third copy of the rational ``LDL^*``
    # is carried.
    #
    # THIS IS STILL NOT THE DECISION. It only chooses which rung of the ladder
    # to stop at; :func:`~certiqs_key.foundations.exact_admission.is_psd_exact`
    # decides the family the table finally returns, through
    # :func:`verify_family_exact`, on the binary64 numbers that will be
    # declared.
    return all(is_positive_semidefinite(element) for element in family)


# ---------------------------------------------------------------------------
#  Steps exact on the lattice
# ---------------------------------------------------------------------------


def snap_column_stochasticity(
    m: Matrix,
    *,
    designated_row: int,
    lattice_exponent: int,
    tolerance: float,
    site: str,
    setting: str | None = None,
    block: str | None = None,
) -> tuple[Matrix, SnapRecord]:
    """Rescale each column of ``m`` to sum **exactly** to one, on the lattice.

    Three steps: each column is divided by its own sum, which removes the bulk
    of the defect; the whole matrix is rounded onto the ``2^-k`` lattice; and
    the exact residue ``1 - sum_r m[r, c]`` of each column -- a multiple of
    ``2^-k``, because every entry is -- is added to the **designated entry** of
    that column. Nominating the row is the caller's act: there is no natural
    absorber, and choosing one here would put a modelling decision in the
    shared-format tier.

    The post-snap column sums are **exactly** one, not one only to within
    binary64, which a float rescaling would give because it re-rounds.

    Args:
        m: the declared column-stochastic matrix, rows indexed by target
            outcome. May be rectangular. Not modified.
        designated_row: the row whose entry absorbs each column's residue.
        lattice_exponent: the declared ``k``.
        tolerance: the declared ``tau``, the ceiling on the pre-snap residue.
        site: where in the declaration ``m`` sits.
        setting: the setting half of the record's key, where there is one.
        block: the block half of the record's key, where there is one.

    Returns:
        The snapped matrix and its :class:`SnapRecord`, whose ``defect`` is the
        pre-snap :func:`~certiqs_key.foundations.numeric.column_residue` and whose
        ``detail`` names the designated row and the lattice.

    Raises:
        SnapRefusedError: if that residue exceeds ``tolerance``, if a column
            sums to zero and cannot be rescaled, if a part of an entry has
            modulus above one, or if the absorbed columns do not sum exactly to one.
        ValueError: if ``m`` is not a finite 2-D array, if ``designated_row``
            is out of range, or if ``k`` or ``tolerance`` is not what it should
            be.
    """
    admitted = _checked_tolerance(tolerance)
    exponent = _checked_lattice_exponent(lattice_exponent)
    defect = column_residue(m)
    array = checked_matrix(m, "m")
    rows = array.shape[0]
    if not 0 <= designated_row < rows:
        raise ValueError(
            f"designated_row {designated_row} is outside range({rows}); the "
            "designated entry is declared, so it must exist"
        )
    _admit(defect, admitted, SnapPredicate.COLUMN_STOCHASTICITY, site, setting, block)

    sums = array.sum(axis=0)
    zero_columns = [index for index, total in enumerate(sums) if total == 0]
    if zero_columns:
        raise SnapRefusedError(
            f"column(s) {zero_columns} of {site} sum to zero; no rescaling "
            "carries them to one, so there is nothing to snap",
            reason="degenerate_column",
            predicate=SnapPredicate.COLUMN_STOCHASTICITY,
            site=site,
            setting=setting,
            block=block,
            defect=defect,
            tolerance=admitted,
        )

    rescaled = to_exact(np.asarray(array / sums))
    _refuse_part_above_one(rescaled, "before", site, setting, block)
    rounded = [list(entries) for entries in _round_exact(rescaled, exponent)]
    for column in range(len(rounded[0])):
        residue = ONE
        for row in range(rows):
            residue = residue - rounded[row][column]
        rounded[designated_row][column] = rounded[designated_row][column] + residue
    snapped_exact = tuple(tuple(entries) for entries in rounded)
    _refuse_part_above_one(snapped_exact, "after", site, setting, block)
    _refuse_columns_not_exactly_one(snapped_exact, site, setting, block)

    snapped = np.zeros(array.shape, dtype=array.dtype)
    for i, entries in enumerate(snapped_exact):
        for j, entry in enumerate(entries):
            if not is_binary64(entry.re) or not is_binary64(entry.im):
                raise SnapRefusedError(
                    f"entry ({i}, {j}) of {_where(site, setting, block)} is not "
                    "a binary64 number after the column snap, so (D-LAT) does "
                    "not hold (spec/architecture.md 2.9)",
                    reason="not_exactly_admissible",
                    predicate=SnapPredicate.COLUMN_STOCHASTICITY,
                    site=site,
                    setting=setting,
                    block=block,
                    detail={"entry": [i, j]},
                )
            snapped[i, j] = (
                complex(float(entry.re), float(entry.im))
                if np.iscomplexobj(array)
                else float(entry.re)
            )
    return snapped, SnapRecord(
        predicate=SnapPredicate.COLUMN_STOCHASTICITY,
        rule=SnapRule.RESCALE_AND_ABSORB,
        site=site,
        setting=setting,
        block=block,
        defect=defect,
        tolerance=admitted,
        detail={
            "designated_row": designated_row,
            "columns": int(array.shape[1]),
            "lattice_exponent": exponent,
        },
    )


def _refuse_columns_not_exactly_one(
    m: ExactMatrix, site: str, setting: str | None, block: str | None
) -> None:
    """Raise unless every column of the exact matrix sums exactly to one."""
    for column in range(len(m[0])):
        total = sum((m[row][column].re for row in range(len(m))), Fraction(0))
        imaginary = sum((m[row][column].im for row in range(len(m))), Fraction(0))
        if total != 1 or imaginary != 0:
            raise SnapRefusedError(
                f"column {column} of {_where(site, setting, block)} sums to "
                f"{total} after the snap, not exactly to one",
                reason="not_exactly_admissible",
                predicate=SnapPredicate.COLUMN_STOCHASTICITY,
                site=site,
                setting=setting,
                block=block,
                detail={"column": column, "sum": str(total)},
            )


def snap_forbidden_entries(
    a: Matrix,
    entries: Sequence[tuple[int, int]],
    *,
    tolerance: float,
    site: str,
    setting: str | None = None,
    block: str | None = None,
) -> tuple[Matrix, SnapRecord]:
    """Set to zero the entries the declaration says must be zero.

    It needs no lattice argument: zero is a multiple of ``2^-k`` for every
    ``k``, so this row of the table is exact.

    The forbidden set is the caller's -- this module never infers which entries
    "should" vanish, because an inferred zero is a structural claim and the
    shared-format tier is not entitled to make one.

    **Order matters, and it is the caller's to get right.** Zeroing an entry of
    a Hermitian operator without zeroing its mirror breaks Hermiticity, and
    :func:`snap_family_exact` re-establishes Hermiticity, the lattice and
    completeness after this row rather than before it -- so a family carrying a
    forbidden set is snapped here first and handed to the entry point
    afterwards. The completeness absorb may re-introduce a forbidden entry on
    the **designated element**; a caller with both a forbidden set and a family
    re-checks its own forbidden entries after
    :func:`snap_family_exact` returns. This table does not adjudicate between a
    structural zero and exact completeness, because only the declaration knows
    which of them it means.

    Args:
        a: the declared operator. Not modified.
        entries: the ``(row, column)`` positions the declaration forbids.
        tolerance: the declared ``tau``, the ceiling on the pre-snap modulus.
        site: where in the declaration ``a`` sits.
        setting: the setting half of the record's key, where there is one.
        block: the block half of the record's key, where there is one.

    Returns:
        The snapped operator and its :class:`SnapRecord`, whose ``defect`` is
        the LARGEST pre-snap modulus over the named entries -- the number the
        tolerance decides -- and whose ``detail`` names the worst entry and how
        many were zeroed.

    Raises:
        SnapRefusedError: if any named entry's modulus exceeds ``tolerance``.
        ValueError: if ``a`` is not a finite 2-D array, if ``entries`` is empty
            or names a position outside it, or if ``tolerance`` is not a
            tolerance.
    """
    admitted = _checked_tolerance(tolerance)
    array = checked_matrix(a, "a")
    if not entries:
        raise ValueError(
            "snap_forbidden_entries was given no entries; a snap of nothing is "
            "a record of a repair that did not happen"
        )
    rows, columns = array.shape
    for row, column in entries:
        if not (0 <= row < rows and 0 <= column < columns):
            raise ValueError(
                f"forbidden entry ({row}, {column}) is outside an array of "
                f"shape {(rows, columns)}"
            )

    moduli = {(row, column): float(abs(array[row, column])) for row, column in entries}
    worst = max(moduli, key=lambda position: moduli[position])
    defect = moduli[worst]
    _admit(defect, admitted, SnapPredicate.FORBIDDEN_ENTRY, site, setting, block)

    snapped = array.copy()
    for row, column in entries:
        snapped[row, column] = 0
    return snapped, SnapRecord(
        predicate=SnapPredicate.FORBIDDEN_ENTRY,
        rule=SnapRule.ZEROED,
        site=site,
        setting=setting,
        block=block,
        defect=defect,
        tolerance=admitted,
        detail={"entries": len(moduli), "worst_entry": [worst[0], worst[1]]},
    )


# ---------------------------------------------------------------------------
#  The last step -- verification, and the entry point that runs the table
# ---------------------------------------------------------------------------


def verify_family_exact(
    blocks: Sequence[Matrix],
    *,
    site: str,
    setting: str | None = None,
    block: str | None = None,
    lattice_exponent: int | None = None,
) -> ExactAdmission:
    """Decide exact admissibility of a family, and refuse if it fails.

    The five conditions of a consumer's admission (spec/architecture.md 2.9), less the
    sector map, which is metadata this module never sees: exact Hermiticity,
    exact positive semidefiniteness, exact completeness, and condition (S) --
    that the completeness sum **in the declared order** rounds nowhere in
    binary64. (S) is decided here, last, and never earlier: the completeness
    absorb and the positivity lift both change partial sums from the touched
    element onward, and "sums exactly to the identity" is strictly weaker than
    "every partial sum is on the lattice" (spec/architecture.md 2.9, constraint (2)).

    A producer calls this on what it is about to emit -- (D-EMIT) (ii) to (v)
    -- and refuses rather than emitting. It is also what
    :func:`snap_family_exact` runs on its own result: a snap that returned a
    family it had not verified would be asserting the one thing its caller
    cannot check for itself.

    Args:
        blocks: the family ``{F_v}_v`` on one sector, in the declared order.
        site: where in the declaration the family sits.
        setting: the setting half of the refusal's key, where there is one.
        block: the block half of the refusal's key, where there is one.
        lattice_exponent: when given, (D-LAT) is decided as well.

    Returns:
        The :class:`~certiqs_key.foundations.exact_admission.ExactAdmission` of the
        family, whose ``admissible`` is then necessarily ``True``.

    Raises:
        SnapRefusedError: if any condition fails. ``reason`` is
            ``not_exactly_admissible``; ``predicate`` names the first failed
            condition and ``detail`` names all of them, with the first inexact
            addition of condition (S) where that is what failed.
        ValueError: if the family is empty or ragged.
        certiqs_key.foundations.exact_admission.ExactInputError: if an entry is
            not finite.
    """
    if lattice_exponent is not None:
        exponent = _checked_lattice_exponent(lattice_exponent)
        off = [
            index
            for index, element in enumerate(blocks)
            if not is_on_lattice(element, lattice_exponent=exponent)
        ]
        if off:
            raise SnapRefusedError(
                f"elements {off} of {_where(site, setting, block)} are not on "
                f"the 2^-{exponent} lattice, so (D-LAT) does not hold and the "
                "declared numbers are not binary64 by construction "
                "(spec/architecture.md 2.9)",
                reason="not_exactly_admissible",
                predicate=SnapPredicate.LATTICE,
                site=site,
                setting=setting,
                block=block,
                detail={"failures": ["lattice"], "off_lattice_elements": off},
            )

    rounds_nowhere = sum_rounds_nowhere(blocks)
    admission = admit_family_exact(blocks)
    if admission.admissible:
        return admission

    first = admission.failures[0]
    predicate = {
        "hermiticity": SnapPredicate.HERMITICITY,
        "positivity": SnapPredicate.POSITIVITY,
        "completeness": SnapPredicate.COMPLETENESS,
        "declared_order_sum": SnapPredicate.DECLARED_ORDER_SUM,
    }[first]
    raise SnapRefusedError(
        f"the family at {_where(site, setting, block)} is not exactly "
        f"admissible: {', '.join(admission.failures)} "
        "(spec/architecture.md 2.9; meat-core def:declaration, its "
        "exact-admissibility paragraph and eq:declorder)",
        reason="not_exactly_admissible",
        predicate=predicate,
        site=site,
        setting=setting,
        block=block,
        detail={
            "failures": list(admission.failures),
            "admission": admission.as_record(),
            "rounds_nowhere": rounds_nowhere.as_record(),
        },
    )


def snap_family_exact(
    blocks: Sequence[Matrix],
    *,
    tolerance: float,
    lattice_exponent: int,
    site: str,
    setting: str | None = None,
    block: str | None = None,
) -> tuple[tuple[Matrix, ...], tuple[SnapRecord, ...]]:
    """Run the whole family table on ONE sector block's family (2.9).

    A snap in the sense of ``foundations/def:snap`` with constant ``1``: the
    returned family has the input's shape, lies on the ``2^-k`` lattice, is
    exactly admissible, and its displacement is recorded. It serves data other
    than a measurement family -- the probability vectors the instances and the
    run tier's input preparation declare -- unchanged.

    **Not for a measurement family.** Its Positivity row mixes every element
    with a uniform family and its Completeness row places the residue whatever
    the receiving element's structural support, which
    ``foundations/req:support-safe-snap`` forbids for a measurement family
    except as a flagged last resort; a measurement family is snapped by
    :func:`snap_measurement_family` (``instances/common/declare.py``).

    Hermitian part, lattice, completeness, positivity -- and then, last, the
    rounds-nowhere check and the full exact admission. What comes back is
    **exactly admissible as binary64 data** or nothing comes back at all.

    The two remaining rows of the table, column-stochasticity and forbidden
    entries, act on different objects -- a channel matrix, and an operator
    whose declaration names structural zeros -- and are
    :func:`snap_column_stochasticity` and :func:`snap_forbidden_entries`, which
    a caller applies itself. See :func:`snap_forbidden_entries` on the order.

    Every pre-snap defect is measured on the **input**, in binary64, by
    :mod:`certiqs_key.foundations.numeric`, and compared against ``tolerance`` before
    anything moves: Hermiticity and completeness as entrywise maximum moduli,
    positivity as ``max(0, -lambda_min)`` against the spectral floor
    (spec/architecture.md 2.8). A defect above ``tau`` is a modelling error
    and is refused, never snapped.

    **A record is returned for every step that changed something**, and for two
    steps that may not have: a completeness step whose pre-snap residue was
    non-zero, because the lattice rounding often closes the residue by itself
    and a reader still needs to see which element was designated to carry it;
    and a positivity step whose float diagnostic disagreed with the exact
    decision, which is the disagreement spec/architecture.md 2.9 constraint (4)
    exists to make visible. The run record carries all of them.

    Args:
        blocks: the family ``{F_v}_v`` on one sector, in the declared order.
            The order is part of the datum: condition (S) is stated in it. Not
            modified.
        tolerance: the declared ``tau``, the ceiling on the pre-snap defect.
        lattice_exponent: the declared ``k``. No default (spec/architecture.md 2.9); the
            measured recommendation is ``40``.
        site: where in the declaration the family sits.
        setting: the setting half of the records' key, where there is one.
        block: the block half of the records' key, where there is one.

    Returns:
        The snapped family, in the order it was given, and the records of the
        steps that changed something. Every record carries, in ``detail``,
        the displacement of the whole snap of ``foundations/def:snap``, the
        largest entrywise modulus of the returned family minus the input
        (``snap_displacement``, and its exact square
        ``snap_displacement_squared``). A snap that returns no record moved
        nothing, since every step that moves an entry records itself, so its
        displacement is 0.

    Raises:
        SnapRefusedError: if a pre-snap defect exceeds ``tolerance``, if
            (D-LAT)'s modulus condition fails, if every element is structurally
            zero, if no rung of the lift ladder restores exact positivity, or
            if the final exact verification fails.
        ValueError: if the family is empty, ragged or not square, or if ``k``
            or ``tolerance`` is not what it should be.
    """
    admitted = _checked_tolerance(tolerance)
    exponent = _checked_lattice_exponent(lattice_exponent)
    original = [
        checked_matrix(element, f"blocks[{index}]").copy()
        for index, element in enumerate(blocks)
    ]
    _exact_family(original, "snap_family_exact")
    records: list[SnapRecord] = []

    # --- Hermiticity, measured on the input and restored exactly ------------
    hermiticity = max(hermiticity_defect(element) for element in original)
    _admit(hermiticity, admitted, SnapPredicate.HERMITICITY, site, setting, block)
    hermitian = [_hermitian_part_exact(element) for element in original]
    if any(
        not np.array_equal(before, after)
        for before, after in zip(original, hermitian, strict=True)
    ):
        records.append(
            SnapRecord(
                predicate=SnapPredicate.HERMITICITY,
                rule=SnapRule.HERMITIAN_PART,
                site=site,
                setting=setting,
                block=block,
                defect=hermiticity,
                tolerance=admitted,
                detail={"elements": len(original), "exactly_hermitian": True},
            )
        )

    # --- Completeness and positivity, measured on the INPUT -----------------
    #
    # Both ceilings are read off the declaration and not off an intermediate.
    # It matters for positivity in particular: the lattice rounding can carry a
    # badly indefinite family back onto the cone, and measuring afterwards
    # would let a modelling error through a ceiling it never met.
    completeness = completeness_residue(original)
    _admit(completeness, admitted, SnapPredicate.COMPLETENESS, site, setting, block)
    smallest = min(min_eigenvalue(element) for element in original)
    _admit(
        max(0.0, -smallest),
        admitted,
        SnapPredicate.POSITIVITY,
        site,
        setting,
        block,
        detail={
            "min_eigenvalue": smallest,
            "decided_by": "certiqs_key.foundations.exact_admission.is_psd_exact",
            "diagnostic": "certiqs_key.foundations.numeric.min_eigenvalue",
        },
    )

    # --- Lattice ------------------------------------------------------------
    exact = _exact_family(hermitian, "snap_family_exact")
    for element in exact:
        _refuse_part_above_one(element, "before", site, setting, block)
    rounded = [_round_exact(element, exponent) for element in exact]
    for element in rounded:
        _refuse_part_above_one(element, "after", site, setting, block)
    displacement = 0.0
    moved = 0
    for before, after in zip(exact, rounded, strict=True):
        for i, row in enumerate(after):
            for j, entry in enumerate(row):
                if entry != before[i][j]:
                    moved += 1
                gap = float((entry - before[i][j]).squared_modulus) ** 0.5
                displacement = max(displacement, gap)
    if moved:
        records.append(
            SnapRecord(
                predicate=SnapPredicate.LATTICE,
                rule=SnapRule.ROUND_TO_LATTICE,
                site=site,
                setting=setting,
                block=block,
                defect=displacement,
                tolerance=admitted,
                detail={
                    "lattice_exponent": exponent,
                    "displacement": displacement,
                    "entries_moved": moved,
                    "elements": len(rounded),
                },
            )
        )

    # --- Completeness, absorbed into the designated element -----------------
    complex_output = _wants_complex(original)
    on_lattice = _to_arrays(
        rounded,
        complex_output=complex_output,
        site=site,
        setting=setting,
        block=block,
        predicate=SnapPredicate.LATTICE,
    )
    designated = designated_element_index(on_lattice)
    absorbed, residue_entries = _absorb_completeness(rounded, designated)
    _refuse_part_above_one(absorbed[designated], "after", site, setting, block)
    # A record whenever completeness was defective on the input OR the absorb
    # moved an entry. The first disjunct matters: the lattice rounding often
    # closes the residue by itself, so the absorb moves nothing -- and a reader
    # of the run record still needs to see WHICH element was designated to
    # carry it, and that the family the run declares is exactly complete
    # because of this table and not by luck. ``residue_entries_moved == 0``
    # with a non-zero ``pre_snap_defect`` says exactly that.
    if residue_entries or completeness != 0.0:
        records.append(
            SnapRecord(
                predicate=SnapPredicate.COMPLETENESS,
                rule=SnapRule.ABSORB_INTO_DESIGNATED_ELEMENT,
                site=site,
                setting=setting,
                block=block,
                defect=completeness,
                tolerance=admitted,
                detail={
                    "elements": len(absorbed),
                    "lattice_exponent": exponent,
                    "designated_element": designated,
                    "designated_element_trace": str(_exact_trace(rounded[designated])),
                    "residue_entries_moved": residue_entries,
                },
            )
        )
    closed = _to_arrays(
        absorbed,
        complex_output=complex_output,
        site=site,
        setting=setting,
        block=block,
        predicate=SnapPredicate.COMPLETENESS,
    )

    # --- Positivity, decided exactly ---------------------------------------
    lifted, positivity_record = snap_positivity(
        closed,
        tolerance=admitted,
        lattice_exponent=exponent,
        site=site,
        setting=setting,
        block=block,
        pre_snap_min_eigenvalue=smallest,
    )
    if positivity_record is not None:
        records.append(positivity_record)

    # --- Last: (S), and the whole exact admission ---------------------------
    verify_family_exact(
        lifted,
        site=site,
        setting=setting,
        block=block,
        lattice_exponent=exponent,
    )
    # --- The displacement of the snap, foundations/def:snap -----------------
    #
    # "The largest entrywise modulus of D' - D, taken over every block of every
    # element": from the INPUT to the RETURNED family, so the Hermitian-part
    # move, the lattice rounding, the completeness absorb and the positivity
    # lift are all in it. The lattice record's own ``displacement`` is that one
    # step's move from the Hermitian part and stays what it is; this number is
    # the snap's, and every record of this call carries it.
    squared = _displacement_squared(original, lifted)
    whole = {
        "snap_displacement": float(squared) ** 0.5,
        "snap_displacement_squared": str(squared),
    }
    return lifted, tuple(
        replace(record, detail={**record.detail, **whole}) for record in records
    )


def _displacement_squared(
    before: Sequence[Matrix], after: Sequence[Matrix]
) -> Fraction:
    """Return ``max |after - before|^2`` over every entry of every element, exactly.

    Both families are binary64 arrays and are read as the rationals they are;
    the square is exact, and its root is the displacement of
    ``foundations/def:snap``.
    """
    worst = Fraction(0)
    for old, new in zip(before, after, strict=True):
        for old_row, new_row in zip(to_exact(old), to_exact(new), strict=True):
            for old_entry, new_entry in zip(old_row, new_row, strict=True):
                worst = max(worst, (new_entry - old_entry).squared_modulus)
    return worst


# ===========================================================================
#  THE MEASUREMENT-FAMILY SNAP: KEPT, OR MOVED AND DISCLOSED
#
#  ``foundations/def:snap``, ``req:snap-reference``, ``req:support-safe-snap``
#  and ``req:who-snaps``; spec/architecture.md 2.9, "A measurement family is
#  kept where it is known exactly on the lattice and moved elsewhere".
#
#  No claim relates a snapped family to the model it replaced, so the soundness
#  of a run never rests on the snap where the run can avoid reading it: a run
#  that holds a reference of the family hands it beside the snap
#  (``def:evaluated-off-snap`` (i)) and evaluates its first-order bound with the
#  reference in place of the snap (``meat-core/frank-wolfe/
#  req:bracket-on-reference``). The snap therefore aims at fidelity and at
#  nothing else. Each BLOCK is KEPT, where an exact reference of it is a lattice
#  family passing its last decisions, and rests on nothing; or it is MOVED by
#  the one support-safe procedure (the rows of spec/architecture.md 2.9), on
#  the centres of its exact reference or on the data, and rests on
#  ``foundations/ass:snapped-measurement`` (A-SNAP) unless the run evaluates
#  it off its snap. A moved block on which no reference is handed rests on
#  A-SNAP whatever the run does, in the group ``no usable reference`` (or
#  ``last resort``); which handed moved blocks rest is the run's decision
#  (:mod:`certiqs_key.runs.direct_route`). A strict run refuses wherever a
#  block would rest. The uniform lift survives only as the flagged last resort
#  (``support_not_preserved``).
# ===========================================================================

#: The assumption a run rests on where a moved block is not evaluated off its
#: snap (``req:snap-reference`` (iii)), and its ledger key
#: (``spec/modules/foundations/interface.yaml``).
ASSUMPTION_ID: Final[str] = "A-SNAP"
ASSUMPTION_MACHINE_KEY: Final[str] = "snapped_measurement"
ASSUMPTION_CLAIM: Final[str] = "foundations/ass:snapped-measurement"


class BlockStatus(StrEnum):
    """What the snap of a measurement family did on one block (``def:snap``)."""

    #: The snap is decided exactly to equal the data it is made from: the
    #: centres of an exact reference that is a lattice family, or data stated
    #: with no model behind them that the procedure leaves unchanged.
    KEPT = "kept"
    #: Every other block: made by the procedure or its last resort.
    MOVED = "moved"


class SnapStep(StrEnum):
    """A step of the procedure that made a block's snap (``req:who-snaps``)."""

    KEEP = "keep"
    DECIDE_LAST = "decide-last"
    HERMITIAN_PART = "hermitian-part"
    LATTICE = "lattice"
    COMPLETENESS_PER_ENTRY = "completeness-per-entry"
    COORDINATE_LIFT = "coordinate-lift"
    UNIFORM_LIFT_LAST_RESORT = "uniform-lift-last-resort"


@dataclass(frozen=True)
class SnapSettings:
    """The two run options a measurement-family snap reads (``req:snap-reference``).

    * ``reference_enclosure`` -- default on; off declares that enclosed
      references are not used, so that only the blocks of a reference every
      radius of which is zero are handed (``req:snap-reference`` (i));
    * ``strict`` -- the run option ``strict_snaps``, default off; on,
      the run refuses wherever a moved block would rest on A-SNAP
      (``req:snap-reference`` (iv)).

    Both are recorded with every snap (``req:who-snaps``).
    """

    reference_enclosure: bool = True
    strict: bool = False

    def __post_init__(self) -> None:
        """Refuse a setting that is not a boolean."""
        flags = (self.reference_enclosure, self.strict)
        if not all(isinstance(flag, bool) for flag in flags):
            raise ValueError("reference_enclosure and strict are booleans")

    def as_record(self) -> dict[str, object]:
        """JSON-ready, under the run options' names."""
        return {
            "reference_enclosure": self.reference_enclosure,
            "strict_snaps": self.strict,
        }


@dataclass(frozen=True)
class HandedBlock:
    """The reference handed beside the snap on one block (``def:evaluated-off-snap``).

    ``foundations/req:who-snaps``: the kind of the reference handed
    (``exact``, every radius zero, or ``enclosed``), the largest radius of the
    block and the largest radius of the enclosures of the irrational inputs
    from which the constructing module computed the centres (``None`` where it
    states none). ``block`` is the reference block itself, which the declarer
    passes on unaltered.
    """

    block: ReferenceBlock

    @property
    def kind(self) -> ReferenceKind:
        """``exact`` or ``enclosed``."""
        return self.block.kind

    @property
    def largest_radius(self) -> Fraction:
        """The largest radius of the block."""
        return max(element.largest_radius for element in self.block.elements)

    def as_record(self) -> dict[str, object]:
        """JSON-ready: exact rationals as strings."""
        radius = self.block.input_radius
        return {
            "kind": str(self.kind),
            "largest_radius": str(self.largest_radius),
            "input_radius": None if radius is None else str(radius),
        }


@dataclass(frozen=True)
class BlockSnapRecord:
    """The record of one block of a measurement-family snap (``req:who-snaps``).

    Per block: the status, kept or moved; the reference kind the snap ran on
    (``exact``, the centres of an exact reference, or ``none``, the data); the
    reference handed beside the snap, or the cause of a block on which none is
    handed (``req:snap-reference`` (iii)(a)); the steps of the procedure; any
    lift weight; the ``support_not_preserved`` flag of the last resort; and the
    displacement from the data the snap was made from (the centres, where it
    ran on them).

    Whether a moved block on which a reference is handed rests on A-SNAP is
    decided by the run after its search; :attr:`rests_on_assumption` is the
    part decided here: a moved block on which no reference is handed rests on
    it whatever the run does.
    """

    block: str
    status: BlockStatus
    reference_kind: ReferenceKind
    handed: HandedBlock | None = None
    cause: RestingCause | None = None
    steps: tuple[SnapStep, ...] = ()
    lift_weight: Fraction | None = None
    support_not_preserved: bool = False
    displacement_squared: Fraction = Fraction(0)
    pre_snap: Mapping[str, float] = field(default_factory=dict)
    defects_ground: str = "measured"
    residue_placement: tuple[tuple[int, int, str], ...] = ()

    @property
    def moved(self) -> bool:
        """Whether the block is moved (``def:snap``)."""
        return self.status is BlockStatus.MOVED

    @property
    def rests_on_assumption(self) -> bool:
        """Whether the block rests on A-SNAP whatever the run does.

        A moved block on which no reference is handed: nothing the run can do
        evaluates it off its snap (``def:evaluated-off-snap`` (ii)).
        """
        return self.moved and self.handed is None

    @property
    def group(self) -> RestingGroup | None:
        """The group of a block that rests here (``req:snap-reference`` (iii))."""
        if not self.rests_on_assumption:
            return None
        return resting_group(self.cause, last_resort=self.support_not_preserved)

    @property
    def fix(self) -> str | None:
        """The fix of the cause, with the device's noise for a last-resort block."""
        if not self.rests_on_assumption:
            return None
        return resting_fix(self.cause, last_resort=self.support_not_preserved)

    @property
    def group_fix(self) -> str | None:
        """The fix of the block's group; the cause's fix details it."""
        group = self.group
        return None if group is None else group.fix(self.cause)

    @property
    def displacement(self) -> float:
        """The displacement of ``foundations/def:snap``, as a float diagnostic."""
        return math.sqrt(float(self.displacement_squared))

    def as_record(self) -> dict[str, object]:
        """JSON-ready: exact rationals as strings, never floats."""
        handed = self.handed
        return {
            "block": self.block,
            "status": str(self.status),
            "reference_kind": str(self.reference_kind),
            "handed_reference": None if handed is None else handed.as_record(),
            "handed_reference_kind": None if handed is None else str(handed.kind),
            "cause": None if self.cause is None else str(self.cause),
            "group": None if self.group is None else str(self.group),
            "fix": self.fix,
            "group_fix": self.group_fix,
            "steps": [str(step) for step in self.steps],
            "lift_weight": None if self.lift_weight is None else str(self.lift_weight),
            "support_not_preserved": self.support_not_preserved,
            "rests_on_assumption": self.rests_on_assumption,
            "displacement": self.displacement,
            "displacement_squared": str(self.displacement_squared),
            "pre_snap": dict(self.pre_snap),
            "defects_ground": self.defects_ground,
            "residue_placement": [list(entry) for entry in self.residue_placement],
            "decided_by": "certiqs_key.foundations.exact.is_positive_semidefinite",
        }


@dataclass(frozen=True)
class MeasurementSnapRecord:
    """The record of one measurement-family snap (``foundations/req:who-snaps``).

    Implements the record of ``foundations/req:who-snaps`` for an operator
    family read as a measurement: the run's two snap settings; the identity of
    the reference where one is held, and why it is not used where it is not;
    per block a :class:`BlockSnapRecord`; and the blocks that rest on A-SNAP
    whatever the run does, which the run's manifest names
    (``req:snap-reference`` (iii)).
    """

    site: str
    setting: str | None
    alphabet: tuple[str, ...]
    lattice_exponent: int
    constant: Fraction
    declared_tolerance: float
    settings: SnapSettings
    blocks: tuple[BlockSnapRecord, ...]
    cause: RestingCause | None = None
    reference: Mapping[str, object] | None = None
    reference_failures: tuple[str, ...] = ()

    @property
    def moved_blocks(self) -> tuple[str, ...]:
        """The moved blocks, in the order they were snapped."""
        return tuple(b.block for b in self.blocks if b.moved)

    @property
    def handed_blocks(self) -> tuple[str, ...]:
        """The blocks on which the reference is handed beside the snap."""
        return tuple(b.block for b in self.blocks if b.handed is not None)

    @property
    def resting_blocks(self) -> tuple[str, ...]:
        """The blocks that rest on A-SNAP whatever the run does."""
        return tuple(b.block for b in self.blocks if b.rests_on_assumption)

    @property
    def support_not_preserved_blocks(self) -> tuple[str, ...]:
        """The blocks the last resort snapped, flagged ``support_not_preserved``."""
        return tuple(b.block for b in self.blocks if b.support_not_preserved)

    @property
    def assumption(self) -> dict[str, object] | None:
        """Return the manifest entry A-SNAP naming its blocks, or ``None``."""
        resting = self.resting_blocks
        if not resting:
            return None
        return {
            "id": ASSUMPTION_ID,
            "machine_key": ASSUMPTION_MACHINE_KEY,
            "claim": ASSUMPTION_CLAIM,
            "site": self.site,
            "setting": self.setting,
            "blocks": list(resting),
        }

    def as_record(self) -> dict[str, object]:
        """JSON-ready."""
        return {
            "site": self.site,
            "setting": self.setting,
            "alphabet": list(self.alphabet),
            "lattice_exponent": self.lattice_exponent,
            "constant": str(self.constant),
            "declared_tolerance": self.declared_tolerance,
            "run_settings": self.settings.as_record(),
            "cause": None if self.cause is None else str(self.cause),
            "fix": None if self.cause is None else self.cause.fix,
            "reference": None if self.reference is None else dict(self.reference),
            "reference_failures": list(self.reference_failures),
            "blocks": [block.as_record() for block in self.blocks],
            "moved_blocks": list(self.moved_blocks),
            "handed_blocks": list(self.handed_blocks),
            "resting_blocks": list(self.resting_blocks),
            "support_not_preserved_blocks": list(self.support_not_preserved_blocks),
            "assumption": self.assumption,
        }


@dataclass(frozen=True)
class MeasurementSnap:
    """A snapped measurement family, exact and on the lattice, with its record.

    ``handed`` is the reference the declarer hands beside the snap, per block
    label, unaltered (``foundations/def:evaluated-off-snap`` (i)).
    """

    blocks: Mapping[str, tuple[ExactMatrix, ...]]
    record: MeasurementSnapRecord
    handed: Mapping[str, ReferenceBlock] = field(default_factory=dict)

    def arrays(self) -> dict[str, tuple[Matrix, ...]]:
        """Return every block as ``complex128`` arrays -- an exact conversion.

        Every entry is a lattice value at ``k <= 53`` and hence a binary64
        number (``foundations/lem:binary64-lattice``); a value that is not is
        refused rather than rounded.
        """
        out: dict[str, tuple[Matrix, ...]] = {}
        for label, family in self.blocks.items():
            out[label] = _to_arrays(
                family,
                complex_output=True,
                site=self.record.site,
                setting=self.record.setting,
                block=label,
                predicate=SnapPredicate.LATTICE,
            )
        return out



# ---------------------------------------------------------------------------
#  Exact helpers of the measurement-family snap
# ---------------------------------------------------------------------------


def _is_zero_matrix(m: ExactMatrix) -> bool:
    """Whether every entry vanishes exactly."""
    return all(entry.is_zero for row in m for entry in row)


def _hermitian_part(m: ExactMatrix) -> ExactMatrix:
    """Return ``(m + m^dag) / 2``, exactly."""
    n = len(m)
    return tuple(
        tuple((m[i][j] + m[j][i].conjugate()).over(Fraction(2)) for j in range(n))
        for i in range(n)
    )


def _real_trace(m: ExactMatrix) -> Fraction:
    """Return the real part of the exact trace."""
    return sum((m[i][i].re for i in range(len(m))), Fraction(0))


def _numeric_support(m: ExactMatrix) -> frozenset[int]:
    """Return the structural support of a matrix given as numbers (def:snap).

    An entry is structurally zero exactly when it is the number zero; index
    ``i`` lies in the support when row ``i`` or column ``i`` holds a non-zero
    entry.
    """
    n = len(m)
    return frozenset(
        i
        for i in range(n)
        if any(not m[i][j].is_zero or not m[j][i].is_zero for j in range(n))
    )


def _completeness_residue(
    family: Sequence[ExactMatrix], constant: Fraction
) -> ExactMatrix:
    """Return ``c 1 - sum_j F_j``, exactly."""
    total = _exact_sum(family)
    c = Cx(constant, Fraction(0))
    return tuple(
        tuple((c - entry) if i == j else (ZERO - entry) for j, entry in enumerate(row))
        for i, row in enumerate(total)
    )


def _all_psd(family: Sequence[ExactMatrix]) -> bool:
    """Whether every element is Hermitian and positive semidefinite, exactly."""
    return all(is_hermitian(m) and is_positive_semidefinite(m) for m in family)


def _first_largest(candidates: Sequence[int], traces: Sequence[Fraction]) -> int:
    """Return the candidate of largest trace, the first in declared order."""
    best = candidates[0]
    for index in candidates[1:]:
        if traces[index] > traces[best]:
            best = index
    return best


def _displacement_squared_exact(
    before: Sequence[ExactMatrix], after: Sequence[ExactMatrix]
) -> Fraction:
    """Return ``max |after - before|^2`` over every entry, exactly."""
    worst = Fraction(0)
    for old, new in zip(before, after, strict=True):
        for old_row, new_row in zip(old, new, strict=True):
            for old_entry, new_entry in zip(old_row, new_row, strict=True):
                worst = max(worst, (new_entry - old_entry).squared_modulus)
    return worst


def decide_last(
    family: Sequence[ExactMatrix], constant: Fraction, lattice_exponent: int
) -> tuple[str, ...]:
    """Decide exact admissibility at ``c`` and the lattice condition, last.

    ``foundations/req:snap-reference`` (ii) and the last row of the table of
    spec/architecture.md 2.9: exact Hermiticity, exact positive
    semidefiniteness, completeness at ``c`` as an identity of the numbers,
    the lattice condition at ``k`` (``req:declared-lattice``, part by part),
    and -- on lattice data, whose entries are binary64 numbers -- that the
    completeness sum in the declared order rounds nowhere
    (``foundations/def:exact-admissibility``). Returns the conditions that
    fail, empty when the family is admissible.
    """
    failures: list[str] = []
    if not all(is_hermitian(m) for m in family):
        failures.append("hermiticity")
    elif not all(is_positive_semidefinite(m) for m in family):
        failures.append("positivity")
    if not is_complete_at(family, constant):
        failures.append("completeness")
    if not all(on_lattice(m, lattice_exponent) for m in family):
        failures.append("lattice")
    elif not exact_sum_rounds_nowhere(family).ok:
        failures.append("declared_order_sum")
    return tuple(failures)


# ---------------------------------------------------------------------------
#  req:support-safe-snap: the procedure that moves a block, and its last resort
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SupportSafeSnap:
    """The snap of one moved block by the rows of spec/architecture.md 2.9.

    ``family`` is ``None`` only where not even the last resort restored the
    conditions. ``support_not_preserved`` flags the last resort
    (``req:support-safe-snap`` (iv)); ``failure`` names what the support-safe
    rows could not restore (``completeness`` or ``positivity``) when it ran.
    ``residue_placement`` lists ``(i, l, outcome)`` for every residue entry
    placed; the last resort places the whole residue, recorded ``(-1, -1, v)``.
    """

    family: tuple[ExactMatrix, ...] | None
    steps: tuple[SnapStep, ...]
    lift_weight: Fraction | None
    support_not_preserved: bool
    residue_placement: tuple[tuple[int, int, int], ...]
    failure: str | None


def _absorb_per_entry(
    family: Sequence[ExactMatrix],
    supports: Sequence[frozenset[int]],
    traces: Sequence[Fraction],
    constant: Fraction,
) -> tuple[tuple[ExactMatrix, ...], tuple[tuple[int, int, int], ...]] | None:
    """Absorb ``c 1 - sum_v F_v`` entry by entry, support-safely.

    The Completeness row for a measurement family: a diagonal entry ``(i,i)``,
    and an off-diagonal pair ``(i,m), (m,i)``, each into the element of
    largest trace, the first in the declared order, whose structural support
    contains ``i`` and ``m`` (``req:support-safe-snap`` (iii)). ``None`` where
    some non-zero entry has no such element.
    """
    residue = _completeness_residue(family, constant)
    work = [[list(row) for row in element] for element in family]
    placements: list[tuple[int, int, int]] = []
    size = len(residue)
    for i in range(size):
        for m in range(i, size):
            if residue[i][m].is_zero and residue[m][i].is_zero:
                continue
            eligible = [
                v for v, support in enumerate(supports) if i in support and m in support
            ]
            if not eligible:
                return None
            v = _first_largest(eligible, traces)
            work[v][i][m] = work[v][i][m] + residue[i][m]
            if m != i:
                work[v][m][i] = work[v][m][i] + residue[m][i]
            placements.append((i, m, v))
    return tuple(tuple(tuple(row) for row in element) for element in work), tuple(
        placements
    )


def _coordinate_family(
    data: Sequence[ExactMatrix], constant: Fraction
) -> tuple[ExactMatrix, ...] | None:
    """Return the coordinate family ``T_v = c diag(d_v) diag(sum_w d_w)^-1``.

    ``d_v(i) = max(Re D_v(i,i), 0)``: diagonal, non-negative, complete at
    ``c``, and non-zero only on coordinates of the structural support of
    ``D_v`` -- the mixture ``req:support-safe-snap`` (ii) admits. ``None``
    where some coordinate has ``sum_w d_w(i) = 0``, so that no such family is
    complete.
    """
    size = len(data[0])
    weights = [[max(m[i][i].re, Fraction(0)) for i in range(size)] for m in data]
    totals = [sum((w[i] for w in weights), Fraction(0)) for i in range(size)]
    if any(total == 0 for total in totals):
        return None
    return tuple(
        tuple(
            tuple(
                Cx(constant * w[i] / totals[i], Fraction(0)) if i == j else ZERO
                for j in range(size)
            )
            for i in range(size)
        )
        for w in weights
    )


def _mix(
    family: Sequence[ExactMatrix], other: Sequence[ExactMatrix], weight: Fraction
) -> list[ExactMatrix]:
    """Return ``(1 - w) E_v + w T_v`` for every ``v``, exactly."""
    keep = Cx(Fraction(1) - weight, Fraction(0))
    share = Cx(weight, Fraction(0))
    return [
        tuple(
            tuple(keep * a + share * b for a, b in zip(row_e, row_t, strict=True))
            for row_e, row_t in zip(e, t, strict=True)
        )
        for e, t in zip(family, other, strict=True)
    ]


def support_safe_snap_block(
    data: Sequence[ExactMatrix],
    *,
    supports: Sequence[frozenset[int]],
    traces: Sequence[Fraction],
    constant: Fraction,
    lattice_exponent: int,
) -> SupportSafeSnap:
    """Snap one block of a measurement family by the support-safe rows.

    Implements ``foundations/req:support-safe-snap`` (i)-(iv) through the
    table of spec/architecture.md 2.9 "Step (every moved block of a
    measurement family, and data other than a measurement family)":

    * Hermiticity: the Hermitian part ``(a + a^dag)/2``, exact;
    * Lattice: every part to the nearest multiple of ``2^-k``, ties to even;
      a zero stays zero, so nothing structurally zero is revived;
    * Completeness: the residue absorbed entry by entry, each into an element
      whose structural support holds it (:func:`_absorb_per_entry`);
    * Positivity, decided exactly: a failing block is mixed with its
      coordinate family (:func:`_coordinate_family`) at the smallest weight of
      :data:`LIFT_LADDER` that restores exact positivity, the Lattice and
      Completeness rows run again and completeness re-checked exactly;
    * the last resort of item (iv), where those rows cannot restore the
      conditions: the uniform lift with the dyadic uniform family
      ``U_v = u_v c 1`` at the smallest weight of the same ladder that
      restores them, the residue then placed into the designated element of
      largest trace without the structural-support condition, the block
      flagged ``support_not_preserved``.

    The caller decides the result last (:func:`decide_last`).

    Args:
        data: the block's family ``D``: the binary64 data as exact rationals,
            or the centres of a reference, in the declared order.
        supports: the structural support of each ``D_v`` (``def:snap``): of the
            numbers, or of the enclosure (centre and radius both zero).
        traces: the real trace of each ``D_v``, which ranks the receiving
            elements.
        constant: ``c``.
        lattice_exponent: ``k``.
    """
    k = _checked_lattice_exponent(lattice_exponent)
    steps: list[SnapStep] = []
    hermitian = [_hermitian_part(m) for m in data]
    if any(not equal(h, m) for h, m in zip(hermitian, data, strict=True)):
        steps.append(SnapStep.HERMITIAN_PART)
    rounded = [lattice_round_matrix(h, k) for h in hermitian]
    if any(not equal(r, h) for r, h in zip(rounded, hermitian, strict=True)):
        steps.append(SnapStep.LATTICE)
    residue_nonzero = not _is_zero_matrix(_completeness_residue(rounded, constant))
    if residue_nonzero:
        steps.append(SnapStep.COMPLETENESS_PER_ENTRY)
    placed = _absorb_per_entry(rounded, supports, traces, constant)
    failure: str
    base: Sequence[ExactMatrix]
    if placed is not None:
        family, placements = placed
        if _all_psd(family):
            return SupportSafeSnap(
                tuple(family), tuple(steps), None, False, placements, None
            )
        coordinate = _coordinate_family(hermitian, constant)
        if coordinate is not None:
            for weight in LIFT_LADDER:
                mixed = [
                    lattice_round_matrix(m, k) for m in _mix(family, coordinate, weight)
                ]
                again = _absorb_per_entry(mixed, supports, traces, constant)
                if again is None:
                    continue
                lifted, lifted_placements = again
                if _all_psd(lifted) and is_complete_at(lifted, constant):
                    return SupportSafeSnap(
                        lifted,
                        (*steps, SnapStep.COORDINATE_LIFT),
                        weight,
                        False,
                        lifted_placements,
                        None,
                    )
        failure = "positivity"
        base = family
    else:
        failure = "completeness"
        base = rounded
    # The last resort, req:support-safe-snap (iv): flagged, refused under strict.
    size = len(base[0])
    shares = dyadic_uniform_weights(len(base))
    uniform = [
        tuple(
            tuple(
                Cx(constant * share, Fraction(0)) if i == j else ZERO
                for j in range(size)
            )
            for i in range(size)
        )
        for share in shares
    ]
    nonzero = [v for v, support in enumerate(supports) if support]
    designated = _first_largest(nonzero or list(range(len(base))), traces)
    last_steps = (*steps, SnapStep.UNIFORM_LIFT_LAST_RESORT)
    for weight in LIFT_LADDER:
        mixed = [lattice_round_matrix(m, k) for m in _mix(base, uniform, weight)]
        residue = _completeness_residue(mixed, constant)
        closed = list(mixed)
        closed[designated] = _exact_add(closed[designated], residue)
        if _all_psd(closed) and is_complete_at(closed, constant):
            return SupportSafeSnap(
                tuple(closed),
                last_steps,
                weight,
                True,
                ((-1, -1, designated),),
                failure,
            )
    return SupportSafeSnap(None, last_steps, None, True, (), failure)


def _rows_or_refuse(
    data: Sequence[ExactMatrix],
    supports: Sequence[frozenset[int]],
    traces: Sequence[Fraction],
    *,
    constant: Fraction,
    lattice_exponent: int,
    site: str,
    setting: str | None,
    block: str,
) -> tuple[tuple[ExactMatrix, ...], SupportSafeSnap]:
    """Run the support-safe rows and their last decisions, or refuse the data."""
    result = support_safe_snap_block(
        data,
        supports=supports,
        traces=traces,
        constant=constant,
        lattice_exponent=lattice_exponent,
    )
    if result.family is None:
        raise SnapRefusedError(
            "neither the support-safe rows nor the last resort restore exact "
            f"positivity and completeness at {_where(site, setting, block)}; the "
            "declarer refuses the data (foundations/req:snap-reference (ii))",
            reason="positivity_not_restored",
            predicate=SnapPredicate.POSITIVITY,
            site=site,
            setting=setting,
            block=block,
            detail={
                "failed_rows": result.failure,
                "ladder": [str(w) for w in LIFT_LADDER],
            },
        )
    failures = decide_last(result.family, constant, lattice_exponent)
    if failures:
        predicate = {
            "hermiticity": SnapPredicate.HERMITICITY,
            "positivity": SnapPredicate.POSITIVITY,
            "completeness": SnapPredicate.COMPLETENESS,
            "lattice": SnapPredicate.LATTICE,
            "declared_order_sum": SnapPredicate.DECLARED_ORDER_SUM,
        }[failures[0]]
        raise SnapRefusedError(
            f"the snapped family at {_where(site, setting, block)} fails its last "
            f"decisions: {', '.join(failures)}; the declarer refuses the data "
            "(foundations/req:snap-reference (ii))",
            reason="not_exactly_admissible",
            predicate=predicate,
            site=site,
            setting=setting,
            block=block,
            detail={"failures": list(failures)},
        )
    return result.family, result


# ---------------------------------------------------------------------------
#  The entry point
# ---------------------------------------------------------------------------


def _checked_measurement_data(
    data: Mapping[str, Sequence[Matrix]], alphabet: tuple[str, ...]
) -> dict[str, tuple[Matrix, ...]]:
    """Refuse data that are not a family over ``alphabet`` per block."""
    if not data:
        raise ValueError("a measurement family has at least one block")
    if not alphabet or len(set(alphabet)) != len(alphabet):
        raise ValueError("the alphabet is non-empty and repeats no letter")
    out: dict[str, tuple[Matrix, ...]] = {}
    for label, family in data.items():
        if len(family) != len(alphabet):
            raise ValueError(
                f"block {label!r} has {len(family)} elements for an alphabet "
                f"of {len(alphabet)}"
            )
        _exact_family(list(family), f"block {label!r}")
        out[label] = tuple(family)
    return out


def _checked_reference(
    reference: Reference,
    families: Mapping[str, Sequence[Matrix]],
    alphabet: tuple[str, ...],
    constant: Fraction,
) -> None:
    """Refuse a reference that is not one of this family.

    The reference may name a subset of the family's blocks, in the family's
    order: a declarer holds no enclosure of a block it does not carry (a run
    that declares enclosed references not used is offered the exact blocks
    alone, ``receiver/detector-imperfections/req:dark-composed-reference``
    (vi)).
    """
    if reference.alphabet != alphabet:
        raise ValueError(
            f"the reference's alphabet {list(reference.alphabet)} is not the "
            f"family's {list(alphabet)}"
        )
    if reference.constant != constant:
        raise ValueError(
            f"the reference is complete at {reference.constant}, "
            f"the family at {constant}"
        )
    labels = list(families)
    positions = []
    for block in reference.blocks:
        if block.label not in families:
            raise ValueError(
                f"the reference's block {block.label!r} is not a block of the "
                f"family {labels}"
            )
        positions.append(labels.index(block.label))
        size = np.asarray(families[block.label][0]).shape[0]
        if block.dimension != size:
            raise ValueError(
                f"block {block.label!r}: reference dimension {block.dimension}, "
                f"data dimension {size}"
            )
    if positions != sorted(positions):
        raise ValueError("the reference names its blocks in the family's order")


def _usable_blocks(
    reference: Reference,
) -> tuple[dict[str, ReferenceBlock], set[str], tuple[str, ...]]:
    """Take the decisions of ``req:snap-reference`` (i), block by block.

    Returns the blocks that pass, the labels of those that fail, and the
    failures. The decisions are taken per block, so that a block failing them
    takes no valid block of the same setting down with it.
    """
    usable: dict[str, ReferenceBlock] = {}
    failed: set[str] = set()
    found: list[str] = []
    for block in reference.blocks:
        verdict = Reference(
            alphabet=reference.alphabet,
            blocks=(block,),
            constant=reference.constant,
            identity=reference.identity,
        ).decide()
        if verdict.usable:
            usable[block.label] = block
        else:
            failed.add(block.label)
            found.extend(verdict.failures)
    return usable, failed, tuple(found)


@dataclass(frozen=True)
class _BlockOutcome:
    """One block's snap before the record is assembled."""

    family: tuple[ExactMatrix, ...]
    status: BlockStatus
    steps: tuple[SnapStep, ...] = ()
    lift_weight: Fraction | None = None
    support_not_preserved: bool = False
    residue_placement: tuple[tuple[int, int, int], ...] = ()


def _from_rows(
    family: tuple[ExactMatrix, ...], result: SupportSafeSnap, status: BlockStatus
) -> _BlockOutcome:
    """Wrap a support-safe snap as a block outcome."""
    return _BlockOutcome(
        family=family,
        status=status,
        steps=result.steps,
        lift_weight=result.lift_weight,
        support_not_preserved=result.support_not_preserved,
        residue_placement=result.residue_placement,
    )


def _snap_on_centres(
    block: ReferenceBlock,
    *,
    constant: Fraction,
    lattice_exponent: int,
    site: str,
    setting: str | None,
) -> _BlockOutcome:
    """Keep a block whose exact reference is a lattice family, or move it.

    ``req:snap-reference`` (ii): kept where every element of the exact
    reference is a lattice value at ``k`` and exact admissibility at ``c``
    and the lattice condition, decided last, hold; otherwise moved by the
    support-safe rows on the centres.
    """
    centres = block.centres
    if all(on_lattice(centre, lattice_exponent) for centre in centres) and not (
        decide_last(centres, constant, lattice_exponent)
    ):
        return _BlockOutcome(
            family=tuple(centres),
            status=BlockStatus.KEPT,
            steps=(SnapStep.KEEP, SnapStep.DECIDE_LAST),
        )
    family, result = _rows_or_refuse(
        centres,
        [element.structural_support for element in block.elements],
        [_real_trace(centre) for centre in centres],
        constant=constant,
        lattice_exponent=lattice_exponent,
        site=site,
        setting=setting,
        block=block.label,
    )
    return _from_rows(family, result, BlockStatus.MOVED)


def _snap_on_data(
    data: Sequence[Matrix],
    *,
    constant: Fraction,
    tolerance: float,
    lattice_exponent: int,
    data_from_model: bool,
    site: str,
    setting: str | None,
    block: str,
) -> tuple[_BlockOutcome, dict[str, float], tuple[ExactMatrix, ...]]:
    """Snap one block from its binary64 data, admitted within ``tau``.

    ``req:declared-tolerance``: the defects are measured in binary64 on the
    data as they stand -- Hermiticity, completeness at ``c``, and the least
    eigenvalue of each Hermitian part -- and data with a defect above ``tau``
    or an eigenvalue below ``-tau`` are refused. Then the support-safe rows
    run on the data. The block is kept only where the snap is decided exactly
    to equal the data and the data are stated with no model behind them;
    data computed from a model are an evaluation the snap is not decided to
    equal, so such a block is moved even where the snap leaves the evaluation
    unchanged (``foundations/def:snap``).
    """
    arrays = [
        checked_matrix(element, f"{block}[{index}]")
        for index, element in enumerate(data)
    ]
    hermiticity = max(hermiticity_defect(element) for element in arrays)
    _admit(hermiticity, tolerance, SnapPredicate.HERMITICITY, site, setting, block)
    total = np.zeros(arrays[0].shape, dtype=np.complex128)
    for element in arrays:
        total = total + element
    completeness = float(
        np.max(np.abs(total - float(constant) * np.eye(total.shape[0])))
    )
    _admit(completeness, tolerance, SnapPredicate.COMPLETENESS, site, setting, block)
    smallest = min(min_eigenvalue(element) for element in arrays)
    _admit(
        max(0.0, -smallest),
        tolerance,
        SnapPredicate.POSITIVITY,
        site,
        setting,
        block,
        detail={"min_eigenvalue": smallest},
    )
    exact = tuple(to_exact(element) for element in arrays)
    family, result = _rows_or_refuse(
        exact,
        [_numeric_support(m) for m in exact],
        [_real_trace(m) for m in exact],
        constant=constant,
        lattice_exponent=lattice_exponent,
        site=site,
        setting=setting,
        block=block,
    )
    unchanged = all(equal(f, d) for f, d in zip(family, exact, strict=True))
    status = (
        BlockStatus.KEPT if unchanged and not data_from_model else BlockStatus.MOVED
    )
    pre_snap = {
        "hermiticity_defect": hermiticity,
        "completeness_residue": completeness,
        "min_eigenvalue": smallest,
    }
    return _from_rows(family, result, status), pre_snap, exact


def snap_measurement_family(
    data: Mapping[str, Sequence[Matrix]],
    *,
    alphabet: Sequence[str],
    tolerance: float,
    lattice_exponent: int,
    site: str,
    reference: Reference | None = None,
    constant: Fraction = Fraction(1),
    settings: SnapSettings | None = None,
    setting: str | None = None,
    data_from_model: bool = True,
    withheld_blocks: Collection[str] = (),
) -> MeasurementSnap:
    """Snap one measurement family block by block: kept, or moved and disclosed.

    Implements ``foundations/def:snap`` for an operator family read as a
    measurement, with ``foundations/req:snap-reference`` (i)-(iv),
    ``foundations/req:support-safe-snap`` and the record of
    ``foundations/req:who-snaps``; spec/architecture.md 2.9.

    1. **The reference** (item (i)). The decisions of a declarer's reference
       are taken block by block (:meth:`~certiqs_key.foundations.reference.
       Reference.decide`). A block that passes them is HANDED beside the snap
       (``foundations/def:evaluated-off-snap`` (i)), every such block where the
       run uses enclosed references and the exact ones alone where it declares
       them not used (``settings.reference_enclosure`` off).
    2. **The snap** (item (ii)). A block whose handed reference is exact runs
       on its centres: KEPT where they are a lattice family passing the last
       decisions, MOVED by the support-safe rows otherwise
       (:func:`support_safe_snap_block`, with the flagged last resort). Every
       other block runs on the binary64 data, admitted within ``tau``
       (``req:declared-tolerance``), and is MOVED unless the data are stated
       with no model behind them (``data_from_model`` false) and the snap is
       decided to leave them unchanged.
    3. **Resting** (item (iii)). A moved block on which no reference is handed
       rests on A-SNAP whatever the run does, with its cause in the group
       ``no usable reference`` (``last resort`` where the last resort snapped
       it): no reference held, a reference failing its decisions, or the
       block withheld because the run declares enclosed references not used.
       Whether a moved block on which the reference is handed rests is the
       run's decision after its search.
    4. **The strict option** (item (iv)). With ``settings.strict`` a moved
       block on which no reference is handed refuses the data
       (``strict_snaps``), naming the block, its cause, its group and
       the fix; the run refuses after its search where a handed moved block is
       not evaluated off its snap.

    Args:
        data: per block label, in the sector map's order, the binary64 family
            in the declared order of ``alphabet`` -- the model as evaluated.
            Read on every block the snap does not run on an exact reference
            of; elsewhere it fixes the shapes only.
        alphabet: the outcome letters, in the declared order.
        tolerance: ``tau``, the ceiling on the pre-snap defects of data
            snapped on the data.
        lattice_exponent: ``k``, no default.
        site: where in the declaration the family sits.
        reference: the reference the declarer holds of the family, or
            ``None``. It may name a subset of the blocks, in their order.
        constant: ``c``, the completeness constant (``1`` for a POVM).
        settings: the run's enclosure setting and strict option; the
            defaults of :class:`SnapSettings` where ``None``.
        setting: the probe setting the family belongs to, where there is one.
        data_from_model: whether the declarer computes ``data`` from a model
            of the family (default), rather than stating them with no model
            behind them (``foundations/def:snap``).
        withheld_blocks: the blocks the declarer holds a reference of but
            does not pass in, because the run declares enclosed references not
            used and they are not enclosed exactly; their cause is
            ``enclosure_not_used`` rather than ``no_reference``.

    Raises:
        SnapRefusedError: a defect above ``tau``; data the last resort does not
            restore; or, under the strict option, a block that rests on A-SNAP
            whatever the run does.
        ValueError: on malformed arguments, or a reference whose alphabet,
            blocks, dimensions or constant are not those of the data.
    """
    admitted = _checked_tolerance(tolerance)
    k = _checked_lattice_exponent(lattice_exponent)
    policy = settings if settings is not None else SnapSettings()
    c = Fraction(constant)
    if c <= 0:
        raise ValueError(f"the completeness constant {c} is not positive")
    letters = tuple(alphabet)
    families = _checked_measurement_data(data, letters)
    withheld = frozenset(withheld_blocks)

    usable: dict[str, ReferenceBlock] = {}
    failed: set[str] = set()
    failures: tuple[str, ...] = ()
    snap_cause: RestingCause | None = None
    if reference is None:
        snap_cause = (
            RestingCause.ENCLOSURE_NOT_USED if withheld else RestingCause.NO_REFERENCE
        )
    else:
        _checked_reference(reference, families, letters, c)
        usable, failed, failures = _usable_blocks(reference)
        if failed:
            snap_cause = RestingCause.REFERENCE_FAILED
    handed = {
        label: block
        for label, block in usable.items()
        if policy.reference_enclosure or block.kind is ReferenceKind.EXACT
    }

    outcomes: dict[str, tuple[ExactMatrix, ...]] = {}
    records: list[BlockSnapRecord] = []
    for label, family in families.items():
        ref_block = handed.get(label)
        before: tuple[ExactMatrix, ...]
        pre_snap: dict[str, float]
        if ref_block is not None and ref_block.kind is ReferenceKind.EXACT:
            outcome = _snap_on_centres(
                ref_block, constant=c, lattice_exponent=k, site=site, setting=setting
            )
            before = ref_block.centres
            pre_snap = {
                "hermiticity_defect": 0.0,
                "completeness_residue": 0.0,
                "min_eigenvalue_defect": 0.0,
            }
            ground = "reference"
            kind = ReferenceKind.EXACT
        else:
            outcome, pre_snap, before = _snap_on_data(
                family,
                constant=c,
                tolerance=admitted,
                lattice_exponent=k,
                data_from_model=data_from_model,
                site=site,
                setting=setting,
                block=label,
            )
            ground = "measured"
            kind = ReferenceKind.NONE
        cause: RestingCause | None = None
        if ref_block is None and outcome.status is BlockStatus.MOVED:
            if label in failed:
                cause = RestingCause.REFERENCE_FAILED
            elif label in withheld or label in usable:
                cause = RestingCause.ENCLOSURE_NOT_USED
            else:
                cause = RestingCause.NO_REFERENCE
        outcomes[label] = outcome.family
        records.append(
            BlockSnapRecord(
                block=label,
                status=outcome.status,
                reference_kind=kind,
                handed=None if ref_block is None else HandedBlock(ref_block),
                cause=cause,
                steps=outcome.steps,
                lift_weight=outcome.lift_weight,
                support_not_preserved=outcome.support_not_preserved,
                displacement_squared=_displacement_squared_exact(
                    before, outcome.family
                ),
                pre_snap=pre_snap,
                defects_ground=ground,
                residue_placement=tuple(
                    (i, col, letters[v]) for i, col, v in outcome.residue_placement
                ),
            )
        )

    record = MeasurementSnapRecord(
        site=site,
        setting=setting,
        alphabet=letters,
        lattice_exponent=k,
        constant=c,
        declared_tolerance=admitted,
        settings=policy,
        blocks=tuple(records),
        cause=snap_cause,
        reference=None if reference is None else reference.as_record(),
        reference_failures=failures,
    )
    if policy.strict:
        _refuse_under_strict(record)
    return MeasurementSnap(blocks=outcomes, record=record, handed=handed)


def _refuse_under_strict(record: MeasurementSnapRecord) -> None:
    """Apply the strict option at the snap (``req:snap-reference`` (iv)).

    Refuses a moved block on which no reference is handed, naming the block,
    its cause, its group and the fix; a block the last resort snapped is
    named with its flag (``req:support-safe-snap`` (iv)). Changes nothing for
    a snap none of whose blocks rests on the assumption whatever the run does.
    """
    for block in record.blocks:
        if not block.rests_on_assumption:
            continue
        flagged = (
            " (snapped by the last resort, support_not_preserved)"
            if block.support_not_preserved
            else ""
        )
        group = block.group
        raise SnapRefusedError(
            f"the strict option refuses block {block.block!r} of "
            f"{_where(record.site, record.setting, None)}{flagged}: no reference "
            f"is handed on it, so it would rest on {ASSUMPTION_ID} "
            f"({ASSUMPTION_CLAIM}); group: {group}; cause: {block.cause}; fix: "
            f"{block.fix} (foundations/req:snap-reference (iv))",
            reason="strict_snaps",
            predicate=SnapPredicate.STRICT_OPTION,
            site=record.site,
            setting=record.setting,
            block=block.block,
            detail={
                "cause": None if block.cause is None else str(block.cause),
                "fix": block.fix,
                "group": None if group is None else str(group),
                "support_not_preserved": block.support_not_preserved,
                "record": record.as_record(),
            },
        )
