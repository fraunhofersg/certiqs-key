"""Requested entries on a decided certificate, and the licence that names it.

``reductions/cor:entries`` (i)-(iii), ``reductions/req:uncertified-operator-refused``
and ``reductions/req:licence-record``, with the flat instance's decided
certificate ``reductions/wpfss/cor:two-sector-decided``: a requested operator
is emitted only where a claim stated for the instance gives a condition on the
emitted numbers that implies its certificate and the engine decides it; every
other one is refused ``constraint_without_certificate``; and the licence names,
per entry, the claim that discharges it and the supplier artefact where that
claim reads one. The cases run the noisy optical BB84 device's reduction, no
solve; a removable submodule's builder has its cases in that submodule's own
test file.
"""

from __future__ import annotations

import importlib
import inspect
import pkgutil
from dataclasses import replace
from fractions import Fraction as F
from pathlib import Path

import pytest
import yaml

from certiqs_key.foundations.exact import (
    Matrix,
    add,
    direct_sum,
    matrix,
    scale,
    subtract,
)
from certiqs_key.reductions.artifact import ProofReductionArtifact
from certiqs_key.reductions.companion import ReferenceCompanion
from certiqs_key.reductions.constraints import (
    CERTIFICATE_LOCATORS,
    RECEIVER_FACT,
    TWO_SECTOR_DECIDED_CLAIM,
    WRITING_DEFAULT_CARRIED,
)
from certiqs_key.reductions.emit import reduce
from certiqs_key.reductions.inputs import CarriedOperatorRequest, ReductionCall
from certiqs_key.reductions.reasons import CertificateKind, Relation
from certiqs_key.reductions.wpfss.api import FlatInstanceBuilder
from certiqs_key.reductions.wpfss.construction import (
    FSS_INSTANCE_LOCATOR,
    transported_cutoff_projectors,
)

pytestmark = pytest.mark.contract

ROOT = Path(__file__).resolve().parents[2]

REFUSED = "constraint_without_certificate"


def _optical_call(route: str = "licensed") -> ReductionCall:
    """Return the noisy optical device's reduction call (N = 2), on a route."""
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
    return ReductionCall(
        adapted.rows, device.reduction_declaration, device.reduction_request
    )


def _asking(call: ReductionCall, *requested: CarriedOperatorRequest) -> ReductionCall:
    return replace(call, request=replace(call.request, carried_operators=requested))


def _flat(call: ReductionCall) -> ProofReductionArtifact:
    artifact = reduce(call, FlatInstanceBuilder()).artifact
    assert artifact is not None
    return artifact


def _cutoff_projectors(artifact: ProofReductionArtifact) -> tuple[Matrix, Matrix]:
    preserved = artifact.source_descriptor.channel_grading.preserved_dimension
    return transported_cutoff_projectors(preserved, len(artifact.target_povm))


def _request(
    label: str,
    operator: Matrix,
    artifact: ProofReductionArtifact,
    *,
    relation: Relation = Relation.GE,
    constant: F = F(0),
) -> CarriedOperatorRequest:
    return CarriedOperatorRequest(
        label=label,
        operator=operator,
        relation=relation,
        constant=constant,
        certificate_kind=CertificateKind.POSITIVITY,
        certified_against=artifact.squashing_channel.identity,
    )


def _two_sector(
    artifact: ProofReductionArtifact, below: F, above_extra: F = F(0)
) -> CarriedOperatorRequest:
    """``F^FSS_e - a Pi_{<=N} - b Pi_Flag`` from the first baseline entry.

    The baseline entry is ``F^FSS_e - p_e Pi_Flag``, so this is the two-sector
    entry at ``a = below`` and ``b = p_e + above_extra``.
    """
    baseline = artifact.constraint_list[0]
    pi_leq, pi_flag = _cutoff_projectors(artifact)
    operator = subtract(
        subtract(direct_sum(list(baseline.operator)), scale(below, pi_leq)),
        scale(above_extra, pi_flag),
    )
    return _request(f"{baseline.label} - {below} Pi_leq", operator, artifact)


