"""The reference companion: the same instance, run on the handed reference.

``reductions/req:reference-companion``, by ``reductions/cor:reference-companion``
and ``reductions/lem:row-relaxation``; for the flat instance (H-REF) is
``reductions/wpfss/cor:flat-companion``.

WHERE IT IS FORMED (``req:reference-companion``, its opening and (vi)): where a
claim establishes (H-REF) for the instance and either the declaring instance
hands its reference on at least one block or the emission normalizer moved at
least one class. Where no block is handed, ``G`` is the instance's snapped
family and the companion's datum is the HANDED DATUM, the producer's exact
construction before the normalizer (``cor:reference-companion`` (i)): the
classes the normalizer moved are then evaluated off their snap while the
instance's own moved blocks stay snapped.

WHY THIS EXISTS. The run searches on the declaration compiled from the snapped
measurement, and the first-order bound is then evaluated on the declaration
compiled from the receiver's reference at the points the search found
(``meat-core/frank-wolfe/req:bracket-on-reference``). The snap then only steers
the search: a block on which the companion carries the reference is
``foundations/def:evaluated-off-snap`` and rests on no premise about the snap.
The companion is the same chain run on other data, so it is built HERE, where
the artefact is built, by the same builder, and carries the same shape by
construction.

WHAT IS FORMED, IN ORDER (``req:reference-companion`` (i)-(v)):

1. every handed enclosure is recentred (``foundations/lem:recentred-enclosure``
   (i)), entries whose disc contains zero getting centre zero;
2. the builder is called in COMPANION MODE
   (:class:`~certiqs_key.reductions.instance.CompanionMode`) on the rows whose
   blocks are the recentred centres where handed and the snapped blocks
   elsewhere: no normalizer, no lattice condition, the same weight route,
   scalar values, sectors and supports. The datum its rule
   (I1) forms is the centre of the companion's datum enclosure;
3. the same builder on the RADII forms the radius of that enclosure: the rule of
   (I1) of every instance with a companion claim in this tree is
   ``A^(m)_(y,t) = q_t sum_y' R^cg_{y|y'} K^(m)_{y'|t}`` (or ``q_t K^(m)_{y|t}``
   in the dark-composed form), a combination with NON-NEGATIVE coefficients
   (``q_t > 0``; ``R^cg`` entrywise non-negative, ``wpfss/lem:descent``), and
   ``receiver/lem:enclosure-arithmetic`` gives such a combination of enclosed
   numbers the radius ``sum |coefficient| r``, which is the same combination of
   the radii (``cor:reference-companion`` (iii));
4. the datum's enclosure is made Hermitian with symmetric radii (lemma part
   (iv)) and recentred again, element by element and block by block;
5. the instance at the recentred centre gives the companion's target, and its
   emitted entries are the companion's entries ``(O_k, bowtie_k, c_k)``; the
   enclosure of each entry operator is ``sum_v |alpha_{k,v,s}| R_v^(s)``
   (``cor:reference-companion`` (iii)), formed here by perturbing the datum of
   one element at a time by its radius and reading the change of each entry,
   which is ``alpha_{k,v,s} R_v^(s)`` for an entry affine in the datum;
6. each entry is rounded to binary64 with its constant moved outward by the
   exactly computed ``delta_k`` (``lem:row-relaxation``; ``req:reference-companion``
   (iii)); ``delta_k = 0`` leaves the entry as it is, an equality included.

ENTRIES A CALLER REQUESTED (``carried_operators``) ARE FORMED ON THE COMPANION
WHERE THEIR CERTIFICATE IS ESTABLISHED THERE (``req:reference-companion`` (iii);
``cor:reference-companion`` (vi)).
Each is formed at the writing of ``eq:instance-entry`` by which the builder
recognised it (:class:`~certiqs_key.reductions.constraints.EntryWriting`):

* a default carried operator requested as an entry (``cor:entries`` (i)), a
  sum of sector projectors, is the artefact's operator at every admissible
  datum, radius zero, and its pull-back is positive at the companion's datum
  as at every other (``cor:reference-companion`` (vi));
* the class-marginal entry of ``rem:unsound`` is the artefact's operator at
  every admissible datum, radius zero, and carries its certificate wherever
  the instance discharges ``eq:instance-classmarginal``, as the artefact's
  builder decided (``cor:reference-companion`` (vi));
* the operator ``eq:two-sector-entry`` is formed at the companion's datum,
  ``F_e[A^ref] - a Pi_{<=N} - b Pi_Flag``, and carried where the condition
  ``eq:companion-two-sector`` of ``wpfss/cor:flat-companion`` holds, decided exactly
  on the recentred enclosure of the datum: every below-cutoff block of the
  centre clears ``a`` by the block's row-sum radius, and ``b <= p_e``. Only an
  instance whose builder names that claim (:data:`COMPANION_ENTRY_CLAIMS`)
  forms it.

Every formed entry is then relaxed outward like the instance's own
(``lem:row-relaxation``). An entry not formed has no entry in its place:
leaving it out only enlarges the companion's feasible set
(``meat-core/prop:reference-companion``), so no bound formed on the companion
is raised by it; the record names it with its reason.

FACTOR ENCLOSURES (``req:reference-companion`` (vii)). Where the handed
reference carries factor enclosures (the receiver's, on the blocks of a
component graph whose count admits them) and the builder names a claim that
its rule of (I1) is a non-negative combination (``factor_claim``: the flat
instance's ``wpfss/cor:flat-companion``), every element of the datum whose
combining blocks all carry one gets :func:`combined_factor` of theirs
(``cor:companion-factor-enclosure`` (i)), emitted as the factor enclosure of
the target's block on that data sector (its (ii)) beside the entrywise
enclosure, which it does not alter. A builder that names no such claim -- a
branching submodule's, the branching and register instances -- carries none, and the
record says so per element.

EXACT DATA ARE KEPT. Centres are Gaussian rationals and radii rationals,
entry by entry, so that an entry the reference knows exactly is carried exactly
with radius zero; nothing here rounds but the entries of step 6, which a
solver's oracle reads as constraints. Whoever evaluates the companion rounds
its family (``meat-core/req:companion-admission`` (iii)); a later certified
evaluation reads the exact data here and needs no other path (the interface's
``exact_data_note``).
"""

