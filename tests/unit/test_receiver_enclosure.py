"""Complex enclosures, their leaves, the exact radicals, and the angle presentation.

Contract tests of ``receiver/def:complex-enclosure`` and
``receiver/lem:enclosure-arithmetic`` (their implementation in
:mod:`certiqs_key.receiver.enclosure`), of the exact arithmetic
``receiver/req:exact-route-decision`` (ii) asks for
(:mod:`certiqs_key.receiver.radicals`), and of the angle presentation of
``interface.yaml`` ``parameters.units`` (b).
"""

from __future__ import annotations

import math
from fractions import Fraction

import numpy as np
import pytest
from receiver_povm_support import MACHINE_AGREEMENT, TOLERANCE

from certiqs_key.receiver import (
    Beamsplitter,
    GenericBlock,
    Loss,
    Mirror,
    ModeRouting,
    PhaseShifter,
    Polarizer,
    PolarizingBeamsplitter,
    Retarder,
    Rotator,
)
from certiqs_key.receiver.catalogue import Component
from certiqs_key.receiver.enclosure import (
    Ball,
    _round_up,
    angle_enclosure,
    hermitian_centred,
    pi_bounds,
    sqrt_enclosure,
)
from certiqs_key.receiver.errors import MalformedInputError
from certiqs_key.receiver.generic import (
    BallField,
    FloatField,
    RecordingField,
    element_matrix,
)
from certiqs_key.receiver.numerics import PiMultiple, to_float
from certiqs_key.receiver.radicals import NotRepresented, RadicalField, coprime_base

pytestmark = pytest.mark.contract

#: pi to 60 decimals, as a reference for the bounds (a published constant).
PI_60 = Fraction("3.141592653589793238462643383279502884197169399375105820974944")


def test_pi_bounds_bracket_pi_tightly() -> None:
    """The one irrational constant enters through rational bounds only."""
    lo, hi = pi_bounds(128)
    assert lo < PI_60 + Fraction(1, 10**59) and PI_60 - Fraction(1, 10**59) < hi
    assert hi - lo <= Fraction(1, 2**128)


@pytest.mark.parametrize(
    "value", [Fraction(1, 2), Fraction(2), Fraction(9, 10), Fraction(1, 3)]
)
def test_a_square_root_enclosure_brackets_the_root(value: Fraction) -> None:
    """def:complex-enclosure: ``(c - r)^2 <= p <= (c + r)^2``, a rational centre."""
    ball = sqrt_enclosure(value, 64)
    assert ball.im == 0 and ball.radius > 0
    assert (ball.re - ball.radius) ** 2 <= value <= (ball.re + ball.radius) ** 2


@pytest.mark.parametrize(
    "value", [Fraction(0), Fraction(1), Fraction(9, 4), Fraction(1, 16)]
)
def test_a_square_root_enclosure_is_exact_on_squares(value: Fraction) -> None:
    """def:complex-enclosure: exact where ``p`` is the square of a rational."""
    ball = sqrt_enclosure(value)
    assert ball.is_exact and ball.re * ball.re == value


@pytest.mark.parametrize(
    "angle",
    [
        PiMultiple(Fraction(0)),
        PiMultiple(Fraction(1, 2)),
        PiMultiple(Fraction(1)),
        PiMultiple(Fraction(3, 2)),
        PiMultiple(Fraction(7, 2)),
        Fraction(0),
        0.0,
    ],
)
def test_an_angle_enclosure_is_exact_at_multiples_of_half_pi(angle: object) -> None:
    """def:complex-enclosure: exact where ``theta = c pi`` with ``2c`` an integer."""
    cos, sin = angle_enclosure(angle)  # type: ignore[arg-type]
    assert cos.is_exact and sin.is_exact
    assert cos.re * cos.re + sin.re * sin.re == 1


@pytest.mark.parametrize(
    "angle",
    [
        PiMultiple(Fraction(1, 8)),
        PiMultiple(Fraction(1, 24)),
        PiMultiple(Fraction(-7, 3)),
        math.pi / 8,
        5.5,
        1e-12,
        Fraction(6),
    ],
)
def test_an_angle_enclosure_contains_the_values(angle: object) -> None:
    """def:complex-enclosure: coarse enclosures contain the binary64 values.

    At 2^-30 the radius dominates the binary64 error of ``math.cos``, so the
    containment is decided, not compared to a tolerance.
    """
    cos, sin = angle_enclosure(angle, 30)  # type: ignore[arg-type]
    value = to_float(angle)  # type: ignore[arg-type]
    assert cos.contains(complex(math.cos(value)))
    assert sin.contains(complex(math.sin(value)))
    fine_cos, _ = angle_enclosure(angle, 128)  # type: ignore[arg-type]
    assert fine_cos.radius <= Fraction(1, 2**120)
    assert abs(float(fine_cos.re) - math.cos(value)) <= 1e-15


