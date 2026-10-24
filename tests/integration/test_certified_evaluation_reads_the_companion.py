"""On the reference route the certified evaluation reads the companion.

``meat-core/frank-wolfe/req:certified-evaluation`` (i), (ii) and
``cor:certified-keylength-reference``: where the reference companion's bracket
counts, the certified number is formed on the companion's declaration with the
companion's enclosures, never on the searched (snapped) declaration.

The first test fails on two mutants: one that evaluates on the searched maps
while the result still names the companion route, and one that does not hand
over the companion's enclosures, so its blocks read as exact centres and the
rank rule never fires. It also reads the record's ``declaration`` and
``premises``; the others pin the fallback of item (i) and the withdrawal of
item (iv)(c) end to end on the ideal optical device at angle 1/7 -- its two
branches (prototype 5.4), the strict option, which accepts a run certified
through the fallback, the strict option ``strict_snaps``, which keeps the
fallback from running, both together, which refuse, and a defective carrier,
whose inconsistency withdraws the companion's bracket.
"""

from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("flint")


# req:certified-evaluation (i): on the reference route the evaluation reads
# the companion (MF1, MF2)


def _example_record(
    name: str, monkeypatch: pytest.MonkeyPatch, seen: dict[str, Any]
) -> dict[str, Any]:
    import tempfile
    from pathlib import Path

    from instances import surface_of
    from runs.report_examples import generate as examples

    from certiqs_key.runs.surface import InstanceIdentity
    from certiqs_key.runs.sweep import sweep
    from certiqs_key.solvers.frank_wolfe import certified, general_keyrate
    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    real_certify, real_evaluate = general_keyrate._certify, certified.evaluate

    def certify(maps: Any, *args: Any, **kwargs: Any) -> Any:
        seen["searched"] = maps
        return real_certify(maps, *args, **kwargs)

    def evaluate(maps: Any, *args: Any, **kwargs: Any) -> Any:
        seen["evaluated"] = maps
        seen["companion"] = kwargs.get("companion")
        return real_evaluate(maps, *args, **kwargs)

    monkeypatch.setattr(general_keyrate, "_certify", certify)
    monkeypatch.setattr(certified, "evaluate", evaluate)
    example = next(e for e in examples.EXAMPLES if e.name == name)
    surface = surface_of(example.instance)
    identity = InstanceIdentity(surface.DESCRIPTOR, tuple(surface.PARAMETERS))
    with tempfile.TemporaryDirectory() as scratch:
        runner = surface.runner(QicsSectorChoiOracle(), Path(scratch), created_by="t")
        (point,) = sweep(
            example.configs(surface), runner, created_by="t", instance=identity
        )
        return point.record.as_dict()


def test_on_the_reference_route_the_certified_evaluation_reads_the_companion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pytest.importorskip("qics")
    seen: dict[str, Any] = {}
    record = _example_record("optical_bb84", monkeypatch, seen)
    key_rate = record["payload"]["stages"]["key_rate"]
    assert key_rate["reference_bracket"]["status"] == "counted"
    assert key_rate["reported_tier"] == "certified"
    assert seen["evaluated"] is not seen["searched"], (
        "evaluated on the searched declaration"
    )
    assert seen["evaluated"].declaration is not seen["searched"].declaration
    assert seen["companion"] is not None, (
        "the companion enclosures were not handed to the evaluation"
    )
    # req:certified-evaluation (ix), record 0.35.0: the declaration the number
    # is formed on, and no premise at the snap where every moved block is
    # evaluated off it.
    certified = key_rate["certified"]
    assert certified["declaration"] == "reference_companion"
    assert certified["premises"] == [] and certified["resting_blocks"] == []
    assert "companion_points" not in certified
    assert "meat-core/frank-wolfe/cor:certified-keylength-reference" in (
        key_rate["claim_roots"]
    )


# req:certified-evaluation (i), (vi), (viii), (ix) and req:bracket-on-reference
# (v): THE FALLBACK, on the ideal optical device at angle 1/7 (the canary
# optical-N2-ideal-angle-1/7, N = 2, 20 iterations). Its analyser's elements are
# rank-deficient with irrational entries, so the companion's entrywise
# enclosures fix no rank; the factor form that fixes it is taken away
# (``certified._carried`` returns none), so that the companion certifies no
# point whether or not the receiver emits factor enclosures.

