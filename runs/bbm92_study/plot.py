r"""Draw the study's figures from the summary CSVs, and nothing else.

::

    python -m runs.bbm92_study.plot                     # every figure with data
    python -m runs.bbm92_study.plot --figure F1 --data runs/bbm92_study/data

Every figure reads ``<data>/<sweep>/summary.csv`` (:mod:`runs.bbm92_study.summarize`)
and writes ``<build>/<id>-<sweep>.pdf`` and ``.png``. Beside each it writes the
plotted columns as a whitespace-separated ``.dat`` table that PGFPlots reads
with ``\\addplot table``, so the whitepaper can redraw a figure natively without
a rerun. The figure files go to the git-ignored ``build/`` by default. Copy a
figure into the whitepaper only together with its ``.dat`` and the commit its
records name (the CSV's ``git_commit``).

STYLE. The house rules of the whitepaper's style guide: flat, a restrained
palette, and series told apart by line style and marker as well as colour, with
direct labels at the line ends. Ordered series (several n, several losses) take
one blue ramp, light to dark (validated ordinal: monotone lightness, light end
2.06:1 on white). Unordered ones (solver methods) take blue, orange and aqua,
validated across all pairs; aqua is under 3:1 on white, so each line also
carries a marker and a label. One y-scale per panel; the coincidence axis of F3
is a second x-axis that relabels the same rounds, not a second measure.

WHAT IS PLOTTED. The key rate is ``key_length / rounds``, secret bits per
channel use. A point with no positive key (clamped to zero or refused) cannot
sit on a log axis, so it is left out and counted in the panel's note. The CSV
keeps it.
"""

from __future__ import annotations

import argparse
import csv
import math
from collections import defaultdict
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

__all__ = ["FIGURES", "main"]

DEFAULT_DATA = Path("runs/bbm92_study/data")
DEFAULT_BUILD = Path("build/bbm92-study/figures")

#: The ordinal blue ramp (steps 250 .. 650 of the reference palette).
RAMP = ("#86b6ef", "#5598e7", "#2a78d6", "#1c5cab", "#104281")
#: The categorical slots 1 .. 3.
CATEGORICAL = ("#2a78d6", "#eb6834", "#1baf7a")
LINESTYLES = ("-", "--", "-.", ":", (0, (5, 1, 1, 1)))
MARKERS = ("o", "s", "^", "D", "v")
INK = "#0b0b0b"
INK_SECONDARY = "#52514e"
GRID = "#e4e3df"
WIDTH_IN = 6.0


def _ramp(count: int) -> tuple[str, ...]:
    """Return ``count`` steps of the ordinal ramp, spread end to end."""
    if count == 1:
        return (RAMP[2],)
    return tuple(RAMP[round(i * (len(RAMP) - 1) / (count - 1))] for i in range(count))


def _read(data: Path, sweep: str) -> list[dict[str, str]]:
    path = data / sweep / "summary.csv"
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _num(row: dict[str, str], key: str) -> float | None:
    value = row.get(key)
    if value in (None, "", "None"):
        return None
    return float(value)


def _rate(row: dict[str, str]) -> float | None:
    key, n = _num(row, "key_length"), _num(row, "rounds")
    if key is None or n is None or key <= 0:
        return None
    return key / n


