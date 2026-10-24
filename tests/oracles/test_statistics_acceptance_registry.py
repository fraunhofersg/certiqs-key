"""The ``statistics-acceptance`` registry is well formed and bound to 0.1.2.

Four things this pins, and one thing it deliberately does not.

1. **Traceability.** ESTABLISHED ELSEWHERE AND NOT HERE. Every claim id,
   reason code, convention and ledger row of the registry was once bound
   to a single interface transcription; that file has no successor at the
   same shape -- the claims are claim files under ``spec/modules/statistics/``
   and the interface is two files -- so all nine of those tests are in
   ``tests/oracles/test_statistics_acceptance_registry_interface.py``, where
   they read the documents this repository has. The banner below names them one
   by one. WHAT STAYS IN THIS FILE is the binding of the frozen values to their
   own arithmetic.
2. **Admissibility (ADR-0003).** No expected value here comes from MATLAB,
   OpenQKDSecurity, CVX, MOSEK or Julia. The guard reuses
   ``registry.INADMISSIBLE_SOURCES`` so the two registries cannot drift on what
   an admissible oracle is.
3. **Well-formedness.** Unique ids, a kind from ``registry.KINDS``, and a
   derivation long enough to redo on paper.
4. **Internal consistency of the frozen tables.** Relations that hold *among the
   frozen numbers* -- a pmf that sums to one, a cdf that is its running sum, a
   guard cost that matches its endpoints, a dual witness that pairs to its own
   primal value. These catch a transcription typo. THE DERIVATION IN THE ENTRY,
   NOT THE TABLE, STAYS AUTHORITATIVE.

**What is deliberately absent: any reconstruction of the module.** Nothing here
builds an acceptance set, searches for ``kappa``, runs the greedy fill of
Eq. ``eq:greedy``, or evaluates a binomial law. That is the discipline
``registry.py`` states for C11 and C12 -- an oracle that *is* the implementation
checks the solver against itself -- and it binds harder in run A of a two-run
band, where no implementation exists yet and the whole point of the freeze is
that run B cannot tune the numbers to its code. Every assertion below either
substitutes a frozen value into a contract equation, or relates two frozen
fields of the same case.
"""

from __future__ import annotations

import math
from fractions import Fraction

import pytest
from registry_statistics_acceptance import (
    BINOMIAL_TAIL_CASES,
    BOX_MINIMUM_CASES,
    CONSTRUCTION_CASES,
    GEOMETRY_VALIDATION_CASES,
    GUARD_CASES,
    INADMISSIBLE_SOURCES,
    INPUT_DOMAIN_VIOLATION_CASES,
    KINDS,
    REASON_CODES,
    SA_ORACLES,
    SINGLETON_CASES,
    sa_oracle,
)

#: The contract version the freeze bound, and the nine section names its
#: entries pin. Kept here because the entries name them and a reader of this
#: file needs to know what an ``SA3`` in a ``claims`` tuple is; the mapping
#: onto this repository's claim labels is the companion interface file's.
CONTRACT_VERSION = "0.1.2"
CLAIM_IDS = ("SA1", "SA2", "SA3", "SA4", "SA5", "SA6", "SA7", "SA8", "SA9")


# ---------------------------------------------------------------------------
#  1. Traceability -- IN A FILE OF ITS OWN, NOT HERE
#
#  THE NINE TESTS WOULD READ A SINGLE INTERFACE TRANSCRIPTION, WHICH
#  DOES NOT EXIST IN THIS REPOSITORY: the claims are claim files under
#  `spec/modules/statistics/` and the interface is two files (the core and
#  `binomial-box`). A test that reads a missing file is not evidence of
#  anything, so all nine are, under their own names, in
#  `tests/oracles/test_statistics_acceptance_registry_interface.py`, where they
#  are asserted against the documents this repository has. The reductions
#  and receiver registries do the same.
#
#  The nine, by name:
#    test_interface_yaml_exists_and_names_the_accepted_contract
#    test_every_oracle_claim_id_exists_in_the_interface
#    test_the_registry_covers_every_claim_of_the_contract
#    test_every_claim_is_newly_derived_and_cites_nothing
#    test_the_interface_carries_the_five_assumption_ledger_rows (now
#      test_the_interface_carries_the_own_and_inherited_ledger_rows)
#    test_the_interface_conventions_match_what_the_registry_assumes
#    test_alpha_is_not_a_parameter_of_this_module
#    test_the_nine_reason_codes_are_the_interface_ones
#    test_the_acceptance_support_row_carries_both_branches
#
#  NOTHING ELSE IN THIS FILE MOVED OR CHANGED: what stays is the registry's
#  own arithmetic, which needs no document to check.
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
#  2. Admissibility and well-formedness
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_no_entry_derives_from_an_inadmissible_source() -> None:
    for entry in SA_ORACLES:
        text = f"{entry.subject}\n{entry.derivation}"
        for source in INADMISSIBLE_SOURCES:
            assert source.lower() not in text.lower(), (entry.oracle_id, source)


