r"""Definition ``def:emitnorm``: the emission normalizer, a fidelity-first snap.

WHAT IT ACTS ON, AND WHAT IT NEVER TOUCHES. The normalizer acts on the DATA
SECTORS of a reduction instance, per data sector and per class, and on nothing
else: "a snap of the module's own emission, never of anything it was handed"
(``def:emitnorm``, fourth property). A scalar sector's value is declared, not
computed, so the normalizer never reads one; that is the stability clause of
``def:reduction-instance`` (I1), and it is what lets ``thm:emit`` (iii) apply
the instance's own existence theorem to the declared datum.

THE STEPS RUN ON ``V_t n V^(s)``. ``def:emitnorm`` acts "on the elements
``A^(s)_v`` with ``v in V_t n V^(s)``, the elements of the class ``t`` in the
sector's support; the elements OUTSIDE THE SECTOR SUPPORT are exactly zero, lie
on the lattice, and are touched by no step". :func:`normalize` takes the
supports, and every step below ranges over the support, which meets every
class (``def:reduction-instance``); the DEFAULT support is ``V``.

THE PROCEDURE, IN THE DEFINITION'S ORDER
========================================
The handed datum of every class is Hermitian, positive semidefinite and
complete at its class weight with Gaussian-rational entries, so it is an EXACT
REFERENCE of itself (``foundations/def:exact-reference``, every radius zero).
No claim relates a snapped class to it, and a run evaluates off the snap
through the reference companion (``reductions/cor:reference-companion``),
which bypasses the normalizer; so the normalizer aims at fidelity and at
nothing else:

1. *Keep*: a class every element of which is already on the lattice is kept
   and no further step acts on it;
2. *Snap for fidelity*: for ``w = 0`` and then ``2^-kappa, ..., 2^-1``, every
   element is the handed one with its off-diagonal entries multiplied by
   ``1 - w`` (the mixture with its diagonal parts, a lift per coordinate),
   rounded to nearest; the class residue is split by its components and each
   is added to its HOST, the first element in the DESIGNATION ORDER whose
   structural support in the handed datum contains it; the first ``w`` at
   which every component has a host and every element is decided positive
   semidefinite gives the family (:func:`_snap_for_fidelity`);
3. *The last resort*: where no ``w`` does, the uniform lift
   ``(1 - w) A_v + w (q_t / n) 1`` from the handed datum, flagged
   ``support_not_preserved`` (:func:`_last_resort`), with its fall-back on the
   round-down candidates of :mod:`certiqs_key.foundations.rungs`.

A class that step (1) does not keep is MOVED. It is disclosed in the record
(``req:emission-record``), and the run rests on
``foundations/ass:snapped-measurement`` (A-SNAP) there unless it evaluates the
class off its snap; under the strict option a moved class is refused at
emission where no reference companion is formed
(``req:emission-refusal``), which :func:`certiqs_key.reductions.emit.reduce`
decides, since it is the one that forms the companion.

STEP (4) IS NOT RUN HERE. "ALL SIX CONDITIONS ARE DECIDED LAST", and the
decision is the emitted-family row
(:func:`certiqs_key.reductions.validation.rule_emitted_family`), which fires on
the numbers :func:`normalize` returns. On declared data that pass the refusal
rules every path below produces a family the six conditions hold of, so the
row is a DEFENSIVE EXACT CHECK (``thm:emit`` (ii), proof): a handed class that
is not Hermitian positive semidefinite is passed through untouched and refused
there, never repaired here.

NUMPY-FREE ON PURPOSE. Importing :mod:`certiqs_key.reductions` pulls in no array
library (``tests/golden/test_reductions_docking.py``), so the exact decisions
come from :mod:`certiqs_key.foundations.exact`, and the weight ladder and the
round-down candidates are the ONE COPY in :mod:`certiqs_key.foundations.rungs`.
"""

from __future__ import annotations

import math
from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from fractions import Fraction