def _style(ax: Any) -> None:
    ax.grid(True, which="major", color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(INK_SECONDARY)
        ax.spines[side].set_linewidth(0.6)
    ax.tick_params(colors=INK_SECONDARY, labelcolor=INK, width=0.6)


def _label_end(
    ax: Any, x: Sequence[float], y: Sequence[float], text: str, *, at: str = "end"
) -> None:
    """Label a line at its last point, or at its first where lines meet at the end."""
    i, offset, align = (-1, 4, "left") if at == "end" else (0, -4, "right")
    ax.annotate(
        text,
        (x[i], y[i]),
        xytext=(offset, 0),
        textcoords="offset points",
        va="center",
        ha=align,
        fontsize=7,
        color=INK,
    )


def _series(
    ax: Any,
    groups: dict[Any, list[tuple[float, float]]],
    label: Callable[[Any], str],
    colours: Sequence[str],
    *,
    label_at: str = "end",
) -> list[tuple[str, list[float], list[float]]]:
    """Draw one line per group, ordered by key; return the plotted columns."""
    plotted = []
    for i, key in enumerate(sorted(groups)):
        pts = sorted(groups[key])
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        if not xs:
            continue
        ax.plot(
            xs,
            ys,
            color=colours[i],
            linestyle=LINESTYLES[i % len(LINESTYLES)],
            marker=MARKERS[i % len(MARKERS)],
            markersize=3.5,
            linewidth=1.4,
            label=label(key),
        )
        _label_end(ax, xs, ys, label(key), at=label_at)
        plotted.append((label(key), xs, ys))
    return plotted


def _note(ax: Any, dropped: int) -> None:
    if dropped:
        ax.text(
            0.99,
            0.99,
            f"{dropped} point(s) without a positive key not shown",
            transform=ax.transAxes,
            ha="right",
            va="top",
            fontsize=6.5,
            color=INK_SECONDARY,
        )


def _write_dat(path: Path, columns: Mapping[str, Sequence[Any]]) -> None:
    names = list(columns)
    rows = max(len(v) for v in columns.values())
    lines = [" ".join(names)]
    for i in range(rows):
        cells = []
        for name in names:
            seq = columns[name]
            cells.append(str(seq[i]) if i < len(seq) else "nan")
        lines.append(" ".join(cells))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def _flat_dat(
    plotted: list[tuple[str, list[float], list[float]]], x: str, y: str
) -> dict[str, list[Any]]:
    out: dict[str, list[Any]] = {"series": [], x: [], y: []}
    for name, xs, ys in plotted:
        for a, b in zip(xs, ys, strict=True):
            out["series"].append(name.replace(" ", "_"))
            out[x].append(a)
            out[y].append(b)
    return out


def _n_label(n: float) -> str:
    exponent = math.log10(n)
    if abs(exponent - round(exponent)) < 1e-9:
        return f"$n=10^{{{round(exponent)}}}$"
    return f"$n={n:.2g}$"


# --------------------------------------------------------------------------
# The figures
# --------------------------------------------------------------------------


def figure_loss(data: Path, build: Path, plt: Any) -> Path | None:
    """F1: key rate against total loss, one line per n."""
    rows = _read(data, "loss")
    groups: dict[float, list[tuple[float, float]]] = defaultdict(list)
    dropped = 0
    for row in rows:
        rate, loss, n = _rate(row), _num(row, "loss_db"), _num(row, "rounds")
        if row.get("status") == "missing" or loss is None or n is None:
            continue
        if rate is None:
            dropped += 1
            continue
        groups[n].append((loss, rate))
    if not groups:
        return None
    fig, ax = plt.subplots(figsize=(WIDTH_IN, 3.4))
    plotted = _series(ax, groups, _n_label, _ramp(len(groups)))
    ax.set_yscale("log")
    ax.set_xlabel("total channel loss (dB), split equally between the arms")
    ax.set_ylabel("secret bits per channel use")
    _style(ax)
    _note(ax, dropped)
    return _save(fig, build, "F1-loss", _flat_dat(plotted, "loss_db", "rate"))


def figure_qber(data: Path, build: Path, plt: Any) -> Path | None:
    """F2: key rate against QBER (depolarising noise), one line per loss."""
    rows = _read(data, "qber")
    groups: dict[float, list[tuple[float, float]]] = defaultdict(list)
    dropped = 0
    for row in rows:
        rate, loss, q = _rate(row), _num(row, "loss_db"), _num(row, "qber")
        if row.get("status") == "missing" or loss is None or q is None:
            continue
        if rate is None:
            dropped += 1
            continue
        groups[loss].append((100 * q, rate))
    if not groups:
        return None
    fig, ax = plt.subplots(figsize=(WIDTH_IN, 3.4))
    plotted = _series(ax, groups, lambda loss: f"{loss:g} dB", _ramp(len(groups)))
    ax.set_yscale("log")
    ax.set_xlabel("QBER from depolarising noise (%)")
    ax.set_ylabel("secret bits per channel use")
    _style(ax)
    _note(ax, dropped)
    return _save(fig, build, "F2-qber", _flat_dat(plotted, "qber_percent", "rate"))


def figure_rounds(data: Path, build: Path, plt: Any) -> Path | None:
    """F3: key rate against n, one panel per loss, coincidences on top."""
    rows = _read(data, "rounds")
    panels: dict[float, list[tuple[float, float, float]]] = defaultdict(list)
    dropped: dict[float, int] = defaultdict(int)
    for row in rows:
        rate, loss, n = _rate(row), _num(row, "loss_db"), _num(row, "rounds")
        pc = _num(row, "p_coincidence")
        if row.get("status") == "missing" or loss is None or n is None:
            continue
        if rate is None or pc is None:
            dropped[loss] += 1
            continue
        panels[loss].append((n, rate, pc))
    if not panels:
        return None
    losses = sorted(panels)
    fig, axes = plt.subplots(
        1, len(losses), figsize=(WIDTH_IN, 2.8), sharey=True, squeeze=False
    )
    colours = _ramp(len(losses))
    columns: dict[str, list[Any]] = {
        "loss_db": [],
        "rounds": [],
        "coincidences": [],
        "rate": [],
    }
    for i, loss in enumerate(losses):
        ax = axes[0][i]
        pts = sorted(panels[loss])
        xs, ys, pc = [p[0] for p in pts], [p[1] for p in pts], pts[0][2]
        ax.plot(
            xs,
            ys,
            color=colours[i],
            linestyle=LINESTYLES[i],
            marker=MARKERS[i],
            markersize=3,
            linewidth=1.4,
        )
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_title(f"{loss:g} dB", fontsize=8, color=INK)
        ax.set_xlabel("$n$, channel uses")
        top = ax.secondary_xaxis(
            "top", functions=(lambda x, pc=pc: x * pc, lambda x, pc=pc: x / pc)
        )
        top.set_xlabel("expected coincidences", fontsize=7, color=INK_SECONDARY)
        top.tick_params(labelsize=6, colors=INK_SECONDARY)
        _style(ax)
        _note(ax, dropped[loss])
        for n, rate, p in pts:
            columns["loss_db"].append(loss)
            columns["rounds"].append(n)
            columns["coincidences"].append(n * p)
            columns["rate"].append(rate)
    axes[0][0].set_ylabel("secret bits per channel use")
    return _save(fig, build, "F3-rounds", columns)


def figure_solvers(data: Path, build: Path, plt: Any) -> Path | None:
    """F4: the certified bracket [h_lb, h_low] per method, against alpha."""
    rows = _read(data, "solvers")
    methods: dict[str, list[tuple[float, float, float]]] = defaultdict(list)
    for row in rows:
        a, lb, low = _num(row, "alpha"), _num(row, "h_lb"), _num(row, "h_low")
        method = row.get("method")
        if (
            row.get("status") != "ok"
            or a is None
            or lb is None
            or low is None
            or not method
        ):
            continue
        methods[method].append((a - 1.0, lb, low))
    if not methods:
        return None
    order = [m for m in ("fw", "pairwise", "auto") if m in methods]
    fig, ax = plt.subplots(figsize=(WIDTH_IN, 3.4))
    columns: dict[str, list[Any]] = {
        "method": [],
        "alpha_minus_one": [],
        "h_lb": [],
        "h_low": [],
    }
    for i, method in enumerate(order):
        pts = sorted(methods[method])
        xs = [p[0] for p in pts]
        lbs = [p[1] for p in pts]
        lows = [p[2] for p in pts]
        ax.plot(
            xs,
            lbs,
            color=CATEGORICAL[i],
            linestyle=LINESTYLES[i],
            marker=MARKERS[i],
            markersize=3.5,
            linewidth=1.4,
            label=f"{method}: $h_{{lb}}$",
        )
        ax.fill_between(xs, lbs, lows, color=CATEGORICAL[i], alpha=0.15, linewidth=0)
        _label_end(ax, xs, lbs, method)
        for x, lb, low in pts:
            columns["method"].append(method)
            columns["alpha_minus_one"].append(x)
            columns["h_lb"].append(lb)
            columns["h_low"].append(low)
    ax.set_xscale("log")
    ax.set_xlabel(r"$\alpha - 1$")
    ax.set_ylabel("bits per round: $h_{lb}$ (line) to $h_{low}$ (band)")
    ax.legend(frameon=False, fontsize=7)
    _style(ax)
    return _save(fig, build, "F4-solvers", columns)


def figure_alpha(data: Path, build: Path, plt: Any) -> Path | None:
    """F7: key length relative to its best, against alpha, one line per n."""
    rows = _read(data, "alpha")
    groups: dict[float, list[tuple[float, float]]] = defaultdict(list)
    for row in rows:
        a, n, key = _num(row, "alpha"), _num(row, "rounds"), _num(row, "key_length")
        if row.get("status") != "ok" or a is None or n is None or key is None:
            continue
        groups[n].append((a - 1.0, key))
    groups = {n: pts for n, pts in groups.items() if max(k for _, k in pts) > 0}
    if not groups:
        return None
    relative = {
        n: [(x, k / max(kk for _, kk in pts)) for x, k in pts if k > 0]
        for n, pts in groups.items()
    }
    fig, ax = plt.subplots(figsize=(WIDTH_IN, 3.4))
    colours = _ramp(len(relative))
    plotted = _series(ax, relative, _n_label, colours, label_at="start")
    for i, (_name, xs, ys) in enumerate(plotted):
        best = max(range(len(ys)), key=ys.__getitem__)
        ax.plot(
            [xs[best]],
            [ys[best]],
            marker="*",
            markersize=9,
            color=colours[i],
            markeredgecolor="white",
            markeredgewidth=0.6,
            linestyle="none",
        )
    ax.set_xscale("log")
    ax.set_xlim(left=min(min(xs) for _, xs, _ in plotted) / 4)
    ax.set_xlabel(r"$\alpha - 1$")
    ax.set_ylabel("key length / best key length over the grid (star)")
    _style(ax)
    return _save(
        fig, build, "F7-alpha", _flat_dat(plotted, "alpha_minus_one", "relative")
    )


FIGURES: dict[str, Callable[[Path, Path, Any], Path | None]] = {
    "F1": figure_loss,
    "F2": figure_qber,
    "F3": figure_rounds,
    "F4": figure_solvers,
    "F7": figure_alpha,
}


def _save(
    fig: Any, build: Path, stem: str, columns: Mapping[str, Sequence[Any]]
) -> Path:
    build.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    pdf = build / f"{stem}.pdf"
    fig.savefig(pdf, metadata={"CreationDate": None, "ModDate": None})
    fig.savefig(build / f"{stem}.png", dpi=200)
    _write_dat(build / f"{stem}.dat", columns)
    import matplotlib.pyplot as plt

    plt.close(fig)
    return pdf


def main(argv: list[str] | None = None) -> int:
    """Draw the requested figures (all by default) that have data."""
    parser = argparse.ArgumentParser(prog="python -m runs.bbm92_study.plot")
    parser.add_argument("--figure", action="append", choices=sorted(FIGURES))
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--build", type=Path, default=DEFAULT_BUILD)
    args = parser.parse_args(argv)
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update(
        {
            "font.family": "serif",
            "mathtext.fontset": "cm",
            "font.size": 8,
            "axes.labelsize": 8,
            "axes.labelcolor": INK,
            "xtick.labelsize": 7,
            "ytick.labelsize": 7,
            "pdf.fonttype": 42,
        }
    )
    for name in args.figure or sorted(FIGURES):
        path = FIGURES[name](args.data, args.build, plt)
        print(f"{name}: {path if path else 'no data yet'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
