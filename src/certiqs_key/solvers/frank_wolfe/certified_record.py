"""The record of the certified evaluation, importable without the ball arithmetic.

``meat-core/frank-wolfe/req:certified-evaluation`` (ix): what the evaluation
formed on one run, and the frank-wolfe interface's ``certified_evaluation``
reasons. The evaluation itself is
:mod:`certiqs_key.solvers.frank_wolfe.certified`, which imports
:mod:`certiqs_key.foundations.balls` and through it python-flint.

WHY A MODULE OF ITS OWN. A run with the option ``off`` records that the
evaluation did not run (:data:`EVALUATION_OFF`) and loads neither the
evaluation nor the library: the solve returns that record before importing
:mod:`~certiqs_key.solvers.frank_wolfe.certified`; a test holds that to be so.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from fractions import Fraction
from typing import TYPE_CHECKING, Any

from certiqs_key.foundations.dyadic import float_down
from certiqs_key.meat_core.objective.joint import JointSector

if TYPE_CHECKING:
    from certiqs_key.foundations.balls import Ball

__all__ = [
    "ACCEPTANCE_GEOMETRY_NOT_CERTIFIED",
    "ACCEPTANCE_ITERATE_NOT_EXACT",
    "BLOCK_NOT_POSITIVE_DEFINITE",
    "BOXED_FORM_INCONSISTENT",
    "CERTIFIED_EVALUATION_OFF",
    "CERTIFIER_UNAVAILABLE",
    "EVALUATION_OFF",
    "FACTOR_ENCLOSURE_INCONSISTENT",
    "FLOOR_NOT_CERTIFIED",
    "FRAME_NOT_ENCLOSED",
    "NOT_CERTIFIED",
    "ON_REFERENCE_COMPANION",
    "ON_SEARCHED",
    "POSITIVITY_NOT_CERTIFIED",
    "RANK_NOT_CERTIFIED",
    "SUPPORT_NOT_ESTABLISHED",
    "WORKING_PRECISION",
    "CertifiedEvaluation",
    "CertifiedPoint",
]

#: The working precision, the requirement's floor (item (v)).
WORKING_PRECISION = 128

#: The frank-wolfe interface's ``certified_evaluation.reasons``.
ACCEPTANCE_ITERATE_NOT_EXACT = "acceptance_iterate_not_exact"
FRAME_NOT_ENCLOSED = "frame_not_enclosed"
RANK_NOT_CERTIFIED = "rank_not_certified"
#: Item (iv)(c): a block's two enclosures contradict each other, a defect of a
#: carrier; it also withdraws the companion's bracket
#: (``req:bracket-on-reference`` (iv)).
FACTOR_ENCLOSURE_INCONSISTENT = "factor_enclosure_inconsistent"
BLOCK_NOT_POSITIVE_DEFINITE = "block_not_positive_definite"
POSITIVITY_NOT_CERTIFIED = "positivity_not_certified"
SUPPORT_NOT_ESTABLISHED = "support_not_established"
FLOOR_NOT_CERTIFIED = "floor_not_certified"
ACCEPTANCE_GEOMETRY_NOT_CERTIFIED = "acceptance_geometry_not_certified"
#: The engine's reordered form of an element with a boxed block (the third
#: kind of ``lem:certified-bracket-enclosed``, "(b), the reordering") is
#: inconsistent with itself: parts and block keys differ in number, a split
#: form is present where the factor is exact or absent where it is a box, or
#: one tuple of block keys has two positions or dimensions. No claim admits
#: it; it is a defect of the engine, and like ``factor_enclosure_inconsistent``
#: it marks every point of the declaration evaluated. On a reference companion
#: the fallback of item (i) then runs as for any companion that certifies no
#: point; on the searched declaration the run's number stays first order.
BOXED_FORM_INCONSISTENT = "boxed_form_inconsistent"
NOT_CERTIFIED = "not_certified"
CERTIFIER_UNAVAILABLE = "certifier_unavailable"
CERTIFIED_EVALUATION_OFF = "certified_evaluation_off"

#: Item (ix)'s ``declaration``: where the per-point entries were evaluated.
ON_REFERENCE_COMPANION = "reference_companion"
ON_SEARCHED = "searched"


@dataclass(frozen=True)
class CertifiedPoint:
    """One point's certified bracket, or its reasons (item (ix))."""

    index: int
    iteration: int
    certified: bool
    acceptance_side_bound: Fraction | None = None
    feasible_side_bound: Fraction | None = None
    reasons: tuple[str, ...] = ()
    detail: tuple[str, ...] = ()
    gradient_radius: float | None = None
    #: The enclosures of the gradient (``g_q`` balls, ``g_J`` blocks), for tests.
    gradient_q: Mapping[str, Any] = field(default_factory=dict, compare=False)
    gradient_blocks: Mapping[JointSector, Ball] = field(
        default_factory=dict, compare=False
    )
    #: The set of ``req:bracket-on-reference`` (i) the point belongs to
    #: (``search`` or ``polish``) and the order the search and then the polish
    #: consumed it in, which breaks ties in item (i)'s selection; set by the
    #: caller that chose the points, ``None`` where it did not say. Where a
    #: point came from, not what was certified there: not compared.
    point_set: str | None = field(default=None, compare=False)
    sequence: int | None = field(default=None, compare=False)

    @property
    def bracket(self) -> Fraction | None:
        """Return ``b^A_t + b^F_t``, exact, where the point is certified."""
        if self.acceptance_side_bound is None or self.feasible_side_bound is None:
            return None
        return self.acceptance_side_bound + self.feasible_side_bound

    def as_record(self) -> dict[str, Any]:
        """Return the record, the bounds rounded toward ``-inf`` (item (vi))."""
        bounds = (self.acceptance_side_bound, self.feasible_side_bound, self.bracket)
        down = [None if x is None else float_down(x) for x in bounds]
        return {
            "index": self.index,
            "iteration": self.iteration,
            "set": self.point_set,
            "sequence": self.sequence,
            "certified": self.certified,
            "acceptance_side_bound": down[0],
            "feasible_side_bound": down[1],
            "certified_bracket": down[2],
            "gradient_radius": self.gradient_radius,
            "reasons": list(self.reasons),
            "detail": list(self.detail),
        }