def test_sums_products_and_conjugates_follow_the_rules() -> None:
    """lem:enclosure-arithmetic (i), (ii): the stated centres and radii."""
    x = Ball(Fraction(1, 2), Fraction(-1, 3), Fraction(1, 2**70))
    y = Ball(Fraction(3), Fraction(1, 5), Fraction(1, 2**71))
    total = x + y
    assert (total.re, total.im) == (Fraction(7, 2), Fraction(-2, 15))
    assert total.radius >= x.radius + y.radius
    product = x * y
    assert product.re == Fraction(1, 2) * 3 + Fraction(1, 3) * Fraction(1, 5)
    expected = x.l1 * y.radius + x.radius * y.l1 + x.radius * y.radius
    assert expected <= product.radius <= expected * (1 + Fraction(1, 2**62))
    assert x.conjugate().im == Fraction(1, 3) and x.conjugate().radius == x.radius


def test_exact_operands_give_exact_results() -> None:
    """lem:enclosure-arithmetic (iv): a node with exact operands is exact."""
    x = Ball(Fraction(2, 3), Fraction(1, 7))
    y = Ball(Fraction(-5, 11))
    for value in (x + y, x - y, x * y, -x, x.conjugate()):
        assert value.is_exact
    reciprocal = x.reciprocal()
    assert reciprocal is not None and reciprocal.is_exact
    assert (x * reciprocal).re == 1 and (x * reciprocal).im == 0


def test_a_reciprocal_is_refused_where_the_radius_reaches_zero() -> None:
    """lem:enclosure-arithmetic (iii): no ``l`` with ``r < l``, no enclosure."""
    assert Ball(Fraction(1, 10), Fraction(0), Fraction(1, 5)).reciprocal() is None
    assert Ball(Fraction(0)).reciprocal() is None
    ball = Ball(Fraction(4), Fraction(0), Fraction(1, 2**80)).reciprocal()
    assert ball is not None and ball.contains(complex(0.25))


def test_a_radius_is_rounded_up_never_down() -> None:
    """A larger radius still encloses (def:complex-enclosure); zero stays zero."""
    assert _round_up(Fraction(0)) == 0
    for value in (
        Fraction(1, 3),
        Fraction(10**40, 7),
        Fraction(3, 2**300),
        Fraction(5),
    ):
        rounded = _round_up(value)
        assert value <= rounded <= value * (1 + Fraction(1, 2**62))
        assert rounded.denominator & (rounded.denominator - 1) == 0


def test_the_hermitian_centre_is_hermitian_and_keeps_exact_entries() -> None:
    """lem:enclosure-arithmetic (v)."""
    matrix = [
        [Ball(Fraction(1)), Ball(Fraction(1, 2), Fraction(1, 4), Fraction(1, 2**60))],
        [Ball(Fraction(1, 2), Fraction(-1, 4), Fraction(1, 2**61)), Ball(Fraction(3))],
    ]
    centre, radii = hermitian_centred(matrix)
    assert centre[0][1] == centre[1][0].conjugate()
    assert radii[0][1] == radii[1][0] == (Fraction(1, 2**60) + Fraction(1, 2**61)) / 2
    assert radii[0][0] == 0 and centre[0][0].re == 1


# ---------------------------------------------------------------------------
#  req:exact-route-decision (ii): the exact arithmetic
# ---------------------------------------------------------------------------


def test_a_coprime_base_has_pairwise_coprime_members() -> None:
    """The base the radicals are written over, by gcd refinement."""
    base = coprime_base([12, 18, 2, 45, 7])
    assert all(math.gcd(a, b) == 1 for a in base for b in base if a != b)
    for value in (12, 18, 2, 45, 7):
        rest = value
        for b in base:
            while rest % b == 0:
                rest //= b
        assert rest == 1


