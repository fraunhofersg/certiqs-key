"""What a preparation will cost, estimated before it runs: the time, and why.

WHY THIS EXISTS. A preparation is quick at an instance's defaults (about a
second) and can take minutes at the far end of its own parameter domain:
optical_bb84 admits a photon cutoff of 16, prepares cutoff 9 in one to two
minutes and cutoff 10 in ten to twenty. An MCP client gives a tool call about a
minute (Codex's default), so a preparation that may take long runs as a
background job, like a run. The long expected runtime (with reason) is
transparent to any user, so the cost is estimated BEFORE the preparation, from
the configuration alone, and the estimate -- the expected time and the
parameters driving it -- is stated in every reply that concerns the preparation
(``prepare``,
``start_run``, ``run_status``, ``describe_instance``, ``list_instances``).

CHEAP BY CONSTRUCTION. The estimate reads the receiver requests an instance
would construct (its optional ``receiver_requests(config)``: the lowering of a
protocol document, or an instance's own request builder), never constructs
them, and does arithmetic on a few integers per station. It decides nothing:
an instance without ``receiver_requests``, or a configuration its lowering
refuses, is estimated ``unknown`` and prepared in the call as before (a
refusal is fast). A configuration that will not finish in practice is NOT
refused: it runs in the background and the reply says it
will not finish and that a smaller cutoff or window would.

THE MODEL. A preparation's cost is its optical receivers' (a Band-A protocol
constructs none). Per station, with ``K`` detector ports, ``k`` channel input
modes, photon cutoff ``N`` and deepest photon number ``m`` (the cutoff, or the
deepest exact or tail window), and ``dim(n) = C(n + k - 1, k - 1)``:

    station = PROBE * (3^(K - 4) * WINDOW(sum_{n <= m} dim(n)^2)
                       + CUTOFF(sum_{n <= N} dim(n)))
    seconds = BASE + sum of the stations + JOINT(sum of the stations' CUTOFF
              arguments, two or more stations)

WINDOW is the receiver's work, the measure of ``instances/declared/limits.py``
(``receiver_work = 3^K * sum dim(n)^2``) read relative to four ports; CUTOFF
the exact arithmetic of the reductions and the honest model on the
photon-number space up to the cutoff; JOINT the docking of two or more
stations' factors. None is linear, so each is a piecewise power law through
measured points (log-log interpolation; past the last point the last
segment's slope extrapolates, and the reply says ``extrapolated``). The terms
add: cutoff and window were measured together (the grid below), and the sum
of the two terms reproduces the combined points within the spread of the
machine's load. A probe's source modes are not counted in ``k``; a station
with a probe costs PROBE times as much plus PROBE_BASE (measured on the
passive receiver with a two-mode thermal probe).

THE CALIBRATION. This machine (Windows 11, the venv's Python 3.14.6, the
engine at the time of measuring), each point one ``prepare_surface`` call in a fresh
process, the import excluded, measured while other processes loaded the
machine; an unloaded machine was 1.5 to 2.3 times faster (in brackets, where
measured). Seconds:

- optical_bb84 (K = 4, k = 2), cutoff N / window m: 1/2 0.47, 1/5 0.62,
  1/7 0.46, 1/9 1.95 [0.81], 1/10 14.7 [8.8], 1/11 [115]; 3/4 0.80,
  3/6 0.85, 3/8 1.09, 3/9 2.30, 3/10 15.2; 4/5 1.17; 5/6 1.91, 5/8 2.04,
  5/9 3.34, 5/10 15.6; 6/7 2.99; 7/8 5.16 [2.8], 7/9 6.13, 7/10 18.9;
  8/9 20.1 [8.6], 8/10 29.6; 9/10 86.8 [55]; 10/11 [638];
  12 and 13 did not finish in 600 s and 400 s at cutoff 1;
- bbm92 (two such stations), both cutoffs N / windows m: 2/3 1.40,
  3/4 6.12, 3/5 5.91, 4/5 23.1; cutoffs 1 and 6, windows 2 and 7: 14.8;
- decoy_bb84's station: 3/4 1.82, 5/6 2.84, 5/8 3.04, 7/8 5.85 (its source
  cutoff does not matter: 100 costs 0.2 s);
- the port-Gram documents at N = 1, window 2: K = 8 1.1 s, 10 10.9 s,
  which the 3^(K - 4) factor over-estimates by a factor of a few.

WINDOW, CUTOFF and JOINT are these points less BASE and the other terms; the
unloaded 1/11 and 10/11 are scaled by the measured load ratio (1.7).

HEADROOM. ``prepare`` answers in the call only when SAFETY_FACTOR times the
estimate fits the budget (20 s by default, so an estimate of at most 10 s).
Over every point above the time taken is at most 1.3 times the estimate
(decoy_bb84 at 3/4, whose source preparation BASE only roughly covers); the
estimate errs high elsewhere, up to 2.4 times at the smallest points and 1.8
for bbm92 at cutoffs 1 and 6. So a preparation answered in the call took at
most 1.3 x 10 = 13 s under the load above: inside the 20 s budget, and under
a quarter of Codex's 60 s tool timeout. A machine 4.6 times slower than this
one under load could pass 60 s in the call.

A MAINTENANCE COST (PRINCIPLES.md section 9). The calibration goes stale when
the engine's speed changes -- a faster receiver, a slower reduction -- and no
check catches that: a stale table only makes the stated time wrong, never a
number of the key rate. It is worth that cost because a client's tool call
fails after about a minute with no explanation, and because the user is told
how long the preparation will take and why before waiting. Re-measure the
points above when a preparation's speed visibly changes, and rewrite them
here.
"""

