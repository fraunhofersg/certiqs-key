"""The rule registry is well formed, admissible, and internally consistent.

The same four things ``test_statistics_acceptance_registry.py`` pins for the
original freeze, for the frozen cases added later:

1. **Admissibility.** No expected value comes from MATLAB, OpenQKDSecurity,
   CVX, MOSEK or Julia; the guard reuses ``registry.INADMISSIBLE_SOURCES``,
   imported rather than restated.
2. **Well-formedness.** Unique ids, a kind from ``registry.KINDS``, and a
   derivation long enough to redo on paper.
3. **Traceability.** Every claim label an entry names has a claim file under
   ``spec/modules/statistics/``.
4. **Internal consistency of the frozen tables.** Relations that hold AMONG
   THE FROZEN NUMBERS -- a binomial row that sums to its denominator, a
   quantile that is the extremal admissible index of its own table, a
   deviation that is the positive root of its own quadratic, a bracket of
   ``ln(1/eps)`` that actually contains it. These catch a transcription typo.
   THE DERIVATION IN THE CASE, NOT THE TABLE, STAYS AUTHORITATIVE.

**Nothing here runs the module.** No assertion below calls
``certiqs_key.statistics``: that is
``tests/golden/test_statistics_rules_against_registry.py``'s job, and keeping
the two apart is what makes the frozen values evidence rather than a
restatement of the code. The one arithmetic this file does is exact rational
arithmetic on the frozen integers, and the one inequality it checks against an
irrational is ``ln(1/eps)``, bracketed by the artanh series the registry's own
docstring derives -- evaluated here as a truncated exact rational sum with a
bound on the omitted tail, not by :func:`math.log`.
"""

from __future__ import annotations

import math
from fractions import Fraction
from pathlib import Path

import pytest
from registry import INADMISSIBLE_SOURCES, KINDS
from registry_statistics_rules import (
    BERNSTEIN_CASES,
    ENCLOSURE_CASES,
    RULE_ORACLES,
    BernsteinCase,
    EnclosureCase,
    rule_oracle,
)

MODULE = Path(__file__).resolve().parents[2] / "spec" / "modules" / "statistics"
_ZERO = Fraction(0)
_ONE = Fraction(1)


def _claim_file(label: str) -> Path:
    parts = label.split("/")
    stem = parts[-1].replace(":", "-")
    return MODULE.joinpath(*parts[:-1]) / "claims" / f"{stem}.tex"


def _artanh_bracket(value: Fraction, terms: int = 24) -> tuple[Fraction, Fraction]:
    """Return rationals bracketing ``ln value`` for ``1 <= value <= 2``.

    ``ln x = 2 (u + u^3/3 + u^5/5 + ...)`` with ``u = (x - 1) / (x + 1)``. The
    partial sum is a LOWER bound (every term is positive for ``x > 1``) and the
    omitted tail is bounded by the geometric series
    ``u^(2T+1) / ((2T+1) (1 - u^2))``. On ``[1, 2]`` the ratio ``u`` is at most
    ``1/3``, so twenty-four terms leave a tail under ``3^-49``.
    """
    if not _ONE <= value <= 2:
        raise ValueError(f"the series is summed on [1, 2]; got {value}")
    if value == _ONE:
        return _ZERO, _ZERO
    unit = (value - _ONE) / (value + _ONE)
    partial = _ZERO
    power = unit
    square = unit * unit
    for index in range(terms):
        partial += power / (2 * index + 1)
        power *= square
    tail = power / ((2 * terms + 1) * (_ONE - square))
    return 2 * partial, 2 * (partial + tail)


