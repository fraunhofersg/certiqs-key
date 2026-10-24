"""The BBM92 study (runs/bbm92_study): declarations, summary and plots, no solving.

Running a point needs the solver and is exercised by
tests/integration/test_runs_alpha_search_bbm92.py; these tests check what the
study declares and how it reads a finished point.
"""

from __future__ import annotations

import csv
import re
from fractions import Fraction
from pathlib import Path

import pytest
from instances import surface_of
from runs.bbm92_study.summarize import coincidence_probability, row, write_csv
from runs.bbm92_study.sweeps import SWEEPS, configure, per_arm_transmittance


@pytest.mark.parametrize("name", sorted(SWEEPS))
def test_point_ids_are_unique_and_filesystem_safe(name: str) -> None:
    ids = [p.id for p in SWEEPS[name].points()]
    assert len(ids) == len(set(ids))
    assert all(re.fullmatch(r"[A-Za-z0-9_.-]+", i) for i in ids)


@pytest.mark.parametrize("name", sorted(SWEEPS))
def test_every_point_configures_against_the_bbm92_defaults(name: str) -> None:
    base = surface_of("bbm92").default_config()
    for point in SWEEPS[name].points():
        config = configure(base, point)
        assert config.rounds == point.rounds
        assert config.solver == point.solver
        if point.alpha is not None:
            assert config.alpha == point.alpha


def test_qber_is_set_exactly_through_visibility() -> None:
    point = next(p for p in SWEEPS["qber"].points() if p.id == "realistic-L0-Q0p01")
    assert point.model["visibility"] == Fraction(49, 50)


def test_total_loss_splits_equally_between_the_arms() -> None:
    t = per_arm_transmittance(10.0)
    assert float(t * t) == pytest.approx(0.1, rel=1e-12)
    assert per_arm_transmittance(0.0) == 1


def test_coincidences_count_rounds_where_both_stations_click() -> None:
    raw = {
        "x0|(nc,gen)__nc": "1/4",
        "x0|(nc,gen)__H": "1/8",
        "x0|(H,gen)__nc": "1/8",
        "x0|(H,gen)__H": "1/4",
        "x0|(D,test)__mc": "1/4",
    }
    assert coincidence_probability(raw) == Fraction(1, 2)


def test_a_point_not_yet_run_is_a_missing_row(tmp_path: Path) -> None:
    point = SWEEPS["loss"].points()[0]
    r = row("loss", point, tmp_path / point.id)
    assert r["status"] == "missing"
    target = tmp_path / "summary.csv"
    write_csv([r], target)
    with target.open(encoding="utf-8", newline="") as handle:
        (read,) = list(csv.DictReader(handle))
    assert read["point"] == point.id and read["status"] == "missing"


def test_the_loss_figure_draws_from_a_summary(tmp_path: Path) -> None:
    pytest.importorskip("matplotlib")
    from runs.bbm92_study import plot

    rows = [
        {
            "sweep": "loss",
            "point": f"p{i}",
            "loss_db": loss,
            "rounds": n,
            "status": "ok",
            "key_length": key,
        }
        for i, (loss, n, key) in enumerate(
            [(0, 10**8, 4e7), (10, 10**8, 4e6), (20, 10**8, 0), (0, 10**6, 3e5)]
        )
    ]
    write_csv(rows, tmp_path / "data" / "loss" / "summary.csv")
    assert (
        plot.main(
            [
                "--figure",
                "F1",
                "--data",
                str(tmp_path / "data"),
                "--build",
                str(tmp_path / "build"),
            ]
        )
        == 0
    )
    assert (tmp_path / "build" / "F1-loss.pdf").exists()
    dat = (tmp_path / "build" / "F1-loss.dat").read_text(encoding="utf-8")
    assert dat.splitlines()[0] == "series loss_db rate"
    assert len(dat.splitlines()) == 1 + 3  # the zero-key point is not drawn


def test_only_the_declared_points_use_the_spectral_oracle() -> None:
    """Only the declared points use the spectral oracle; every other keeps QICS."""
    from runs.bbm92_study.sweeps import SPECTRAL_POINTS

    spectral = {
        (name, p.id)
        for name, sweep in SWEEPS.items()
        for p in sweep.points()
        if p.solver.advanced is not None and p.solver.advanced.oracle == "spectral"
    }
    assert spectral == SPECTRAL_POINTS
    assert spectral == {
        ("rounds", "realistic-L10-c1e4"),
        ("qber", "realistic-L10-Q0p05"),
        ("qber", "realistic-L0-Q0"),
        ("rounds", "realistic-L20-c3e5"),
    }


def test_routes_run_both_device_sets_each_borrowing_its_own_alpha() -> None:
    points = {p.id: p for p in SWEEPS["routes"].points()}
    for kind in ("realistic", "perfect"):
        for cutoff in (1, 2, 3, 4, 5):
            encoded = points[f"{kind}-encoded-N{cutoff}"]
            licensed = points[f"{kind}-licensed-N{cutoff}"]
            assert encoded.labels["devices"] == licensed.labels["devices"] == kind
            if kind == "realistic" and cutoff > 3:
                # Above cutoff 3 both routes take realistic encoded N3's
                # alpha, on the long budget (REALISTIC_LONG_FROM_CUTOFF).
                assert encoded.alpha_from == licensed.alpha_from
                assert encoded.alpha_from == "realistic-encoded-N3"
                assert encoded.solver.budget_seconds == 7200
            else:
                assert encoded.alpha_from is None
                assert licensed.alpha_from == encoded.id
            long_from = 3 if kind == "realistic" else 4
            assert (licensed.solver.budget_seconds == 7200) == (cutoff >= long_from)
            assert encoded.rounds == licensed.rounds
            window = encoded.device["alice_exact_window"]
            assert window == licensed.device["bob_exact_window"] > cutoff
    assert points["perfect-encoded-N1"].rounds < points["realistic-encoded-N1"].rounds


def test_the_realistic_set_is_the_ladders_bottom_rung_and_perfect_its_top() -> None:
    """Realistic = every imperfection, perfect = none, at the same channel.

    Realistic is every source and receiver imperfection; perfect is the
    ladder's top rung.
    """
    from runs.bbm92_study.sweeps import REALISTIC, _realistic_device

    ladder = [p for p in SWEEPS["ladder"].points() if p.id.startswith("c1e6-")]
    assert dict(ladder[0].device) == {} and "visibility" not in ladder[0].model
    assert dict(ladder[-1].device) == _realistic_device()
    assert ladder[-1].model["visibility"] == REALISTIC["visibility"]
    loss = {p.id: p for p in SWEEPS["loss"].points()}
    real, perf = loss["realistic-c1e6-L10"], loss["perfect-c1e6-L10"]
    assert dict(real.device) == _realistic_device() and dict(perf.device) == {}
    assert real.model["visibility"] == REALISTIC["visibility"]
    assert perf.model["visibility"] == 1
    for side in ("alice", "bob"):
        key = f"{side}_transmittance"
        assert real.model[key] == perf.model[key]


def test_the_dark_count_is_the_cited_rate_times_the_window() -> None:
    """1 kHz (joshi2020network p.8) times about 130 ps (p.2), per port per round."""
    from runs.bbm92_study.sweeps import REALISTIC

    assert REALISTIC["dark_count"] == Fraction(1000) * Fraction(130, 10**12)
