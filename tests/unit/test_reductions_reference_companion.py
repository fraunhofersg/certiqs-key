"""The reference companion beside the artefact: ``reductions/req:reference-companion``.

By ``reductions/cor:reference-companion``, ``reductions/lem:row-relaxation`` and,
for the flat instance, ``reductions/wpfss/cor:flat-companion``. The cases run
the optical BB84 instance's own preparation, which constructs the receiver,
hands its reference beside the snap and reduces (no solve; well under a second
each), and read the companion the reductions emitted beside the artefact.
"""

from __future__ import annotations

from dataclasses import replace
from fractions import Fraction as F
from typing import Any

import pytest

from certiqs_key.foundations.exact import (
    Cx,
    identity,
    is_hermitian,
    loewner_ge,
    scale,
    subtract,
)
from certiqs_key.reductions.artifact import ProofReductionArtifact
from certiqs_key.reductions.companion import (
    CompanionAbsence,
    NoReferenceCompanion,
    ReferenceCompanion,
)
from certiqs_key.reductions.emit import reduce
from certiqs_key.reductions.inputs import ReductionCall
from certiqs_key.reductions.instance import BuildContext, BuildOutcome
from certiqs_key.reductions.reasons import Relation
from certiqs_key.reductions.sectors import SectorKind
from certiqs_key.reductions.wpfss.api import FlatInstanceBuilder
from certiqs_key.runs.config import SolverSettings
from certiqs_key.runs.pipeline import Preparation

pytestmark = pytest.mark.contract


PORTS = ("H", "V", "D", "A")
NOISY = {
    "efficiency": dict.fromkeys(PORTS, F(9, 10)),
    "dark_count": dict.fromkeys(PORTS, F(1, 10**6)),
}


def _prepared(**device: Any) -> Preparation:
    from instances.optical_bb84.surface import default_config, preparation

    base = default_config(solver=SolverSettings(method="fw", max_iterations=3))
    config = base.with_(device={**base.device, **device}) if device else base
    outcome = preparation(config)
    assert isinstance(outcome, Preparation)
    return outcome


def _artifact(**device: Any) -> ProofReductionArtifact:
    artifact = _prepared(**device).reduction_artifact
    assert artifact is not None
    return artifact


def _companion(artifact: ProofReductionArtifact) -> ReferenceCompanion:
    companion = artifact.reference_companion
    assert isinstance(companion, ReferenceCompanion), companion
    return companion


def test_the_companion_has_the_artefact_s_shape_and_differs_on_data_only() -> None:
    """cor:reference-companion (i); req:reference-companion (ii), (iv), (v)."""
    artifact = _artifact(photon_cutoff=F(2), exact_window=F(3), **NOISY)
    companion = _companion(artifact)
    assert companion.claim == "reductions/wpfss/cor:flat-companion"
    assert companion.evaluation_only
    sectors = artifact.target_descriptor.sectors.sectors
    assert set(companion.target_centre) == set(artifact.target_povm)
    for outcome, blocks in artifact.target_povm.items():
        centre = companion.target_centre[outcome]
        assert [len(block) for block in centre] == [len(block) for block in blocks]
        for sector, mine, theirs, radius in zip(
            sectors, centre, blocks, companion.target_radius[outcome], strict=True
        ):
            if sector.kind is SectorKind.SCALAR:
                # The scalar values are the instance's, exactly, with radius 0.
                assert mine == theirs
                assert all(r == 0 for row in radius for r in row)
            assert is_hermitian(mine)
    # Every block of the device is handed: m = 0, 1 exactly, m = 2 enclosed.
    kinds = {block.name: block.kind for block in companion.blocks}
    assert kinds == {"m=0, t=off": "exact", "m=1, t=off": "exact",
                     "m=2, t=off": "enclosed"}
    assert all(block.handed for block in companion.blocks)
    assert 0 < companion.datum_largest_radius < F(1, 10**30)
    # (iv): nothing of domination; the artefact itself is emitted as it is.
    record = companion.as_record()
    assert record["evaluation_only"] is True and len(record["exact_data_sha256"]) == 64
    assert artifact.as_machine_record()["reference_companion"] == record


