"""The E1 lemmas one at a time: substrate, logarithm, Stirling, window, bracket.

The frozen oracles pin the two new ROUTES end to end; this file pins the
LEMMAS they are built from, each against something that does not come from the
lemma itself:

* the directed dyadic rounding against the exact rational it rounds;
* the root bounds of ``lem:log-enclosure`` against the artanh series, summed
  here in exact rational arithmetic -- a second derivation of the logarithm
  that shares no step with the first (no square root, no grid);
* Robbins' bounds of ``lem:stirling-enclosure`` (i) against EXACT factorials,
  which is the only check of a Stirling bound that is not circular;
* Wallis's product of its (ii) against a rational bracket of ``pi`` a reader
  can check;
* the window and majorant of ``lem:tail-majorant`` (ii)-(iii) against the
  exact tail summed from the exact law at small ``n``;
* the mirror of its (v) against the exact law of ``n - N``;
* the three verdicts of ``prop:bracketed-endpoints`` against the exact tails.

NO LIBRARY LOGARITHM IS CALLED ANYWHERE IN THIS FILE, which is the convention
``binomial-box/interface.yaml`` makes binding on the submodule
(``no_transcendental_dependency``) and is worth holding its tests to as well:
a test that checked a self-contained enclosure against ``math.log`` would be
checking it against the dependency the lemmas exist to avoid.
"""

from __future__ import annotations

import itertools
import math
from fractions import Fraction

import pytest

from certiqs_key.statistics.dyadic import round_dyadic, round_ratio
from certiqs_key.statistics.enclosure import (
    DEFAULT_ENCLOSURE_PARAMETERS,
    Verdict,
    bracketed_upper_endpoint,
    certify_upper,
    first_decreasing_index,
    log_pmf_bounds,
    mass_ratio,
    upper_tail_log_bounds,
)
from certiqs_key.statistics.logs import (
    LogBounds,
    exp_upper,
    grid_sqrt_down,
    grid_sqrt_up,
    isqrt_bounds,
    log_bounds,
    log_factorial_bounds,
    root_bounds,
    two_pi_bounds,
    wallis_partial_product,
)
from certiqs_key.statistics.tails import BOUNDED_TAIL_PRECISION, binomial_pmf

_ZERO = Fraction(0)
_ONE = Fraction(1)
J = DEFAULT_ENCLOSURE_PARAMETERS.root_exponent
S = DEFAULT_ENCLOSURE_PARAMETERS.root_precision
M = DEFAULT_ENCLOSURE_PARAMETERS.wallis_length


def artanh_log(value: Fraction, terms: int = 40) -> tuple[Fraction, Fraction]:
    """Return rationals bracketing ``ln value``, by a route sharing no step.

    ``ln x = 2 (u + u^3/3 + ...)`` with ``u = (x - 1)/(x + 1)``, split on the
    binary exponent so that the series is summed on ``[1, 2]`` where ``u`` is
    at most ``1/3``. Exact rational arithmetic; NO SQUARE ROOT, NO GRID AND NO
    LIBRARY LOGARITHM, so it shares no step with the enclosure it checks.

    The mantissa is rounded OUTWARD to 240 bits before the series is summed --
    ``ln`` is increasing, so the two bounds still bracket -- because the
    arguments include exact factorials of tens of thousands of bits, whose
    ``u^80`` would otherwise be an integer of millions of digits. The slack
    that introduces, about ``2^-240``, is thirty orders of magnitude under the
    widths this file asserts against.
    """
    if value <= _ZERO:
        raise ValueError("a logarithm needs a positive argument")

    def series(mantissa: Fraction) -> tuple[Fraction, Fraction]:
        if mantissa == _ONE:
            return _ZERO, _ZERO
        unit = (mantissa - _ONE) / (mantissa + _ONE)
        square = unit * unit
        partial, power = _ZERO, unit
        for index in range(terms):
            partial += power / (2 * index + 1)
            power *= square
        tail = power / ((2 * terms + 1) * (_ONE - square))
        return 2 * partial, 2 * (partial + tail)

    exponent = value.numerator.bit_length() - value.denominator.bit_length()
    while Fraction(2) ** exponent > value:
        exponent -= 1
    while Fraction(2) ** (exponent + 1) <= value:
        exponent += 1
    mantissa = value / Fraction(2) ** exponent
    low = series(round_dyadic(mantissa, 240, upward=False))[0]
    high = series(min(Fraction(2), round_dyadic(mantissa, 240, upward=True)))[1]
    two_low, two_high = series(Fraction(2))
    if exponent >= 0:
        return exponent * two_low + low, exponent * two_high + high
    return exponent * two_high + low, exponent * two_low + high