from certiqs_key.foundations.exact import (
    Cx,
    Matrix,
    add,
    identity,
    is_hermitian,
    is_positive_semidefinite,
    lattice_round_matrix,
    on_lattice,
    scale,
    subtract,
    zeros,
)
from certiqs_key.foundations.rungs import round_down as shared_round_down
from certiqs_key.foundations.rungs import (
    round_down_candidates as shared_candidates,
)
from certiqs_key.foundations.rungs import rung_ladder
from certiqs_key.reductions.errors import MalformedInputError
from certiqs_key.reductions.inputs import JointOutcome, Label

__all__ = [
    "BlockSnap",
    "ClassSnap",
    "ClassStatus",
    "EmissionStep",
    "JointClass",
    "Normalization",
    "designation_order",
    "entrywise_max_modulus_squared",
    "in_support",
    "normalize",
    "round_down",
    "round_down_candidates",
    "structural_support",
]


@dataclass(frozen=True)
class JointClass:
    """One class ``V_t`` of the joint alphabet, with its exact lattice weight.

    Definition ``def:joint-family``: ``V = bigsqcup_t V_t`` with exact lattice
    weights ``q_t > 0`` summing to one. ``names`` is what a member is called
    WITHIN its class -- for ``V = Y x T`` that is the detection letter ``y`` --
    and it is what a host is recorded as, so that the emitted record names an
    outcome the way the declaration does.
    """

    label: Label
    weight: Fraction
    members: tuple[JointOutcome, ...]
    names: tuple[str, ...]


class ClassStatus(StrEnum):
    """What the normalizer did to one class at one data sector."""

    #: Step (1): every element already on the lattice.
    KEPT = "kept"
    #: Step (2) or (3) snapped it.
    MOVED = "moved"
    #: The handed class is not Hermitian positive semidefinite, which the
    #: definition's hypothesis ``A in D_adm`` excludes: passed through
    #: untouched, and refused by step (4), never repaired.
    NOT_ADMISSIBLE = "not_admissible"


class EmissionStep(StrEnum):
    """Which step of ``def:emitnorm`` snapped a moved class."""

    #: Step (2), the snap for fidelity.
    SNAP_FOR_FIDELITY = "snap_for_fidelity"
    #: Step (3), the flagged last resort.
    LAST_RESORT = "last_resort"


@dataclass(frozen=True, slots=True)
class ClassSnap:
    """What the normalizer did to ONE class at ONE data sector.

    The per-class fields of ``req:emission-record``: whether the class was
    kept or moved, and for a moved class the step (2) or (3) that snapped it,
    the weight ``w`` taken or the fall-back of (3), the hosts of the
    components of its residue under (2), and the flag
    ``support_not_preserved`` of a class snapped by (3).
    """

    label: Label
    status: ClassStatus
    step: EmissionStep | None = None
    #: The hosts of the residue's components under (2), in component order;
    #: under (3) the first element in the designation order, which takes the
    #: completeness residue.
    hosts: tuple[str, ...] = ()
    #: ``w`` of (2) or (3), where a weight of their ladder was taken.
    mixing_weight: Fraction | None = None
    #: (3) fell back to the round-down candidates below ``B^{1/2}``.
    mixing_fallback: bool = False
    #: Under (3): whether at every ``w`` of (2) some component of the residue
    #: had no host (rather than every element hosting its component but some
    #: element failing positivity).
    component_without_host: bool = False
    support_not_preserved: bool = False
    #: (3)'s mixing share ``1 / n`` per element of the support.
    uniform_share: Fraction | None = None

    @property
    def moved(self) -> bool:
        """Whether the class is moved (``def:emitnorm``: not kept by (1))."""
        return self.status is ClassStatus.MOVED

    def as_record(self) -> dict[str, object]:
        """JSON-ready: exact rationals as strings."""
        return {
            "class": self.label,
            "status": str(self.status),
            "kept": self.status is ClassStatus.KEPT,
            "step": None if self.step is None else str(self.step),
            "hosts": list(self.hosts),
            "mixing_weight": (
                None if self.mixing_weight is None else str(self.mixing_weight)
            ),
            "mixing_fallback": self.mixing_fallback,
            "component_without_host": self.component_without_host,
            "support_not_preserved": self.support_not_preserved,
        }