def test_on_an_exact_block_the_companion_carries_the_reference_not_the_snap() -> None:
    """The datum on a handed exact block is the reference's centre, unnormalised.

    The noisy device's snap moves every block (each uncertified in a run that
    does not request certification); the companion's data sector carries
    q_t times the reference's own centre instead, off the lattice, exactly.
    """
    prepared = _prepared(photon_cutoff=F(2), exact_window=F(3), **NOISY)
    artifact = prepared.reduction_artifact
    assert artifact is not None
    companion = _companion(artifact)
    sectors = artifact.target_descriptor.sectors.sectors
    first = next(i for i, s in enumerate(sectors) if s.kind is SectorKind.DATA)
    moved = [
        outcome
        for outcome in artifact.target_povm
        if companion.target_centre[outcome][first]
        != artifact.target_povm[outcome][first]
    ]
    assert moved, "the snap moved no block, so the case shows nothing"


def test_the_licensed_route_carries_its_own_rows_relaxed_outward() -> None:
    """req:reference-companion (iii); lem:row-relaxation (i), (ii).

    The companion's entry is the flat instance's entry at the companion's datum
    (wpfss/cor:flat-companion), emitted as a Hermitian binary64 operator with
    the constant moved down by delta: -delta 1 <= O' - O <= delta 1.
    """
    artifact = _artifact(route="licensed", **NOISY)
    companion = _companion(artifact)
    assert len(companion.entries) == len(artifact.constraint_list) == 1
    (item,) = companion.entries
    (exact,) = artifact.constraint_list
    assert item.relaxed and item.delta > 0
    assert item.relaxes == exact.label
    entry = item.entry
    assert entry.relation is Relation.GE
    assert entry.constant <= exact.constant - item.delta
    assert entry.certificate_kind is exact.certificate_kind
    for block in entry.operator:
        assert is_hermitian(block)
        for row in block:
            for value in row:
                assert F(float(value.re)) == value.re and F(float(value.im)) == value.im
    # The exact operator of the companion's own entry is its target element at
    # the companion's datum minus p_o Pi_flag; rebuild it and check (i).
    sectors = artifact.target_descriptor.sectors
    flag = sectors.block_projector(
        sum(sectors.data_dimensions), len(artifact.target_povm)
    )
    weight = F(exact.label.split(" - ")[1].split(" ")[0])
    outcome = next(
        v for v in artifact.target_povm
        if exact.label.startswith(f"F^FSS_{v[0]}")
    )
    rebuilt = tuple(
        subtract(block, scale(weight, projector))
        for block, projector in zip(
            companion.target_centre[outcome], flag, strict=True
        )
    )
    for rounded, original in zip(entry.operator, rebuilt, strict=True):
        error = subtract(rounded, original)
        size = len(error)
        bound = scale(Cx(item.delta, F(0)), identity(size))
        assert loewner_ge(bound, error)
        assert loewner_ge(error, scale(Cx(-item.delta, F(0)), identity(size)))


def test_no_companion_where_no_block_is_handed_or_no_claim_covers_it() -> None:
    """req:reference-companion (vi): the record says which of the two holds.

    The noisy device's emission normalizer moves no class, so with no block
    handed nothing would be evaluated off its snap and no companion is formed.
    """
    call = _call()
    unhanded = replace(
        call, artifact_rows=replace(call.artifact_rows, handed_reference=None)
    )
    outcome = reduce(unhanded, FlatInstanceBuilder())
    assert outcome.artifact is not None
    absent = outcome.artifact.reference_companion
    assert isinstance(absent, NoReferenceCompanion)
    assert absent.reason is CompanionAbsence.NO_BLOCK_HANDED_NO_CLASS_MOVED

    class Unclaimed:
        """A builder that names no claim establishing (H-REF)."""

        def build(self, context: BuildContext) -> BuildOutcome:
            return FlatInstanceBuilder().build(context)

    outcome = reduce(call, Unclaimed())
    assert outcome.artifact is not None
    absent = outcome.artifact.reference_companion
    assert isinstance(absent, NoReferenceCompanion)
    assert absent.reason is CompanionAbsence.NO_H_REF_CLAIM
    assert outcome.artifact.as_machine_record()["reference_companion"] == {
        "emitted": False,
        "reason": "no_h_ref_claim",
        "detail": absent.detail,
    }


