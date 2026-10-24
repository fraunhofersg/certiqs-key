"""The snap run parameters, from configuration to snap and request.

Two run parameters bear on a measurement snap
(``foundations/req:snap-reference`` (i), (iv)):

* ``reference_enclosure`` (default on) -- whether enclosed references are
  handed beside the snap;
* ``strict_snaps`` (default off) -- refuse rather than disclose a
  block that would rest on A-SNAP.

What is held here: their defaults and domains, their place in the payload,
the digest and the record, that every instance's runner hands them to its
snap and to the reduction request, the reductions ledger's A-SNAP row under
its presence rule, and that the manifest lists A-SNAP from the closure of the
reductions device roots: engaged, among the user's premises, exactly where
the record names a resting block, and not engaged elsewhere, with no
ledger/closure disagreement either way.
"""

from __future__ import annotations

import importlib
from types import SimpleNamespace

import pytest

from certiqs_key.domain.claim_closure import (
    DEVICE_ROOTS,
    assumption_info,
    claim_closure,
)
from certiqs_key.foundations.snap import SnapSettings
from certiqs_key.reductions.emit import _snap_resting, emitted_assumption_rows
from certiqs_key.reductions.inputs import InstanceSnapBlock, InstanceSnapRecord
from certiqs_key.reductions.reasons import (
    ASSUMED_FROM_FOUNDATIONS,
    PRESENT_ONLY_WHERE_A_BLOCK_RESTS_ON_A_SNAP,
)
from certiqs_key.runs.assumptions import (
    LEDGER_VOCABULARIES,
    DiscrepancyKind,
    EmittedRow,
    Section,
    route_exact_assumptions,
)
from certiqs_key.runs.config import RunConfig, RunConfigError, parameters_payload
from certiqs_key.runs.errors import RunInputReason

pytestmark = pytest.mark.contract

#: Each instance whose receiver the instance snaps, with its surface module.
SURFACES: dict[str, str] = {
    "optical_bb84": "instances.optical_bb84.surface",
    "decoy_bb84": "instances.decoy_bb84.surface",
    "bbm92": "instances.bbm92.surface",
}


def _default() -> RunConfig:
    from instances.optical_bb84.surface import default_config

    config: RunConfig = default_config()
    return config


# ---------------------------------------------------------------------------
#  Defaults, domains, payload, digest, record
# ---------------------------------------------------------------------------


def test_the_defaults_are_the_decided_ones() -> None:
    """Enclosure on, not strict; the retired parameters are absent."""
    config = _default()
    assert config.reference_enclosure is True
    assert config.strict_snaps is False
    assert not hasattr(config, "certify_snaps")
    assert not hasattr(config, "certified_weight_ceiling")


def test_the_payload_writes_a_choice_and_the_record_writes_both() -> None:
    """The house rule of A-AUTH's two: a default keeps the digest it had.

    The configuration's payload (and so its digest) carries a parameter where
    it is not its default; the record's ``parameters`` block carries both.
    The strict option needs no other option.
    """
    config = _default()
    assert not {"reference_enclosure", "strict_snaps"} & set(
        config.to_payload()["parameters"]
    )
    record = parameters_payload(config, defaults=True)
    assert record["reference_enclosure"] is True
    assert record["strict_snaps"] is False
    assert not {"certify_snaps", "certified_weight_ceiling"} & set(record)
    for change in ({"reference_enclosure": False}, {"strict_snaps": True}):
        chosen = config.with_(**change)
        assert chosen.digest() != config.digest(), change
        assert RunConfig.from_payload(chosen.to_payload()) == chosen
        (name, value) = next(iter(change.items()))
        assert chosen.to_payload()["parameters"][name] == value


@pytest.mark.parametrize(
    "change",
    [{"reference_enclosure": 1}, {"strict_snaps": "yes"}],
)
def test_a_setting_outside_its_domain_is_refused_with_its_reason(
    change: dict[str, object],
) -> None:
    from instances.optical_bb84.surface import default_config

    with pytest.raises(RunConfigError) as refusal:
        default_config(**change)
    assert refusal.value.reason is RunInputReason.SNAP_SETTING_OUT_OF_DOMAIN


def test_a_retired_parameter_is_refused() -> None:
    """The retired parameters are no inputs any more.

    ``certify_snaps`` and ``certified_weight_ceiling`` belong to a
    certification of snaps that does not exist: a configuration naming either
    is malformed.
    """
    from instances.optical_bb84.surface import default_config

    for name, value in (
        ("certify_snaps", True),
        ("certified_weight_ceiling", 0.5),
        ("strict_certification", True),
    ):
        with pytest.raises((TypeError, KeyError, ValueError)):
            default_config(**{name: value})


