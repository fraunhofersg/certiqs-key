"""Every sweep of the BBM92 study, declared once, as data.

A sweep is a named tuple of points; a point is a set of overrides of the bbm92
document's defaults plus the study's two opt-in choices: whether alpha is
searched (:mod:`certiqs_key.runs.alpha_search`) and whether lambda_EC is
estimated (:mod:`certiqs_key.runs.error_correction`). Running a point is
:mod:`runs.bbm92_study.run`'s business, so this module builds configurations and
runs nothing.

The figure ids (F1, F2, ...) are the study's names for its figures; each
sweep's docstring says what its figure shows. A sweep that cannot run yet is
marked ``blocked`` with the reason; the runner refuses it unless told
otherwise.

QUANTITIES. ``loss_db`` is the TOTAL symmetric channel loss, split half per arm:
each arm's transmittance is ``10^(-loss_db / 20)``. ``qber`` is the
depolarising error of the Werner state, ``(1 - v) / 2`` per key basis, set
through ``visibility``. ``rounds`` is ``n``, the channel uses, set from a
point's expected ``coincidences`` (:func:`rounds_for`); the exact expected
coincidences are a derived column (:mod:`runs.bbm92_study.summarize`).
"""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field, fields, replace
from fractions import Fraction
from typing import Any

from certiqs_key.runs.config import AdvancedSolverSettings, RunConfig, SolverSettings

__all__ = [
    "SWEEPS",
    "Point",
    "Sweep",
    "configure",
    "per_arm_transmittance",
    "rounds_for",
]

PORTS = ("H", "V", "D", "A")
#: The study's solver: the accepted opt-in portfolio.
AUTO = SolverSettings(method="auto", budget_seconds=600)


def per_arm_transmittance(loss_db: float) -> Fraction:
    """Return one arm's transmittance for a total symmetric loss in dB, exactly.

    The float ``10^(-loss_db/20)`` converted exactly, so the configuration
    states the value the float denotes rather than a rounding of it.
    """
    return Fraction(10.0 ** (-loss_db / 20.0))


@dataclass(frozen=True)
class Point:
    """One configuration of the study, by its overrides of the defaults."""

    #: Unique within its sweep; also the point's folder name.
    id: str
    #: The axis values, as plotted and as summarised (JSON scalars).
    labels: Mapping[str, Any]
    model: Mapping[str, Any] = field(default_factory=dict)
    device: Mapping[str, Any] = field(default_factory=dict)
    rounds: int = 100_000_000
    solver: SolverSettings = AUTO
    #: A fixed alpha, or ``None`` to search it.
    alpha: float | None = None
    #: Take alpha from the search of this sibling point (same sweep) instead of
    #: searching: the licensed route's pairwise solve costs too much to repeat
    #: for every alpha a search evaluates, so a licensed point uses the alpha
    #: its encoded twin found. The runner runs such points after the others.
    alpha_from: str | None = None
    #: Estimate lambda_EC with this f_EC, or ``None`` to keep the declared one.
    f_ec: float | None = 1.1
    #: Run parameters beyond alpha and lambda_EC, as ``{name: value}``: a
    #: RunConfig field (e.g. ``reference_enclosure``) or a key-length
    #: parameter.
    parameters: Mapping[str, Any] = field(default_factory=dict)

    def as_payload(self) -> dict[str, Any]:
        """Return the point as JSON, as the runner records it."""
        return {
            "id": self.id,
            "labels": dict(self.labels),
            "model": {k: str(v) for k, v in self.model.items()},
            "device": {k: _wire(v) for k, v in self.device.items()},
            "rounds": self.rounds,
            "solver": self.solver.as_payload(),
            "alpha": (
                self.alpha
                if self.alpha is not None
                else f"from {self.alpha_from}"
                if self.alpha_from
                else "search"
            ),
            "f_ec": self.f_ec,
            "parameters": {k: str(v) for k, v in self.parameters.items()},
        }