def test_enclosed_blocks_are_recentred_before_the_construction() -> None:
    """req:reference-companion (i): the ideal device at angle 1/7 (P19).

    Its m = 1 and m = 2 blocks are known through enclosures whose discs contain
    zero at entries the model has exactly zero; the companion sets those
    centres to zero and records how many.
    """
    companion = _companion(
        _artifact(photon_cutoff=F(2), exact_window=F(3), half_wave_angle=F(1, 7))
    )
    enclosed = [block for block in companion.blocks if block.kind == "enclosed"]
    assert enclosed and all(block.handed for block in companion.blocks)
    assert sum(block.recentred_entries for block in enclosed) > 0


def test_the_licensed_relaxation_at_angle_one_seventh_bounds_the_enclosure() -> None:
    """lem:row-relaxation; req:reference-companion (iii), with radii not zero.

    The enclosed reference on the licensed
    route, so that the entry's enclosure has a radius. Its operator is the
    target element at the companion's datum minus p_o Pi_flag, affine in that
    element alone with coefficient 1, so its enclosure is the element's:
    centre ``C = target_centre[v] - p_o Pi_flag``, radius
    ``R = target_radius[v]``. ``delta`` is recomputed from those, exactly, as
    ``max_i sum_l (|Re(O' - C)| + |Im(O' - C)| + R)_il``.
    """
    artifact = _artifact(
        route="licensed",
        photon_cutoff=F(2),
        exact_window=F(3),
        half_wave_angle=F(1, 7),
    )
    companion = _companion(artifact)
    assert any(block.kind == "enclosed" for block in companion.blocks)
    (item,) = companion.entries
    (exact,) = artifact.constraint_list
    assert item.relaxed and item.relaxes == exact.label
    sectors = artifact.target_descriptor.sectors
    flag = sectors.block_projector(
        sum(sectors.data_dimensions), len(artifact.target_povm)
    )
    weight = F(exact.label.split(" - ")[1].split(" ")[0])
    outcome = next(
        v for v in artifact.target_povm if exact.label.startswith(f"F^FSS_{v[0]}")
    )
    radius_seen = F(0)
    delta = F(0)
    for rounded, centre, radius, projector in zip(
        item.entry.operator,
        companion.target_centre[outcome],
        companion.target_radius[outcome],
        flag,
        strict=True,
    ):
        exact_block = subtract(centre, scale(weight, projector))
        for near_row, row, radius_row in zip(rounded, exact_block, radius, strict=True):
            total = F(0)
            for near, value, r in zip(near_row, row, radius_row, strict=True):
                total += abs(near.re - value.re) + abs(near.im - value.im) + r
                radius_seen = max(radius_seen, r)
            delta = max(delta, total)
    assert radius_seen > 0, "no radius reached the entry, so the case shows nothing"
    assert item.delta == delta
    assert item.entry.constant <= exact.constant - delta


def _partially_handed(call: ReductionCall, photons: int, letters: int) -> ReductionCall:
    """Return ``call`` with block ``photons`` unhanded for its first ``letters``."""
    handed = call.artifact_rows.handed_reference
    assert handed is not None
    blocks = dict(handed.blocks)
    for key in list(blocks)[:letters]:
        row = list(blocks[key])
        row[photons] = None
        blocks[key] = tuple(row)
    return replace(
        call,
        artifact_rows=replace(
            call.artifact_rows, handed_reference=replace(handed, blocks=blocks)
        ),
    )


