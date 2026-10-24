"""The reference companion compiled beside the declaration.

``protocol-compiler/req:reference-companion-compiled``.

WHY THIS EXISTS. A reductions emission may carry, beside its artefact, the
reference companion: the same receiver segment run on the receiver's reference
(``reductions/req:reference-companion``). The run's first-order bound is
evaluated on the declaration compiled from it
(``meat-core/frank-wolfe/req:bracket-on-reference``), so the compiler forms
that declaration beside the one it compiles, BY THE SAME MAP FROM THE SAME
SPECIFICATION: every slot is read from the same data, save the last link's
target family, which is the companion's, and that link's entries, which are the
companion's relaxed entries (item (i); ``meat-core/prop:reference-companion``
(i): the two differ in the measured family and those entries and in nothing
else).

HOW, CONCRETELY. The declaration ``D`` is compiled first and is the template:
its slots are what the compilation map read from the specification, and the
companion changes two of them.

* THE FAMILY of each measured factor whose segment's last link carries a
  companion: the companion's target, labelled by the same rule the docking
  labels the artefact's target (``outcome_label``), and where Bob's family is
  weighted after the chain (``def:weighted``) every product
  ``P(f | t(v)) F_v`` formed EXACTLY from the enclosure: the centre times the
  weight and every radius times its modulus (item (ii)), over the support the
  weighting declares and under the label :func:`setting_joint_label` gives,
  which is what ``setting_weighted_family`` does for ``D``.
* THE ENTRIES: ``D``'s list is ``def:compile``'s concatenation (the
  specification's entries, then the source links', then the receiver links'
  of each factor in order, :func:`~certiqs_key.protocol_compiler.compile.
  emitted_constraint_list`); the positions of each such last link's entries
  are replaced by the companion's relaxed entries, docked as the artefact's
  are (:func:`certiqs_key.reductions.docking.companion_constraint_entries`).

NOTHING IS DECIDED ON IT (item (iii)): no Hermiticity, positivity or
completeness of the family, no completeness sum in a declared order, no chain
condition and no check of the validator; its family is off the binary64 grid
and known through enclosures. That it is a POVM is imported from
``reductions/cor:reference-companion`` (i); the consumer admits it under its own
rule (``meat-core/req:companion-admission``). What IS decided here is that the
companion's shape is ``D``'s, alphabet for alphabet and sector for sector, so
that a mismatch is named rather than compiled.

NO BUNDLE (item (iv)): the result is marked evaluation-only, a declaration
with no run of its own, and refers to the declaration it accompanies; nothing
here writes a bundle.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from fractions import Fraction

from certiqs_key.domain.constraints import ConstraintEntry
from certiqs_key.foundations.blocks import BlockKind, Label
from certiqs_key.foundations.exact import Matrix, scale
from certiqs_key.foundations.recentring import Radii
from certiqs_key.foundations.reference import FactorEnclosure
from certiqs_key.protocol_compiler.chain import ReductionChain
from certiqs_key.protocol_compiler.compile import CompilationResult
from certiqs_key.protocol_compiler.spec import ProtocolSpecification
from certiqs_key.protocol_compiler.weights import setting_joint_label
from certiqs_key.reductions import docking
from certiqs_key.reductions.artifact import ProofReductionArtifact
from certiqs_key.reductions.companion import ReferenceCompanion

__all__ = [
    "CompanionFactor",
    "CompiledReferenceCompanion",
    "EntryReplacement",
    "NoCompiledCompanion",
    "NoCompiledCompanionReason",
    "compile_reference_companion",
]


class NoCompiledCompanionReason(StrEnum):
    """Why no companion was compiled beside the declaration."""

    #: No measured factor's segment was emitted with a companion
    #: (``reductions/req:reference-companion`` (vi) names why, per artefact).
    NO_COMPANION_EMITTED = "no_companion_emitted"
    #: The companion's shape is not the declaration's: an alphabet, a sector
    #: map or the entry positions differ. A defect of one of the two
    #: emissions, named rather than compiled.
    SHAPE_NOT_SHARED = "companion_shape_not_shared"


@dataclass(frozen=True)
class NoCompiledCompanion:
    """The record that no companion was compiled, and why."""

    reason: NoCompiledCompanionReason
    detail: str = ""
    #: Per measured factor, the reductions' record of its companion or of its
    #: absence, carried unchanged.
    records: tuple[Mapping[str, object] | None, ...] = ()

    def as_record(self) -> dict[str, object]:
        """JSON-ready."""
        return {
            "compiled": False,
            "reason": str(self.reason),
            "detail": self.detail,
            "factors": [
                None if record is None else dict(record) for record in self.records
            ],
        }


@dataclass(frozen=True)
class CompanionFactor:
    """One measured factor's family in the companion, exact.

    ``position`` is the factor's place in the declaration's factor list and
    ``alphabet``, ``sector_labels`` and ``sector_dims`` are the declaration's
    for it, decided equal to the companion's; ``centres[v]`` and ``radii[v]``
    are the enclosure of every sector block of ``F^ref_v``, in the sector
    map's order, after the weighting. ``factor_enclosures[v]`` holds, in the
    same order, the factor enclosure carried with each block
    (``foundations/def:factor-enclosure``; item (ii)), ``None`` on a block that
    carries none; a letter absent from it carries none on any block.
    """

    position: int
    label: Label
    alphabet: tuple[Label, ...]
    sector_labels: tuple[Label, ...]
    sector_dims: tuple[int, ...]
    centres: Mapping[Label, tuple[Matrix, ...]]
    radii: Mapping[Label, tuple[Radii, ...]]
    #: The reductions' record of the companion, carried unchanged (item (iv)).
    record: Mapping[str, object]
    factor_enclosures: Mapping[Label, tuple[FactorEnclosure | None, ...]] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        """Refuse a factor enclosure whose shape is not its block's."""
        for letter, enclosures in self.factor_enclosures.items():
            if letter not in self.alphabet or len(enclosures) != len(self.sector_dims):
                raise ValueError(
                    f"factor enclosures of {letter!r}: one per sector of a letter "
                    "of the factor's alphabet"
                )
            for enclosure, dimension in zip(enclosures, self.sector_dims, strict=True):
                if enclosure is not None and enclosure.dimension != dimension:
                    raise ValueError(
                        f"a factor enclosure of {letter!r} has dimension "
                        f"{enclosure.dimension}, its block {dimension}"
                    )

    @property
    def largest_radius(self) -> Fraction:
        """The largest radius of the factor's family."""
        return max(
            (r for blocks in self.radii.values() for block in blocks for row in block
             for r in row),
            default=Fraction(0),
        )


