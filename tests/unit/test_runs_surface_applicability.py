"""``ParameterSpec.applies_when``: validation and serialisation.

The field says when a parameter has an effect, as a condition on OTHER
parameters of the same table. It is advisory metadata for a consumer's form and
changes nothing a run does, so what is tested here is the two things a
consumer relies on: a table whose conditions do not resolve is refused, and the
payload carries the conditions in the house conventions (``null`` when absent,
rationals as ``"p/q"``). That every instance's own table resolves is asserted
over the discovered instances in ``test_instance_surface.py``.
"""

from __future__ import annotations

import json
from dataclasses import replace
from fractions import Fraction

import pytest

from certiqs_key.runs.surface import (
    Kind,
    ParameterSpec,
    Quantity,
    Section,
    check_applicability,
    check_keys,
    choices,
    closed_interval,
    when,
)

MODEL = ParameterSpec(
    name="model",
    section=Section.DEVICE,
    kind=Kind.CHOICE,
    quantity=Quantity.CHOICE,
    unit=None,
    default="a",
    domain=choices(("a", "first"), ("b", "second")),
    snapped=False,
    meaning="Which model",
)
RATE = ParameterSpec(
    name="rate",
    section=Section.DEVICE,
    kind=Kind.FRACTION,
    quantity=Quantity.PROBABILITY,
    unit=None,
    default=Fraction(1, 2),
    domain=closed_interval(0, 1),
    snapped=False,
    meaning="A rate",
)
PORTS = ParameterSpec(
    name="ports",
    section=Section.DEVICE,
    kind=Kind.PER_PORT_FRACTION,
    quantity=Quantity.EFFICIENCY,
    unit=None,
    default={"p": Fraction(1)},
    domain=closed_interval(0, 1),
    snapped=False,
    meaning="Per port",
    per_port_labels=("p",),
)
KNOB = ParameterSpec(
    name="knob",
    section=Section.DEVICE,
    kind=Kind.FRACTION,
    quantity=Quantity.PROBABILITY,
    unit=None,
    default=Fraction(0),
    domain=closed_interval(0, 1),
    snapped=False,
    meaning="Used under model b only",
)


def _table(condition: dict[str, tuple[object, ...]]) -> tuple[ParameterSpec, ...]:
    return (MODEL, RATE, PORTS, replace(KNOB, applies_when=when(condition)))


def test_absent_means_always_and_serialises_as_null() -> None:
    assert KNOB.applies_when is None
    assert KNOB.as_payload()["applies_when"] is None
    check_applicability((MODEL, KNOB), "toy")


def test_a_condition_serialises_as_name_to_allowed_values() -> None:
    table = _table({"model": ("b",), "rate": (Fraction(1, 3), Fraction(1))})
    check_applicability(table, "toy")
    payload = table[-1].as_payload()
    assert payload["applies_when"] == {"model": ["b"], "rate": ["1/3", "1"]}
    assert json.loads(json.dumps(payload)) == payload


def test_when_keeps_the_spec_hashable() -> None:
    spec = replace(KNOB, applies_when=when({"model": ["b"]}))
    assert spec.applies_when == (("model", ("b",)),)
    hash(spec)


@pytest.mark.parametrize(
    ("condition", "match"),
    [
        ({"missing": ("b",)}, "not a parameter"),
        ({"knob": (Fraction(0),)}, "refers to itself"),
        ({"model": ("c",)}, "outside"),
        ({"rate": (Fraction(2),)}, "outside"),
        ({"model": ()}, "no value"),
        ({"ports": (Fraction(1),)}, "per-port"),
    ],
)
def test_a_condition_that_does_not_resolve_is_refused(
    condition: dict[str, tuple[object, ...]], match: str
) -> None:
    with pytest.raises(ValueError, match=match):
        check_applicability(_table(condition), "toy")


def test_an_empty_condition_is_refused_in_favour_of_none() -> None:
    table = (MODEL, replace(KNOB, applies_when=()))
    with pytest.raises(ValueError, match="empty"):
        check_applicability(table, "toy")


def test_a_repeated_name_is_refused() -> None:
    table = (MODEL, replace(KNOB, applies_when=(("model", ("a",)), ("model", ("b",)))))
    with pytest.raises(ValueError, match="twice"):
        check_applicability(table, "toy")


def test_an_inapplicable_parameter_is_still_accepted_and_checked() -> None:
    """Advisory only: the key check ignores the field entirely."""
    table = _table({"model": ("b",)})
    check_keys(
        Section.DEVICE, {"model": "a", "knob": Fraction(1, 4)}, table, "toy"
    )
    with pytest.raises(ValueError, match="knob"):
        check_keys(Section.DEVICE, {"model": "a", "knob": Fraction(2)}, table, "toy")
