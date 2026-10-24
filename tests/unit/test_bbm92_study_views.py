"""The worked example's figure generator (runs.bbm92_study.views) on its snapshot.

Runs the command line on the committed snapshot
``runs/bbm92_study/data/viewmodels`` (two device sets) (and on small synthetic
key-rate summaries) into a temporary folder and checks the structure of what it
writes: every figure and caption is there, every ``tikzpicture`` is closed,
braces balance, no text-mode ``_`` or ``&`` slipped past the escaping, and the
figure rules hold (the whitepaper's fonts, lane colours in the swimlane only,
annotations in captions). LaTeX is not compiled here;
``--preview`` does that for a person.
"""

from __future__ import annotations

import copy
import csv
import io
import json
import math
import re
from fractions import Fraction
from pathlib import Path
from typing import Any

import pytest
from runs.bbm92_study.asymptote import binary_entropy
from runs.bbm92_study.views.__main__ import main
from runs.bbm92_study.views.build import build
from runs.bbm92_study.views.devices import SYMBOLS, efficiency_symbol
from runs.bbm92_study.views.keyrate import parse_summary, render_keyrate
from runs.bbm92_study.views.optics import (
    _parameter_lines,
    pi_multiple,
    radians,
    render_optics,
)
from runs.bbm92_study.views.optics_compact import DASH, render_optics_compact
from runs.bbm92_study.views.snapshot import SETS, VIEW_MODELS, read_snapshot
from runs.bbm92_study.views.snapshot import main as snapshot_main
from runs.bbm92_study.views.statistics import use_log_axis
from runs.bbm92_study.views.tex import escape, numeral

SNAPSHOT = Path(__file__).resolve().parents[2] / "runs/bbm92_study/data/viewmodels"
TIKZ = [
    "protocol.tex",
    "optics.tex",
    "optics-compact.tex",
    "povm.tex",
    "povm-compare.tex",
    "statistics.tex",
]
TABULAR = ["keymap.tex", "devices.tex"]
KEYRATE = [
    "keyrate-loss.tex",
    "keyrate-qber.tex",
    "keyrate-rounds.tex",
    "keyrate-coincidences.tex",
    "keyrate-solvers.tex",
    "keyrate-routes.tex",
    "keyrate-ladder.tex",
    "keyrate-alpha.tex",
]
KEYRATE_TABLES = ["keyrate-routes-table.tex"]

_TOKEN = re.compile(r"\\\\|\\[^A-Za-z]|\\[A-Za-z]+|\$|[^\\$]+")
"""A line break, an escaped character, a control word, a math shift, or a run
of anything else: enough of TeX's reading to tell text from markup."""

_HEADER = [
    "sweep",
    "point",
    "devices",
    "coincidences",
    "loss_db",
    "qber",
    "rounds",
    "method",
    "alpha",
    "rung",
    "effect",
    "value",
    "source",
    "cutoff",
    "route",
    "status",
    "key_length",
    "termination",
    "oracle",
    "rests_on_a_snap",
    "bracket_status",
    "snapped_key_length",
    "h_lb",
    "h_low",
    "gap",
    "alpha_searched",
    "f_ec",
    "expected_coincidences",
    "git_commit",
    "git_dirty",
]


def _summary(sweep: str, rows: list[dict[str, object]]) -> str:
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=_HEADER, lineterminator="\n")
    writer.writeheader()
    for r in rows:
        base: dict[str, object] = {
            "sweep": sweep,
            "status": "ok",
            "alpha_searched": "True",
            "f_ec": "1.1",
            "git_commit": "0123456789abcdef",
            "git_dirty": "False",
        }
        writer.writerow({**base, **r})
    return out.getvalue()


def _rounds(c: float, d: float, devices: str) -> int:
    return int(c / (10 ** (-d / 10) * (0.64 if devices == "realistic" else 1.0)))


