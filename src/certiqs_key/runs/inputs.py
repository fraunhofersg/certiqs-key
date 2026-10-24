"""Prepare convenient numerical inputs at the declaring boundary.

The core still decides its declared data exactly. This adapter owns parsing
and records both conversion to binary64 and preparation on the declared
lattice. Probability normalization uses foundations.snap's existing family table;
directed bounds use exact integer rounding, never nearest rounding. A recorded
displacement is a modelling change, not a bound on a key-rate change.

Every refusal here is a :class:`~certiqs_key.runs.errors.RunInputError` with a
code from :class:`~certiqs_key.runs.errors.RunInputReason`; the two
``AssertionError`` sites are invariants of this module, not input checks.
"""

from __future__ import annotations

import math
import struct
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from typing import TYPE_CHECKING, Any, Literal, cast

import numpy as np

from certiqs_key.foundations.numeric import completeness_residue
from certiqs_key.foundations.snap import snap_family_exact
from certiqs_key.runs.errors import (
    RunInputKeyError,
    RunInputReason,
    RunInputTypeError,
    RunInputValueError,
)

if TYPE_CHECKING:
    from certiqs_key.runs.config import RunConfig
    from certiqs_key.runs.pipeline import Preparation, SliceRefusal, SliceResult

type NumericInput = int | float | Decimal | Fraction | str


def prepare_config_inputs(
    inputs: Mapping[str, Any], *, numeric_device_fields: Sequence[str] = ()
) -> dict[str, Any]:
    """Convert configuration scalars without changing exact rational meanings."""
    prepared = dict(inputs)
    records = list(prepared.get("input_preparation", ()))

    def number(value: Any, site: str, *, binary64: bool = False) -> Any:
        exact = exact_input(value)
        try:
            # float() of a Fraction beyond binary64 raises rather than
            # returning an infinity; both are the same refusal.
            result = float(exact) if binary64 else exact
        except OverflowError:
            result = math.inf
        if binary64 and not math.isfinite(result):
            raise RunInputValueError(
                f"{site} is outside the binary64 range",
                reason=RunInputReason.OUTSIDE_BINARY64,
            )
        if type(value) is not type(result) or exact != Fraction(result):
            records.append(
                {
                    "site": site,
                    "rule": "numeric_input_conversion",
                    "input_type": type(value).__name__,
                    "input_value": str(exact),
                    "prepared_value": str(Fraction(result)),
                    "total_displacement": str(Fraction(result) - exact),
                }
            )
        return result

    for section in ("model", "device"):
        if section not in prepared:
            continue
        converted: dict[str, Any] = {}
        for name, value in prepared[section].items():
            site = f"{section}.{name}"
            if isinstance(value, Mapping):
                converted[name] = {
                    port: number(entry, f"{site}.{port}")
                    for port, entry in value.items()
                }
            elif (
                section == "device"
                and isinstance(value, str)
                and name not in numeric_device_fields
            ):
                # A string is a name until the instance's parameter table says
                # this field is numeric. Its spelling is not a type declaration.
                converted[name] = value
            else:
                converted[name] = number(value, site)
        prepared[section] = converted
    if "completeness_budget" in prepared:
        prepared["completeness_budget"] = number(
            prepared["completeness_budget"], "completeness_budget"
        )
    if "min_model_pass_probability" in prepared:
        # meat-core/req:unreachable-acceptance-set's tau, an exact rational;
        # a binary64 or decimal input is converted exactly and recorded.
        prepared["min_model_pass_probability"] = number(
            prepared["min_model_pass_probability"], "min_model_pass_probability"
        )
    from certiqs_key.runs.config import NO_DECLARED_TOLERANCE

    if (
        "declared_tolerance" in prepared
        and prepared["declared_tolerance"] is not NO_DECLARED_TOLERANCE
    ):
        prepared["declared_tolerance"] = number(
            prepared["declared_tolerance"], "declared_tolerance", binary64=True
        )
    if "eps_auth" in prepared:
        # A-AUTH's error bound is a binary64 datum of the engine, as eps_pa and
        # eps_ev are; an exact or integer input is converted and recorded.
        prepared["eps_auth"] = number(prepared["eps_auth"], "eps_auth", binary64=True)
    prepared["input_preparation"] = tuple(records)
    return prepared


