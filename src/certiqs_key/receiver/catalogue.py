"""The component catalogue, C1-C10, and its admissibility.

Definition ``def:catalogue-entries`` with Table ``tab:catalogue`` and Theorem
``thm:catalogue-admissibility`` (the component-catalogue submodule): every
entry type, at EVERY parameter tuple in its declared domain, yields a local
element in the sense of Definition ``def:embed``, and is lossless exactly on the
subfamily the table names.

WHAT EACH ENTRY IS
==================
Every entry is a unitary core with a positive semidefinite attenuation on one
or both sides, which is why Lemma ``lem:attenuated`` does almost all the work:
``D_2 V D_1`` is a contraction, with equality exactly at ``D_1 = D_2 = 1``.

    C1  beamsplitter          Eq. eq:bs, real at phi = 0 with det B = -1
    C2  polarizing bs         Eq. eq:pbs, the direct sum in the Xi ordering
    C3  retarder + presets    Eq. eq:retarder, Eq. eq:hwpqwp
    C4  circular retarder     R(rho), Eq. eq:retgen: NOT a special case of C3
    C5  mirror or fold        Eq. eq:mirror, with the declared handedness flip
    C6  phase shifter         diagonal, unimodular
    C7  loss                  diag(sqrt(eta_m)); the loss PRIMITIVE
    C8  polarizer             Eq. eq:polarizer; the blocked polarization is loss
    C9  mode routing          a permutation matrix; moves light between modes
    C10 generic block         admitted AFTER the explicit contraction check

L1 and L2 are LAYERS, not rows of the catalogue (Remark ``rem:layers``): the
detector layer lives in :mod:`certiqs_key.receiver.efficiency` and the source
layer in :mod:`certiqs_key.receiver.settings`, which hands a receiver with
source modes to the submodule that conditions on them.

THREE CONVENTIONS ARE REALISED HERE AND NOWHERE ELSE
====================================================
* ``waveplate_convention`` -- the retarder CARRIES its physical global phase
  ``exp(-i delta / 2)`` and it is not dropped. At ``delta = pi`` that factor is
  ``-i`` and it multiplies every entry of the plate. Whether it matters is
  Corollary ``cor:phases``, a theorem WITH A HYPOTHESIS, not a reflex.
* ``beamsplitter_convention`` -- the core is ``B(x, varphi)`` of Eq. ``eq:bs``,
  real at ``varphi = 0`` with ``det B = -1``. The symmetric "i" convention is a
  different presentation and is NOT built here. The convention
  (``interface.yaml`` ``conventions.beamsplitter_convention``) states that the
  two conventions are Gram-equivalent ONLY UNDER TWO CONDITIONS -- the two
  output paths never interfere again downstream, AND the input-side factor of
  Eq. ``eq:bssym`` is a SCALAR on the declared input space (Remark
  ``rem:bsconv``) -- and that a matrix taken from the other convention IS
  CONVERTED BEFORE IT IS DECLARED, NEVER DECLARED AS IS. Nothing in this
  module depends on either condition, because the convention fixes the core
  to ``B(x, varphi)``.
* ``mirror_handedness`` -- an explicit boolean per mirror, DEFAULT ``false``,
  "documented as a coordinate-frame choice and never applied implicitly". It is
  the ONLY default value the contract fixes (``interface.yaml``
  ``component_catalogue``, C5), and it is the only default any entry below
  carries.

NO OTHER DECLARED PARAMETER HAS A DEFAULT
=========================================
``interface.yaml`` ``conventions.fail_closed``: "No default is substituted for
a missing datum." Every parameter of every entry -- a reflection phase, a
per-output loss, a retarder's axis angle and scalar loss, a mirror's s/p
phases, a polarizer's leak -- is REQUIRED, so a declaration that omits one is a
construction error before any validation runs, rather than a device silently
declared at zero. A dropped phase is exactly the failure the receiver's design.md
names: a phase that is global on one element is RELATIVE as soon as that
element sits on one arm of an interferometer, so no catalogue entry drops one
(also Remark ``rem:bsconv``, last sentence), and a default of ``0`` would drop
it without a word. The one exception is the reserved OPTIONAL ``tolerance``
field every parameter carries (``interface.yaml`` ``parameters.exactness``), so
its absence is a declared meaning and not a substituted datum.

DOMAINS ARE REFUSED, NEVER CLIPPED
==================================
``interface.yaml`` ``parameters.domains``: "A parameter outside its domain is
refused; it is never clipped to the boundary." The half-open ranges are the trap
and are checked as written -- ``delta`` in ``[0, 2 pi)``, ``theta`` in
``[0, pi)`` -- so ``delta = 2 pi`` is refused although the clipped value
``delta = 0`` would give the identity and pass every other validation in the
contract. A failing domain check is condition (E1) of Definition ``def:graph``,
and that is the identifier the refusal names.
"""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from fractions import Fraction
from typing import ClassVar, Final

import numpy as np