def _synthetic() -> dict[str, str]:
    """Small summaries for every key-rate sweep, with zero and missing points."""
    loss: list[dict[str, object]] = [
        {
            "point": f"{det}-{c}-{d}",
            "devices": det,
            "coincidences": c,
            "loss_db": d,
            "qber": 0.01,
            "rounds": _rounds(c, d, det),
            "key_length": int(c * 0.3),
            "expected_coincidences": c,
        }
        for det in ("realistic", "perfect")
        for c in (10**5, 10**6)
        for d in (0.0, 10.0, 20.0)
    ]
    loss.append(
        {
            "point": "z",
            "devices": "realistic",
            "coincidences": 10**5,
            "loss_db": 30.0,
            "qber": 0.01,
            "rounds": _rounds(10**5, 30.0, "realistic"),
            "key_length": 0,
        }
    )
    loss.append(
        {
            "point": "m",
            "devices": "realistic",
            "coincidences": 10**6,
            "loss_db": 30.0,
            "qber": 0.01,
            "rounds": _rounds(10**6, 30.0, "realistic"),
            "status": "missing",
            "key_length": "",
        }
    )
    qber: list[dict[str, object]] = [
        {
            "point": f"{det}-{d}-{q}",
            "devices": det,
            "coincidences": 10**6,
            "loss_db": d,
            "qber": q,
            "rounds": _rounds(10**6, d, det),
            "key_length": max(0, int(10**6 * (0.4 - 4 * q))),
        }
        for det in ("realistic", "perfect")
        for d in (0.0, 10.0)
        for q in (0.0, 0.05, 0.12)
    ]
    rounds: list[dict[str, object]] = [
        {
            "point": f"{det}-{d}-{c}",
            "devices": det,
            "coincidences": c,
            "loss_db": d,
            "qber": 0.01,
            "rounds": _rounds(c, d, det),
            "key_length": 0 if (c == 10**4 and det == "realistic") else int(c * 0.3),
            "oracle": (
                "spectral" if (c == 10**6 and d == 10.0 and det == "realistic") else ""
            ),
            "expected_coincidences": c,
        }
        for det in ("realistic", "perfect")
        for d in (0.0, 10.0)
        for c in (10**4, 10**5, 10**6)
    ]
    solvers: list[dict[str, object]] = [
        {
            "point": f"{m}-{a}",
            "method": m,
            "alpha": a,
            "loss_db": 10.0,
            "qber": 0.01,
            "rounds": 16_000_000,
            "key_length": 1000,
            "h_lb": 0.03,
            # fw's bracket is wide, as in the drafts: its band must widen the
            # axis rather than run off it.
            "h_low": 0.25 if m == "fw" else 0.0301,
            "alpha_searched": "False",
        }
        for m in ("fw", "auto")
        for a in (1.001, 1.01)
    ]
    alpha: list[dict[str, object]] = [
        {
            "point": f"{c}-{a}",
            "alpha": a,
            "coincidences": c,
            "rounds": _rounds(c, 10.0, "realistic"),
            "loss_db": 10.0,
            "qber": 0.01,
            "key_length": int(c * (0.3 - abs(a - 1.01))),
            "alpha_searched": "False",
        }
        for c in (10**5, 10**6)
        for a in (1.001, 1.01, 1.03)
    ]
    effects = (
        ("perfect", "", ""),
        ("efficiency", "0.8 per detector", "neumann2022transnational"),
        ("dark", "1.3e-7 per port per round", "joshi2020network"),
        ("visibility", "0.98", "wengerowsky2019submarine"),
    )
    ladder: list[dict[str, object]] = [
        {
            "point": f"{block}-{k:02d}-{effect}",
            "rung": k,
            "effect": effect,
            "value": value,
            "source": source,
            "loss_db": 0.0,
            "rounds": n,
            "coincidences": c,
            "key_length": int(n * rate),
        }
        for block, c, n in (("c1e5", 10**5, 10**6), ("n1e10", None, 10**10))
        for k, ((effect, value, source), rate) in enumerate(
            zip(effects, (0.40, 0.26, 0.2599, 0.21), strict=True)
        )
    ]
    routes: list[dict[str, object]] = [
        {
            "point": f"{route}-N{cutoff}",
            "cutoff": cutoff,
            "route": route,
            "devices": "realistic",
            "coincidences": 10**6,
            "loss_db": 10.0,
            "rounds": 16_000_000,
            "key_length": 2_256_251 + cutoff if route == "encoded" else 2_100_000,
            "snapped_key_length": (
                2_256_240 + cutoff if route == "encoded" else 2_099_990
            ),
            "bracket_status": "counted",
            "rests_on_a_snap": "False",
            "termination": "stagnated" if route == "encoded" else "max_iterations",
            "h_lb": 0.024 if route == "encoded" else 0.022,
            "gap": 0.0000012 if route == "encoded" else 0.002,
        }
        for cutoff in (1, 2)
        for route in ("encoded", "licensed")
    ]
    routes[-1] = {**routes[-1], "status": "missing", "key_length": ""}
    return {
        "routes": _summary("routes", routes),
        "ladder": _summary("ladder", ladder),
        "loss": _summary("loss", loss),
        "qber": _summary("qber", qber),
        "rounds": _summary("rounds", rounds),
        "solvers": _summary("solvers", solvers),
        "alpha": _summary("alpha", alpha),
    }


@pytest.fixture(scope="module")
def written(tmp_path_factory: pytest.TempPathFactory) -> dict[str, str]:
    data = tmp_path_factory.mktemp("keyrate-data")
    for sweep, text in _synthetic().items():
        (data / sweep).mkdir()
        (data / sweep / "summary.csv").write_text(text, encoding="utf-8")
    out = tmp_path_factory.mktemp("views")
    argv = ["--viewmodels", str(SNAPSHOT), "--out", str(out)]
    assert main([*argv, "--keyrate-data", str(data)]) == 0
    return {p.name: p.read_text(encoding="utf-8") for p in out.iterdir()}


