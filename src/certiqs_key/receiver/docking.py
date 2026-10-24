"""The emitted artifact, in the records the consumer already reads.

THIS IS THE ONLY FILE OF THIS PACKAGE THAT NAMES A CONSUMER'S TYPES
===================================================================
PRINCIPLES.md section 4 lets imports point downward only, and
:mod:`certiqs_key.receiver` is a MODULE: no module carries another module's
package on its own surface. This file is the sanctioned exception and is
deliberately NOT imported from :mod:`certiqs_key.receiver` -- a caller that wants
it imports it by name, so the package surface stays clean whether or not the
consumer is installed. ``tests/unit/test_receiver_docking_surface.py`` asserts
both halves: importing the package does not put ``certiqs_key.reductions`` on the
import path, and no other module of the package names it.

The conversion happens HERE, ONCE, IN ONE DIRECTION:

    ``ReceiverMeasurementArtifact``  ->  ``ReceiverArtifactRows``
                                        (``certiqs_key.reductions.inputs``)

Nothing in the consuming module is modified and nothing reads back the other
way. The artifact this module OWNS is the fifteen-key
``ReceiverMeasurementArtifact`` of its own outputs table; what it does NOT own
is the type the consuming module carries the receiver-facing rows of ITS inputs
table in. ``ReceiverArtifactRows`` belongs to another module -- it is that
module's own reading of those rows, not a copy of this one's artifact -- and it
is not this module's to change. THE PATTERN IS ONE FILE PER PRODUCING MODULE: a
``docking.py`` that converts its own module's artifact into a consumer's
declared type, once, in one direction, in the PRODUCING module's package.

THE ONE CONVERSION SITE, AND THE ONE DIRECTION
==============================================
    IEEE-754 double  ->  exact ``Fraction``, by ``Fraction(value)``.

:func:`_rational` is that site and the only one; :func:`_scalar` and
:func:`_matrix` are its complex and matrix wrappers, building the consumer's
exact pair form ``Cx(re, im)``.

**The conversion is EXACT and LOSSLESS, and it is not a rounding.** A binary64
value IS a dyadic rational, so ``Fraction(x)`` names that rational exactly:
nothing is approximated, nothing is chosen, and the operation has no direction
to round in. The exact substrate the consumer reads says the same --
:mod:`certiqs_key.foundations.exact` records that a binary64 value converts to
a ``Fraction`` exactly and losslessly, it IS a dyadic rational, so an exact
substrate costs the floating-point supplier nothing and loses no information
it had -- and its ``as_scalar`` REFUSES a float at its boundary precisely so
that the caller says which rational it means. This function says it.

**Every decision of this module was taken BEFORE the conversion.** The numbers
crossing here are the finished output of the double-precision evaluation of
Definition ``def:evaluation-model``: the Grams after the efficiency layer, the
conditioned blocks, ``p_mc`` with its branch already selected, the dark-count
matrix, the residual verdicts. No comparison, no branch selector, no refusal and
no residual verdict of :mod:`certiqs_key.receiver` is evaluated on a converted
value, and none is re-evaluated here. What the conversion buys is on the
consumer's side of the boundary, where its own order tests become exact; what it
must not do is let the consumer's exactness be mistaken for an enclosure of this
module's arithmetic. It is not one: ``bound_evaluation`` is propagated UNCHANGED
as ``floating_point``, and Theorem ``thm:exact-and-evaluated`` (iii) still
says that no path in this module produces a label stronger than the
floating-point one.

WHAT SURVIVES THE CONVERSION, ROW BY ROW
========================================
The consumer's receiver rows
(:class:`certiqs_key.reductions.inputs.ReceiverArtifactRows`) are each filled
from the artifact and from nothing else::

    mathematical_spec_version   the artifact's, verbatim -- a draft version
                                cannot occur, the artifact refusing to hold one
    detection_alphabet          the emitted alphabet Y, IN ITS DECLARED ORDER
    photon_blocks               RE-KEYED from (t, m, y) to (y, t) -> tuple over
                                m; no block is recomputed, reordered within a
                                block, or opened
    high_photon_bounds          each entry WITH ITS PER-SETTING WEIGHTS
    bound_quantifier_domain     N and T carried; the statement MAPPED, not
                                rewritten (see below)
    dark_count_channel          the RAW R on 2^[K]; r_min NOT handed over
    outcome_coarse_graining     cg, from the artifact's own fibres
    bound_evaluation            propagated unchanged
    channel_grading             from block_dimensions, above_cutoff_finite=False
    validation_results_present  from the artifact's validation_results
    declared_device_family      from calibration_coverage: EMPTY, or a refusal
    occupation_basis_order      from block_dimensions' occupation vectors
    inherited_assumption_ledger the artifact's assumption_ledger, transported
    exact_model_admissible      the exact-route record's has_exact_model
                                (req:exact-route-decision (iv)), read by the
                                consumer's presence rule of A-RECV alone

THREE THINGS THE CONSUMER'S TYPE CANNOT CARRY, NAMED RATHER THAN PAPERED OVER
============================================================================
Each is a limitation OF THIS DOCKING, not a defect of either contract, and none
is repaired by inventing a value. (The per-setting multi-click weights are not
among them: Theorem ``thm:emitted-bound`` states them (Eq. ``eq:pmcsetting``)
and the consumer's ``HighPhotonBound`` carries one weight per setting, so they
cross entire, and the minimum is the consumer's to read off them,
``reductions/wpfss/rem:minweight``.)

1. **THE QUANTIFIER SENTENCE, because the two contracts letter the photon number
   differently.** This module emits the literal "for all n > N and all t in T"
   (``interface.yaml`` ``outputs.bound_quantifier_domain``); the consumer's
   inputs table (``reductions/wpfss/interface.yaml``) types it as the literal
   statement "for all m > N and all t in T", and its ``BoundQuantifierDomain``
   carries only ``cutoff`` and ``settings`` -- there is no field for the
   sentence. So the sentence is MAPPED and not rewritten: ``N`` and ``T`` cross,
   the sentence does not, and nothing here edits this module's ``n`` into the
   consumer's ``m``. The two letters denote the same photon number and each
   contract says so in its own words.

2. **THE THREE DARK-COUNT SCALARS, AND THE COMPOSITION RULE THEY ATTEST.** The
   artifact carries ``r_min``, ``rbar`` and ``delta_dc`` under distinct names
   beside the matrix (the consumer's ``dark_count_channel`` input row), and
   NONE OF THE THREE CROSSES. The consumer's ``DarkCountChannel`` has exactly
   ``{ports, entries}``, which is the type enforcing what the field-to-row map
   says: the raw ``R`` crosses and the scalars do not.

   * ``r_min`` is the minimum of Eq. ``eq:rmin`` over every non-multiclick
     column of the RAW matrix. The consumer needs PER-LETTER constants
     ``r_min,i`` of the DESCENDED matrix ``R^cg`` and derives them itself under
     its own Lemma ``lem:descent``; handing this one over as ``r_min,i`` would
     substitute one contract's quantity for another's.
   * ``rbar = min{r_min, 1}`` of Eq. ``eq:rbar`` is a COEFFICIENT in one stated
     inequality of THIS contract, not a property of the matrix. Nothing in the
     consumer's rows is that coefficient, and it is not a repaired ``r_min``.
   * ``delta_dc`` of Eq. ``eq:darkdelta`` is the composition correction, and it
     is the one a reader would most want and must not take: it says the emitted
     ``R`` was admitted under the WIDENED (D1)/(D2) of
     Definition ``def:tolmap`` (iii), and therefore that the inequality a
     consumer composes with is Eq. ``eq:darkpmcslack`` and NOT Eq.
     ``eq:darkpmc``. It is a function of THIS module's declared tolerances and
     of ``K``, so it means nothing against the consumer's own declared numbers.

   The ``composition_rule`` string the artifact carries beside them attests
   exactly that, and it does not cross either. The consumer states its own
   composition; carrying this one over would assert a relation between two
   contracts' constants that neither states.

3. **SEVEN OF THE FIFTEEN KEYS.** ``input_mode_space``, ``port_grams``,
   ``receiver_construction``, ``efficiency_record`` (beyond its factored
   loss), ``calibration_coverage`` (beyond the device-family reading),
   ``validation_results`` (beyond its presence) and the emitted alphabet's stable
   IDs have no row in the consumer's inputs table. They are not lost -- they
   stay in the emitted artifact, which is what a run logs -- but they do not
   cross this boundary, and this module invents no row to carry them. The
   factored loss ``t`` of ``efficiency_record`` DOES cross, into the
   consumer's ``factored_loss`` row: where it is below one the blocks that
   cross are the normalized station's
   (``detector-imperfections/req:normalization-record``), and the consumer
   records the loss in front of its link
   (``reductions/wpfss/req:normalized-link-record``).

   **``assumption_ledger`` IS NOT IN THIS LIST, BECAUSE THE CONSUMER CARRIES THE
   SUPPLIER'S LEDGER BY MACHINE KEY.** On the row of its Assumption
   ``reductions/ass:recv`` it carries every key the supplied ledger carries, as
   supplied and in the supplier's order
   (``reductions/req:supplier-ledger-pass-through``), and it refuses a ledger
   that lacks a key the supplier's presence rules make present
   (``reductions/req:supplier-ledger-refusals``). So the rows it asks of a
   supplier include this one, and the adapter fills it by TRANSPORT: each row's
   ``machine_key`` with the supplier's own ``constrains`` record beside it,
   converted to strings and READ BY NOTHING HERE. No key is invented, none is
   renamed, none is dropped, and nothing about the consumer's own ledger is
   decided here.

WHERE A ROW CANNOT BE FILLED, THE ADAPTER REFUSES
=================================================
:class:`DockingRefusal` is a docking limitation with a machine-readable reason,
and it is a RECORD, never an exception and never a default. Its reasons are NOT
members of :class:`certiqs_key.receiver.reasons.RefusalReason`: that vocabulary
names the contract's own failing checks, and a docking limitation is not one of
them. The contract's own refusals happen upstream, in
:func:`certiqs_key.receiver.construct.construct_receiver`, and an artifact exists
only because none of them fired.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from fractions import Fraction

import numpy as np

from certiqs_key.foundations.exact import Cx
from certiqs_key.foundations.exact import Matrix as ExactMatrix
from certiqs_key.receiver.artifact import ReceiverMeasurementArtifact
from certiqs_key.receiver.numerics import Matrix, Scalar
from certiqs_key.receiver.reasons import CALIBRATION_COVERAGE_STATEMENT
from certiqs_key.reductions.inputs import (
    BoundQuantifierDomain,
    ChannelGrading,
    ClickPattern,
    CoarseGraining,
    DarkCountChannel,
    HighPhotonBound,
    InheritedAssumption,
    JointOutcome,
    Label,
    ReceiverArtifactRows,
    patterns,
)

__all__ = [
    "DockingRefusal",
    "DockingRefusalReason",
    "receiver_artifact_rows",
]


class DockingRefusalReason(StrEnum):
    """Why a docking could not fill a consumer row without inventing a datum.

    A DOCKING LIMITATION, not a contract refusal: no member of this enum names a
    check of either contract, and none can be produced by
    :func:`certiqs_key.receiver.construct.construct_receiver`. The conventions block's
    ``fail_closed`` convention is nonetheless the shape -- a machine-readable
    reason and no output -- because a defaulted row would be a datum this module
    invented on a boundary neither contract describes.
    """

    #: The artifact's ``calibration_coverage`` is not the statement this
    #: module emits, so whether a device family is represented cannot be read
    #: off it.
    CALIBRATION_COVERAGE_NOT_RECOGNISED = "calibration_coverage_not_recognised"
    #: The artifact declares no port, so the port ORDER the consumer's 1-based
    #: click patterns need cannot be read off ``port_grams``.
    PORT_ORDER_UNAVAILABLE = "port_order_unavailable"
    #: A raw click pattern of ``2^[K]`` is not in the emitted coarse-graining, so
    #: ``cg`` would not be the TOTAL map the consumer types.
    COARSE_GRAINING_NOT_TOTAL = "coarse_graining_not_total"
    #: The emitted blocks do not cover some ``(y, t, m)``, so the consumer's
    #: ``photon_blocks`` mapping would have a hole.
    PHOTON_BLOCK_MISSING = "photon_block_missing"
    #: An emitted click pattern names a port the artifact's port order does not.
    UNKNOWN_PORT_LABEL = "unknown_port_label"


@dataclass(frozen=True)
class DockingRefusal:
    """A docking limitation, as a record.

    ``reason`` is the machine-readable field and the load-bearing one;
    ``detail`` names the offending datum in prose. Returned INSTEAD OF the
    consumer's rows, never beside them, and never raised.
    """

    reason: DockingRefusalReason
    detail: str

    def as_machine_record(self) -> dict[str, str]:
        """Return the limitation as a machine record."""
        return {"reason": str(self.reason), "detail": self.detail}


def _rational(value: Scalar) -> Fraction:
    """Return an emitted scalar as the exact rational it IS.

    THE ONE CONVERSION SITE of this module, in the one direction. See the module
    docstring: ``Fraction(x)`` on a binary64 value is exact and lossless -- the
    value is a dyadic rational and this names it -- so there is nothing to round
    and no direction to round in. Every decision of :mod:`certiqs_key.receiver` was
    taken before this is called.

    **ON AN ALREADY-EXACT VALUE THIS IS THE IDENTITY, AND THAT IS THE POINT AT
    ``dark_count_channel``.** The generated-route ``R`` is evaluated exactly
    (Eq. ``eq:darkR``; :func:`certiqs_key.receiver.dark.product_form`), so its
    entries arrive here as :class:`~fractions.Fraction` and cross UNCHANGED --
    no conversion, no rounding, and no re-derivation on this side. What the
    consumer receives therefore has columns summing to EXACTLY 1, which is
    Theorem ``thm:dark-counts`` (i) holding in the matrix and not only in the
    equation, and is what its own exact scalar rules require of a declared
    dark-count channel.
    """
    return Fraction(value)


def _scalar(value: complex) -> Cx:
    """Return a complex entry in the consumer's exact pair form."""
    return Cx(_rational(value.real), _rational(value.imag))