from certiqs_key.receiver.enclosure import pi_bounds
from certiqs_key.receiver.errors import MalformedInputError
from certiqs_key.receiver.numerics import (
    Angle,
    Matrix,
    NumericalTolerances,
    PiMultiple,
    Scalar,
    as_matrix,
    identity,
    positive_part,
    residual_norm,
    to_float,
)
from certiqs_key.receiver.reasons import Refusal, RefusalReason

__all__ = [
    "CATALOGUE_IDS",
    "Beamsplitter",
    "Component",
    "GenericBlock",
    "Loss",
    "Mirror",
    "ModeRouting",
    "PhaseShifter",
    "Polarizer",
    "PolarizingBeamsplitter",
    "Retarder",
    "Rotator",
    "beamsplitter_core",
    "decibel_to_transmittance",
    "rotation",
    "splitting_ratio_presentation",
]

#: The ten entry types of Table tab:catalogue, in the table's order.
CATALOGUE_IDS: Final[tuple[str, ...]] = (
    "C1",
    "C2",
    "C3",
    "C4",
    "C5",
    "C6",
    "C7",
    "C8",
    "C9",
    "C10",
)


def rotation(angle: float) -> Matrix:
    """Return ``R(theta) = [[cos, -sin], [sin, cos]]`` of entry C3.

    The sign pattern is the contract's (Definition ``def:catalogue-entries``):
    Remark ``rem:rotator`` writes ``R(rho) = exp(-i rho sigma_y)``, and its
    Eq. ``eq:retgen`` is an IDENTITY, not an equality up to a phase.
    """
    cos, sin = math.cos(angle), math.sin(angle)
    return np.asarray([[cos, -sin], [sin, cos]], dtype=np.complex128)


def beamsplitter_core(transmittance: float, phase: float) -> Matrix:
    """Return ``B(x, varphi)`` of Eq. ``eq:bs``.

    Real at ``varphi = 0`` with ``det B = -1``; Remark ``rem:bsconv`` records
    that the sign is a convention artifact.
    """
    root_t = math.sqrt(transmittance)
    root_r = math.sqrt(1.0 - transmittance)
    return np.asarray(
        [
            [root_t, root_r * np.exp(1j * phase)],
            [root_r * np.exp(-1j * phase), -root_t],
        ],
        dtype=np.complex128,
    )


def decibel_to_transmittance(loss_db: float) -> float:
    """Return ``eta = 10^(-L_dB / 10)`` -- ``interface.yaml`` ``parameters.units``.

    A power loss in decibels is converted at validation, and THE CONVERTED
    VALUE IS WHAT THE ARTIFACT CARRIES; the presentation is not a second source
    of truth (``presentation_rule``).
    """
    return float(10.0 ** (-loss_db / 10.0))


def splitting_ratio_presentation(ratio: tuple[Scalar, Scalar]) -> Refusal:
    """Refuse a splitting-ratio presentation -- the parameters and refusal rules.

    **REFUSED, NOT MERELY UNREADABLE.** ``interface.yaml`` ``parameters.units``:
    EXACTLY ONE ALTERNATIVE PRESENTATION IS ADMITTED, a POWER loss in decibels,
    and A SPLITTING RATIO IS NOT ADMITTED AND IS REFUSED. A declaration offering
    a beamsplitter as ``a : b`` is refused with the reason
    ``splitting_ratio_presentation_unsupported``, and the transmittance ``x`` of
    Eq. ``eq:bs`` IS DECLARED DIRECTLY (``splitting_ratio_rule``).

    The reason string is verbatim from the refusal rules (``interface.yaml``
    ``refusals``, row 2). ``splitting_ratio_rule`` gives the argument: the
    string ``a : b`` does not carry the two facts a conversion needs --
    WHETHER THE RATIO IS OF POWER OR OF AMPLITUDE, AND WHICH OF THE TWO DECLARED
    OUTPUT PATHS THE FIRST TERM NAMES -- so any conversion rule would IMPOSE A
    READING on a declared datum, which ``fail_closed`` forbids; and a wrong
    reading is SILENT, since ``90:10`` read as an amplitude ratio gives
    ``x = 81/100`` where the power reading gives ``x = 9/10``, and both are
    legal transmittances.

    NO INPUT KEY CARRIES A RATIO, and none is added: this function IS the
    refusal, for a caller that has one in hand. The decibel presentation
    SURVIVES THE SAME TEST -- ``L_dB`` names one quantity, applied to one
    element, WITH NO ARM TO CHOOSE -- and is implemented in
    :func:`decibel_to_transmittance`, whose converted value is what the artifact
    carries.
    """
    first, second = ratio
    return Refusal(
        RefusalReason.SPLITTING_RATIO_PRESENTATION_UNSUPPORTED,
        f"the splitting-ratio presentation {first}:{second} is refused by "
        f"the parameters table, which states no conversion rule (power or "
        f"amplitude, which arm, x or 1 - x); declare the transmittance x of "
        f"Eq. eq:bs directly",
    )


