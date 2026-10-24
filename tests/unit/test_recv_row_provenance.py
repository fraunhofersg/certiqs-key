"""``reductions/req:recv-row-provenance``: where the A-RECV row is omitted.

WHY THIS EXISTS. The reductions ledger omits the row of ``ass:recv`` (A-RECV)
only where the run attests that it built the receiver artefact itself and
handed it on as emitted, the record carries that artefact's ledger
(conditions (i), (iii), the run's ``receiver_provenance``), and the artefact
is the installed receiver's version, passes the supplier refusals, records a
model admissible exactly and carries the ``rigorous`` label (conditions (ii),
(iv), decided on the artefact). A wrong omission understates what a key
length rests on, which is the direction PRINCIPLES.md section 2.1 forbids, so
every way a condition fails is held here to keep the row:

* an exact, rigorous artefact the run built: the row is omitted, the omission
  recorded with the artefact's version, and the run's record carries the
  receiver's own ledger;
* a weight evaluated in floating point (A-EIG's case among them): kept;
* a declaration admitted only within the receiver tolerances (no model
  admissible exactly, ``port_grams_not_enclosed``): kept;
* no attestation (a hand-built call, an artefact from outside the run), an
  attestation naming another artefact, rows that are not the artefact's own
  docking, a version that is not the installed receiver's: kept.

The cases are built from real receiver artefacts and the shipped optical BB84
instance; the conditions are hand-derived from the requirement, not read back
from the code.
"""

from __future__ import annotations

import importlib
from collections.abc import Iterator
from dataclasses import replace
from fractions import Fraction
from typing import Any

import numpy as np
import pytest
from receiver_povm_support import bb84_channel_only_request, probe_free_matrix_request

from certiqs_key.foundations.assurance import Assurance
from certiqs_key.receiver import GramFamily, ReceiverRequest, construct_receiver
from certiqs_key.receiver import construct as construct_module
from certiqs_key.receiver.artifact import (
    MATHEMATICAL_SPEC_VERSION,
    ReceiverMeasurementArtifact,
)
from certiqs_key.receiver.docking import DockingRefusal, receiver_artifact_rows
from certiqs_key.receiver.rigorous import PORT_GRAMS_NOT_ENCLOSED
from certiqs_key.reductions.artifact import ProofReductionArtifact
from certiqs_key.reductions.emit import (
    emitted_assumption_rows,
    receiver_row_omitted_on_provenance,
)
from certiqs_key.reductions.errors import MalformedInputError
from certiqs_key.reductions.inputs import (
    HighPhotonBound,
    LinkDeclaration,
    ProbeDeclaration,
    ProtocolDeclaration,
    ReceiverArtifactRows,
    ReductionCall,
    ReductionRequest,
)
from certiqs_key.reductions.provenance import ReceiverProvenance
from certiqs_key.reductions.reasons import LinkKind, LinkStage, SourceMode
from certiqs_key.runs import pipeline
from certiqs_key.runs.receiver_provenance import attest_receiver_provenance

pytestmark = pytest.mark.contract

ACCEPTED = (MATHEMATICAL_SPEC_VERSION,)


def _artifact(request: ReceiverRequest) -> ReceiverMeasurementArtifact:
    emission = construct_receiver(request)
    assert emission.refusal is None, emission.refusal
    assert emission.artifact is not None
    return emission.artifact


def _rows(artifact: ReceiverMeasurementArtifact) -> ReceiverArtifactRows:
    rows = receiver_artifact_rows(artifact)
    assert not isinstance(rows, DockingRefusal), rows
    return rows


