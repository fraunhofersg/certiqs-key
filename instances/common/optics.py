"""The receiver, as optics you can edit: a beamsplitter, a half-wave plate, two PBSs.

WHAT THIS DECLARES
==================
The passive-basis-choice BB84 receiver, in the form ``receiver`` calls route
(iii) -- a graph of catalogue components, compiled by Eq. ``eq:compile``:

    channel ---->[ BS ]--+--> Z arm ------------->[ PBS ]--> H  ,  V
                         |
                         +--> X arm --[ HWP ]---->[ PBS ]--> +  ,  -

Four paths carry two polarization modes each, so the mode space is eight modes;
the channel enters on the ``Z`` path and the other three inputs are vacuum. The
beamsplitter makes the basis choice passively, the half-wave plate at ``pi/8``
rotates the X basis onto the Z basis so that a second identical PBS can separate
it, and each of the four output paths is watched by one threshold detector
that clicks on either polarization (:data:`PORTS`).

EVERY PARAMETER IS AN EXACT RATIONAL AND MEANT TO BE CHANGED
===========================================================
:class:`ReceiverParameters` is the whole surface: the splitting ratio, the plate
angle, the polarizing beamsplitters' two leaks, the four detector efficiencies,
the four dark-count probabilities, and the photon cutoff. They are exact
rationals because ``receiver``'s inputs are declared data and a ``float``
reaching an exact substrate is a number nobody wrote down (the rule
:mod:`instances.common.honest.depolarized_bell_pair` states for ``Q``); the one
place a float appears is the plate ANGLE, which is stated as a rational
multiple of ``pi`` and converted at the boundary because a retardance is an
angle and not a ratio.

There is no exactly-representable subset to stay inside.
:mod:`instances.optical_bb84.rationalize` absorbs the float evaluation
downstream, so an arbitrary rational splitting ratio and an arbitrary rational
plate angle are as usable as the ideal ones. What a parameter change CAN do is
make the declaration fail the rationalizer's exact test, and that refuses with a
legible reason rather than producing a plausible wrong number.

A PROBE SOURCE IS AN OPTIONAL SECOND INPUT; ABSENT IS THE PROBE-FREE RECEIVER
===========================================================================
A :class:`ProbeSource` declares a probe on free inputs of the receiver --
``receiver``'s declared source modes ``Inp_S``, with a probe declaration
``(T, {Gamma^(t)})`` whose ``off`` setting is vacuum (Definition
``def:probe``) and an exact-window depth, also the tail window, at each lit
setting. Without one :func:`receiver_request` declares ``Inp_S`` empty and
``T = {off}``, the probe-free receiver. A receiver with source modes is
conditioned on its probe states by ``receiver``'s probe-conditioning
submodule; where that submodule is absent, the receiver refuses such a
declaration with ``probe_conditioning_submodule_absent``.

THE ANALYTIC GRAMS ARE A CROSS-CHECK AND NOT AN INPUT
====================================================
:func:`analytic_port_grams` writes down, in exact rationals, what the four port
Grams of the IDEAL device are: ``x`` and ``1 - x`` times the four BB84
projectors, scaled by the detector efficiencies. Nothing in a run consumes it.
It exists so that a test can assert the compiled graph and the rationalized
declaration agree with the device the optics were supposed to describe -- the
difference between snapping onto the RIGHT numbers and snapping onto some
numbers, which no admissibility check can tell apart.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Protocol

from certiqs_key.receiver import (
    OFF_SETTING,
    Assurance,
    Beamsplitter,
    CoarseGraining,
    DetectorPort,
    Element,
    ElementGraph,
    InputModes,
    Mode,
    ModeSpace,
    PiMultiple,
    Polarization,
    PolarizingBeamsplitter,
    PortMap,
    ProbeDeclaration,
    ReceiverRequest,
    Retarder,
)
from instances.common.errors import OpticalReceiverError

__all__ = [
    "DECLARED_EXACT_WINDOW_TOLERANCES",
    "DECLARED_TOLERANCES",
    "PATHS",
    "PORTS",
    "RAW_LETTERS",
    "ProbeSource",
    "ReceiverParameters",
    "analytic_port_grams",
    "coarse_graining",
    "element_graph",
    "mode_space",
    "receiver_request",
]

#: The four optical paths, in declared order. ``Z`` carries the channel in and
#: the Z-basis transmitted port out; ``X`` the reflected arm after the plate.
#: ``Zr`` and ``Xr`` are the two polarizing beamsplitters' reflected ports.
PATHS: tuple[str, ...] = ("Z", "X", "Zr", "Xr")

#: Detector labels in declared order, and the modes each one watches. This is
#: the physical claim the whole file exists to make: ``H`` is the Z-basis
#: transmitted path, ``V`` its reflection, and ``D``/``A`` the same pair behind
#: the plate. A detector sits behind a PATH and clicks on either polarization
#: (``ass:port``), so each port watches both modes of its path: the light an
#: imperfect PBS sends the wrong way (its two leaks,
#: :attr:`ReceiverParameters.pbs_leak_transmitted` and
#: :attr:`ReceiverParameters.pbs_leak_reflected`) clicks the other detector of
#: the pair, as it does on a bench, instead of leaving the receiver unseen.
PORTS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("H", ("Z_H", "Z_V")),
    ("V", ("Zr_H", "Zr_V")),
    ("D", ("X_H", "X_V")),
    ("A", ("Xr_H", "Xr_V")),
)

#: The emitted alphabet: no click, one click per port, and every multi-click
#: pattern aggregated. ``receiver``'s coarse-graining is a TOTAL map from
#: the ``2^4`` raw patterns onto these six letters.
RAW_LETTERS: tuple[str, ...] = ("nc", "H", "V", "D", "A", "mc")

#: ``receiver``'s six declared numerical tolerances, Section 2.1. They are
#: DECLARED and never defaulted -- the module refuses a request that omits them
#: -- so this instance states them, and states them once. They govern the
#: SUPPLIER's own residual checks (``r_1``..``r_5``, ``eps_gap``) and have
#: nothing to do with ``eps_op`` or ``eps_dec``, which are the consumers' and are
#: run at zero.
DECLARED_TOLERANCES: Mapping[str, float] = {
    "eps_1": 1e-3,
    "eps_2": 1e-3,
    "eps_3": 1e-3,
    "eps_4": 1e-3,
    "eps_5": 1e-3,
    "eps_gap": 1e-3,
}

#: The two CONDITIONAL tolerances of ``receiver``'s opt-in exact window,
#: declared exactly where :attr:`ReceiverParameters.exact_window` is set and
#: refused when it is not. Both are sized at this instance's declared 1e-3, and
#: the choice of ``eps_eig`` in particular is a decision this instance owns and
#: states.
#:
#: ``eps_eig`` IS NOT ZERO, AND THAT IS DELIBERATE. Zero is inside the declared
#: domain and was admitted when the exact window was accepted --
#: ``rem:tolerancedomain`` says "the domain is a floor, not sizing advice" --
#: but at ``eps_eig = 0`` Assumption ``ass:eig`` reads "the eigenvalue routine
#: never overshoots at all", which is false of a floating-point ``eigvalsh`` and
#: would be this instance asserting exactness it does not have. A sized slack
#: states the assumption honestly and costs ``eps_eig`` of ``p_mc``: ``ell(n) =
#: max{beta(n), beta-hat*(n) - eps_eig}`` (Eq. ``eq:elldef``), so the emitted
#: value can only be LOWER than at zero, never higher, and it is bounded below
#: by the analytic ``beta(n)`` whatever the size -- the opt-in route is never
#: worse than Definition ``def:pmc`` (Proposition ``prop:exactnoworse``).
DECLARED_EXACT_WINDOW_TOLERANCES: Mapping[str, float] = {
    "eps_6": 1e-3,
    "eps_eig": 1e-3,
}

class ProbeSource(Protocol):
    """A probe declared on free inputs of this receiver (Definition ``def:probe``).

    The one hook the passive receiver has for a probe: :func:`receiver_request`
    reads the source modes, the declaration and the lit settings' windows from
    it, and :func:`~instances.common.passive_device.passive_device_requests`
    reads its settings for the reductions' probe classes.
    """

    @property
    def source_modes(self) -> tuple[str, ...]:
        """Return the declared source modes ``Inp_S``, by mode label."""
        ...

    @property
    def settings(self) -> tuple[str, ...]:
        """Return the probe alphabet ``T`` in its declared order, ``off`` first."""
        ...

    def declaration(self) -> ProbeDeclaration:
        """Return the probe declaration ``(T, {Gamma^(t)})``."""
        ...

    def windows(self, photon_cutoff: int) -> Mapping[str, int]:
        """Return each lit setting's exact-window depth, also its tail window."""
        ...