from __future__ import annotations

import hashlib
import json
import math
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from enum import StrEnum
from fractions import Fraction
from typing import Final

from certiqs_key.foundations.exact import (
    Cx,
    Matrix,
    identity,
    loewner_ge,
    scale,
    subtract,
    zeros,
)
from certiqs_key.foundations.recentring import (
    EntrywiseEnclosure,
    Radii,
    hermitian_enclosure,
    recentred_enclosure,
)
from certiqs_key.foundations.reference import FactorEnclosure
from certiqs_key.reductions.channels import ChannelWitness
from certiqs_key.reductions.constraints import (
    WRITING_CLASS_MARGINAL,
    WRITING_DEFAULT_CARRIED,
    WRITING_TWO_SECTOR,
    ConstraintEntry,
    EntryWriting,
    theta_typing,
)
from certiqs_key.reductions.inputs import (
    HandedReference,
    JointOutcome,
    Label,
    ReductionCall,
)
from certiqs_key.reductions.instance import (
    BuildContext,
    CompanionMode,
    InstanceBuilder,
    ReductionInstance,
)
from certiqs_key.reductions.normalizer import JointClass
from certiqs_key.reductions.reasons import Relation, Route
from certiqs_key.reductions.sectors import SectorKind

__all__ = [
    "CLASS_MARGINAL_CLAIM",
    "COMPANION_ENTRY_CLAIMS",
    "CompanionAbsence",
    "CompanionBlock",
    "CompanionEntry",
    "NoReferenceCompanion",
    "NotFormedReason",
    "ReferenceCompanion",
    "RequestedEntry",
    "block_name",
    "combined_factor",
    "reference_companion",
    "relaxed_entries",
]

#: What establishes the certificate of a requested class-marginal entry, and of
#: a requested default carried operator, at the companion's datum, for every
#: instance with a companion (``cor:reference-companion`` (vi)).
CLASS_MARGINAL_CLAIM: Final[str] = "reductions/cor:reference-companion (vi)"

#: The name of a builder's attribute that maps a writing kind other than the
#: class-marginal one to the claim stating, for that builder's instance, the
#: condition on an enclosure of the companion's datum under which the entry's
#: certificate holds (``req:reference-companion`` (iii)). A builder without it,
#: or without the kind, forms no such entry on the companion.
COMPANION_ENTRY_CLAIMS: Final[str] = "companion_entry_claims"

def block_name(photons: int, setting: Label) -> str:
    """Return ``m=<photons>, t=<setting>``: one block of the declaring snap.

    The declaring party's snap record spells an instance-snap block so
    (:attr:`~certiqs_key.reductions.inputs.InstanceSnapBlock.name`), and a block
    the companion carries and a block a record names as resting are joined by
    name.
    """
    return f"m={photons}, t={setting}"


class CompanionAbsence(StrEnum):
    """Why no companion is emitted: ``req:reference-companion`` (vi).

    The requirement's third case -- a reciprocal node of the rule of (I1) that
    receives no enclosure, so that ``cor:reference-companion`` (iii) gives none
    -- has no member, because no builder of this engine binds a rule with a
    reciprocal: every builder with a ``companion_claim`` is the flat builder or
    lifts it, and that instance's rule is
    ``A^(m)_(y,t) = q_t sum_y' R^cg_{y|y'} K^(m)_{y'|t}`` (or ``q_t K^(m)_{y|t}``),
    a non-negative combination with no reciprocal node
    (``wpfss/cor:flat-companion``). The radius step of :func:`reference_companion`
    rests on exactly that. ``tests/unit/test_reductions_decided_certificates.py``
    holds the list of such builders, so that a builder with another rule fails
    there until its rule is examined and this case is given its member.
    """

    #: The declaring instance hands the reference on no block and the emission
    #: normalizer moved no class, so nothing would be evaluated off its snap.
    NO_BLOCK_HANDED_NO_CLASS_MOVED = "no_block_handed_no_class_moved"
    #: No claim of this module establishes (H-REF) for the instance.
    NO_H_REF_CLAIM = "no_h_ref_claim"
    #: The builder built no instance in companion mode. Defensive: the rows a
    #: builder decides read no datum, so they decide the same as for the
    #: artefact, which was emitted.
    NOT_BUILT = "companion_instance_not_built"


@dataclass(frozen=True)
class NoReferenceCompanion:
    """The record that no companion was emitted, and which condition failed."""

    reason: CompanionAbsence
    detail: str = ""

    def as_record(self) -> dict[str, object]:
        """JSON-ready."""
        return {"emitted": False, "reason": str(self.reason), "detail": self.detail}


@dataclass(frozen=True)
class CompanionBlock:
    """One block ``(m, t)`` of the family ``G`` (``req:reference-companion`` (v))."""

    setting: Label
    photons: int
    #: Whether the companion carries the HANDED REFERENCE here, or the snapped
    #: block the instance declares.
    handed: bool
    #: ``exact`` (every radius zero) or ``enclosed`` on a handed block; ``None``
    #: on a snapped one.
    kind: str | None = None
    #: The largest radius of the block after recentring.
    largest_radius: Fraction = Fraction(0)
    #: The entries the recentring set to zero on this block.
    recentred_entries: int = 0
    #: On a block the companion carries snapped: how many of its letters the
    #: handed reference named all the same. A block handed for only some
    #: letters is carried snapped in full (``_handed_rows``); a non-zero count
    #: says the declaring instance handed it in part.
    partially_handed_letters: int = 0

    @property
    def name(self) -> str:
        """The block's name, as the declaring party's snap record names it."""
        return block_name(self.photons, self.setting)

    def as_record(self) -> dict[str, object]:
        """JSON-ready, exact rationals as strings."""
        return {
            "block": self.name,
            "setting": self.setting,
            "photons": self.photons,
            "carries": "handed_reference" if self.handed else "snapped_block",
            "kind": self.kind,
            "largest_radius": str(self.largest_radius),
            "recentred_entries": self.recentred_entries,
            "partially_handed_letters": self.partially_handed_letters,
        }