def test_square_roots_multiply_back_to_rationals() -> None:
    """The monomials are a basis: products of roots reduce, rationals are recognised."""
    field = RadicalField([Fraction(1, 3), Fraction(2, 3), Fraction(9, 10)])
    third = field.sqrt(Fraction(1, 3))
    two_thirds = field.sqrt(Fraction(2, 3))
    assert not third.is_gaussian_rational
    assert (third * third).as_cx().re == Fraction(1, 3)
    cross = third * two_thirds  # sqrt(2) / 3: not rational
    assert not cross.is_gaussian_rational
    assert (cross * cross).as_cx().re == Fraction(2, 9)
    eta = field.sqrt(Fraction(9, 10))
    assert (eta * eta).as_cx().re == Fraction(9, 10)
    assert field.sqrt(Fraction(1, 4)).is_gaussian_rational


def test_the_exact_angles_are_the_quarter_turns() -> None:
    """Cosine and sine of ``c pi`` with ``4c`` integral; non-zero radians are not."""
    field = RadicalField([])
    cos, sin = field.cos_sin(PiMultiple(Fraction(1, 4)))
    assert ((cos * cos) + (sin * sin)).as_cx().re == 1
    assert (cos - sin).is_gaussian_rational and not cos.is_gaussian_rational
    cos2, _ = field.cos_sin(PiMultiple(Fraction(1, 2)))
    assert cos2.is_gaussian_rational and not cos2.terms
    with pytest.raises(NotRepresented):
        field.cos_sin(PiMultiple(Fraction(1, 8)))
    with pytest.raises(NotRepresented):
        field.cos_sin(math.pi / 4)
    one, zero = field.cos_sin(0.0)
    assert one.as_cx().re == 1 and not zero.terms


def test_a_root_outside_the_field_is_not_represented() -> None:
    """The base is fixed at construction; a later radicand is refused, never misread."""
    field = RadicalField([Fraction(1, 3)])
    with pytest.raises(NotRepresented):
        field.sqrt(Fraction(1, 5))


# ---------------------------------------------------------------------------
#  The angle presentation, and exact domains
# ---------------------------------------------------------------------------


def test_the_pi_presentation_evaluates_as_the_radians_it_replaces() -> None:
    """Presentation (b): binary64 ``float(c) * pi``, numbers unchanged."""
    assert to_float(PiMultiple(Fraction(1, 8))) == float(Fraction(1, 8)) * math.pi
    for theta in (math.pi / 8, 0.3, 0.0):
        assert np.array_equal(
            Retarder.half_wave(theta, 0).matrix(), Retarder(math.pi, theta, 0).matrix()
        )
        assert np.array_equal(
            Retarder.quarter_wave(theta, 0).matrix(),
            Retarder(math.pi / 2, theta, 0).matrix(),
        )
    assert np.array_equal(
        Retarder.half_wave(PiMultiple(Fraction(1, 8)), 0).matrix(),
        Retarder.half_wave(float(Fraction(1, 8)) * math.pi, 0).matrix(),
    )


def test_a_pi_coefficient_is_compared_with_its_domain_exactly() -> None:
    """``parameters.domains``: refused, never clipped; the endpoint is excluded."""
    assert PhaseShifter((PiMultiple(Fraction(2)),)).check_domain(TOLERANCE) is not None
    assert (
        PhaseShifter((PiMultiple(Fraction(199, 100)),)).check_domain(TOLERANCE) is None
    )
    assert (
        Retarder(PiMultiple(Fraction(1)), PiMultiple(Fraction(1)), 0).check_domain(
            TOLERANCE
        )
        is not None
    )


def test_a_declared_rational_just_outside_its_domain_is_refused() -> None:
    """``parameters.domains`` decided on the declared number, not its binary64 image."""
    outside = Fraction(1) + Fraction(1, 2**60)
    assert to_float(outside) == 1.0
    assert Beamsplitter(outside, 0, 0, 0).check_domain(TOLERANCE) is not None
    assert Beamsplitter(Fraction(1), 0, 0, 0).check_domain(TOLERANCE) is None


def test_a_binary64_pi_coefficient_is_read_as_its_dyadic_rational() -> None:
    """Presentation (b): a binary64 coefficient denotes the dyadic rational it is."""
    assert PiMultiple(0.125).coefficient == Fraction(1, 8)  # type: ignore[arg-type]
    assert PiMultiple(0.1).coefficient == Fraction(0.1)  # type: ignore[arg-type]
    assert PiMultiple(3).coefficient == Fraction(3)  # type: ignore[arg-type]
    assert to_float(PiMultiple(0.125)) == to_float(PiMultiple(Fraction(1, 8)))  # type: ignore[arg-type]
    for bad in (math.inf, math.nan, True, "1/8"):
        with pytest.raises(MalformedInputError):
            PiMultiple(bad)  # type: ignore[arg-type]