from __future__ import annotations

import itertools
import math
import os
from collections.abc import Mapping, Sequence
from typing import Any, Final

__all__ = [
    "BUDGET_ENV",
    "CAP_SECONDS",
    "DEFAULT_BUDGET_S",
    "PRACTICAL_SECONDS",
    "SAFETY_FACTOR",
    "budget_seconds",
    "duration",
    "estimate_preparation",
    "statement",
]

#: The environment variable that sets the budget, in seconds.
BUDGET_ENV: Final[str] = "CERTIQS_KEY_PREPARE_BUDGET_S"
#: A preparation that may take longer runs in the background: a third of
#: Codex's 60 s tool timeout.
DEFAULT_BUDGET_S: Final[float] = 20.0
#: ``prepare`` answers in the call only when this many times the estimate
#: fits the budget (HEADROOM, above).
SAFETY_FACTOR: Final[float] = 2.0
#: Above this the reply says the preparation will not finish in practice.
PRACTICAL_SECONDS: Final[float] = 86_400.0
#: The largest figure stated; beyond it the reply says "more than" this.
CAP_SECONDS: Final[float] = 30 * 86_400.0

#: Every preparation's own seconds: a first call's warm-up, compilation,
#: tables, and a ``wcp_decoy`` source's preparation.
BASE_SECONDS: Final[float] = 1.0
#: A station with a probe (declared source modes): its terms times PROBE_FACTOR,
#: plus PROBE_BASE seconds (the passive receiver with a two-mode thermal probe).
PROBE_FACTOR: Final[float] = 6.0
PROBE_BASE: Final[float] = 0.6

#: WINDOW: ``sum_{n <= m} dim(n)^2`` on two channel modes at four ports ->
#: seconds (windows 2, 6, 7, 9, 10, 11 at cutoff 1).
WINDOW_POINTS: Final[tuple[tuple[float, float], ...]] = (
    (14.0, 0.05),
    (140.0, 0.05),
    (204.0, 0.05),
    (385.0, 1.5),
    (506.0, 14.2),
    (650.0, 200.0),
)
#: CUTOFF: ``sum_{n <= N} dim(n)`` on two channel modes -> seconds (cutoffs
#: 1, 3, 4, 5, 6, 7, 8, 9, 10).
CUTOFF_POINTS: Final[tuple[tuple[float, float], ...]] = (
    (3.0, 0.01),
    (10.0, 0.30),
    (15.0, 0.67),
    (21.0, 1.41),
    (28.0, 2.49),
    (36.0, 4.3),
    (45.0, 18.2),
    (55.0, 72.0),
    (66.0, 860.0),
)
#: JOINT: the sum of the stations' ``sum_{n <= N} dim(n)`` -> seconds (bbm92,
#: both cutoffs 1, 2, 3, 4).
JOINT_POINTS: Final[tuple[tuple[float, float], ...]] = (
    (6.0, 0.1),
    (12.0, 0.71),
    (20.0, 5.0),
    (30.0, 21.2),
)

