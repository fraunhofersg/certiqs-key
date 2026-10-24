"""Full binary64 admission, including range rather than only significand width.

A value such as 2^-1075 must not pass the helper and reach
accumulation. These boundaries exercise the shared predicate and its
real first-form consumer, without changing any frozen numerical target.
"""

import math
import random
import struct
from fractions import Fraction as F

import pytest

from certiqs_key.foundations.errors import MalformedInputError
from certiqs_key.foundations.exact import identity, is_binary64, scale
from certiqs_key.protocol_compiler import weights as weighting
from certiqs_key.protocol_compiler.spec import Party, PublicChoices
from certiqs_key.protocol_compiler.weights import weighted_family


@pytest.mark.parametrize(
    ("value", "representable"),
    [
        (F(0), True),
        (F(1, 1 << 1074), True),
        (F(1, 1 << 1075), False),
        (F(3, 1 << 1075), False),
        (F((1 << 52) - 1, 1 << 1074), True),
        (F(1, 1 << 1022), True),
        (F((1 << 53) - 1, 1 << 1075), False),
        (F(1 << 1023), True),
        (F(((1 << 53) - 1) << 971), True),
        (F(1 << 1024), False),
        (F((1 << 1024) - 1), False),
        (F((1 << 53) + 1), False),
        (F(1, 3), False),
    ],
)
def test_integer_predicate_matches_binary64_boundaries(
    value: F, representable: bool
) -> None:
    assert is_binary64(value) is representable
    assert is_binary64(-value) is representable


def test_every_sampled_finite_bit_pattern_is_admitted_exactly() -> None:
    rng = random.Random(80291)
    for _ in range(1000):
        value = struct.unpack(">d", rng.getrandbits(64).to_bytes(8, "big"))[0]
        if math.isfinite(value):
            assert is_binary64(F.from_float(value))


def _choices(first: F) -> PublicChoices:
    labels = ("tiny", "left", "right")
    return PublicChoices(
        party=Party.ALICE,
        choices=labels,
        weights=dict(zip(labels, (first, F(1, 2), F(1, 2)), strict=True)),
        conditional_alphabets=dict.fromkeys(labels, ("only",)),
        conditional_elements={label: {"only": identity(1)} for label in labels},
        joint_labels={("only", label): label for label in labels},
    )


@pytest.mark.parametrize("first", [F(1, 1 << 1075), F(1 << 1024)])
def test_off_range_weight_refuses_before_accumulation_or_products(
    first: F, monkeypatch: pytest.MonkeyPatch
) -> None:
    choices = _choices(first)

    def forbidden_round(value: F) -> F:
        raise AssertionError("an off-range weight reached accumulation")

    monkeypatch.setattr(weighting, "round_to_binary64", forbidden_round)
    with pytest.raises(MalformedInputError, match=r"q\('tiny'\).*binary64"):
        weighted_family(choices)


def test_underflowed_exact_product_is_not_representable() -> None:
    """A normalized weight list whose smallest weight times 1/2 underflows.

    The weights are ``2**-1074, 2**-1074, 2**-1073, ..., 2**-1``: every
    partial sum of their declared-order accumulation is a power of two, and the
    exact sum is 1, so ``req:weight-list`` admits the list (the list
    ``2**-1074, 1/2, 1/2`` sums to more than 1 and is refused as
    ``choice_weights_not_normalized`` before any product is decided). The
    product of the first weight with the entry ``1/2`` is ``2**-1075``, below
    the smallest subnormal.
    """
    smallest = F(1, 1 << 1074)
    half = F(1, 2)
    assert is_binary64(smallest) and is_binary64(half)
    assert not is_binary64(smallest * half)
    weights = (smallest, *(F(1, 1 << k) for k in range(1074, 0, -1)))
    assert sum(weights) == 1
    labels = ("tiny", *(f"w{k}" for k in range(1074, 0, -1)))
    choices = PublicChoices(
        party=Party.ALICE,
        choices=labels,
        weights=dict(zip(labels, weights, strict=True)),
        conditional_alphabets=dict.fromkeys(labels, ("a", "b")),
        conditional_elements={
            label: {"a": scale(half, identity(1)), "b": scale(half, identity(1))}
            for label in labels
        },
    )
    family = weighted_family(choices)
    assert family.refusal is None
    decision = weighting.decide_emission(family)
    assert not decision.every_product_is_binary64
    assert decision.refusal is not None
    assert str(decision.refusal.reason) == "emitted_value_not_representable"