# ---------------------------------------------------------------------------
#  The substrate (rem:local-evaluation, "The substrate")
# ---------------------------------------------------------------------------


@pytest.mark.contract
@pytest.mark.parametrize(
    "value",
    [
        Fraction(1),
        Fraction(1, 3),
        Fraction(-7, 5),
        Fraction(2**64 + 1, 3),
        Fraction(1, 2**300),
    ],
)
def test_the_directed_rounding_brackets_its_argument(value: Fraction) -> None:
    """Rigorous at any precision, which is what makes it not a threshold."""
    for bits in (8, 32, 192):
        assert round_dyadic(value, bits, upward=False) <= value
        assert round_dyadic(value, bits, upward=True) >= value


@pytest.mark.contract
def test_the_directed_rounding_is_a_dyadic_and_bounded_in_size() -> None:
    """The denominator is a power of two and the mantissa fits the precision.

    This is the whole of the substrate rule: "an exact rational whose
    denominator is a power of the round count is NOT a number model for this
    route".
    """
    value = Fraction(3**200, 7**150)
    for bits in (16, 64, 128):
        for upward in (False, True):
            rounded = round_dyadic(value, bits, upward=upward)
            denominator = rounded.denominator
            assert denominator & (denominator - 1) == 0
            assert rounded.numerator.bit_length() <= bits + 1


@pytest.mark.contract
def test_round_ratio_agrees_with_round_dyadic_without_the_gcd() -> None:
    """The integer-pair form is the same value, which is why both may exist."""
    for numerator, denominator in ((7, 3), (2**70, 3**5), (-11, 4), (0, 9)):
        for bits in (8, 64):
            for upward in (False, True):
                assert round_ratio(numerator, denominator, bits, upward=upward) == (
                    round_dyadic(Fraction(numerator, denominator), bits, upward=upward)
                )


@pytest.mark.contract
def test_the_sweeps_shrink_is_the_shared_substrate_at_its_own_precision() -> None:
    """``tails._shrink`` delegates, and this is the identity the 55 cases pin."""
    from certiqs_key.statistics import tails

    for value in (Fraction(1, 3), Fraction(2**33, 5), Fraction(1, 2**40)):
        for upward in (False, True):
            assert tails._shrink(value, upward=upward) == round_dyadic(
                value, BOUNDED_TAIL_PRECISION, upward=upward
            )


# ---------------------------------------------------------------------------
#  lem:log-enclosure
# ---------------------------------------------------------------------------


@pytest.mark.contract
@pytest.mark.parametrize(
    "value",
    [
        Fraction(1),
        Fraction(3, 2),
        Fraction(2),
        Fraction(10),
        Fraction(1, 10),
        Fraction(10**9),
        Fraction(1, 10**9),
        Fraction(999, 1000),
    ],
)
def test_the_root_bounds_bracket_the_logarithm(value: Fraction) -> None:
    """Eq. ``eq:log-rational-bounds``, against the artanh series."""
    enclosure = log_bounds(value, J, S)
    low, high = artanh_log(value)
    assert enclosure.lower <= low
    assert high <= enclosure.upper
    assert enclosure.width >= _ZERO


@pytest.mark.contract
def test_the_enclosure_narrows_as_the_root_exponent_grows() -> None:
    """Eq. ``eq:log-root-slack``: the slack is ``(ln x)^2 / 2m`` times a factor.

    Not asserted as that formula -- ``lem:log-enclosure`` states the enclosure
    computable at any prescribed width, the caller choosing the precisions --
    but as the property a caller relies on: more root steps, a narrower
    enclosure.
    """
    widths = [log_bounds(Fraction(10), exponent, S).width for exponent in (4, 12, 32)]
    assert widths[0] > widths[1] > widths[2] > _ZERO


