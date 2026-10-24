"""Premises emitted only where they are non-trivial.

WHY THIS EXISTS. An emitter asking "could this premise be needed in some mode"
rather than "is it non-trivial on this run" would emit A-ENS on an untrusted
source, A-ALICE-MEAS at one letter, A-PROBE and A-TSM at a station with no
private setting. Each row's emission rule is stated on the run's roles
(transmitter, protocol-compiler and reductions ``interface.yaml``,
``assumption_ledger``), and these tests would fail were any rule false on the
real routes, emitter by emitter:

* A-ENS: absent from BBM92's transmitter ledger (untrusted), present on BB84's;
* A-ALICE-MEAS: absent on BBM92 (untrusted at one letter, ``{M_x}`` the
  identity);
* A-PROBE: absent at both BBM92 stations (``T = {off}``), present at a
  probe station with two settings or more (the truth table below);
* A-TSM: absent at BBM92's Bob station (no setting, no public choice),
  present at Alice's (the test coin is applied there);
* the station bindings of A-MEAS, A-ROUND-SQ and A-SEQ name the station's
  party.

A-LINK's per-factor discharge is ``tests/unit/test_protocol_link_row_provenance.py``.
No solve.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from tests.support.route_fixtures import preparation, route_result

from certiqs_key.protocol_compiler.reasons import (
    ASSUMPTION_MACHINE_KEYS as COMPILER_KEYS,
)
from certiqs_key.protocol_compiler.reasons import AssumptionId as CompilerId
from certiqs_key.reductions.emit import emitted_assumption_rows
from certiqs_key.runs.assumptions import (
    emitted_rows,
    route_exact_assumptions,
    run_claim_roots,
)
from certiqs_key.transmitter.reasons import SourceMode

pytestmark = pytest.mark.contract

A_ENS = "source_ensemble"
A_ALICE_MEAS = COMPILER_KEYS[CompilerId.A_ALICE_MEAS]


def _station_rows(route: str) -> list[dict[str, dict[str, object]]]:
    """Return each station's reductions rows: ``{short id: {name: value}}``."""
    prepared, _ = preparation(route)
    artifacts = (
        [emission.reduction for emission in prepared.device_artifacts]
        or [prepared.reduction_artifact]
    )
    return [
        {
            entry.assumption_id: dict(entry.constrains)
            for entry in artifact.assumption_ledger
        }
        for artifact in artifacts
    ]


def test_a_ens_only_in_trusted_source_mode() -> None:
    """Transmitter ``emission_rule`` ``trusted_mode_matrix_declared_ensemble``."""
    bbm92 = preparation("untrusted-two-station")[0].specification.source.artifact
    assert bbm92.source_mode is SourceMode.UNTRUSTED
    assert A_ENS not in bbm92.assumption_ledger
    bb84 = preparation("band-a")[0].specification.source.artifact
    assert bb84.source_mode is SourceMode.TRUSTED
    assert A_ENS in bb84.assumption_ledger


def test_an_untrusted_run_names_no_fact_sr_and_lists_a_ens_not_engaged() -> None:
    """``fact:sr`` is a transmitter root in trusted mode only."""
    result = route_result("untrusted-two-station")
    roots = run_claim_roots(result)
    assert roots["transmitter"] == ("transmitter/thm:certificate-sufficiency",)
    assert "transmitter/fact:sr" in run_claim_roots(route_result("band-a"))[
        "transmitter"
    ]
    found = route_exact_assumptions(roots, emitted_rows(result))
    assert "A-ENS" not in {entry.short_id for entry in found.entries}
    assert "A-ENS" not in {item.short_id for item in found.discrepancies}


def test_a_alice_meas_absent_at_one_letter() -> None:
    """protocol-compiler ``emission_rule``: untrusted (or d_A = 1) AND |X| >= 2."""
    prepared = preparation("untrusted-two-station")[0]
    assert len(prepared.specification.source.alphabet) == 1
    assert A_ALICE_MEAS not in prepared.compilation.assumption_ledger


def test_bbm92_stations_carry_no_a_probe_and_a_tsm_only_where_the_coin_is() -> None:
    """Reductions ``emission_rule``: A-PROBE at |T| >= 2; A-TSM also at a choice."""
    prepared = preparation("untrusted-two-station")[0]
    alice, bob = _station_rows("untrusted-two-station")
    parts = prepared.specification.receiver_parts
    assert [part.factor_label for part in parts] == ["alice_station", "bob_station"]
    assert parts[0].choice_weighting is not None and parts[1].choice_weighting is None
    assert "A-PROBE" not in alice and "A-PROBE" not in bob
    assert "A-TSM" in alice
    assert "A-TSM" not in bob
    assert "A-MEAS" in alice and "A-MEAS" in bob


def test_the_station_bindings_name_the_station_s_party() -> None:
    """The A-MEAS, A-ROUND-SQ and A-SEQ bindings name the party, not a role."""
    alice, bob = _station_rows("untrusted-two-station")
    assert "Alice's device enters through one POVM" in alice["A-MEAS"]
    assert "Bob's device enters through one POVM" in bob["A-MEAS"]
    assert "Alice's physical POVM" in alice["A-ROUND-SQ"]
    assert "Bob's physical POVM" in bob["A-ROUND-SQ"]
    assert alice["A-SEQ"]["measured system"] == "the systems Alice's station measures"
    assert bob["A-SEQ"]["measured system"] == "the systems Bob's station measures"
    for rows in (alice, bob):
        assert not any("measuring party" in name for row in rows.values()
                       for name in row)