@pytest.mark.contract
def test_every_oracle_entry_is_well_formed() -> None:
    identifiers = [entry.oracle_id for entry in SA_ORACLES]
    assert len(identifiers) == len(set(identifiers))
    for entry in SA_ORACLES:
        assert entry.oracle_id.startswith("O-SA-"), entry.oracle_id
        assert entry.kind in KINDS, entry.oracle_id
        assert len(entry.derivation.strip()) > 200, entry.oracle_id
        assert entry.subject.strip(), entry.oracle_id
        # Every entry is estimate-tier: this module declares no assurance label.
        assert entry.assurance == "estimate", entry.oracle_id
        assert sa_oracle(entry.oracle_id) is entry


@pytest.mark.contract
def test_every_case_carries_its_arithmetic() -> None:
    groups = (
        BINOMIAL_TAIL_CASES,
        GEOMETRY_VALIDATION_CASES,
        GUARD_CASES,
        CONSTRUCTION_CASES,
        BOX_MINIMUM_CASES,
        SINGLETON_CASES,
        INPUT_DOMAIN_VIOLATION_CASES,
    )
    for group in groups:
        identifiers = [case.case_id for case in group]
        assert len(identifiers) == len(set(identifiers))
        for case in group:
            assert len(case.arithmetic.strip()) > 120, case.case_id


@pytest.mark.contract
def test_unknown_oracle_id_raises() -> None:
    with pytest.raises(KeyError):
        sa_oracle("O-SA-NO-SUCH-ENTRY")


# ---------------------------------------------------------------------------
#  3. SA2 -- the frozen tail tables are internally consistent
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_binomial_tables_are_internally_consistent() -> None:
    """The pmf sums to one, the cdf is its running sum, the tails complement it.

    No binomial law is evaluated here: every number compared is frozen, and the
    relations are the ones Lemma lem:exact-strict-tails states between them.
    """
    for case in BINOMIAL_TAIL_CASES:
        n, den = case.n, case.denominator
        assert len(case.pmf_numerators) == n + 1, case.case_id
        assert len(case.cdf_numerators) == n + 1, case.case_id
        assert len(case.lower_tail_numerators) == n + 2, case.case_id
        assert len(case.upper_tail_numerators) == n + 1, case.case_id
        assert sum(case.pmf_numerators) == den, case.case_id
        running = 0
        for k, mass in enumerate(case.pmf_numerators):
            running += mass
            assert case.cdf_numerators[k] == running, (case.case_id, k)
        # Pr[N < k] = Pr[N <= k-1], with Pr[N < 0] = 0.
        assert case.lower_tail_numerators[0] == 0, case.case_id
        for k in range(1, n + 2):
            assert case.lower_tail_numerators[k] == case.cdf_numerators[k - 1], (
                case.case_id,
                k,
            )
        # Pr[N > k] = 1 - Pr[N <= k], with Pr[N > n] = 0.
        for k in range(n + 1):
            assert case.upper_tail_numerators[k] == den - case.cdf_numerators[k], (
                case.case_id,
                k,
            )
        assert case.upper_tail_numerators[n] == 0, case.case_id
        # Monotone in k, which is all the proof of Theorem thm:sa3 (iii) uses.
        assert list(case.lower_tail_numerators) == sorted(case.lower_tail_numerators), (
            case.case_id
        )
        assert list(case.upper_tail_numerators) == sorted(
            case.upper_tail_numerators, reverse=True
        ), case.case_id