def _domain_refusal(detail: str) -> Refusal:
    """Return the (E1) refusal for a parameter outside its declared domain."""
    return Refusal(RefusalReason.GRAPH_CONDITION_E1_FAILED, detail)


def _closed_unit(name: str, value: Scalar) -> Refusal | None:
    """Return a refusal unless ``value`` lies in the closed interval [0, 1].

    DECIDED ON THE DECLARED NUMBER, NOT ON ITS MACHINE IMAGE. A declared
    :class:`~fractions.Fraction` such as ``1 + 2^-60`` converts to the double
    ``1.0`` and would pass a comparison made after :func:`to_float`, although
    the declared parameter lies outside the domain; the exact model
    (Requirement ``req:exact-route-decision``) would then take the square root
    of a negative rational. A finite binary64 value is the dyadic rational it
    denotes, so the exact comparison is the same comparison for it.
    """
    if isinstance(value, float) and not math.isfinite(value):
        inside = False
    else:
        exact = Fraction(value)
        inside = 0 <= exact <= 1
    if inside:
        return None
    return _domain_refusal(
        f"(E1) parameter {name} = {value} lies outside its declared domain "
        f"[0, 1]; the parameters table refuses it rather than clipping it"
    )


def _half_open(
    name: str, value: Angle, upper_pi: int, upper_name: str
) -> Refusal | None:
    """Return a refusal unless ``value`` lies in ``[0, upper_pi * pi)``.

    DECIDED ON THE DECLARED NUMBER, as :func:`_closed_unit` is. An angle given
    as a coefficient of pi (:class:`PiMultiple`) is compared exactly, its
    coefficient against ``upper_pi``. An angle given in radians is the
    rational it denotes (a finite binary64 value is a dyadic rational), and
    it is compared with ``upper_pi * pi`` through the rational bounds of
    :func:`_below_multiple_of_pi`: a binary64 comparison with
    ``upper_pi * math.pi`` would refuse the double ``math.pi`` itself as an
    angle in ``[0, pi)``, since ``math.pi < pi``.
    """
    if isinstance(value, PiMultiple):
        inside = 0 <= value.coefficient < upper_pi
    elif isinstance(value, float) and not math.isfinite(value):
        inside = False
    else:
        exact = Fraction(value)
        inside = exact >= 0 and _below_multiple_of_pi(exact, upper_pi)
    if inside:
        return None
    return _domain_refusal(
        f"(E1) parameter {name} = {value} lies outside its declared domain "
        f"[0, {upper_name}); the endpoint {upper_name} is NOT in the domain and "
        f"the parameters table refuses it rather than clipping it"
    )


def _below_multiple_of_pi(value: Fraction, multiple: int) -> bool:
    """Decide ``value < multiple * pi`` exactly, for a rational ``value``.

    With rational bounds ``lo < pi < hi`` (:func:`~certiqs_key.receiver.
    enclosure.pi_bounds`), ``value < multiple lo`` decides it true and
    ``value >= multiple hi`` false; otherwise the bounds are refined. The
    loop ends, because for ``multiple > 0`` the number ``multiple * pi`` is
    irrational and so differs from every rational.
    """
    assert multiple > 0, "the declared angle domains end at pi or 2 pi"
    bits = 64
    while True:
        lo, hi = pi_bounds(bits)
        if value < multiple * lo:
            return True
        if value >= multiple * hi:
            return False
        bits *= 2


def _first(*refusals: Refusal | None) -> Refusal | None:
    """Return the first refusal among the arguments, or ``None``."""
    for refusal in refusals:
        if refusal is not None:
            return refusal
    return None


@dataclass(frozen=True)
class Component(ABC):
    """One catalogue element, declared at a parameter tuple.

    ``tolerances`` is the reserved optional ``tolerance`` field of
    ``interface.yaml`` ``parameters.exactness``, keyed by parameter name. This
    module validates every entry as ABSENT OR EXACTLY ZERO and refuses
    otherwise, because "an ignored tolerance is a silent claim that the device
    is exact" (``exactness.rule``; Assumption ``ass:exact``,
    Requirement ``req:reserved-tolerance-field``); the check itself is
    :func:`certiqs_key.receiver.validation.check_parameter_tolerances`.
    """

    tolerances: Mapping[str, Scalar] = field(default_factory=dict, kw_only=True)

    entry_id: ClassVar[str]

    @abstractmethod
    def support_size(self) -> int:
        """Return the number of modes the entry acts on."""

    @abstractmethod
    def check_domain(self, tolerances: NumericalTolerances) -> Refusal | None:
        """Return a refusal if a parameter lies outside its declared domain."""

    @abstractmethod
    def matrix(self) -> Matrix:
        """Return the local element on ``C^Sigma``, rows = outputs."""

    @abstractmethod
    def is_lossless(self) -> bool:
        """Return the Table ``tab:catalogue`` losslessness verdict."""

    def is_lossless_under(self, tolerances: NumericalTolerances) -> bool:
        """Return the losslessness verdict a DECLARED tolerance decides.

        For nine of the ten catalogue entries the lossless subfamily of Table
        ``tab:catalogue`` is a condition on the DECLARED PARAMETERS --
        ``y = 0``, ``x in {0, 1}``, ``eta_k = 1`` -- which Definition
        ``def:tolmap``'s closing enumeration classes, as kind (a), as "a
        comparison of declared data against a declared domain" and which
        therefore consumes no tolerance at all: this default forwards to
        :meth:`is_lossless` and the argument is unused.

        C10 IS THE EXCEPTION AND OVERRIDES IT. Its (E1) is spectral rather than
        a parameter comparison, and Definition ``def:tolmap`` (v) decides its
        lossless sub-case TWO-SIDEDLY at ``eps_1``.
        """
        del tolerances
        return self.is_lossless()

    def loss_parameters(self) -> tuple[tuple[float, str], ...]:
        """Return the declared loss parameters, with their parameter names.

        Requirement ``req:efficiency-record``: the composition record lists EVERY
        declared loss parameter ``q_i`` that ``thm:efficiency`` (iv) names, with
        the element that declares it and its position in the compiled product,
        each value read as the parameter its name says: a transmittance (``x``,
        ``t_H``, ``t_V``, ``eta_m``, ``t``, ``t_perp``), a reflectivity
        (``R_H``, ``R_V``), or a loss whose transmittance is ``1 - q_i`` (``y``,
        ``y_1``, ``y_2``). "Two elements may carry equal numerical values; they
        are still two losses and appear as two rows."
        """
        return ()


