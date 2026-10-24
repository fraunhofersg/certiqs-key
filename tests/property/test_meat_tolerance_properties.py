"""Properties of the EXACT ADMISSION, on randomly drawn families.

There is no declared numerical tolerance: the admission is exact.

The exact admission decides FOUR CONDITIONS on a declared receiver family and each is
decided EXACTLY -- Hermiticity, positive semidefiniteness, completeness per
sector, and that the declared-order completeness sum rounds nowhere. What the
property asserts is that each decision is its condition and nothing else, with
every reference computed independently: Hermiticity by an entrywise comparison
of the drawn arrays, positivity by an eigensolver, completeness OVER THE
RATIONALS, and the rounding condition by the emulated accumulation.

WHAT IS NOT A PROPERTY, because there is no tolerance value:

* **Monotonicity of admission in a declared tolerance.** The predicate is
  decided at exactly zero and the parametrised sweep has one point.
* **Declaring a tolerance changes nothing on an exactly admissible family.**
  The entry points take no tolerance argument, which is asserted structurally
  in ``tests/golden/test_admission_surface_against_registry.py``.

WHAT IS ASSERTED INSTEAD. No defect is measured on declared data (the
interface's ``not_outputs``, ``tolerance_report``), so the statement is made of
the VERDICTS the admission records -- per block, per
sector -- and of the refusal it raises when one fails.

WHY THE DRAWS LOOK LIKE THIS. Every family is built on a two-dimensional ``Q``
with two one-dimensional sectors, so the sector map agrees by construction and
the draw exercises the numerical conditions alone -- the map is compared where
the two maps meet and no random number decides it. The perturbations are drawn
independently per condition so that a family with, say, a Hermiticity failure
and an exact sum is reachable; the frozen families are the same shape for the
same reason.
"""

from __future__ import annotations

import sys
from fractions import Fraction
from pathlib import Path

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

SUPPORT_TREE = Path(__file__).resolve().parents[1] / "support"
if str(SUPPORT_TREE) not in sys.path:
    sys.path.insert(0, str(SUPPORT_TREE))

from certiqs_key.foundations.exact_admission import sum_rounds_nowhere  # noqa: E402
from certiqs_key.meat_core.declaration.admission import (  # noqa: E402
    AdmissionError,
    AdmissionRefusal,
    admit_bob_povm_exact,
)
from certiqs_key.meat_core.reasons import GroupAPredicate  # noqa: E402

#: Weights of an exactly admissible two-outcome family on two one-dimensional
#: sectors: ``F_v0 = diag(a, b)``, ``F_v1 = diag(1 - a, 1 - b)``.
weights = st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)

#: Perturbations, dyadic so that the declared numbers are exact in binary64 and
#: a zero draw means a genuinely absent failure rather than a rounded one. THE
#: SMALLEST IS THE POINT OF THE SWEEP: ``2^-37`` is far inside any window a
#: declared tolerance would plausibly have carried, and it is refused, because
#: the predicate is decided at exactly zero and at no window.
perturbations = st.sampled_from([0.0, 2.0**-37, 2.0**-10, 0.0625, 0.125, 0.25])


def _family(
    a: float, b: float, herm: float, pos: float, cpl: float
) -> dict[str, dict[str, np.ndarray]]:
    """Return a two-outcome family with the three failures independently placed.

    ``herm`` enters as an IMAGINARY PART OF A BLOCK'S OWN DIAGONAL ENTRY, on the
    first element only: a one-dimensional block ``[[x + iy]]`` is Hermitian
    exactly when ``y`` is zero, and the Hermitian part is ``[[x]]``, so the
    failure does not disturb positivity. ``pos`` shifts one diagonal entry down
    and the partner entry up, so the sum is untouched and completeness is
    unaffected. ``cpl`` is added to the sum last.

    ``herm`` IS NOT PUT ON THE OFF-DIAGONAL OF THE ASSEMBLED 2x2: under the
    block form that perturbation would be INERT, the entry lying BETWEEN the two
    sectors and absent from the datum, so the family built would be Hermitian at
    every draw and the clause it is drawn for never exercised. The failure is
    placed inside a block, which is the only place a declared operator has
    entries (spec/architecture.md 2.9).
    """
    first = np.array([[a + 0j, 0j], [0j, b + 0j]])
    second = np.array([[1.0 - a + 0j, 0j], [0j, 1.0 - b + 0j]])
    if herm:
        first = first + np.array([[herm * 1j, 0j], [0j, 0j]])
    if pos:
        first = first - pos * np.array([[1.0 + 0j, 0j], [0j, 0j]])
        second = second + pos * np.array([[1.0 + 0j, 0j], [0j, 0j]])
    if cpl:
        second = second + cpl * np.array([[0j, 0j], [0j, 1.0 + 0j]])
    # BLOCKWISE: two one-dimensional sectors, which is what the diagonal 2x2
    # spelling above always meant and the only form an operator takes
    # (spec/architecture.md 2.9).
    return {
        outcome: {
            "s0": np.ascontiguousarray(element[0:1, 0:1]),
            "s1": np.ascontiguousarray(element[1:2, 1:2]),
        }
        for outcome, element in (("v0", first), ("v1", second))
    }


#: The declared sector index set the families above are written against.
SECTORS = ("s0", "s1")


def _elements(family: dict[str, dict[str, np.ndarray]]) -> list[np.ndarray]:
    """Return the two declared elements as 2x2 block-diagonal arrays.

    A TEST-SIDE CONVENIENCE for the reference comparisons below, and NOT what
    the module reads: no ``d_Q x d_Q`` operator exists as a datum.
    """
    return [
        np.diag([blocks["s0"][0, 0], blocks["s1"][0, 0]]) for blocks in family.values()
    ]