@dataclass(frozen=True, slots=True)
class BlockSnap:
    """What the normalizer did to ONE data sector, class by class.

    One record per data sector -- "the sectors the normalizer touches and the
    only ones both data have" (Eq. ``eq:displacement``).
    """

    block_index: int
    #: Per class, in the declared order of the classes.
    classes: Mapping[Label, ClassSnap]
    #: Eq. eq:displacement, as the EXACT SQUARE of the entrywise maximum
    #: modulus; ``Delta_s`` itself is "the square root of an exact rational and
    #: IN GENERAL IRRATIONAL" (thm:emit (i)).
    displacement_squared: Fraction

    @property
    def already_on_lattice(self) -> bool:
        """``def:emitnorm``, first property: every class kept."""
        return all(snap.status is ClassStatus.KEPT for snap in self.classes.values())

    @property
    def moved(self) -> tuple[ClassSnap, ...]:
        """The moved classes of this sector."""
        return tuple(snap for snap in self.classes.values() if snap.moved)

    @property
    def displacement(self) -> float:
        """``Delta_s`` in binary64 -- THE ONE EMITTED NUMBER THAT IS NOT EXACT."""
        return math.sqrt(self.displacement_squared)


@dataclass(frozen=True, slots=True)
class Normalization:
    """The declared datum ``A'`` of the data sectors, with what produced it."""

    #: Per outcome, the declared datum of every data sector, in the declared
    #: order of the data sectors.
    family: Mapping[JointOutcome, tuple[Matrix, ...]]
    #: One record per data sector, in sector order.
    blocks: tuple[BlockSnap, ...]

    @property
    def moved(self) -> tuple[tuple[int, ClassSnap], ...]:
        """Every moved class, with its data sector."""
        return tuple(
            (block.block_index, snap) for block in self.blocks for snap in block.moved
        )


# ---------------------------------------------------------------------------
#  Small exact helpers
# ---------------------------------------------------------------------------


def in_support(
    names: Sequence[str], support: Collection[str] | None
) -> tuple[str, ...]:
    """Return the members of a class inside the sector's declared support.

    ``None`` is the DEFAULT support ``V``. The declared order is preserved,
    because it breaks the designation order's ties.
    """
    if support is None:
        return tuple(names)
    return tuple(name for name in names if name in support)


def _exact_trace(m: Matrix) -> Fraction:
    """Return the real part of the exact trace of a block."""
    return sum((m[index][index].re for index in range(len(m))), start=Fraction(0))


def designation_order(
    names: Sequence[str], family: Mapping[str, Matrix]
) -> tuple[str, ...]:
    """``def:emitnorm``: the DESIGNATION ORDER of a class.

    "ranks the elements of a class in the sector's support by largest exact
    trace and, among equal traces, by the declared order of the class". A tie
    is exact and ordinary: a sector symmetric under a relabelling of the class
    ties every element, and the declared order then names the element, so the
    order is a function of the declaration and of nothing else.
    """
    position = {name: index for index, name in enumerate(names)}
    return tuple(
        sorted(names, key=lambda name: (-_exact_trace(family[name]), position[name]))
    )


def structural_support(m: Matrix) -> frozenset[int]:
    """Return the indices ``i`` whose row or column ``i`` holds a non-zero entry.

    ``foundations/def:snap``'s structural support, which step (2) places a
    residue component by, read on the HANDED datum.
    """
    size = len(m)
    return frozenset(
        index
        for index in range(size)
        if any(not m[index][j].is_zero for j in range(size))
        or any(not m[j][index].is_zero for j in range(size))
    )


def _sum(family: Sequence[Matrix], dim: int) -> Matrix:
    total = zeros(dim)
    for element in family:
        total = add(total, element)
    return total


def _complement(weight: Fraction, others: Sequence[Matrix], dim: int) -> Matrix:
    """``q_t 1 - sum others``, exactly."""
    return subtract(scale(weight, identity(dim)), _sum(others, dim))


def _psd(m: Matrix) -> bool:
    return is_hermitian(m) and is_positive_semidefinite(m)