def _wire(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {k: str(v) for k, v in value.items()}
    return str(value)


@dataclass(frozen=True)
class Sweep:
    """A named set of points: one figure's data."""

    name: str
    figure: str
    title: str
    points: Callable[[], tuple[Point, ...]]
    #: Why the sweep cannot run yet, or ``None``.
    blocked: str | None = None


def configure(base: RunConfig, point: Point) -> RunConfig:
    """Return ``base`` with ``point``'s overrides applied, lambda_EC aside."""
    model = dict(base.model)
    model.update(point.model)
    device = dict(base.device)
    device.update(point.device)
    config = base.with_(
        model=model, device=device, rounds=point.rounds, solver=point.solver
    )
    if point.parameters:
        # A name RunConfig declares (the snap settings) is set there; any
        # other is a key-length parameter.
        own = {f.name for f in fields(config)}
        on_config = {k: v for k, v in point.parameters.items() if k in own}
        on_parameters = {k: v for k, v in point.parameters.items() if k not in own}
        if on_config:
            config = config.with_(**on_config)
        if on_parameters:
            config = config.with_(
                parameters=replace(config.parameters, **on_parameters)
            )
    if point.alpha is not None:
        config = config.with_(alpha=point.alpha)
    return config


# --------------------------------------------------------------------------
# Building blocks
# --------------------------------------------------------------------------


def _channel(loss_db: float, qber: float) -> dict[str, Any]:
    t = per_arm_transmittance(loss_db)
    return {
        "alice_transmittance": t,
        "bob_transmittance": t,
        "visibility": Fraction(1) - 2 * Fraction(str(qber)),
    }


def _both(name: str, value: Any) -> dict[str, Any]:
    return {f"alice_{name}": value, f"bob_{name}": value}


def _per_port(value: Fraction | Mapping[str, Fraction]) -> dict[str, Fraction]:
    if isinstance(value, Mapping):
        return {p: Fraction(value[p]) for p in PORTS}
    return {p: Fraction(value) for p in PORTS}


def _tag(value: float) -> str:
    return f"{value:g}".replace(".", "p").replace("-", "m").replace("+", "")


#: The realistic source and receivers, each value checked against a
#: registered source, its locator given beside the value. The
#: values are a composite of reported ones, not one experiment's:
#: - efficiency 0.8 per detector (neumann2022transnational p.14), with the
#:   measured pair 54 % and 59 % (wengerowsky2019submarine p.3) kept as the
#:   ratio of the V and A ports to the H and D ports;
#: - dark count 1.3e-7 per port per round: about 1 kHz (joshi2020network p.8)
#:   times the coincidence window of about 130 ps (p.2), the exact product
#:   for the ideal pair, stated as such. A round is one
#:   emitted pair, and DCR x window is the chance that a dark click lands in
#:   the window around the partner's photon: the ratio of dark-made to true
#:   coincidences is the same as in a CW coincidence count;
#: - basis split T = 56 % (joshi2020network p.8);
#: - PBS leaks (joshi2020network p.8): 1e-3 of the vertical polarization
#:   transmitted (Tp:Ts > 1000:1 at the transmitted port) and 1e-2 of the
#:   horizontal reflected (Rs:Rp 100:1, the better end of the reported 20:1 to
#:   100:1 at the reflected port); the leaked light clicks the other detector
#:   of the pair, since each detector watches both polarizations of its path;
#: - Bob's misalignment sin^2 theta = 0.004 of polarization rotation
#:   (neumann2022transnational p.5);
#: - source visibility 0.98 (wengerowsky2019submarine p.3, DA basis; 97 % in
#:   HV), the Werner state's, entering only the honest statistics: the source
#:   is untrusted. It stands in for all source noise (multi-pair accidentals
#:   included, which source_model ideal_pair does not emit) and is held fixed
#:   across loss.
REALISTIC = {
    "efficiency": Fraction(4, 5),
    "dark_count": Fraction(13, 10**8),
    "mismatch_ratio": Fraction(54, 59),
    "basis_split": Fraction(56, 100),
    "pbs_leak_transmitted": Fraction(1, 1000),
    "pbs_leak_reflected": Fraction(1, 100),
    "misalignment_rad": Fraction(math.asin(math.sqrt(0.004))),
    "visibility": Fraction(98, 100),
}


def _effects() -> dict[str, tuple[dict[str, Any], dict[str, Any]]]:
    """Return each imperfection as its (model, device) overrides.

    The ladder adds them one by one; the realistic set is all of them.
    """
    eff = REALISTIC["efficiency"]
    low = eff * REALISTIC["mismatch_ratio"]
    mismatch = {"H": eff, "V": low, "D": eff, "A": low}
    # half_wave_angle is in units of pi and pi/8 is ideal; a plate turned by
    # t rotates the polarization by 2t, so a rotation theta is a plate offset
    # of theta / 2.
    hwp = Fraction(1, 8) + REALISTIC["misalignment_rad"] / 2 / Fraction(math.pi)
    return {
        "perfect": ({}, {}),
        "visibility": ({"visibility": REALISTIC["visibility"]}, {}),
        "efficiency": ({}, {**_both("efficiency", _per_port(eff))}),
        "dark": ({}, {**_both("dark_count", _per_port(REALISTIC["dark_count"]))}),
        "mismatch": ({}, {**_both("efficiency", _per_port(mismatch))}),
        "basis-split": ({}, {**_both("basis_split", REALISTIC["basis_split"])}),
        "extinction": (
            {},
            {
                **_both("pbs_leak_transmitted", REALISTIC["pbs_leak_transmitted"]),
                **_both("pbs_leak_reflected", REALISTIC["pbs_leak_reflected"]),
            },
        ),
        # BOB'S PLATE ONLY. The same plate M at both stations leaves the source
        # state alone: (A x B)|Phi+> = (A B^T x 1)|Phi+>, and a half-wave
        # plate's Jones matrix is real orthogonal, so M M^T = 1. A misalignment
        # on both sides costs nothing; the first draft did that and the rung
        # moved the key by 0.01 %.
        "misalignment": ({}, {"bob_half_wave_angle": hwp}),
    }


def _realistic_device() -> dict[str, Any]:
    """Return both stations' realistic receivers: every device effect."""
    device: dict[str, Any] = {}
    for _model, d in _effects().values():
        device.update(d)
    return device


# --------------------------------------------------------------------------
# The sweeps (figure ids of the plan, section 3)
# --------------------------------------------------------------------------
#
# ROUNDS ARE SET BY COINCIDENCES.
# A round is one emitted pair; the registered BBM92 experiments collect about
# 1e6 coincidences per key block (wengerowsky2019submarine p.3: 257 per second;
# neumann2022transnational p.16: about 9 per second over 28 h active). So a
# point names its expected coincidences, and n follows from the loss and the
# devices (:func:`rounds_for`); the summary's ``expected_coincidences`` is
# the exact count. 1e5 coincidences is explored as well, and included
# where it still gives key.
#
# TWO DEVICE SETS, ONE CHANNEL: every plot comparing realistic with perfect
# devices uses the same channel model. ``realistic``
# is every value of :data:`REALISTIC`, source visibility included;
# ``perfect`` is the ladder's top rung, a perfect source (QBER 0) and
# receivers. The loss, rounds and routes sweeps run
# each point with both at the same loss; the QBER sweep varies the source
# visibility for both, so there the sets differ in the receivers only. The
# perfect lines carry the closed-form asymptote (runs/bbm92_study/asymptote.py).

QBER_BASE = 0.01
HEADLINE_COINCIDENCES = 10**6
HEADLINE_LOSS_DB = 10.0
DEVICES = ("realistic", "perfect")
#: The source QBER of each set: the realistic visibility's, and 0.
SOURCE_QBER = {"realistic": QBER_BASE, "perfect": 0.0}
assert Fraction(1) - 2 * Fraction(str(QBER_BASE)) == REALISTIC["visibility"]


def mean_efficiency(devices: str) -> float:
    """Return a station's detection efficiency averaged over its four ports.

    Each basis has one port at the full efficiency and one at the mismatched
    one, so the average does not depend on the basis split.
    """
    if devices != "realistic":
        return 1.0
    eff = float(REALISTIC["efficiency"])
    return eff * (1.0 + float(REALISTIC["mismatch_ratio"])) / 2.0


def coincidence_probability_estimate(loss_db: float, devices: str) -> float:
    """Return the probability that both stations click, to the leading order.

    ``eta_A eta_B e^2`` with ``e`` the mean port efficiency, dark counts left
    out: at 1.3e-7 per port they move it by less than a part in a thousand
    below 30 dB. Only the choice of n uses it; the figures use the exact count.
    """
    return float(10.0 ** (-loss_db / 10.0)) * mean_efficiency(devices) ** 2


def rounds_for(coincidences: float, loss_db: float, devices: str) -> int:
    """Return n for ``coincidences`` expected coincidences, to two digits."""
    n = coincidences / coincidence_probability_estimate(loss_db, devices)
    return int(float(f"{n:.2g}"))


def _device(kind: str) -> dict[str, Any]:
    return _realistic_device() if kind == "realistic" else {}


def _power_tag(value: float) -> str:
    exponent = math.log10(value)
    if abs(exponent - round(exponent)) < 1e-9:
        return f"1e{round(exponent)}"
    return f"{value:.0e}".replace("+0", "").replace("+", "")


LOSSES_DB = (0.0, 4.0, 8.0, 10.0, 12.0, 16.0, 20.0, 24.0, 28.0, 32.0)
#: The study's three blocks, shared by the loss, alpha and ladder sweeps so a
#: colour names the same block in every figure; 3e4 is the smallest block on
#: the rounds grid with a positive realistic key (1e4 certifies none).
BLOCK_COINCIDENCES = (3 * 10**4, 10**5, 10**6)
LOSS_COINCIDENCES = BLOCK_COINCIDENCES


def _loss_points() -> tuple[Point, ...]:
    """F1: key rate against loss, a line per block of expected coincidences."""
    return tuple(
        Point(
            id=f"{kind}-c{_power_tag(c)}-L{_tag(loss)}",
            labels={
                "devices": kind,
                "coincidences": c,
                "loss_db": loss,
                "rounds": (n := rounds_for(c, loss, kind)),
                "qber": SOURCE_QBER[kind],
            },
            model=_channel(loss, SOURCE_QBER[kind]),
            device=_device(kind),
            rounds=n,
        )
        for kind in DEVICES
        for c in LOSS_COINCIDENCES
        for loss in LOSSES_DB
    )


QBERS = (0.0, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.10)
QBER_LOSSES_DB = (0.0, 10.0, 20.0)


def _qber_points() -> tuple[Point, ...]:
    """F2: key rate against the source QBER, a line per loss, headline block.

    Both sets sweep the source visibility, so they differ in the receivers.
    """
    c = HEADLINE_COINCIDENCES
    return tuple(
        Point(
            id=f"{kind}-L{_tag(loss)}-Q{_tag(q)}",
            labels={
                "devices": kind,
                "loss_db": loss,
                "qber": q,
                "coincidences": c,
                "rounds": (n := rounds_for(c, loss, kind)),
            },
            model=_channel(loss, q),
            device=_device(kind),
            rounds=n,
        )
        for kind in DEVICES
        for loss in QBER_LOSSES_DB
        for q in QBERS
    )


ROUNDS_COINCIDENCES = (
    10**4, 3 * 10**4, 10**5, 3 * 10**5, 10**6, 3 * 10**6, 10**7, 10**8, 10**9
)
ROUNDS_LOSSES_DB = (0.0, 10.0, 20.0, 30.0)


def _rounds_points() -> tuple[Point, ...]:
    """F3 and F3b: key rate against n and per coincidence, a line per loss.

    The grid is in coincidences, the same for every loss, so the F3b lines
    share their x values and their overlap is a comparison point by point.
    """
    return tuple(
        Point(
            id=f"{kind}-L{_tag(loss)}-c{_power_tag(c)}",
            labels={
                "devices": kind,
                "loss_db": loss,
                "coincidences": c,
                "rounds": (n := rounds_for(c, loss, kind)),
                "qber": SOURCE_QBER[kind],
            },
            model=_channel(loss, SOURCE_QBER[kind]),
            device=_device(kind),
            rounds=n,
        )
        for kind in DEVICES
        for loss in ROUNDS_LOSSES_DB
        for c in ROUNDS_COINCIDENCES
    )


def _headline(kind: str = "realistic") -> dict[str, Any]:
    """Return the headline point's labels: 10 dB, 1e6 coincidences."""
    return {
        "devices": kind,
        "loss_db": HEADLINE_LOSS_DB,
        "coincidences": HEADLINE_COINCIDENCES,
        "rounds": rounds_for(HEADLINE_COINCIDENCES, HEADLINE_LOSS_DB, kind),
        "qber": SOURCE_QBER[kind],
    }


SOLVER_METHODS = ("fw", "pairwise", "auto")
SOLVER_ALPHAS = (1.001, 1.003, 1.01, 1.05)


def _solver_points() -> tuple[Point, ...]:
    """F4: the solver methods at the realistic headline point, fixed alphas."""
    head = _headline()
    points = []
    for method in SOLVER_METHODS:
        for alpha in SOLVER_ALPHAS:
            solver = (
                AUTO
                if method == "auto"
                else SolverSettings.from_choices(
                    method=method, max_iterations=2000, budget_seconds=1800
                )
            )
            points.append(
                Point(
                    id=f"{method}-a{_tag(alpha - 1)}",
                    labels={"method": method, "alpha": alpha, **head},
                    model=_channel(HEADLINE_LOSS_DB, QBER_BASE),
                    device=_realistic_device(),
                    rounds=head["rounds"],
                    solver=solver,
                    alpha=alpha,
                )
            )
    return tuple(points)


ALPHA_GRID = tuple(1.0 + 10 ** (-k / 4) for k in range(4, 21))  # 1.1 .. 1 + 1e-5
ALPHA_COINCIDENCES = BLOCK_COINCIDENCES


def _alpha_points() -> tuple[Point, ...]:
    """F7: key length against alpha at the headline loss, a line per block."""
    return tuple(
        Point(
            id=f"c{_power_tag(c)}-a{_tag(alpha - 1)}",
            labels={
                "alpha": alpha,
                "coincidences": c,
                "rounds": (n := rounds_for(c, HEADLINE_LOSS_DB, "realistic")),
                "devices": "realistic",
                "loss_db": HEADLINE_LOSS_DB,
                "qber": QBER_BASE,
            },
            model=_channel(HEADLINE_LOSS_DB, QBER_BASE),
            device=_realistic_device(),
            rounds=n,
            alpha=alpha,
        )
        for c in ALPHA_COINCIDENCES
        for alpha in ALPHA_GRID
    )


#: The ladder's rungs in order, cumulative, each with the value it sets and
#: the source of that value (the view's side table prints both); the top rung
#: is the perfect set, the bottom one the realistic set. Source visibility
#: comes right after perfect devices: a rung charged while the devices still
#: make no errors pays the acceptance test's margin on outcomes that were
#: impossible before, which at n = 1e6 is worth far more than the effect
#: itself (dark counts at 1e-7 cost 2.3 % there, and nothing at 1e10, in the
#: first order). With the visibility's QBER in place first, every later rung
#: shows its own cost.
LADDER_RUNGS: tuple[tuple[str, str, str], ...] = (
    ("perfect", "", ""),
    ("visibility", "0.98", "wengerowsky2019submarine"),
    ("efficiency", "0.8 per detector", "neumann2022transnational"),
    ("dark", "1.3e-7 per port per round", "joshi2020network"),
    ("mismatch", "54 % : 59 %", "wengerowsky2019submarine"),
    ("basis-split", "T : R = 56 : 44", "joshi2020network"),
    ("extinction", "1e-3 transmitted, 1e-2 reflected", "joshi2020network"),
    ("misalignment", "sin^2 theta = 0.004 (Bob)", "neumann2022transnational"),
)
LADDER_LOSS_DB = 0.0
#: The study's blocks, each at the n where the fully realistic devices expect
#: that many coincidences at 0 dB, and the same n on every rung, so that a bar
#: shows only its rung's cost (re-choosing n per rung would hide most of the
#: efficiency's cost). Plus one large block as a near-asymptotic reference
#: (10^8 and 10^10 barely differ).
LADDER_REFERENCE_ROUNDS = 10**10
LADDER_BLOCKS: tuple[tuple[int | None, int], ...] = (
    *((c, rounds_for(c, LADDER_LOSS_DB, "realistic")) for c in BLOCK_COINCIDENCES),
    (None, LADDER_REFERENCE_ROUNDS),
)


def _ladder_points() -> tuple[Point, ...]:
    """F6: the cumulative imperfection ladder, loss-free, per block.

    Loss-free so that the bars show the devices alone; the study's three
    blocks and one large reference, so that each rung's cost is seen against
    the finite-size cost.
    """
    effects = _effects()
    points = []
    for c, n in LADDER_BLOCKS:
        block = f"c{_power_tag(c)}" if c is not None else f"n{_power_tag(n)}"
        model: dict[str, Any] = {
            "alice_transmittance": per_arm_transmittance(LADDER_LOSS_DB),
            "bob_transmittance": per_arm_transmittance(LADDER_LOSS_DB),
        }
        device: dict[str, Any] = {}
        for index, (name, value, source) in enumerate(LADDER_RUNGS):
            m, d = effects[name]
            model = {**model, **m}
            device = {**device, **d}
            points.append(
                Point(
                    id=f"{block}-{index:02d}-{name}",
                    labels={
                        "rung": index,
                        "effect": name,
                        "value": value,
                        "source": source,
                        "loss_db": LADDER_LOSS_DB,
                        "rounds": n,
                        "coincidences": c,
                    },
                    model=dict(model),
                    device=dict(device),
                    rounds=n,
                )
            )
    return tuple(points)


#: The licensed route's solver: auto, as everywhere else, since auto's
#: corrective stage handles constraint rows (solvers-auto-caps; it replaced
#: pairwise, whose solves
#: never converged: relative gaps 0.5 %, 1.8 % and 8.5 % at cutoff 1, 2, 3 after
#: 2400 s, against about 0.1 % under auto in under three minutes). From cutoff
#: 4 a corrective iteration takes about 10 s (25 s at cutoff 5), so those points
#: get two hours; the figure shows
#: the gap that remains.
LICENSED_SOLVER = AUTO
LICENSED_SOLVER_LONG = SolverSettings(method="auto", budget_seconds=7200)
LICENSED_LONG_FROM_CUTOFF = 4
#: At realistic devices a 600 s solve does not converge from cutoff 3 up
#: (licensed N3 a 74 % relative gap at 600 s;
#: encoded N4 and N5 refused a bound at most alphas of their search, N5 at
#: every one, so its chosen alpha meant nothing and licensed N5 borrowed it).
#: So from this cutoff the realistic points run on the long budget, and above
#: it they take the alpha the realistic encoded point at this cutoff chose
#: instead of searching; at equal alpha the cutoffs agreed within their gaps.
REALISTIC_LONG_FROM_CUTOFF = 3
#: Both routes to cutoff 5.
ROUTE_CUTOFFS = (1, 2, 3, 4, 5)
#: The exact-window depth m* per cutoff (receiver/def:pmcex): the smallest at
#: which the analytic remainder beta(m* + 1) no longer binds, so p_mc is the
#: computed block minimum, at n = N + 1 for every cutoff scanned (realistic
#: detectors: p_mc 0.320, 0.640, 0.794, 0.890, 0.937; deeper only costs
#: time). The analytic value is always available and already larger than
#: the exact one, so the exact one can be used.
EXACT_WINDOW = {1: 3, 2: 4, 3: 5, 4: 7, 5: 8}


def _routes_points() -> tuple[Point, ...]:
    """F5: encoded (WPFSS) against licensed (FSS), per photon cutoff.

    The encoded route is the weight-preserving flag-state squasher
    (reductions/wpfss, tupkary2026decoy); the licensed route the published
    flag-state squasher as a constraint list (meat-core ex:fss,
    zhang2021security). Since the direct route a run evaluates its bound on
    the receiver's reference declaration wherever it holds one; the record
    keeps the snapped run's own bound beside it
    (``stages.key_rate.reference_bracket``), which the F5 table shows.

    Both device sets run, in two panels, so the cost
    of the route is seen apart from the devices'; ids ``realistic-encoded-N1``,
    ``perfect-licensed-N3``, ..., each set at 1e6 expected coincidences and so
    at its own n.
    """
    points = []
    for kind in DEVICES:
        head = _headline(kind)
        for cutoff in ROUTE_CUTOFFS:
            tag = f"N{cutoff}"
            device = {
                **_device(kind),
                **_both("photon_cutoff", Fraction(cutoff)),
                **_both("exact_window", Fraction(EXACT_WINDOW[cutoff])),
            }
            labels = {"cutoff": cutoff, **head}
            model = _channel(HEADLINE_LOSS_DB, SOURCE_QBER[kind])
            long_from = (
                REALISTIC_LONG_FROM_CUTOFF
                if kind == "realistic"
                else LICENSED_LONG_FROM_CUTOFF
            )
            # Above REALISTIC_LONG_FROM_CUTOFF a realistic point borrows the
            # alpha of the encoded point at that cutoff (its comment).
            borrowed = (
                f"{kind}-encoded-N{REALISTIC_LONG_FROM_CUTOFF}"
                if kind == "realistic" and cutoff > REALISTIC_LONG_FROM_CUTOFF
                else None
            )
            points.append(
                Point(
                    id=f"{kind}-encoded-{tag}",
                    labels={**labels, "route": "encoded"},
                    device={**device, "route": "encoded"},
                    solver=AUTO if borrowed is None else LICENSED_SOLVER_LONG,
                    alpha_from=borrowed,
                    model=model,
                    rounds=head["rounds"],
                )
            )
            points.append(
                Point(
                    id=f"{kind}-licensed-{tag}",
                    labels={**labels, "route": "licensed"},
                    device={**device, "route": "licensed"},
                    solver=(
                        LICENSED_SOLVER_LONG
                        if cutoff >= long_from
                        else LICENSED_SOLVER
                    ),
                    alpha_from=borrowed or f"{kind}-encoded-{tag}",
                    model=model,
                    rounds=head["rounds"],
                )
            )
    return tuple(points)


#: Points that run with the spectral linear oracle instead of QICS. Under auto,
#: both stop on a QICS slow_progress at the search's first alpha, alpha - 1 =
#: 1e-5; the spectral oracle is
#: an exact closed-form minimiser for these untrusted-source, row-free
#: declarations and makes no QICS call. Each record's config states it, and the
#: captions count it. The second two, where the detectors watch both
#: polarizations of their path: an assessment's QICS return has a
#: block below the oracle repair window (minimum eigenvalue -2.3e-7 and
#: -1.4e-7 against 1e-7), which ends the solve.
SPECTRAL_POINTS: frozenset[tuple[str, str]] = frozenset(
    {
        ("rounds", "realistic-L10-c1e4"),
        ("qber", "realistic-L10-Q0p05"),
        ("qber", "realistic-L0-Q0"),
        ("rounds", "realistic-L20-c3e5"),
    }
)


def _spectral(name: str, build: Callable[[], tuple[Point, ...]]) -> Callable[
    [], tuple[Point, ...]
]:
    """Return ``build`` with the :data:`SPECTRAL_POINTS` of sweep ``name`` set."""

    def points() -> tuple[Point, ...]:
        return tuple(
            replace(
                p,
                solver=replace(
                    p.solver,
                    advanced=replace(
                        p.solver.advanced or AdvancedSolverSettings(),
                        oracle="spectral",
                    ),
                ),
            )
            if (name, p.id) in SPECTRAL_POINTS
            else p
            for p in build()
        )

    return points


SWEEPS: dict[str, Sweep] = {
    s.name: s
    for s in (
        Sweep("loss", "F1", "Key rate against loss, per block", _loss_points),
        Sweep(
            "qber",
            "F2",
            "Key rate against QBER, per loss",
            _spectral("qber", _qber_points),
        ),
        Sweep(
            "rounds",
            "F3",
            "Key rate against n and per coincidence",
            _spectral("rounds", _rounds_points),
        ),
        Sweep("solvers", "F4", "Solver methods against alpha", _solver_points),
        Sweep("routes", "F5", "WPFSS against FSS, per photon cutoff", _routes_points),
        Sweep("ladder", "F6", "Imperfection ladder, loss-free, per n", _ladder_points),
        Sweep("alpha", "F7", "Key length against alpha, per block", _alpha_points),
    )
}
