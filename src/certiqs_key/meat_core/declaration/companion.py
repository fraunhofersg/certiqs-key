"""Admission of the compiled reference companion beside its declaration.

``meat-core/req:companion-admission``, by ``meat-core/prop:reference-companion``.

WHY THIS EXISTS. Exact admission (``req:exact-admission``,
``req:declaration-admission``) exists so that the binary64 numbers of a
declaration denote exactly what was declared, which a solver over them needs.
A reference companion has no run of its own (evaluation-only): its value is
bounded below at points of the search on another declaration and of a short
search continued on its own program from them, the polish, whose points serve
only as points at which brackets are formed
(``meat-core/frank-wolfe/req:bracket-on-reference`` (i)); no estimate and no
key length is reported from it save through those brackets, and its family is
not on the binary64 grid. So it is admitted beside the declaration ``D`` it
accompanies, AFTER ``D`` is admitted, and only as follows.

(i) DECIDED EQUAL. The companion is formed FROM ``D``: every component
``prop:reference-companion`` (i) names as shared -- shapes, sector maps and
joint sectors, alphabets and their orders, Alice's slots, the party partition,
the announcement, sifting and raw-key maps, the acceptance set -- is ``D``'s
own object, carried over, so it is equal by construction; what is decided here
is that the measured families it replaces have ``D``'s shape for that factor
(the alphabet's length, the sector count and every block dimension, the labels
having been decided equal by the compiler against the compiled declaration),
and that its list is ``D``'s save the replaced link's entries, each a
Hermitian binary64 operator with the blocks of its scope. A failure is a
companion NOT ADMITTED, with the reason naming the component, and the run
proceeds without it. The maps are generated from the companion's own slots by
whoever evaluates it (``def:maps``); nothing generated from ``D``'s family is
reused.

(ii) IMPORTED, NEVER DECIDED. No condition of ``def:admissible-declaration`` is
decided on the companion's measured family: that it is a POVM is
``reductions/cor:reference-companion`` (i), and with (i) above that gives
``prop:reference-companion`` (ii).

(iii) EVALUATED AND MEASURED. The family is read at the binary64 numbers
nearest the centres of its enclosure (``float`` of a rational, ties to even),
rounded once, here; per block of the measured family the completeness defect
and the least eigenvalue of those numbers are MEASURED and recorded, never
decided, beside the largest radius of the enclosure. What they mean for the
bound is ``meat-core/frank-wolfe/rem:fo-arithmetic``.

(iv) NOTHING ELSE. This module builds the declaration that is evaluated and
the measurements; it solves nothing and reports nothing from it. The one
program solved over the companion is the polish of
``req:bracket-on-reference`` (i), which its evaluation runs.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from enum import StrEnum
from fractions import Fraction

import numpy as np

from certiqs_key.foundations.exact import Matrix as ExactMatrix
from certiqs_key.meat_core.declaration.general import (
    GeneralConstraintEntry,
    GeneralDeclaration,
    GeneralRhsTag,
    MeasuredFactor,
)
from certiqs_key.meat_core.docking import RELATION_TO_CONSUMER
from certiqs_key.meat_core.objective.linalg import Matrix
from certiqs_key.protocol_compiler.companion import CompiledReferenceCompanion

__all__ = [
    "AdmittedCompanion",
    "BlockMeasurement",
    "CompanionNotAdmitted",
    "NotAdmittedReason",
    "admit_reference_companion",
]


class NotAdmittedReason(StrEnum):
    """The components item (i) decides, as the reason that names one."""

    #: A replaced factor is not a measured factor of ``D``, or its alphabet or
    #: its sector map has another shape.
    MEASURED_FAMILY_SHAPE = "companion_measured_family_shape"
    #: The list the companion replaces is not ``D``'s list.
    CONSTRAINT_LIST = "companion_constraint_list"
    #: A replacing entry is not a Hermitian binary64 operator with the blocks
    #: of its scope.
    ENTRY_NOT_HERMITIAN_BINARY64 = "companion_entry_not_hermitian_binary64"


@dataclass(frozen=True)
class CompanionNotAdmitted:
    """A companion item (i) refused, naming the component."""

    reason: NotAdmittedReason
    detail: str

    def as_record(self) -> dict[str, object]:
        """JSON-ready."""
        return {"admitted": False, "reason": str(self.reason), "detail": self.detail}


@dataclass(frozen=True)
class BlockMeasurement:
    """Item (iii) on one block of one measured factor: measured, never decided."""

    factor: str
    sector: str
    #: ``max_ij |(sum_v F_v^(s) - 1)_ij|`` of the evaluated numbers.
    completeness_defect: float
    #: ``min_v lambda_min(F_v^(s))`` of the evaluated numbers.
    least_eigenvalue: float
    #: The largest radius of the block's enclosure, exact.
    largest_radius: Fraction

    def as_record(self) -> dict[str, object]:
        """JSON-ready."""
        return {
            "factor": self.factor,
            "sector": self.sector,
            "completeness_defect": self.completeness_defect,
            "least_eigenvalue": self.least_eigenvalue,
            "largest_radius": str(self.largest_radius),
            "largest_radius_float": float(self.largest_radius),
        }


@dataclass(frozen=True)
class AdmittedCompanion:
    """The companion admitted for evaluation: ``D^ref`` and what was measured."""

    #: ``D^ref``: ``D`` with the replaced measured families at the binary64
    #: numbers nearest their centres and the replaced entries. Evaluation-only:
    #: no run of its own.
    declaration: GeneralDeclaration
    measurements: tuple[BlockMeasurement, ...]
    largest_radius: Fraction
    compiled: CompiledReferenceCompanion

    def as_record(self) -> dict[str, object]:
        """JSON-ready: the admission and item (iii)'s measurements."""
        return {
            "admitted": True,
            "evaluation_only": True,
            "largest_radius": str(self.largest_radius),
            "largest_radius_float": float(self.largest_radius),
            "measurements": [item.as_record() for item in self.measurements],
        }