def _data_sector_defects(
    artifact: ProofReductionArtifact, companion: ReferenceCompanion
) -> list[F]:
    """Return, per data sector, how far the companion's elements miss the identity."""
    out = []
    for index, sector in enumerate(artifact.target_descriptor.sectors.sectors):
        if sector.kind is not SectorKind.DATA:
            continue
        total = None
        for blocks in companion.target_centre.values():
            block = blocks[index]
            total = block if total is None else tuple(
                tuple(x + y for x, y in zip(r1, r2, strict=True))
                for r1, r2 in zip(total, block, strict=True)
            )
        assert total is not None
        defect = subtract(total, identity(len(total)))
        out.append(max(abs(v.re) + abs(v.im) for row in defect for v in row))
    return out


def test_a_block_handed_for_some_letters_only_is_carried_snapped_whole() -> None:
    """req:reference-companion (i), (v); cor:reference-companion (H-REF).

    The noisy device's handed reference with the
    m = 1 element of one letter dropped. The companion must not mix the
    reference and the snap inside one block, which breaks the exact
    completeness (H-REF) needs: the whole m = 1 block
    is carried snapped, recorded so with the letters that were named, and
    every data sector of the companion still sums to the identity exactly.
    """
    call = _partially_handed(_call(), photons=1, letters=1)
    outcome = reduce(call, FlatInstanceBuilder())
    assert outcome.artifact is not None
    companion = _companion(outcome.artifact)
    by_name = {block.name: block for block in companion.blocks}
    assert not by_name["m=1, t=off"].handed
    letters = len(call.artifact_rows.photon_blocks)
    assert by_name["m=1, t=off"].partially_handed_letters == letters - 1
    assert by_name["m=1, t=off"].as_record()["carries"] == "snapped_block"
    assert by_name["m=0, t=off"].handed and by_name["m=2, t=off"].handed
    assert all(block.partially_handed_letters == 0 for block in companion.handed_blocks)
    assert all(
        defect == 0 for defect in _data_sector_defects(outcome.artifact, companion)
    )


def test_a_reference_that_hands_no_block_whole_emits_no_companion() -> None:
    """req:reference-companion (vi): a block handed in part is not handed."""
    call = _call()
    for photons in range(3):
        call = _partially_handed(call, photons=photons, letters=1)
    outcome = reduce(call, FlatInstanceBuilder())
    assert outcome.artifact is not None
    absent = outcome.artifact.reference_companion
    assert isinstance(absent, NoReferenceCompanion)
    assert absent.reason is CompanionAbsence.NO_BLOCK_HANDED_NO_CLASS_MOVED
    assert "handed in part" in absent.detail


def _call(route: str = "encoded") -> ReductionCall:
    """Return the reduction call the noisy two-photon device's prologue makes.

    The published order of the run tier (``tests/support/
    optical_bb84_prologue.py``): construct, dock through the instance's rows
    adapter, which snaps and hands the reference, and call the reduction.
    """
    from instances.common.optics import ReceiverParameters
    from tests.support.lowered_templates import optical_lowered

    from certiqs_key.receiver.construct import construct_receiver
    from certiqs_key.runs.pipeline import AdaptedRows, DeviceRequests

    parameters = ReceiverParameters(
        efficiency=(F(9, 10),) * 4,
        dark_count=(F(1, 10**6),) * 4,
        photon_cutoff=2,
        exact_window=3,
    )
    device = optical_lowered(parameters, route=route).device
    assert isinstance(device, DeviceRequests) and device.rows_adapter is not None
    artifact = construct_receiver(device.receiver_request).artifact
    assert artifact is not None
    adapted = device.rows_adapter(artifact)
    assert isinstance(adapted, AdaptedRows)
    assert adapted.rows.handed_reference is not None
    return ReductionCall(
        adapted.rows, device.reduction_declaration, device.reduction_request
    )