def _matrix(block: Matrix) -> ExactMatrix:
    """Return a ``complex128`` matrix in the consumer's exact substrate."""
    array = np.asarray(block, dtype=np.complex128)
    return tuple(tuple(_scalar(complex(entry)) for entry in row) for row in array)


def _port_index(artifact: ReceiverMeasurementArtifact) -> dict[str, int]:
    """Return the declared port order as the consumer's 1-BASED indices.

    ``port_grams`` is the authoritative order on EVERY route: it is emitted in
    the declared port-map order and is present on all three, whereas the port map
    itself is carried only by ``receiver_construction`` and so only on route
    (iii). The consumer's :func:`certiqs_key.reductions.inputs.patterns` enumerates
    ``2^[K]`` over ``1..K``, so the index is the position plus one.
    """
    return {
        label: position + 1 for position, (label, _) in enumerate(artifact.port_grams)
    }


def _pattern(
    labels: Sequence[str], index: Mapping[str, int]
) -> ClickPattern | DockingRefusal:
    """Return a click pattern of port LABELS as the consumer's index set."""
    members: list[int] = []
    for label in labels:
        if label not in index:
            return DockingRefusal(
                DockingRefusalReason.UNKNOWN_PORT_LABEL,
                f"the emitted click pattern names port {label!r}, which the "
                f"artifact's port order {sorted(index)} does not declare",
            )
        members.append(index[label])
    return frozenset(members)