@dataclass(frozen=True)
class EntryReplacement:
    """One last link's entries in the declaration's list, and what replaces them.

    ``start`` and ``stop`` are positions in the declaration's ``constraint_list``
    (``def:compile``'s concatenation); ``entries`` are the companion's relaxed
    entries for that link, docked, with ``deltas`` and ``relaxed`` beside them
    (``reductions/lem:row-relaxation``).
    """

    position: int
    start: int
    stop: int
    entries: tuple[ConstraintEntry, ...]
    deltas: tuple[Fraction, ...]
    relaxed: tuple[bool, ...]


@dataclass(frozen=True)
class CompiledReferenceCompanion:
    """``D^ref``: the compiled reference companion, EVALUATION-ONLY (no run of its own).

    The declaration it accompanies supplies every slot this record does not
    carry (``meat-core/prop:reference-companion`` (i)); what it carries is the
    two that differ: the measured families of :attr:`factors` and the entries
    of :attr:`replacements`, with :attr:`constraint_list` the whole list the
    compilation map gives for ``D^ref``.
    """

    factors: tuple[CompanionFactor, ...]
    replacements: tuple[EntryReplacement, ...]
    constraint_list: tuple[ConstraintEntry, ...]
    #: Per measured factor, the reductions' record (a companion's, or the
    #: record of its absence), in the declaration's factor order.
    records: tuple[Mapping[str, object] | None, ...]
    #: Per measured factor that carries none: why (the reductions' own
    #: reason), by factor label.
    absent: Mapping[Label, str]
    #: The length of the declaration's own list, against which a consumer
    #: decides that the list it admitted is the one replaced here.
    base_entry_count: int
    #: Item (iv): the declaration this is the companion of, by the identifier
    #: the caller gives it (the run tier: its declaration artefact's id).
    companion_of: str = "the declaration compiled from the same specification"

    @property
    def evaluation_only(self) -> bool:
        """Always true: no bundle to be solved is emitted from it (item (iv))."""
        return True

    @property
    def largest_radius(self) -> Fraction:
        """The largest radius of the companion's measured families."""
        return max(
            (factor.largest_radius for factor in self.factors), default=Fraction(0)
        )

    def as_record(self) -> dict[str, object]:
        """JSON-ready: the evaluation-only mark, the factors and the entries."""
        return {
            "compiled": True,
            "evaluation_only": True,
            "companion_of": self.companion_of,
            "factors": [
                {
                    "position": factor.position,
                    "factor": factor.label,
                    "alphabet": list(factor.alphabet),
                    "largest_radius": str(factor.largest_radius),
                    "largest_radius_float": float(factor.largest_radius),
                    "reductions": dict(factor.record),
                }
                for factor in self.factors
            ],
            "absent": dict(self.absent),
            "entry_replacements": [
                {
                    "factor_position": item.position,
                    "replaced": [item.start, item.stop],
                    "emitted": len(item.entries),
                    "deltas": [str(delta) for delta in item.deltas],
                    "relaxed": list(item.relaxed),
                }
                for item in self.replacements
            ],
        }