# ---------------------------------------------------------------------------
#  4. SA1 -- the validation predicates and the rational witness
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_geometry_validation_cases_are_consistent() -> None:
    for case in GEOMETRY_VALIDATION_CASES:
        assert case.tag in {"singleton", "polytope"}, case.case_id
        if case.tag == "singleton":
            assert case.q_star is not None
            in_simplex = all(v >= 0 for v in case.q_star) and sum(case.q_star) == 1
            assert case.predicate_holds is in_simplex, case.case_id
            continue
        assert case.box_bounds is not None
        lower, upper = case.box_bounds
        assert case.box_sums == (sum(lower), sum(upper)), case.case_id
        well_formed = all(0 <= lo <= hi for lo, hi in zip(lower, upper, strict=True))
        assert case.well_formed is well_formed, case.case_id
        if well_formed:
            # Eq. eq:boxfeas, valid ONLY under well-formedness.
            brackets = case.box_sums[0] <= 1 <= case.box_sums[1]
            assert case.predicate_holds is brackets, case.case_id
        else:
            # ILLFORMED-box-inverted: the closed form would PASS. That is the
            # trap the case exists to expose, so assert it explicitly.
            assert case.box_sums[0] <= 1 <= case.box_sums[1], case.case_id
            assert case.predicate_holds is False, case.case_id


@pytest.mark.contract
def test_the_interpolation_witness_is_rational_and_lands_in_the_set() -> None:
    """Theorem thm:geometry-validation (iii), the (<=) direction, checked by substitution."""  # noqa: E501
    checked = 0
    for case in GEOMETRY_VALIDATION_CASES:
        if case.theta_star is None or case.box_bounds is None:
            continue
        lower, upper = case.box_bounds
        theta = case.theta_star
        assert isinstance(theta, Fraction), case.case_id
        assert 0 <= theta <= 1, case.case_id
        point = tuple(
            lo + theta * (hi - lo) for lo, hi in zip(lower, upper, strict=True)
        )
        assert point == case.witness_point, case.case_id
        assert sum(point) == 1, case.case_id
        for lo, value, hi in zip(lower, point, upper, strict=True):
            assert lo <= value <= hi, case.case_id
        checked += 1
    assert checked == 2


# ---------------------------------------------------------------------------
#  5. SA3 -- the guard cost matches its own endpoints
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_guard_cases_satisfy_the_ordering_chain_and_the_cost_identities() -> None:
    for case in GUARD_CASES:
        n, p = case.n, case.p
        # Eq. eq:ordering.
        assert 0 <= case.k_lower <= case.floor_np, case.case_id
        assert case.floor_np <= case.ceil_np <= case.k_upper <= n, case.case_id
        # floor / ceil of n p, checked against the frozen p. Exact on Fraction.
        assert case.floor_np == math.floor(n * p), case.case_id
        assert case.ceil_np == math.ceil(n * p), case.case_id
        # Eq. eq:guard: k^- = min{kappa^-, floor}, k^+ = max{kappa^+, ceil}.
        assert case.k_lower == min(case.kappa_lower, case.floor_np), case.case_id
        assert case.k_upper == max(case.kappa_upper, case.ceil_np), case.case_id
        # Eq. eq:guard-cost.
        assert case.lower_enlargement == max(0, case.kappa_lower - case.floor_np), (
            case.case_id
        )
        assert case.upper_enlargement == max(0, case.ceil_np - case.kappa_upper), (
            case.case_id
        )
        # The four iff conditions, as verdicts about the SAME two numbers.
        assert case.guard_lo0_holds is (case.lower_enlargement == 0), case.case_id
        assert case.guard_lo1_holds is (case.lower_enlargement <= 1), case.case_id
        assert case.guard_up0_holds is (case.upper_enlargement == 0), case.case_id
        assert case.guard_up1_holds is (case.upper_enlargement <= 1), case.case_id
        # Eq. eq:guard-from-p, and the 1/n clause ON THE ACTIVE SIDE ONLY.
        assert case.distance_below_p == p - Fraction(case.k_lower, n), case.case_id
        assert case.distance_above_p == Fraction(case.k_upper, n) - p, case.case_id
        assert case.distance_below_p >= 0, case.case_id
        assert case.distance_above_p >= 0, case.case_id
        if case.lower_enlargement > 0:
            assert case.distance_below_p <= Fraction(1, n), case.case_id
        if case.upper_enlargement > 0:
            assert case.distance_above_p <= Fraction(1, n), case.case_id