def _coarse_graining(
    artifact: ReceiverMeasurementArtifact, index: Mapping[str, int]
) -> CoarseGraining | DockingRefusal:
    """Return ``cg`` in the consumer's type, from the artifact's own fibres.

    The letters keep THEIR DECLARED ORDER: the consumer's
    ``alphabet_or_order_mismatch`` rule compares ``Y`` ORDER INCLUDED
    (``reductions/interface.yaml``), and the order is a declared datum of the
    protocol declaration on both sides.
    """
    ports = len(index)
    assignment: dict[ClickPattern, Label] = {}
    for letter, fibre in artifact.outcome_alphabet.fibres:
        for pattern_labels in fibre:
            pattern = _pattern(pattern_labels, index)
            if isinstance(pattern, DockingRefusal):
                return pattern
            assignment[pattern] = letter
    missing = [pattern for pattern in patterns(ports) if pattern not in assignment]
    if missing:
        return DockingRefusal(
            DockingRefusalReason.COARSE_GRAINING_NOT_TOTAL,
            f"the emitted coarse-graining leaves {len(missing)} of the "
            f"{2**ports} raw click patterns unmapped, the first being "
            f"{sorted(missing[0])}",
        )
    return CoarseGraining(
        ports=ports,
        letters=tuple(letter for _, letter in artifact.outcome_alphabet.letters),
        assignment=assignment,
    )