def _strip_comments(text: str) -> str:
    return "\n".join(re.sub(r"(?<!\\)%.*", "", line) for line in text.splitlines())


def _tokens(text: str) -> list[str]:
    return _TOKEN.findall(_strip_comments(text))


def _text_mode(text: str) -> str:
    """Return the plain characters TeX reads in text mode.

    Math spans are dropped, and control sequences and escaped characters removed.
    """
    out: list[str] = []
    in_math = False
    for token in _tokens(text):
        if token == "$":
            in_math = not in_math
        elif not in_math and not token.startswith("\\"):
            out.append(token)
    assert not in_math, "an unclosed $"
    return "".join(out)


def _outside_tabular(text: str) -> str:
    return re.sub(r"\\begin\{tabular\}.*?\\end\{tabular\}", "", text, flags=re.DOTALL)


def _outside_tables(text: str) -> str:
    """Drop pgfplots' inline data tables (``table[...] {...}``): data, not text."""
    return re.sub(r"table\[[^\]]*\] \{.*?\n\}", "", text, flags=re.DOTALL)


def test_every_expected_file_is_written(written: dict[str, str]) -> None:
    for name in [*TIKZ, *TABULAR, *KEYRATE, *KEYRATE_TABLES]:
        assert name in written, name
        assert name.replace(".tex", ".caption.tex") in written, name
    assert "views-preamble.tex" in written


def test_every_figure_opens_with_its_header(written: dict[str, str]) -> None:
    for name in [*TIKZ, *TABULAR, *KEYRATE, *KEYRATE_TABLES]:
        head = written[name].splitlines()[:3]
        assert head[0].startswith("% ") and "runs.bbm92_study.views" in head[0]
        assert head[1].startswith("% Source JSON: "), name
        assert head[2].startswith("% Pins: ") and "engine " in head[2], name


@pytest.mark.parametrize("name", [*TIKZ, *KEYRATE])
def test_tikzpicture_is_opened_and_closed(written: dict[str, str], name: str) -> None:
    body = _strip_comments(written[name])
    assert body.count(r"\begin{tikzpicture}") == 1
    assert body.count(r"\end{tikzpicture}") == 1
    assert body.count(r"\begin{axis}") == body.count(r"\end{axis}")


def test_keymap_is_a_table_body(written: dict[str, str]) -> None:
    body = _strip_comments(written["keymap.tex"])
    assert r"\begin{tikzpicture}" not in body and r"\begin{table}" not in body
    assert body.count(r"\begin{tabular}") == body.count(r"\end{tabular}") == 2
    assert r"\toprule" in body and r"\bottomrule" in body
    assert r"\figmain" in body
    assert r"\textbf{pass}" in body and r"{$\times$}" in body and "fail" not in body


def test_the_device_table_cites_every_realistic_value(written: dict[str, str]) -> None:
    """Every realistic value has its source; the channel is the same for both.

    Both sets side by side, every realistic value with its citation.
    """
    body = _strip_comments(written["devices.tex"])
    assert "quantity & symbol & perfect & realistic & source" in body
    rows = [line for line in body.splitlines() if line.endswith(r"\\")][1:-1]
    assert len(rows) == 8
    assert all(r"\parencite[" in row for row in rows)
    assert r"$1.3\times10^{-7}$" in body and "$0.98$" in body
    assert "the same" in body
    caption = written["devices.caption.tex"]
    assert "A round is one emitted pair" in caption and "Not modelled" in caption


def test_braces_balance(written: dict[str, str]) -> None:
    for name, text in written.items():
        depth = 0
        for token in _tokens(text):
            if token.startswith("\\"):
                continue
            for ch in token:
                depth += {"{": 1, "}": -1}.get(ch, 0)
                assert depth >= 0, f"{name}: a closing brace before its opening one"
        assert depth == 0, f"{name}: {depth} unclosed braces"


def test_no_unescaped_underscore_or_ampersand_in_text(written: dict[str, str]) -> None:
    for name, text in written.items():
        plain = _text_mode(_outside_tables(text))
        assert "_" not in plain, f"{name}: text-mode underscore"
        assert "&" not in _text_mode(_outside_tabular(text)), f"{name}: stray &"


def test_the_checks_see_what_they_look_for() -> None:
    assert _text_mode(r"a\_b $x_1$ \\$y_2$ c").split() == ["ab", "c"]
    assert "_" in _text_mode(r"\node {pbs_z};")
    assert "&" in _text_mode(r"a & b")