@pytest.mark.contract
def test_both_guard_regimes_are_frozen() -> None:
    """Remark rem:guard separates two condition pairs; both must fail somewhere."""
    lo1_fails = [c.case_id for c in GUARD_CASES if not c.guard_lo1_holds]
    lo0_fails = [c.case_id for c in GUARD_CASES if not c.guard_lo0_holds]
    up0_fails = [c.case_id for c in GUARD_CASES if not c.guard_up0_holds]
    # The near-unit-budget regime: a cost above one count.
    assert lo1_fails == ["GUARD-lower-two-counts"]
    # The ordinary-budget regime: the guard active at all, on BOTH sides, and
    # at n = 10^6 as well as n = 10 -- the F-2-01 correction of 0.1.2.
    assert set(lo0_fails) == {"GUARD-lower-two-counts", "GUARD-lower-active-uniform"}
    assert set(up0_fails) == {
        "GUARD-upper-active-uniform",
        "GUARD-fine-alphabet-million-rounds",
    }
    # Both degenerate honest masses, Theorem thm:sa3 (v).
    degenerate = {c.case_id: c for c in GUARD_CASES if c.p in (0, 1)}
    assert set(degenerate) == {"GUARD-degenerate-p-zero", "GUARD-degenerate-p-one"}
    assert degenerate["GUARD-degenerate-p-zero"].k_upper == 0
    assert degenerate["GUARD-degenerate-p-one"].k_lower == 4


# ---------------------------------------------------------------------------
#  6. SA4 / SA5 / SA6 / SA8 -- the emitted geometry and what travels with it
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_constructions_emit_a_well_formed_canonical_box() -> None:
    for case in CONSTRUCTION_CASES:
        outcomes, n = case.outcomes, case.rounds
        m = len(outcomes)
        assert sum(case.honest) == 1, case.case_id
        assert all(v >= 0 for v in case.honest), case.case_id
        assert set(case.constrained) <= set(outcomes), case.case_id
        # Theorem thm:box-construction (ii).
        for lo, hi in zip(case.box_lower, case.box_upper, strict=True):
            assert 0 <= lo <= hi <= 1, case.case_id
        # Theorem thm:box-construction (i): denominator n on Chat_con, else 0 or 1.
        for outcome, lo, hi in zip(
            outcomes, case.box_lower, case.box_upper, strict=True
        ):
            if outcome in case.constrained:
                assert (lo * n).denominator == 1, (case.case_id, outcome)
                assert (hi * n).denominator == 1, (case.case_id, outcome)
            else:
                assert (lo, hi) == (0, 1), (case.case_id, outcome)
        # Eq. eq:boxrows, and m_row = 2|Chat| INDEPENDENT of Chat_con.
        assert case.m_row == 2 * m, case.case_id
        assert len(case.rows) == case.m_row, case.case_id
        assert len(case.rhs) == case.m_row, case.case_id
        for i in range(m):
            cap = tuple(1 if j == i else 0 for j in range(m))
            floor = tuple(-1 if j == i else 0 for j in range(m))
            assert case.rows[i] == cap, (case.case_id, i)
            assert case.rows[m + i] == floor, (case.case_id, i)
            assert case.rhs[i] == case.box_upper[i], (case.case_id, i)
            assert case.rhs[m + i] == -case.box_lower[i], (case.case_id, i)
        assert all(v in (0, 1, -1) for row in case.rows for v in row), case.case_id


