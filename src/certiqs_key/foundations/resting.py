"""Why a moved block rests on A-SNAP: the causes, the groups and their fixes.

``foundations/req:snap-reference`` (iii): a moved block of a snap of a
measurement family that the run does not evaluate off its snap rests on
``foundations/ass:snapped-measurement`` (A-SNAP), and its record names its
cause, its group and a fix. A user acts on the group, of which there are four,
each with its fix; the cause stays in the record as the detail of the group.

The vocabulary lives here and not in :mod:`certiqs_key.foundations.snap`
because more parties than the declarer read it: the snap names the causes it
decides (no usable reference), the receiver details their fixes
(``receiver/detector-imperfections/req:snap-fix``) and the run
decides the causes of the groups that only its search settles (reference
bracket withdrawn, not evaluated; :mod:`certiqs_key.runs.direct_route`). The
snapping table is called by a declarer only (spec/architecture.md 2.8, "Who
snaps"), so no module imports it; this file holds words, and anyone may.
"""

from __future__ import annotations

from collections.abc import Mapping
from enum import StrEnum
from typing import Final

__all__ = [
    "FIX_NOISE_MODEL",
    "RestingCause",
    "RestingGroup",
    "resting_fix",
    "resting_group",
]


class RestingCause(StrEnum):
    """Why a moved block rests on A-SNAP (``foundations/req:snap-reference`` (iii)).

    The first four are causes of the group ``no usable reference`` (iii)(a),
    known when the block is snapped or the class emitted; the last four are
    the run's, decided after its search: three of the group ``reference
    bracket withdrawn`` (iii)(b) and one of ``reference bracket not
    evaluated`` (iii)(c). :attr:`fix` is the fix the claim names for each.
    """

    #: (a): the declarer holds no reference of the family.
    NO_REFERENCE = "no_reference"
    #: (a): a reference failing the decisions of (i), or one a property of
    #: which (i) leaves to its constructing module is not established.
    REFERENCE_FAILED = "reference_failed"
    #: (a): the run declares enclosed references not used, and a radius of
    #: the block is not zero.
    ENCLOSURE_NOT_USED = "enclosure_not_used"
    #: (a), a producer's class: no reference companion that bypasses it is
    #: formed beside the artefact (a bypassing companion).
    NO_REFERENCE_COMPANION = "no_reference_companion"
    #: (b): a reference is handed on the block, or for a producer's class a
    #: bypassing companion is formed, and a companion carrying it is
    #: evaluated, but no evaluated point contributes a bound on it.
    REFERENCE_BRACKET_WITHDRAWN = "reference_bracket_withdrawn"
    #: (b), the second cause: the certified evaluation finds the two
    #: enclosures of a block the companion carries inconsistent, and the
    #: companion's bracket is withdrawn; an engine defect, not a property of
    #: the declaration.
    FACTOR_ENCLOSURE_INCONSISTENT = "factor_enclosure_inconsistent"
    #: (b), the third cause: a point contributes on the companion, but its
    #: certified evaluation certifies none, and the key length is formed from
    #: a number certified on the snapped declaration in its place.
    COMPANION_NOT_CERTIFIED = "companion_not_certified"
    #: (c): a reference is handed on the block, or for a producer's class a
    #: bypassing companion is formed, but no companion carrying it is
    #: evaluated, because none is compiled or admitted.
    REFERENCE_BRACKET_NOT_EVALUATED = "reference_bracket_not_evaluated"

    @property
    def fix(self) -> str:
        """The fix ``foundations/req:snap-reference`` (iii) names for the cause."""
        return _CAUSE_FIXES[self]

    @property
    def group(self) -> RestingGroup:
        """The group of the cause; a last-resort block's is decided on the block."""
        return _CAUSE_GROUPS[self]


class RestingGroup(StrEnum):
    """The four groups a user acts on (``foundations/req:snap-reference`` (iii)).

    The cause stays in the record as the detail of its group; its fix names
    which change within the group's fix the block needs.
    """

    NO_USABLE_REFERENCE = "no_usable_reference"
    REFERENCE_BRACKET_WITHDRAWN = "reference_bracket_withdrawn"
    REFERENCE_BRACKET_NOT_EVALUATED = "reference_bracket_not_evaluated"
    #: A block snapped by the last resort of ``req:support-safe-snap`` (iv),
    #: whatever its cause; its fix adds the device's noise to its cause's.
    LAST_RESORT = "last_resort"

    def fix(self, cause: RestingCause | None = None) -> str:
        """Return the group's fix; for the last resort, with its cause's group fix."""
        if self is RestingGroup.LAST_RESORT:
            if cause is None:
                return FIX_NOISE_MODEL
            return f"{FIX_NOISE_MODEL}; and {_GROUP_FIXES[cause.group]}"
        return _GROUP_FIXES[self]