class NotFormedReason(StrEnum):
    """Why a requested entry is not formed on the companion (item (iii))."""

    #: The builder recorded no writing of ``eq:instance-entry`` for the entry.
    NO_WRITING = "no_writing"
    #: No claim of this module states, for this instance, a condition on an
    #: enclosure of the companion's datum under which the entry's certificate
    #: holds.
    NO_CLAIM_FOR_INSTANCE = "no_claim_for_instance"
    #: The claim's condition fails on the recentred enclosure of the datum.
    CERTIFICATE_NOT_ESTABLISHED = "certificate_not_established"


@dataclass(frozen=True)
class RequestedEntry:
    """One entry a caller requested, formed on the companion or not.

    ``req:reference-companion`` (v): the record names every requested entry
    formed on the companion with what established its certificate there
    (``established_by``), and every one not formed with the reason.
    """

    label: str
    #: The writing kind the entry was recognised at, where one was recorded.
    writing: str | None
    formed: bool
    #: Formed: the claim that established its certificate at the companion.
    established_by: str | None = None
    #: Not formed: why.
    reason: NotFormedReason | None = None
    detail: str = ""

    def as_record(self) -> dict[str, object]:
        """JSON-ready."""
        return {
            "label": self.label,
            "writing": self.writing,
            "formed": self.formed,
            "established_by": self.established_by,
            "reason": None if self.reason is None else str(self.reason),
            "detail": self.detail,
        }


@dataclass(frozen=True)
class CompanionEntry:
    """One emitted entry of the companion, with what produced it.

    ``entry`` is the entry a consumer reads: its operator is binary64 entry by
    entry (exact :class:`~certiqs_key.foundations.exact.Cx` of binary64
    values), Hermitian with the blocks of the exact entry. ``relaxed`` marks an
    entry formed by ``lem:row-relaxation`` (``delta > 0``); where ``delta`` is
    zero the exact entry is emitted as it is. Its certificate is the exact
    entry's case, discharged by ``lem:row-relaxation`` (ii).
    """

    entry: ConstraintEntry
    relaxes: str
    delta: Fraction
    relaxed: bool

    def as_record(self) -> dict[str, object]:
        """JSON-ready: no operator, which travels with the entry itself."""
        return {
            "label": self.entry.label,
            "relaxes": self.relaxes,
            "relation": str(self.entry.relation),
            "constant": str(self.entry.constant),
            "delta": str(self.delta),
            "delta_float": float(self.delta),
            "relaxed": self.relaxed,
            "certificate": str(self.entry.certificate_kind),
        }