def _call(
    rows: ReceiverArtifactRows,
    provenance: ReceiverProvenance | None,
    accepted: tuple[str, ...] = ACCEPTED,
) -> ReductionCall:
    """Return a reduction call reading ``rows``; only the decision reads it here."""
    settings = rows.bound_quantifier_domain.settings
    return ReductionCall(
        rows,
        ProtocolDeclaration(
            probe_declaration=ProbeDeclaration(
                settings=settings,
                weights=dict.fromkeys(settings, Fraction(1, len(settings))),
            ),
            detection_alphabet=rows.detection_alphabet,
            photon_cutoff=rows.bound_quantifier_domain.cutoff,
            source_mode=SourceMode.UNTRUSTED,
            joint_alphabet=tuple(
                (letter, setting)
                for setting in settings
                for letter in rows.detection_alphabet
            ),
        ),
        ReductionRequest(
            lattice_exponent=12,
            link_declarations=(
                LinkDeclaration(stage=LinkStage.RECEIVER, kind=LinkKind.WPFSS),
            ),
            route="encoded",
            requested_assurance=Assurance.ESTIMATE,
            accepted_receiver_versions=accepted,
        ),
        receiver_provenance=provenance,
    )


@pytest.fixture
def floating_point_weights(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Every setting keeps its floating-point weight (no enclosure)."""
    monkeypatch.setattr(
        construct_module,
        "rigorous_weights",
        lambda validated: {
            setting.label: PORT_GRAMS_NOT_ENCLOSED
            for setting in validated.request.probe_declaration.settings
        },
    )
    yield


def _tolerance_admitted() -> ReceiverMeasurementArtifact:
    """Return a declaration admitted only at the receiver tolerances (no exact model).

    The route-(ii) receiver's port Grams sum to ``1/2``; doubled and stretched
    by ``2^-20`` they sum to ``(1 + 2^-20) 1``, which the tolerance admits and
    the exact decision does not (``receiver/req:exact-route-decision`` (i)).
    """
    request = probe_free_matrix_request()
    supplied = _artifact(request)
    stretched = GramFamily(
        tuple(label for label, _ in supplied.port_grams),
        tuple(
            np.asarray(matrix * (2 + 2.0**-19), dtype=np.complex128)
            for _, matrix in supplied.port_grams
        ),
    )
    return _artifact(replace(request, instrument_matrix=None, port_grams=stretched))


# ---------------------------------------------------------------------------
#  The decision on the artefact: (ii) and (iv), with the run's word for (i), (iii)
# ---------------------------------------------------------------------------


def test_an_exact_rigorous_artefact_the_run_attests_omits_the_row() -> None:
    artifact = _artifact(bb84_channel_only_request())
    assert artifact.bound_evaluation == "rigorous"
    rows = _rows(artifact)
    assert rows.exact_model_admissible is True
    provenance = attest_receiver_provenance(artifact, rows)
    assert provenance == ReceiverProvenance.of(rows)
    assert provenance is not None
    assert provenance.artifact_version == MATHEMATICAL_SPEC_VERSION
    assert receiver_row_omitted_on_provenance(_call(rows, provenance)) == (
        MATHEMATICAL_SPEC_VERSION,
    )


def test_without_the_attestation_the_row_is_kept() -> None:
    """A hand-built call or an artefact from outside the run carries no word."""
    rows = _rows(_artifact(bb84_channel_only_request()))
    assert receiver_row_omitted_on_provenance(_call(rows, None)) == ()


def test_an_attestation_naming_another_artefact_keeps_the_row() -> None:
    rows = _rows(_artifact(bb84_channel_only_request()))
    other = ReceiverProvenance.of(_rows(_tolerance_admitted()))
    assert receiver_row_omitted_on_provenance(_call(rows, other)) == ()


def test_an_attestation_does_not_carry_over_to_other_rows() -> None:
    """The word is bound to the rows it attests, not to the version alone.

    Two exact, rigorous receiver artefacts at the installed version: the
    attestation minted for one does not omit the row of the other, though the
    version, the label and the exact-route record agree.
    """
    ideal = _artifact(bb84_channel_only_request())
    lossy = _artifact(bb84_channel_only_request(efficiencies=(Fraction(9, 10),) * 4))
    assert ideal.bound_evaluation == lossy.bound_evaluation == "rigorous"
    first, second = _rows(ideal), _rows(lossy)
    assert first.mathematical_spec_version == second.mathematical_spec_version
    assert first.exact_model_admissible and second.exact_model_admissible
    minted = attest_receiver_provenance(ideal, first)
    assert minted is not None
    assert receiver_row_omitted_on_provenance(_call(first, minted)) == (
        MATHEMATICAL_SPEC_VERSION,
    )
    assert receiver_row_omitted_on_provenance(_call(second, minted)) == ()


def test_a_version_other_than_the_installed_receiver_s_keeps_the_row() -> None:
    """(ii): the declared version is the one the installed module states."""
    rows = replace(
        _rows(_artifact(bb84_channel_only_request())),
        mathematical_spec_version="receiver@0.0.1",
    )
    provenance = ReceiverProvenance.of(rows)
    call = _call(rows, provenance, accepted=("receiver@0.0.1",))
    assert receiver_row_omitted_on_provenance(call) == ()


def test_an_artefact_the_supplier_refusals_refuse_keeps_the_row() -> None:
    """(ii): req:supplier-version-accepted and req:supplier-ledger-refusals."""
    rows = _rows(_artifact(bb84_channel_only_request()))
    provenance = ReceiverProvenance.of(rows)
    assert receiver_row_omitted_on_provenance(_call(rows, provenance, ())) == ()
    no_results = replace(rows, validation_results_present=False)
    assert receiver_row_omitted_on_provenance(
        _call(no_results, ReceiverProvenance.of(no_results))
    ) == ()
    short = replace(
        rows, inherited_assumption_ledger=rows.inherited_assumption_ledger[1:]
    )
    assert receiver_row_omitted_on_provenance(
        _call(short, ReceiverProvenance.of(short))
    ) == ()


def test_a_floating_point_weight_keeps_the_row(floating_point_weights: None) -> None:
    """(iv): a weight evaluated in floating point; the run's word does not help."""
    artifact = _artifact(bb84_channel_only_request())
    assert artifact.bound_evaluation == "floating_point"
    rows = _rows(artifact)
    provenance = attest_receiver_provenance(artifact, rows)
    assert provenance is not None  # the run built it; (iv) is the artefact's
    assert receiver_row_omitted_on_provenance(_call(rows, provenance)) == ()


def test_a_tolerance_admitted_declaration_keeps_the_row() -> None:
    """(iv): no model admissible exactly (``port_grams_not_enclosed``)."""
    artifact = _tolerance_admitted()
    assert not artifact.photon_blocks[0].reference.exact_route.has_exact_model
    rows = _rows(artifact)
    assert rows.exact_model_admissible is False
    assert rows.bound_evaluation == "floating_point"
    provenance = attest_receiver_provenance(artifact, rows)
    assert provenance is not None
    assert receiver_row_omitted_on_provenance(_call(rows, provenance)) == ()
    # And the label alone does not stand in for the exact-route record.
    rigorous_but_no_model = replace(rows, bound_evaluation="rigorous")
    assert receiver_row_omitted_on_provenance(
        _call(rigorous_but_no_model, ReceiverProvenance.of(rigorous_but_no_model))
    ) == ()


def test_rows_built_by_hand_default_to_keeping_the_row() -> None:
    """``exact_model_admissible`` defaults to False, the direction that keeps it."""
    rows = _rows(_artifact(bb84_channel_only_request()))
    fields = {
        name: getattr(rows, name)
        for name in rows.__dataclass_fields__
        if name != "exact_model_admissible"
    }
    by_hand = ReceiverArtifactRows(**fields)
    assert by_hand.exact_model_admissible is False
    provenance = ReceiverProvenance.of(by_hand)
    assert receiver_row_omitted_on_provenance(_call(by_hand, provenance)) == ()


# ---------------------------------------------------------------------------
#  The run's attestation: only for the artefact it built, handed on as emitted
# ---------------------------------------------------------------------------


def test_rows_that_are_not_the_artefact_s_docking_obtain_no_attestation() -> None:
    """A changed weight is not the artefact handed on as emitted (i)."""
    artifact = _artifact(bb84_channel_only_request())
    rows = _rows(artifact)
    bound = rows.high_photon_bounds[0]
    changed = replace(
        bound,
        per_setting=tuple(
            (setting, weight / 2) for setting, weight in bound.per_setting
        ),
    )
    assert isinstance(changed, HighPhotonBound)
    altered = replace(rows, high_photon_bounds=(changed, *rows.high_photon_bounds[1:]))
    assert attest_receiver_provenance(artifact, altered) is None
    claimed_exact = replace(_rows(_tolerance_admitted()), exact_model_admissible=True)
    assert attest_receiver_provenance(_tolerance_admitted(), claimed_exact) is None


def test_the_declaration_s_own_blocks_do_not_withdraw_the_attestation() -> None:
    """Snapped blocks below the cutoff are the instance's declaration, not imports."""
    artifact = _artifact(bb84_channel_only_request())
    rows = _rows(artifact)
    snapped = replace(rows, photon_blocks=dict.fromkeys(rows.photon_blocks, ()))
    minted = attest_receiver_provenance(artifact, snapped)
    assert minted == ReceiverProvenance.of(rows)
    assert minted is not None and minted.names(snapped) and minted.names(rows)


def test_a_provenance_names_an_artefact() -> None:
    rows = _rows(_artifact(bb84_channel_only_request()))
    with pytest.raises(ValueError, match="names the receiver artefact"):
        ReceiverProvenance.of(replace(rows, mathematical_spec_version=" "))


def test_a_discharged_a_recv_row_links_its_assumption() -> None:
    """F-3: the not-engaged row names the assumption it discharges, linked."""
    from pathlib import Path

    page = (
        Path(__file__).resolve().parents[2]
        / "runs" / "report_examples" / "optical_bb84" / "report.md"
    ).read_text(encoding="utf-8")
    (row,) = [line for line in page.splitlines() if line.startswith("| [A-RECV]")]
    assert "nameddest=claim-reductions/ass:recv)" in row
    assert "reductions/req:recv-row-provenance" in row


# ---------------------------------------------------------------------------
#  The emission: the row, the record of its omission, and the run's record
# ---------------------------------------------------------------------------


def test_the_emitted_rows_drop_a_recv_exactly_where_omitted() -> None:
    chain = _prepare().reduction_artifact.reduction_chain
    kept = {row.identifier for row in emitted_assumption_rows(chain)}
    dropped = {
        row.identifier
        for row in emitted_assumption_rows(chain, receiver_row_omitted=True)
    }
    assert "A-RECV" in kept
    assert kept - dropped == {"A-RECV"}


def _prepare(monkeypatch: pytest.MonkeyPatch | None = None, **patches: Any) -> Any:
    surface = importlib.import_module("instances.optical_bb84.surface")
    if monkeypatch is not None:
        for name, value in patches.items():
            monkeypatch.setattr(pipeline, name, value)
    return surface.preparation(surface.default_config())


def _ledger_ids(artifact: ProofReductionArtifact) -> set[str]:
    return {entry.assumption_id for entry in artifact.assumption_ledger}


def test_a_run_that_built_an_exact_rigorous_receiver_omits_and_records() -> None:
    prepared = _prepare()
    reduction = prepared.reduction_artifact
    receiver = prepared.receiver_artifact
    assert receiver.bound_evaluation == "rigorous"
    assert "A-RECV" not in _ledger_ids(reduction)
    assert reduction.receiver_row_omitted_on_provenance == (
        receiver.mathematical_spec_version,
    )
    record = reduction.as_machine_record()
    assert record["receiver_row_omitted_on_provenance"] == [
        receiver.mathematical_spec_version
    ]
    # (iii): the run's record carries the receiver artefact's own ledger.
    from certiqs_key.runs.record import receiver_payload

    carried = receiver_payload(prepared)["assumption_ledger"]
    assert [row["machine_key"] for row in carried] == [
        row.machine_key for row in receiver.assumption_ledger
    ]
    # And no compiler row of A-RECV.
    assert "receiver_artifact_accepted" not in prepared.compilation.assumption_ledger


def test_a_run_without_the_attestation_keeps_the_row(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The run tier's word withheld: the row is emitted, with its supplier."""
    prepared = _prepare(
        monkeypatch, attest_receiver_provenance=lambda artifact, rows: None
    )
    reduction = prepared.reduction_artifact
    assert reduction.receiver_row_omitted_on_provenance == ()
    (recv,) = [e for e in reduction.assumption_ledger if e.assumption_id == "A-RECV"]
    assert recv.inherited_from == prepared.receiver_artifact.mathematical_spec_version
    assert recv.inherited
    assert "receiver_artifact_accepted" not in prepared.compilation.assumption_ledger


def test_a_run_with_floating_point_weights_keeps_the_row(
    floating_point_weights: None,
) -> None:
    prepared = _prepare()
    assert prepared.receiver_artifact.bound_evaluation == "floating_point"
    reduction = prepared.reduction_artifact
    assert reduction.receiver_row_omitted_on_provenance == ()
    assert "A-RECV" in _ledger_ids(reduction)


def test_an_artefact_cannot_name_an_omission_and_carry_the_row() -> None:
    prepared = _prepare()
    reduction = prepared.reduction_artifact
    with_row = _prepare_with_row()
    with pytest.raises(MalformedInputError, match="carries that row"):
        replace(
            with_row,
            receiver_row_omitted_on_provenance=(
                prepared.receiver_artifact.mathematical_spec_version,
            ),
        )
    assert reduction.receiver_row_omitted_on_provenance


def _prepare_with_row() -> ProofReductionArtifact:
    patch = pytest.MonkeyPatch()
    try:
        prepared = _prepare(
            patch, attest_receiver_provenance=lambda artifact, rows: None
        )
    finally:
        patch.undo()
    reduction: ProofReductionArtifact = prepared.reduction_artifact
    assert "A-RECV" in _ledger_ids(reduction)
    return reduction


# ---------------------------------------------------------------------------
#  The run's roots: the requirement named only where every station omitted it
# ---------------------------------------------------------------------------


def test_a_run_whose_stations_differ_keeps_a_recv_a_premise() -> None:
    """One station's row omitted, the other's emitted: A-RECV is the run's premise.

    The requirement is named among the reductions roots only where every
    reductions artefact of the run omitted its row; here the second station's
    emitted row makes A-RECV a premise of the run, engaged, with no discharge
    and no discrepancy, and both stations' roots stay those of a supplied
    receiver artefact.
    """
    from types import SimpleNamespace

    from tests.support.route_fixtures import route_result

    from certiqs_key.reductions.artifact import AssumptionLedgerEntry
    from certiqs_key.runs.assumptions import (
        emitted_rows,
        route_exact_assumptions,
        run_claim_roots,
    )

    result = route_result("untrusted-two-station")
    first, second = result.device_artifacts
    reduction = second.reduction
    (version,) = reduction.receiver_row_omitted_on_provenance
    row = AssumptionLedgerEntry(
        assumption_id="A-RECV",
        machine_key="receiver_artifact_accepted",
        never_verifiable=True,
        inherited=tuple(r.machine_key for r in second.receiver.assumption_ledger),
        inherited_from=version,
    )
    kept = replace(
        reduction,
        receiver_row_omitted_on_provenance=(),
        assumption_ledger=(*reduction.assumption_ledger, row),
    )
    mixed = SimpleNamespace(
        **{**vars(result), "device_artifacts": (first, replace(second, reduction=kept))}
    )
    roots = run_claim_roots(mixed)  # type: ignore[arg-type]
    assert "reductions/req:recv-row-provenance" not in roots["reductions"]
    assert roots["reductions"] == ("reductions/wpfss/cor:emitted-flat",)
    found = route_exact_assumptions(roots, emitted_rows(mixed))  # type: ignore[arg-type]
    entries = {entry.short_id: entry for entry in found.entries}
    assert [emitter[:2] for emitter in entries["A-RECV"].emitted_by] == [
        ("reductions", 1)
    ]
    assert "A-RECV" not in {item.short_id for item in found.not_engaged}
    assert found.discrepancies == ()