#: The fix of the group ``last resort`` (``req:snap-reference`` (iii)): a model
#: that includes the noise the device has.
FIX_NOISE_MODEL: Final[str] = (
    "a model that includes the noise the device has (its loss and dark "
    "counts), so that every element of the block is positive definite"
)

_FIX_REFERENCE: Final[str] = (
    "a model of the family with a reference that the run uses"
)
_FIX_WITHDRAWN: Final[str] = (
    "the fix the withdrawal reasons recorded at the evaluated points name"
)
#: The group's fix over its three causes (iii)(b): the one the reasons
#: recorded at the companion's evaluated points name.
_FIX_WITHDRAWN_GROUP: Final[str] = (
    "the fix the reasons recorded at the reference companion's evaluated "
    "points name"
)
_FIX_NOT_EVALUATED: Final[str] = (
    "the fix the reason recorded for the reference companion names"
)

_CAUSE_FIXES: Final[Mapping[RestingCause, str]] = {
    RestingCause.NO_REFERENCE: _FIX_REFERENCE,
    RestingCause.REFERENCE_FAILED: _FIX_REFERENCE,
    RestingCause.ENCLOSURE_NOT_USED: (
        "an exact reference, or a run that uses enclosed references "
        "(run parameter reference_enclosure on)"
    ),
    RestingCause.NO_REFERENCE_COMPANION: (
        "declared numbers on which the producer's exact construction stays on "
        "the lattice, so that the class is kept"
    ),
    RestingCause.REFERENCE_BRACKET_WITHDRAWN: _FIX_WITHDRAWN,
    RestingCause.FACTOR_ENCLOSURE_INCONSISTENT: (
        "no change of the declaration: the two enclosures of a block the "
        "reference companion carries are inconsistent, a defect of the engine "
        "in the modules that carry the enclosures; report it"
    ),
    RestingCause.COMPANION_NOT_CERTIFIED: (
        "the fix the certified evaluation's reasons recorded at the reference "
        "companion's points name"
    ),
    RestingCause.REFERENCE_BRACKET_NOT_EVALUATED: _FIX_NOT_EVALUATED,
}

_CAUSE_GROUPS: Final[Mapping[RestingCause, RestingGroup]] = {
    RestingCause.NO_REFERENCE: RestingGroup.NO_USABLE_REFERENCE,
    RestingCause.REFERENCE_FAILED: RestingGroup.NO_USABLE_REFERENCE,
    RestingCause.ENCLOSURE_NOT_USED: RestingGroup.NO_USABLE_REFERENCE,
    RestingCause.NO_REFERENCE_COMPANION: RestingGroup.NO_USABLE_REFERENCE,
    RestingCause.REFERENCE_BRACKET_WITHDRAWN: RestingGroup.REFERENCE_BRACKET_WITHDRAWN,
    RestingCause.FACTOR_ENCLOSURE_INCONSISTENT: (
        RestingGroup.REFERENCE_BRACKET_WITHDRAWN
    ),
    RestingCause.COMPANION_NOT_CERTIFIED: RestingGroup.REFERENCE_BRACKET_WITHDRAWN,
    RestingCause.REFERENCE_BRACKET_NOT_EVALUATED: (
        RestingGroup.REFERENCE_BRACKET_NOT_EVALUATED
    ),
}

_GROUP_FIXES: Final[Mapping[RestingGroup, str]] = {
    RestingGroup.NO_USABLE_REFERENCE: _FIX_REFERENCE,
    RestingGroup.REFERENCE_BRACKET_WITHDRAWN: _FIX_WITHDRAWN_GROUP,
    RestingGroup.REFERENCE_BRACKET_NOT_EVALUATED: _FIX_NOT_EVALUATED,
}


def resting_group(
    cause: RestingCause | None, *, last_resort: bool
) -> RestingGroup | None:
    """Return the group a resting block is recorded in, or ``None`` without a cause.

    ``foundations/req:snap-reference`` (iii): the group of the cause, save for
    a block snapped by the last resort, whose group is
    :attr:`RestingGroup.LAST_RESORT`.
    """
    if cause is None:
        return None
    return RestingGroup.LAST_RESORT if last_resort else cause.group


def resting_fix(cause: RestingCause | None, *, last_resort: bool) -> str | None:
    """Return the fix of a resting block's cause, with the noise for a last resort."""
    if cause is None:
        return None
    if last_resort:
        return f"{cause.fix}; and {FIX_NOISE_MODEL}"
    return cause.fix