def _link_ranges(
    specification: ProtocolSpecification, chain: ReductionChain
) -> tuple[dict[int, tuple[int, int]], int]:
    """Return per factor position the range of its last link's entries, and the length.

    Read in the order of ``def:compile``'s concatenation
    (:func:`~certiqs_key.protocol_compiler.compile.emitted_constraint_list`),
    the further factors' links following as the general format appends them.
    """
    position = len(specification.constraints.entries)
    for link in chain.source_segment:
        position += len(link.transported_constraints)
    ranges: dict[int, tuple[int, int]] = {}
    segments: list[ReductionChain] = [chain]
    for part in specification.further_receiver_factors:
        if isinstance(part.chain, ReductionChain):
            segments.append(part.chain)
    for factor, segment in enumerate(segments):
        links = segment.receiver_segment
        for index, link in enumerate(links):
            count = len(link.transported_constraints)
            if index == len(links) - 1:
                ranges[factor] = (position, position + count)
            position += count
    return ranges, position


#: Per outcome label, the factor enclosure of every sector block, or ``None``.
_Factors = dict[Label, tuple[FactorEnclosure | None, ...]]


def _family(
    companion: ReferenceCompanion, artifact: ProofReductionArtifact
) -> tuple[dict[Label, tuple[Matrix, ...]], dict[Label, tuple[Radii, ...]], _Factors]:
    """Return the companion's target, labelled as the docking labels the artefact's.

    With it the factor enclosures the target carries (item (ii);
    ``reductions/req:reference-companion`` (vii)), altered by no step.
    """
    order = artifact.wpfss_data.flag_basis
    settings = docking.probe_settings_of(order)
    centres: dict[Label, tuple[Matrix, ...]] = {}
    radii: dict[Label, tuple[Radii, ...]] = {}
    factors: _Factors = {}
    for outcome in order:
        label = docking.outcome_label(outcome, settings)
        centres[label] = tuple(companion.target_centre[outcome])
        radii[label] = tuple(companion.target_radius[outcome])
        found = companion.target_factors.get(outcome)
        if found is not None:
            factors[label] = tuple(found)
    return centres, radii, factors


def _weighted_factor(
    factor: FactorEnclosure | None, weight: Fraction
) -> FactorEnclosure | None:
    """Return ``protocol-compiler/lem:weighted-factor``: same box, core times ``P``.

    The weight is positive on every pair of the support the weighting
    declares, so the core stays positive; computed in exact rational
    arithmetic.
    """
    if factor is None:
        return None
    return FactorEnclosure(
        factor.centre, factor.radii, tuple(weight * w for w in factor.core)
    )


def _weighted(
    alphabet: Sequence[Label],
    centres: Mapping[Label, tuple[Matrix, ...]],
    radii: Mapping[Label, tuple[Radii, ...]],
    specification: ProtocolSpecification,
    position: int,
    factors: Mapping[Label, tuple[FactorEnclosure | None, ...]],
) -> tuple[
    tuple[Label, ...],
    dict[Label, tuple[Matrix, ...]],
    dict[Label, tuple[Radii, ...]],
    _Factors,
]:
    """Apply the factor's weighting exactly to the enclosure (item (ii)).

    The support and its labels are ``setting_weighted_family``'s: every pair
    ``(v, f)`` with ``P(f | t(v)) > 0``, in the order of ``V`` and then of the
    choice alphabet, labelled by :func:`setting_joint_label`. The centre is
    multiplied by the weight and every radius by its modulus, which encloses
    the product of the weight and the companion's element; a factor
    enclosure keeps its box and takes the weight into its core
    (``protocol-compiler/lem:weighted-factor``). Unweighted, everything passes
    unaltered.
    """
    weighting = specification.receiver_parts[position].choice_weighting
    if weighting is None:
        return tuple(alphabet), dict(centres), dict(radii), dict(factors)
    emitted: list[Label] = []
    out_centres: dict[Label, tuple[Matrix, ...]] = {}
    out_radii: dict[Label, tuple[Radii, ...]] = {}
    out_factors: _Factors = {}
    for outcome in alphabet:
        setting = weighting.setting_of[outcome]
        for choice in weighting.choice_alphabet:
            weight = Fraction(weighting.weight(setting, choice))
            if weight == 0:
                continue
            label = setting_joint_label(outcome, choice)
            emitted.append(label)
            out_centres[label] = tuple(
                scale(weight, block) for block in centres[outcome]
            )
            modulus = abs(weight)
            out_radii[label] = tuple(
                tuple(tuple(modulus * r for r in row) for row in block)
                for block in radii[outcome]
            )
            if outcome in factors:
                out_factors[label] = tuple(
                    _weighted_factor(factor, weight) for factor in factors[outcome]
                )
    return tuple(emitted), out_centres, out_radii, out_factors