def _references(
    family: dict[str, dict[str, np.ndarray]],
) -> tuple[bool, bool, bool, bool]:
    """Return the four conditions, each computed independently of the module."""
    elements = _elements(family)
    hermitian = all(np.array_equal(f, f.conj().T) for f in elements)
    positive = all(
        float(np.min(np.linalg.eigvalsh(0.5 * (f + f.conj().T)))) >= 0.0
        for f in elements
    )
    # COMPLETENESS IS DECIDED OVER THE RATIONALS and never off the computed sum.
    # ``1 - a`` is a binary64 rounding of the real ``1 - a``, so
    # ``a + fl(1 - a)`` need not be 1 as a real number even when the COMPUTED
    # sum is the identity: that gap is exactly the ``(1, 2^-60, 2^-60)`` hazard,
    # and the drawn families exhibit it at ordinary weights.
    complete = all(
        sum((Fraction(float(np.real(f[i, i]))) for f in elements), Fraction(0)) == 1
        for i in range(2)
    )
    rounds_nowhere = all(
        sum_rounds_nowhere([family[outcome][sector] for outcome in ("v0", "v1")]).ok
        for sector in SECTORS
    )
    return hermitian, positive, complete, rounds_nowhere


@pytest.mark.contract
@given(a=weights, b=weights, herm=perturbations, pos=perturbations, cpl=perturbations)
@settings(max_examples=200, deadline=None)
def test_the_exact_admission_is_its_four_conditions_and_nothing_else(
    a: float, b: float, herm: float, pos: float, cpl: float
) -> None:
    """A family is admitted exactly when all four conditions hold, exactly.

    The admission RAISES on the first failure, so the property has two halves:
    on a family for which every reference holds it returns a record whose
    verdicts are those references, and on any other it refuses -- naming the
    predicate that failed and, for the summation row, a reason of its own.
    """
    family = _family(a, b, herm, pos, cpl)
    hermitian, positive, complete, rounds_nowhere = _references(family)
    admissible = hermitian and positive and complete and rounds_nowhere

    if admissible:
        record = admit_bob_povm_exact(family, SECTORS)
        assert record.exactly_admissible is True
        assert all(
            record.per_block_hermitian[outcome][sector]
            for outcome in record.outcomes
            for sector in record.sectors
        )
        assert all(
            record.per_block_positive[outcome][sector]
            for outcome in record.outcomes
            for sector in record.sectors
        )
        assert all(record.per_sector_complete.values())
        assert all(verdict.ok for verdict in record.per_sector_summation.values())
        return

    with pytest.raises(AdmissionError) as refusal:
        admit_bob_povm_exact(family, SECTORS)
    # THE REFUSAL NAMES THE PREDICATE, which is what def:declaration asks for
    # where it spells no string: the summation row has a reason of its own and
    # every other failure is the one exact refusal.
    #
    # THE SUMMATION ROW IS DECIDED BEFORE EXACT COMPLETENESS and after the two
    # per-block rows, which is the order the
    # interface's fail-closed row lists. It matters exactly where a family's
    # sum ROUNDS -- the informative refusal is then the one that names the
    # additions, because the remedy is the producer's.
    if hermitian and positive and not rounds_nowhere:
        assert refusal.value.reason is AdmissionRefusal.BOB_POVM_SUMMATION_ROUNDS
        assert refusal.value.predicate is GroupAPredicate.BOB_POVM_SUMMATION_EXACT
    else:
        assert (
            refusal.value.reason
            is AdmissionRefusal.DECLARATION_NOT_EXACTLY_ADMISSIBLE
        )
        assert refusal.value.predicate is GroupAPredicate.BOB_POVM_ADMISSION


@pytest.mark.contract
@given(a=weights, b=weights, scale=st.sampled_from([2.0**-37, 2.0**-40, 2.0**-45]))
@settings(max_examples=120, deadline=None)
def test_a_failure_far_inside_any_plausible_window_is_still_refused(
    a: float, b: float, scale: float
) -> None:
    """The predicate is decided at EXACTLY ZERO, and the sweep says what that buys.

    There is no tolerance value to be monotone in, so what is asserted is the
    consequence for a declaration: a Hermiticity failure of ``2^-45`` -- smaller
    than any window a declared tolerance would plausibly carry -- is REFUSED.
    The exact reading is the STRICTER of the readings spec/architecture.md 2.8
    licenses, so nothing that passes here could fail a tolerance-based policy,
    and this is the direction of that inclusion.
    """
    family = _family(a, b, scale, 0.0, 0.0)
    hermitian, _, _, _ = _references(family)
    assert hermitian is False
    with pytest.raises(AdmissionError) as refusal:
        admit_bob_povm_exact(family, SECTORS)
    assert refusal.value.reason is AdmissionRefusal.DECLARATION_NOT_EXACTLY_ADMISSIBLE
    assert refusal.value.predicate is GroupAPredicate.BOB_POVM_ADMISSION
    # AND NOTHING WAS REPAIRED: every array the caller passed in is the array it
    # still holds, entry for entry -- no projection, clamp, symmetrization or
    # renormalization (the interface's `no_row_repairs_declared_data`).
    untouched = _family(a, b, scale, 0.0, 0.0)
    for outcome in ("v0", "v1"):
        for sector in SECTORS:
            assert np.array_equal(family[outcome][sector], untouched[outcome][sector])
