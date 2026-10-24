"""The declared acceptance set: its geometries, and linear minimization over them.

def:admissible-acceptance-set admits any closed convex subset of the probability
simplex; the REPRESENTATIONS a declaration may use are the two tags of the accepted
``statistics`` taxonomy (Definition ``def:taxonomy``), read
here as data. What this package adds to them is the acceptance-side linear
minimization contract Remark ``rem:acc-side`` consumes -- and the exact decision
of whether the declared set has any point at all.
"""

from certiqs_key.meat_core.acceptance.geometry import (
    GEOMETRY_TAGS,
    POLYTOPE,
    SINGLETON,
    AcceptanceDefect,
    AcceptanceMinimum,
    AcceptanceVerdict,
    AcceptanceWitness,
    acceptance_contains_exact,
    acceptance_floors,
    acceptance_minimizer,
    acceptance_minimizer_exact,
    acceptance_minimum,
    acceptance_start,
    acceptance_start_exact,
    acceptance_verdict,
    acceptance_witness,
    minimal_acceptance_support,
    polytope_contains,
    polytope_coordinate_maximizers,
    polytope_coordinate_minima,
    polytope_defect,
    polytope_is_nonempty,
    polytope_minimizer,
    polytope_minimizer_exact,
    polytope_of,
    polytope_relative_interior_point,
    polytope_relative_interior_point_exact,
    polytope_support,
    polytope_support_and_exact_start,
    polytope_support_and_start,
    singleton_frequencies,
)
from certiqs_key.meat_core.acceptance.simplex import (
    LinearProgramResult,
    LinearProgramStatus,
    solve_standard_form,
)

__all__ = [
    "GEOMETRY_TAGS",
    "POLYTOPE",
    "SINGLETON",
    "AcceptanceDefect",
    "AcceptanceMinimum",
    "AcceptanceVerdict",
    "AcceptanceWitness",
    "LinearProgramResult",
    "LinearProgramStatus",
    "acceptance_contains_exact",
    "acceptance_floors",
    "acceptance_minimizer",
    "acceptance_minimizer_exact",
    "acceptance_minimum",
    "acceptance_start",
    "acceptance_start_exact",
    "acceptance_verdict",
    "acceptance_witness",
    "minimal_acceptance_support",
    "polytope_contains",
    "polytope_coordinate_maximizers",
    "polytope_coordinate_minima",
    "polytope_defect",
    "polytope_is_nonempty",
    "polytope_minimizer",
    "polytope_minimizer_exact",
    "polytope_of",
    "polytope_relative_interior_point",
    "polytope_relative_interior_point_exact",
    "polytope_support",
    "polytope_support_and_exact_start",
    "polytope_support_and_start",
    "singleton_frequencies",
    "solve_standard_form",
]