def entrywise_max_modulus_squared(left: Matrix, right: Matrix) -> Fraction:
    """``max_{jk} |left_jk - right_jk|^2``, exact (Eq. ``eq:displacement``).

    The square of the modulus is a rational and stays in the substrate; the
    modulus itself is taken once, at the boundary, in binary64.
    """
    best = Fraction(0)
    for row_left, row_right in zip(left, right, strict=True):
        for entry_left, entry_right in zip(row_left, row_right, strict=True):
            difference = entry_left - entry_right
            squared = difference.re * difference.re + difference.im * difference.im
            if squared > best:
                best = squared
    return best


# ---------------------------------------------------------------------------
#  Step (3)'s fall-back: the round-down candidates
# ---------------------------------------------------------------------------


def round_down_candidates(element: Matrix, kappa: int) -> tuple[Matrix, ...]:
    """``def:emitnorm`` (3): the candidate list of the last resort's fall-back.

    "``B^{1/2}_v`` itself; then, for ``r = kappa, kappa-1, ..., 1`` in this
    order, the shift ``B - 2^-r 1`` and the scaling ``(1 - 2^-r) B``, each
    rounded to nearest at ``kappa``; finally the zero matrix". The list is a
    function of the element and ``kappa`` alone, and it is the one copy of
    :func:`certiqs_key.foundations.rungs.round_down_candidates`.
    """
    return shared_candidates(element, kappa)


def round_down(element: Matrix, kappa: int) -> Matrix:
    """``def:emitnorm`` (3): the first candidate ``0 <= A' <= B`` on the lattice.

    Implements Eq. ``eq:rounddown`` for one element: the first matrix of
    :func:`round_down_candidates` that is Hermitian, satisfies Eq.
    ``eq:latinv`` entry by entry and lies between ``0`` and the element in the
    Loewner order, each decided exactly; the search is the shared one
    (:func:`certiqs_key.foundations.rungs.round_down`). The zero matrix always
    qualifies, the element being positive semidefinite.
    """
    return shared_round_down(
        element,
        kappa,
        below=lambda candidate: is_positive_semidefinite(subtract(element, candidate)),
    )


def _round_nearest(element: Matrix, kappa: int) -> Matrix:
    """Every part of every entry to the nearest ``2^-kappa`` multiple, ties to even."""
    return lattice_round_matrix(element, kappa)


# ---------------------------------------------------------------------------
#  Step (2): the residue, its components, and their hosts
# ---------------------------------------------------------------------------


def _components(residue: Matrix) -> tuple[frozenset[int], ...]:
    """``def:emitnorm`` (2): the components of a class residue.

    "the classes of the equivalence relation on the indices ``i`` whose row
    ``i`` of ``E`` is non-zero generated by ``i ~ l`` whenever ``E_il != 0``".
    In the order of their least index.
    """
    size = len(residue)
    active = [
        i for i in range(size) if any(not residue[i][j].is_zero for j in range(size))
    ]
    parent = {i: i for i in active}

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i in active:
        for j in active:
            if not residue[i][j].is_zero:
                root_i, root_j = find(i), find(j)
                if root_i != root_j:
                    parent[max(root_i, root_j)] = min(root_i, root_j)
    groups: dict[int, set[int]] = {}
    for i in active:
        groups.setdefault(find(i), set()).add(i)
    return tuple(frozenset(groups[root]) for root in sorted(groups))


def _restricted(residue: Matrix, component: frozenset[int]) -> Matrix:
    """``E_C``: ``E`` on the entries whose row and column lie in ``C``, else 0."""
    size = len(residue)
    zero = Cx(Fraction(0), Fraction(0))
    return tuple(
        tuple(
            residue[i][j] if i in component and j in component else zero
            for j in range(size)
        )
        for i in range(size)
    )