@pytest.mark.contract
def test_the_isqrt_bounds_are_eq_isqrt_bounds_verbatim() -> None:
    """Eq. ``eq:isqrt-bounds``, and the two ends differ by at most ``2^-s``."""
    for value in (Fraction(2), Fraction(7, 3), Fraction(1, 5)):
        for precision in (0, 8, 64):
            low, high = isqrt_bounds(value, precision)
            assert low * low <= value
            assert high * high > value
            assert high - low <= Fraction(1, 1 << precision)


@pytest.mark.contract
def test_the_grid_square_roots_are_monotone_in_their_mantissa() -> None:
    """What makes ``prop:rule-bernstein`` (ii) hold: a monotone rounding.

    The bare Eq. ``eq:isqrt-bounds`` is NOT monotone in its argument -- its
    excess depends on the denominator -- and the counterexample the arrival
    review found is asserted here, beside the grid form that repairs it.
    """
    for precision in (0, 4, 16):
        values = [grid_sqrt_up(mantissa, precision) for mantissa in range(1, 60)]
        assert all(x <= y for x, y in itertools.pairwise(values))
        floors = [grid_sqrt_down(mantissa, precision) for mantissa in range(1, 60)]
        assert all(x <= y for x, y in itertools.pairwise(floors))
    # THE COUNTEREXAMPLE, at s = 0 and j = 1 (so
    # m = 2): the bare Eq. eq:isqrt-bounds gives a SMALLER budget term for the
    # SMALLER budget, which is the inversion prop:rule-bernstein (ii) forbids.
    #   eps = 4/9 -> x = 9/4: isqrt(9*4)/4 = 6/4, so u = 7/4 and L = 2(u-1) = 3/2
    #   eps = 1/2 -> x = 2:   isqrt(2*1)/1 = 1,   so u = 2   and L = 2(u-1) = 2
    # The budget GREW from 4/9 to 1/2 and the term GREW from 3/2 to 2, so the
    # deviation and the emitted interval would grow with the budget.
    bare_four_ninths = 2 * (isqrt_bounds(Fraction(9, 4), 0)[1] - _ONE)
    bare_half = 2 * (isqrt_bounds(Fraction(2), 0)[1] - _ONE)
    assert bare_four_ninths == Fraction(3, 2)
    assert bare_half == Fraction(2)
    assert Fraction(4, 9) < Fraction(1, 2)
    assert bare_four_ninths < bare_half  # the inversion, on the bare bound
    # And the rule's own budget term, on the grid, does NOT invert: the larger
    # budget gives the smaller term.
    assert (
        log_bounds(_ONE / Fraction(1, 2), J, S).upper
        <= log_bounds(_ONE / Fraction(4, 9), J, S).upper
    )


@pytest.mark.contract
def test_the_root_iteration_refuses_an_argument_outside_its_range() -> None:
    """The normalized range is the caller's obligation, and it is checked."""
    with pytest.raises(ValueError, match="normalized range"):
        root_bounds(Fraction(10), J, S)
    with pytest.raises(ValueError, match="positive argument"):
        log_bounds(Fraction(0), J, S)


# ---------------------------------------------------------------------------
#  lem:stirling-enclosure
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_wallis_brackets_two_pi() -> None:
    """Eq. ``eq:wallis-bounds``: ``4 P_M < 2 pi < 4 P_M (1 + 1/(2M))``.

    Against a rational bracket of ``pi`` a reader can check -- Archimedes'
    ``223/71 < pi < 22/7`` is too coarse at this ``M``, so the bracket used is
    the standard continued-fraction convergents ``333/106 < pi < 355/113``,
    whose correctness is one long division each.
    """
    below, above = Fraction(333, 106), Fraction(355, 113)
    for length in (16, 256, M):
        partial = wallis_partial_product(length)
        assert 4 * partial < 2 * above
        assert 2 * below < 4 * partial * (1 + Fraction(1, 2 * length))
        # And the relative width is 1/(2M), which is the row's own sizing.
        assert Fraction(1, 2 * length) >= (
            4 * partial * (1 + Fraction(1, 2 * length)) - 4 * partial
        ) / (4 * partial)
    enclosure = two_pi_bounds(M, J, S)
    low, high = artanh_log(2 * below)
    assert enclosure.lower <= high
    low, high = artanh_log(2 * above)
    assert enclosure.upper >= low