def _photon_blocks(
    artifact: ReceiverMeasurementArtifact,
    letters: Sequence[Label],
    dark_composed: bool,
) -> Mapping[JointOutcome, tuple[ExactMatrix, ...]] | DockingRefusal:
    """Re-key the emitted blocks to ``(y, t) -> (blk m = 0, ..., blk m = N)``.

    A RE-KEY AND NOTHING ELSE. This module emits, per probe setting, per photon
    number, per emitted letter (keyed by the declared setting label; the module
    docstring of :mod:`certiqs_key.receiver.artifact`); the consumer indexes by
    the pair and then by ``m``. No block is recomputed, no block is reordered
    within itself, and no above-cutoff block is invented -- the supplier emits
    none (``interface.yaml`` ``outputs.photon_blocks.emitted_range_note``).
    ``dark_composed`` selects the dark-composed blocks of Requirement
    ``req:dark-composed-reference`` (i) instead of the bare ones.
    """
    cutoff = artifact.bound_quantifier_domain.photon_cutoff
    blocks: dict[JointOutcome, tuple[ExactMatrix, ...]] = {}
    for family in artifact.photon_blocks:
        by_photons = dict(family.dark_composed if dark_composed else family.blocks)
        for letter in letters:
            column: list[ExactMatrix] = []
            for photons in range(cutoff + 1):
                emitted = dict(by_photons.get(photons, ()))
                if letter not in emitted:
                    return DockingRefusal(
                        DockingRefusalReason.PHOTON_BLOCK_MISSING,
                        f"no emitted block for letter {letter!r} at setting "
                        f"{family.setting!r} and photon number {photons}",
                    )
                column.append(_matrix(emitted[letter]))
            blocks[(letter, family.setting)] = tuple(column)
    return blocks