@pytest.mark.parametrize(
    ("name", "value", "replacement"),
    [
        ("certify_snaps", True, None),
        ("certified_weight_ceiling", "1/1024", None),
        ("strict_certification", True, "strict_snaps"),
    ],
)
@pytest.mark.parametrize("where", ["parameters", "top level"])
def test_a_payload_naming_a_retired_parameter_is_refused_with_its_code(
    name: str, value: object, replacement: str | None, where: str
) -> None:
    """Refused, never ignored.

    A payload that carries ``certify_snaps`` or ``certified_weight_ceiling``,
    or the strict option under its retired name ``strict_certification``,
    would otherwise run on the default path. It is refused with
    ``retired_parameter``, naming the key and, for a renamed one, its new name
    (no backward compatibility).
    """
    payload = _default().to_payload()
    if where == "parameters":
        payload["parameters"] = {**payload["parameters"], name: value}
    else:
        payload[name] = value
    with pytest.raises(RunConfigError) as refusal:
        RunConfig.from_payload(payload)
    assert refusal.value.reason is RunInputReason.RETIRED_PARAMETER
    assert name in str(refusal.value)
    if replacement is not None:
        assert replacement in str(refusal.value)


# ---------------------------------------------------------------------------
#  Every runner hands them on
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("instance", sorted(SURFACES))
def test_every_instance_hands_the_settings_to_its_snap_and_its_request(
    instance: str,
) -> None:
    """A non-default choice reaches the instance's snap record and the reduction.

    Through each instance's own ``preparation`` (the runner's reader, without
    a solve): the snap record of every station names the two settings, and
    every station's reduction artefact echoes the strict option and the
    enclosure setting in its emission record. Strict passes the preparation
    of every shipped default: every moved block there is handed its
    reference, and a reference companion is formed beside every artefact, so
    whether anything rests is the run's to decide after its search.
    """
    surface = importlib.import_module(SURFACES[instance])
    base: RunConfig = surface.default_config()
    config = base.with_(strict_snaps=True)
    outcome = surface.preparation(config)
    assert not outcome.refuses, getattr(outcome, "detail", outcome)
    adaptation = outcome.rows_adaptation
    assert adaptation is not None
    stations = adaptation.get("stations") or [adaptation]
    expected = SnapSettings(strict=True).as_record()
    for station in stations:
        assert station["snap_settings"] == expected
        for snap in station["measurement_snaps"]:
            assert snap["run_settings"] == expected
    reductions = (
        [outcome.reduction_artifact]
        if outcome.reduction_artifact is not None
        else [emission.reduction for emission in outcome.device_artifacts]
    )
    assert reductions
    for artifact in reductions:
        record = artifact.emission_record
        assert record.strict_snaps is True
        assert record.enclosed_references_used is True


@pytest.mark.parametrize("instance", sorted(SURFACES))
def test_every_instance_hands_the_enclosure_setting_on(instance: str) -> None:
    """``reference_enclosure = False`` reaches every snap and every request.

    ``reductions/req:emission-record``: the emission record echoes whether
    enclosed references were used. Off the default, every station's snap record
    names the setting and every reduction artefact's emission record says
    ``enclosed_references_used`` is false. Not strict, so a block whose
    enclosure is not handed is disclosed and the preparation completes.
    """
    surface = importlib.import_module(SURFACES[instance])
    base: RunConfig = surface.default_config()
    config = base.with_(reference_enclosure=False)
    outcome = surface.preparation(config)
    assert not outcome.refuses, getattr(outcome, "detail", outcome)
    adaptation = outcome.rows_adaptation
    assert adaptation is not None
    stations = adaptation.get("stations") or [adaptation]
    expected = SnapSettings(reference_enclosure=False).as_record()
    for station in stations:
        assert station["snap_settings"] == expected
        for snap in station["measurement_snaps"]:
            assert snap["run_settings"] == expected
            for block in snap["blocks"]:
                assert block["handed_reference_kind"] in (None, "exact")
    reductions = (
        [outcome.reduction_artifact]
        if outcome.reduction_artifact is not None
        else [emission.reduction for emission in outcome.device_artifacts]
    )
    assert reductions
    for artifact in reductions:
        assert artifact.emission_record.enclosed_references_used is False


# ---------------------------------------------------------------------------
#  The reductions ledger's A-SNAP row, under its presence rule
# ---------------------------------------------------------------------------