def prepare_config_probabilities(
    config: RunConfig,
    groups: Sequence[Sequence[str]],
    *,
    lattice_exponent: int,
    numeric_device_fields: Sequence[str] = (),
) -> RunConfig:
    """Prepare instance-declared device probability groups before compilation."""
    from dataclasses import replace

    from certiqs_key.runs.config import RunConfig

    config = RunConfig.from_inputs(
        numeric_device_fields=tuple(numeric_device_fields),
        **{field: getattr(config, field) for field in config.__dataclass_fields__},
    )
    device = dict(config.device)
    records = list(config.input_preparation)
    for group in groups:
        # from_inputs stores exact Fractions, but its conversion record keeps
        # float origins available across serialization. Only a matching latest
        # conversion authorizes the rounding-cell interpretation.
        values: list[NumericInput] = []
        for name in group:
            if name not in device:
                raise RunInputKeyError(
                    f"device.{name} is not declared; it is one of the "
                    f"probability family {list(group)}, prepared together",
                    reason=RunInputReason.MISSING_PARAMETER,
                )
            value: Any = device[name]
            for record in reversed(records):
                if record.get("site") != f"device.{name}":
                    continue
                if (
                    record.get("rule") == "numeric_input_conversion"
                    and record.get("input_type") == "float"
                    and Fraction(record["prepared_value"]) == value
                ):
                    value = float(Fraction(record["input_value"]))
                break
            values.append(cast(NumericInput, value))
        result = prepare_probabilities(
            values,
            tolerance=config.declared_tolerance,
            lattice_exponent=lattice_exponent,
            site="device." + "+".join(group),
        )
        original = tuple(device[name] for name in group)
        if result.values != original:
            records.append(result.record)
        device.update(zip(group, result.values, strict=True))
    return replace(config, device=device, input_preparation=tuple(records))


def attach_input_preparation[T: Preparation | SliceResult | SliceRefusal](
    outcome: T, config: RunConfig
) -> T:
    """Carry the declaring-boundary record through existing preparation/run slots."""
    from certiqs_key.runs.pipeline import SliceRefusal

    if not config.input_preparation or isinstance(outcome, SliceRefusal):
        return outcome
    from dataclasses import replace

    record = dict(outcome.rows_adaptation or {})
    record["input_preparation"] = list(config.input_preparation)
    return cast(T, replace(outcome, rows_adaptation=record))


def attach_protocol_document[T: Preparation | SliceResult | SliceRefusal](
    outcome: T, record: Mapping[str, Any]
) -> T:
    """Carry a protocol document's record block onto an outcome (record 0.21.0).

    Beside :func:`attach_input_preparation`, and unlike it ALSO ONTO A REFUSAL:
    a refused run must still name the document it was lowered from, or a
    reader of the refusal cannot tell which protocol was refused. The block is
    the document layer's (``instances/declared``) and is carried verbatim; the
    run tier never reads it.
    """
    from dataclasses import replace

    return replace(outcome, protocol_document=dict(record))


def exact_input(value: NumericInput) -> Fraction:
    """Read a decimal/fraction exactly; a float denotes its actual stored value.

    Numeric strings are accepted here only at an explicitly numeric field.
    Names in a device configuration must never pass through this function.
    """
    if isinstance(value, bool):
        raise RunInputTypeError(
            "a Boolean is not a numerical input", reason=RunInputReason.NOT_A_NUMBER
        )
    if not isinstance(value, int | float | Decimal | Fraction | str):
        raise RunInputTypeError(
            f"unsupported numerical input: {type(value).__name__}",
            reason=RunInputReason.NOT_A_NUMBER,
        )
    try:
        return Fraction(value)
    except (ValueError, OverflowError, ZeroDivisionError) as error:
        if _names_a_non_finite_float(value):
            raise RunInputValueError(
                f"a numerical input must be finite; got {value!r}",
                reason=RunInputReason.NOT_FINITE,
            ) from error
        raise RunInputValueError(
            f"{value!r} is not a decimal or a fraction",
            reason=RunInputReason.UNREADABLE_NUMBER,
        ) from error