_BASIS: Final[str] = (
    "calibrated on preparations of the packaged instances on the engine's "
    "reference machine under load (runs/facade/estimate.py): an order of "
    "magnitude, not a promise"
)
#: What one preparation's estimate covers (a run job says its own, jobs.py).
_COVERS: Final[str] = (
    "this preparation only; a run job prepares once more itself (a prepare "
    "call's result is not reused by the run) and then solves"
)


def budget_seconds() -> float:
    """Return the budget: ``$CERTIQS_KEY_PREPARE_BUDGET_S``, or 20 s."""
    try:
        return max(0.0, float(os.environ.get(BUDGET_ENV, DEFAULT_BUDGET_S)))
    except ValueError:
        return DEFAULT_BUDGET_S


def duration(seconds: float) -> str:
    """Return ``seconds`` in the unit a person reads: s, min, h or days."""
    for unit, size, below in (
        ("s", 1.0, 90.0),
        ("min", 60.0, 90 * 60.0),
        ("h", 3600.0, 48 * 3600.0),
    ):
        if seconds < below:
            return f"about {seconds / size:.2g} {unit}"
    return f"about {seconds / 86_400.0:.2g} days"


def statement(estimate: Mapping[str, Any]) -> str:
    """Return the sentence the user is told before waiting: how long, and why."""
    if estimate.get("expected_seconds") is None:
        return f"How long preparing takes is {estimate.get('why')}."
    text = f"Preparing is expected to take {estimate['duration']} ({estimate['why']})."
    advice = estimate.get("advice")
    return f"{text} {advice}" if advice else text


def _interpolate(points: Sequence[tuple[float, float]], x: float) -> tuple[float, bool]:
    """Return the piecewise power law through ``points`` at ``x``, and if past them.

    Log-log. Below the first point it is the first value; past the last, the
    last segment's slope extrapolates and the flag is set. Monotone, as the
    points are.
    """
    if x <= points[0][0]:
        return points[0][1], False
    segment = points[-2:]
    for left, right in itertools.pairwise(points):
        if x <= right[0]:
            segment = (left, right)
            break
    (x0, y0), (x1, y1) = segment
    slope = math.log(y1 / y0) / math.log(x1 / x0)
    try:
        value: float = y0 * (x / x0) ** slope
    except OverflowError:
        value = math.inf
    return value, x > points[-1][0]


def _station(request: Any) -> dict[str, Any]:
    """Return one receiver request's cost drivers and its terms."""
    from instances.declared.limits import photon_blocks, receiver_work

    ports = len(request.port_map.entries)
    modes = len(request.input_modes.channel)
    cutoff = int(request.photon_cutoff)
    deepest = max(
        [
            cutoff,
            *(int(value) for value in dict(request.exact_window).values()),
            *(int(value) for value in dict(request.tail_window or {}).values()),
        ]
    )
    blocks = photon_blocks(modes, deepest)
    below = float(sum(blocks[: cutoff + 1])) or 1.0
    probe = bool(request.input_modes.source)
    factor = PROBE_FACTOR if probe else 1.0
    window, window_past = _interpolate(
        WINDOW_POINTS, float(sum(block * block for block in blocks))
    )
    cut, cut_past = _interpolate(CUTOFF_POINTS, below)
    return {
        "ports": ports,
        "channel_modes": modes,
        "photon_cutoff": cutoff,
        "deepest_photon_number": deepest,
        "receiver_work": receiver_work(ports, modes, deepest),
        "probe": probe,
        "window_s": factor * 3.0 ** (ports - 4) * window,
        "cutoff_s": factor * cut + (PROBE_BASE if probe else 0.0),
        "extrapolated": window_past or cut_past,
        "states_below_cutoff": below,
    }