# ---------------------------------------------------------------------------
#  The companion on a producer-only run, and requested entries on the companion.
# ---------------------------------------------------------------------------


def _optical_call(route: str, photon_cutoff: int = 2) -> ReductionCall:
    """Return the noisy device's reduction call at a cutoff, on a route."""
    from instances.common.optics import ReceiverParameters
    from tests.support.lowered_templates import optical_lowered

    from certiqs_key.receiver.construct import construct_receiver
    from certiqs_key.runs.pipeline import AdaptedRows, DeviceRequests

    parameters = ReceiverParameters(
        efficiency=(F(9, 10),) * 4,
        dark_count=(F(1, 10**6),) * 4,
        photon_cutoff=photon_cutoff,
        exact_window=3,
    )
    device = optical_lowered(parameters, route=route).device
    assert isinstance(device, DeviceRequests) and device.rows_adapter is not None
    artifact = construct_receiver(device.receiver_request).artifact
    assert artifact is not None
    adapted = device.rows_adapter(artifact)
    assert isinstance(adapted, AdaptedRows)
    return ReductionCall(
        adapted.rows, device.reduction_declaration, device.reduction_request
    )


def _two_sector_artifact(
    call: ReductionCall, builder: Any = None
) -> tuple[ProofReductionArtifact, str]:
    """Return the licensed+two-sector artefact of ``call`` and its requested label."""
    from instances.common.passive_device import two_sector_provider

    builder = FlatInstanceBuilder() if builder is None else builder
    first = reduce(call, builder).artifact
    assert first is not None
    requested = two_sector_provider()(first)
    assert len(requested) == 1, "no two-sector entry was asked for"
    outcome = reduce(
        replace(call, request=replace(call.request, carried_operators=requested)),
        builder,
    )
    assert outcome.artifact is not None, outcome.refusal
    return outcome.artifact, requested[0].label


def test_the_two_sector_entry_is_formed_on_the_companion_and_relaxed() -> None:
    """req:reference-companion (iii), (v); cor:reference-companion (vi).

    The operator eq:two-sector-entry
    requested on licensed+two-sector is formed on the companion at its writing,
    F_e[A^ref] - a Pi_<=N - b Pi_Flag, where wpfss/cor:flat-companion's
    eq:companion-two-sector holds, and relaxed outward: -delta 1 <= O' - O <= delta 1
    for the companion form O, rebuilt here as the artefact's operator with the
    emitted element replaced by the companion's.
    """
    artifact, label = _two_sector_artifact(_optical_call("licensed"))
    companion = _companion(artifact)
    (formed,) = companion.requested_entries_formed
    assert formed.label == label and formed.writing == "two_sector"
    assert formed.established_by == (
        "reductions/wpfss/cor:flat-companion (eq:companion-two-sector)"
    )
    assert companion.requested_entries_not_formed == ()
    record = companion.as_record()
    assert record["requested_entries_formed"][0]["label"] == label
    exact = next(e for e in artifact.constraint_list if e.label == label)
    items = [item for item in companion.entries if item.relaxes == label]
    assert items, "the two-sector entry is not among the companion's entries"
    outcome = next(
        v for v in artifact.target_povm if label.startswith(f"F^FSS_{v[0]}")
    )
    form = tuple(
        tuple(
            tuple(o - t + c for o, t, c in zip(ro, rt, rc, strict=True))
            for ro, rt, rc in zip(bo, bt, bc, strict=True)
        )
        for bo, bt, bc in zip(
            exact.operator,
            artifact.target_povm[outcome],
            companion.target_centre[outcome],
            strict=True,
        )
    )
    for item in items:
        assert item.entry.relation is Relation.GE
        assert item.entry.constant <= -item.delta
        for rounded, original in zip(item.entry.operator, form, strict=True):
            error = subtract(rounded, original)
            size = len(error)
            assert loewner_ge(scale(Cx(item.delta, F(0)), identity(size)), error)
            assert loewner_ge(error, scale(Cx(-item.delta, F(0)), identity(size)))