def _place_components(
    family: dict[str, Matrix],
    residue: Matrix,
    order: Sequence[str],
    supports: Mapping[str, frozenset[int]],
) -> tuple[str, ...] | None:
    """Add each component of ``residue`` to its host, in place.

    Returns ``None`` where some component has no host.

    ``def:emitnorm`` (2): "Each ``E_C`` is added to the first element
    ``A'_u`` in the designation order whose structural support in the handed
    datum, that of ``A_u``, contains ``C``." Returns the hosts in component
    order.
    """
    hosts: list[str] = []
    for component in _components(residue):
        host = next((name for name in order if component <= supports[name]), None)
        if host is None:
            return None
        family[host] = add(family[host], _restricted(residue, component))
        hosts.append(host)
    return tuple(hosts)


def _snap_for_fidelity(
    handed: Mapping[str, Matrix],
    order: Sequence[str],
    supports: Mapping[str, frozenset[int]],
    weight: Fraction,
    dim: int,
    kappa: int,
) -> tuple[dict[str, Matrix], Fraction, tuple[str, ...]] | bool:
    """``def:emitnorm`` (2): snapped close to the handed datum.

    For ``w = 0`` and then ``2^-kappa, ..., 2^-1``, every element is the
    handed one with its off-diagonal entries multiplied by ``1 - w`` (the
    mixture with its diagonal parts, a lift per coordinate), rounded to
    nearest; the class residue is split by components and each is placed on
    its host; the first ``w`` at which every component has a host and every
    element is decided positive semidefinite gives the family. Where no ``w``
    does, returns whether some ``w`` gave every component a host (``False``:
    a component had no host at every ``w``).
    """
    hosted = False
    for w in (Fraction(0), *rung_ladder(kappa)):
        family: dict[str, Matrix] = {}
        for name in order:
            element = handed[name]
            dephased = tuple(
                tuple(
                    entry if i == j else Cx(entry.re * (1 - w), entry.im * (1 - w))
                    for j, entry in enumerate(row)
                )
                for i, row in enumerate(element)
            )
            family[name] = _round_nearest(dephased, kappa)
        residue = _complement(weight, [family[name] for name in order], dim)
        hosts = _place_components(family, residue, order, supports)
        if hosts is None:
            continue
        hosted = True
        if all(_psd(family[name]) for name in order):
            return family, w, hosts
    return hosted


def _last_resort(
    handed: Mapping[str, Matrix],
    order: Sequence[str],
    weight: Fraction,
    dim: int,
    kappa: int,
) -> tuple[dict[str, Matrix], Fraction | None, Fraction]:
    """``def:emitnorm`` (3): the uniform lift, flagged ``support_not_preserved``.

    ``B^w_v = (1 - w) A_v + w (q_t / n) 1`` over the ``n`` elements of the
    class in the sector's support, starting from the HANDED datum; for each
    ``w`` of the ladder, smallest first, every element but the first in the
    designation order is rounded to nearest (ties to even) and the first takes
    ``q_t 1`` minus the rest; the first ``w`` at which every element so formed
    is decided positive semidefinite gives the family. Where none does, every
    element but the first takes the first round-down candidate below
    ``B^{1/2}`` and the first takes ``q_t 1`` minus the rest. Returns the
    family, the ``w`` taken (``None`` for the fall-back) and the share ``1/n``.
    """
    count = len(order)
    share = Fraction(1, count)
    first = order[0]

    def mixed(w: Fraction) -> dict[str, Matrix]:
        uniform = scale(w * weight * share, identity(dim))
        return {name: add(scale(1 - w, handed[name]), uniform) for name in order}

    for w in rung_ladder(kappa):
        lifted = mixed(w)
        family = {name: _round_nearest(lifted[name], kappa) for name in order[1:]}
        family[first] = _complement(weight, [family[name] for name in order[1:]], dim)
        if all(_psd(family[name]) for name in order):
            return family, w, share
    lifted = mixed(Fraction(1, 2))
    family = {name: round_down(lifted[name], kappa) for name in order[1:]}
    family[first] = _complement(weight, [family[name] for name in order[1:]], dim)
    return family, None, share


# ---------------------------------------------------------------------------
#  One class at one data sector
# ---------------------------------------------------------------------------