def _two_sector_provided(call: ReductionCall) -> tuple[CarriedOperatorRequest, ...]:
    from instances.common.passive_device import two_sector_provider

    requested = two_sector_provider()(_flat(call))
    assert requested, "the noisy device asks for no two-sector entry"
    return requested


# --------------------------------------------------------------------------
# wpfss/cor:two-sector-decided: decided on the emitted numbers, both ways
# --------------------------------------------------------------------------


def test_the_two_sector_entry_is_emitted_where_its_decided_certificate_holds() -> None:
    """cor:two-sector-decided (ii)-(iii): the run tier's request passes, named."""
    call = _optical_call()
    requested = _two_sector_provided(call)
    outcome = reduce(_asking(call, *requested), FlatInstanceBuilder())
    assert outcome.artifact is not None, outcome.refusal
    labels = {entry.label for entry in outcome.artifact.constraint_list}
    assert {item.label for item in requested} <= labels


def test_a_two_sector_entry_whose_a_exceeds_a_least_eigenvalue_is_refused() -> None:
    """The first condition of eq:two-sector-condition fails: refused, and says so.

    At ``a = 1/2`` no below-cutoff multi-click block of the noisy device clears
    ``a`` (its least eigenvalue is of the order of the dark count), and
    cor:two-sector-decided (iii) shows the condition necessary.
    """
    call = _optical_call()
    artifact = _flat(call)
    outcome = reduce(
        _asking(call, _two_sector(artifact, F(1, 2))), FlatInstanceBuilder()
    )
    assert outcome.artifact is None
    assert outcome.refusal is not None
    assert str(outcome.refusal.reason) == REFUSED
    assert "does not clear a = 1/2" in outcome.refusal.detail
    assert "cor:two-sector-decided" in outcome.refusal.detail


def test_a_two_sector_entry_whose_b_exceeds_the_certified_weight_is_refused() -> None:
    """The second condition, ``b <= p_e``, fails: refused, naming the weight."""
    call = _optical_call()
    artifact = _flat(call)
    outcome = reduce(
        _asking(call, _two_sector(artifact, F(0), above_extra=F(1, 2**40))),
        FlatInstanceBuilder(),
    )
    assert outcome.artifact is None
    assert outcome.refusal is not None
    assert str(outcome.refusal.reason) == REFUSED
    assert "exceeds the certified weight" in outcome.refusal.detail


def test_an_operator_no_claim_gives_a_decided_certificate_for_is_refused() -> None:
    """req:uncertified-operator-refused: of the form, but no decided certificate.

    ``Pi_Flag`` at ``>= 1/2`` is a combination of sector projectors and so of
    the form eq:instance-entry, its pull-back is not ``>= 1/2`` in general, and
    no claim gives a decided certificate for it: refused, whatever the request's
    own certificate case says, and never emitted at another constant.
    """
    call = _optical_call()
    artifact = _flat(call)
    _, pi_flag = _cutoff_projectors(artifact)
    asked = _request("Pi_flag >= 1/2", pi_flag, artifact, constant=F(1, 2))
    outcome = reduce(_asking(call, asked), FlatInstanceBuilder())
    assert outcome.artifact is None
    assert outcome.refusal is not None
    assert str(outcome.refusal.reason) == REFUSED
    assert "no claim stated for this instance gives a decided certificate" in (
        outcome.refusal.detail
    )


# --------------------------------------------------------------------------
# cor:entries (i): a default carried operator requested as an entry
# --------------------------------------------------------------------------