def _quadruple(values: Sequence[Fraction], what: str) -> tuple[Fraction, ...]:
    """Return four exact rationals, or refuse to guess at what was meant."""
    out = tuple(values)
    if len(out) != 4:
        raise OpticalReceiverError(
            f"{what} carries one value per detector, and this receiver has four; "
            f"got {len(out)}"
        )
    for value in out:
        if not isinstance(value, Fraction):
            raise OpticalReceiverError(
                f"{what} is declared in exact rationals; got {value!r} of type "
                f"{type(value).__name__}. A float would be widened silently into "
                "the nearest binary rational, and the declaration would be a "
                "number nobody wrote down"
            )
        if not 0 <= value <= 1:
            raise OpticalReceiverError(f"{what} lies in [0, 1]; got {value}")
    return out


@dataclass(frozen=True)
class ReceiverParameters:
    """The playable surface of the receiver. Every field is exact.

    Defaults describe the IDEAL device: a balanced beamsplitter, a half-wave
    plate at ``pi/8``, perfect polarizing beamsplitters, unit efficiency and no
    dark counts. That is the configuration the qubit limit is compared against,
    so it is the one a default reproduces.
    """

    #: The beamsplitter's transmittance ``x``, which IS the passive Z-basis
    #: probability. ``receiver`` refuses a splitting ratio written ``a:b``
    #: (``splitting_ratio_presentation``); ``x`` is declared directly.
    basis_split: Fraction = Fraction(1, 2)
    #: The half-wave plate's angle, IN UNITS OF ``pi``. ``1/8`` is the 22.5
    #: degrees that carries the X basis onto the Z basis.
    half_wave_angle: Fraction = Fraction(1, 8)
    #: The fraction of the polarization each polarizing beamsplitter should
    #: reflect (V) that it transmits instead: the PBS element's
    #: ``transmittance_v``. That light reaches the transmitted-path detector
    #: (``H``, or ``D`` behind the plate), which clicks on it because each
    #: detector watches both polarizations of its path (:data:`PORTS`).
    #: ``0`` is perfect separation; ``1/2`` is no separation at all.
    pbs_leak_transmitted: Fraction = Fraction(0)
    #: The fraction of the polarization each polarizing beamsplitter should
    #: transmit (H) that it reflects instead: the PBS element's
    #: ``transmittance_h`` is ``1 - pbs_leak_reflected``. That light reaches the
    #: reflected-path detector (``V``, or ``A`` behind the plate), which clicks
    #: on it. ``0`` is perfect separation; ``1/2`` is no separation at all.
    pbs_leak_reflected: Fraction = Fraction(0)
    #: ``eta_k`` per detector, in the order of :data:`PORTS`.
    efficiency: tuple[Fraction, ...] = (Fraction(1),) * 4
    #: ``p_dc|k`` per detector, in the order of :data:`PORTS`.
    dark_count: tuple[Fraction, ...] = (Fraction(0),) * 4
    #: ``N``. A DECLARED protocol parameter: ``receiver`` neither chooses
    #: it nor optimizes it, and the blocks above it are covered by the uniform
    #: high-photon bound instead of being emitted.
    photon_cutoff: int = 1
    #: ``m*``, the OPT-IN exact-window depth of ``receiver``'s
    #: Definition ``def:pmcex``, or ``None`` for no depth. ``None`` is not a
    #: default standing in for a number: Section 1.1 (b) says a declaration
    #: carrying none leaves "Definition ``def:pmc`` EXPRESSION FOR EXPRESSION,
    #: no block above the cutoff is formed, and the emitted value is the one
    #: 0.2.0 emits", which is what this instance emits without a window.
    #:
    #: WHY IT IS WORTH DECLARING HERE. ``thm:multiclick-bound`` gives only
    #: ``lambda_min(blk M^(=n)_mc) >= beta(n)``, and for this receiver that
    #: inequality is badly slack: at ``p_Z = 1/2`` the closed form
    #: ``beta(n) = 1 - 2 p_Z^n - 2 (1-p_Z)^n`` gives ``beta(2) = 0`` while the
    #: true minimum eigenvalue of the two-photon multiclick block is ``1/2``.
    #: At ``N = 1`` that difference is the difference between ``p_mc = 0``,
    #: which bounds the target's weight on the flag sectors by nothing at all,
    #: and ``p_mc ~ 1/2``.
    exact_window: int | None = None
    #: ``receiver``'s Section 2.1 tolerances, defaulting to this instance's
    #: declared set. The two CONDITIONAL ones are not here: they are added by
    #: :func:`receiver_request` exactly where a depth is declared, because the
    #: module refuses them when it is not.
    tolerances: Mapping[str, float] = field(
        default_factory=lambda: dict(DECLARED_TOLERANCES)
    )
    #: ``receiver``'s optional ``efficiency_normalization``: the factored loss
    #: ``t`` the receiver is compiled at, or ``None`` for its default, the
    #: largest declared efficiency divided by ``99/100``, or ``1`` where that
    #: efficiency is at least ``99/100``
    #: (``receiver/detector-imperfections/req:efficiency-normalization``). A
    #: device whose flat instance is read as a BRANCH of a larger receiver
    #: model declares ``1``
    #: (``reductions/wpfss/req:normalized-branch-refusal``).
    efficiency_normalization: Fraction | None = None

    def __post_init__(self) -> None:
        """Check the domains this instance owns, before the module sees them."""
        for name in (
            "basis_split",
            "half_wave_angle",
            "pbs_leak_transmitted",
            "pbs_leak_reflected",
        ):
            value = getattr(self, name)
            if not isinstance(value, Fraction):
                raise OpticalReceiverError(
                    f"{name} is declared as an exact rational; got {value!r} of "
                    f"type {type(value).__name__}"
                )
        if not 0 <= self.basis_split <= 1:
            raise OpticalReceiverError(
                f"the splitting ratio lies in [0, 1]; got {self.basis_split}"
            )
        if not 0 <= self.pbs_leak_transmitted <= Fraction(1, 2):
            raise OpticalReceiverError(
                "a polarizing beamsplitter's transmitted leak (the share of V it "
                "transmits) lies in [0, 1/2]; at 1/2 it separates nothing. Got "
                f"{self.pbs_leak_transmitted}"
            )
        if not 0 <= self.pbs_leak_reflected <= Fraction(1, 2):
            raise OpticalReceiverError(
                "a polarizing beamsplitter's reflected leak (the share of H it "
                "reflects) lies in [0, 1/2]; at 1/2 it separates nothing. Got "
                f"{self.pbs_leak_reflected}"
            )
        if self.photon_cutoff < 0:
            raise OpticalReceiverError(
                f"the photon cutoff N is non-negative; got {self.photon_cutoff}"
            )
        if self.exact_window is not None and self.exact_window <= self.photon_cutoff:
            # The module refuses this too, with the verbatim reason
            # `exact_window_depth_outside_declared_range`. It is checked here as
            # well because a depth is a DECLARATION this instance writes, and a
            # declaration that cannot be honoured is better caught where it is
            # written than three modules downstream.
            raise OpticalReceiverError(
                f"the exact-window depth m* = {self.exact_window} must exceed "
                f"the cutoff N = {self.photon_cutoff}; Definition def:pmcex "
                "requires m* > N, and at m* <= N the window {n : N < n <= m*} "
                "is empty"
            )
        _quadruple(self.efficiency, "efficiency")
        _quadruple(self.dark_count, "dark_count")