@pytest.mark.contract
def test_constructions_contain_the_honest_point_and_are_non_empty() -> None:
    """Theorems thm:box-construction (iii) and thm:honest-containment (i), unconditionally on all twelve."""  # noqa: E501
    for case in CONSTRUCTION_CASES:
        contained = all(
            lo <= p <= hi
            for lo, p, hi in zip(
                case.box_lower, case.honest, case.box_upper, strict=True
            )
        )
        assert contained is True, case.case_id
        assert case.honest_contained is True, case.case_id
        assert case.box_sums == (sum(case.box_lower), sum(case.box_upper)), case.case_id
        # Eq. eq:boxfeas follows from containment, and is NECESSARY here.
        assert case.box_sums[0] <= 1 <= case.box_sums[1], case.case_id


@pytest.mark.contract
def test_the_tight_bounds_are_inside_the_raw_ones_and_are_the_true_range() -> None:
    """The raw/tight split of Group SA-D's header, checked by its closed form.

    The closed form is Theorem thm:box-oracle (ii)'s own fill at g = -e_chat and
    g = +e_chat; it is used here to validate a frozen column that the module
    MUST NOT emit, so no implementation surface is reconstructed by it.
    """
    loose = []
    for case in CONSTRUCTION_CASES:
        for i in range(len(case.outcomes)):
            others_lower = sum(case.box_lower) - case.box_lower[i]
            others_upper = sum(case.box_upper) - case.box_upper[i]
            tight_hi = min(case.box_upper[i], 1 - others_lower)
            tight_lo = max(case.box_lower[i], 1 - others_upper)
            assert case.tight_upper[i] == tight_hi, (case.case_id, i)
            assert case.tight_lower[i] == tight_lo, (case.case_id, i)
            assert case.box_lower[i] <= tight_lo <= tight_hi <= case.box_upper[i], (
                case.case_id,
                i,
            )
        if (case.tight_lower, case.tight_upper) != (case.box_lower, case.box_upper):
            loose.append(case.case_id)
    # Six cases where the emitted box is strictly looser than its denotation.
    # All four two-letter cases with a PROPER SUBSET as Chat_con are loose, for
    # the same structural reason -- the unconstrained coordinate carries the
    # vacuous [0, 1] while sum q = 1 pins it -- and ACC-one-letter-unconstrained
    # is loose on a FLOOR rather than a cap.
    assert set(loose) == {
        "ACC-guard-lower-two-counts",
        "ACC-support-superset",
        "ACC-one-letter-unconstrained",
        "ACC-raw-vs-tight-3letter",
        "ACC-n2-singleton",
        "ACC-n3-wider",
    }
    unconstrained = next(
        c for c in CONSTRUCTION_CASES if c.case_id == "ACC-one-letter-unconstrained"
    )
    assert unconstrained.box_lower == (Fraction(0),)
    assert unconstrained.tight_lower == (Fraction(1),)


@pytest.mark.contract
def test_the_acceptance_support_is_the_cap_positivity_set() -> None:
    """Theorem thm:box-oracle (i) and the Outputs-table formula, on all twelve."""
    superset = []
    for case in CONSTRUCTION_CASES:
        expected = tuple(
            outcome
            for outcome, hi in zip(case.outcomes, case.box_upper, strict=True)
            if hi > 0
        )
        assert case.acceptance_support == expected, case.case_id
        # The minimal support is the union of supports over the DENOTED set,
        # i.e. the outcomes whose tight upper bound is positive.
        minimal = tuple(
            outcome
            for outcome, hi in zip(case.outcomes, case.tight_upper, strict=True)
            if hi > 0
        )
        assert case.minimal_support == minimal, case.case_id
        assert set(case.minimal_support) <= set(case.acceptance_support), case.case_id
        if set(case.minimal_support) < set(case.acceptance_support):
            superset.append(case.case_id)
    # Emitting a STRICT superset is conforming; exactly one case does it.
    assert superset == ["ACC-support-superset"]
    # And exactly one case emits a support strictly smaller than the alphabet.
    smaller = [
        c.case_id
        for c in CONSTRUCTION_CASES
        if set(c.acceptance_support) < set(c.outcomes)
    ]
    assert smaller == ["ACC-degenerate-honest-mass"]


