"""What this instance DECLARES to ``meat-core``, and the snap that makes it exact.

WHY THIS MODULE EXISTS
======================
``meat-core`` 1.0.0 puts the declared acceptance data on the EXACT ISLAND. Its
Section 2.5 (``number_model``) makes them the one exception to the binary64
model -- "every declared number is a binary64 datum and IS the value it
declares, WITH THE SINGLE EXCEPTION of the acceptance data of
def:admissible-acceptance-set, which are exact rationals" -- and Section 2.6's
``acceptance_data_exact`` row decides them at "**exactly 0**; exact rational arithmetic,
the exact island". So an accepted frequency vector must sum to one OVER THE RATIONALS,
not to within a window.

:func:`instances.common.honest.depolarized_bell_pair.honest_distribution` returns exact
rationals that do sum to one. What does not survive is the CROSSING: the
declaration slot is a tuple of binary64 numbers, and ``float(19/640)`` is not
``19/640``, so a vector converted coordinate by coordinate has an exact sum a
hair away from one and is REFUSED. That refusal is correct and ``meat-core``
never repairs it:

    "Nothing is repaired and no window is applied; a producer emits exact
    rationals, or SNAPS AT THE INSTANCE before this module sees the data."

This module is that snap: an instance meets the row by declaring numbers that
are exactly representable and whose defining sum closes exactly in binary64,
addition by addition -- dyadic entries suffice -- and by snapping, at the
instance and before ``meat-core`` sees the data, anything that does not
(spec/architecture.md 2.8, "Who snaps"). ``meat-core``'s Proposition
``prop:optol-nobound`` is why no consumer-side tolerance could do it instead.

WHO MAY SNAP, AND WHY IT IS THIS PACKAGE
========================================
spec/architecture.md 2.8 ("Who snaps"): "declared data is snapped by whoever
declares it, once, by the documented table the ``domain/`` snapping module
owns, and the snap **produces exact admissibility**"; the table is
``foundations/snap.py``. The
acceptance set is THIS instance's assertion about its own honest channel model,
so this instance may round that assertion to the nearest exactly admissible one,
in the open and with the displacement recorded. A MODULE handed the vector may
not, and ``meat-core`` says so of itself: "there is no tolerance at which a module
repairs what it was handed".

The table is not re-implemented here. Every step is
:func:`certiqs_key.foundations.snap.snap_family_exact`, the shared table of
spec/architecture.md 2.9 §7.2, applied to the family of ``1 x 1`` blocks the frequency
vector is: the completeness condition ``sum_v F_v = 1_Q`` on one-dimensional blocks IS
"the frequencies sum to one", the designated element the residue is absorbed into is the
coordinate of largest exact mass, and the final ``rounds-nowhere`` check is the same one
condition (S) uses. Nothing about the rule is BB84's.

WHAT THE SNAP DOES NOT DO, AND MUST NOT BE READ AS DOING
========================================================
It does not make the declared vector the honest one. After it, the instance
declares a DIFFERENT probability vector -- by at most ``2^-(kappa+1)`` per
coordinate, which is ``4.5e-13`` at the measured recommendation ``kappa = 40``
-- and every number ``meat-core`` computes is a statement about the vector that
was declared, not about the model that suggested it. That is the honest reading
of a snap and it is why the displacement is recorded per coordinate rather than
summarized: ``meat-core``'s own Proposition ``prop:optol-nobound`` proves that
no consumer-side tolerance converts into a bound on the key, and nothing here
claims one.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from fractions import Fraction

import numpy as np

from certiqs_key.foundations.snap import SnapRecord, snap_family_exact

__all__ = [
    "ACCEPTANCE_SNAP_SITE",
    "DECLARED_BY",
    "acceptance_snap_report",
    "declare_acceptance_frequencies",
]

#: What the run record's ``snaps`` block names as the author of these numbers.
DECLARED_BY = "instances.bb84.declare"

#: Where in the declaration the snapped family sits, as the records carry it.
ACCEPTANCE_SNAP_SITE = "payload.declaration.acceptance_set.frequencies"


def declare_acceptance_frequencies(
    distribution: Mapping[str, Fraction],
    order: Sequence[str],
    *,
    tolerance: float,
    lattice_exponent: int,
) -> tuple[tuple[float, ...], tuple[SnapRecord, ...]]:
    """Return an exactly admissible frequency vector, and what the snap did.

    The returned tuple is in ``order`` -- the declaration's own acceptance
    alphabet -- and satisfies, over the RATIONALS and not to within a window:
    every entry is a non-negative multiple of ``2^-kappa``, hence exactly a
    binary64 number; the entries sum to exactly ``1``; and the sum in the given
    order rounds nowhere, so the computed sum IS the real sum. That is what
    ``meat-core``'s ``acceptance_data_exact`` row asks of a declared singleton.

    THE RULE IS THE SHARED ONE AND NOT THIS INSTANCE'S.
    :func:`certiqs_key.foundations.snap.snap_family_exact` runs the whole
    spec/architecture.md 2.9 table on the family of ``1 x 1`` blocks the vector is, so
    the completeness row -- "the exact residue ``1 - sum_v F_v`` absorbed into ONE
    designated element" -- is exactly "the frequencies are made to sum to one", and the
    designated element is the coordinate of largest exact mass, never a structurally
    zero one. A coordinate the model puts at exactly ``0`` comes back exactly ``0``,
    which matters: it is what keeps ``Chat_acc`` the set the model says it is rather
    than a set with a spurious ``2^-40`` in it.

    Args:
        distribution: the honest distribution as EXACT RATIONALS, one per
            declared acceptance value. Refused if a value is not a
            :class:`~fractions.Fraction`, because a float arriving here would
            already have lost the exactness this function exists to recover.
        order: the declaration's acceptance alphabet, in its declared order.
            The order is part of the datum -- the rounds-nowhere check is
            stated in it -- so it is taken from the declaration and never
            from a dict's iteration order.
        tolerance: ``tau``, the run's declared numerical tolerance, the CEILING
            on the pre-snap defect this snap may absorb. NO DEFAULT: it has
            none anywhere on this platform (spec/architecture.md 2.8) and this
            instance does not invent one. It does NOT decide the lattice step,
            which is a modelling act rather than an error to minimize.
        lattice_exponent: ``kappa`` of spec/architecture.md 2.9 (D-LAT). NO DEFAULT
        (2.9);
            the measured recommendation is ``40``, at which the per-coordinate
            displacement is at most ``2^-41 = 4.5e-13``.

    Returns:
        ``(frequencies, records)``: the vector to declare, and every
        :class:`~certiqs_key.foundations.snap.SnapRecord` the table produced, in the
        order performed.

    Raises:
        certiqs_key.foundations.snap.SnapRefusedError: if a pre-snap defect exceeds
            ``tolerance``, or if the snapped family fails the final exact
            admission. The caller refuses; nothing is declared.
        KeyError: if ``order`` names a value ``distribution`` does not carry.
        TypeError: if a mass is not an exact rational.
    """
    masses: list[Fraction] = []
    for value in order:
        mass = distribution[value]
        if not isinstance(mass, Fraction):
            raise TypeError(
                f"the acceptance mass at {value!r} is {mass!r} of type "
                f"{type(mass).__name__}; this function snaps EXACT RATIONALS "
                "onto the declared lattice, and a float arriving here has "
                "already lost the exactness the snap exists to recover"
            )
        masses.append(mass)

    family = [np.array([[float(mass)]], dtype=np.float64) for mass in masses]
    snapped, records = snap_family_exact(
        family,
        tolerance=tolerance,
        lattice_exponent=lattice_exponent,
        site=ACCEPTANCE_SNAP_SITE,
    )
    frequencies = tuple(float(block[0][0]) for block in snapped)
    # THE POST-CONDITION, ASSERTED RATHER THAN ASSUMED, and over the rationals.
    # `snap_family_exact` establishes it -- this re-reads it in the form
    # `meat-core`'s own validator will, so that a future change to the shared
    # table that broke this instance's declaration fails here, at the producer,
    # rather than three stages later inside the engine.
    total = sum((Fraction(value) for value in frequencies), Fraction(0))
    if total != 1:
        raise AssertionError(  # pragma: no cover - the table establishes it
            f"the snapped acceptance vector sums to {total}, not 1; "
            "meat-core Section 2.6's acceptance_data_exact row decides this at "
            "exactly 0 in exact rational arithmetic and refuses anything else"
        )
    return frequencies, records


def acceptance_snap_report(
    records: Sequence[SnapRecord], tolerance: float, lattice_exponent: int
) -> dict[str, object]:
    """Return the JSON-ready record the run record's ``snaps`` block copies.

    Every snap, verbatim and in the order performed -- the same shape
    ``instances.optical_bb84.declare`` writes, and NOT summarized, for
    the same reason: the largest displacement over a run is a different fact
    from the displacement of one coordinate, and a reader checking that the
    displacement is of the same order as the defect it corrects needs them
    paired.
    """
    return {
        "declared_by": DECLARED_BY,
        "declared_tolerance": tolerance,
        "lattice_exponent": lattice_exponent,
        "snaps": [record.as_record() for record in records],
        "note": (
            "the declared acceptance set carries numbers this instance "
            "DECLARED, not the exact honest distribution that suggested them; "
            "no claim relates the two (meat-core prop:optol-nobound), and "
            "every number the engine computes is about the vector declared "
            "here"
        ),
    }