PORTS = ("H", "V", "D", "A")
SEARCHED_ROOTS = [
    "meat-core/frank-wolfe/cor:fo-reference",
    "meat-core/frank-wolfe/cor:certified-keylength",
    "meat-core/cor:keylength-bound",
]


def _ideal_record(
    monkeypatch: pytest.MonkeyPatch,
    seen: dict[str, Any],
    *,
    certified_evaluation: str | None = None,
    strict_snaps: bool = False,
    carried: Any = None,
    device: dict[str, Any] | None = None,
    factor_form: bool = False,
) -> dict[str, Any]:
    """Run the ideal device with no factor form, recording what was evaluated.

    ``carried`` stands in for ``certified._carried``: by default no factor
    enclosure is read on any block; ``factor_form`` keeps the real one.
    ``device`` overrides entries of the ideal device.
    """
    import importlib
    import tempfile
    from fractions import Fraction
    from pathlib import Path

    from certiqs_key.runs.config import SolverSettings
    from certiqs_key.runs.record import record_run
    from certiqs_key.solvers.frank_wolfe import certified, general_keyrate
    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    real_certify, real_evaluate = general_keyrate._certify, certified.evaluate
    real_length = general_keyrate.certified_key_length
    seen.update(evaluated=[], lengths=[])

    def certify(maps: Any, *args: Any, **kwargs: Any) -> Any:
        seen["searched"] = maps
        seen["result"] = real_certify(maps, *args, **kwargs)
        return seen["result"]

    def evaluate(maps: Any, *args: Any, **kwargs: Any) -> Any:
        result = real_evaluate(maps, *args, **kwargs)
        seen["evaluated"].append((maps, kwargs.get("companion"), result))
        return result

    def length(**kwargs: Any) -> Any:
        found = real_length(**kwargs)
        seen["lengths"].append((kwargs["h"], found[0]))
        return found

    if not factor_form:
        monkeypatch.setattr(
            certified, "_carried", carried if carried is not None else lambda *_: None
        )
    monkeypatch.setattr(general_keyrate, "_certify", certify)
    monkeypatch.setattr(certified, "evaluate", evaluate)
    monkeypatch.setattr(general_keyrate, "certified_key_length", length)
    surface = importlib.import_module("instances.optical_bb84.surface")
    base = surface.default_config()
    config = base.with_(
        device={
            **base.device,
            "photon_cutoff": Fraction(2),
            "exact_window": Fraction(3),
            "half_wave_angle": Fraction(1, 7),
            **(device or {}),
        },
        solver=SolverSettings.from_choices(
            max_iterations=20, certified_evaluation=certified_evaluation
        ),
        strict_snaps=strict_snaps,
    )
    with tempfile.TemporaryDirectory() as scratch:
        runner = surface.runner(QicsSectorChoiOracle(), Path(scratch), created_by="t")
        record: dict[str, Any] = record_run(
            runner(config, 0), config, created_by="t"
        ).as_dict()
    return record