@pytest.mark.contract
def test_completeness_is_bounded_by_the_budget_and_bounds_the_truth() -> None:
    """Theorem thm:completeness-bound, Eq. eq:completeness, both inequalities."""
    loose = []
    for case in CONSTRUCTION_CASES:
        assert 0 <= case.epsilon_star <= case.ecomp, case.case_id
        assert 0 <= case.true_failure_probability <= case.epsilon_star, case.case_id
        if case.true_failure_probability < case.epsilon_star:
            loose.append(case.case_id)
    # The union bound double-counts on a binary alphabet with Chat_con = Chat,
    # by a factor of EXACTLY 2 in all three such cases.
    assert set(loose) == {
        "ACC-normal-2letter",
        "ACC-budget-large",
        "ACC-guard-active-uniform",
    }
    for case_id in loose:
        case = next(c for c in CONSTRUCTION_CASES if c.case_id == case_id)
        assert case.epsilon_star == 2 * case.true_failure_probability, case_id


@pytest.mark.contract
def test_the_budget_monotonicity_pair_is_nested_and_the_n_pair_is_not() -> None:
    """Theorem thm:monotonicity-limits (i) against Theorem thm:monotonicity-limits (v), on frozen boxes."""  # noqa: E501
    by_id = {c.case_id: c for c in CONSTRUCTION_CASES}
    small, large = by_id["ACC-normal-2letter"], by_id["ACC-budget-large"]
    assert small.ecomp < large.ecomp
    # A LARGER budget buys a SMALLER set, strictly at all four endpoints.
    for i in range(len(small.outcomes)):
        assert small.box_lower[i] < large.box_lower[i]
        assert large.box_upper[i] < small.box_upper[i]
    # epsilon_star rises with the budget: the trade-off, not an improvement.
    assert small.epsilon_star < large.epsilon_star
    # No monotonicity in n: the n = 2 set is STRICTLY inside the n = 3 set.
    two, three = by_id["ACC-n2-singleton"], by_id["ACC-n3-wider"]
    assert two.rounds < three.rounds
    for i in range(len(two.outcomes)):
        assert three.tight_lower[i] <= two.tight_lower[i]
        assert two.tight_upper[i] <= three.tight_upper[i]
    assert (two.tight_lower, two.tight_upper) != (three.tight_lower, three.tight_upper)
    # And epsilon_star moves the other way, so neither proxies for the other.
    assert two.epsilon_star > three.epsilon_star


@pytest.mark.contract
def test_the_limiting_constructions_are_present_and_correct() -> None:
    by_id = {c.case_id: c for c in CONSTRUCTION_CASES}
    # ecomp = 0 buys the whole simplex (Theorem thm:monotonicity-limits (iii)).
    zero = by_id["ACC-ecomp-zero"]
    assert zero.ecomp == 0
    assert zero.box_lower == (Fraction(0),) * 3
    assert zero.box_upper == (Fraction(1),) * 3
    assert zero.epsilon_star == 0
    # |Chat| = 1: both branches agree on the denotation (Theorem thm:monotonicity-limits
    # (vi)).
    one = by_id["ACC-one-letter-constrained"]
    other = by_id["ACC-one-letter-unconstrained"]
    assert one.outcomes == other.outcomes == ("c0",)
    assert one.tight_lower == other.tight_lower == (Fraction(1),)
    assert one.tight_upper == other.tight_upper == (Fraction(1),)
    assert one.epsilon_star == other.epsilon_star == 0
    assert other.constrained == ()
    # Degenerate honest mass leaves the whole budget unspent.
    degenerate = by_id["ACC-degenerate-honest-mass"]
    assert degenerate.ecomp > 0
    assert degenerate.epsilon_star == 0


