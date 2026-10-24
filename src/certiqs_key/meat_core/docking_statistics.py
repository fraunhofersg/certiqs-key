"""Reading the statistics module's emitted geometry into this module's type.

THIS MODULE IS NOT PART OF THE PACKAGE SURFACE, for the reason
:mod:`certiqs_key.meat_core.docking` gives for itself: it is one of the two
files of :mod:`certiqs_key.meat_core` that import a sibling module, and
importing it from ``__init__`` would put that sibling's exact-rational
substrate on the import path of a package whose own mathematics is binary64
linear algebra. Reach it at ``certiqs_key.meat_core.docking_statistics``;
nothing else in this package imports it.

IT LIVES WITH THE CONSUMER, AND THE DIRECTION IS THE REASON. The code fills
:class:`~certiqs_key.meat_core.declaration.declaration.PolytopeData`, a type of
this module, from the supplier's emitted geometry; placed in the supplier, it
would make ``statistics`` depend on ``meat-core``. Imports point downward only
(PRINCIPLES.md section 4), so the code that converts an emitted geometry into
this module's type belongs to THE CONSUMER THAT READS IT, and the supplier's
``interface.yaml`` records the adapter's owner and path in
``artifact_bindings.docking``. ``certiqs_key.statistics`` imports ``domain/``
only.

WHAT THIS MODULE OWNS AND WHAT IT DOES NOT
==========================================
The artifact the SUPPLIER owns is the exact rational geometry of
:mod:`certiqs_key.statistics.taxonomy`: the conventions of its
``interface.yaml`` require that "every number this module emits is an exact
rational", and Theorem ``thm:box-construction`` (i) proves the box bounds are integer
multiples of ``1/n``. What that module does not own is the type the consumer's
declaration carries that geometry in.
:class:`~certiqs_key.meat_core.declaration.declaration.PolytopeData` types
``B``, ``b`` and ``box_bounds`` as MACHINE NUMBERS, and it is this module's.

So the conversion happens here, once, in one direction, with the direction
named:

    q^- is rounded DOWN and q^+ is rounded UP.

That is the one direction Lemma ``binomial-box/lem:widening`` licenses: lower
bounds moved down and upper bounds moved up give a superset of the emitted box
(its (i)), failed no more often (its (ii)), with no larger infimum (its
(iii)), for any real bounds and so for binary64 ones; its (v) shows the
reverse move can break the completeness figure. Proposition ``prop:rule-exact``
(iii) and Lemma ``lem:guard`` (ii) are the same fact for a rule's own interval:
enlarging the interval can only lower the failure probability. IT IS
ADMISSIBLE FOR EVERY ADMISSIBLE ENDPOINT RULE and not only for the exact one,
``lem:guard`` (ii) being stated for every rule.

WHAT SURVIVES THE CONVERSION, AND THE ONE CLAUSE THAT DOES NOT
==============================================================
The docked box CONTAINS the emitted one, and every claim that survives a
superset survives with it: ``p^hon`` is still inside (Theorem ``thm:box-construction``
(iii)), the closed-form validation predicate still holds (Theorem
``thm:geometry-validation`` (iii)), the emitted data is still a canonical box with
``0 <= q^- <= q^+ <= 1`` (Theorem ``thm:box-construction`` (ii)), the consuming
def:admissible-acceptance-set still holds (Theorem ``thm:box-construction`` (iv)), and
the reported ``epsilon_star`` is still a bound on the honest failure probability -- the
failure event of Theorem ``thm:completeness-bound`` for a LARGER set is a subset of the
one bounded there. What it costs is rate and never soundness: by Lemma
``binomial-box/lem:widening`` (iii), an enlargement can only LOWER the consumer's
``h_low``.

The clause that does NOT survive is the second half of Theorem ``thm:box-construction``
(i): "each ``q^{+-}(chat)`` is either an integer multiple of ``1/n`` or one of
``0, 1``". A rounded bound is an exact rational -- a dyadic one -- but it is no
longer a multiple of ``1/n`` when ``n`` is not a power of two, so the docked
record is not the emitted artifact and is not offered as one. THE SUPPLIER'S
OWN OUTPUT IS THE EXACT GEOMETRY:
:class:`~certiqs_key.statistics.taxonomy.PolytopeGeometry` carries integer
multiples of ``1/n`` and satisfies (i) verbatim, and this function is a
conversion INTO this module's declared type, made here rather than left to a
caller so that it happens once, in one direction, with the direction named.

WHERE IT COSTS NOTHING AT ALL, and how to tell. The bounds have denominator
``n``, so the conversion is EXACT whenever every ``k^{+-}/n`` is a dyadic
rational -- at ``n`` a power of two, and case by case elsewhere.
:func:`conversion_is_exact` decides it, exactly, and a caller that needs the
guarantee can ask rather than assume.

THE TWO DIRECTED ROUNDINGS ARE THIS PACKAGE'S ALREADY, AND THIS FILE GIVES THEM
A PUBLIC NAME AT THE BOUNDARY THAT USES THEM. The construction is
:mod:`certiqs_key.meat_core.acceptance.geometry`'s, and it is IMPORTED rather
than copied -- a third copy of ``nextafter`` in one repository is a third place
a direction could be inverted. The supplier keeps no floating-point path at
all, which is what its ``conventions.no_binary64_anywhere`` row requires of it.

The pair is PUBLIC in ``acceptance/geometry.py``, so that the repository's one
direction-bearing rounding has a public name at the boundary that uses it, and
RE-EXPORTED HERE under :data:`float_below` and
:data:`float_above`, so that a caller of this adapter can name the rounding it
is subject to.
"""