def test_only_the_whitepaper_fonts(written: dict[str, str]) -> None:
    """Fonts are the whitepaper's two sizes, Fira Sans; nothing is set smaller.

    The preamble's copy of the tokens sits behind the whitepaper's guard, so a
    document that read figures/style.tex first defines them once (round 2).
    """
    preamble = written["views-preamble.tex"]
    assert r"\def\figmain{\figfamily\fontsize{7.5}{9.2}\selectfont}" in preamble
    assert r"\def\figsmall{\figfamily\fontsize{6.25}{7.6}\selectfont}" in preamble
    assert r"\def\figfamily{\fontfamily{FiraSans-TLF}}" in preamble
    guard = preamble.index(r"\ifdefined\figtokensloaded\else")
    assert guard < preamble.index(r"\colorlet{cqAccent}") < preamble.rindex("\\fi\n")
    for name, text in written.items():
        assert not re.search(r"\\cq(tiny|small|font)\b", text), name
        assert not re.search(r"\\(tiny|scriptsize|footnotesize)\b", text), name


def test_lane_colours_only_in_the_swimlane(written: dict[str, str]) -> None:
    for name, text in written.items():
        if name not in ("protocol.tex", "views-preamble.tex"):
            assert "cqLane" not in text, name
    assert "vouch" not in written["views-preamble.tex"]


def test_annotations_are_in_the_captions(written: dict[str, str]) -> None:
    statistics = written["statistics.tex"]
    for phrase in ("further outcomes", "endpoint", r"\addlegendentry"):
        assert phrase not in statistics
    caption = written["statistics.caption.tex"]
    assert "51 acceptance outcomes" in caption and "28 of the 79" in caption
    assert r"\dagger" not in written["optics.tex"]
    assert "view model" not in written["optics.tex"] + written["optics.caption.tex"]
    # A rail no port reads is drawn as loss, and only then; a receiver whose
    # detectors watch both polarisations of their path has none.
    unread = _unread_rails(read_snapshot(SNAPSHOT)["sets"]["realistic"]["optics"])
    assert ("unmonitored (loss)" in written["optics.tex"]) == unread
    assert ("is lost" in written["optics.caption.tex"]) == unread
    assert "unrealised" not in written["keymap.tex"]
    keymap = written["keymap.caption.tex"]
    assert "2 pass, 50 are discarded and 28 never occur" in keymap
    assert "optics figure" not in written["protocol.tex"]
    assert "optics figure" in written["protocol.caption.tex"]
    loss = written["keyrate-loss.caption.tex"]
    assert "An open downward triangle on the bottom axis" in loss
    assert "1 point of the sweep has not been run" in loss


def test_lanes_run_source_to_eve(written: dict[str, str]) -> None:
    body = written["protocol.tex"]
    order = [
        body.index(f"text=cqLane{lane}] at")
        for lane in ("Source", "Alice", "Public", "Bob", "Eve")
    ]
    xs = [float(body[i:].split(" at (")[1].split(",")[0]) for i in order]
    assert xs == sorted(xs)


def test_swimlane_box_text(written: dict[str, str]) -> None:
    body = written["protocol.tex"]
    assert r"\Gamma" not in body and r"\cdots" not in body
    assert r"\mbox{party}" not in body
    assert r"\mbox{channel,} \mbox{arms} \mbox{0}" in body


def test_choice_weights_match_the_records_test_fraction(
    written: dict[str, str],
) -> None:
    data = read_snapshot(SNAPSHOT)
    for name, files in data["sets"].items():
        (choice,) = files["protocol_map"]["label_legend"]["choices"]
        weights = {a["value"]: Fraction(a["weight"]) for a in choice["alphabet"]}
        assert weights["test"] == Fraction(files["preparation"]["test_fraction"]), name
        assert sum(weights.values()) == 1
        if files["record_extract"] is not None:
            assert weights["test"] == Fraction(files["record_extract"]["test_fraction"])
    assert r"gen\,7/8\,$\cdot$\,test\,1/8" in written["protocol.tex"]


def test_povm_is_one_figure_with_both_blocks(written: dict[str, str]) -> None:
    body = written["povm.tex"]
    assert "n = 0" in body and "n = 1" in body
    others = {name for name in written if name.startswith("povm-")}
    assert others == {"povm-compare.tex", "povm-compare.caption.tex"}
    assert "cqCellRule, line width=0.4pt" in body


def test_statistics_panels(written: dict[str, str]) -> None:
    body = written["statistics.tex"]
    assert "xmode=log" in body
    assert "width=4.8cm" in body and "width=4.4cm" in body
    assert "title={honest $p$}" in body


def test_keyrate_skips_a_sweep_without_data() -> None:
    sweeps = {k: parse_summary(v) for k, v in _synthetic().items() if k != "solvers"}
    figures, skipped = render_keyrate(sweeps)
    assert "keyrate-solvers" not in figures
    assert any(message.startswith("F4") for message in skipped)


