r"""Detection efficiency, exactly once -- layer L1 and Theorem ``thm:efficiency``.

"Apply the efficiency once" is easy to state for a fixed device and does not
survive verbatim once a receiver is compiled from components: route (iii) has
many legitimate loss sites -- every beamsplitter's loss, every C7 element,
every polarizer's extinction, every mirror's reflectivity, and the detector
efficiency itself. This module is the restatement that is checkable.

ONE STRUCTURAL SITE
===================
Theorem ``thm:efficiency`` (iii): detector efficiency is a parameter of the terminal
layer L1 and enters ``Gamma`` ONLY through the single left factor ``D_eta`` of
Definition ``def:compile``, applied after every chain element. "It is therefore
not an audit but an invariant of the compiler: there is exactly one site at
which it can enter." A C7 element is NOT a detector efficiency, and the input
schema keeps the two in different fields -- ``element_graph`` versus
``detector_layer``.

THE SECOND SUMMAND OF ``D_eta`` IS NOT DECORATION
=================================================
    D_eta = sum_k sqrt(eta_k) E_{P_k} + E_{M \ union_k P_k}

``interface.yaml`` ``layers`` (L1, ``d_eta_second_summand_note``): without it
``D_eta`` would ANNIHILATE EVERY UNMONITORED MODE, and ``D_eta = 1`` at unit
efficiency, on which Theorem ``thm:compilation-well-defined`` (iii) rests, WOULD
FAIL. Dropping it changes no ``A_k`` -- an unmonitored row contributes to none
(Remark ``rem:unmonitored``) -- but it breaks the losslessness statement and the
deficiency identity, because the amplitude that reached an unmonitored mode
would vanish from ``Gamma_Inp^dagger E_un Gamma_Inp``.

UNIFORM WITHIN A PORT IS A SCALAR; NON-UNIFORM IS NOT, AND THE RANK CAN DROP
============================================================================
Theorem ``thm:efficiency`` (i): ``A_k -> eta_k A_k``, and for ``eta_k > 0`` this
preserves ``rk A_k``. The total becomes ``sum_k eta_k A_k``, which is in
general not a multiple of ``A_Sigma`` unless the ``eta_k`` agree -- so scaling
``A_Sigma`` by one average efficiency would give a different, and generally
wrong, ``lmax`` and hence a wrong ``c`` in Eq. ``eq:cd``.

Theorem ``thm:efficiency`` (ii) and Remark ``rem:effrank``: a diagonal attenuation
that varies WITHIN a port gives Eq. ``eq:noneffgram``, which is in general not
a multiple of ``A_k`` and satisfies only ``rk A_k^eff <= rk A_k``, with strict
inequality possible, so the rank test gives its answer only on the Grams
AFTER every efficiency is applied, NEVER BEFORE (Requirement
``req:one-mode-per-port``). Both functions here return a NEW
Gram family for exactly that reason: there is no in-place correction to apply
a stale rank to.

WHY A PRODUCT OF TRANSMITTANCES IS THE WRONG CHECK, AND IS NOT IMPLEMENTED
==========================================================================
Remark ``rem:wrongcheck`` proves that the obvious audit -- multiply the
declared transmittances along each path and compare with the port throughput --
is WRONG in any interferometric topology, and not by a little: at a balanced
Mach-Zehnder with ``phi = 0`` every declared transmittance is ``1``, the
compiled matrix is the identity, and the audit reports a spurious 50 per cent
loss that does not exist. No function in this module computes one. The
checkable invariant is the deficiency identity Eq. ``eq:deficiencyid``
(:func:`certiqs_key.receiver.grams.deficiency_identity`), and it is what the
artifact reports, as residual ``r_3``.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from fractions import Fraction

import numpy as np

from certiqs_key.receiver.errors import HypothesisError
from certiqs_key.receiver.grams import GramFamily
from certiqs_key.receiver.numerics import Matrix, Scalar, residual_norm, to_float

__all__ = [
    "DEFAULT_MARGIN",
    "EfficiencyNormalization",
    "EfficiencyRecord",
    "EfficiencyRow",
    "NormalizationReason",
    "NormalizedPort",
    "apply_uniform_efficiency",
    "default_factor",
    "detector_layer_matrix",
    "efficiency_record",
    "is_multiple_of_a_sigma",
    "nonuniform_effective_gram",
    "normalize_efficiencies",
    "weighted_total",
]


def detector_layer_matrix(
    port_rows: Sequence[Sequence[int]],
    efficiencies: Sequence[Scalar],
    mode_count: int,
) -> Matrix:
    """Return ``D_eta`` of Definition ``def:compile`` -- the terminal layer.

    ``sqrt(eta_k)`` on the modes of port ``k`` and ONE on every mode in no
    port. At unit efficiency the result is the identity, which is what Theorem
    ``thm:compilation-well-defined`` (iii) needs.
    """
    diagonal = np.ones(mode_count, dtype=np.complex128)
    for rows, efficiency in zip(port_rows, efficiencies, strict=True):
        value = to_float(efficiency)
        if not 0.0 <= value <= 1.0:
            raise HypothesisError(
                f"a detector efficiency lies in [0, 1]; got eta = {value}"
            )
        for row in rows:
            diagonal[row] = math.sqrt(value)
    return np.diag(diagonal)


def apply_uniform_efficiency(
    family: GramFamily, efficiencies: Sequence[Scalar]
) -> GramFamily:
    """Return ``{eta_k A_k}`` -- Eq. ``eq:etagram``.

    Theorem ``thm:efficiency`` (i). Every formula of Theorems
    ``thm:click-povm``, ``thm:coarse-graining``, ``thm:multiclick-bound`` and
    ``thm:emitted-bound`` covers inefficient detectors under this single
    substitution, so a caller applies it once and then computes as before. The
    returned family is NEW: the ranks of the old one are stale (Remark
    ``rem:effrank``).
    """
    scaled = tuple(
        np.asarray(to_float(efficiency) * matrix, dtype=np.complex128)
        for matrix, efficiency in zip(family.matrices, efficiencies, strict=True)
    )
    return GramFamily(family.labels, scaled)


def weighted_total(family: GramFamily, efficiencies: Sequence[Scalar]) -> Matrix:
    """Return ``sum_k eta_k A_k`` -- the image of ``A_Sigma`` under Eq. eq:etagram."""
    return apply_uniform_efficiency(family, efficiencies).a_sigma


def is_multiple_of_a_sigma(
    family: GramFamily, efficiencies: Sequence[Scalar], tolerance: float
) -> bool:
    """Return whether ``sum_k eta_k A_k`` is a scalar multiple of ``A_Sigma``.

    The clause of Theorem ``thm:efficiency`` (i) an implementation can get wrong.
    Tested as a MATRIX relation rather than by comparing the declared
    efficiencies, because that is what the clause states; ``tolerance`` has no
    default and callers pass the declared ``eps_2``, the Gram-level tolerance.
    """
    total = weighted_total(family, efficiencies)
    reference = family.a_sigma
    scale_reference = float(np.trace(reference).real)
    if abs(scale_reference) <= tolerance:
        return bool(residual_norm(total) <= tolerance)
    scale = float(np.trace(total).real) / scale_reference
    return bool(residual_norm(total - scale * reference) <= tolerance)


def nonuniform_effective_gram(
    gamma_inp: Matrix, port_rows: Sequence[int], attenuation: Sequence[Scalar]
) -> Matrix:
    """Return ``A_k^eff`` of Eq. ``eq:noneffgram`` for a within-port ``D``.

        A_k^eff = Gamma_Inp^dagger D^dagger E_{k} D Gamma_Inp

    ``attenuation`` gives the diagonal amplitude factor on the rows of the
    port, in the port's own row order. Theorem ``thm:efficiency`` (ii): the result is
    in general NOT a multiple of ``A_k``, and ``rk A_k^eff <= rk A_k`` with
    strict inequality possible.
    """
    rows = gamma_inp[list(port_rows), :]
    factors = np.asarray(
        [to_float(value) for value in attenuation], dtype=np.complex128
    )
    if factors.shape[0] != rows.shape[0]:
        raise HypothesisError("one attenuation factor per row of the port is needed")
    attenuated = factors[:, None] * rows
    return np.asarray(attenuated.conj().T @ attenuated, dtype=np.complex128)


@dataclass(frozen=True)
class EfficiencyRow:
    """One row of the emitted composition record -- Req. req:efficiency-record.

    ``value`` is the declared loss parameter ``q_i``, ``element`` names the
    element ``e_i`` that declares it and the parameter (``parameter y_1``),
    and ``site`` is the single position ``s_i`` at which it enters ``Gamma``.
    THE VALUE IS READ AS THE PARAMETER ITS ROW NAMES: a transmittance, a
    reflectivity, or, for ``y``, ``y_1`` and ``y_2``, a loss whose
    transmittance is ``1 - q_i`` (Requirement ``req:efficiency-record``), so
    the field carries no name that would read every value as a transmittance.
    TWO ELEMENTS MAY CARRY EQUAL NUMERICAL VALUES; THEY ARE STILL TWO LOSSES
    AND APPEAR AS TWO ROWS.
    """

    value: float
    element: str
    site: str


def efficiency_record(
    chain: Sequence[tuple[str, str, tuple[tuple[float, str], ...]]],
    detector: Sequence[tuple[str, float]] = (),
) -> tuple[EfficiencyRow, ...]:
    """Return the composition record of Requirement ``req:efficiency-record``.

    ``chain`` lists, in compiled order, ``(element name, catalogue entry id,
    declared loss parameters)``, each parameter a ``(value, name)`` pair from
    the component's ``loss_parameters()`` and read as its name says (a
    transmittance, a reflectivity, or a loss ``y``, ``y_1``, ``y_2``);
    ``detector`` lists the per-port efficiencies of layer L1. Positions are
    the element's place in the compiled product, and
    the detector layer's site is the terminal factor ``D_eta`` -- the one site
    Theorem ``thm:efficiency`` (iii) allows it.

    Requirement ``req:efficiency-convention`` records what the record is FOR:
    whether the declared Grams came from power data (and are then rescaled by
    ``eta_k``) or from click data (in which case the ``eta_k`` are already
    inside them and must be declared as ``1``) is a declared field, and the
    ``efficiency_record`` is where the answer is written down; Remark
    ``rem:powervsclick`` says why it is not inferable from the numbers.
    """
    rows: list[EfficiencyRow] = []
    for position, (name, entry_id, parameters) in enumerate(chain, start=1):
        for value, parameter in parameters:
            rows.append(
                EfficiencyRow(
                    value=value,
                    element=f"{entry_id} {name}, parameter {parameter}",
                    site=f"chain position {position}",
                )
            )
    for port_label, efficiency in detector:
        rows.append(
            EfficiencyRow(
                value=efficiency,
                element=f"L1 detector layer, parameter eta_{port_label}",
                site="terminal factor D_eta",
            )
        )
    return tuple(rows)


# ---------------------------------------------------------------------------
#  The efficiency normalization (detector-imperfections)
# ---------------------------------------------------------------------------
#
# WHY THE FACTOR IS TAKEN OUT HERE AND NOT IN THE CONSUMER. The efficiencies
# enter the measurement only at the terminal layer D_eta, where the three input
# routes converge (Theorem thm:efficiency (iii)); no block, weight or
# dark-composed element a consumer reads can be renormalized afterwards. So the
# normalized station (def:normalized-station) is compiled here, from the exact
# rationals eta_k / t, and the factor t travels in the efficiency record
# (req:normalization-record) to every consumer that must put the loss back in
# front of an evaluation (req:loss-before-evaluation) or record it in its link
# (reductions/wpfss/req:normalized-link-record).
#
# WHY THE DEFAULT STOPS SHORT OF eta_max. The full normalization t = eta_max
# makes the normalized station's largest efficiency exactly one, and with dark
# counts at a photon cutoff of two or more its singular two-photon block can be
# evaluated in floating point, lifted by the snap and counted by the support
# check, so a run can report key 0 where the model's rate is positive. That is
# the engine's present handling of a singular block and not a property of the
# identity (spec/modules/receiver/design.md, structural decision 14; the
# trade-off itself is rem:normalization-scope). The default therefore divides
# eta_max by the exact margin 99/100 where eta_max < 99/100 and is one from
# eta_max >= 99/100 on; a declared t in [eta_max, 1], eta_max itself included,
# stays allowed. The margin moves the rate, never the bound
# (prop:efficiency-normalization holds at every t).

#: The margin of the default factor: ``t = eta_max / DEFAULT_MARGIN`` where
#: ``eta_max < DEFAULT_MARGIN``, and ``t = 1`` from there on
#: (req:efficiency-normalization).
DEFAULT_MARGIN = Fraction(99, 100)


class NormalizationReason(StrEnum):
    """Why a request was compiled at ``t = 1``: req:normalization-record's reasons.

    Listed in the order the requirement takes them: a record carries the first
    that holds.
    """

    #: The receiver declares source (probe) modes: the loss would act on the
    #: probe light too, and no claim states that form (rem:normalization-scope).
    SOURCE_MODES_DECLARED = "source_modes_declared"
    #: Every declared efficiency is zero, so there is no largest one to factor.
    ALL_EFFICIENCIES_ZERO = "all_efficiencies_zero"
    #: The factor is one, declared (``efficiency_normalization = 1``) or the
    #: default where ``eta_max >= 99/100``; the record's ``factor_declared``
    #: says which. At ``t = 1`` the normalized station is the declared
    #: receiver however the factor was reached, so the two read alike.
    FACTOR_ONE = "factor_one"


@dataclass(frozen=True)
class NormalizedPort:
    """One port's declared efficiency beside the exact one it is compiled at."""

    label: str
    #: ``eta_k`` as declared, as the exact rational the declared number denotes.
    declared: Fraction
    #: ``eta_k / t``, exactly; equal to ``declared`` where nothing was applied.
    compiled: Fraction