def _names_a_non_finite_float(value: NumericInput) -> bool:
    """Whether ``value`` is, or spells, an infinity or a NaN."""
    try:
        return not math.isfinite(float(value))
    except (ValueError, OverflowError):
        return False


@dataclass(frozen=True)
class PreparedProbabilities:
    """Normalized binary64 probabilities and their declaration record."""

    values: tuple[Fraction, ...]
    record: Mapping[str, Any]


def _float_cell(value: float) -> tuple[Fraction, Fraction, bool]:
    """Exact nearest-even rounding cell, clipped to probability space.

    Structural zero is fixed, including negative zero. Endpoint inclusion
    follows the binary64 significand parity, including subnormal numbers.
    The next-and-previous-float construction handles asymmetric power-of-two
    cells without approximating a half-ULP in floating-point arithmetic.
    """
    exact = Fraction(value)
    if value == 0:
        return exact, exact, True
    lower = max(Fraction(), (Fraction(math.nextafter(value, -math.inf)) + exact) / 2)
    upper = min(Fraction(1), (Fraction(math.nextafter(value, math.inf)) + exact) / 2)
    even = int.from_bytes(struct.pack(">d", value), "big") % 2 == 0
    return lower, upper, even


def prepare_probabilities(
    values: Sequence[NumericInput],
    *,
    tolerance: float,
    lattice_exponent: int,
    site: str,
    preserve_exact: bool = True,
) -> PreparedProbabilities:
    """Prepare a probability family with exact normalization and recorded moves.

    The caller supplies its existing tolerance and lattice choice. Exact input
    defects are checked before a float conversion could hide them. Float inputs
    additionally denote their explicit nearest-even rounding cells; this is a
    versioned front-end representation policy, separate from the core tolerance.
    Structural zeros and positive support are preserved or preparation refuses.
    Already exactly admissible binary64 inputs are preserved,
    including values finer than the nominal preparation lattice, so existing
    declarations and frozen runs do not change merely by using this adapter.
    A caller whose later arithmetic needs the values ON the lattice passes
    ``preserve_exact=False``: the family is then snapped at the lattice
    exponent even when it is already exactly admissible in binary64, by the
    same rule, guard and record (``instances/common/wcp.py``, the tagged WCP
    source's preparation, whose category masses must lie on its lattice).
    """
    if not values:
        raise RunInputValueError(
            f"{site}: a probability family must be nonempty",
            reason=RunInputReason.PROBABILITY_FAMILY_EMPTY,
        )
    if (
        type(tolerance) is not float
        or not math.isfinite(tolerance)
        or not 0 <= tolerance < 1
    ):
        raise RunInputValueError(
            "tolerance must be a finite float in [0, 1)",
            reason=RunInputReason.PREPARATION_ARGUMENT_INVALID,
        )
    if type(lattice_exponent) is not int or not 0 <= lattice_exponent <= 53:
        raise RunInputValueError(
            "lattice_exponent must be an integer in [0, 53]",
            reason=RunInputReason.PREPARATION_ARGUMENT_INVALID,
        )
    original = tuple(exact_input(value) for value in values)
    if any(value < 0 or value > 1 for value in original):
        raise RunInputValueError(
            f"{site}: probabilities must lie in [0, 1]",
            reason=RunInputReason.PROBABILITY_OUTSIDE_UNIT_INTERVAL,
        )
    defect = abs(sum(original, Fraction()) - 1)
    cells = [
        _float_cell(value) if isinstance(value, float) else (exact, exact, True)
        for value, exact in zip(values, original, strict=True)
    ]
    lower = sum((cell[0] for cell in cells), Fraction())
    upper = sum((cell[1] for cell in cells), Fraction())
    closed = all(cell[2] for cell in cells)
    representation_admitted = (lower < 1 < upper) or (
        closed and (lower == 1 or upper == 1)
    )
    if defect > Fraction(tolerance) and not representation_admitted:
        raise RunInputValueError(
            f"{site}: input probability normalization exceeds the declared "
            "tolerance and the float rounding-cell enclosure",
            reason=RunInputReason.NORMALIZATION_EXCEEDS_TOLERANCE,
        )
    converted = tuple(Fraction(float(value)) for value in original)
    partial = Fraction()
    already_exact = (
        preserve_exact
        and sum(original, Fraction()) == 1
        and original == converted
    )
    for value in converted:
        partial += value
        already_exact = already_exact and Fraction(float(partial)) == partial
    snaps: list[dict[str, Any]] = []
    snap_guard = tolerance
    if already_exact:
        prepared = converted
    else:
        family = [np.asarray([[float(value)]]) for value in original]
        # Admission was decided exactly above. The shared routine measures
        # completeness in floating-point arithmetic, which can round even for
        # exactly normalized rational inputs. Its local guard lets it execute
        # the already-authorized scalar preparation; it admits no new input.
        # This guard is recorded separately and is never passed to the core.
        snap_guard = max(tolerance, completeness_residue(family))
        result, records = snap_family_exact(
            family, tolerance=snap_guard, lattice_exponent=lattice_exponent, site=site
        )
        prepared = tuple(Fraction(float(element[0, 0])) for element in result)
        snaps = [record.as_record() for record in records]
    if sum(prepared, Fraction()) != 1 or any(value < 0 for value in prepared):
        raise AssertionError(
            "the shared probability preparation violated normalization"
        )
    if any(
        before == 0 and after != 0
        for before, after in zip(original, prepared, strict=True)
    ):
        raise AssertionError("probability preparation changed a structural zero")
    if any(
        before > 0 and after == 0
        for before, after in zip(original, prepared, strict=True)
    ):
        raise RunInputValueError(
            f"{site}: probability preparation would lose positive support "
            "on the selected lattice",
            reason=RunInputReason.POSITIVE_SUPPORT_LOST,
        )
    return PreparedProbabilities(
        prepared,
        {
            "site": site,
            "rule": "shared_family_snap",
            "input_types": [type(value).__name__ for value in values],
            "input_values": [str(value) for value in original],
            "binary64_values": [str(value) for value in converted],
            "prepared_values": [str(value) for value in prepared],
            "conversion_displacement": [
                str(b - a) for a, b in zip(original, converted, strict=True)
            ],
            "total_displacement": [
                str(b - a) for a, b in zip(original, prepared, strict=True)
            ],
            "normalization_defect": str(defect),
            "representation_policy": "binary64_nearest_even_cells_v1",
            "rounding_cells": [
                {"lower": str(lo), "upper": str(hi), "endpoints_closed": incl}
                for lo, hi, incl in cells
            ],
            "normalization_interval": [str(lower), str(upper)],
            "representation_admitted": representation_admitted,
            "admission": "declared_tolerance"
            if defect <= Fraction(tolerance)
            else "float_rounding_cells",
            "shared_snap_guard": snap_guard,
            "declared_tolerance": tolerance,
            "lattice_exponent": lattice_exponent,
            "snaps": snaps,
        },
    )