def _reference_log(value: Fraction) -> tuple[Fraction, Fraction]:
    """Return rationals bracketing ``ln value``, by the binary decomposition.

    ``x = 2^e m`` with ``m`` in ``[1, 2)``, so ``ln x = e ln 2 + ln m`` and both
    pieces come from :func:`_artanh_bracket`, whose series converges fastest
    exactly there. THE SAME DECOMPOSITION THE REGISTRY'S OWN DERIVATION USES
    (``3 ln 10 = 10 ln 2 - ln 1.024``) and the same one
    ``certiqs_key.statistics.logs`` uses, ARRIVED AT INDEPENDENTLY AND CHECKED
    HERE AGAINST THE FROZEN BRACKETS rather than against that module: nothing
    in this file imports it. No library logarithm is called.
    """
    if value <= _ZERO:
        raise ValueError(f"a logarithm needs a positive argument; got {value}")
    exponent = value.numerator.bit_length() - value.denominator.bit_length()
    while Fraction(2) ** exponent > value:
        exponent -= 1
    while Fraction(2) ** (exponent + 1) <= value:
        exponent += 1
    mantissa_low, mantissa_high = _artanh_bracket(value / Fraction(2) ** exponent)
    two_low, two_high = _artanh_bracket(Fraction(2))
    if exponent >= 0:
        return exponent * two_low + mantissa_low, exponent * two_high + mantissa_high
    return exponent * two_high + mantissa_low, exponent * two_low + mantissa_high


# ---------------------------------------------------------------------------
#  1. Admissibility, well-formedness, traceability
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_no_entry_derives_from_an_inadmissible_source() -> None:
    for entry in RULE_ORACLES:
        blob = f"{entry.subject} {entry.derivation}".lower()
        for source in INADMISSIBLE_SOURCES:
            assert source.lower() not in blob, (entry.oracle_id, source)


@pytest.mark.contract
def test_every_oracle_entry_is_well_formed() -> None:
    seen: set[str] = set()
    for entry in RULE_ORACLES:
        assert entry.oracle_id not in seen, entry.oracle_id
        seen.add(entry.oracle_id)
        assert entry.kind in KINDS, (entry.oracle_id, entry.kind)
        assert entry.claims, entry.oracle_id
        assert len(entry.derivation) > 200, entry.oracle_id
        assert entry.assurance == "estimate", entry.oracle_id


@pytest.mark.contract
def test_every_claim_an_entry_names_has_a_claim_file() -> None:
    for entry in RULE_ORACLES:
        for label in entry.claims:
            assert _claim_file(label).is_file(), (entry.oracle_id, label)


@pytest.mark.contract
def test_unknown_oracle_id_raises() -> None:
    with pytest.raises(KeyError):
        rule_oracle("O-NOT-AN-ENTRY")


@pytest.mark.contract
def test_every_case_carries_its_arithmetic() -> None:
    """A derivation a reader can redo, on every case and not only every entry."""
    for case in BERNSTEIN_CASES:
        assert len(case.derivation) > 300, case.case_id
    for case in ENCLOSURE_CASES:
        assert len(case.derivation) > 300, case.case_id
    ids = [case.case_id for case in (*BERNSTEIN_CASES, *ENCLOSURE_CASES)]
    assert len(set(ids)) == len(ids)


# ---------------------------------------------------------------------------
#  2. The Bernstein cases are consistent with their own brackets
# ---------------------------------------------------------------------------


@pytest.mark.contract
@pytest.mark.parametrize("case", BERNSTEIN_CASES, ids=lambda c: c.case_id)
def test_the_frozen_variance_and_bracket_are_what_they_claim(
    case: BernsteinCase,
) -> None:
    """``v = n p (1 - p)``, and the bracket really contains ``ln(1/eps)``."""
    assert case.variance == case.rounds * case.honest * (_ONE - case.honest)
    if case.eps_upper == _ZERO or case.honest in (_ZERO, _ONE):
        # The two convention cases take no logarithm at all; their brackets are
        # carried for uniformity and the case's own derivation says so.
        return
    lower, upper = _reference_log(_ONE / case.eps_upper)
    assert case.budget_low <= lower, case.case_id
    assert upper <= case.budget_high, case.case_id