def _why(
    stations: Sequence[Mapping[str, Any]], joint: float, extrapolated: bool
) -> str:
    """Name what drives the time, in the words of the parameters' meanings."""
    if not stations:
        return (
            "no optical receiver to construct (a directly declared measurement): "
            "the preparation is compilation and tables only"
        )
    parts = []
    for index, station in enumerate(stations):
        name = "the receiver" if len(stations) == 1 else f"station {index + 1}"
        parts.append(
            f"{name}: photon cutoff {station['photon_cutoff']}, deepest photon "
            f"number {station['deepest_photon_number']} (cutoff or exact/tail "
            f"window), {station['ports']} detector ports"
            + (", a probe" if station["probe"] else "")
        )
    terms = {
        "the photon cutoff (exact arithmetic on every photon number up to it)": sum(
            station["cutoff_s"] for station in stations
        ),
        "the deepest window and the 3^ports click patterns of the receiver": sum(
            station["window_s"] for station in stations
        ),
        "the stations' joint photon-number space": joint,
    }
    driver = max(terms, key=lambda name: terms[name])
    text = "; ".join(parts) + f". Mostly driven by {driver}"
    if extrapolated:
        text += (
            ". Extrapolated past the measured range (photon cutoff 10, window "
            "11 on two modes): the figure is only a trend"
        )
    return text


def estimate_preparation(s: Any, config: Any) -> dict[str, Any]:
    """Return the expected time of ``s.preparation(config)``, and the reason.

    ``expected_seconds`` (numeric; ``None`` where unknown: an instance without
    ``receiver_requests``, a configuration its lowering refuses; at most
    :data:`CAP_SECONDS`, ``capped`` above it), ``duration`` (the same in human
    units, "more than ..." when capped), ``why``, ``extrapolated``,
    ``practical`` (and ``advice`` when it is not), ``budget_seconds``,
    ``background`` (whether ``prepare`` runs it as a job: the estimate times
    :data:`SAFETY_FACTOR` past the budget), ``covers``, ``basis`` and the
    ``stations``' drivers. Never raises, never prepares.
    """
    budget = budget_seconds()
    read = getattr(s, "receiver_requests", None)
    unknown: dict[str, Any] = {
        "expected_seconds": None,
        "duration": "unknown",
        "extrapolated": False,
        "capped": False,
        "practical": True,
        "budget_seconds": budget,
        "background": False,
        "covers": _COVERS,
        "basis": _BASIS,
    }
    if read is None:
        return {
            **unknown,
            "why": "unknown: this instance does not state its receivers before "
            "preparing; it is prepared in the call",
        }
    try:
        stations = [_station(request) for request in tuple(read(config))]
    except Exception as failure:  # the preparation reports any refusal itself
        return {
            **unknown,
            "why": f"unknown: the configuration does not lower "
            f"({type(failure).__name__}); the preparation reports why",
        }
    joint, joint_past = (
        _interpolate(
            JOINT_POINTS,
            sum(station["states_below_cutoff"] for station in stations),
        )
        if len(stations) > 1
        else (0.0, False)
    )
    extrapolated = joint_past or any(station["extrapolated"] for station in stations)
    seconds = (
        BASE_SECONDS
        + joint
        + sum(station["window_s"] + station["cutoff_s"] for station in stations)
    )
    capped = seconds > CAP_SECONDS
    expected = CAP_SECONDS if capped else float(f"{seconds:.2g}")
    value: dict[str, Any] = {
        "expected_seconds": expected,
        "duration": (
            "more than " + duration(CAP_SECONDS).removeprefix("about ")
            if capped
            else duration(expected)
        ),
        "why": _why(stations, joint, extrapolated),
        "extrapolated": extrapolated,
        "capped": capped,
        "practical": expected <= PRACTICAL_SECONDS,
        "budget_seconds": budget,
        "background": expected * SAFETY_FACTOR > budget,
        "covers": _COVERS,
        "basis": _BASIS,
        "stations": [
            {
                key: station[key]
                for key in (
                    "ports",
                    "channel_modes",
                    "photon_cutoff",
                    "deepest_photon_number",
                    "receiver_work",
                    "probe",
                )
            }
            for station in stations
        ],
    }
    if not value["practical"]:
        value["advice"] = (
            "At this size it will not finish in practice: choose a smaller "
            "photon cutoff or window. It is not refused, and runs in the "
            "background if started."
        )
    return value