# ---------------------------------------------------------------------------
#  7. SA8 -- the box minimum and its tight dual witness
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_box_minima_are_feasible_optimal_and_certified_by_their_witness() -> None:
    """Theorem thm:box-oracle (ii)-(iii), checked by substitution only.

    The greedy fill of Eq. eq:greedy is NOT re-run here: ``q_opt`` is frozen and
    is checked for feasibility, for value, and against its own dual witness.
    """
    for case in BOX_MINIMUM_CASES:
        m = len(case.outcomes)
        lower, upper, g = case.box_lower, case.box_upper, case.g
        # Theorem thm:box-oracle (ii) is stated for a NON-EMPTY box (Eq. eq:boxfeas).
        assert sum(lower) <= 1 <= sum(upper), case.case_id
        # Every frozen minimizer is feasible and attains the frozen minimum.
        for point in (case.q_opt, *case.minimizers):
            assert sum(point) == 1, case.case_id
            for lo, value, hi in zip(lower, point, upper, strict=True):
                assert lo <= value <= hi, case.case_id
            paired = sum(gi * qi for gi, qi in zip(g, point, strict=True))
            assert paired == case.minimum, case.case_id
        # The sorted order is g ascending, and lambda is g at the split.
        order = [case.outcomes.index(name) for name in case.sorted_order]
        assert sorted(order) == list(range(m)), case.case_id
        values = [g[i] for i in order]
        assert values == sorted(values), case.case_id
        assert case.lam == g[case.outcomes.index(case.j_star)], case.case_id
        assert case.dual_v == -case.lam, case.case_id
        # r and the widths, in the sorted order.
        assert case.residual_r == 1 - sum(lower), case.case_id
        assert case.widths == tuple(upper[i] - lower[i] for i in order), case.case_id
        assert all(w >= 0 for w in case.widths), case.case_id
        # b of Eq. eq:boxrows: caps then floors.
        assert case.rhs == tuple(upper) + tuple(-v for v in lower), case.case_id
        # u >= 0, and Eq. eq:dualfeas with EQUALITY.
        assert len(case.dual_u) == 2 * m, case.case_id
        assert all(v >= 0 for v in case.dual_u), case.case_id
        caps, floors = case.dual_u[:m], case.dual_u[m:]
        for i in range(m):
            assert caps[i] == max(case.lam - g[i], Fraction(0)), (case.case_id, i)
            assert floors[i] == max(g[i] - case.lam, Fraction(0)), (case.case_id, i)
            residual = g[i] + (caps[i] - floors[i]) + case.dual_v
            assert residual == case.dual_feasibility[i], (case.case_id, i)
            assert residual == 0, (case.case_id, i)
        # Eq. eq:dualvalue: the witness is TIGHT.
        pairing = sum(b * u for b, u in zip(case.rhs, case.dual_u, strict=True))
        assert -pairing - case.dual_v == case.dual_value, case.case_id
        assert case.dual_value == case.minimum, case.case_id


@pytest.mark.contract
def test_all_three_fill_regimes_and_the_tie_are_frozen() -> None:
    by_id = {c.case_id: c for c in BOX_MINIMUM_CASES}
    widths = {
        c.case_id: dict(zip(c.sorted_order, c.widths, strict=True))
        for c in BOX_MINIMUM_CASES
    }
    at_cap: list[str] = []
    inside: list[str] = []
    degenerate: list[str] = []
    for case in BOX_MINIMUM_CASES:
        width = widths[case.case_id][case.j_star]
        if case.fill_increment == 0:
            degenerate.append(case.case_id)
        elif case.fill_increment == width:
            at_cap.append(case.case_id)
        else:
            assert 0 < case.fill_increment < width, case.case_id
            inside.append(case.case_id)
    assert set(at_cap) == {
        "PMIN-normal-fill-at-cap",
        "PMIN-floors-carry-the-mass",
        "PMIN-tie-in-g",
    }
    assert inside == ["PMIN-fill-strictly-inside"]
    assert set(degenerate) == {"PMIN-degenerate-point", "PMIN-box-superset"}
    # The tie: two DIFFERENT minimizers, ONE minimum, and a zero witness.
    tie = by_id["PMIN-tie-in-g"]
    assert len(set(tie.minimizers)) == 2
    assert len(set(tie.g)) == 1
    assert set(tie.dual_u) == {Fraction(0)}
    # The strict-superset case: the sum over the LARGER support agrees.
    superset = by_id["PMIN-box-superset"]
    assert superset.acceptance_support == ("c0", "c1")
    assert superset.minimum == Fraction(5)


