"""The instance's snap of its receiver family: kept, or moved and disclosed.

``receiver`` evaluates in floating point and every consumer downstream
decides EXACTLY and refuses, and NO MODULE MAY CLOSE THE GAP --
spec/architecture.md 2.8: "no module repairs what it was handed". So this
instance declares a family of its own, by
:func:`certiqs_key.foundations.snap.snap_measurement_family`: the dark-composed
blocks the receiver emits, each KEPT where the receiver's exact reference is a
lattice family, or MOVED by the one fidelity-first procedure, with the
receiver's reference handed beside the snap
(``foundations/def:evaluated-off-snap`` (i)).

The property that matters is still:

    **whatever comes out is a POVM, exactly, in the substrate the consumer
    decides in -- or nothing comes out at all.**

and beside it, that every block says how it relates to the model: kept, or
moved with the reference handed beside it, or moved with none handed and its
cause and fix, resting on A-SNAP.

A snap carries no weight: a run evaluates its first-order bound on the
reference companion. What the record says is kept or moved, and the reference
handed.
"""

from __future__ import annotations

from fractions import Fraction as F
from typing import Any

import pytest
from instances.common.declare import (
    DECLARED_BY,
    declare_receiver_family,
    rows_adapter,
)
from instances.common.optics import (
    ProbeSource,
    ReceiverParameters,
    receiver_request,
)
from instances.common.passive_device import LATTICE_EXPONENT
from optical_bb84_prologue import run_prologue
from probe_presence import requires_probe

from certiqs_key.foundations.exact import (
    Cx,
    add,
    identity,
    is_hermitian,
    is_positive_semidefinite,
)
from certiqs_key.foundations.snap import REFUSAL_REASONS, SnapSettings
from certiqs_key.receiver.artifact import ReceiverMeasurementArtifact
from certiqs_key.receiver.construct import construct_receiver
from certiqs_key.receiver.docking import receiver_artifact_rows
from certiqs_key.reductions.inputs import ReceiverArtifactRows
from certiqs_key.runs.pipeline import AdaptedRows, AdapterRefusal

#: The ceiling every test below declares (the sweep's).
TAU = 1e-12

#: The snap settings at their defaults: enclosed references used, not strict.
DEFAULTS = SnapSettings()

#: Devices the snap is exercised over. Each changes what the reference and
#: the evaluation carry: loss and dark counts move every entry, an
#: unbalanced split moves the two bases apart, and cutoff 2 brings an
#: enclosed block.
DEVICES: tuple[tuple[str, ReceiverParameters], ...] = (
    ("ideal", ReceiverParameters(photon_cutoff=1)),
    ("cutoff-2", ReceiverParameters(photon_cutoff=2)),
    # Declared at t = 1, so that the loss stays in the receiver at the dyadic
    # 7/8: the default factor (7/8)(100/99) = 175/198 would compile every port
    # at 99/100, whose exact reference is off the lattice and is moved.
    (
        "lossy",
        ReceiverParameters(
            photon_cutoff=1,
            efficiency=(F(7, 8),) * 4,
            efficiency_normalization=F(1),
        ),
    ),
    ("dark", ReceiverParameters(photon_cutoff=1, dark_count=(F(1, 64),) * 4)),
    ("unbalanced", ReceiverParameters(photon_cutoff=1, basis_split=F(1, 4))),
    (
        "imperfect-pbs",
        ReceiverParameters(
            photon_cutoff=1, pbs_leak_transmitted=F(1, 32), pbs_leak_reflected=F(1, 32)
        ),
    ),
    (
        "noisy-cutoff-2",
        ReceiverParameters(
            photon_cutoff=2,
            efficiency=(F(9, 10),) * 4,
            dark_count=(F(1, 10**6),) * 4,
        ),
    ),
)
_BY_NAME = dict(DEVICES)

_ARTIFACTS: dict[str, ReceiverMeasurementArtifact] = {}


def _artifact(name: str, led: ProbeSource | None = None) -> ReceiverMeasurementArtifact:
    """Return the receiver artefact of one device, built once and shared."""
    key = name if led is None else f"{name}+led"
    if key not in _ARTIFACTS:
        emission = construct_receiver(receiver_request(_BY_NAME[name], led))
        assert emission.artifact is not None, emission.refusal
        _ARTIFACTS[key] = emission.artifact
    return _ARTIFACTS[key]