def _high_photon_bounds(
    artifact: ReceiverMeasurementArtifact, index: Mapping[str, int]
) -> tuple[HighPhotonBound, ...] | DockingRefusal:
    """Return the slot entries WITH THEIR PER-SETTING WEIGHTS.

    The per-setting weights are the slot's guaranteed content (Theorem
    ``thm:emitted-bound``, Eq. ``eq:pmcsetting``; Definition
    ``def:slot``), and the consumer takes the slot in that form
    (``reductions/wpfss/def:weight-route``). Each weight crosses through the
    one conversion site, in the declared order of ``T``; the entry's uniform
    weight is the consumer's to read off them and is not carried a second
    time. Whether the artifact's version states the per-setting weights is the
    consumer's row to decide (its ``high_photon_slot`` row), not this adapter's.
    """
    entries: list[HighPhotonBound] = []
    for entry in artifact.high_photon_bounds.entries:
        outcome_set: list[ClickPattern] = []
        for pattern_labels in entry.outcome_set:
            pattern = _pattern(pattern_labels, index)
            if isinstance(pattern, DockingRefusal):
                return pattern
            outcome_set.append(pattern)
        entries.append(
            HighPhotonBound(
                outcome_set=frozenset(outcome_set),
                per_setting=tuple(
                    (setting, _rational(weight))
                    for setting, weight in entry.per_setting
                ),
            )
        )
    return tuple(entries)


def _dark_count_channel(
    artifact: ReceiverMeasurementArtifact, index: Mapping[str, int]
) -> DarkCountChannel | DockingRefusal:
    """Return the RAW ``R`` on ``2^[K]``; ``r_min`` does NOT cross.

    Limitation 2 of the module docstring. Only the non-zero entries are carried,
    which is what the emitted record stores and what the consumer's type reads
    (in :class:`certiqs_key.reductions.inputs.DarkCountChannel` an absent pair
    is zero), and (D2) makes every other entry zero by definition.
    """
    entries: dict[tuple[ClickPattern, ClickPattern], Fraction] = {}
    for column_labels, column_entries in artifact.dark_count_channel.columns:
        column = _pattern(column_labels, index)
        if isinstance(column, DockingRefusal):
            return column
        for row_labels, value in column_entries:
            row = _pattern(row_labels, index)
            if isinstance(row, DockingRefusal):
                return row
            entries[(row, column)] = _rational(value)
    return DarkCountChannel(ports=len(index), entries=entries)