def test_a_default_carried_operator_is_emitted_as_an_entry_on_request() -> None:
    """cor:entries (i): ``(Pi, >=, 0)`` for a transported sum of sector projectors.

    Emitted with the positivity certificate, the licence present, its
    discharge ``cor:entries`` (i) with NO supplier fact (the positivity of the
    adjoint reads none), and the companion carries it as it is, radius zero
    (cor:reference-companion (vi); req:reference-companion (iii)).
    """
    call = _optical_call()
    artifact = _flat(call)
    pi_leq, pi_flag = _cutoff_projectors(artifact)
    asked = (
        _request("Pi_leq as an entry", pi_leq, artifact),
        _request("Pi_flag as an entry", pi_flag, artifact),
    )
    outcome = reduce(_asking(call, *asked), FlatInstanceBuilder())
    emitted = outcome.artifact
    assert emitted is not None, outcome.refusal
    by_label = {entry.label: entry for entry in emitted.constraint_list}
    for item in asked:
        entry = by_label[item.label]
        assert entry.relation is Relation.GE and entry.constant == 0
        assert entry.certificate_kind is CertificateKind.POSITIVITY
    licence = emitted.attack_set_license
    assert licence is not None
    discharges = {item.entry: item for item in licence.discharge_per_entry}
    for item in asked:
        discharge = discharges[item.label]
        assert discharge.claim.startswith(CERTIFICATE_LOCATORS[WRITING_DEFAULT_CARRIED])
        assert discharge.supplier_fact is None and discharge.supplier_version is None
    companion = emitted.reference_companion
    assert isinstance(companion, ReferenceCompanion)
    formed = {entry.label: entry for entry in companion.requested_entries_formed}
    for item in asked:
        assert formed[item.label].writing == WRITING_DEFAULT_CARRIED
        assert formed[item.label].established_by == (
            "reductions/cor:reference-companion (vi)"
        )
        (relaxed,) = [e for e in companion.entries if e.relaxes == item.label]
        assert relaxed.delta == 0 and relaxed.entry == by_label[item.label]


def test_a_sector_projector_entry_is_emitted_and_an_untransported_sum_refused() -> None:
    """wpfss/cor:emitted-flat: a default carried operator, block by block.

    One sector projector, of a data sector (``Pi_(C,0)``) and of a flag
    sector (``Pi_(C,mc)``), requested as an entry on the flat path is emitted
    at ``(>=, 0)`` with the positivity certificate: each is an operator of the
    transported set (prop:flat-instance (I3)). The identity and
    ``Pi_(C,0) + Pi_(C,1)`` are sums of sector projectors the instance does
    not transport, and are refused ``constraint_without_certificate``.
    """
    call = _optical_call()
    artifact = _flat(call)
    projectors = {
        row.label: direct_sum(list(row.target_operator))
        for row in artifact.transported_operators
    }
    asked = (
        _request("Pi_(C,0) as an entry", projectors["Pi_(C,0)"], artifact),
        _request("Pi_(C,mc) as an entry", projectors["Pi_(C,mc)"], artifact),
    )
    outcome = reduce(_asking(call, *asked), FlatInstanceBuilder())
    emitted = outcome.artifact
    assert emitted is not None, outcome.refusal
    by_label = {entry.label: entry for entry in emitted.constraint_list}
    for item in asked:
        entry = by_label[item.label]
        assert entry.relation is Relation.GE and entry.constant == 0
        assert entry.certificate_kind is CertificateKind.POSITIVITY
    pi_leq, pi_flag = _cutoff_projectors(artifact)
    untransported = (
        ("the identity", add(pi_leq, pi_flag)),
        ("Pi_(C,0) + Pi_(C,1)", add(projectors["Pi_(C,0)"], projectors["Pi_(C,1)"])),
    )
    for label, operator in untransported:
        refused = reduce(
            _asking(call, _request(label, operator, artifact)), FlatInstanceBuilder()
        )
        assert refused.artifact is None, label
        assert refused.refusal is not None, label
        assert str(refused.refusal.reason) == REFUSED, label


def test_a_projector_at_another_constant_is_not_the_default_entry() -> None:
    """cor:entries (i) emits ``(Pi, >=, 0)`` only; ``Pi <= 0`` is refused."""
    call = _optical_call()
    artifact = _flat(call)
    pi_leq, _ = _cutoff_projectors(artifact)
    asked = _request("Pi_leq <= 0", pi_leq, artifact, relation=Relation.LE)
    outcome = reduce(_asking(call, asked), FlatInstanceBuilder())
    assert outcome.artifact is None
    assert outcome.refusal is not None
    assert str(outcome.refusal.reason) == REFUSED