def _declare(
    artifact: ReceiverMeasurementArtifact,
    *,
    tolerance: float = TAU,
    lattice_exponent: int = LATTICE_EXPONENT,
    settings: SnapSettings = DEFAULTS,
) -> AdaptedRows | AdapterRefusal:
    """Call the snap at this file's declarations, so that a test names only its own."""
    return declare_receiver_family(
        artifact,
        tolerance=tolerance,
        lattice_exponent=lattice_exponent,
        settings=settings,
    )


def _snaps(adapted: AdaptedRows) -> list[dict[str, Any]]:
    """Return the per-setting snap records of one adaptation."""
    snaps = adapted.report["measurement_snaps"]
    assert isinstance(snaps, list)
    return [snap for snap in snaps if isinstance(snap, dict)]


def _blocks(adapted: AdaptedRows) -> list[dict[str, Any]]:
    return [block for snap in _snaps(adapted) for block in snap["blocks"]]


def _families(rows: ReceiverArtifactRows) -> list[tuple[str, int, list[object]]]:
    """Return one ``(setting, photons, family)`` per block of the rows."""
    domain = rows.bound_quantifier_domain
    return [
        (
            setting,
            photons,
            [
                rows.photon_blocks[(y, setting)][photons]
                for y in rows.detection_alphabet
            ],
        )
        for setting in domain.settings
        for photons in range(domain.cutoff + 1)
    ]


# ===========================================================================
#  What comes out is a POVM, exactly, in the dark-composed form.
# ===========================================================================


@pytest.mark.parametrize(("name", "parameters"), DEVICES, ids=[n for n, _ in DEVICES])
def test_every_declared_block_is_an_exact_povm(
    name: str, parameters: ReceiverParameters
) -> None:
    """Complete, Hermitian and PSD -- decided exactly, with no tolerance."""
    del parameters
    adapted = _declare(_artifact(name))
    assert isinstance(adapted, AdaptedRows), adapted
    for setting, photons, family in _families(adapted.rows):
        total = family[0]
        for element in family[1:]:
            total = add(total, element)  # type: ignore[arg-type]
        where = f"{name} setting={setting} photons={photons}"
        assert total == identity(len(family[0])), f"completeness at {where}"  # type: ignore[arg-type]
        for element in family:
            assert is_hermitian(element), f"hermiticity at {where}"  # type: ignore[arg-type]
            assert is_positive_semidefinite(element), f"positivity at {where}"  # type: ignore[arg-type]


@pytest.mark.parametrize(("name", "parameters"), DEVICES, ids=[n for n, _ in DEVICES])
def test_every_declared_entry_is_a_lattice_number_in_an_exact_carrier(
    name: str, parameters: ReceiverParameters
) -> None:
    """Nothing that reaches the consumer is a float, and every entry is dyadic."""
    del parameters
    adapted = _declare(_artifact(name))
    assert isinstance(adapted, AdaptedRows)
    step = F(1, 2**LATTICE_EXPONENT)
    for _setting, _photons, family in _families(adapted.rows):
        for element in family:
            for row in element:  # type: ignore[attr-defined]
                for entry in row:
                    assert isinstance(entry, Cx)
                    assert isinstance(entry.re, F) and isinstance(entry.im, F)
                    assert entry.re % step == 0 and entry.im % step == 0, entry
                    assert abs(entry.re) <= 1 and abs(entry.im) <= 1, entry


def test_the_rows_cross_dark_composed_with_the_instance_snap_record() -> None:
    """``reductions`` is handed the dark-composed form and the party's record.

    ``receiver/detector-imperfections/req:dark-composed-reference`` (v) and
    ``reductions/wpfss/prop:precomposed-blocks``: the declared blocks are the
    family after the dark counts, and the form travels with them so that
    ``reductions`` does not compose ``R`` again; the snap record names the
    blocks the reductions name in the A-SNAP row where moved. Every other row
    crosses as the receiver's docking emits it.
    """
    artifact = _artifact("dark")
    docked = receiver_artifact_rows(artifact, dark_composed=True)
    assert isinstance(docked, ReceiverArtifactRows)
    adapted = _declare(artifact)
    assert isinstance(adapted, AdaptedRows)
    assert adapted.rows.photon_blocks_form == "dark_composed"
    snap = adapted.rows.instance_snap
    assert snap is not None and snap.moved == ()
    assert {(block.block, block.setting) for block in snap.blocks} == {
        (0, "off"),
        (1, "off"),
    }
    assert all(
        block.status == "kept" and block.handed and block.reference_kind == "exact"
        for block in snap.blocks
    )
    for field in (
        "mathematical_spec_version",
        "detection_alphabet",
        "high_photon_bounds",
        "bound_quantifier_domain",
        "dark_count_channel",
        "outcome_coarse_graining",
        "bound_evaluation",
        "channel_grading",
        "validation_results_present",
        "declared_device_family",
        "occupation_basis_order",
        "inherited_assumption_ledger",
    ):
        assert getattr(adapted.rows, field) == getattr(docked, field), field
    # Every block is KEPT: the declared blocks ARE the receiver's
    # exact reference (the dark-composed model computed exactly), not the
    # binary64 evaluation of it, whose last-bit noise the snap does not keep.
    (family,) = artifact.photon_blocks
    reference = family.reference.reference
    assert reference is not None
    for photons in range(2):
        centres = reference.block(f"m={photons}").centres
        for letter, centre in zip(reference.alphabet, centres, strict=True):
            assert adapted.rows.photon_blocks[(letter, "off")][photons] == centre
    assert adapted.rows.photon_blocks != docked.photon_blocks