def _snap_class(
    group: JointClass,
    handed: Mapping[str, Matrix],
    inside: Sequence[str],
    dim: int,
    kappa: int,
) -> tuple[dict[str, Matrix], ClassSnap]:
    """Run ``def:emitnorm`` (1)--(3) on one class at one sector."""
    if not all(_psd(handed[name]) for name in inside):
        return dict(handed), ClassSnap(
            label=group.label, status=ClassStatus.NOT_ADMISSIBLE
        )

    # --- (1) keep -------------------------------------------------------------
    if all(on_lattice(handed[name], kappa) for name in inside):
        return dict(handed), ClassSnap(label=group.label, status=ClassStatus.KEPT)

    order = designation_order(inside, handed)
    supports = {name: structural_support(handed[name]) for name in inside}

    # --- (2) snap for fidelity --------------------------------------------------
    close = _snap_for_fidelity(handed, order, supports, group.weight, dim, kappa)
    if not isinstance(close, bool):
        family, w, hosts = close
        return family, ClassSnap(
            label=group.label,
            status=ClassStatus.MOVED,
            step=EmissionStep.SNAP_FOR_FIDELITY,
            hosts=hosts,
            mixing_weight=w,
        )

    # --- (3) the last resort ----------------------------------------------------
    family, lift, share = _last_resort(handed, order, group.weight, dim, kappa)
    return family, ClassSnap(
        label=group.label,
        status=ClassStatus.MOVED,
        step=EmissionStep.LAST_RESORT,
        hosts=(order[0],),
        mixing_weight=lift,
        mixing_fallback=lift is None,
        component_without_host=not close,
        support_not_preserved=True,
        uniform_share=share,
    )


def normalize(
    data: Mapping[JointOutcome, tuple[Matrix, ...]],
    *,
    classes: Sequence[JointClass],
    sector_dimensions: Sequence[int],
    kappa: int,
    supports: Sequence[frozenset[JointOutcome] | None] | None = None,
) -> Normalization:
    r"""Run the emission normalizer on every data sector and class.

    Implements ``reductions/def:emitnorm``, steps (1)--(3).

    Per data sector and per class: keep; snap for fidelity; and, where that
    yields no family, the flagged last resort. Step (4) is the emitted-family
    row.

    Args:
        data: the handed datum ``A^(s)_v`` per outcome and then per data
            sector, formed exactly by the instance's own construction.
        classes: the class decomposition of ``V`` with its exact weights.
        sector_dimensions: the declared dimension of each data sector.
        kappa: the declared lattice exponent, already validated.
        supports: ``V^(s)`` of each data sector; ``None`` is the default
            support ``V``. An element outside the support is passed through
            untouched.

    Returns:
        The declared datum ``A'`` and one record per data sector.
    """
    normalized: dict[JointOutcome, list[Matrix]] = {
        member: [] for group in classes for member in group.members
    }
    records: list[BlockSnap] = []

    for index, dim in enumerate(sector_dimensions):
        support = None if supports is None else supports[index]
        displacement_squared = Fraction(0)
        per_class: dict[Label, ClassSnap] = {}
        for group in classes:
            names = group.names
            source = {
                name: data[member][index]
                for name, member in zip(names, group.members, strict=True)
            }
            inside = tuple(
                name
                for name, member in zip(names, group.members, strict=True)
                if support is None or member in support
            )
            if not inside:
                raise MalformedInputError(
                    "def:reduction-instance (I1) requires a data sector's "
                    "declared support to MEET EVERY CLASS; this class has no "
                    "element inside it"
                )
            snapped, record = _snap_class(
                group, {name: source[name] for name in inside}, inside, dim, kappa
            )
            per_class[group.label] = record
            for name, member in zip(names, group.members, strict=True):
                element = snapped.get(name, source[name])
                normalized[member].append(element)
                squared = entrywise_max_modulus_squared(element, source[name])
                if squared > displacement_squared:
                    displacement_squared = squared
        records.append(
            BlockSnap(
                block_index=index,
                classes=per_class,
                displacement_squared=displacement_squared,
            )
        )

    return Normalization(
        family={outcome: tuple(blocks) for outcome, blocks in normalized.items()},
        blocks=tuple(records),
    )