def mode_space() -> ModeSpace:
    """Return the eight declared modes: four paths, two polarizations each."""
    return ModeSpace.declare(
        Mode(path, polarization, 0)
        for path in PATHS
        for polarization in (Polarization.H, Polarization.V)
    )


def _index() -> dict[str, int]:
    """Return the mode label to position map of the declared mode space."""
    return {mode.label: position for position, mode in enumerate(mode_space().modes)}


def element_graph(parameters: ReceiverParameters) -> ElementGraph:
    """Return the four-element graph of the receiver.

    The edges are the physical order and are declared rather than inferred:
    condition (E3) refuses a graph in which two elements sharing a mode are not
    reachability-comparable, so a receiver whose order was ambiguous would be
    refused rather than silently resolved.
    """
    at = _index()
    pbs = PolarizingBeamsplitter(
        transmittance_h=1 - parameters.pbs_leak_reflected,
        transmittance_v=parameters.pbs_leak_transmitted,
        phase_h=0,
        phase_v=0,
        loss_1=0,
        loss_2=0,
    )
    return ElementGraph(
        (
            Element(
                "bs",
                Beamsplitter(
                    transmittance=parameters.basis_split, phase=0, loss_1=0, loss_2=0
                ),
                (at["Z_H"], at["Z_V"], at["X_H"], at["X_V"]),
            ),
            Element(
                "hwp",
                # The angle is declared in units of pi, so it is handed over
                # in that presentation (receiver interface.yaml
                # parameters.units, presentation_rule (b)): c pi exactly, which
                # puts a rational c on the exact route of
                # receiver/req:exact-route-decision (ii). Its binary64
                # evaluation is float(c) * math.pi, the radian value this
                # element carried before.
                Retarder.half_wave(PiMultiple(parameters.half_wave_angle), loss=0),
                (at["X_H"], at["X_V"]),
            ),
            Element("pbs_z", pbs, (at["Z_H"], at["Z_V"], at["Zr_H"], at["Zr_V"])),
            Element("pbs_x", pbs, (at["X_H"], at["X_V"], at["Xr_H"], at["Xr_V"])),
        ),
        (("bs", "hwp"), ("bs", "pbs_z"), ("hwp", "pbs_x")),
    )