@dataclass(frozen=True)
class Beamsplitter(Component):
    """C1 -- beamsplitter. Support: two paths, four modes. Eq. ``eq:bs``."""

    transmittance: Scalar
    phase: Angle
    loss_1: Scalar
    loss_2: Scalar

    entry_id: ClassVar[str] = "C1"

    def support_size(self) -> int:
        """Return 4: two paths carrying two polarization modes each."""
        return 4

    def check_domain(self, tolerances: NumericalTolerances) -> Refusal | None:
        """Check ``x, y_1, y_2`` in [0, 1] and ``varphi`` in [0, 2 pi)."""
        del tolerances
        return _first(
            _closed_unit("x", self.transmittance),
            _half_open("varphi", self.phase, 2, "2 pi"),
            _closed_unit("y_1", self.loss_1),
            _closed_unit("y_2", self.loss_2),
        )

    def core(self) -> Matrix:
        """Return the 2x2 core of Eq. ``eq:bs``, with the output losses."""
        attenuation = np.diag(
            np.asarray(
                [
                    math.sqrt(1.0 - to_float(self.loss_1)),
                    math.sqrt(1.0 - to_float(self.loss_2)),
                ],
                dtype=np.complex128,
            )
        )
        core = beamsplitter_core(to_float(self.transmittance), to_float(self.phase))
        return np.asarray(attenuation @ core, dtype=np.complex128)

    def matrix(self) -> Matrix:
        """Return the core tensored with the identity on polarization.

        The support is ordered ``(p1H, p1V, p2H, p2V)``: the path index is
        outer and the polarization inner, so the element is ``core (x) id_2``.
        """
        return np.asarray(np.kron(self.core(), identity(2)), dtype=np.complex128)

    def is_lossless(self) -> bool:
        """Return whether ``y_1 = y_2 = 0`` -- Table ``tab:catalogue``, C1."""
        return to_float(self.loss_1) == 0.0 and to_float(self.loss_2) == 0.0

    def loss_parameters(self) -> tuple[tuple[float, str], ...]:
        """Return ``x``, ``y_1`` and ``y_2``."""
        return (
            (to_float(self.transmittance), "x"),
            (to_float(self.loss_1), "y_1"),
            (to_float(self.loss_2), "y_2"),
        )