@pytest.mark.contract
@pytest.mark.parametrize("case", BERNSTEIN_CASES, ids=lambda c: c.case_id)
def test_the_frozen_deviations_are_the_positive_root_of_their_quadratic(
    case: BernsteinCase,
) -> None:
    """``t(L)`` is the positive root of ``t^2 - (2L/3) t - 2 v L = 0``.

    Checked at both ends of the bracket, in exact rational arithmetic, by
    substituting the frozen ``t`` into the quadratic: the frozen values are
    rounded to four decimal places, so what is asserted is that the quadratic
    changes sign across each of them by less than the rounding can hide.
    """
    if case.eps_upper == _ZERO or case.honest in (_ZERO, _ONE):
        return
    for term, deviation in (
        (case.budget_low, case.deviation_low),
        (case.budget_high, case.deviation_high),
    ):
        slack = Fraction(1, 1000)
        for offset, sign in ((-slack, -1), (slack, 1)):
            probe = deviation + offset
            value = probe * probe - (2 * term / 3) * probe - 2 * case.variance * term
            assert value * sign > 0, (case.case_id, term, offset)


@pytest.mark.contract
@pytest.mark.parametrize("case", BERNSTEIN_CASES, ids=lambda c: c.case_id)
def test_the_frozen_endpoints_are_the_floor_and_ceiling_over_the_whole_bracket(
    case: BernsteinCase,
) -> None:
    """Eq. ``eq:bernstein-endpoints`` at BOTH ends gives the frozen integers.

    This is what makes the case a fact about the rule rather than about one
    evaluation: if the floor and the ceiling agree at both ends of the bracket
    and the map ``L -> t(L)`` is increasing, they agree everywhere in it.
    """
    if case.eps_upper == _ZERO or case.honest in (_ZERO, _ONE):
        return
    mean = case.rounds * case.honest
    for deviation in (case.deviation_low, case.deviation_high):
        assert max(0, math.floor(mean - deviation)) == case.endpoint_lower
        assert min(case.rounds, math.ceil(mean + deviation)) == case.endpoint_upper
    assert case.deviation_low <= case.deviation_high


@pytest.mark.contract
def test_the_two_convention_cases_are_the_definition_and_not_an_evaluation() -> None:
    """``def:endpoint-rule`` (b) and (c), frozen as cases of their own."""
    degenerate = next(
        case for case in BERNSTEIN_CASES if case.case_id == "BERN-degenerate-mass-zero"
    )
    assert degenerate.honest == _ZERO
    assert (degenerate.endpoint_lower, degenerate.endpoint_upper) == (0, 0)
    zero_budget = next(
        case for case in BERNSTEIN_CASES if case.case_id == "BERN-zero-budget"
    )
    assert zero_budget.eps_lower == zero_budget.eps_upper == _ZERO
    assert zero_budget.endpoint_lower == 0
    assert zero_budget.endpoint_upper == zero_budget.rounds


# ---------------------------------------------------------------------------
#  3. The enclosure cases are consistent with their own binomial tables
# ---------------------------------------------------------------------------


@pytest.mark.contract
@pytest.mark.parametrize("case", ENCLOSURE_CASES, ids=lambda c: c.case_id)
def test_the_frozen_binomial_row_is_the_law(case: EnclosureCase) -> None:
    """The row sums to its denominator and IS ``C(n,k) a^k (b-a)^(n-k)``."""
    assert len(case.mass) == case.rounds + 1
    assert sum(case.mass) == case.denominator
    numerator = case.honest.numerator
    complement = case.honest.denominator - numerator
    assert case.denominator == case.honest.denominator**case.rounds
    for index, value in enumerate(case.mass):
        expected = (
            math.comb(case.rounds, index)
            * numerator**index
            * complement ** (case.rounds - index)
        )
        assert value == expected, (case.case_id, index)