def test_a_device_that_says_no_choice_falsely_is_refused() -> None:
    """The run holds a device's "no public choice" to the specification it built."""
    from certiqs_key.runs.errors import SliceAssemblyError
    from certiqs_key.runs.pipeline import _check_public_choice_told

    specification = preparation("untrusted-two-station")[0].specification

    class _Device:
        """The two fields of DeviceRequests the check reads."""

        def __init__(self, factor: str, told: bool | None) -> None:
            self.public_choice_at_station = told
            self.station = type("S", (), {"factor": factor})()

    _check_public_choice_told(
        specification,
        [_Device("alice_station", True), _Device("bob_station", False)],  # type: ignore[list-item]
    )
    with pytest.raises(SliceAssemblyError, match="no public choice"):
        _check_public_choice_told(
            specification,
            [_Device("alice_station", False), _Device("bob_station", False)],  # type: ignore[list-item]
        )


# ===========================================================================
#  Repeated labels, probe and coin rules
# ===========================================================================


@pytest.mark.parametrize(
    ("settings", "told", "probe", "tsm"),
    [
        (("*",), None, False, True),  # not told: A-TSM stays (the safe default)
        (("*",), True, False, True),  # a public choice at the station
        (("*",), False, False, False),  # told no choice, one setting: both vacuous
        (("off", "on"), False, True, True),  # a private setting: both, whatever told
        (None, False, True, True),  # settings not given: both kept
    ],
)
def test_a_probe_and_a_tsm_presence_truth_table(
    settings: tuple[str, ...] | None, told: bool | None, probe: bool, tsm: bool
) -> None:
    """req:assumption-ledger: A-PROBE at |T| >= 2; A-TSM also at a choice or untold."""
    rows = emitted_assumption_rows(
        SimpleNamespace(source_segment=()),  # type: ignore[arg-type]
        emits_constraints=False,
        settings=settings,
        public_choice_applied=told,
    )
    ids = {str(row.identifier) for row in rows}
    assert ("A-PROBE" in ids) is probe
    assert ("A-TSM" in ids) is tsm
    assert "A-MEAS" in ids


def test_a_choice_weighted_family_at_a_station_told_no_choice_is_refused() -> None:
    """Both forms of a station's public choice are held against a told "no"."""
    from certiqs_key.protocol_compiler import PublicChoices
    from certiqs_key.runs.errors import SliceAssemblyError
    from certiqs_key.runs.pipeline import _check_public_choice_told

    chosen = preparation("wpfss-encoded")[0].specification.source.alice_choices
    assert isinstance(chosen, PublicChoices)
    spec = SimpleNamespace(receiver_parts=(
        SimpleNamespace(factor_label=None, choice_weighting=None, physical_povm=chosen),
    ))
    single = SimpleNamespace(public_choice_at_station=False, station=None)
    with pytest.raises(SliceAssemblyError, match="no public choice"):
        _check_public_choice_told(spec, [single])  # type: ignore[arg-type,list-item]
    stray = SimpleNamespace(
        public_choice_at_station=False, station=SimpleNamespace(factor="nowhere")
    )
    with pytest.raises(SliceAssemblyError, match="no public choice"):
        _check_public_choice_told(spec, [stray])  # type: ignore[arg-type,list-item]
    # Not told is never refused: the reduction kept A-TSM.
    _check_public_choice_told(
        spec,  # type: ignore[arg-type]
        [SimpleNamespace(public_choice_at_station=None, station=None)],  # type: ignore[list-item]
    )


def test_a_repeated_factor_label_is_checked_at_each_of_its_factors() -> None:
    """A weighting on an earlier factor sharing a label is not missed."""
    from certiqs_key.runs.errors import SliceAssemblyError
    from certiqs_key.runs.pipeline import _check_public_choice_told

    weighted = SimpleNamespace(
        factor_label="twin", choice_weighting=object(), physical_povm=None
    )
    plain = SimpleNamespace(
        factor_label="twin", choice_weighting=None, physical_povm=None
    )
    spec = SimpleNamespace(receiver_parts=(weighted, plain))
    station = SimpleNamespace(
        public_choice_at_station=False, station=SimpleNamespace(factor="twin")
    )
    with pytest.raises(SliceAssemblyError, match="no public choice"):
        _check_public_choice_told(spec, [station])  # type: ignore[arg-type,list-item]


def test_the_manifest_refuses_engine_bindings_that_miss_a_ledger_row() -> None:
    """Engine rows are read off the bindings, which must cover the ledger."""
    from certiqs_key.runs.errors import RunError

    result = route_result("band-a")
    key_rate = result.key_rate
    short = SimpleNamespace(
        **{**vars(key_rate), "assumption_bindings": key_rate.assumption_bindings[:-1]}
    )
    broken = SimpleNamespace(**{**vars(result), "key_rate": short})
    with pytest.raises(RunError, match="row for row"):
        emitted_rows(broken)  # type: ignore[arg-type]