@dataclass(frozen=True)
class PolarizingBeamsplitter(Component):
    """C2 -- polarizing beamsplitter, Eq. ``eq:pbs``. Ideal at t_H=1, t_V=0."""

    transmittance_h: Scalar
    transmittance_v: Scalar
    phase_h: Angle
    phase_v: Angle
    loss_1: Scalar
    loss_2: Scalar

    entry_id: ClassVar[str] = "C2"

    def support_size(self) -> int:
        """Return 4: two paths, ``(p1H, p1V, p2H, p2V)``."""
        return 4

    def check_domain(self, tolerances: NumericalTolerances) -> Refusal | None:
        """Check ``t_H, t_V, y_1, y_2`` in [0, 1] and the phases in [0, 2 pi)."""
        del tolerances
        return _first(
            _closed_unit("t_H", self.transmittance_h),
            _closed_unit("t_V", self.transmittance_v),
            _half_open("varphi_H", self.phase_h, 2, "2 pi"),
            _half_open("varphi_V", self.phase_v, 2, "2 pi"),
            _closed_unit("y_1", self.loss_1),
            _closed_unit("y_2", self.loss_2),
        )

    def matrix(self) -> Matrix:
        """Return Eq. ``eq:pbs`` in the declared ordering ``(p1H,p1V,p2H,p2V)``.

        The ``H`` core acts on ``(p1H, p2H)`` -- declared indices 0 and 2 --
        and the ``V`` core on ``(p1V, p2V)`` -- indices 1 and 3. That is the
        conjugation by the permutation ``Xi`` of Eq. ``eq:pbs``, written out.
        """
        core_h = beamsplitter_core(
            to_float(self.transmittance_h), to_float(self.phase_h)
        )
        core_v = beamsplitter_core(
            to_float(self.transmittance_v), to_float(self.phase_v)
        )
        block = np.zeros((4, 4), dtype=np.complex128)
        for row in range(2):
            for column in range(2):
                block[2 * row, 2 * column] = core_h[row, column]
                block[2 * row + 1, 2 * column + 1] = core_v[row, column]
        attenuation = np.diag(
            np.asarray(
                [
                    math.sqrt(1.0 - to_float(self.loss_1)),
                    math.sqrt(1.0 - to_float(self.loss_1)),
                    math.sqrt(1.0 - to_float(self.loss_2)),
                    math.sqrt(1.0 - to_float(self.loss_2)),
                ],
                dtype=np.complex128,
            )
        )
        return np.asarray(attenuation @ block, dtype=np.complex128)

    def is_lossless(self) -> bool:
        """Return whether ``y_1 = y_2 = 0`` -- Table ``tab:catalogue``, C2."""
        return to_float(self.loss_1) == 0.0 and to_float(self.loss_2) == 0.0

    def loss_parameters(self) -> tuple[tuple[float, str], ...]:
        """Return ``t_H``, ``t_V``, ``y_1`` and ``y_2``."""
        return (
            (to_float(self.transmittance_h), "t_H"),
            (to_float(self.transmittance_v), "t_V"),
            (to_float(self.loss_1), "y_1"),
            (to_float(self.loss_2), "y_2"),
        )


@dataclass(frozen=True)
class Retarder(Component):
    """C3 -- retarder, Eq. ``eq:retarder``, with the presets of Eq. eq:hwpqwp.

    The physical global phase ``exp(-i delta / 2)`` IS CARRIED
    (``waveplate_convention``). At ``delta = pi`` it is ``-i``, and it is the
    factor "an implementation that writes HWP as the real matrix ... silently
    drops" (Example ``ex:bb84``).
    """

    retardance: Angle
    angle: Angle
    loss: Scalar

    entry_id: ClassVar[str] = "C3"

    @classmethod
    def half_wave(cls, angle: Angle, loss: Scalar) -> Retarder:
        """Return ``HWP(theta) = W(pi, theta)`` -- Eq. ``eq:hwpqwp``.

        The retardance is ``pi`` EXACTLY, the coefficient ``1`` of pi
        (:class:`~certiqs_key.receiver.numerics.PiMultiple`), so that the
        preset can lie on the exact route of Requirement
        ``req:exact-route-decision`` (ii). Its binary64 evaluation is
        ``math.pi``, the value the preset has always carried.
        """
        return cls(PiMultiple(Fraction(1)), angle, loss)

    @classmethod
    def quarter_wave(cls, angle: Angle, loss: Scalar) -> Retarder:
        """Return ``QWP(theta) = W(pi/2, theta)`` -- Eq. ``eq:hwpqwp``.

        The retardance is ``pi/2`` exactly; its binary64 evaluation is
        ``math.pi / 2``, as before (a power-of-two scaling is exact).
        """
        return cls(PiMultiple(Fraction(1, 2)), angle, loss)

    def support_size(self) -> int:
        """Return 2: the polarization modes of one path."""
        return 2

    def check_domain(self, tolerances: NumericalTolerances) -> Refusal | None:
        """Check ``delta`` in [0, 2 pi), ``theta`` in [0, pi), ``y`` in [0, 1]."""
        del tolerances
        return _first(
            _half_open("delta", self.retardance, 2, "2 pi"),
            _half_open("theta", self.angle, 1, "pi"),
            _closed_unit("y", self.loss),
        )

    def matrix(self) -> Matrix:
        """Return ``sqrt(1 - y) W(delta, theta)`` of Eq. ``eq:retarder``."""
        delta = to_float(self.retardance)
        rot = rotation(to_float(self.angle))
        inner = np.diag(np.asarray([1.0, np.exp(1j * delta)], dtype=np.complex128))
        plate = np.exp(-0.5j * delta) * (rot @ inner @ rot.T)
        return np.asarray(
            math.sqrt(1.0 - to_float(self.loss)) * plate, dtype=np.complex128
        )

    def is_lossless(self) -> bool:
        """Return whether ``y = 0`` -- Table ``tab:catalogue``, C3."""
        return to_float(self.loss) == 0.0

    def loss_parameters(self) -> tuple[tuple[float, str], ...]:
        """Return the declared scalar loss ``y``."""
        return ((to_float(self.loss), "y"),)