def test_an_two_sector_entry_the_reference_does_not_certify_is_left_out(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """req:reference-companion (iii): the entry is not formed, with its reason.

    At the noisy one-photon device the floor of the SNAPPED multi-click block
    exceeds what the reference certifies (the snap moves the block by about
    a itself). Asked at the snapped floor alone, the artefact certifies the
    entry, the companion does not, and leaves it out, so its feasible set
    only grows (meat-core/prop:reference-companion).
    """
    from instances.common import passive_device

    monkeypatch.setattr(passive_device, "_reference_floor", lambda *a, **k: None)
    artifact, label = _two_sector_artifact(_optical_call("licensed", photon_cutoff=1))
    companion = _companion(artifact)
    assert any(e.label == label for e in artifact.constraint_list)
    (left_out,) = companion.requested_entries_not_formed
    assert left_out.label == label
    assert str(left_out.reason) == "certificate_not_established"
    assert "eq:companion-two-sector fails" in left_out.detail
    assert not [item for item in companion.entries if item.relaxes == label]


def test_an_two_sector_entry_needs_a_claim_for_the_instance() -> None:
    """req:reference-companion (iii): no claim for the instance, no entry."""

    class NoEntryClaims:
        """The flat builder with its (H-REF) claim, none for the two-sector entry."""

        companion_claim = "reductions/wpfss/cor:flat-companion"

        def build(self, context: BuildContext) -> BuildOutcome:
            return FlatInstanceBuilder().build(context)

    artifact, label = _two_sector_artifact(_optical_call("licensed"), NoEntryClaims())
    (left_out,) = _companion(artifact).requested_entries_not_formed
    assert left_out.label == label
    assert str(left_out.reason) == "no_claim_for_instance"


def test_a_requested_class_marginal_entry_is_carried_as_it_is() -> None:
    """cor:reference-companion (vi): the class-marginal entry is the artefact's.

    rem:unsound's sum_y F_(y,t) = q_t is the same operator at every admissible
    datum, so the companion carries it with radius zero and delta zero, an
    equality, its certificate established by cor:reference-companion (vi).
    """
    from certiqs_key.foundations.exact import direct_sum
    from certiqs_key.reductions.constraints import flag_sum_over_setting
    from certiqs_key.reductions.inputs import CarriedOperatorRequest
    from certiqs_key.reductions.reasons import CertificateKind

    call = _optical_call("licensed")
    first = reduce(call, FlatInstanceBuilder()).artifact
    assert first is not None
    order = list(first.target_povm)
    setting = order[0][1]
    weight = call.declaration.probe_declaration.weights[setting]
    asked = CarriedOperatorRequest(
        label=f"sum_y F_(y,{setting}) = q_{setting}",
        operator=flag_sum_over_setting(
            [direct_sum(list(first.target_povm[v])) for v in order], order, setting
        ),
        relation=Relation.EQ,
        constant=weight,
        certificate_kind=CertificateKind.IDENTITY,
        certified_against=first.squashing_channel.identity,
    )
    outcome = reduce(
        replace(call, request=replace(call.request, carried_operators=(asked,))),
        FlatInstanceBuilder(),
    )
    assert outcome.artifact is not None, outcome.refusal
    companion = _companion(outcome.artifact)
    (formed,) = companion.requested_entries_formed
    assert formed.writing == "class_marginal"
    assert formed.established_by == "reductions/cor:reference-companion (vi)"
    (item,) = [item for item in companion.entries if item.relaxes == asked.label]
    exact = next(e for e in outcome.artifact.constraint_list if e.label == asked.label)
    assert not item.relaxed and item.delta == 0
    assert item.entry == exact