def test_a_structurally_zero_entry_stays_exactly_zero() -> None:
    """The ideal device's H port sees nothing at zero photons; snapping keeps it."""
    adapted = _declare(_artifact("ideal"))
    assert isinstance(adapted, AdaptedRows)
    assert adapted.rows.photon_blocks[("H", "off")][0] == ((Cx(F(0), F(0)),),)


# ===========================================================================
#  Kept, or moved: what each block says.
# ===========================================================================


@pytest.mark.parametrize(
    "name", ["ideal", "lossy", "dark", "unbalanced", "imperfect-pbs"]
)
def test_the_one_photon_devices_are_kept(name: str) -> None:
    """Every N = 1 device here lies on the exact route and is kept.

    The receiver's exact reference is on the lattice already, so the snap moves
    nothing (``foundations/req:snap-reference`` (ii)): the shipped defaults'
    numbers do not move.
    """
    adapted = _declare(_artifact(name))
    assert isinstance(adapted, AdaptedRows)
    for block in _blocks(adapted):
        assert block["status"] == "kept", block
        assert block["reference_kind"] == "exact"
        assert block["handed_reference_kind"] == "exact"
        assert block["displacement"] == 0.0
        assert block["rests_on_assumption"] is False
        assert block["receiver_fix"] is None


def test_a_noisy_two_photon_device_hands_every_block() -> None:
    """Eta = 0.9 and dark counts on every port: every block moved and handed.

    The ``m = 0`` and ``m = 1`` blocks are exact and snapped on their centres;
    the ``m = 2`` block is enclosed, snapped from the data, and handed with its
    radii recorded. No block rests on A-SNAP by the snap's own record: the run
    decides whether they are evaluated off their snap.
    """
    adapted = _declare(_artifact("noisy-cutoff-2"))
    assert isinstance(adapted, AdaptedRows)
    (snap,) = _snaps(adapted)
    assert snap["moved_blocks"] == ["m=0", "m=1", "m=2"]
    assert snap["handed_blocks"] == ["m=0", "m=1", "m=2"]
    for block in snap["blocks"]:
        assert block["status"] == "moved", block
        assert block["rests_on_assumption"] is False
        assert block["cause"] is None
    by_block = {block["block"]: block for block in snap["blocks"]}
    assert by_block["m=0"]["reference_kind"] == "exact"
    assert by_block["m=2"]["reference_kind"] == "none"
    handed = by_block["m=2"]["handed_reference"]
    assert handed["kind"] == "enclosed"
    assert F(handed["largest_radius"]) > 0 and F(handed["input_radius"]) > 0
    assert adapted.rows.instance_snap is not None
    assert {block.status for block in adapted.rows.instance_snap.blocks} == {"moved"}
    assert adapted.rows.handed_reference is not None


def test_an_ideal_two_photon_block_is_moved_and_handed() -> None:
    """The ideal device at N = 2: m = 0 and m = 1 kept, m = 2 moved and handed.

    The two-photon block is irrational (a rotated projector), so its reference
    is enclosed; the snap moves it from the data, by the fidelity-first rows,
    and hands the enclosure beside it. Nothing rests on A-SNAP by the snap's
    record, and the receiver names no fix.
    """
    adapted = _declare(_artifact("cutoff-2"))
    assert isinstance(adapted, AdaptedRows)
    (snap,) = _snaps(adapted)
    by_block = {block["block"]: block for block in snap["blocks"]}
    assert by_block["m=0"]["status"] == by_block["m=1"]["status"] == "kept"
    top = by_block["m=2"]
    assert top["status"] == "moved" and top["cause"] is None
    assert top["handed_reference_kind"] == "enclosed"
    assert top["rests_on_assumption"] is False
    assert snap["resting_blocks"] == []
    assert snap["receiver_fixes"] == {}