@pytest.mark.contract
@pytest.mark.parametrize("case", ENCLOSURE_CASES, ids=lambda c: c.case_id)
def test_the_frozen_quantiles_are_extremal_in_their_own_table(
    case: EnclosureCase,
) -> None:
    """``kappa^-`` is the largest and ``kappa^+`` the smallest admissible index.

    Read off the frozen integers alone: no binomial law is evaluated and no
    tail is summed by anything but the row above.
    """
    scale = case.denominator

    def upper_tail(index: int) -> Fraction:
        return Fraction(sum(case.mass[index + 1 :]), scale)

    def lower_tail(index: int) -> Fraction:
        return Fraction(sum(case.mass[:index]), scale)

    assert upper_tail(case.kappa_upper) <= case.eps_upper
    if case.kappa_upper > 0:
        assert upper_tail(case.kappa_upper - 1) > case.eps_upper
    assert lower_tail(case.kappa_lower) <= case.eps_lower
    if case.kappa_lower < case.rounds:
        assert lower_tail(case.kappa_lower + 1) > case.eps_lower


@pytest.mark.contract
@pytest.mark.parametrize("case", ENCLOSURE_CASES, ids=lambda c: c.case_id)
def test_the_bracketed_endpoints_relax_the_exact_ones_and_meet_the_budget(
    case: EnclosureCase,
) -> None:
    """``prop:bracketed-endpoints`` (i) and (ii), checked on the frozen table.

    (i) The bracketed endpoints are ADMISSIBLE and the interval they define
    contains the exact quantile interval. (ii) Where the bracket is decided
    they EQUAL the exact quantiles, and where it is not the case must say so.
    """
    scale = case.denominator
    assert case.bracketed_upper >= case.kappa_upper
    assert case.bracketed_lower <= case.kappa_lower
    assert Fraction(sum(case.mass[case.bracketed_upper + 1 :]), scale) <= case.eps_upper
    assert Fraction(sum(case.mass[: case.bracketed_lower]), scale) <= case.eps_lower
    assert (case.bracketed_upper == case.kappa_upper) is case.upper_decided
    assert (case.bracketed_lower == case.kappa_lower) is case.lower_decided


@pytest.mark.contract
def test_the_undecided_case_sets_its_budget_exactly_on_a_tail() -> None:
    """Why that case CANNOT be decided, asserted rather than asserted in prose.

    The budget equals a tail value exactly, so no enclosure of positive width
    separates them: the upper bound strictly exceeds ``ln eps`` and the lower
    bound is at most it, which is the definition of an undecided index.
    """
    case = next(
        item
        for item in ENCLOSURE_CASES
        if item.case_id == "ENCL-n10-budget-on-a-tail-undecided"
    )
    exact_tail = Fraction(sum(case.mass[case.kappa_upper + 1 :]), case.denominator)
    assert exact_tail == case.eps_upper
    mirrored = Fraction(sum(case.mass[: case.kappa_lower]), case.denominator)
    assert mirrored == case.eps_lower
    assert case.upper_decided is False
    assert case.lower_decided is False
    # AND THE COST IS EXACTLY ONE COUNT ON EACH SIDE.
    assert case.bracketed_upper - case.kappa_upper == 1
    assert case.kappa_lower - case.bracketed_lower == 1


@pytest.mark.contract
@pytest.mark.parametrize("case", ENCLOSURE_CASES, ids=lambda c: c.case_id)
def test_the_guard_is_the_two_clamps_on_the_frozen_endpoints(
    case: EnclosureCase,
) -> None:
    """Eq. ``eq:guard`` applied to the bracketed endpoints, on the frozen table."""
    mean = case.rounds * case.honest
    assert case.guarded_lower == min(case.bracketed_lower, math.floor(mean))
    assert case.guarded_upper == max(case.bracketed_upper, math.ceil(mean))
    assert 0 <= case.guarded_lower <= math.floor(mean)
    assert math.ceil(mean) <= case.guarded_upper <= case.rounds
