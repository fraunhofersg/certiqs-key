"""The direct route end to end: the bound on the reference companion, record, report.

``meat-core/frank-wolfe/req:bracket-on-reference`` with the chain that feeds it
(``reductions/req:reference-companion``,
``protocol-compiler/req:reference-companion-compiled``,
``meat-core/req:companion-admission``). The search runs on the snapped declaration;
after it, the first-order bound is formed on the reference companion at the best four
points of the search and its last, and at those of the polish, a short search continued
on the companion's own program. Where some point contributes, that bound is the run's
number, and every block on which the companion carries the handed reference is evaluated
off its snap (``foundations/def:evaluated-off-snap``) and rests on the receiver model,
not on A-SNAP.

Every case runs an instance's own runner, records the run and builds its
report. The key lengths compared are measured at :data:`KEY_ITERATIONS`, and
the snapped bound's key length is recorded beside the run's
(``reference_bracket.snapped``), so a case reads the current key from the same
record. Where the search stops short of converging (these budgets of 20 or 30
iterations), the polish moves on from its best point and the companion's key
can exceed the snapped one; it does not fall below it by more than a bit
(:func:`_not_below_snapped`).
"""

from __future__ import annotations

import json
import tempfile
from dataclasses import replace
from fractions import Fraction as F
from pathlib import Path
from typing import Any

import pytest

import certiqs_key.runs as runs_package
from certiqs_key.runs.config import RunConfig, SolverSettings
from certiqs_key.runs.record import record_run
from certiqs_key.runs.report import build_report

pytest.importorskip("qics")

PORTS = ("H", "V", "D", "A")
#: Declared at the factored loss one
#: (receiver/detector-imperfections/req:efficiency-normalization): the device
#: keeps its loss, so that its blocks are the non-dyadic ones these cases are
#: about; at its default the normalized station is lossless.
NOISY = {
    "efficiency": dict.fromkeys(PORTS, F(9, 10)),
    "dark_count": dict.fromkeys(PORTS, F(1, 10**6)),
    "efficiency_normalization": F(1),
}
#: The Frank-Wolfe budget of these cases; the snap-certification runs' budget,
#: at which the shipped default gives 1809 and the noisy device 1482.
KEY_ITERATIONS = 20


def _config(
    instance: str = "optical_bb84", iterations: int = KEY_ITERATIONS, **device: Any
) -> RunConfig:
    import importlib

    surface = importlib.import_module(f"instances.{instance}.surface")
    base: RunConfig = surface.default_config(
        solver=SolverSettings(method="fw", max_iterations=iterations)
    )
    if not device:
        return base
    return base.with_(device={**base.device, **device})


def _run(config: RunConfig, instance: str = "optical_bb84") -> dict[str, Any]:
    import importlib

    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    surface = importlib.import_module(f"instances.{instance}.surface")
    with tempfile.TemporaryDirectory() as tmp:
        outcome = surface.runner(QicsSectorChoiOracle(), Path(tmp), created_by="t")(
            config, 0
        )
        record: dict[str, Any] = record_run(outcome, config, created_by="t").as_dict()
    found: dict[str, Any] = json.loads(json.dumps(record))
    _validate(found)
    return found


def _validate(record: dict[str, Any]) -> None:
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads(
        (Path(runs_package.__file__).resolve().parent / "record.schema.json").read_text(
            encoding="utf-8"
        )
    )
    jsonschema.validate(record, schema)


def _key_rate(record: dict[str, Any]) -> dict[str, Any]:
    rate: dict[str, Any] = record["payload"]["stages"]["key_rate"]
    return rate


def _decision(record: dict[str, Any]) -> dict[str, Any]:
    decision: dict[str, Any] = record["payload"]["snaps"]["reference_companion"]
    return decision


def _engaged(record: dict[str, Any]) -> set[str]:
    manifest = record["payload"]["assumption_manifest"]
    return {entry["short_id"] for entry in manifest["assumptions"]}