def coarse_graining() -> CoarseGraining:
    """Return ``cg``: no click, four single clicks, everything else ``mc``.

    Written out rather than taken from a constructor, because the map is a
    DECLARED datum of this receiver and its letter order is what
    ``reductions`` compares across artifacts.
    """
    assignment: dict[frozenset[int], str] = {}
    for pattern in range(1 << 4):
        fired = frozenset(port for port in range(4) if pattern & (1 << port))
        if not fired:
            assignment[fired] = "nc"
        elif len(fired) == 1:
            assignment[fired] = PORTS[next(iter(fired))][0]
        else:
            assignment[fired] = "mc"
    return CoarseGraining(port_count=4, alphabet=RAW_LETTERS, assignment=assignment)


def receiver_request(
    parameters: ReceiverParameters, probe: ProbeSource | None = None
) -> ReceiverRequest:
    """Return ``receiver``'s input keys for this device.

    Fourteen keys, or FIFTEEN where
    :attr:`ReceiverParameters.exact_window` carries a depth:
    ``exact_window`` is the only optional row of Section 2.1, and it brings
    ``eps_6`` and ``eps_eig`` with it -- required exactly where a depth is
    declared and REFUSED where it is not, which is why they are added here
    rather than sitting in :data:`DECLARED_TOLERANCES`.

    WITHOUT ``probe`` the depth is declared at the ONE probe setting this
    receiver has. It is probe-free, so ``Inp_S`` is empty and ``T = {off}`` by
    Definition ``def:probe``; ``off`` is spelled from the module's own
    :data:`~certiqs_key.receiver.settings.OFF_SETTING` rather than repeated, so the
    two cannot drift.

    WITH ``probe`` (a :class:`ProbeSource`) its source modes become ``Inp_S``
    and its declaration ``T``, ``off`` being vacuum.
    :attr:`ReceiverParameters.exact_window` stays the ``off`` depth, and the
    source's window at each lit setting is that setting's depth and tail
    window; a lit setting fails predicate (X), so its tail window is required
    (``tail_window_missing`` otherwise).

    Route (iii) -- the element graph -- is the declared one, because the graph is
    what a reader can check against the bench. ``requested_assurance`` is
    ``estimate`` and could be nothing else: Theorem ``thm:exact-and-evaluated`` (iii)
    says no path in that module can produce a ``certified`` label.
    """
    at = _index()
    tolerances = dict(parameters.tolerances)
    exact_window: dict[str, int] = {}
    tail_window: dict[str, int] = {}
    if parameters.exact_window is not None:
        exact_window[OFF_SETTING] = parameters.exact_window
    source: tuple[int, ...] = ()
    declaration = ProbeDeclaration.probe_free()
    if probe is not None:
        lit = probe.windows(parameters.photon_cutoff)
        source = tuple(at[mode] for mode in probe.source_modes)
        declaration = probe.declaration()
        for label, window in lit.items():
            exact_window[label] = window
            tail_window[label] = window
    if exact_window:
        for key, value in DECLARED_EXACT_WINDOW_TOLERANCES.items():
            tolerances.setdefault(key, value)
    return ReceiverRequest(
        mode_space=mode_space(),
        input_modes=InputModes(channel=(at["Z_H"], at["Z_V"]), source=source),
        port_map=PortMap(
            tuple((label, tuple(at[m] for m in modes)) for label, modes in PORTS)
        ),
        detector_layer=tuple(
            DetectorPort(label, efficiency, dark)
            for (label, _modes), efficiency, dark in zip(
                PORTS, parameters.efficiency, parameters.dark_count, strict=True
            )
        ),
        probe_declaration=declaration,
        photon_cutoff=parameters.photon_cutoff,
        exact_window=exact_window,
        numerical_tolerances=tolerances,
        outcome_coarse_graining=coarse_graining(),
        requested_assurance=Assurance.ESTIMATE,
        element_graph=element_graph(parameters),
        tail_window=tail_window,
        efficiency_normalization=parameters.efficiency_normalization,
    )