@dataclass(frozen=True)
class CertifiedEvaluation:
    """What ``req:certified-evaluation`` formed on one run, for the record (ix).

    ``declaration`` is the declaration :attr:`points` were evaluated on
    (:data:`ON_REFERENCE_COMPANION` or :data:`ON_SEARCHED`; ``None`` where the
    evaluation did not run). ``companion_points`` holds the companion's points
    wherever the evaluation ran on a companion and then once more on the
    searched declaration: in the fallback of item (i), and where the
    companion's bracket was withdrawn by item (iv)(c), whose cause
    ``bracket_withdrawn`` names. The record's ``premises`` and
    ``resting_blocks`` are the run tier's (``runs/direct_route.py``), which
    alone holds the snap records that name the moved blocks.
    """

    option: str
    #: ``certified``, ``not_certified``, ``withheld`` or ``off``.
    status: str
    #: ``h^cert``, exact, where some point is certified.
    certified_bound: Fraction | None
    points: tuple[CertifiedPoint, ...] = ()
    reasons: tuple[str, ...] = ()
    library: str | None = None
    precision: int = WORKING_PRECISION
    seconds: float = 0.0
    declaration: str | None = None
    companion_points: tuple[CertifiedPoint, ...] | None = None
    #: The cause the companion's bracket was withdrawn with by item (iv)(c),
    #: :data:`FACTOR_ENCLOSURE_INCONSISTENT`, or ``None``.
    bracket_withdrawn: str | None = None

    @property
    def reported(self) -> bool:
        """Whether the run is reported at the certified tier (items (vi), (vii))."""
        return self.status == "certified"

    @property
    def inconsistent(self) -> bool:
        """Whether some point found a block's two enclosures inconsistent ((iv)(c))."""
        return any(
            FACTOR_ENCLOSURE_INCONSISTENT in point.reasons for point in self.points
        )

    @property
    def fallback(self) -> bool:
        """Whether this is the fallback of item (i): the companion certified none."""
        return (
            self.declaration == ON_SEARCHED
            and self.companion_points is not None
            and self.bracket_withdrawn is None
        )

    def as_record(
        self, *, first_order: float | None, first_order_key_length: int | None
    ) -> dict[str, Any]:
        """Return ``stages.key_rate.certified``, the frank-wolfe interface's fields.

        ``first_order`` is the first-order number on the declaration the
        points were evaluated on (item (ix)): in the fallback the searched
        declaration's, ``None`` where it has none.
        """
        radii = [
            p.gradient_radius for p in self.points if p.gradient_radius is not None
        ]
        bound = self.certified_bound
        record: dict[str, Any] = {
            "certified_evaluation": self.option,
            "status": self.status,
            "certified_bound": None if bound is None else float_down(bound),
            "first_order_key_length": first_order_key_length,
            "certified_minus_first_order": None
            if bound is None or first_order is None
            else float(bound - Fraction(first_order)),
            "max_gradient_radius": max(radii, default=None),
            "working_precision_bits": self.precision,
            "arithmetic_library": self.library,
            "reasons": list(self.reasons),
            "seconds": self.seconds,
            "points": [point.as_record() for point in self.points],
            "declaration": self.declaration,
        }
        if self.companion_points is not None:
            record["companion_points"] = [
                point.as_record() for point in self.companion_points
            ]
        return record


#: The record of a run whose option is ``off``: the evaluation did not run.
EVALUATION_OFF = CertifiedEvaluation(
    "off", "off", None, reasons=(CERTIFIED_EVALUATION_OFF,)
)
