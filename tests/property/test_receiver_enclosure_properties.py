"""Properties of the receiver's enclosures, over random data.

``receiver/lem:enclosure-arithmetic``: every rule, applied to complex
enclosures of numbers, gives a complex enclosure of the result -- decided here
exactly, on random Gaussian rationals placed anywhere inside random balls.
``receiver/detector-imperfections/prop:noise-floor`` (i): with loss and a
dark-count probability in (0, 1) in every port, every element of the
dark-composed reference is decided positive definite, over random dyadic
devices; and ``receiver/thm:exact-and-evaluated`` (vi): a coarse enclosure
contains the binary64 evaluation entry by entry.
"""

from __future__ import annotations

from dataclasses import replace
from fractions import Fraction

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from receiver_povm_support import bb84_channel_only_request

from certiqs_key.foundations.reference import enclosure_pd
from certiqs_key.receiver import construct_receiver
from certiqs_key.receiver.construct import _dark_channel
from certiqs_key.receiver.enclosure import Ball
from certiqs_key.receiver.reference import dark_composed_reference
from certiqs_key.receiver.request import validate_request

pytestmark = pytest.mark.contract

_RATIONALS = st.fractions(min_value=-4, max_value=4, max_denominator=1000)
_FRACTION_OF_RADIUS = st.fractions(min_value=0, max_value=1, max_denominator=50)


@st.composite
def _enclosed(draw: st.DrawFn) -> tuple[Ball, Fraction, Fraction]:
    """Return a ball and an exact point of it (re, im)."""
    re = draw(_RATIONALS)
    im = draw(_RATIONALS)
    radius = draw(st.sampled_from([Fraction(0), Fraction(1, 2**10), Fraction(1, 3)]))
    # A point at distance <= radius: |(a, b)| <= radius via |a| + |b| <= radius.
    a = draw(_FRACTION_OF_RADIUS) * radius
    b = draw(_FRACTION_OF_RADIUS) * (radius - a)
    sign_a = draw(st.sampled_from([1, -1]))
    sign_b = draw(st.sampled_from([1, -1]))
    return Ball(re, im, radius), re + sign_a * a, im + sign_b * b


def _holds(ball: Ball, re: Fraction, im: Fraction) -> bool:
    dx = re - ball.re
    dy = im - ball.im
    return dx * dx + dy * dy <= ball.radius * ball.radius


@settings(max_examples=150, deadline=None)
@given(_enclosed(), _enclosed())
def test_every_rule_encloses_its_result(
    first: tuple[Ball, Fraction, Fraction], second: tuple[Ball, Fraction, Fraction]
) -> None:
    """lem:enclosure-arithmetic (i)-(iii), with the radius rounded up."""
    x, xr, xi = first
    y, yr, yi = second
    assert _holds(x, xr, xi) and _holds(y, yr, yi)
    assert _holds(x + y, xr + yr, xi + yi)
    assert _holds(x - y, xr - yr, xi - yi)
    assert _holds(-x, -xr, -xi)
    assert _holds(x.conjugate(), xr, -xi)
    assert _holds(x * y, xr * yr - xi * yi, xr * yi + xi * yr)
    reciprocal = x.reciprocal(64)
    if reciprocal is not None:
        squared = xr * xr + xi * xi
        assert squared != 0
        assert _holds(reciprocal, xr / squared, -xi / squared)


_EFFICIENCY = st.sampled_from([Fraction(k, 8) for k in range(1, 8)])
_DARK = st.sampled_from([Fraction(1, 2**j) for j in (3, 6, 10)])


@settings(max_examples=12, deadline=None)
@given(
    st.lists(_EFFICIENCY, min_size=4, max_size=4),
    st.lists(_DARK, min_size=4, max_size=4),
    st.sampled_from([1, 2]),
)
def test_a_noise_floor_makes_every_element_decided_definite(
    efficiencies: list[Fraction], dark_counts: list[Fraction], cutoff: int
) -> None:
    """prop:noise-floor (i) and (iii), decided through foundations/lem:enclosure-psd.

    Declared at the factored loss one, so that the detectors keep the loss
    that makes the floor (detector-imperfections/rem:normalization-scope).
    """
    request = replace(
        bb84_channel_only_request(
            photon_cutoff=cutoff,
            efficiencies=tuple(efficiencies),
            dark_counts=tuple(dark_counts),
        ),
        efficiency_normalization=Fraction(1),
    )
    emission = construct_receiver(request)
    assert emission.artifact is not None
    for family in emission.artifact.photon_blocks:
        reference = family.reference.reference
        assert reference is not None and reference.decide().usable
        for block in reference.blocks:
            for element in block.elements:
                assert enclosure_pd(element.centre, element.radii)


@settings(max_examples=8, deadline=None)
@given(
    st.lists(_EFFICIENCY, min_size=4, max_size=4),
    st.lists(_DARK, min_size=4, max_size=4),
)
def test_a_coarse_enclosure_contains_the_evaluation(
    efficiencies: list[Fraction], dark_counts: list[Fraction]
) -> None:
    """thm:exact-and-evaluated (vi), at a leaf precision of 2^-24 and dyadic data."""
    request = bb84_channel_only_request(
        photon_cutoff=2,
        efficiencies=tuple(efficiencies),
        dark_counts=tuple(dark_counts),
    )
    validated = validate_request(request)
    references = dark_composed_reference(validated, _dark_channel(validated), bits=24)
    emission = construct_receiver(request)
    assert emission.artifact is not None
    for family, offered in zip(
        emission.artifact.photon_blocks, references, strict=True
    ):
        assert offered.reference is not None
        for (_, letters), block in zip(
            family.dark_composed, offered.reference.blocks, strict=True
        ):
            for (_, matrix), element in zip(letters, block.elements, strict=True):
                for i, row in enumerate(element.centre):
                    for j, centre in enumerate(row):
                        value = complex(matrix[i][j])
                        ball = Ball(centre.re, centre.im, element.radii[i][j])
                        assert ball.contains(value)