def test_keyrate_draws_realistic_solid_and_perfect_as_reference(
    written: dict[str, str],
) -> None:
    """F1: realistic lines named at their ends; perfect dashed, the asymptote dotted.

    Two panels: the rate (log) and the rate over the asymptote (linear), each
    with the perfect lines dashed and the asymptote dotted (the level 1 below).
    The blocks are named at the lower panel's line ends (round 2), so the
    legend keys only the line styles; no 0.766^2 reference line.
    """
    body = written["keyrate-loss.tex"]
    assert "ymode=log" in body
    assert body.count(r"\begin{axis}") == 2 and "name=p1" in body
    prefix = "\\addlegendentry{"
    entries = [
        line[len(prefix) : -1] for line in body.splitlines() if line.startswith(prefix)
    ]
    assert not any("coincidences" in e for e in entries)
    references = {
        "perfect devices (same colours)",
        r"perfect{,} $n \rightarrow \infty$",
    }
    assert references | {"no positive key"} == set(entries)
    # The two blocks named at the line ends, under the quantity's heading.
    assert r"{10\textsuperscript{5}};" in body and r"{10\textsuperscript{6}};" in body
    assert body.count("{coincidences};") == 1
    assert "dashdotted" not in body and "0.766" not in body
    assert body.count("densely dashed, line width=0.7pt, forget plot") == 4
    assert body.count("dotted, line width=1.0pt, forget plot") == 2
    assert r"rate $/$ perfect $n \rightarrow \infty$" in body
    caption = written["keyrate-loss.caption.tex"]
    assert "the parameter table" in caption


def test_keyrate_marks_points_without_key_on_the_axis(written: dict[str, str]) -> None:
    """A zero-key point is an open downward triangle near the axis bottom."""
    body = written["keyrate-loss.tex"]
    ymin = float(re.search(r"ymin=([0-9.e+-]+)", body).group(1))  # type: ignore[union-attr]
    marks = re.findall(r"rotate=180.*?coordinates \{\(30\.0,([0-9.e+-]+)\)\}", body)
    assert len(marks) == 1 and ymin < float(marks[0]) < 2 * ymin
    # On F3b's linear axis the triangle sits on the zero line.
    coincidences = written["keyrate-coincidences.tex"]
    assert re.search(r"rotate=180.*?coordinates \{\(10000\.0,0\.0\)\}", coincidences)
    assert "zero line" in written["keyrate-coincidences.caption.tex"]


def test_keyrate_asymptote_is_the_closed_form(written: dict[str, str]) -> None:
    """F3b's level line is the ideal key per coincidence at QBER 1 %, f_EC 1.1."""
    body = written["keyrate-coincidences.tex"]
    level = 7 / 8 * 0.5 * (1 - 2.1 * binary_entropy(0.01))
    assert f"{level!r}" in body
    assert "mark=o, mark size=4.0pt" in body and "mark=square, mark size=3.0pt" in body
    caption = written["keyrate-coincidences.caption.tex"]
    assert "smallest block with a positive key is $10^{5}$" in caption


def test_keyrate_qber_asymptote_stops_at_its_threshold(written: dict[str, str]) -> None:
    """F2's asymptote reaches zero where 1 = (1 + f_EC) h(Q): Q = 10.2 % at 1.1."""
    caption = written["keyrate-qber.caption.tex"]
    assert r"reaches zero at QBER $10.2\,\%$" in caption


def test_keyrate_caption_counts_points_on_another_oracle(
    written: dict[str, str],
) -> None:
    """A point that ran with the spectral oracle is counted in the caption."""
    caption = written["keyrate-rounds.caption.tex"]
    assert "1 point (" in caption and "ran with the spectral linear oracle" in caption
    assert "spectral" not in written["keyrate-loss.caption.tex"]


def test_keyrate_solvers_show_rate_and_solve_time(written: dict[str, str]) -> None:
    """F4: rate per method against alpha, beside each method's solve time."""
    body = written["keyrate-solvers.tex"]
    assert body.count(r"\begin{axis}") == 2
    assert "key rate per round" in body and "solve time (s)" in body
    assert "yticklabels={{fw},{auto}}" in body
    assert "ymode=log" not in body
    caption = written["keyrate-solvers.caption.tex"]
    assert "Left: the key rate per round" in caption


def test_keyrate_ladder_groups_bars_over_a_table(written: dict[str, str]) -> None:
    """F6: one bar per block, and a table of value, source and change per block.

    The blocks are named by their coincidences, the reference block (no
    coincidences label) by its n and drawn in the muted reference grey.
    """
    body = written["keyrate-ladder.tex"]
    assert body.count(r"\addplot[xbar") == 2
    assert "fill=cqSeries1" in body and "fill=cqReference" in body
    assert r"{10\textsuperscript{5}};" in body
    assert r"{\textit{n}\,=\,10\textsuperscript{10}};" in body
    assert "addlegendentry" not in body
    assert "yticklabels={{perfect devices},{+ detector efficiency}" in body
    assert r"\cite{neumann2022transnational}" in body
    assert r"$\eta = 0.8$" in body
    # 0.40 -> 0.26 is -35.0 %; 0.26 -> 0.2599 is under one percent, two digits.
    assert r"$-35.0\,\%$" in body and r"$-0.04\,\%$" in body
    assert "reference" in body
    caption = written["keyrate-ladder.caption.tex"]
    assert "Bob's analyser only" in caption
    assert "not yet checked" not in caption
    assert "blocks of $10^{5}$ expected coincidences" in caption
    assert "the grey bar is a large reference block, $n = 10^{10}$" in caption