@dataclass(frozen=True)
class EfficiencyNormalization:
    """The normalization record of ``req:normalization-record``.

    ``factored_loss`` is the factor ``t`` of Definition ``def:normalized-station``
    the receiver was compiled at; ``applied`` says whether the normalization
    was applied, which it was exactly where ``t < 1``, and ``reason`` why not
    where it was not; ``factor_declared`` says whether ``t`` was the request's
    ``efficiency_normalization`` or the default of :func:`default_factor`, so a
    station at ``t = 1`` reads the same whoever chose the one, apart from that
    flag; ``ports`` carries every declared efficiency beside the exact rational
    ``eta_k / t`` compiled.
    """

    factored_loss: Fraction
    applied: bool
    reason: NormalizationReason | None
    factor_declared: bool
    ports: tuple[NormalizedPort, ...]

    def __post_init__(self) -> None:
        """Refuse a record that contradicts itself; a programming error, raised."""
        if self.applied == (self.reason is not None):
            raise HypothesisError(
                "a normalization record carries a reason exactly where it was "
                "not applied (req:normalization-record)"
            )
        if not 0 < self.factored_loss <= 1:
            raise HypothesisError(
                f"the factored loss lies in (0, 1]; got {self.factored_loss}"
            )
        if self.applied != (self.factored_loss < 1):
            raise HypothesisError(
                "the normalization is recorded as applied exactly where t < 1 "
                f"(req:normalization-record); got applied = {self.applied} at "
                f"t = {self.factored_loss}"
            )
        # The parts of the reason order the record itself can show: where every
        # declared efficiency is zero the reason is all_efficiencies_zero (or
        # the earlier source_modes_declared), so factor_one never has every
        # port at zero, and all_efficiencies_zero never has a port above zero.
        some_positive = any(port.declared > 0 for port in self.ports)
        if self.reason is NormalizationReason.ALL_EFFICIENCIES_ZERO and some_positive:
            raise HypothesisError(
                "the reason all_efficiencies_zero is recorded, but a declared "
                "efficiency is above zero (req:normalization-record)"
            )
        if self.reason is NormalizationReason.FACTOR_ONE and not some_positive:
            raise HypothesisError(
                "the reason factor_one is recorded, but every declared efficiency "
                "is zero, for which the earlier reason all_efficiencies_zero "
                "holds (req:normalization-record)"
            )

    @property
    def below_one(self) -> bool:
        """Whether ``t < 1``: the case every consumer obligation is stated for."""
        return self.factored_loss < 1

    @property
    def measurement_statement(self) -> str | None:
        """Return the sentence ``req:normalization-record`` asks for where ``t < 1``.

        ``None`` at ``t = 1``, where the emitted measurement is the receiver's.
        """
        if not self.below_one:
            return None
        return (
            "the blocks, multiclick weights and dark-composed family of this "
            "artifact are those of the normalized station at factored loss "
            f"t = {self.factored_loss}; the receiver's measurement is their "
            "pull-back through the pure-loss channel of transmittance t on the "
            "channel modes (receiver/detector-imperfections/"
            "prop:efficiency-normalization), so a consumer evaluating them on a "
            "state that stands for the receiver's statistics applies that loss "
            "first (req:loss-before-evaluation)"
        )

    def as_payload(self) -> dict[str, object]:
        """Return the JSON-ready form; every rational as an exact ``p/q`` string."""
        return {
            "factored_loss": str(self.factored_loss),
            "factor_declared": self.factor_declared,
            "applied": self.applied,
            "reason": None if self.reason is None else str(self.reason),
            "ports": [
                {
                    "port": port.label,
                    "declared_efficiency": str(port.declared),
                    "compiled_efficiency": str(port.compiled),
                }
                for port in self.ports
            ],
            "measurement": self.measurement_statement,
        }