def _counted(record: dict[str, Any]) -> dict[str, Any]:
    """Assert the companion's bound counted; return its record."""
    rate = _key_rate(record)
    bracket = rate["reference_bracket"]
    assert bracket["status"] == "counted" and bracket["counted"] is True
    assert bracket["reason"] is None
    assert rate["h_lb"] == bracket["h_lb_reference"]
    roots = rate["optimizer_certificate"]["claim_roots"]
    assert "meat-core/frank-wolfe/cor:fo-reference" in roots
    assert "meat-core/frank-wolfe/thm:firstorder" not in roots
    # Two sets of at most four best points and the last each, the search's
    # and the polish's (req:bracket-on-reference (i)), each point naming its
    # set; at most five certified (req:certified-evaluation (i)).
    sets = [point["set"] for point in bracket["points"]]
    assert 1 <= sets.count("search") <= 5 and sets.count("polish") <= 5
    assert set(sets) <= {"search", "polish"}
    assert sets == sorted(sets, key=["search", "polish"].index)
    certified = rate["certified"]
    assert certified is not None and len(certified["points"]) <= 5
    closure = record["payload"]["assumption_manifest"]["claim_closure"]
    for root in (
        "meat-core/frank-wolfe/cor:fo-reference",
        "reductions/cor:reference-companion",
        "reductions/wpfss/cor:flat-companion",
    ):
        assert root in closure, root
    result: dict[str, Any] = bracket
    return result


def _not_below_snapped(record: dict[str, Any], bracket: dict[str, Any]) -> None:
    """Assert the companion's key is the snapped one's or more, within one bit.

    The first set's points are where the snapped bound is formed, and the
    companion's bracket there is the snapped one within rounding; the polish
    can only add points (req:bracket-on-reference (i), (iii)).
    """
    key = _key_rate(record)["key_length"]
    snapped = bracket["snapped"]["key_length"]
    assert key >= snapped - 1, (key, snapped)


def _withdraw_every_companion_point(monkeypatch: pytest.MonkeyPatch) -> None:
    """Withdraw every point evaluated on the companion, the polish's among them."""
    from certiqs_key.solvers.frank_wolfe import reference

    first, polish = reference.assess_first_order, reference.assess_candidate

    def withdrawn(original: Any) -> Any:
        def wrapped(*args: Any, **kwargs: Any) -> Any:
            found = original(*args, **kwargs)
            gate = replace(found.gate, withdrawal="iterate_not_feasible")
            return replace(found, gate=gate)

        return wrapped

    monkeypatch.setattr(reference, "assess_first_order", withdrawn(first))
    monkeypatch.setattr(reference, "assess_candidate", withdrawn(polish))


def _no_a_snap(record: dict[str, Any]) -> None:
    """A-SNAP is not engaged, is listed as not engaged, and the report agrees."""
    assert "A-SNAP" not in _engaged(record)
    manifest = record["payload"]["assumption_manifest"]
    assert not [d for d in manifest["discrepancies"] if d["short_id"] == "A-SNAP"]
    decision = _decision(record)
    assert decision["rests_on_a_snap"] is False and decision["resting_blocks"] == []
    section = build_report(record)["sections"]["protocol"]["measurement_snaps"]
    assert section is not None
    assert section["rests_on_a_snap"] is False and section["assumption"] is None
    assert all(not row["rests_on_assumption"] for row in section["rows"])


def _all_evaluated_off(record: dict[str, Any], *, moved: bool = True) -> None:
    """Every moved block is evaluated off its snap; a kept block is named kept.

    A kept block is the model itself, so it is
    named among the decision's ``kept_blocks`` and never counted as evaluated
    off its snap (``foundations/req:who-snaps``). ``moved`` says whether the
    run has a moved block at all.
    """
    decision = _decision(record)
    kept = set()
    for snap in record["payload"]["snaps"]["instance"]["measurement_snaps"]:
        for block in snap["blocks"]:
            if block["status"] == "kept":
                assert block["evaluated_off_snap"] is False, block["block"]
                kept.add(f"{block['block']}, t={snap['setting']}")
            else:
                assert block["evaluated_off_snap"] is True, block["block"]
    assert {item["block"] for item in decision["kept_blocks"]} == kept
    assert decision["evaluated_off_snap_count"] == len(decision["evaluated_off_snap"])
    assert (decision["evaluated_off_snap_count"] > 0) is moved