def test_the_double_nearest_below_pi_is_inside_the_plate_domain() -> None:
    """``parameters.domains`` decided exactly for a radian angle.

    ``math.pi`` is a dyadic rational below pi, so it lies in ``[0, pi)``; the
    next double lies above pi and is refused. Declared rationals on either
    side of pi are decided the same way (``333/106 < pi < 22/7``).
    """
    assert Fraction(math.pi) < PI_60
    assert Retarder(PiMultiple(Fraction(1)), math.pi, 0).check_domain(TOLERANCE) is None
    above = math.nextafter(math.pi, math.inf)
    assert (
        Retarder(PiMultiple(Fraction(1)), above, 0).check_domain(TOLERANCE) is not None
    )
    assert Retarder(0, Fraction(333, 106), 0).check_domain(TOLERANCE) is None
    assert Retarder(0, Fraction(22, 7), 0).check_domain(TOLERANCE) is not None
    assert PhaseShifter((2 * math.pi,)).check_domain(TOLERANCE) is None
    assert PhaseShifter((Fraction(44, 7),)).check_domain(TOLERANCE) is not None


# ---------------------------------------------------------------------------
#  The trigonometric leaf at the default precision, against published values
# ---------------------------------------------------------------------------

#: cos 1 and sin 1 to 80 decimals (OEIS A049470 and A049469).
COS_1 = Fraction(
    "0.54030230586813971740093660744297660373231042061792222767009725538110039477447176"
)
SIN_1 = Fraction(
    "0.84147098480789650665250232163029899962256306079837106567275170999191040439123967"
)
#: cos 5.5 and sin 5.5 to 80 decimals.
COS_5_5 = Fraction(
    "0.70866977429126000002742118132584373498775839267675422048209124842213032042962931"
)
SIN_5_5 = Fraction(
    "-0.70554032557039190623191917552207007884729028198817673530600206285357435061537490"
)
DIGITS_80 = Fraction(1, 10**79)


@pytest.mark.parametrize("bits", [24, 64, 128, 200])
@pytest.mark.parametrize(
    ("angle", "cos_value", "sin_value"),
    [(Fraction(1), COS_1, SIN_1), (Fraction(11, 2), COS_5_5, SIN_5_5)],
)
def test_the_angle_leaf_is_sound_at_and_beyond_the_default_precision(
    bits: int, angle: Fraction, cos_value: Fraction, sin_value: Fraction
) -> None:
    """def:complex-enclosure: the enclosure contains the value, at every precision.

    At 128 bits (the default) and above the radius is far below the binary64
    error of ``math.cos``, so only a reference to many more digits can tell
    an undercounted error term; the published constants carry 80.
    """
    cos, sin = angle_enclosure(angle, bits)
    for ball, value in ((cos, cos_value), (sin, sin_value)):
        assert ball.im == 0
        assert abs(ball.re - value) <= ball.radius + DIGITS_80
        assert ball.radius <= Fraction(1, 2 ** (bits - 4))


@pytest.mark.parametrize("bits", [24, 64, 128, 200])
def test_the_angle_leaf_at_pi_over_8_contains_the_algebraic_value(bits: int) -> None:
    """def:complex-enclosure, decided exactly: ``4 cos(pi/8)^2 - 2 = sqrt 2``.

    ``x -> 4 x^2 - 2`` is increasing on the positive reals, so ``cos(pi/8)``
    lies in ``[c - r, c + r]`` exactly when ``sqrt 2`` lies between the images
    of the endpoints, which is decided in rational arithmetic.
    """
    cos, sin = angle_enclosure(PiMultiple(Fraction(1, 8)), bits)
    low, high = cos.re - cos.radius, cos.re + cos.radius
    assert low > 0
    below, above = 4 * low * low - 2, 4 * high * high - 2
    assert below < 0 or below * below <= 2
    assert above >= 0 and above * above >= 2
    # sin(pi/8) > 0 with 4 sin(pi/8)^2 = 2 - sqrt 2.
    low_s, high_s = sin.re - sin.radius, sin.re + sin.radius
    assert low_s > 0
    below_s, above_s = 2 - 4 * high_s * high_s, 2 - 4 * low_s * low_s
    assert below_s < 0 or below_s * below_s <= 2
    assert above_s >= 0 and above_s * above_s >= 2


# ---------------------------------------------------------------------------
#  The generic catalogue formulas against the binary64 catalogue
# ---------------------------------------------------------------------------