@dataclass(frozen=True)
class EfficiencyRecord:
    """The emitted ``efficiency_record``: the loss-parameter rows and the normalization.

    ``rows`` is Requirement ``req:efficiency-record``'s record of every
    declared loss parameter, the detector efficiencies AS DECLARED among them;
    ``normalization`` is Requirement ``req:normalization-record``'s.
    """

    rows: tuple[EfficiencyRow, ...]
    normalization: EfficiencyNormalization


def default_factor(largest: Fraction) -> Fraction:
    """Return the default factored loss for the largest declared efficiency.

    Requirement ``req:efficiency-normalization``: ``t = eta_max / (99/100)``,
    formed exactly, where ``eta_max < 99/100``, and ``t = 1`` where
    ``eta_max >= 99/100``. ``largest`` is positive; a request whose
    efficiencies are all zero is compiled at ``t = 1`` before this is asked.
    """
    if largest >= DEFAULT_MARGIN:
        return Fraction(1)
    return largest / DEFAULT_MARGIN


def normalize_efficiencies(
    ports: Sequence[tuple[str, Scalar]],
    *,
    declared_factor: Scalar | None,
    source_modes_declared: bool,
) -> EfficiencyNormalization | str:
    """Return the normalization a request compiles at, or why its factor is refused.

    Requirement ``req:efficiency-normalization``: a request whose receiver
    declares no source modes and some efficiency ``eta_k > 0`` is compiled at
    its normalized station at the factored loss ``t``, the declared
    ``efficiency_normalization`` where there is one and otherwise
    :func:`default_factor` of the largest declared efficiency ``eta_max``
    (``eta_max / (99/100)`` below ``99/100``, one from there on), with port
    ``k`` at the EXACT rational ``eta_k / t`` (one exactly at a port with
    ``eta_k = t``). The record (``req:normalization-record``) says applied
    exactly where ``t < 1``; where not, it names the first reason that holds:
    source modes declared, every efficiency zero, or the factor one, declared
    or by default, with ``factor_declared`` saying which. A declared ``t`` outside
    ``[eta_max, 1]`` is refused; a request with source modes, or whose
    efficiencies are all zero, is compiled at ``t = 1``, and a declared
    ``t < 1`` there is refused with the same reason. The returned string is
    that refusal's detail; the caller words the refusal.

    Every declared number is read as the exact rational it denotes (a
    binary64 value as its dyadic rational), so the quotient is formed exactly
    whatever type the declaration used, and no rounded quotient is formed.
    """
    declared = tuple((label, Fraction(value)) for label, value in ports)
    largest = max((value for _, value in declared), default=Fraction(0))
    factor: Fraction | None = None
    if declared_factor is not None:
        value = to_float(declared_factor)
        if not math.isfinite(value):
            return (
                f"efficiency_normalization = {value} is not a finite number; "
                "the factored loss is declared in [eta_max, 1]"
            )
        factor = Fraction(declared_factor)

    def unchanged(reason: NormalizationReason) -> EfficiencyNormalization:
        return EfficiencyNormalization(
            factored_loss=Fraction(1),
            applied=False,
            reason=reason,
            factor_declared=factor is not None,
            ports=tuple(NormalizedPort(label, eta, eta) for label, eta in declared),
        )

    if source_modes_declared or largest == 0:
        if factor is not None and factor != 1:
            why = (
                "the receiver declares source modes"
                if source_modes_declared
                else "every declared efficiency is zero"
            )
            return (
                f"efficiency_normalization = {factor} is declared, but {why}, so "
                "the receiver is compiled at t = 1 and only t = 1 may be "
                "declared (req:efficiency-normalization)"
            )
        return unchanged(
            NormalizationReason.SOURCE_MODES_DECLARED
            if source_modes_declared
            else NormalizationReason.ALL_EFFICIENCIES_ZERO
        )
    if factor is not None and not largest <= factor <= 1:
        # BOTH SIDES ARE THE EXACT RATIONALS DECLARED (foundations/def:binary64):
        # a binary64 efficiency 0.8 is 3602879701896397/2^52, above 4/5, so a
        # declared t = 4/5 lies below it and would compile a port at eta/t > 1.
        # The detail says so where an efficiency was declared in binary64.
        floats = [
            value for _, value in ports
            if isinstance(value, float) and Fraction(value) == largest
        ]
        hint = (
            ""
            if not floats
            else f"; eta_max is the binary64 value {floats[0]!r} declared, read "
            "as the exact rational it denotes (foundations/def:binary64), so "
            "declare t as that same value or every efficiency as an exact "
            "fraction"
        )
        return (
            f"efficiency_normalization = {factor} lies outside [eta_max, 1] = "
            f"[{largest}, 1]; the factored loss is at least the largest declared "
            "efficiency and at most one (def:normalized-station)" + hint
        )
    t = default_factor(largest) if factor is None else factor
    if t == 1:
        return unchanged(NormalizationReason.FACTOR_ONE)
    return EfficiencyNormalization(
        factored_loss=t,
        applied=True,
        reason=None,
        factor_declared=factor is not None,
        ports=tuple(NormalizedPort(label, eta, eta / t) for label, eta in declared),
    )