def test_a_companion_that_certifies_no_point_falls_back_to_the_searched(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The fallback: the number is certified on the searched declaration.

    The evaluation runs twice, on the companion with its compilation and then
    on the searched maps with none; the number is certified on the searched
    declaration under A-SNAP for the blocks the companion carried, the
    companion's points and reasons are kept, the roots name
    ``cor:certified-keylength`` and not the reference corollary, and the key
    length is the one of ``h_cert[D]`` itself.
    """
    pytest.importorskip("qics")
    seen: dict[str, Any] = {}
    record = _ideal_record(monkeypatch, seen)
    payload = record["payload"]
    assert payload["refused"] is False
    key_rate = payload["stages"]["key_rate"]
    (companion, on_companion), (searched, on_searched) = [
        (maps, handed) for maps, handed, _ in seen["evaluated"]
    ]
    assert on_companion is not None and on_searched is None
    assert companion is not seen["searched"] and searched is seen["searched"]
    assert key_rate["reference_bracket"]["status"] == "counted"
    assert key_rate["reported_tier"] == "certified"
    certified = key_rate["certified"]
    assert certified["declaration"] == "searched"
    assert certified["premises"] == ["A-SNAP"]
    # The resting blocks are the companion's handed moved blocks, every one.
    handed_moved = {
        f"{block['block']}, t={snap['setting']}"
        for snap in payload["snaps"]["instance"]["measurement_snaps"]
        for block in snap["blocks"]
        if block["status"] == "moved" and block["handed_reference"] is not None
    }
    assert handed_moved == {"m=1, t=off", "m=2, t=off"}
    assert {
        (b["block"], b["group"], b["cause"]) for b in certified["resting_blocks"]
    } == {
        (block, "reference_bracket_withdrawn", "companion_not_certified")
        for block in handed_moved
    }
    route = payload["snaps"]["reference_companion"]
    assert route["fallback"] is True and route["evaluated_off_snap_count"] == 0
    assert route["resting_blocks"] == certified["resting_blocks"]
    assert [p["reasons"] for p in certified["companion_points"]] == [
        ["rank_not_certified"]
    ] * len(certified["companion_points"])
    assert key_rate["claim_roots"] == SEARCHED_ROOTS
    result = seen["result"]
    assert result.fallback and result.certified_bound is not None
    ((h, length),) = seen["lengths"]
    assert h == result.certified_bound and key_rate["key_length"] == length
    # Item (ix): the diagnostic against the searched declaration's own bound.
    snapped = key_rate["reference_bracket"]["snapped"]["h_lb"]
    assert certified["certified_minus_first_order"] == pytest.approx(
        float(result.certified_bound) - snapped, abs=1e-15
    )
    # The companion's first-order number stays the run's, with its key length.
    assert key_rate["h_lb"] == key_rate["reference_bracket"]["h_lb_reference"]


def test_strict_accepts_a_run_certified_through_the_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Item (viii)."""
    pytest.importorskip("qics")
    record = _ideal_record(monkeypatch, {}, certified_evaluation="strict")
    payload = record["payload"]
    assert payload["refused"] is False
    key_rate = payload["stages"]["key_rate"]
    assert key_rate["reported_tier"] == "certified"
    assert key_rate["certified"]["premises"] == ["A-SNAP"]


def test_under_strict_snaps_the_fallback_does_not_run(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Item (i) and ``foundations/req:snap-reference`` (iv).

    The run keeps the companion's first-order number on the device model, its
    blocks evaluated off their snap, with no A-SNAP; it does not refuse.
    """
    pytest.importorskip("qics")
    seen: dict[str, Any] = {}
    record = _ideal_record(monkeypatch, seen, strict_snaps=True)
    payload = record["payload"]
    assert payload["refused"] is False, payload.get("reason")
    assert len(seen["evaluated"]) == 1
    key_rate = payload["stages"]["key_rate"]
    assert key_rate["reported_tier"] == "first-order"
    certified = key_rate["certified"]
    assert certified["status"] == "not_certified"
    assert certified["declaration"] == "reference_companion"
    assert certified["premises"] == []
    assert payload["snaps"]["reference_companion"]["evaluated_off_snap_count"] == 2


def test_strict_with_strict_snaps_refuses(monkeypatch: pytest.MonkeyPatch) -> None:
    pytest.importorskip("qics")
    record = _ideal_record(
        monkeypatch, {}, certified_evaluation="strict", strict_snaps=True
    )
    solve = record["payload"]["stages"]["solve"]
    assert record["payload"]["refused"] is True and solve["refused"] is True
    assert solve["reason"] == "certification_refused"
    assert "rank_not_certified" in solve["detail"]


# req:bracket-on-reference (iv), its second cause, and req:certified-evaluation
# (iv)(c): a defective carrier. Every block of the companion is read with a
# factor enclosure of no column, which the entrywise rule's "not zero"
# contradicts on every block that is not zero.


def _no_column(source: Any, letter: str, s: int) -> Any:
    from certiqs_key.foundations.reference import FactorEnclosure

    return FactorEnclosure.no_column(source.sector_dims[s])


def test_an_inconsistent_carrier_withdraws_the_bracket(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The bracket is withdrawn after it counted, and every number moves to ``D``.

    The run's first-order number is formed again on the searched declaration,
    the evaluation runs there as on any run without a companion, the moved
    blocks rest on A-SNAP with the cause ``factor_enclosure_inconsistent``, and
    the roots name ``thm:firstorder``, not ``cor:fo-reference``.
    """
    pytest.importorskip("qics")
    seen: dict[str, Any] = {}
    record = _ideal_record(monkeypatch, seen, carried=_no_column)
    payload = record["payload"]
    assert payload["refused"] is False
    key_rate = payload["stages"]["key_rate"]
    bracket = key_rate["reference_bracket"]
    assert bracket["status"] == "withdrawn" and bracket["counted"] is False
    assert bracket["reason"] == "reference_bracket_withdrawn"
    assert bracket["cause"] == "factor_enclosure_inconsistent"
    assert key_rate["h_lb"] == bracket["snapped"]["h_lb"]
    certified = key_rate["certified"]
    # The first-order number formed again on D carries the first-order key
    # length recorded beside the certified one, and the diagnostic.
    assert certified["first_order_key_length"] == bracket["snapped"]["key_length"]
    result = seen["result"]
    assert result.certified_bound is not None
    assert certified["certified_minus_first_order"] == pytest.approx(
        float(result.certified_bound) - bracket["snapped"]["h_lb"], abs=1e-15
    )
    assert certified["declaration"] == "searched"
    assert {tuple(p["reasons"]) for p in certified["companion_points"]} == {
        ("factor_enclosure_inconsistent",)
    }
    assert key_rate["claim_roots"][0] == "meat-core/frank-wolfe/thm:firstorder"
    assert "meat-core/frank-wolfe/cor:fo-reference" not in key_rate["claim_roots"]
    assert {b["cause"] for b in certified["resting_blocks"]} == {
        "factor_enclosure_inconsistent"
    }
    route = payload["snaps"]["reference_companion"]
    assert route["status"] == "withdrawn" and route["evaluated_off_snap_count"] == 0
    assert certified["premises"] == ["A-SNAP"]


def test_an_inconsistent_carrier_under_strict_snaps_refuses(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``foundations/req:snap-reference`` (iv): strict_snaps refuses on that cause."""
    pytest.importorskip("qics")
    record = _ideal_record(monkeypatch, {}, strict_snaps=True, carried=_no_column)
    solve = record["payload"]["stages"]["solve"]
    assert solve["refused"] is True and solve["reason"] == "strict_snaps"
    assert "factor_enclosure_inconsistent" in solve["detail"]


# receiver/detector-imperfections/req:dark-composed-reference (vii), the count:
# a lossy device with no dark counts at N = 2.


def test_the_lossy_two_photon_device_certifies_through_the_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Efficiency 9/10, no dark counts: the count refuses the two-photon blocks.

    One photon in a port and one in each of four loss modes make five columns
    in a block of dimension three, so the receiver offers no factor enclosure
    there and the entrywise enclosure fixes no rank of the analyser's
    rank-two elements. The companion certifies no point, and the run is
    certified on the searched declaration under A-SNAP (lossy
    multi-photon devices without dark counts are left to the fallback).
    """
    pytest.importorskip("qics")
    from fractions import Fraction

    seen: dict[str, Any] = {}
    record = _ideal_record(
        monkeypatch,
        seen,
        factor_form=True,
        # Declared at the factored loss one: the station keeps its loss modes
        # (receiver/detector-imperfections/req:efficiency-normalization), which
        # make it the lossy device whose count refuses the factor form.
        device={
            "efficiency": dict.fromkeys(PORTS, Fraction(9, 10)),
            "efficiency_normalization": Fraction(1),
        },
    )
    payload = record["payload"]
    assert payload["refused"] is False
    certified = payload["stages"]["key_rate"]["certified"]
    assert payload["stages"]["key_rate"]["reported_tier"] == "certified"
    assert certified["declaration"] == "searched"
    assert certified["premises"] == ["A-SNAP"]
    assert {tuple(p["reasons"]) for p in certified["companion_points"]} == {
        ("rank_not_certified",)
    }
    offered = payload["stages"]["receiver_construction"]
    assert "columns_exceed_dimension" in str(offered)