def prepare_bound(
    value: NumericInput,
    *,
    direction: Literal["lower", "upper"],
    lattice_exponent: int,
    site: str,
) -> tuple[Fraction, dict[str, Any]]:
    """Round a unit-interval bound outward using exact rational arithmetic."""
    if direction not in ("lower", "upper"):
        raise RunInputValueError(
            "direction must be lower or upper",
            reason=RunInputReason.PREPARATION_ARGUMENT_INVALID,
        )
    if type(lattice_exponent) is not int or not 0 <= lattice_exponent <= 53:
        raise RunInputValueError(
            "lattice_exponent must be an integer in [0, 53]",
            reason=RunInputReason.PREPARATION_ARGUMENT_INVALID,
        )
    original = exact_input(value)
    if not 0 <= original <= 1:
        raise RunInputValueError(
            f"{site}: a probability bound must lie in [0, 1]",
            reason=RunInputReason.PROBABILITY_OUTSIDE_UNIT_INTERVAL,
        )
    scale = 1 << lattice_exponent
    scaled = original * scale
    numerator = math.floor(scaled) if direction == "lower" else math.ceil(scaled)
    prepared = Fraction(numerator, scale)
    return prepared, {
        "site": site,
        "rule": f"round_{direction}_bound_outward",
        "input_type": type(value).__name__,
        "input_value": str(original),
        "prepared_value": str(prepared),
        "total_displacement": str(prepared - original),
        "lattice_exponent": lattice_exponent,
    }