#: The four BB84 projectors on the channel's two polarization modes, exactly, in
#: the order of :data:`PORTS`. ``|H>``, ``|V>``, ``|+>`` and ``|->`` -- the last
#: two rational despite their irrational amplitudes, which is the same fact
#: :data:`instances.common.honest.depolarized_bell_pair.PHI_PLUS` rests on.
_PROJECTORS: tuple[tuple[tuple[Fraction, ...], ...], ...] = (
    ((Fraction(1), Fraction(0)), (Fraction(0), Fraction(0))),
    ((Fraction(0), Fraction(0)), (Fraction(0), Fraction(1))),
    ((Fraction(1, 2), Fraction(1, 2)), (Fraction(1, 2), Fraction(1, 2))),
    ((Fraction(1, 2), Fraction(-1, 2)), (Fraction(-1, 2), Fraction(1, 2))),
)


def analytic_port_grams(
    parameters: ReceiverParameters,
) -> tuple[tuple[str, tuple[tuple[Fraction, ...], ...]], ...]:
    """Return the ideal device's four port Grams, exactly. A CROSS-CHECK ONLY.

    ``A_k = eta_k w_k P_k`` with ``w_H = w_V = x``, ``w_+ = w_- = 1 - x`` and
    ``P_k`` the BB84 projector the port watches. Consumed by no run.

    Raises:
        OpticalReceiverError: where the device is not the ideal one, because
            then the Grams involve the plate angle through ``cos 4theta`` and are
            not rational. A cross-check that quietly returned the ideal values
            for a non-ideal device would compare the graph against the wrong
            thing, which is worse than not comparing it.
    """
    if parameters.pbs_leak_transmitted != 0 or parameters.pbs_leak_reflected != 0:
        raise OpticalReceiverError(
            "the closed form is stated for perfect polarizing beamsplitters; "
            "this declaration has the leaks "
            f"{parameters.pbs_leak_transmitted} (transmitted) and "
            f"{parameters.pbs_leak_reflected} (reflected)"
        )
    if parameters.half_wave_angle != Fraction(1, 8):
        raise OpticalReceiverError(
            "the closed form is stated at the plate angle pi/8, where the X "
            "basis lands exactly on the Z basis; this declaration has "
            f"{parameters.half_wave_angle} pi. At a general angle the Grams "
            "involve cos 4theta and are not rational"
        )
    weights = (
        parameters.basis_split,
        parameters.basis_split,
        1 - parameters.basis_split,
        1 - parameters.basis_split,
    )
    return tuple(
        (
            label,
            tuple(
                tuple(efficiency * weight * entry for entry in row) for row in projector
            ),
        )
        for (label, _modes), efficiency, weight, projector in zip(
            PORTS, parameters.efficiency, weights, _PROJECTORS, strict=True
        )
    )