def _nearest(block: ExactMatrix) -> Matrix:
    """Return the binary64 numbers nearest an exact block, part by part."""
    return np.array(
        [[complex(float(entry.re), float(entry.im)) for entry in row] for row in block],
        dtype=np.complex128,
    )


def _binary64_hermitian(block: ExactMatrix) -> bool:
    """Decide exactly that a block is Hermitian with binary64 entries."""
    size = len(block)
    for i in range(size):
        for j in range(size):
            entry = block[i][j]
            if Fraction(float(entry.re)) != entry.re:
                return False
            if Fraction(float(entry.im)) != entry.im:
                return False
            if entry != block[j][i].conjugate():
                return False
    return True


def _measured(
    label: str,
    sectors: tuple[str, ...],
    family: Mapping[str, Mapping[str, Matrix]],
    radii: Mapping[str, tuple[tuple[tuple[Fraction, ...], ...], ...]],
) -> list[BlockMeasurement]:
    """Return item (iii) per sector block of one factor's evaluated family."""
    out: list[BlockMeasurement] = []
    letters = tuple(family)
    radius_letters = tuple(radii)
    for index, sector in enumerate(sectors):
        blocks = [np.asarray(family[v][sector]) for v in letters]
        total = sum(blocks[1:], blocks[0].copy())
        defect = float(np.max(np.abs(total - np.eye(total.shape[0]))))
        least = min(
            float(np.min(np.linalg.eigvalsh((block + block.conj().T) / 2)))
            for block in blocks
        )
        largest = max(
            (
                r
                for letter in radius_letters
                for row in radii[letter][index]
                for r in row
            ),
            default=Fraction(0),
        )
        out.append(BlockMeasurement(label, sector, defect, least, largest))
    return out