@pytest.mark.contract
@pytest.mark.parametrize("value", [0, 1, 2, 7, 60, 255, 256, 257, 1000, 4096])
def test_robbins_brackets_the_exact_factorial(value: int) -> None:
    """``lem:stirling-enclosure`` (iii), against ``math.factorial`` exactly.

    The only non-circular check of a Stirling bound: the exact integer ``m!``
    is available here, its logarithm is bracketed by the artanh series, and the
    enclosure must contain that bracket. It crosses
    :data:`SMALL_FACTORIAL_MAX` in both directions, so both branches are
    exercised.
    """
    enclosure = log_factorial_bounds(value, J, S, M)
    if value <= 1:
        assert enclosure == LogBounds(_ZERO, _ZERO)
        return
    low, high = artanh_log(Fraction(math.factorial(value)))
    assert enclosure.lower <= low
    assert high <= enclosure.upper


@pytest.mark.contract
def test_the_robbins_branch_is_narrower_than_a_whole_nat() -> None:
    """The gap ``1/(12m(12m+1))`` is why small factorials take the other branch.

    At ``m = 1`` it is ``1/156``, a hundredth of a nat, which at a small ``n``
    is comparable to the per-count decay itself. The exact branch is what keeps
    the bracket decidable there, and this asserts the crossing is on the right
    side: the enclosure at 2 is far narrower than 1/156.
    """
    assert log_factorial_bounds(2, J, S, M).width < Fraction(1, 156)
    assert log_factorial_bounds(1000, J, S, M).width < Fraction(1, 100)


# ---------------------------------------------------------------------------
#  lem:pmf-enclosure and lem:tail-majorant
# ---------------------------------------------------------------------------


@pytest.mark.contract
@pytest.mark.parametrize("honest", [Fraction(1, 2), Fraction(1, 4), Fraction(9, 10)])
@pytest.mark.parametrize("rounds", [1, 5, 12])
def test_the_pmf_enclosure_brackets_the_exact_mass_point(
    rounds: int, honest: Fraction
) -> None:
    """Eq. ``eq:pmf-enclosure``, against the exact rational mass point."""
    for index in range(rounds + 1):
        enclosure = log_pmf_bounds(rounds, honest, index, DEFAULT_ENCLOSURE_PARAMETERS)
        low, high = artanh_log(binomial_pmf(rounds, honest, index))
        assert enclosure.lower <= low
        assert high <= enclosure.upper


@pytest.mark.contract
def test_the_ratios_are_eq_pmf_ratio_and_decrease_strictly() -> None:
    """``lem:tail-majorant`` (i), against the exact mass points."""
    rounds, honest = 14, Fraction(3, 7)
    ratios = [mass_ratio(rounds, honest, index) for index in range(rounds)]
    assert all(x > y for x, y in itertools.pairwise(ratios))
    for index, ratio in enumerate(ratios):
        assert ratio == binomial_pmf(rounds, honest, index + 1) / binomial_pmf(
            rounds, honest, index
        )
    assert mass_ratio(rounds, honest, rounds) == _ZERO


@pytest.mark.contract
def test_the_first_decreasing_index_is_the_least_one_with_ratio_below_one() -> None:
    """The short cut's hinge, checked against the ratios themselves."""
    laws = ((10, Fraction(1, 2)), (37, Fraction(2, 7)), (5, Fraction(1, 9)))
    for rounds, honest in laws:
        start = first_decreasing_index(rounds, honest)
        assert mass_ratio(rounds, honest, start) < _ONE
        if start > 0:
            assert mass_ratio(rounds, honest, start - 1) >= _ONE