@dataclass(frozen=True)
class ReferenceCompanion:
    """``req:reference-companion``: the companion emitted beside the artefact.

    EVALUATION-ONLY (item (v)): it has no run of its own, no consumer
    admitting it as the declaration of a run, and what a consumer decides or
    computes of it beside the declaration it accompanies is the consumer's
    (``meat-core/req:companion-admission``). Its shape is the artefact's
    (item (ii)): the same sector map, alphabet, classes, weights, scalar values
    and party partition, the target differing on the data sectors alone.
    """

    #: Per joint outcome, the centre of every sector block of the target, in the
    #: sector map's order (data sectors carry the datum, scalar sectors the
    #: scalar values, exactly).
    target_centre: Mapping[JointOutcome, tuple[Matrix, ...]]
    #: The matching radii: the datum's on the data sectors, zero elsewhere.
    target_radius: Mapping[JointOutcome, tuple[Radii, ...]]
    entries: tuple[CompanionEntry, ...]
    blocks: tuple[CompanionBlock, ...]
    datum_recentred_entries: int
    datum_largest_radius: Fraction
    #: Every entry a caller requested beside the instance's own, formed or not
    #: (item (iii), (v)).
    requested_entries: tuple[RequestedEntry, ...]
    #: The claim establishing (H-REF) for the instance.
    claim: str
    #: Item (ii): the artefact's channel witness, read at the companion's
    #: datum, and the labels of its transported set there, the relaxed
    #: entries' operators among them with their pull-backs (item (iii)).
    channel_witness: str = ""
    transported: tuple[str, ...] = ()
    #: The channel the instance is precomposed with, where it is
    #: (``lem:precomposed-instance``): the companion's channel is the
    #: artefact's, that channel acting first, and its pull-backs are taken
    #: through that channel's adjoint (``wpfss/req:normalized-link-record``,
    #: the companion's link "recorded the same way";
    #: ``wpfss/cor:normalized-flat`` (iv)). ``None``, and no record key,
    #: where nothing is precomposed.
    precomposed_with: ChannelWitness | None = None
    #: Wall-clock seconds the formation took. A diagnostic; not in the record,
    #: which must not depend on the machine.
    seconds: float = field(default=0.0, compare=False)
    #: Item (vii): per joint outcome, the factor enclosure of every sector
    #: block of the target, in the sector map's order, ``None`` where none is
    #: carried (every scalar sector, and every data sector some combining
    #: block of which carries none); empty where none is carried at all.
    target_factors: Mapping[JointOutcome, tuple[FactorEnclosure | None, ...]] = (
        field(default_factory=dict)
    )
    #: The claim that shows the instance's rule of (I1) a non-negative
    #: combination (the builder's ``factor_claim``), or ``None``: then no
    #: factor enclosure is carried.
    factor_claim: str | None = None
    #: The positions of the target's data sectors in its sector map.
    data_sectors: tuple[int, ...] = ()

    @property
    def evaluation_only(self) -> bool:
        """Always true: a companion has no run of its own.

        A consumer evaluates it beside the declaration it accompanies, and may
        search on it there (the polish of
        ``meat-core/frank-wolfe/req:bracket-on-reference`` (i)); it is never
        the declaration of a run.
        """
        return True

    @property
    def handed_blocks(self) -> tuple[CompanionBlock, ...]:
        """The blocks on which the companion carries the handed reference."""
        return tuple(block for block in self.blocks if block.handed)

    @property
    def formed_from(self) -> str:
        """``handed_reference`` where some block is handed, else ``handed_datum``.

        Where no block is handed the companion carries the snapped block on
        every block, so its datum is the handed datum: the producer's exact
        construction before the normalizer (``cor:reference-companion`` (i)).
        """
        return "handed_reference" if self.handed_blocks else "handed_datum"

    @property
    def requested_entries_formed(self) -> tuple[RequestedEntry, ...]:
        """The requested entries formed on the companion."""
        return tuple(item for item in self.requested_entries if item.formed)

    @property
    def requested_entries_not_formed(self) -> tuple[RequestedEntry, ...]:
        """The requested entries not formed on the companion, with the reason."""
        return tuple(item for item in self.requested_entries if not item.formed)

    def exact_data_digest(self) -> str:
        """Return the SHA-256 of the exact centres and radii, canonically written."""
        payload = {
            "|".join(str(part) for part in outcome): {
                "centre": [
                    [[str(entry) for entry in row] for row in block]
                    for block in self.target_centre[outcome]
                ],
                "radius": [
                    [[str(entry) for entry in row] for row in block]
                    for block in self.target_radius[outcome]
                ],
            }
            for outcome in self.target_centre
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def as_record(self) -> dict[str, object]:
        """JSON-ready: the record of item (v), and a digest of the exact data.

        The exact centres and radii are not written out: their rationals grow
        with the cutoff, and the record travels with every run. The digest pins
        them; :attr:`target_centre` and :attr:`target_radius` hold them.
        """
        record: dict[str, object] = {
            "emitted": True,
            "evaluation_only": True,
            "claim": self.claim,
            "formed_from": self.formed_from,
            "channel_witness": self.channel_witness,
            "transported": list(self.transported),
            "blocks": [block.as_record() for block in self.blocks],
            "handed_blocks": [block.name for block in self.handed_blocks],
            "datum_recentred_entries": self.datum_recentred_entries,
            "datum_largest_radius": str(self.datum_largest_radius),
            "datum_largest_radius_float": float(self.datum_largest_radius),
            "entries": [entry.as_record() for entry in self.entries],
            "requested_entries_formed": [
                item.as_record() for item in self.requested_entries_formed
            ],
            "requested_entries_not_formed": [
                item.as_record() for item in self.requested_entries_not_formed
            ],
            "exact_data_sha256": self.exact_data_digest(),
            "factor_enclosures": self.factor_record(),
        }
        if self.precomposed_with is not None:
            record["precomposed_with"] = self.precomposed_with.as_machine_record()
        return record

    def factor_record(self) -> dict[str, object]:
        """Item (vii)'s record: per element of the datum, carried or why not.

        ``outcome`` is the joint outcome ``y|t`` and ``data_sector`` the
        sector's position in the target's sector map; a carried one with its
        number of columns, otherwise its cause: the builder's, where it names
        no combination claim, else a combining block without one.
        """
        missing = (
            "combining_block_without_factor"
            if self.factor_claim is not None
            else "no_non_negative_combination_claim"
        )
        elements: list[dict[str, object]] = []
        for outcome in self.target_centre:
            factors = self.target_factors.get(outcome, ())
            for index in self.data_sectors:
                factor = factors[index] if index < len(factors) else None
                elements.append(
                    {
                        "outcome": "|".join(str(part) for part in outcome),
                        "data_sector": index,
                        "carried": factor is not None,
                        "columns": None if factor is None else factor.columns,
                        "cause": None if factor is not None else missing,
                    }
                )
        return {
            "claim": self.factor_claim,
            "cause": None if self.factor_claim is not None else missing,
            "carried": sum(1 for item in elements if item["carried"]),
            "elements": elements,
        }


#: The two outcomes of :func:`reference_companion`.
type CompanionOutcome = ReferenceCompanion | NoReferenceCompanion

#: Every value the companion's record takes as "the kind" of a handed block.
_EXACT: Final[str] = "exact"
_ENCLOSED: Final[str] = "enclosed"


def _radius_matrix(radii: Radii) -> Matrix:
    """Return non-negative rational radii as a real exact matrix."""
    return tuple(tuple(Cx(r, Fraction(0)) for r in row) for row in radii)


def _radii_of(matrix: Matrix) -> Radii:
    """Return the real parts of a matrix the radius run formed, as radii.

    The radius run applies a combination with non-negative coefficients to
    real non-negative matrices (module docstring, step 3), so every entry it
    forms is real and non-negative; a negative or complex entry would mean the
    instance's rule is not of that form, which this refuses rather than reads.
    """
    out: list[tuple[Fraction, ...]] = []
    for row in matrix:
        values = []
        for entry in row:
            if entry.im != 0 or entry.re < 0:
                raise ValueError(
                    "the instance's datum rule formed a radius that is not a "
                    "non-negative real number; its rule is not a combination with "
                    "non-negative coefficients, which the companion's enclosure "
                    "of cor:reference-companion (iii) is formed for here"
                )
            values.append(entry.re)
        out.append(tuple(values))
    return tuple(out)


def _zero_radii(size: int) -> Radii:
    return tuple(tuple(Fraction(0) for _ in range(size)) for _ in range(size))


def _largest(radii: Radii) -> Fraction:
    return max((r for row in radii for r in row), default=Fraction(0))


def _down(value: Fraction) -> Fraction:
    """Return the largest binary64 number at most ``value``, exactly."""
    nearest = float(value)
    if Fraction(nearest) > value:
        nearest = math.nextafter(nearest, -math.inf)
    return Fraction(nearest)


def _up(value: Fraction) -> Fraction:
    """Return the smallest binary64 number at least ``value``, exactly."""
    nearest = float(value)
    if Fraction(nearest) < value:
        nearest = math.nextafter(nearest, math.inf)
    return Fraction(nearest)


def _nearest_cx(entry: Cx) -> Cx:
    """Round each part to the nearest binary64, ties to even (``float``)."""
    return Cx(Fraction(float(entry.re)), Fraction(float(entry.im)))


def _handed_rows(
    call: ReductionCall, handed: HandedReference
) -> tuple[
    dict[JointOutcome, tuple[Matrix, ...]],
    dict[JointOutcome, tuple[Matrix, ...]],
    tuple[CompanionBlock, ...],
    dict[JointOutcome, tuple[FactorEnclosure | None, ...]],
]:
    """Return the centre and radius blocks of ``G``, its record and its factors.

    The factors are the factor enclosures the handed reference carries on the
    blocks ``G`` carries handed (item (vii)), ``None`` on every other block.

    ``G`` carries the recentred handed enclosure where a block is handed and the
    snapped block, with radius zero, elsewhere (``cor:reference-companion``;
    ``req:reference-companion`` (i)). A block ``(m, t)`` is handed when every
    letter's element at it is, and THE DECISION IS TAKEN PER BLOCK BEFORE ANY
    ENCLOSURE IS READ: where the handed reference names only some letters of a
    block, every letter of that block carries the snapped element, and the
    block is recorded as ``snapped_block`` with the letters that were handed
    (``partially_handed_letters``). Mixing the two inside one block would give
    a ``G^(b)`` that is neither the handed reference nor ``K^(b)``, whose
    completeness identities (H-REF) needs hold of neither.
    """
    rows = call.artifact_rows
    # Pass 1: per block (t, m), the letters whose element is handed, and all
    # the letters the block has.
    letters: dict[tuple[Label, int], int] = {}
    given_letters: dict[tuple[Label, int], int] = {}
    for key, snapped in rows.photon_blocks.items():
        _, setting = key
        given = handed.blocks.get(key, ())
        for photons in range(len(snapped)):
            where = (setting, photons)
            letters[where] = letters.get(where, 0) + 1
            if photons < len(given) and given[photons] is not None:
                given_letters[where] = given_letters.get(where, 0) + 1
    whole = {
        where for where, count in letters.items() if given_letters.get(where) == count
    }
    # Pass 2: the rows of G, a whole block handed or none of it.
    centres: dict[JointOutcome, tuple[Matrix, ...]] = {}
    radii: dict[JointOutcome, tuple[Matrix, ...]] = {}
    factors: dict[JointOutcome, tuple[FactorEnclosure | None, ...]] = {}
    per_block: dict[tuple[Label, int], list[tuple[EntrywiseEnclosure, int]]] = {}
    for key, snapped in rows.photon_blocks.items():
        _, setting = key
        given = handed.blocks.get(key, ())
        centre_row: list[Matrix] = []
        radius_row: list[Matrix] = []
        factor_row: list[FactorEnclosure | None] = []
        for photons, block in enumerate(snapped):
            enclosure = given[photons] if photons < len(given) else None
            if enclosure is None or (setting, photons) not in whole:
                centre_row.append(block)
                radius_row.append(_radius_matrix(_zero_radii(len(block))))
                factor_row.append(None)
                continue
            recentred, changed = recentred_enclosure(enclosure)
            centre_row.append(recentred.centre)
            radius_row.append(_radius_matrix(recentred.radii))
            factor_row.append(enclosure.factor)
            per_block.setdefault((setting, photons), []).append((recentred, changed))
        centres[key] = tuple(centre_row)
        radii[key] = tuple(radius_row)
        factors[key] = tuple(factor_row)
    blocks: list[CompanionBlock] = []
    settings = list(dict.fromkeys(setting for _, setting in rows.photon_blocks))
    for setting in settings:
        photons_seen = sorted(
            photons for (where, photons) in letters if where == setting
        )
        for photons in photons_seen:
            where = (setting, photons)
            members = per_block.get(where, [])
            handed_here = where in whole
            largest = max(
                (enclosure.largest_radius for enclosure, _ in members),
                default=Fraction(0),
            )
            blocks.append(
                CompanionBlock(
                    setting=setting,
                    photons=photons,
                    handed=handed_here,
                    kind=(
                        None
                        if not handed_here
                        else _EXACT if largest == 0 else _ENCLOSED
                    ),
                    largest_radius=largest,
                    recentred_entries=sum(changed for _, changed in members),
                    partially_handed_letters=(
                        0 if handed_here else given_letters.get(where, 0)
                    ),
                )
            )
    return centres, radii, tuple(blocks), factors


def combined_factor(
    terms: Sequence[tuple[Fraction, FactorEnclosure | None]], dimension: int
) -> FactorEnclosure | None:
    """Return the factor enclosure of ``sum lambda K`` from the terms' own.

    Implements ``reductions/cor:companion-factor-enclosure`` (i): the boxes of the
    combining blocks (``lambda > 0``) side by side in the terms' order, their
    centres and radii unaltered, and the core of the ``lambda W`` in exact
    rational arithmetic; no column where every ``lambda`` is zero. ``None``
    where a combining block carries no factor enclosure, or a coefficient is
    negative (the rule is then no non-negative combination).
    """
    centre: list[tuple[Cx, ...]] = [() for _ in range(dimension)]
    radii: list[tuple[Fraction, ...]] = [() for _ in range(dimension)]
    core: list[Fraction] = []
    for coefficient, factor in terms:
        if coefficient < 0:
            return None
        if coefficient == 0:
            continue
        if factor is None or factor.dimension != dimension:
            return None
        for i in range(dimension):
            centre[i] += factor.centre[i]
            radii[i] += factor.radii[i]
        core.extend(coefficient * weight for weight in factor.core)
    return FactorEnclosure(tuple(centre), tuple(radii), tuple(core))


def _datum_factors(
    builder: InstanceBuilder,
    call: ReductionCall,
    factors: Mapping[JointOutcome, tuple[FactorEnclosure | None, ...]],
) -> tuple[str | None, Mapping[JointOutcome, tuple[FactorEnclosure | None, ...]]]:
    """Return item (vii)'s claim and the factor enclosures of the datum's elements.

    ``reductions/req:reference-companion`` (vii): only through a rule a claim
    of this module shows to be a non-negative combination (the builder's
    ``factor_claim``, with its ``datum_factors``,
    ``reductions/cor:companion-factor-enclosure`` (i)); none for any other
    builder, nor where the handed reference carries none.
    """
    claim = getattr(builder, "factor_claim", None)
    method = getattr(builder, "datum_factors", None)
    if not isinstance(claim, str) or method is None:
        return None, {}
    if all(factor is None for row in factors.values() for factor in row):
        return claim, {}
    found = method(call, factors)
    return claim, ({} if found is None else found)


def _context(
    call: ReductionCall,
    *,
    lattice_exponent: int,
    route: Route,
    classes: tuple[JointClass, ...],
    override: Mapping[JointOutcome, tuple[Matrix, ...]] | None = None,
) -> BuildContext:
    return BuildContext(
        request=call,
        lattice_exponent=lattice_exponent,
        route=route,
        classes=classes,
        core_ready=True,
        companion=CompanionMode(override=override),
    )


def _built(
    builder: InstanceBuilder, context: BuildContext
) -> tuple[
    ReductionInstance | None, Mapping[JointOutcome, tuple[Matrix, ...]] | None
]:
    """Run the builder in companion mode; return the instance and its datum."""
    outcome = builder.build(context)
    assert context.companion is not None
    captured = context.companion.captured
    return outcome.instance, (captured[-1] if captured else None)


def _recentred_datum(
    centre: Mapping[JointOutcome, tuple[Matrix, ...]],
    radius: Mapping[JointOutcome, tuple[Matrix, ...]],
) -> tuple[
    dict[JointOutcome, tuple[Matrix, ...]],
    dict[JointOutcome, tuple[Radii, ...]],
    int,
]:
    """Make the datum's enclosure Hermitian, then recentre it, block by block."""
    centres: dict[JointOutcome, tuple[Matrix, ...]] = {}
    radii: dict[JointOutcome, tuple[Radii, ...]] = {}
    changed = 0
    for outcome, blocks in centre.items():
        centre_row: list[Matrix] = []
        radius_row: list[Radii] = []
        for block, radius_block in zip(blocks, radius[outcome], strict=True):
            enclosure = hermitian_enclosure(block, _radii_of(radius_block))
            recentred, count = recentred_enclosure(enclosure)
            changed += count
            centre_row.append(recentred.centre)
            radius_row.append(recentred.radii)
        centres[outcome] = tuple(centre_row)
        radii[outcome] = tuple(radius_row)
    return centres, radii, changed


def _plus_radius(block: Matrix, radii: Radii) -> Matrix:
    return tuple(
        tuple(
            entry + Cx(r, Fraction(0))
            for entry, r in zip(row, radius_row, strict=True)
        )
        for row, radius_row in zip(block, radii, strict=True)
    )


def _entry_radii(
    builder: InstanceBuilder,
    call: ReductionCall,
    centre: Mapping[JointOutcome, tuple[Matrix, ...]],
    radius: Mapping[JointOutcome, tuple[Radii, ...]],
    entries: Sequence[ConstraintEntry],
    emitted: Callable[[ReductionInstance, Route | None], tuple[ConstraintEntry, ...]],
    *,
    lattice_exponent: int,
    route: Route,
    classes: tuple[JointClass, ...],
) -> dict[str, list[Radii]]:
    """Return, per entry label, the radius of every sector block of its operator.

    ``cor:reference-companion`` (iii): ``sum_v |alpha_{k,v,s}| R_v^(s)`` on a
    data sector ``s`` and zero on a scalar one. Each element ``v`` whose radius
    is not zero is perturbed alone by its radius, and the change it makes to an
    entry's block ``s`` is ``alpha_{k,v,s} R_v^(s)`` exactly (an entry operator
    is affine in the datum, eq:instance-entry); its modulus, summed over ``v``,
    is the radius. Elements known exactly add nothing and cost no call.
    """
    totals: dict[str, list[list[list[Fraction]]]] = {
        entry.label: [
            [[Fraction(0)] * len(block) for _ in range(len(block))]
            for block in entry.operator
        ]
        for entry in entries
    }
    base = {entry.label: entry for entry in entries}
    for outcome, radii in radius.items():
        if all(_largest(block) == 0 for block in radii):
            continue
        override = dict(centre)
        override[outcome] = tuple(
            _plus_radius(block, block_radii)
            for block, block_radii in zip(centre[outcome], radii, strict=True)
        )
        instance, _ = _built(
            builder,
            _context(
                call,
                lattice_exponent=lattice_exponent,
                route=route,
                classes=classes,
                override=override,
            ),
        )
        if instance is None:  # pragma: no cover - the rows read no datum
            raise ValueError("the builder built no instance at a perturbed datum")
        for moved in emitted(instance, route):
            if moved.label not in base:
                continue
            for index, (after, before) in enumerate(
                zip(moved.operator, base[moved.label].operator, strict=True)
            ):
                total = totals[moved.label][index]
                for i, (row_after, row_before) in enumerate(
                    zip(after, before, strict=True)
                ):
                    for j, (a, b) in enumerate(zip(row_after, row_before, strict=True)):
                        change = a - b
                        if not change.is_zero:
                            total[i][j] += abs(change.re) + abs(change.im)
    return {
        label: [tuple(tuple(row) for row in block) for block in blocks]
        for label, blocks in totals.items()
    }


def relaxed_entries(
    entry: ConstraintEntry,
    radii: Sequence[Radii],
    call: ReductionCall,
) -> tuple[CompanionEntry, ...]:
    """Return the emitted entries of one exact entry: ``req:reference-companion`` (iii).

    The binary64 operator ``O'`` nearest to the centre, part by part; the
    rationals ``rho_il = |Re(O' - C)| + |Im(O' - C)| + R_il`` and
    ``delta = max_i sum_l rho_il``, computed exactly (the operator is
    block-diagonal, so a row's sum is its block's); and the relaxed entries of
    ``lem:row-relaxation`` at ``delta``. Rounding to nearest, ties to even, is
    odd under negation, so ``O'`` is Hermitian and keeps the exact entry's
    blocks.
    """
    rounded: list[Matrix] = []
    delta = Fraction(0)
    for block, block_radii in zip(entry.operator, radii, strict=True):
        near = tuple(tuple(_nearest_cx(value) for value in row) for row in block)
        rounded.append(near)
        for row, near_row, radius_row in zip(block, near, block_radii, strict=True):
            total = Fraction(0)
            for value, approx, r in zip(row, near_row, radius_row, strict=True):
                total += abs(approx.re - value.re) + abs(approx.im - value.im) + r
            delta = max(delta, total)
    if delta == 0:
        return (
            CompanionEntry(
                entry=entry, relaxes=entry.label, delta=delta, relaxed=False
            ),
        )
    mode = call.declaration.source_mode
    operator = tuple(rounded)
    out: list[CompanionEntry] = []
    if entry.relation in (Relation.GE, Relation.EQ):
        constant = _down(entry.constant - delta)
        out.append(
            CompanionEntry(
                entry=replace(
                    entry,
                    label=f"{entry.label} [relaxed >=]",
                    operator=operator,
                    relation=Relation.GE,
                    constant=constant,
                    theta_typing=theta_typing(mode, constant),
                ),
                relaxes=entry.label,
                delta=delta,
                relaxed=True,
            )
        )
    if entry.relation in (Relation.LE, Relation.EQ):
        constant = _up(entry.constant + delta)
        out.append(
            CompanionEntry(
                entry=replace(
                    entry,
                    label=f"{entry.label} [relaxed <=]",
                    operator=operator,
                    relation=Relation.LE,
                    constant=constant,
                    theta_typing=theta_typing(mode, constant),
                ),
                relaxes=entry.label,
                delta=delta,
                relaxed=True,
            )
        )
    return tuple(out)


def _block_radius_sum(radii: Radii) -> Fraction:
    """Return ``max_i sum_l R_il``: the bound on the eigenvalues of a deviation."""
    return max((sum(row, Fraction(0)) for row in radii), default=Fraction(0))


def _two_sector_companion_form(
    artefact_entry: ConstraintEntry,
    writing: EntryWriting,
    instance: ReductionInstance,
    order: Sequence[JointOutcome],
    target_radius: Mapping[JointOutcome, tuple[Radii, ...]],
) -> tuple[ConstraintEntry, list[Radii]] | str:
    """Return the companion form of an ``eq:two-sector-entry`` entry, or why it fails.

    ``wpfss/cor:flat-companion``: at the writing with coefficient ``1`` for
    ``e`` on every sector of the branch and ``Z = -a Pi_{<=N} - b Pi_Flag``,
    the companion form is ``F_e[A^ref] - a Pi_{<=N} - b Pi_Flag``, which
    carries the certificate where ``eq:companion-two-sector`` holds:
    ``C^(m)_e - (a + rho_m) 1 >= 0`` on every below-cutoff block, with
    ``rho_m = max_i sum_l R^(m)_{e,il}``, and ``b <= p_e``. Decided exactly on
    the recentred enclosure of the datum, whose centre the companion instance
    carries (``instance``) and whose radius ``target_radius`` holds. Returns
    the entry with the artefact's label, relation, constant and form, and the
    radius of every sector block of its operator.
    """
    assert writing.outcome is not None
    outcome = writing.outcome
    index = list(order).index(outcome)
    sectors = instance.sectors
    in_branch = sectors.sectors_inside(*writing.branch)
    in_data = sectors.sectors_inside(*writing.data_part)
    leq = sectors.block_projector(*writing.data_part)
    flag = sectors.block_projector(*writing.flag_part)
    centre = instance.target_povm[index]
    radius = target_radius[outcome]
    for block, block_radii, inside in zip(centre, radius, in_data, strict=True):
        if not inside:
            continue
        rho = _block_radius_sum(block_radii)
        if not loewner_ge(block, scale(writing.below + rho, identity(len(block)))):
            return (
                "eq:companion-two-sector fails: a below-cutoff block of the centre "
                f"does not clear a = {writing.below} by its row-sum radius "
                f"{float(rho):.3e}"
            )
    weight = instance.weights[outcome]
    if writing.above > weight:
        return (
            f"eq:companion-two-sector fails: b = {writing.above} exceeds the routed "
            f"weight p_e = {weight}"
        )
    operator = tuple(
        subtract(
            subtract(
                block if inside else zeros(len(block)),
                scale(writing.below, leq_block),
            ),
            scale(writing.above, flag_block),
        )
        for block, inside, leq_block, flag_block in zip(
            centre, in_branch, leq, flag, strict=True
        )
    )
    radii = [
        block_radii if inside else _zero_radii(len(block_radii))
        for block_radii, inside in zip(radius, in_branch, strict=True)
    ]
    return replace(artefact_entry, operator=operator), radii


def _requested_on_companion(
    builder: InstanceBuilder,
    requested: Sequence[tuple[ConstraintEntry, EntryWriting | None]],
    instance: ReductionInstance,
    order: Sequence[JointOutcome],
    target_radius: Mapping[JointOutcome, tuple[Radii, ...]],
) -> tuple[list[tuple[ConstraintEntry, list[Radii]]], list[RequestedEntry]]:
    """Form every requested entry on the companion where its certificate holds.

    ``req:reference-companion`` (iii); ``cor:reference-companion`` (vi). Returns
    the exact entries formed, each with the radius of every block of its
    operator, and the record of every requested entry.
    """
    claims: Mapping[str, str] = getattr(builder, COMPANION_ENTRY_CLAIMS, None) or {}
    formed: list[tuple[ConstraintEntry, list[Radii]]] = []
    record: list[RequestedEntry] = []
    for entry, writing in requested:
        if writing is None:
            record.append(
                RequestedEntry(
                    label=entry.label,
                    writing=None,
                    formed=False,
                    reason=NotFormedReason.NO_WRITING,
                    detail="the builder recorded no writing of eq:instance-entry "
                    "by which it recognised the entry",
                )
            )
            continue
        if writing.kind in (WRITING_CLASS_MARGINAL, WRITING_DEFAULT_CARRIED):
            formed.append(
                (entry, [_zero_radii(len(block)) for block in entry.operator])
            )
            record.append(
                RequestedEntry(
                    label=entry.label,
                    writing=writing.kind,
                    formed=True,
                    established_by=CLASS_MARGINAL_CLAIM,
                )
            )
            continue
        claim = claims.get(writing.kind)
        if claim is None or writing.kind != WRITING_TWO_SECTOR:
            record.append(
                RequestedEntry(
                    label=entry.label,
                    writing=writing.kind,
                    formed=False,
                    reason=NotFormedReason.NO_CLAIM_FOR_INSTANCE,
                    detail="no claim of this module states, for "
                    f"{type(builder).__name__}, a condition on an enclosure of "
                    "the companion's datum under which the certificate of a "
                    f"{writing.kind} entry holds",
                )
            )
            continue
        outcome = _two_sector_companion_form(
            entry, writing, instance, order, target_radius
        )
        if isinstance(outcome, str):
            record.append(
                RequestedEntry(
                    label=entry.label,
                    writing=writing.kind,
                    formed=False,
                    reason=NotFormedReason.CERTIFICATE_NOT_ESTABLISHED,
                    detail=outcome,
                )
            )
            continue
        formed.append(outcome)
        record.append(
            RequestedEntry(
                label=entry.label,
                writing=writing.kind,
                formed=True,
                established_by=claim,
            )
        )
    return formed, record


def reference_companion(
    call: ReductionCall,
    builder: InstanceBuilder,
    *,
    lattice_exponent: int,
    route: Route,
    classes: tuple[JointClass, ...],
    emitted: Callable[[ReductionInstance, Route | None], tuple[ConstraintEntry, ...]],
    classes_moved: bool,
    requested: Sequence[tuple[ConstraintEntry, EntryWriting | None]] = (),
) -> CompanionOutcome:
    """Form the reference companion of the emitted instance, or say why there is none.

    Implements ``reductions/req:reference-companion`` (i)-(vi) by
    ``reductions/cor:reference-companion`` and ``reductions/lem:row-relaxation``;
    (H-REF) for the instance is the builder's ``companion_claim``
    (``reductions/wpfss/cor:flat-companion`` for the flat instance). Called by
    :func:`certiqs_key.reductions.emit.reduce` with the same lattice exponent,
    route and classes as the artefact; ``emitted`` is the core's emission rule
    for an instance's entries (``cor:entries``), so that the companion's list is
    emitted by the rule the artefact's is. ``classes_moved`` says whether the
    emission normalizer moved a class, which forms a companion where no block
    is handed; ``requested`` is every entry a caller requested that the
    artefact carries, with the writing by which the builder recognised it.
    """
    started = time.perf_counter()
    claim = getattr(builder, "companion_claim", None)
    if not isinstance(claim, str):
        return NoReferenceCompanion(
            CompanionAbsence.NO_H_REF_CLAIM,
            f"no claim of this module establishes (H-REF) for {type(builder).__name__}",
        )
    handed = call.artifact_rows.handed_reference
    if handed is None:
        handed = HandedReference(blocks={})
    centre_rows, radius_rows, blocks, handed_factors = _handed_rows(call, handed)
    if not any(block.handed for block in blocks) and not classes_moved:
        # Item (vi): a block handed for only some of its letters is not handed
        # (``_handed_rows``), so a reference that hands no block whole hands
        # none; and where the normalizer moved no class either, nothing would
        # be evaluated off its snap.
        partial = [block.name for block in blocks if block.partially_handed_letters]
        return NoReferenceCompanion(
            CompanionAbsence.NO_BLOCK_HANDED_NO_CLASS_MOVED,
            "the declaring instance hands the reference on no block whole and "
            "the emission normalizer moved no class"
            + ("" if not partial else f" (handed in part: {', '.join(partial)})"),
        )
    base_request = replace(call.request, carried_operators=())
    rows = replace(
        call.artifact_rows,
        photon_blocks=centre_rows,
        instance_snap=None,
        handed_reference=None,
    )
    centre_call = replace(call, artifact_rows=rows, request=base_request)
    radius_call = replace(
        centre_call, artifact_rows=replace(rows, photon_blocks=radius_rows)
    )
    _, datum = _built(
        builder,
        _context(
            centre_call, lattice_exponent=lattice_exponent, route=route, classes=classes
        ),
    )
    _, radius = _built(
        builder,
        _context(
            radius_call, lattice_exponent=lattice_exponent, route=route, classes=classes
        ),
    )
    if datum is None or radius is None:
        return NoReferenceCompanion(
            CompanionAbsence.NOT_BUILT,
            "the builder formed no datum in companion mode",
        )
    centre, radii, recentred = _recentred_datum(datum, radius)
    instance, _ = _built(
        builder,
        _context(
            centre_call,
            lattice_exponent=lattice_exponent,
            route=route,
            classes=classes,
            override=centre,
        ),
    )
    if instance is None:
        return NoReferenceCompanion(
            CompanionAbsence.NOT_BUILT,
            "the builder built no instance at the companion's datum",
        )
    order = call.declaration.joint_alphabet
    data_positions = [
        index
        for index, sector in enumerate(instance.sectors.sectors)
        if sector.kind is SectorKind.DATA
    ]
    dimensions = instance.sectors.dimensions
    target_centre = {
        outcome: instance.target_povm[index] for index, outcome in enumerate(order)
    }
    target_radius: dict[JointOutcome, tuple[Radii, ...]] = {}
    for outcome in order:
        data = iter(radii[outcome])
        target_radius[outcome] = tuple(
            next(data) if index in data_positions else _zero_radii(dimensions[index])
            for index in range(len(dimensions))
        )
    # Item (vii): the datum's factor enclosures, emitted as the target's on its
    # data sectors (cor:companion-factor-enclosure (ii)), the centres and radii
    # of (i) unaltered.
    factor_claim, datum_factors = _datum_factors(builder, call, handed_factors)
    target_factors: dict[JointOutcome, tuple[FactorEnclosure | None, ...]] = {}
    for outcome, row in datum_factors.items():
        data_factors = iter(row)
        target_factors[outcome] = tuple(
            next(data_factors) if index in data_positions else None
            for index in range(len(dimensions))
        )
    exact_entries = emitted(instance, route)
    entry_radii = (
        _entry_radii(
            builder,
            centre_call,
            centre,
            radii,
            exact_entries,
            emitted,
            lattice_exponent=lattice_exponent,
            route=route,
            classes=classes,
        )
        if exact_entries
        else {}
    )
    formed, requested_record = _requested_on_companion(
        builder, requested, instance, order, target_radius
    )
    companion_entries = tuple(
        relaxed
        for entry in exact_entries
        for relaxed in relaxed_entries(entry, entry_radii[entry.label], call)
    ) + tuple(
        relaxed
        for entry, radii_of_entry in formed
        for relaxed in relaxed_entries(entry, radii_of_entry, call)
    )
    return ReferenceCompanion(
        target_centre=target_centre,
        target_radius=target_radius,
        entries=companion_entries,
        blocks=blocks,
        datum_recentred_entries=recentred,
        datum_largest_radius=max(
            (_largest(block) for row in radii.values() for block in row),
            default=Fraction(0),
        ),
        requested_entries=tuple(requested_record),
        claim=claim,
        channel_witness=instance.witness.identity,
        precomposed_with=instance.witness.precomposed_with,
        transported=(
            *(operator.label for operator in instance.transported),
            *(item.entry.label for item in companion_entries),
        ),
        seconds=time.perf_counter() - started,
        target_factors=target_factors,
        factor_claim=factor_claim,
        data_sectors=tuple(data_positions),
    )