# ---------------------------------------------------------------------------
#  8. SA9 -- singleton completeness, including both degenerate cases
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_singleton_cases_are_consistent_with_theorem_sa9() -> None:
    for case in SINGLETON_CASES:
        assert sum(case.honest) == 1, case.case_id
        assert sum(case.q_star) == 1, case.case_id
        assert all(v >= 0 for v in case.q_star), case.case_id
        scaled = [case.rounds * v for v in case.q_star]
        integral = all(v.denominator == 1 and v >= 0 for v in scaled)
        assert case.counts_are_integral is integral, case.case_id
        if integral:
            assert case.counts == tuple(int(v) for v in scaled), case.case_id
            assert sum(case.counts) == case.rounds, case.case_id
        else:
            assert case.counts is None, case.case_id
        # q^* << p^hon: q^*(chat) > 0 implies p^hon(chat) > 0.
        absolutely_continuous = all(
            p > 0 for q, p in zip(case.q_star, case.honest, strict=True) if q > 0
        )
        assert case.absolutely_continuous is absolutely_continuous, case.case_id
        # Theorem thm:singleton-completeness (ii): the probability is 0 iff one of the
        # two fails.
        expect_zero = not (integral and absolutely_continuous)
        assert (case.accept_probability == 0) is expect_zero, case.case_id
        if expect_zero:
            # The admissible interval is [1, 1) = EMPTY. ecomp = 1 is NOT a
            # substitute: it lies outside the declared domain [0, 1).
            assert case.least_admissible_budget is None, case.case_id
            assert "EMPTY" in case.admissible_budget_interval, case.case_id
        else:
            assert 0 < case.accept_probability <= 1, case.case_id
            assert case.least_admissible_budget == 1 - case.accept_probability, (
                case.case_id
            )
            assert 0 <= case.least_admissible_budget < 1, case.case_id


@pytest.mark.contract
def test_both_degenerate_singleton_routes_and_the_zero_budget_are_frozen() -> None:
    by_id = {c.case_id: c for c in SINGLETON_CASES}
    # Route 1: non-integer counts. Route 2: failed absolute continuity, with
    # INTEGRAL counts -- so the two routes are independent.
    non_integral = by_id["SING-nonintegral-counts"]
    not_ac = by_id["SING-not-absolutely-continuous"]
    assert non_integral.counts_are_integral is False
    assert non_integral.absolutely_continuous is True
    assert not_ac.counts_are_integral is True
    assert not_ac.absolutely_continuous is False
    assert non_integral.least_admissible_budget is None
    assert not_ac.least_admissible_budget is None
    # Theorem thm:singleton-completeness (iii): budget 0 iff p^hon is a point mass and
    # q^* equals it. Exactly two cases reach it, and both have a point-mass honest law.
    zero = [c for c in SINGLETON_CASES if c.least_admissible_budget == 0]
    assert {c.case_id for c in zero} == {
        "SING-point-mass-zero-budget",
        "SING-one-letter",
    }
    for case in zero:
        assert case.accept_probability == 1
        assert max(case.honest) == 1
        assert case.q_star == case.honest
    # The SA5 / SA9 agreement on the one set both statements apply to.
    agreement = by_id["SING-n2-agrees-with-sa5"]
    construction = next(
        c for c in CONSTRUCTION_CASES if c.case_id == "ACC-n2-singleton"
    )
    assert agreement.least_admissible_budget == construction.epsilon_star
    assert agreement.least_admissible_budget == Fraction(1, 2)


# ---------------------------------------------------------------------------
#  9. SA6 -- the infeasibility report
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_every_reason_code_has_exactly_one_case_and_emits_no_set() -> None:
    seen = [case.reason_code for case in INPUT_DOMAIN_VIOLATION_CASES]
    assert seen == list(REASON_CODES)
    assert len(set(seen)) == 9
    for case in INPUT_DOMAIN_VIOLATION_CASES:
        assert case.emits_acceptance_set is False, case.case_id
        assert case.violated_clause.strip(), case.case_id
        assert case.offending_input.strip(), case.case_id