def test_the_shipped_default_keeps_its_key_and_rests_on_no_snap() -> None:
    """Shipped default: 1809 snapped, every block kept, none counted as evaluated off.

    The polish continues the 20-iteration search on the companion, which here
    is the snapped declaration itself (every block kept), and raises the key
    to 1810.
    """
    record = _run(_config())
    bracket = _counted(record)
    assert bracket["snapped"]["key_length"] == 1809
    assert _key_rate(record)["key_length"] == 1810
    assert bracket["difference"] >= 0.0
    _all_evaluated_off(record, moved=False)
    _no_a_snap(record)


def test_a_noisy_device_is_evaluated_off_its_snap_by_default() -> None:
    """The noisy two-photon device: no A-SNAP, the key at least the snapped one's.

    The bound is formed on the receiver model's companion, every block is
    evaluated off its snap, and the key is the snapped bound's or more, to
    within one bit (the polish moves on where the search stopped).
    """
    record = _run(_config(photon_cutoff=F(2), exact_window=F(3), **NOISY))
    bracket = _counted(record)
    assert bracket["snapped"]["key_length"] == 1482
    _not_below_snapped(record, bracket)
    assert bracket["difference"] > -1e-9
    _all_evaluated_off(record)
    _no_a_snap(record)
    # The emission's moved data sectors would be evaluated off too (the
    # companion bypasses the normaliser); here the normaliser keeps every
    # class (the snapped declaration is on the lattice), and a sector with no
    # moved class is not counted as evaluated off (record 0.28.0).
    moved = []
    for block in record["payload"]["snaps"]["producer"]["blocks"]:
        here = any(item["status"] == "moved" for item in block["classes"])
        assert block["evaluated_off_snap"] is here, block["block_index"]
        moved += [block["block_index"]] if here else []
    assert [
        sector
        for item in _decision(record)["emission_evaluated_off_snap"]
        for sector in item["data_sectors"]
    ] == moved
    report = build_report(record)
    glance = " ".join(
        item["text"] for item in report["sections"]["summary"]["considerations"]
    )
    assert "the key length is computed from your receiver model" in glance
    assert "do not rest on [[A-SNAP]]" in glance


def test_the_licensed_route_carries_the_companion_s_own_rows_relaxed() -> None:
    """Licensed: the companion's relaxed entry replaces its link's; key >= today's."""
    record = _run(_config(route="licensed", **NOISY))
    bracket = _counted(record)
    compiled = _decision(record)["compiled"]
    (replacement,) = compiled["entry_replacements"]
    assert replacement["relaxed"] == [True]
    assert all(F(delta) > 0 for delta in replacement["deltas"])
    entries = record["payload"]["stages"]["reduction"]["reference_companion"]["entries"]
    assert entries and all(entry["relaxed"] for entry in entries)
    assert all(F(entry["constant"]) < 0 for entry in entries)
    assert _key_rate(record)["key_length"] >= bracket["snapped"]["key_length"]
    _no_a_snap(record)


def test_an_ideal_device_at_angle_one_seventh_is_evaluated_off_its_snap() -> None:
    """The rotated ideal device (P19): enclosed references, recentred, evaluated off."""
    record = _run(
        _config(photon_cutoff=F(2), exact_window=F(3), half_wave_angle=F(1, 7))
    )
    bracket = _counted(record)
    blocks = record["payload"]["stages"]["reduction"]["reference_companion"]["blocks"]
    enclosed = [block for block in blocks if block["kind"] == "enclosed"]
    assert enclosed and sum(block["recentred_entries"] for block in enclosed) > 0
    measured = bracket["admission"]["measurements"]
    assert any(F(item["largest_radius"]) > 0 for item in measured)
    _not_below_snapped(record, bracket)
    # The receiver's factor form fixes the analyser's ranks,
    # so the number is certified on the companion and nothing rests.
    assert _key_rate(record)["certified"]["declaration"] == "reference_companion"
    _all_evaluated_off(record)
    _no_a_snap(record)