# --------------------------------------------------------------------------
# req:licence-record: per entry, the discharging claim
# --------------------------------------------------------------------------


def test_the_licence_names_the_discharging_claim_per_entry() -> None:
    """req:licence-record: the instance's claim, or the decided certificate's.

    The flat instance's own entries are discharged by wpfss/cor:fssinstance,
    which reads the certified weights the receiver's claims state (A-RECV, by
    the receiver artefact's version); the requested two-sector entry by
    wpfss/cor:two-sector-decided, which reads them too.
    """
    call = _optical_call()
    requested = _two_sector_provided(call)
    outcome = reduce(_asking(call, *requested), FlatInstanceBuilder())
    artifact = outcome.artifact
    assert artifact is not None, outcome.refusal
    licence = artifact.attack_set_license
    assert licence is not None
    assert [item.entry for item in licence.discharge_per_entry] == [
        entry.label for entry in artifact.constraint_list
    ]
    version = call.artifact_rows.mathematical_spec_version
    asked = {item.label for item in requested}
    for item in licence.discharge_per_entry:
        if item.entry in asked:
            assert item.claim.startswith(TWO_SECTOR_DECIDED_CLAIM.split("/", 1)[1])
        else:
            assert item.claim == FSS_INSTANCE_LOCATOR
        assert item.supplier_fact == RECEIVER_FACT
        assert item.supplier_version == version
    assert licence.receiver_spec_version == version
    record = licence.as_machine_record()
    assert record["discharge_per_entry"] == [
        item.as_machine_record() for item in licence.discharge_per_entry
    ]


# --------------------------------------------------------------------------
# req:licence-record: one label per entry, or the request is refused
# --------------------------------------------------------------------------


def _collisions(
    baseline: ProofReductionArtifact,
) -> list[tuple[str, tuple[CarriedOperatorRequest, ...]]]:
    """Return the two collisions: an own label repeated; two requests, one label.

    Both requests are certifiable on their own (a default carried operator),
    so what is refused is the label alone.
    """
    total = sum(baseline.target_descriptor.sectors.dimensions)
    first = baseline.target_descriptor.sectors.dimensions[0]
    pi_first = matrix(
        [
            [F(1) if i == j and i < first else F(0) for j in range(total)]
            for i in range(total)
        ]
    )
    own = baseline.constraint_list[0].label
    return [
        ("an entry the instance builds itself", (_request(own, pi_first, baseline),)),
        (
            "another requested entry",
            (
                _request("x", pi_first, baseline),
                _request("x", pi_first, baseline),
            ),
        ),
    ]


def test_a_requested_label_repeating_an_entry_label_is_refused_flat() -> None:
    """A label that is not the entry's own cannot key its discharge: refused."""
    call = _optical_call()
    baseline = _flat(call)
    for owner, asked in _collisions(baseline):
        outcome = reduce(_asking(call, *asked), FlatInstanceBuilder())
        assert outcome.artifact is None, owner
        assert outcome.refusal is not None
        assert str(outcome.refusal.reason) == REFUSED
        assert f"repeats the label of {owner}" in outcome.refusal.detail
        assert repr(asked[0].label) in outcome.refusal.detail
    # Each request alone, under a label of its own, is admitted.
    _, (alone,) = _collisions(baseline)[0]
    fresh = replace(alone, label="the first sector projector")
    assert reduce(_asking(call, fresh), FlatInstanceBuilder()).artifact is not None