@dataclass(frozen=True)
class Rotator(Component):
    """C4 -- circular retarder, ``R(rho)``. Lossless at every parameter.

    NOT a special case of C3 (Remark ``rem:rotator``): Eq. ``eq:retgen`` shows
    ``W(delta, theta)`` generates in the ``sigma_z``-``sigma_x`` plane while
    ``R(rho) = exp(-i rho sigma_y)`` generates about the missing axis, so no
    single C3 element equals ``R(rho)`` for ``rho`` in ``(0, 2 pi)``, and C4
    is the one-element primitive.
    """

    rotation_angle: Angle

    entry_id: ClassVar[str] = "C4"

    def support_size(self) -> int:
        """Return 2: the polarization modes of one path."""
        return 2

    def check_domain(self, tolerances: NumericalTolerances) -> Refusal | None:
        """Check ``rho`` in [0, 2 pi)."""
        del tolerances
        return _half_open("rho", self.rotation_angle, 2, "2 pi")

    def matrix(self) -> Matrix:
        """Return ``R(rho)``."""
        return rotation(to_float(self.rotation_angle))

    def is_lossless(self) -> bool:
        """Return ``True`` -- Table ``tab:catalogue`` reads "always"."""
        return True


@dataclass(frozen=True)
class Mirror(Component):
    """C5 -- mirror or fold, Eq. ``eq:mirror``.

    ``handedness_flip`` defaults to ``false``, which is the one default value
    the contract fixes. ``interface.yaml`` ``conventions.mirror_handedness``:
    "an explicit boolean per mirror, default false, documented as a
    coordinate-frame choice and never applied implicitly".
    """

    reflectivity_h: Scalar
    reflectivity_v: Scalar
    phase_h: Angle
    phase_v: Angle
    handedness_flip: bool = False

    entry_id: ClassVar[str] = "C5"

    def support_size(self) -> int:
        """Return 2: the polarization modes of one path."""
        return 2

    def check_domain(self, tolerances: NumericalTolerances) -> Refusal | None:
        """Check ``R_H, R_V`` in [0, 1] and the phases in [0, 2 pi)."""
        del tolerances
        return _first(
            _closed_unit("R_H", self.reflectivity_h),
            _closed_unit("R_V", self.reflectivity_v),
            _half_open("varphi_H", self.phase_h, 2, "2 pi"),
            _half_open("varphi_V", self.phase_v, 2, "2 pi"),
        )

    def matrix(self) -> Matrix:
        """Return ``diag(sqrt R) diag(e^{i varphi}) F`` of Eq. ``eq:mirror``."""
        amplitudes = np.diag(
            np.asarray(
                [
                    math.sqrt(to_float(self.reflectivity_h)),
                    math.sqrt(to_float(self.reflectivity_v)),
                ],
                dtype=np.complex128,
            )
        )
        phases = np.diag(
            np.asarray(
                [
                    np.exp(1j * to_float(self.phase_h)),
                    np.exp(1j * to_float(self.phase_v)),
                ],
                dtype=np.complex128,
            )
        )
        flip = np.diag(
            np.asarray(
                [1.0, -1.0 if self.handedness_flip else 1.0], dtype=np.complex128
            )
        )
        return np.asarray(amplitudes @ phases @ flip, dtype=np.complex128)

    def is_lossless(self) -> bool:
        """Return whether ``R_H = R_V = 1`` -- Table ``tab:catalogue``, C5."""
        return (
            to_float(self.reflectivity_h) == 1.0
            and to_float(self.reflectivity_v) == 1.0
        )

    def loss_parameters(self) -> tuple[tuple[float, str], ...]:
        """Return ``R_H`` and ``R_V``."""
        return (
            (to_float(self.reflectivity_h), "R_H"),
            (to_float(self.reflectivity_v), "R_V"),
        )


@dataclass(frozen=True)
class PhaseShifter(Component):
    """C6 -- phase shifter, ``diag(e^{i varphi_m})``. Lossless always."""

    phases: tuple[Angle, ...]

    entry_id: ClassVar[str] = "C6"

    def support_size(self) -> int:
        """Return the number of declared phases."""
        return len(self.phases)

    def check_domain(self, tolerances: NumericalTolerances) -> Refusal | None:
        """Check every ``varphi_m`` in [0, 2 pi)."""
        del tolerances
        return _first(
            *(
                _half_open(f"varphi_{index}", phase, 2, "2 pi")
                for index, phase in enumerate(self.phases)
            )
        )

    def matrix(self) -> Matrix:
        """Return the diagonal unimodular matrix."""
        return np.diag(
            np.asarray(
                [np.exp(1j * to_float(phase)) for phase in self.phases],
                dtype=np.complex128,
            )
        )

    def is_lossless(self) -> bool:
        """Return ``True`` -- Table ``tab:catalogue`` reads "always"."""
        return True