#: One declaration of every catalogue entry C1-C10, with angles in radians and
#: as coefficients of pi, losses and reflectivities off the trivial values.
EVERY_ENTRY: tuple[Component, ...] = (
    Beamsplitter(Fraction(1, 3), 0.7, Fraction(1, 10), Fraction(1, 5)),
    Beamsplitter(Fraction(1, 2), PiMultiple(Fraction(1, 4)), 0, 0),
    PolarizingBeamsplitter(
        Fraction(9, 10), Fraction(1, 20), 0.3, PiMultiple(Fraction(3, 2)), 0.1, 0.2
    ),
    Retarder(1.3, 0.4, 0.2),
    Retarder(PiMultiple(Fraction(3, 2)), PiMultiple(Fraction(1, 8)), 0),
    Retarder.quarter_wave(PiMultiple(Fraction(1, 4)), Fraction(1, 4)),
    Rotator(0.7),
    Rotator(PiMultiple(Fraction(3, 4))),
    Mirror(0.3, 0.8, 1.1, 2.0, True),
    Mirror(Fraction(1, 2), 1, PiMultiple(Fraction(1, 2)), 0, False),
    PhaseShifter((0.4, 5.0)),
    PhaseShifter((PiMultiple(Fraction(5, 4)), PiMultiple(Fraction(1, 3)))),
    Loss((0.2, 0.9)),
    Loss((Fraction(1, 4), Fraction(1, 2))),
    Polarizer(0.3, 0.9, 0.1),
    Polarizer(PiMultiple(Fraction(1, 4)), Fraction(1, 2), 0),
    ModeRouting((2, 0, 1)),
    GenericBlock.of(((0.6, 0.8j), (0.8, -0.6j))),
)


def _as_array(matrix: list[list[Ball]]) -> tuple[np.ndarray, np.ndarray]:
    centre = np.asarray(
        [[complex(float(b.re), float(b.im)) for b in row] for row in matrix]
    )
    radius = np.asarray([[float(b.radius) for b in row] for row in matrix])
    return centre, radius


@pytest.mark.parametrize("component", EVERY_ENTRY, ids=lambda c: type(c).__name__)
def test_the_generic_entry_encloses_the_catalogue_entry(component: Component) -> None:
    """def:catalogue-entries in the generic pipeline, req:exact-route-decision (iii).

    The enclosure of each local element (:class:`BallField`) and its binary64
    instance (:class:`FloatField`) agree with the catalogue's own NumPy
    element, entry by entry: a sign or a factor wrong in a generic formula
    would make the reference enclose a different model.
    """
    assert component.check_domain(TOLERANCE) is None
    expected = component.matrix()
    centre, radius = _as_array(element_matrix(BallField(), component))
    assert centre.shape == expected.shape
    assert np.all(np.abs(centre - expected) <= radius + MACHINE_AGREEMENT)
    floats = np.asarray(element_matrix(FloatField(), component), dtype=np.complex128)
    assert np.max(np.abs(floats - expected)) <= MACHINE_AGREEMENT


#: The entries of :data:`EVERY_ENTRY` with rational parameters and angles
#: ``c pi``, ``4c`` an integer: those the exact arithmetic represents.
EXACT_ENTRIES: tuple[Component, ...] = (
    Beamsplitter(Fraction(1, 2), PiMultiple(Fraction(1, 4)), 0, 0),
    Retarder(PiMultiple(Fraction(3, 2)), PiMultiple(Fraction(1, 8)), 0),
    Retarder.quarter_wave(PiMultiple(Fraction(1, 4)), Fraction(1, 4)),
    Rotator(PiMultiple(Fraction(3, 4))),
    Mirror(Fraction(1, 2), 1, PiMultiple(Fraction(1, 2)), 0, False),
    PhaseShifter((PiMultiple(Fraction(5, 4)), PiMultiple(Fraction(7, 4)))),
    Loss((Fraction(1, 4), Fraction(1, 2))),
    Polarizer(PiMultiple(Fraction(1, 4)), Fraction(1, 2), 0),
    ModeRouting((2, 0, 1)),
)


@pytest.mark.parametrize("component", EXACT_ENTRIES, ids=lambda c: type(c).__name__)
def test_the_exact_entry_is_the_catalogue_entry(component: Component) -> None:
    """req:exact-route-decision (ii): the element in exact arithmetic, enclosed back."""
    recorder = RecordingField()
    element_matrix(recorder, component)
    exact = element_matrix(RadicalField(recorder.radicands), component)
    balls = [[entry.to_ball()[0] for entry in row] for row in exact]
    centre, radius = _as_array(balls)
    assert np.all(np.abs(centre - component.matrix()) <= radius + MACHINE_AGREEMENT)
