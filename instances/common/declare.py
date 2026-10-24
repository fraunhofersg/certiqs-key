"""The one place a float-evaluated receiver becomes a family this instance DECLARES.

WHAT THIS MODULE DOES
=====================
``receiver`` evaluates in floating point and says so: Definition
``def:evaluation-model``, and Theorem ``thm:exact-and-evaluated`` (ii) -- "this
contract asserts NO BOUND ON THE DIFFERENCE". Every consumer downstream decides
admissibility EXACTLY and refuses, and ``meat-core``'s Proposition
``prop:optol-nobound`` proves that no consumer-side tolerance converts into a
bound on the key. So the perturbation is absorbed where data is DECLARED, once,
in the open -- and this instance is what declares the receiver's blocks
(``foundations/req:who-snaps``: the instance snaps its own device's family).

Per probe setting ``t`` the instance snaps the DARK-COMPOSED family
``{Ftilde^{=m}_{y|t}}`` the receiver emits (``receiver/detector-imperfections/
req:dark-composed-reference`` (i)) with
:func:`certiqs_key.foundations.snap.snap_measurement_family`
(``foundations/def:snap``, ``req:snap-reference``, ``req:support-safe-snap``),
block by block. A block whose exact reference is a lattice family is KEPT and
rests on nothing; every other block is MOVED by the one fidelity-first,
support-safe procedure (on the centres of its exact reference where it has
one), with the flagged last resort, and its record names the cause and the
receiver's fix (``receiver/detector-imperfections/req:snap-fix``)
where no reference is handed on it.

THE REFERENCE IS HANDED BESIDE THE SNAP (the direct route;
``foundations/def:evaluated-off-snap`` (i)). Every block of the receiver's
reference that passes the decisions ``foundations/req:snap-reference`` (i) asks
of a declarer's reference, exact or enclosed (the exact ones alone where the run
declares enclosed references not used), crosses unaltered beside the snapped
blocks in
:attr:`~certiqs_key.reductions.inputs.ReceiverArtifactRows.handed_reference`;
the reductions form the reference companion from it
(``reductions/req:reference-companion``), and the run's first-order bound is
evaluated on that companion
(``meat-core/frank-wolfe/req:bracket-on-reference``). Where that bound counts, a
moved block on which the reference is handed is evaluated off its snap and rests
on no premise about the snap; elsewhere it rests on
``foundations/ass:snapped-measurement`` (A-SNAP). The run record decides it
(:mod:`certiqs_key.runs.direct_route`). A moved block on which no reference is
handed rests on A-SNAP whatever the run does, and a run that declares the strict
option refuses it here.

The blocks cross to ``reductions`` in the dark-composed form
(``photon_blocks_form = dark_composed``), so that ``reductions`` does not
compose the dark counts again (``reductions/wpfss/prop:precomposed-blocks``;
``receiver/.../req:dark-composed-reference`` (v)).

THE TWO RUN PARAMETERS
======================
:class:`~certiqs_key.foundations.snap.SnapSettings`, built from the run
configuration by :func:`snap_settings`: whether enclosed references are used
(default on; off, only the exact blocks of the reference are handed) and the
strict option (default off). Both are recorded with every snap and reach the
reduction request.

WHAT IT DOES NOT CLAIM
======================
A moved block relates the declared family to the computed one by nothing
beyond its recorded displacement: ``meat-core``'s ``prop:optol-nobound``
proves no such bound exists in general.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import replace
from typing import TYPE_CHECKING, Any

from certiqs_key.foundations.exact import Matrix as ExactMatrix
from certiqs_key.foundations.recentring import EntrywiseEnclosure
from certiqs_key.foundations.snap import (
    MeasurementSnapRecord,
    SnapRefusedError,
    SnapSettings,
    snap_measurement_family,
)
from certiqs_key.receiver.docking import DockingRefusal, receiver_artifact_rows
from certiqs_key.receiver.reference import ReferenceCause
from certiqs_key.receiver.snapfix import receiver_fixes
from certiqs_key.reductions.inputs import (
    OFF_SETTING,
    HandedReference,
    InstanceSnapRecord,
)
from certiqs_key.runs.pipeline import AdaptedRows, AdapterRefusal, RowsAdapter

if TYPE_CHECKING:
    from certiqs_key.receiver.artifact import ReceiverMeasurementArtifact
    from certiqs_key.runs.config import RunConfig

__all__ = [
    "DECLARED_BY",
    "SNAP_SITE",
    "declare_receiver_family",
    "rows_adapter",
    "snap_settings",
]

#: What the run record's ``snaps.instance`` block says produced it. A module
#: path and never a machine path, timestamp or run ID
#: (spec/architecture.md 2.6).
DECLARED_BY = "instances.optical_bb84.declare"

#: Where in the declaration the snapped family sits, as the records carry it.
SNAP_SITE = "receiver_photon_blocks"


def snap_settings(config: RunConfig) -> SnapSettings:
    """Return the run's two snap parameters as foundations reads them.

    ``RunConfig.reference_enclosure`` and ``strict_snaps``
    (``foundations/req:snap-reference`` (i), (iv)).
    """
    return SnapSettings(
        reference_enclosure=config.reference_enclosure,
        strict=config.strict_snaps,
    )


def declare_receiver_family(
    artifact: ReceiverMeasurementArtifact,
    *,
    tolerance: float,
    lattice_exponent: int,
    settings: SnapSettings,
    declared_by: str = DECLARED_BY,
) -> AdaptedRows | AdapterRefusal:
    """Return the docked rows carrying the family this instance declares, or decline.

    Implements the instance's half of ``foundations/req:who-snaps`` for the
    receiver's measurement family: per probe setting, the dark-composed blocks
    snapped with :func:`~certiqs_key.foundations.snap.snap_measurement_family`,
    the per-setting :class:`~certiqs_key.foundations.snap.MeasurementSnapRecord`
    with the receiver's fixes (``receiver/detector-imperfections/
    req:snap-fix``), the reference handed beside the snap, and the
    :class:`~certiqs_key.reductions.inputs.InstanceSnapRecord` handed to
    ``reductions``, which names its moved blocks in the A-SNAP row.

    Args:
        artifact: what ``receiver`` emitted. Docked with the dark-composed
            blocks (``receiver_artifact_rows(..., dark_composed=True)``);
            every other row crosses unchanged.
        tolerance: ``tau``, the ceiling on the pre-snap defects of a block
            snapped on its data (spec/architecture.md 2.8).
        lattice_exponent: ``kappa`` (D-LAT); the same number ``reductions`` is
            given.
        settings: the run's enclosure setting and strict option.
        declared_by: the module path the record names.

    Returns:
        An :class:`~certiqs_key.runs.pipeline.AdaptedRows` whose report carries
        every snap record, or an :class:`~certiqs_key.runs.pipeline.AdapterRefusal`
        naming the docking refusal or the block that could not be declared
        (``strict_snaps`` under the strict option).
    """
    rows = receiver_artifact_rows(artifact, dark_composed=True)
    if isinstance(rows, DockingRefusal):
        return AdapterRefusal(reason=str(rows.reason), detail=rows.detail)
    probe_settings = rows.bound_quantifier_domain.settings
    letters = tuple(rows.detection_alphabet)

    blocks: dict[tuple[str, str], list[ExactMatrix]] = {}
    handed: dict[tuple[str, str], list[EntrywiseEnclosure | None]] = {}
    identities: dict[str, Mapping[str, object]] = {}
    records: list[dict[str, Any]] = []
    by_setting: dict[str, Mapping[str, object]] = {}
    for family in artifact.photon_blocks:
        # In increasing photon number, the order the rows index the blocks
        # by and the reference labels its blocks in.
        data = {
            f"m={photons}": [dict(pairs)[letter] for letter in letters]
            for photons, pairs in sorted(family.dark_composed, key=lambda b: b[0])
        }
        offered = family.reference
        try:
            snap = snap_measurement_family(
                data,
                alphabet=letters,
                tolerance=tolerance,
                lattice_exponent=lattice_exponent,
                site=SNAP_SITE,
                reference=offered.reference,
                settings=settings,
                setting=family.setting,
                # The receiver computes the blocks from its model, so a block
                # is moved even where the snap leaves that evaluation unchanged
                # (foundations/def:snap).
                data_from_model=True,
                # The blocks the receiver encloses but does not carry, because
                # the run declares enclosed references not used
                # (req:dark-composed-reference (vi)): their cause is
                # enclosure_not_used, not no_reference.
                withheld_blocks=tuple(
                    block.label
                    for block in offered.offered
                    if block.cause is ReferenceCause.ENCLOSURE_NOT_USED
                ),
            )
        except SnapRefusedError as refusal:
            # The instance's refusal, not the snapping module's exception: the
            # run tier reads an AdapterRefusal, and the machine-readable reason
            # crosses unchanged.
            return AdapterRefusal(
                reason=refusal.reason,
                detail=_refusal_detail(refusal, probe_settings, family.setting),
            )
        fixes = receiver_fixes(family.fix_context, snap.record)
        record = _snap_record(snap.record, fixes)
        # The receiver's record of the reference it OFFERED (identity, kind per
        # block, radii, SHA-256 of the enclosures) replaces the foundations
        # record's copy, which writes the enclosures out in full. The reference
        # is identified by digest, recomputable from its identity: a recorded
        # reading of req:who-snaps.
        record["reference"] = offered.as_record()
        if snap.handed and offered.reference is not None:
            identities[family.setting] = offered.reference.identity.as_record()
        records.append(record)
        by_setting[family.setting] = record
        for label, snapped in snap.blocks.items():
            reference_block = snap.handed.get(label)
            for index, (letter, element) in enumerate(
                zip(letters, snapped, strict=True)
            ):
                blocks.setdefault((letter, family.setting), []).append(element)
                handed.setdefault((letter, family.setting), []).append(
                    None
                    if reference_block is None
                    else EntrywiseEnclosure.of(reference_block.elements[index])
                )

    instance_snap = InstanceSnapRecord.from_snap_records(by_setting)
    declared: Mapping[tuple[str, str], tuple[ExactMatrix, ...]] = {
        key: tuple(value) for key, value in blocks.items()
    }
    handed_reference = HandedReference(
        blocks={key: tuple(value) for key, value in handed.items()},
        identity=identities,
    )
    return AdaptedRows(
        rows=replace(
            rows,
            photon_blocks=declared,
            instance_snap=instance_snap,
            handed_reference=handed_reference if handed_reference.handed else None,
        ),
        report=_report(
            records, instance_snap, tolerance, lattice_exponent, settings, declared_by
        ),
    )


def _snap_record(
    record: MeasurementSnapRecord, fixes: Mapping[str, str]
) -> dict[str, Any]:
    """Return one setting's snap record with the receiver's fix beside each block's."""
    payload = record.as_record()
    raw_blocks = payload.get("blocks")
    if isinstance(raw_blocks, list):
        for block in raw_blocks:
            if isinstance(block, dict):
                block["receiver_fix"] = fixes.get(str(block.get("block")))
    payload["receiver_fixes"] = dict(fixes)
    return payload