@dataclass(frozen=True)
class Loss(Component):
    """C7 -- loss, ``diag(sqrt(eta_m))``. THE LOSS PRIMITIVE.

    Fibre attenuation, coupling efficiency, spectral-filter insertion loss and
    connector loss are ALL C7 at different SITES (Remark ``rem:entry-roles``).
    Detector efficiency is NOT C7 -- it is the terminal layer L1, and the input
    schema keeps the two in different fields (Theorem ``thm:efficiency`` (iii),
    Requirement ``req:efficiency-schema``).
    """

    efficiencies: tuple[Scalar, ...]

    entry_id: ClassVar[str] = "C7"

    @classmethod
    def from_decibels(cls, losses_db: Sequence[Scalar]) -> Loss | Refusal:
        """Return the element for a decibel presentation, CONVERTED here.

        ``interface.yaml`` ``parameters.units``: the conversion happens AT
        VALIDATION, the converted value being what the artifact carries; the
        presentation is not a second source of truth.
        """
        values: list[Scalar] = []
        for index, loss_db in enumerate(losses_db):
            decibels = to_float(loss_db)
            if decibels < 0.0:
                return Refusal(
                    RefusalReason.DECIBEL_LOSS_NEGATIVE,
                    f"L_dB = {decibels} at position {index} is negative; "
                    f"Definition def:catalogue-entries, entry C7, declares "
                    f"L_dB >= 0",
                )
            values.append(decibel_to_transmittance(decibels))
        return cls(tuple(values))

    def support_size(self) -> int:
        """Return the number of declared efficiencies."""
        return len(self.efficiencies)

    def check_domain(self, tolerances: NumericalTolerances) -> Refusal | None:
        """Check every ``eta_m`` in [0, 1]."""
        del tolerances
        return _first(
            *(
                _closed_unit(f"eta_{index}", value)
                for index, value in enumerate(self.efficiencies)
            )
        )

    def matrix(self) -> Matrix:
        """Return ``diag(sqrt(eta_m))``."""
        return np.diag(
            np.asarray(
                [math.sqrt(to_float(value)) for value in self.efficiencies],
                dtype=np.complex128,
            )
        )

    def is_lossless(self) -> bool:
        """Return whether every ``eta_m = 1`` -- Table ``tab:catalogue``, C7."""
        return all(to_float(value) == 1.0 for value in self.efficiencies)

    def loss_parameters(self) -> tuple[tuple[float, str], ...]:
        """Return every declared ``eta_m``."""
        return tuple(
            (to_float(value), f"eta_{index}")
            for index, value in enumerate(self.efficiencies)
        )


@dataclass(frozen=True)
class Polarizer(Component):
    """C8 -- polarizer, Eq. ``eq:polarizer``. The blocked polarization is loss.

    Lossless exactly at ``t = t_perp = 1``, where the element is the identity
    (Table ``tab:catalogue``) -- the one parameter tuple at which a polarizer
    is not a polarizer.
    """

    angle: Angle
    pass_transmittance: Scalar
    leak_transmittance: Scalar

    entry_id: ClassVar[str] = "C8"

    def support_size(self) -> int:
        """Return 2: the polarization modes of one path."""
        return 2

    def check_domain(self, tolerances: NumericalTolerances) -> Refusal | None:
        """Check ``theta`` in [0, pi) and ``t, t_perp`` in [0, 1]."""
        del tolerances
        return _first(
            _half_open("theta", self.angle, 1, "pi"),
            _closed_unit("t", self.pass_transmittance),
            _closed_unit("t_perp", self.leak_transmittance),
        )

    def matrix(self) -> Matrix:
        """Return ``R(theta) diag(sqrt t, sqrt t_perp) R(theta)^T``."""
        rot = rotation(to_float(self.angle))
        inner = np.diag(
            np.asarray(
                [
                    math.sqrt(to_float(self.pass_transmittance)),
                    math.sqrt(to_float(self.leak_transmittance)),
                ],
                dtype=np.complex128,
            )
        )
        return np.asarray(rot @ inner @ rot.T, dtype=np.complex128)

    def is_lossless(self) -> bool:
        """Return whether ``t = t_perp = 1`` -- Table ``tab:catalogue``, C8."""
        return (
            to_float(self.pass_transmittance) == 1.0
            and to_float(self.leak_transmittance) == 1.0
        )

    def loss_parameters(self) -> tuple[tuple[float, str], ...]:
        """Return ``t`` and ``t_perp``."""
        return (
            (to_float(self.pass_transmittance), "t"),
            (to_float(self.leak_transmittance), "t_perp"),
        )


@dataclass(frozen=True)
class ModeRouting(Component):
    """C9 -- mode routing, ``(Gamma)_{ij} = delta_{i, pi(j)}``.

    Remark ``rem:edgemeaning``: moving light from one mode to another is done
    by the elements' matrices, for instance by this one, and not by an edge of
    the declared graph, which only fixes the order in which two elements act.
    """

    permutation: tuple[int, ...]

    entry_id: ClassVar[str] = "C9"

    def support_size(self) -> int:
        """Return the size of the permuted mode subset."""
        return len(self.permutation)

    def check_domain(self, tolerances: NumericalTolerances) -> Refusal | None:
        """Check that the parameter is a permutation of the support."""
        del tolerances
        size = len(self.permutation)
        if sorted(self.permutation) != list(range(size)):
            return _domain_refusal(
                f"(E1) the declared parameter {self.permutation} is not a "
                f"permutation of the {size} modes of the support"
            )
        return None

    def matrix(self) -> Matrix:
        """Return the permutation matrix."""
        size = len(self.permutation)
        block = np.zeros((size, size), dtype=np.complex128)
        for column, row in enumerate(self.permutation):
            block[row, column] = 1.0
        return block

    def is_lossless(self) -> bool:
        """Return ``True`` -- Table ``tab:catalogue`` reads "always"."""
        return True