def _channel_grading(artifact: ReceiverMeasurementArtifact) -> ChannelGrading:
    """Return the declared photon-number grading of ``H(C)``.

    ``block_dimensions[m] = dim H(C_m)`` for ``0 <= m <= N``, in increasing ``m``, which
    is what this module emits under ``block_dimensions`` and what the conventions block
    ``subsystem_order`` orders. ``above_cutoff_finite`` is ``False``: ``H(C)`` is a Fock
    space, the supplier emits no above-cutoff block, and NO DIMENSION IS INVENTED for
    one.
    """
    return ChannelGrading(
        block_dimensions=tuple(row.dimension for row in artifact.block_dimensions),
        above_cutoff_finite=False,
    )


def _occupation_basis_order(
    artifact: ReceiverMeasurementArtifact,
) -> tuple[tuple[str, ...], ...]:
    """Return the occupation-vector basis order the consumer inherits UNCHANGED.

    Every emitted block's basis, concatenated in increasing ``m`` and within a block in
    the ascending lexicographic order of the occupation vector -- the total order the
    conventions block ``subsystem_order`` fixes. Each vector is rendered as its per-mode
    occupation numbers, because the consumer types the row as tuples of strings and
    compares it for EQUALITY against a declared one; the ORDER is the datum, and nothing
    is reordered here.
    """
    return tuple(
        tuple(str(count) for count in vector)
        for row in artifact.block_dimensions
        for vector in row.occupation_vectors
    )


def _declared_device_family(
    artifact: ReceiverMeasurementArtifact,
) -> tuple[str, ...] | DockingRefusal:
    """Return the device family the artifact declares: EMPTY, or a refusal.

    The emitted ``calibration_coverage`` is the LITERAL statement that the
    device is trusted and exactly characterized and that no characterization
    data, uncertainty set or device family is represented (``interface.yaml``
    ``outputs.calibration_coverage``), so the consumer's
    ``declared_device_family`` is empty. It is DERIVED and not
    hardcoded: a statement this module does not recognise might represent a
    family, and the adapter refuses rather than reading an empty tuple off text
    it cannot interpret. The consumer would refuse a non-empty tuple anyway, with
    ``device_family_unsupported``; what must not happen is an empty one asserted
    on unread prose.
    """
    if artifact.calibration_coverage != CALIBRATION_COVERAGE_STATEMENT:
        return DockingRefusal(
            DockingRefusalReason.CALIBRATION_COVERAGE_NOT_RECOGNISED,
            "the artifact's calibration_coverage is not the statement this "
            "module emits, so whether a device family is "
            "represented cannot be read off it",
        )
    return ()


