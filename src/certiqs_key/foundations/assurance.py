"""The assurance tier of a result -- the platform's ONE tier vocabulary.

THE VOCABULARY LIVES IN ``foundations``, beside ``foundations/def:tiers``,
because three modules speak the tier -- ``meat-core`` (which earns it),
``receiver-povm`` and ``proof-reductions`` (which request and report it) -- and
PRINCIPLES.md section 4 lets modules import only downward, so every package may
import it from the floor. The mathematics that EARNS the label
stays in ``meat-core``: this file carries the vocabulary alone, and the
controls that decide which rung a run may claim stay with the module that
earns it.

THE LADDER HAS THREE RUNGS
==========================
spec/architecture.md 2.8 is the single statement of the ladder, and this enum
is its machine-readable form (``foundations/def:tiers``).

* ``estimate`` -- the objective at the point the optimizer returned, reported
  as an estimate of the minimum of the objective and claimed as no bound
  (``foundations/def:tiers`` (i)); live, reported on every run.
* ``first-order`` -- the solver's first-order lower bound on the minimum,
  evaluated in binary64 (``def:tiers`` (ii)).
* ``certified`` -- the same bound formed again from the declaration's data,
  every step exact or rigorously enclosed (``def:tiers`` (iii)). No witness
  apparatus accompanies it (PRINCIPLES.md section 10). A certified number is a
  first-order number as well.

The tier is ACHIEVED, never requested; ``foundations/req:tiers`` reports the
strongest tier reached as ``reported_tier``.
"""

from __future__ import annotations

from enum import StrEnum


class Assurance(StrEnum):
    """The assurance tier of a ``meat-core`` result -- the ladder of 2.8.

    Three members, ordered from weakest to strongest, so that a reader of the
    definition reads the ladder. See the module docstring; spec/architecture.md
    2.8 is the ladder's single statement.

    Implements ``foundations/def:tiers``.
    """

    ESTIMATE = "estimate"
    FIRST_ORDER = "first-order"
    CERTIFIED = "certified"