def test_no_contributing_point_falls_back_to_the_snapped_bound_with_a_snap(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """req:bracket-on-reference (iv), forced: every evaluated point withdrawn.

    The search's points and the polish's alike, so that no set contributes.
    """
    _withdraw_every_companion_point(monkeypatch)
    record = _run(_config(photon_cutoff=F(2), exact_window=F(3), **NOISY))
    rate = _key_rate(record)
    bracket = rate["reference_bracket"]
    assert bracket["status"] == "withdrawn" and bracket["counted"] is False
    assert bracket["reason"] == "reference_bracket_withdrawn"
    assert all(
        point["withdrawal_reference"] == "iterate_not_feasible"
        for point in bracket["points"]
    )
    assert rate["h_lb"] == bracket["snapped"]["h_lb"]
    assert rate["key_length"] == bracket["snapped"]["key_length"] == 1482
    roots = rate["optimizer_certificate"]["claim_roots"]
    assert "meat-core/frank-wolfe/thm:firstorder" in roots
    decision = _decision(record)
    assert decision["status"] == "withdrawn"
    assert decision["evaluated_off_snap"] == [] and decision["rests_on_a_snap"] is True
    assert "A-SNAP" in _engaged(record)
    section = build_report(record)["sections"]["protocol"]["measurement_snaps"]
    assert section is not None and section["rests_on_a_snap"] is True


def test_companion_maps_that_cannot_be_generated_withdraw_the_companion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A failed map generation is no hard error of the run.

    The companion's evaluated numbers need not be a POVM; where its maps
    cannot be generated, the companion is withdrawn with
    reference_bracket_withdrawn and the run falls back by item (iv).
    """
    from certiqs_key.meat_core.errors import DeclarationError
    from certiqs_key.solvers.frank_wolfe import reference

    def refuse(*args: Any, **kwargs: Any) -> Any:
        raise DeclarationError("the companion's maps refuse (forced by the test)")

    monkeypatch.setattr(reference, "build_joint_maps", refuse)
    record = _run(_config(photon_cutoff=F(2), exact_window=F(3), **NOISY))
    rate = _key_rate(record)
    bracket = rate["reference_bracket"]
    assert bracket["status"] == "withdrawn"
    assert bracket["reason"] == "reference_bracket_withdrawn"
    assert "maps could not be generated" in bracket["detail"]
    assert bracket["points"] == []
    assert rate["key_length"] == bracket["snapped"]["key_length"]
    assert "A-SNAP" in _engaged(record)


def test_the_companion_s_gradient_is_formed_with_no_perturbation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """req:bracket-on-reference (ii): the gradient on D^ref has no perturbation.

    The companion is handed settings with a
    gradient perturbation (no run setting reaches it, so the test sets it at
    the call), and every assessment on the companion still runs with none, so
    no point is withdrawn as gradient_perturbation_applied and the bound counts.
    """
    from certiqs_key.solvers.frank_wolfe import general_keyrate, reference

    seen: list[float] = []
    original_assess = reference.assess_first_order
    original_bracket = reference.bracket_on_reference

    def spy(*args: Any, **kwargs: Any) -> Any:
        seen.append(args[6].gradient_perturbation)
        return original_assess(*args, **kwargs)

    def perturbed(*args: Any, **kwargs: Any) -> Any:
        args = (*args[:5], replace(args[5], gradient_perturbation=1e-9), *args[6:])
        return original_bracket(*args, **kwargs)

    monkeypatch.setattr(reference, "assess_first_order", spy)
    monkeypatch.setattr(general_keyrate, "bracket_on_reference", perturbed)
    record = _run(_config(photon_cutoff=F(2), exact_window=F(3), **NOISY))
    _counted(record)
    assert seen and all(value == 0.0 for value in seen)


def test_an_unsolved_companion_call_bounds_the_point_and_withdraws_nothing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """req:first-order-withdrawal: no status removes an iterate, on the companion too.

    Every fresh oracle call on the companion
    raises a status that asserts nothing ("unknown", with no dual). Each
    evaluated point still forms its bracket, from zero multipliers
    (req:verified-feasible-side (ii)); none is withdrawn as "OracleFailure",
    and the companion's bound counts.
    """
    from certiqs_key.solvers.frank_wolfe import general_keyrate, reference
    from certiqs_key.solvers.oracles.protocol import OracleFailure

    original_bracket = reference.bracket_on_reference

    class Unsolved:
        def __init__(self, inner: Any) -> None:
            self.inner = inner

        def capabilities(self) -> Any:
            return self.inner.capabilities()

        def minimize(self, problem: Any) -> Any:
            raise OracleFailure("status 'unknown' (test)", status="unknown")

    def unsolved(*args: Any, **kwargs: Any) -> Any:
        args = (*args[:2], Unsolved(args[2]), *args[3:])
        return original_bracket(*args, **kwargs)

    monkeypatch.setattr(general_keyrate, "bracket_on_reference", unsolved)
    record = _run(_config(photon_cutoff=F(2), exact_window=F(3), **NOISY))
    bracket = _key_rate(record)["reference_bracket"]
    assert bracket["points"]
    for point in bracket["points"]:
        assert point["withdrawal_reference"] is None
        side = point["feasible_side_reference"]
        assert set(side["feasible_side_multipliers"].values()) == {"zero"}
        assert side["oracle_pairing"] is None
    assert bracket["status"] == "counted"


def test_a_point_violating_the_companion_s_own_rows_is_withdrawn(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """req:bracket-on-reference (ii), (iv): membership decided on D^ref's own rows.

    On the licensed route the admitted
    companion's replacing entry is tightened by 1e-3, so that every point the
    search found on D violates a row of D^ref that D does not have. The gate
    decides membership against D^ref's entries, so every evaluated point is
    withdrawn as iterate_not_feasible, and the run falls back to h_lb[D] with
    A-SNAP disclosed. Nothing else is forced.
    """
    from certiqs_key.meat_core.declaration.companion import AdmittedCompanion
    from certiqs_key.solvers.frank_wolfe import general_keyrate

    original = general_keyrate.admit_reference_companion

    def tightened(declaration: Any, companion: Any) -> Any:
        found = original(declaration, companion)
        assert isinstance(found, AdmittedCompanion)
        (replacement,) = companion.replacements
        entries = list(found.declaration.constraint_list)
        for index in range(
            replacement.start, replacement.start + len(replacement.entries)
        ):
            entries[index] = replace(entries[index], bound=entries[index].bound + 1e-3)
        return replace(
            found,
            declaration=replace(
                found.declaration, constraint_list=tuple(entries), _product_cache={}
            ),
        )

    monkeypatch.setattr(general_keyrate, "admit_reference_companion", tightened)
    record = _run(_config(route="licensed", **NOISY))
    rate = _key_rate(record)
    bracket = rate["reference_bracket"]
    assert bracket["status"] == "withdrawn" and bracket["counted"] is False
    assert bracket["reason"] == "reference_bracket_withdrawn"
    assert bracket["points"]
    assert all(
        point["withdrawal_reference"] == "iterate_not_feasible"
        and point["bracket_reference"] is None
        for point in bracket["points"]
    )
    assert rate["h_lb"] == bracket["snapped"]["h_lb"]
    assert rate["key_length"] == bracket["snapped"]["key_length"]
    assert _decision(record)["status"] == "withdrawn"
    assert "A-SNAP" in _engaged(record)
    # The report says why the receiver model was not used.
    section = build_report(record)["sections"]["protocol"]["measurement_snaps"]
    assert section is not None and section["direct_route"] == "withdrawn"
    assert any(
        "not computed from it" in sentence
        and "no point gave a usable bound" in sentence
        for sentence in section["plain"]
    )


def test_a_mixed_companion_engages_a_snap_only_where_no_reference_is_handed() -> None:
    """req:bracket-on-reference (v): enclosed references not used, a mixed companion.

    With reference_enclosure off, the receiver hands only its exact blocks
    (m = 0, 1); the companion carries the snapped m = 2 block, which is not
    evaluated off its snap and rests on A-SNAP, while m = 0, 1 and the emission
    do not.
    """
    config = _config(photon_cutoff=F(2), exact_window=F(3), **NOISY).with_(
        reference_enclosure=False
    )
    record = _run(config)
    _counted(record)
    decision = _decision(record)
    assert {item["block"] for item in decision["evaluated_off_snap"]} == {
        "m=0, t=off",
        "m=1, t=off",
    }
    resting = {(item["origin"], item["block"]) for item in decision["resting_blocks"]}
    assert resting == {("instance_snap", "m=2, t=off")}
    assert "A-SNAP" in _engaged(record)
    entry = next(
        e for e in record["payload"]["assumption_manifest"]["assumptions"]
        if e["short_id"] == "A-SNAP"
    )
    assert entry is not None
    blocks = record["payload"]["stages"]["reduction"]["reference_companion"]["blocks"]
    carries = {block["block"]: block["carries"] for block in blocks}
    assert carries["m=2, t=off"] == "snapped_block"
    offered = record["payload"]["snaps"]["instance"]["measurement_snaps"][0]
    kinds = {item["block"]: item["cause"] for item in offered["reference"]["offered"]
             if "cause" in item}
    assert kinds == {"m=2": "enclosure_not_used"}
    report = build_report(record)
    section = report["sections"]["protocol"]["measurement_snaps"]
    assert section is not None and section["rests_on_a_snap"] is True
    assert [row["evaluated_off_snap"] for row in section["rows"]] == [True, True, False]
    # The summary's considerations name the blocks the model is read on.
    glance = " ".join(
        item["text"] for item in report["sections"]["summary"]["considerations"]
    )
    assert ("On 2 of the 3 moved measurement blocks the key length is computed "
            "from your receiver model; on the other moved blocks it reads the "
            "rounded measurement.") in glance
    assert "not from its rounded form" not in glance


@pytest.mark.slow
def test_bbm92_licensed_with_dark_counts_is_evaluated_off_its_snap() -> None:
    """Two stations, each with its own companion, on the licensed route."""
    base = _config("bbm92", 30)
    config = base.with_(
        device={
            **base.device,
            "alice_dark_count": dict.fromkeys(PORTS, F(1, 10**6)),
            "bob_dark_count": dict.fromkeys(PORTS, F(1, 10**6)),
            "alice_efficiency": dict.fromkeys(PORTS, F(9, 10)),
            "bob_efficiency": dict.fromkeys(PORTS, F(9, 10)),
            "route": "licensed",
        }
    )
    record = _run(config, "bbm92")
    bracket = _counted(record)
    decision = _decision(record)
    stations = {item["factor"] for item in decision["evaluated_off_snap"]}
    assert len(stations) == 2
    _not_below_snapped(record, bracket)
    _no_a_snap(record)


# ---------------------------------------------------------------------------
#  The strict option and the requested entries on the companion
# ---------------------------------------------------------------------------


def test_the_strict_option_refuses_after_a_withdrawn_bracket(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """foundations/req:snap-reference (iv): refused after the search.

    The noisy two-photon device
    hands its reference on every moved block, so neither the snap nor the
    emission refuses; with every evaluated point withdrawn, the run falls back
    to the snapped bound, its moved blocks would rest on A-SNAP, and a strict
    run refuses at ``solve`` under ``strict_snaps``, naming the group.
    """
    _withdraw_every_companion_point(monkeypatch)
    config = _config(photon_cutoff=F(2), exact_window=F(3), **NOISY).with_(
        strict_snaps=True
    )
    record = _run(config)
    solve = record["payload"]["stages"]["solve"]
    assert solve["refused"] is True and solve["reason"] == "strict_snaps"
    assert "reference_bracket_withdrawn" in solve["detail"]
    assert record["payload"]["config"]["parameters"]["strict_snaps"] is True


def test_licensed_two_sector_forms_its_entry_on_the_companion() -> None:
    """reductions/req:reference-companion (iii).

    The noisy one-photon device on ``licensed+two-sector``: the requested operator
    eq:two-sector-entry is formed on the companion where wpfss/cor:flat-companion's
    eq:companion-two-sector holds, carried into the compiled companion relaxed
    outward, and the bound on the companion counts.
    """
    record = _run(
        _config(photon_cutoff=F(1), route="licensed+two-sector", **NOISY)
    )
    _counted(record)
    companion = record["payload"]["stages"]["reduction"]["reference_companion"]
    (formed,) = companion["requested_entries_formed"]
    assert formed["writing"] == "two_sector"
    assert formed["established_by"] == (
        "reductions/wpfss/cor:flat-companion (eq:companion-two-sector)"
    )
    assert companion["requested_entries_not_formed"] == []
    relaxes = {entry["relaxes"] for entry in companion["entries"]}
    assert formed["label"] in relaxes
    _no_a_snap(record)