from __future__ import annotations

from fractions import Fraction

from certiqs_key.meat_core.acceptance.geometry import float_above, float_below
from certiqs_key.meat_core.declaration.declaration import AcceptanceSet, PolytopeData
from certiqs_key.statistics.errors import StatisticsError
from certiqs_key.statistics.taxonomy import GeometryTag, PolytopeGeometry

__all__ = [
    "acceptance_set_record",
    "conversion_is_exact",
    "float_above",
    "float_below",
    "polytope_data",
]


def conversion_is_exact(geometry: PolytopeGeometry) -> bool:
    """Return whether every bound of the geometry is a machine number already.

    Decided in exact arithmetic: a rational is a machine number exactly when
    converting it and back is the identity.
    """
    if geometry.box_bounds is None:
        return all(Fraction(float(value)) == value for value in geometry.rhs)
    lower, upper = geometry.box_bounds
    return all(Fraction(float(value)) == value for value in (*lower, *upper))


def polytope_data(geometry: PolytopeGeometry) -> PolytopeData:
    """Return the geometry as this module's ``PolytopeData``, rounded outward.

    The rows are exact in both worlds -- every entry of ``B`` is in
    ``{0, +-1}`` (Theorem ``thm:box-construction`` (i)) -- and ``b`` is REBUILT from the
    rounded bounds rather than rounded on its own, so that this module's
    well-formedness check finds the rows and the recorded pair agreeing exactly
    as Eq. ``eq:boxrows`` requires. Declared data that contradicts itself is a
    defect that must be refused before anything is computed from it, and the
    cheapest way not to emit one is not to be able to.
    """
    if geometry.box_bounds is None:
        raise StatisticsError(
            "only the canonical box form is docked here: the general polytope "
            "has no (q^-, q^+) pair to round in the two directions Lemma "
            "binomial-box/lem:widening licenses, and rounding rows in place "
            "would change which half-spaces are declared"
        )
    lower, upper = geometry.box_bounds
    floors = tuple(_below(value) for value in lower)
    caps = tuple(_above(value) for value in upper)
    size = len(geometry.outcomes)
    rows = tuple(
        tuple(1.0 if column == index else 0.0 for column in range(size))
        for index in range(size)
    ) + tuple(
        tuple(-1.0 if column == index else 0.0 for column in range(size))
        for index in range(size)
    )
    return PolytopeData(
        columns=size,
        rows=rows,
        rhs=caps + tuple(-value for value in floors),
        box_bounds=(floors, caps),
    )


def acceptance_set_record(geometry: PolytopeGeometry) -> AcceptanceSet:
    """Return the geometry as this module's declared ``acceptance_set``.

    The machine key the supplier's own statement names: ``meat-core`` consumes
    the acceptance set under the machine key ``acceptance_set`` and refuses an
    unknown geometry tag rather than guessing (``def:taxonomy``).
    """
    return AcceptanceSet(
        geometry=str(GeometryTag.POLYTOPE), polytope=polytope_data(geometry)
    )


def _below(value: Fraction) -> float:
    """Return the largest machine number ``<= value``; the floor direction."""
    rounded = float_below(value)
    if rounded is None:  # pragma: no cover - box bounds lie in [0, 1]
        raise StatisticsError(f"no machine number stands below {value}")
    return rounded


def _above(value: Fraction) -> float:
    """Return the smallest machine number ``>= value``; the cap direction."""
    rounded = float_above(value)
    if rounded is None:  # pragma: no cover - box bounds lie in [0, 1]
        raise StatisticsError(f"no machine number stands above {value}")
    return rounded