@pytest.mark.contract
@pytest.mark.parametrize("honest", [Fraction(1, 2), Fraction(1, 5), Fraction(7, 8)])
@pytest.mark.parametrize("rounds", [1, 4, 11])
def test_the_window_and_majorant_bracket_the_exact_tail(
    rounds: int, honest: Fraction
) -> None:
    """Eq. ``eq:tail-log``, against the exact tail summed from the exact law.

    On every index of every one of these laws, which is the whole point of a
    unit test of the lemma: the frozen oracles pin three points, this pins the
    lemma on a few hundred.
    """
    for index in range(-1, rounds + 1):
        enclosure = upper_tail_log_bounds(
            rounds, honest, index, DEFAULT_ENCLOSURE_PARAMETERS
        )
        exact = sum(
            (binomial_pmf(rounds, honest, j) for j in range(index + 1, rounds + 1)),
            _ZERO,
        )
        if enclosure is None:
            assert exact == _ZERO
            continue
        low, high = artanh_log(exact)
        assert enclosure.lower <= low
        assert high <= enclosure.upper


@pytest.mark.contract
def test_the_mirror_reduces_the_lower_tail_to_an_upper_one() -> None:
    """``lem:tail-majorant`` (v), against the two exact laws."""
    rounds, honest = 9, Fraction(2, 5)
    for index in range(rounds + 2):
        lower = sum(
            (binomial_pmf(rounds, honest, j) for j in range(index)), _ZERO
        )
        mirrored = sum(
            (
                binomial_pmf(rounds, _ONE - honest, j)
                for j in range(rounds - index + 1, rounds + 1)
            ),
            _ZERO,
        )
        assert lower == mirrored


# ---------------------------------------------------------------------------
#  prop:bracketed-endpoints
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_the_three_verdicts_agree_with_the_exact_tails() -> None:
    """A certificate never lies, in either direction.

    ``CERTIFIED_ADMISSIBLE`` implies the exact tail really is within the
    budget, ``CERTIFIED_INADMISSIBLE`` implies it really is not, and
    ``UNDECIDED`` implies nothing -- which is why the search counts it as not
    certified.
    """
    rounds, honest = 12, Fraction(1, 3)
    for budget in (Fraction(1, 2), Fraction(1, 20), Fraction(1, 1000)):
        for index in range(rounds + 1):
            exact = sum(
                (binomial_pmf(rounds, honest, j) for j in range(index + 1, rounds + 1)),
                _ZERO,
            )
            verdict = certify_upper(
                rounds, honest, index, budget, DEFAULT_ENCLOSURE_PARAMETERS
            )
            if verdict is Verdict.CERTIFIED_ADMISSIBLE:
                assert exact <= budget, (budget, index)
            elif verdict is Verdict.CERTIFIED_INADMISSIBLE:
                assert exact > budget, (budget, index)


@pytest.mark.contract
def test_the_predicate_holds_at_n_unconditionally_so_the_search_is_total() -> None:
    """``Pr[N > n] = 0`` is exact on every route, which is what makes ``hi = n``.

    The sentence before the definition of a bracketed endpoint in
    ``prop:bracketed-endpoints``, and the reason the enclosure route adds no
    reason code to the core's ten.
    """
    laws = ((1, Fraction(1, 2)), (50, Fraction(1, 7)), (3, Fraction(9, 10)))
    for rounds, honest in laws:
        for budget in (Fraction(1, 10**6), Fraction(1, 3)):
            assert (
                certify_upper(
                    rounds, honest, rounds, budget, DEFAULT_ENCLOSURE_PARAMETERS
                )
                is Verdict.CERTIFIED_ADMISSIBLE
            )
            assert bracketed_upper_endpoint(rounds, honest, budget).index <= rounds


@pytest.mark.contract
def test_exp_upper_is_an_upper_bound_and_never_a_lower_one() -> None:
    """The inverse the completeness report needs, checked against the series."""
    for value in (Fraction(0), Fraction(1, 3), Fraction(-5), Fraction(-13835, 1000)):
        bound = exp_upper(value, J, S)
        # ln(bound) >= value is the defining property, checked by a route that
        # shares no step with the one that produced it.
        assert artanh_log(bound)[1] >= value