def receiver_artifact_rows(
    artifact: ReceiverMeasurementArtifact,
    *,
    dark_composed: bool = False,
) -> ReceiverArtifactRows | DockingRefusal:
    """Return the artifact as the consumer's receiver rows, its inputs table.

    One direction, one conversion site, and a refusal rather than a default
    wherever a row cannot be filled from the artifact alone. The result is the
    consumer's own input type and is validated by ITS rules, not by this
    module's: nothing here decides ``cg``'s descent, the fibre condition, the
    absorbing condition or the cutoff agreement, all of which are the consumer's
    fail-closed rows and are evaluated by
    :func:`certiqs_key.reductions.emit.reduce`.

    WHICH BLOCKS CROSS. ``dark_composed=False`` hands over the BARE blocks, the
    ones the consumer in force reads and composes ``R`` into itself
    (``reductions/wpfss/def:weight-route``); ``dark_composed=True`` hands over
    the dark-composed blocks of Requirement ``req:dark-composed-reference`` (i),
    which a consumer must not compose again (item (v)). The rows state which
    form was handed in the consumer's ``photon_blocks_form``, and
    ``reductions/wpfss`` composes ``R`` only into blocks handed in the bare
    form (``reductions/wpfss/def:weight-route``; ``interface.yaml``
    ``outputs.photon_blocks.who_composes_note``), so the choice is the
    caller's, made where the consumer's reading is known, and no form is
    composed twice.
    """
    index = _port_index(artifact)
    if not index:
        return DockingRefusal(
            DockingRefusalReason.PORT_ORDER_UNAVAILABLE,
            "the artifact declares no port, so the port order the consumer's "
            "click patterns are indexed by cannot be read off port_grams",
        )

    coarse = _coarse_graining(artifact, index)
    if isinstance(coarse, DockingRefusal):
        return coarse

    blocks = _photon_blocks(artifact, coarse.letters, dark_composed)
    if isinstance(blocks, DockingRefusal):
        return blocks

    bounds = _high_photon_bounds(artifact, index)
    if isinstance(bounds, DockingRefusal):
        return bounds

    channel = _dark_count_channel(artifact, index)
    if isinstance(channel, DockingRefusal):
        return channel

    family = _declared_device_family(artifact)
    if isinstance(family, DockingRefusal):
        return family

    return ReceiverArtifactRows(
        mathematical_spec_version=artifact.mathematical_spec_version,
        detection_alphabet=coarse.letters,
        photon_blocks=blocks,
        high_photon_bounds=bounds,
        bound_quantifier_domain=BoundQuantifierDomain(
            cutoff=artifact.bound_quantifier_domain.photon_cutoff,
            settings=artifact.bound_quantifier_domain.probe_alphabet,
        ),
        dark_count_channel=channel,
        outcome_coarse_graining=coarse,
        bound_evaluation=artifact.bound_evaluation,
        channel_grading=_channel_grading(artifact),
        validation_results_present=bool(artifact.validation_results.residuals),
        declared_device_family=family,
        occupation_basis_order=_occupation_basis_order(artifact),
        inherited_assumption_ledger=_inherited_assumption_ledger(artifact),
        # req:dark-composed-reference (v): the form travels with the blocks,
        # so a consumer handed the dark-composed ones does not compose R again.
        photon_blocks_form="dark_composed" if dark_composed else "bare",
        # detector-imperfections/req:normalization-record: the factored loss
        # travels with the blocks, which are the normalized station's where it
        # is below one (reductions/wpfss/req:normalized-link-record).
        factored_loss=artifact.efficiency_record.normalization.factored_loss,
        # req:exact-route-decision (iv): whether the declaration has a model
        # admissible exactly, read off the artifact's exact-route record for
        # the consumer's presence rule of A-RECV
        # (reductions/req:recv-row-provenance (iv)); False where none is
        # recorded, the direction that keeps the row.
        exact_model_admissible=(
            bool(artifact.photon_blocks)
            and artifact.photon_blocks[0].reference.exact_route.has_exact_model
        ),
    )


def _inherited_assumption_ledger(
    artifact: ReceiverMeasurementArtifact,
) -> tuple[InheritedAssumption, ...]:
    """Return this artifact's ledger as the consumer's inherited rows.

    A TRANSPORT AND NOT A STATEMENT. The consumer carries every key of the
    supplied ledger on the row of its Assumption A-RECV
    (``reductions/req:supplier-ledger-pass-through``), and one of them --
    ``exact_window_eigenvalue_slack`` -- it records BESIDE THE SETTINGS AT WHICH
    THE SUPPLIER SAYS IT WAS INVOKED
    (``reductions/wpfss/req:supplier-eig-record``). Both are already on
    :attr:`ReceiverMeasurementArtifact.assumption_ledger`, so nothing is
    computed here: the key is copied and each constrained value is rendered with
    ``repr`` into the string pair the consumer's row is typed for.

    NO ROW IS FILTERED AND NONE IS REORDERED. Deciding which of the supplier's
    rows the consumer needs would be this module reading the consumer's
    contract; the consumer reads the supplier's machine keys and presence
    rules as installed and refuses a ledger that is missing a key those rules
    make present (``reductions/req:supplier-ledger-refusals``). Under the
    supplier's rules every row is on every artifact, so no key is conditional.
    """
    return tuple(
        InheritedAssumption(
            machine_key=row.machine_key,
            constrains=tuple((name, repr(value)) for name, value in row.constrains),
        )
        for row in artifact.assumption_ledger
    )