def test_the_enclosure_off_hands_the_exact_blocks_alone() -> None:
    """``reference_enclosure`` off: an enclosed block is not handed.

    The exact blocks ``m = 0`` and ``m = 1`` are still handed and snapped on
    their centres; the enclosed ``m = 2`` block is snapped from the data,
    handed no reference, and rests on A-SNAP in the group no usable reference
    with the cause ``enclosure_not_used`` (``foundations/req:snap-reference``
    (iii)(a)); the fix names what the receiver offered and the run parameter.
    """
    off = SnapSettings(reference_enclosure=False)
    adapted = _declare(_artifact("noisy-cutoff-2"), settings=off)
    assert isinstance(adapted, AdaptedRows)
    (snap,) = _snaps(adapted)
    assert snap["run_settings"]["reference_enclosure"] is False
    assert snap["handed_blocks"] == ["m=0", "m=1"]
    by_block = {block["block"]: block for block in snap["blocks"]}
    top = by_block["m=2"]
    assert top["reference_kind"] == "none" and top["handed_reference"] is None
    assert top["cause"] == "enclosure_not_used"
    assert top["group"] == "no_usable_reference"
    assert "reference_enclosure" in top["fix"]
    assert "enclosed" in top["receiver_fix"]
    assert snap["resting_blocks"] == ["m=2"]
    offered = {item["block"]: item["kind"] for item in snap["reference"]["offered"]}
    assert offered == {"m=0": "exact", "m=1": "exact", "m=2": "enclosed"}


def test_strict_refuses_a_moved_block_with_no_reference_handed() -> None:
    """The strict option refuses at the snap where no reference is handed.

    With enclosed references used, the ideal device's moved ``m = 2`` block is
    handed, so the snap leaves it to the run; with them not used, it is not
    handed, and the strict option refuses it here, naming the block.
    """
    passed = _declare(_artifact("cutoff-2"), settings=SnapSettings(strict=True))
    assert isinstance(passed, AdaptedRows), passed
    outcome = _declare(
        _artifact("cutoff-2"),
        settings=SnapSettings(reference_enclosure=False, strict=True),
    )
    assert isinstance(outcome, AdapterRefusal), outcome
    assert outcome.reason == "strict_snaps"
    assert "'m=2'" in outcome.detail and "A-SNAP" in outcome.detail


def test_a_coarse_grid_still_declares_an_admissible_family() -> None:
    """At ``2^-1`` the one-photon block is moved, and still an exact POVM.

    The exact reference of the ideal device's one-photon block is not a
    lattice family at ``k = 1``, so the snap moves it by the support-safe rows
    on its centres; it is handed, and what it declares is an exact POVM on the
    lattice.
    """
    adapted = _declare(_artifact("ideal"), lattice_exponent=1)
    assert isinstance(adapted, AdaptedRows), adapted
    statuses = {b["block"]: (b["status"], b["cause"]) for b in _blocks(adapted)}
    assert statuses == {"m=0": ("kept", None), "m=1": ("moved", None)}
    for _setting, _photons, family in _families(adapted.rows):
        total = family[0]
        for element in family[1:]:
            total = add(total, element)  # type: ignore[arg-type]
        assert total == identity(len(family[0]))  # type: ignore[arg-type]
        assert all(is_positive_semidefinite(e) for e in family)  # type: ignore[arg-type]


# ===========================================================================
#  The record.
# ===========================================================================


@pytest.mark.smoke
def test_every_block_record_carries_what_req_who_snaps_asks() -> None:
    """Per setting the settings and reference; per block status, handed or cause."""
    adapted = _declare(_artifact("noisy-cutoff-2"))
    assert isinstance(adapted, AdaptedRows)
    report = adapted.report
    assert report["declared_by"] == DECLARED_BY
    assert report["lattice_exponent"] == LATTICE_EXPONENT
    assert report["declared_tolerance"] == TAU
    assert report["photon_blocks_form"] == "dark_composed"
    assert report["snap_settings"] == DEFAULTS.as_record()
    assert "prop:optol-nobound" in str(report["note"])
    assert "snaps" not in report
    for snap in _snaps(adapted):
        assert snap["site"] == "receiver_photon_blocks" and snap["setting"] == "off"
        assert snap["run_settings"] == DEFAULTS.as_record()
        reference = snap["reference"]
        # The receiver's record of what it offered: the enclosures by digest,
        # never written out in a run record.
        assert "enclosures" not in reference
        assert len(reference["enclosures_sha256"]) == 64
        for block in snap["blocks"]:
            assert set(block) >= {
                "block", "status", "reference_kind", "handed_reference",
                "handed_reference_kind", "cause", "group", "fix", "receiver_fix",
                "support_not_preserved", "rests_on_assumption", "displacement",
            }, block
            assert not {"weight", "attainable_weight", "rho"} & set(block)