def _refusal_detail(
    refusal: SnapRefusedError, settings: Sequence[str], setting: str
) -> str:
    """Return the human half of a snap refusal, naming the probe only if there is one.

    A receiver without a probe declares
    ``T = {off}`` (``receiver/def:probe``), and telling its user about "the
    family at setting 'off'" names a countermeasure the device does not have.
    So on a probe-free receiver the detail names only the family, and the snap's
    own message loses the ``, setting 'off'`` its location carries. The
    machine-readable reason and the snap records are untouched.
    """
    message = str(refusal)
    if tuple(settings) != (OFF_SETTING,):
        return f"the family at setting {setting!r}: {message}"
    # The snap module spells a location as "<site>, setting '<t>', block '<b>'"
    # (foundations/snap.py ``_where``); a test on a probe-free receiver asserts
    # the setting is gone, so a change to that spelling fails there.
    message = message.replace(f", setting {setting!r}", "")
    return f"the receiver's family: {message}"


def _report(
    records: Sequence[Mapping[str, Any]],
    instance_snap: InstanceSnapRecord,
    tolerance: float,
    lattice_exponent: int,
    settings: SnapSettings,
    declared_by: str,
) -> dict[str, object]:
    """Return the JSON-ready record the run record's ``snaps.instance`` block copies.

    Every snap, per setting and block, verbatim: the status, kept or moved; the
    reference kind the snap ran on and the reference handed beside it; the
    cause with both fixes where none is handed; the enclosure and strict
    settings; and the ``support_not_preserved`` flag
    (``foundations/req:who-snaps``). NOT summarized: the largest displacement
    over a run is a different fact from the displacement of one block.
    """
    return {
        "declared_by": declared_by,
        "declared_tolerance": tolerance,
        "lattice_exponent": lattice_exponent,
        "snap_settings": settings.as_record(),
        "photon_blocks_form": "dark_composed",
        "measurement_snaps": [dict(record) for record in records],
        "instance_snap": instance_snap.as_record(),
        "note": (
            "the emitted rows carry the dark-composed family this instance "
            "DECLARED by its snap, not the numbers receiver computed; a kept "
            "block is the receiver's exact reference, and a moved one is "
            "related to the model by nothing beyond its recorded displacement "
            "(meat-core prop:optol-nobound): it rests on "
            "foundations/ass:snapped-measurement unless the run evaluates it "
            "off its snap on the reference handed beside it"
        ),
    }


def rows_adapter(
    *,
    tolerance: float,
    lattice_exponent: int,
    settings: SnapSettings,
    declared_by: str = DECLARED_BY,
) -> RowsAdapter:
    """Return :func:`declare_receiver_family` bound to one ceiling, lattice and policy.

    ``tau`` has no default anywhere (spec/architecture.md 2.8) and ``kappa``
    has none either (spec/architecture.md 2.9, (D-LAT)); the snap settings are
    the run's (:func:`snap_settings`), so a caller states them.
    """

    def adapter(artifact: ReceiverMeasurementArtifact) -> AdaptedRows | AdapterRefusal:
        return declare_receiver_family(
            artifact,
            tolerance=tolerance,
            lattice_exponent=lattice_exponent,
            settings=settings,
            declared_by=declared_by,
        )

    return adapter