@dataclass(frozen=True)
class GenericBlock(Component):
    """C10 -- a supplied matrix, admitted AFTER the explicit check.

    The only entry whose declared domain is the contractivity condition
    itself, so that its check of Theorem ``thm:compilation-well-defined``
    (iv)(E1) is a spectral test on the supplied matrix (Theorem
    ``thm:catalogue-admissibility`` (iii)); and the entry that makes route (ii)
    a special case of route (iii) (Remark ``rem:entry-roles``): the
    fixed-device scope is recovered by declaring exactly one C10 block spanning
    the whole receiver.

    The check is ``Gamma^dagger Gamma <= 1`` and the losslessness verdict is the
    same check with equality (Table ``tab:catalogue``). Both are decided against
    the DECLARED ``eps_1`` -- the tolerance Definition ``def:residuals``
    attaches to exactly this identity, Eq. ``eq:res1`` -- because a second
    threshold here would be one the contract does not declare.
    """

    block: Matrix

    entry_id: ClassVar[str] = "C10"

    @classmethod
    def of(cls, rows: Sequence[Sequence[Scalar | complex]]) -> GenericBlock:
        """Return the entry for a supplied table of entries."""
        return cls(as_matrix(rows))

    def support_size(self) -> int:
        """Return the dimension of the supplied block."""
        return int(self.block.shape[0])

    def check_domain(self, tolerances: NumericalTolerances) -> Refusal | None:
        """Check that the supplied matrix is a contraction, explicitly."""
        if self.block.ndim != 2 or self.block.shape[0] != self.block.shape[1]:
            raise MalformedInputError(
                f"a C10 block must be square, got shape {self.block.shape}"
            )
        defect = self.block.conj().T @ self.block - identity(self.support_size())
        overshoot = residual_norm(positive_part(defect))
        if overshoot > tolerances.eps_1:
            return _domain_refusal(
                f"(E1) the supplied C10 block is not a contraction: the "
                f"positive part of Gamma^dagger Gamma - 1 has spectral norm "
                f"{overshoot} above the declared eps_1 = {tolerances.eps_1}"
            )
        return None

    def is_lossless(self) -> bool:
        """Return whether the explicit check holds WITH EQUALITY, EXACTLY.

        Table ``tab:catalogue`` gives C10's lossless subfamily as
        ``Gamma_Sigma^dagger Gamma_Sigma = id`` (checked), the same check with
        equality, and the supplied block is a DECLARED datum, exact by
        Assumption ``ass:exact``. This is that reading, on the declared data,
        with no tolerance at all.

        **IT IS NOT THE VERDICT Definition ``def:tolmap`` (v) DECIDES.**
        Definition ``def:c10-tolerance``: C10's lossless sub-case
        ``Gamma_Sigma^dagger Gamma_Sigma = id`` is an EQUALITY and is decided
        TWO-SIDEDLY, as ``||Gamma_Sigma^dagger Gamma_Sigma - id|| <= eps_1``,
        and :meth:`is_lossless_under` is that decision procedure. This method
        remains as the exact statement about the declared block, which is a true
        and strictly stronger one, and no validation in this package consults
        it.
        """
        defect = self.block.conj().T @ self.block - identity(self.support_size())
        return residual_norm(defect) == 0.0

    def is_lossless_under(self, tolerances: NumericalTolerances) -> bool:
        """Return C10's lossless verdict as Def. ``def:tolmap`` (v) decides it.

        Definition ``def:c10-tolerance``: C10's lossless sub-case
        ``Gamma_Sigma^dagger Gamma_Sigma = id`` is an EQUALITY and is decided
        TWO-SIDEDLY, as ``||Gamma_Sigma^dagger Gamma_Sigma - id|| <= eps_1``.

        THE TWO-SIDEDNESS IS LOAD-BEARING. The one-sided contraction test of
        :meth:`check_domain` admits ``lmax <= 1 + eps_1`` and says nothing about
        how far BELOW the identity the block sits, so it would call a block with
        ``Gamma_Sigma^dagger Gamma_Sigma = diag(1/4, 1)`` lossless. The
        two-sided norm test refuses that reading, and the same declared
        ``eps_1`` decides both.
        """
        defect = self.block.conj().T @ self.block - identity(self.support_size())
        return bool(residual_norm(defect) <= tolerances.eps_1)

    def matrix(self) -> Matrix:
        """Return the supplied block."""
        return np.asarray(self.block, dtype=np.complex128)