def test_a_snap_is_the_one_row_assumed_from_foundations() -> None:
    assert set(ASSUMED_FROM_FOUNDATIONS) == {"A-SNAP"}
    assert set(PRESENT_ONLY_WHERE_A_BLOCK_RESTS_ON_A_SNAP) == {"A-SNAP"}


def test_the_a_snap_row_is_present_exactly_where_a_block_rests() -> None:
    """``req:emission-record``: "exactly where there is one" resting block."""
    chain = SimpleNamespace(source_segment=())
    without = {row.identifier for row in emitted_assumption_rows(chain)}  # type: ignore[arg-type]
    with_ = {
        row.identifier
        for row in emitted_assumption_rows(chain, rests_on_a_snap=True)  # type: ignore[arg-type]
    }
    assert "A-SNAP" not in without
    assert with_ - without == {"A-SNAP"}


def test_the_moved_blocks_are_read_off_both_records_once() -> None:
    """``thm:emit`` (vi): the artefact names what moved, provisionally.

    Its moved sectors and the declaring party's moved blocks; a kept block is
    named by neither.
    """
    emission = SimpleNamespace(moved_sectors=((1, "class 'y' moved by snap"),))
    snap = InstanceSnapRecord(
        blocks=(
            InstanceSnapBlock(block=2, setting="off", status="moved", handed=True),
            InstanceSnapBlock(
                block=3, setting="off", status="moved", cause="enclosure_not_used"
            ),
            InstanceSnapBlock(block=0, setting="off", status="kept", handed=True),
        )
    )
    names = _snap_resting(emission, snap)  # type: ignore[arg-type]
    assert names == (
        "emission: data sector 1 (class 'y' moved by snap)",
        "instance_snap: m=2, t=off (reference handed)",
        "instance_snap: m=3, t=off (enclosure_not_used)",
    )
    clean = SimpleNamespace(moved_sectors=())
    assert _snap_resting(clean, None) == ()  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
#  The manifest lists A-SNAP from the closure, engaged only where a block rests
# ---------------------------------------------------------------------------


def test_a_snap_is_in_the_closure_of_every_reductions_emission_root() -> None:
    """``reductions/thm:emit`` (vi) assumes A-SNAP.

    Every emission result a run's reductions roots name reaches it;
    ``thm:licence``, added beside an emission root when an attack-set licence
    is carried, is about the licence and does not, nor does
    ``req:recv-row-provenance``, added beside the supplied artefact's emission
    root where the A-RECV row is omitted, which is about the receiver's
    theorems.
    """
    beside = {"reductions/thm:licence", "reductions/req:recv-row-provenance"}
    emission = [root for root in DEVICE_ROOTS["reductions"] if root not in beside]
    assert "reductions/thm:emit" in emission
    for root in emission:
        assert "A-SNAP" in claim_closure(root)["assumptions"], root
    assert "A-SNAP" in LEDGER_VOCABULARIES["reductions"]


def test_a_snap_is_a_user_premise_not_an_engine_numeric() -> None:
    """Its category is ``receiver``: a premise about the user's device."""
    assert assumption_info("A-SNAP")["category"] == "receiver"


def test_a_disclosed_run_lists_a_snap_engaged_with_no_discrepancy() -> None:
    rows = [
        EmittedRow(
            machine_key="snapped_measurement",
            emitted_by="reductions",
            short_id="A-SNAP",
            bindings=(("resting_blocks", ("instance_snap: m=2, t=off (x)",)),),
        )
    ]
    found = route_exact_assumptions({"reductions": ("reductions/thm:emit",)}, rows)
    assert [entry.short_id for entry in found.entries] == ["A-SNAP"]
    assert found.entries[0].section is Section.ASSUMPTIONS
    assert found.discrepancies == ()
    assert "A-SNAP" not in {item.short_id for item in found.not_engaged}


def test_a_run_with_every_block_kept_lists_a_snap_as_not_engaged() -> None:
    """No A-SNAP row: in the closure, not engaged, and no disagreement.

    The presence rule decides engagement, as for A-SRC.
    """
    found = route_exact_assumptions({"reductions": ("reductions/thm:emit",)}, [])
    assert "A-SNAP" not in {entry.short_id for entry in found.entries}
    assert [
        (item.short_id, item.module)
        for item in found.not_engaged
        if item.short_id == "A-SNAP"
    ] == [("A-SNAP", "reductions")]
    assert "A-SNAP" not in {item.short_id for item in found.discrepancies}
    assert found.kinds(DiscrepancyKind.IN_CLOSURE_NO_EMITTER) == ()