def test_keyrate_routes_compares_wpfss_and_fss(written: dict[str, str]) -> None:
    """F5: rate per cutoff, the routes named as the literature names them."""
    body = written["keyrate-routes.tex"]
    assert "xtick={1,2}" in body
    assert r"\addlegendentry{encoded (WPFSS)}" in body
    assert r"\addlegendentry{licensed (FSS)}" in body
    assert "mark=o, mark size=4.8pt" in body
    assert "title={realistic devices}" in body and "key rate per round" in body
    # The convergence gap as a bar above each mark.
    assert "error bars/.cd, y dir=plus, y explicit" in body
    assert "y error plus=e" in body
    caption = written["keyrate-routes.caption.tex"]
    assert "largest convergence gap" in caption and r"$8.3\,\%$" in caption
    assert r"\parencite{zhang2021security}" in caption and "A ring marks" in caption


def test_keyrate_routes_table_has_reported_and_snapped(written: dict[str, str]) -> None:
    body = written["keyrate-routes-table.tex"]
    assert r"\begin{tabular}{llrrrrrr}" in body
    assert "reported & snapped & gap & reported & snapped & gap" in body
    assert (
        r"realistic devices & $1$ & $2\,256\,252$ & $2\,256\,241$ & "
        r"$0.005\,\%$ & $2\,100\,000$$^\dagger$ & $2\,099\,990$ & $8.3\,\%$"
        in body
    )
    assert (
        r" & $2$ & $2\,256\,253$ & $2\,256\,242$ & $0.005\,\%$ & -- & -- & --"
        in body
    )
    caption = written["keyrate-routes-table.caption.tex"]
    assert "In all 3 runs the reported length is the bound on the declared" in caption


def test_escape_covers_the_specials() -> None:
    assert escape("a_b & c%d $e #f {g} |h") == (
        r"a\_b \& c\%d \$e \#f \{g\} \textbar{}h"
    )
    assert escape("perp") == r"$\perp$"
    with pytest.raises(ValueError, match="no LaTeX spelling"):
        escape("\N{SNOWMAN}")


def test_log_axis_beyond_one_decade() -> None:
    assert use_log_axis([7 / 16, 1 / 128])
    assert not use_log_axis([7 / 16, 7 / 32])


# --- the retarder's angle in either form ---------------------------------------


def test_angles_read_as_pi_coefficients_or_radians() -> None:
    """The receiver writes ``{"pi_coefficient": "p/q"}``; floats are radians."""
    assert radians({"pi_coefficient": "1/8"}) == pytest.approx(math.pi / 8)
    assert radians(math.pi / 8) == math.pi / 8
    assert pi_multiple({"pi_coefficient": "1/8"}) == Fraction(1, 8)
    assert pi_multiple(math.pi / 8) == Fraction(1, 8)
    assert pi_multiple(0.3) is None
    exact = "15288567027608731/113187804032455040"
    assert pi_multiple({"pi_coefficient": exact}) == Fraction(exact)


@pytest.mark.parametrize(
    ("retardance", "angle"),
    [
        ({"pi_coefficient": "1"}, {"pi_coefficient": "1/8"}),
        (math.pi, math.pi / 8),
    ],
)
def test_the_plate_prints_the_same_in_either_form(
    retardance: object, angle: object
) -> None:
    plate = {
        "catalogue_id": "C3",
        "parameters": [
            {"name": "retardance", "value": retardance},
            {"name": "angle", "value": angle},
        ],
    }
    assert _parameter_lines(plate) == r"$\lambda/2$\\$\theta{=}22.5^\circ$"


# --- the compact receiver ------------------------------------------------------


def _math_spans(text: str) -> list[str]:
    return re.findall(r"\$([^$]+)\$", _strip_comments(text))


def test_compact_optics_symbols_are_the_device_tables(
    written: dict[str, str],
) -> None:
    """Every symbol the compact figure prints is in the parameter table."""
    figure = written["optics-compact.tex"]
    table = written["devices.tex"]
    symbols = [
        SYMBOLS["basis_split"],
        SYMBOLS["pbs_leak_transmitted"],
        SYMBOLS["pbs_leak_reflected"],
        SYMBOLS["dark_count"],
        SYMBOLS["rotation"],
        *(efficiency_symbol(port) for port in "HVDA"),
    ]
    for symbol in symbols:
        assert symbol in figure, symbol
        assert symbol in table, symbol
    # Symbols, not values: no decimal number is printed in the drawing.
    for span in _math_spans(figure):
        assert not re.search(r"\d\.\d", span), span
    assert r"$\pi/8+\theta/2$" in figure