def admit_reference_companion(
    declaration: GeneralDeclaration, companion: CompiledReferenceCompanion
) -> AdmittedCompanion | CompanionNotAdmitted:
    """Admit ``D^ref`` beside an admitted ``D``; it has no run of its own.

    Implements ``meat-core/req:companion-admission`` (i)-(iv); see the module
    docstring. ``declaration`` is ``D`` as the run admitted and solved it
    (wire-labelled where it was read off a bundle): the replaced factors and
    entries are matched to it by position, which the compilation, the docking
    and the bundle all preserve, and the compiler has decided the labels equal
    against the compiled declaration.
    """
    factors = list(declaration.factors)
    measurements: list[BlockMeasurement] = []
    for item in companion.factors:
        if item.position >= len(factors):
            return CompanionNotAdmitted(
                NotAdmittedReason.MEASURED_FAMILY_SHAPE,
                f"measured factor {item.position} is not a factor of the declaration",
            )
        factor = factors[item.position]
        labels = factor.sectors.labels
        dims = tuple(factor.sectors.dims[s] for s in labels)
        if len(factor.alphabet) != len(item.alphabet) or dims != item.sector_dims:
            return CompanionNotAdmitted(
                NotAdmittedReason.MEASURED_FAMILY_SHAPE,
                f"measured factor {factor.label!r}: alphabet of "
                f"{len(item.alphabet)} for {len(factor.alphabet)}, sector "
                f"dimensions {item.sector_dims} for {dims}",
            )
        blocks: dict[str, dict[str, Matrix]] = {}
        radii: dict[str, tuple[tuple[tuple[Fraction, ...], ...], ...]] = {}
        for wire, letter in zip(factor.alphabet, item.alphabet, strict=True):
            blocks[wire] = {
                sector: _nearest(block)
                for sector, block in zip(labels, item.centres[letter], strict=True)
            }
            radii[wire] = item.radii[letter]
        factors[item.position] = MeasuredFactor(
            label=factor.label,
            party=factor.party,
            sectors=factor.sectors,
            alphabet=factor.alphabet,
            blocks=blocks,
            system=factor.system,
        )
        measurements.extend(_measured(factor.label, labels, blocks, radii))
    if companion.base_entry_count != len(declaration.constraint_list):
        return CompanionNotAdmitted(
            NotAdmittedReason.CONSTRAINT_LIST,
            f"the companion replaces entries of a list of "
            f"{companion.base_entry_count}; the declaration has "
            f"{len(declaration.constraint_list)}",
        )
    entries: list[GeneralConstraintEntry] = []
    cursor = 0
    added = 0
    for replacement in sorted(companion.replacements, key=lambda item: item.start):
        entries.extend(declaration.constraint_list[cursor : replacement.start])
        original = declaration.constraint_list[replacement.start : replacement.stop]
        factor = factors[replacement.position]
        labels = factor.sectors.labels
        scope = original[0].scope if original else factor.label
        for entry in replacement.entries:
            operator = entry.operator.blocks
            if len(operator) != len(labels) or not all(
                _binary64_hermitian(block) for block in operator
            ):
                return CompanionNotAdmitted(
                    NotAdmittedReason.ENTRY_NOT_HERMITIAN_BINARY64,
                    f"a replacing entry of measured factor {factor.label!r} is not a "
                    "Hermitian binary64 operator with the blocks of its scope",
                )
            rhs = entry.rhs
            if not isinstance(rhs, Fraction) or Fraction(float(rhs)) != rhs:
                return CompanionNotAdmitted(
                    NotAdmittedReason.ENTRY_NOT_HERMITIAN_BINARY64,
                    "a replacing entry's constant is not a binary64 number",
                )
            # Each replacing entry's tag is its own, read as the general
            # docking reads every entry of D (``def:compile``): off its datum,
            # the arriving tag deciding ``party_local``. Only an entry whose
            # datum spells no admitted form falls back to the tag of the link
            # it replaces.
            own = entry.tag
            tag = (
                GeneralRhsTag(own.value)
                if own is not None
                else original[0].rhs_tag
                if original
                else GeneralRhsTag.HOMOGENEOUS
            )
            entries.append(
                GeneralConstraintEntry(
                    scope=scope,
                    operator_blocks={
                        sector: _nearest(block)
                        for sector, block in zip(labels, operator, strict=True)
                    },
                    relation=RELATION_TO_CONSUMER[entry.relation],
                    bound=float(rhs),
                    rhs_tag=tag,
                )
            )
        added += len(replacement.entries) - len(original)
        cursor = replacement.stop
    entries.extend(declaration.constraint_list[cursor:])
    evaluated = replace(
        declaration,
        factors=tuple(factors),
        constraint_list=tuple(entries),
        constraints_through_a_reductions_chain=(
            declaration.constraints_through_a_reductions_chain + added
        ),
        _product_cache={},
    )
    return AdmittedCompanion(
        declaration=evaluated,
        measurements=tuple(measurements),
        largest_radius=companion.largest_radius,
        compiled=companion,
    )