# ===========================================================================
#  It refuses rather than emitting an unverified family.
# ===========================================================================


def test_a_defect_above_the_ceiling_on_repair_is_refused_without_a_reference() -> None:
    """``tau`` decides where no reference is used, and refuses above it.

    With an exact reference the snap reads its centres and ``tau`` decides
    nothing; the enclosed two-photon block is snapped from its binary64 data,
    whose completeness residue is one ulp, and at ``tau = 0`` that is refused
    (spec/architecture.md 2.8).
    """
    kept = _declare(_artifact("ideal"), tolerance=0.0)
    assert isinstance(kept, AdaptedRows)
    outcome = _declare(_artifact("noisy-cutoff-2"), tolerance=0.0)
    assert isinstance(outcome, AdapterRefusal), outcome
    assert outcome.reason == "defect_above_tolerance"
    assert outcome.reason in REFUSAL_REASONS


def test_a_probe_free_refusal_names_no_probe_setting() -> None:
    """instances/snap-refusal-probe-wording, on a probe-free receiver.

    A probe-free receiver declares ``T = {off}``: the refusal names the
    family's block and not "setting 'off'".
    """
    outcome = _declare(_artifact("noisy-cutoff-2"), tolerance=0.0)
    assert isinstance(outcome, AdapterRefusal), outcome
    assert outcome.detail.startswith("the receiver's family: ")
    assert "setting" not in outcome.detail and "'off'" not in outcome.detail
    assert "block 'm=" in outcome.detail


@requires_probe
def test_a_refusal_with_a_probe_names_the_setting() -> None:
    """instances/snap-refusal-probe-wording, on a receiver with a probe.

    A receiver with a probe source keeps the setting in the detail. The
    machine-readable reason is the probe-free receiver's.
    """
    from instances.common.led import LedProbe

    outcome = _declare(_artifact("noisy-cutoff-2"), tolerance=0.0)
    assert isinstance(outcome, AdapterRefusal), outcome
    _BY_NAME["noisy-cutoff-2-window"] = ReceiverParameters(
        photon_cutoff=2,
        efficiency=(F(9, 10),) * 4,
        dark_count=(F(1, 10**6),) * 4,
        exact_window=3,
    )
    led = _artifact("noisy-cutoff-2-window", LedProbe(window=4))
    refused = _declare(led, tolerance=0.0)
    assert isinstance(refused, AdapterRefusal), refused
    assert refused.reason == outcome.reason
    assert refused.detail.startswith("the family at setting 'off': ")


def test_the_adapter_is_the_snap_bound_to_its_three_declarations() -> None:
    """A run declares the ceiling on repair, the lattice and the policy once."""
    artifact = _artifact("ideal")
    bound = rows_adapter(tolerance=TAU, lattice_exponent=24, settings=DEFAULTS)(
        artifact
    )
    direct = _declare(artifact, lattice_exponent=24)
    assert isinstance(bound, AdaptedRows) and isinstance(direct, AdaptedRows)
    assert bound.rows.photon_blocks == direct.rows.photon_blocks
    assert bound.report == direct.report


# ===========================================================================
#  And the declared family is the one a run actually uses.
# ===========================================================================


@pytest.mark.smoke
def test_the_run_declares_the_snapped_family_and_records_that_it_did() -> None:
    """The snap is wired into the device request, not merely available."""
    prologue = run_prologue(ReceiverParameters(photon_cutoff=1, exact_window=2))
    report = prologue.adaptation
    assert isinstance(report, dict)
    assert report["declared_by"] == DECLARED_BY
    assert report["lattice_exponent"] == LATTICE_EXPONENT
    assert [
        block["status"]
        for snap in report["measurement_snaps"]
        for block in snap["blocks"]
    ] == ["kept", "kept"]
    ledger = {entry.assumption_id for entry in prologue.reduction.assumption_ledger}
    assert "A-SNAP" not in ledger