def test_compact_optics_is_about_half_a_text_width(written: dict[str, str]) -> None:
    """The coordinates span less than 5 cm; labels add well under a centimetre."""
    body = written["optics-compact.tex"]
    xs = [float(x) for x in re.findall(r"\((-?\d+\.\d+),-?\d+\.\d+\)", body)]
    assert max(xs) - min(xs) < 5.0
    assert "line width=0.6pt" in body


def test_compact_optics_caption(written: dict[str, str]) -> None:
    caption = written["optics-compact.caption.tex"]
    assert len(caption.split()) < 60
    assert caption.startswith("Each station's receiver in symbols")
    assert "the parameter table gives their values" in caption
    assert r"The analyser rotation $\theta$ is zero at Alice." in caption


def _unread_rails(optics: dict[str, Any]) -> bool:
    """Whether some station has a mode no port reads."""
    for station in optics.get("stations") or [optics]:
        read = {mode for port in station["ports"] for mode in port["modes"]}
        if any(mode["label"] not in read for mode in station["modes"]):
            return True
    return False


def _whole_path_ports(optics: dict[str, Any]) -> dict[str, Any]:
    """Return ``optics`` with every port reading both modes of its path."""
    out = copy.deepcopy(optics)
    for station in out.get("stations") or [out]:
        by_path: dict[str, list[str]] = {}
        for mode in station["modes"]:
            by_path.setdefault(mode["path"], []).append(mode["label"])
        path_of = {mode["label"]: mode["path"] for mode in station["modes"]}
        for port in station["ports"]:
            port["modes"] = by_path[path_of[port["modes"][0]]]
    return out


def test_leaked_light_reaches_the_other_detector_when_ports_read_whole_paths() -> None:
    """Detectors watching both polarisations: nothing drawn or captioned as lost.

    The light a polarising splitter leaks the wrong way then clicks the other
    detector of the pair (``instances/common/optics.py``, ``PORTS``); the
    single-mode ports of an older snapshot leave it unread, and both figures
    say so.
    """
    data = read_snapshot(SNAPSHOT)["sets"]["realistic"]["optics"]
    whole = _whole_path_ports(data)
    assert not _unread_rails(whole)
    detailed = render_optics(whole, station=1)
    assert "unmonitored" not in detailed.body
    assert "is lost" not in detailed.caption
    assert "clicks on light in any of them" in detailed.caption
    compact = render_optics_compact(whole, station=1)
    assert "(H) to the other detector" in compact.caption
    assert DASH not in compact.body
    single = render_optics_compact(data, station=1)
    expected = "to no detector" if _unread_rails(data) else "to the other detector"
    assert expected in single.caption


def test_compact_optics_without_a_misalignment() -> None:
    """Plates at one angle: the plate prints that angle, and no rotation is named."""
    data = read_snapshot(SNAPSHOT)
    rendered = render_optics_compact(data["sets"]["perfect"]["optics"], station=1)
    assert r"$\pi/8$" in rendered.body and r"\theta" not in rendered.body
    assert "rotation" not in rendered.caption


def test_compact_optics_refuses_joined_beams() -> None:
    """Two beams entering one element is an interferometer, not a tree."""
    modes = [
        {"label": "a_H", "path": "a", "channel": True},
        {"label": "b_H", "path": "b"},
    ]
    elements = [
        {"id": "s1", "catalogue_id": "C1", "column": 0, "support": ["a_H", "b_H"]},
        {"id": "s2", "catalogue_id": "C1", "column": 1, "support": ["a_H", "b_H"]},
    ]
    optics = {"modes": modes, "elements": elements, "ports": []}
    with pytest.raises(ValueError, match="tree of beams"):
        render_optics_compact(optics)


# --- the POVMs side by side ----------------------------------------------------


def test_povm_compare_shares_one_scale_per_photon_number(
    written: dict[str, str],
) -> None:
    body = written["povm-compare.tex"]
    assert "{perfect}" in body and "{realistic}" in body
    # n = 1: perfect H is 0.5 against the realistic 0.5489, the block's largest.
    assert "cqData!91" in body and "cqData!100" in body
    # The dark counts show at n = 0, the times sign set tight to fit the cell.
    assert r"$1.3{\times}10^{-7}$" in body
    assert r"$|0,1\rangle$" in body


def test_povm_compare_caption(written: dict[str, str]) -> None:
    caption = written["povm-compare.caption.tex"]
    assert len(caption.split()) < 80
    assert "normalized efficiencies" in caption
    assert r"$\eta_{\max}/0.99 = 80/99$" in caption
    assert "$0.8$ and $0.7322$ enter as $0.99$ and $0.9061$" in caption
    assert r"Dark counts give the n = 0 click entries ($1.3\times10^{-7}$)" in caption


# --- the two-set snapshot ------------------------------------------------------