def test_a_requested_label_repeating_an_entry_label_is_refused_on_a_factor() -> None:
    """Through reduce_factors: the factor that collides refuses the emission."""
    from tests.support.reductions_support import flat_call

    from certiqs_key.reductions.factors import FactorCall, reduce_factors

    alice_call = flat_call(party="A", route="licensed")
    baseline = _flat(alice_call)
    for owner, asked in _collisions(baseline):
        factors = [
            FactorCall(
                call=_asking(alice_call, *asked),
                builder=FlatInstanceBuilder(),
                sector_block_kind="proof_sector",
            ),
            FactorCall(
                call=flat_call(
                    party="B",
                    route="licensed",
                    letters=("z_empty", "z_1", "z_2", "z_mc"),
                ),
                builder=FlatInstanceBuilder(),
                sector_block_kind="proof_sector",
            ),
        ]
        outcome = reduce_factors(factors)
        assert outcome.emission is None, owner
        assert outcome.refusal is not None
        assert str(outcome.refusal.reason) == REFUSED
        assert f"repeats the label of {owner}" in outcome.refusal.detail


# --------------------------------------------------------------------------
# (I4): a two-sector entry off the lattice is refused at the lattice row
# --------------------------------------------------------------------------


def test_a_two_sector_entry_off_the_lattice_is_refused_before_the_licence() -> None:
    """``a = -1/3`` or ``b = p_e - 1/3``: the certificate holds, (I4) does not.

    ``eq:two-sector-condition`` holds at both (``A' >= -1/3`` and
    ``b <= p_e``), so the decided certificate admits the entry; its operator
    then carries a coefficient off the ``2^-kappa`` lattice, and the licensed
    route's lattice row (``licensed_hermiticity``,
    ``req:licensed-entry-lattice``) refuses the artefact before any licence is
    issued.
    """
    call = _optical_call()
    artifact = _flat(call)
    for asked in (
        _two_sector(artifact, F(-1, 3)),
        _two_sector(artifact, F(0), above_extra=F(-1, 3)),
    ):
        outcome = reduce(_asking(call, asked), FlatInstanceBuilder())
        assert outcome.artifact is None
        assert outcome.refusal is not None
        assert str(outcome.refusal.rule) == "licensed_hermiticity"
        assert str(outcome.refusal.reason) == REFUSED


# --------------------------------------------------------------------------
# req:reference-companion (vi): no rule of (I1) with a reciprocal is bound
# --------------------------------------------------------------------------


def test_every_builder_with_a_companion_forms_its_datum_without_a_reciprocal() -> None:
    """The third no-companion case cannot occur, and this says why.

    ``req:reference-companion`` (vi) asks for no companion where a reciprocal
    node of the rule of (I1) receives no enclosure. The engine records no such
    reason because no builder binds a rule with a reciprocal: every builder
    naming a ``companion_claim`` is the flat builder, whose rule is the
    non-negative combination of ``wpfss/cor:flat-companion``, or the builder
    of a removable branching submodule, which lifts it
    (``cor:reference-companion`` (iv)) and is checked in that submodule's own
    test file. A new builder
    with a companion fails here until its rule is examined and, if it has a
    reciprocal, the case gets its record reason
    (``certiqs_key.reductions.companion.CompanionAbsence``).
    """
    outside = {
        name for name in companion_builders() if name.split(".")[2] not in REMOVABLE
    }
    assert outside == {"certiqs_key.reductions.wpfss.api.FlatInstanceBuilder"}


#: The submodules of ``reductions`` declared removable (an ``interface.yaml``
#: with a ``removability`` block). A builder of theirs is examined in their own
#: test file, which goes with them.
REMOVABLE = frozenset(
    path.parent.name
    for path in (ROOT / "spec" / "modules" / "reductions").glob("*/interface.yaml")
    if "removability" in yaml.safe_load(path.read_text(encoding="utf-8"))
)


def companion_builders() -> set[str]:
    """Return every class of ``certiqs_key.reductions`` naming a companion claim."""
    import certiqs_key.reductions as package

    found: set[str] = set()
    for info in pkgutil.walk_packages(package.__path__, package.__name__ + "."):
        module = importlib.import_module(info.name)
        for name, value in vars(module).items():
            if (
                inspect.isclass(value)
                and value.__module__ == module.__name__
                and isinstance(getattr(value, "companion_claim", None), str)
            ):
                found.add(f"{module.__name__}.{name}")
    return found