def compile_reference_companion(
    specification: ProtocolSpecification,
    compilation: CompilationResult,
    artifacts: Sequence[ProofReductionArtifact],
) -> CompiledReferenceCompanion | NoCompiledCompanion:
    """Compile ``D^ref`` beside ``D``, or record why none is compiled.

    Implements ``protocol-compiler/req:reference-companion-compiled`` (i)-(iv).
    ``artifacts`` are the reductions artefacts of the measured factors, in the
    declaration's factor order (one on the single-device route), each carrying
    its companion or the record of its absence
    (:attr:`~certiqs_key.reductions.artifact.ProofReductionArtifact.reference_companion`).
    """
    declaration = compilation.declaration
    if declaration is None:
        raise ValueError("a refused compilation has no declaration to accompany")
    records = tuple(
        None
        if artifact.reference_companion is None
        else artifact.reference_companion.as_record()
        for artifact in artifacts
    )
    chain = specification.chain
    if not isinstance(chain, ReductionChain):
        raise ValueError("the specification carries no reduction chain")
    ranges, length = _link_ranges(specification, chain)
    labels = declaration.measured_factor_labels
    factors_of_d = declaration.measured_factors
    if len(artifacts) != len(labels) or length != len(declaration.constraint_list):
        return NoCompiledCompanion(
            NoCompiledCompanionReason.SHAPE_NOT_SHARED,
            f"{len(artifacts)} artefact(s) for {len(labels)} measured factor(s); "
            f"the concatenation has {length} entries and the declaration "
            f"{len(declaration.constraint_list)}",
            records,
        )
    companions: list[CompanionFactor] = []
    replacements: list[EntryReplacement] = []
    absent: dict[Label, str] = {}
    for position, artifact in enumerate(artifacts):
        label = labels[position]
        companion = artifact.reference_companion
        if not isinstance(companion, ReferenceCompanion):
            absent[label] = (
                "no_record"
                if companion is None
                else str(companion.as_record().get("reason"))
            )
            continue
        centres, radii, factors = _family(companion, artifact)
        alphabet, centres, radii, factors = _weighted(
            tuple(centres), centres, radii, specification, position, factors
        )
        expected = (
            declaration.bob_alphabet
            if declaration.bob_factors is None
            else declaration.bob_factors.factors[position].alphabet
        )
        sectors = factors_of_d[position].sectors
        dims = tuple(sectors.dims)
        shapes_agree = tuple(expected) == alphabet and all(
            tuple(len(block) for block in centres[letter]) == dims
            for letter in alphabet
        )
        if not shapes_agree:
            return NoCompiledCompanion(
                NoCompiledCompanionReason.SHAPE_NOT_SHARED,
                f"measured factor {label!r}: the companion's alphabet or sector "
                "map is not the declaration's",
                records,
            )
        companions.append(
            CompanionFactor(
                position=position,
                label=label,
                alphabet=alphabet,
                sector_labels=tuple(sectors.labels),
                sector_dims=dims,
                centres=centres,
                radii=radii,
                record=companion.as_record(),
                factor_enclosures=factors,
            )
        )
        start, stop = ranges[position]
        existing = declaration.constraint_list[start:stop]
        if existing or companion.entries:
            scope = existing[0].scope if existing else None
            kind: BlockKind | str = (
                existing[0].operator.sector_map.block_kind
                if existing
                else sectors.block_kind
            )
            docked = docking.companion_constraint_entries(
                companion, artifact, sector_block_kind=kind, factor_scope=scope
            )
            replacements.append(
                EntryReplacement(
                    position=position,
                    start=start,
                    stop=stop,
                    entries=docked,
                    deltas=tuple(item.delta for item in companion.entries),
                    relaxed=tuple(item.relaxed for item in companion.entries),
                )
            )
    if not companions:
        return NoCompiledCompanion(
            NoCompiledCompanionReason.NO_COMPANION_EMITTED,
            "; ".join(f"{label}: {why}" for label, why in absent.items()),
            records,
        )
    entries: list[ConstraintEntry] = []
    cursor = 0
    for item in sorted(replacements, key=lambda replacement: replacement.start):
        entries.extend(declaration.constraint_list[cursor : item.start])
        entries.extend(item.entries)
        cursor = item.stop
    entries.extend(declaration.constraint_list[cursor:])
    return CompiledReferenceCompanion(
        factors=tuple(companions),
        replacements=tuple(replacements),
        constraint_list=tuple(entries),
        records=records,
        absent=absent,
        base_entry_count=len(declaration.constraint_list),
    )