def test_snapshot_names_both_sets_and_the_realistic_record() -> None:
    """The realistic set's record extract is its headline run's, at its pin."""
    data = read_snapshot(SNAPSHOT)
    assert set(data["sets"]) == set(SETS)
    realistic = data["sets"]["realistic"]
    assert realistic["files"]["record_extract"] == "realistic/record-extract.json"
    extract = realistic["record_extract"]
    pin = data["snapshot"]["sets"]["realistic"]["engine_pin"]
    assert extract["engine_commit"].startswith(pin)
    assert extract["origin"]["record"] == "loss/realistic-c1e6-L10/record.json.gz"
    _, messages = build(data)
    assert not any("placeholder" in m for m in messages)
    normalization = realistic["preparation"]["normalization"][0]
    assert normalization["factored_loss"] == "80/99"


def test_the_record_extract_reads_the_box_from_the_record() -> None:
    """A record that carries its box needs no bundle manifest."""
    from runs.bbm92_study.views.snapshot import extract_record

    record = {
        "payload": {
            "stages": {
                "acceptance_construction": {
                    "outcomes": ["gen", "test:H|H"],
                    "honest_distribution": {"gen": "1/2", "test:H|H": "1/2"},
                    "endpoint_rule": "bernstein",
                    "box": {
                        "gen": {"lower": "2/5", "upper": "3/5"},
                        "test:H|H": {"lower": "1/4", "upper": "3/4"},
                    },
                }
            },
            "config": {
                "rounds": 10,
                "completeness_budget": "1/1000000",
                "device": {"test_fraction": "1/8"},
            },
            "provenance": {"engine": {"git_commit": "abc"}},
        }
    }
    extract = extract_record(record, None, {"record": "r"})
    assert [o["box_lower"] for o in extract["outcomes"]] == [0.4, 0.25]
    assert [o["box_upper"] for o in extract["outcomes"]] == [0.6, 0.75]
    del record["payload"]["stages"]["acceptance_construction"]["box"]
    with pytest.raises(ValueError, match="no box"):
        extract_record(record, None, {"record": "r"})


def _prepared() -> dict[str, object]:
    normalization = {
        "factored_loss": "80/99",
        "factor_declared": False,
        "applied": True,
        "ports": [
            {"port": "H", "declared_efficiency": "4/5", "compiled_efficiency": "99/100"}
        ],
    }
    return {
        "refused": False,
        "config_digest": "abc",
        "config": {
            "rounds": 10,
            "device": {
                "test_fraction": "1/8",
                "alice_efficiency": {"H": "4/5"},
                "alice_dark_count": {"H": "0"},
            },
        },
        "stations": [
            {
                "index": 0,
                "party": "A",
                "receiver": {"efficiency_record": {"normalization": normalization}},
            }
        ],
    }


def test_snapshot_writes_a_set_and_its_entry(tmp_path: Path) -> None:
    """One call fills one set's folder and its ``snapshot.json`` entry."""
    source = tmp_path / "build"
    source.mkdir()
    for name in VIEW_MODELS:
        (source / name).write_bytes(b'{"x": 1}\r\n')
    (source / "prepare.json").write_text(json.dumps(_prepared()), encoding="utf-8")
    out = tmp_path / "snapshot"
    argv = ["--set", "realistic", "--viewmodels", str(source)]
    argv += ["--prepared", str(source / "prepare.json"), "--out", str(out)]
    argv += ["--frontend-commit", "f", "--engine-pin", "e"]
    assert snapshot_main(argv) == 0
    assert (out / "realistic" / "optics.json").read_bytes() == b'{"x": 1}\n'
    entry = json.loads((out / "snapshot.json").read_text(encoding="utf-8"))["sets"]
    assert entry["realistic"]["record_extract"] is None
    assert entry["realistic"]["engine_pin"] == "e"
    extract = json.loads(
        (out / "realistic" / "preparation-extract.json").read_text(encoding="utf-8")
    )
    device = {"efficiency": {"H": "4/5"}, "dark_count": {"H": "0"}}
    assert extract["device"] == {"A": device}
    assert extract["normalization"][0]["ports"][0]["compiled"] == "99/100"
    assert extract["test_fraction"] == "1/8"


def test_the_ladders_dark_count_label_is_the_realistic_value() -> None:
    """The typeset rung value says what the ladder runs (sweeps.REALISTIC)."""
    from runs.bbm92_study.sweeps import REALISTIC
    from runs.bbm92_study.views.keyrate import RUNG_VALUES

    assert REALISTIC["dark_count"] == Fraction(13, 10**8)
    assert "1.3" in RUNG_VALUES["dark"] and "10^{-7}" in RUNG_VALUES["dark"]


def test_a_rounded_numeral_is_written_out_in_full() -> None:
    """A value rounded to its digits never prints in ``g``'s exponent form.

    The routes caption gave a 100 % shortfall as ``1e+02``.
    """
    assert numeral(100, 2) == "100"
    assert numeral(99.96, 2) == "100"
    assert numeral(2500, 2) == "2500"
    assert numeral(-0.041, 2) == "-0.041"
    assert numeral(22.5) == "22.5"
