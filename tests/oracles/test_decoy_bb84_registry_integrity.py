"""The decoy registry is well formed, admissible, and internally consistent.

The four things ``test_registry_integrity.py`` pins for the original
freeze, for the decoy instance's frozen targets.

1. **Admissibility.** No expected value comes from MATLAB, OpenQKDSecurity,
   CVX, MOSEK or Julia; the guard reuses ``registry.INADMISSIBLE_SOURCES``,
   imported rather than restated.
2. **Well-formedness.** Unique ids, a kind from
   ``registry_instances_decoy_bb84.DECOY_KINDS``, an instance that exists, a
   derivation long enough to redo on paper, hypotheses that are stated and an
   observable named for the implementer's test.
3. **Traceability.** Every claim id an entry names has a claim file under
   ``spec/modules/``; and every id listed for the batch-C3 re-pin that has
   SINCE APPEARED is pinned, so the re-pin cannot be forgotten silently.
4. **The freeze.** Every alpha-dependent table is its own closed form
   evaluated on ``ALPHA_GRID``, and the relations that hold AMONG the frozen
   numbers -- the sector weights that sum to the declared marginal, the three
   exact checks of OT4, the rank-one factorisation of OT3, the two
   normalisation conventions in the right order -- are recomputed here in
   exact rational arithmetic wherever the quantity is rational. THE
   DERIVATION, NOT THE TABLE, STAYS AUTHORITATIVE.

**Nothing here runs the engine.** No assertion below imports
``certiqs_key``: these tests pass NOW, before the implementation exists, which
is the whole point of freezing the values first (``PRINCIPLES.md`` section
2.3). The tests that compare an implementation against these entries are the
implementer's and are named in each entry's ``observable``.
"""

from __future__ import annotations

import math
from fractions import Fraction
from pathlib import Path

import pytest
from registry import ALPHA_GRID, INADMISSIBLE_SOURCES
from registry_instances_decoy_bb84 import (
    ACCEPTANCE_CONVENTIONS,
    DECOY_IDEAL_TWO_SECTOR,
    DECOY_INSTANCES,
    DECOY_KINDS,
    DECOY_ORACLES,
    DECOY_TOY,
    DECOY_VACUUM,
    OT3_FOIL_MARGINAL,
    OT3_FOIL_STATE,
    OT3_WITNESS_MARGINAL,
    OT3_WITNESS_STATE,
    Matrix,
    _freeze,
    bell_diagonal_bits,
    binary_entropy,
    d1_objective_with_tail,
    d2_objective_convention_b,
    decoy_instance,
    decoy_oracle,
    dropped_objective,
    flagged_single_photon_objective,
    sector_deficit_factor,
    sifted,
)

MODULES = Path(__file__).resolve().parents[2] / "spec" / "modules"

#: The one place a float comparison is made against a closed form evaluated
#: twice by the same route: the residue is the last-bit difference of a handful
#: of ``log2``/``exp`` calls on quantities of order one.
CLOSED_FORM_TOLERANCE = 1e-12


def _claim_file(claim_id: str) -> Path:
    """Return the claim file ``spec/modules/<module>/claims/<kind>-<name>.tex``."""
    parts = claim_id.split("/")
    stem = parts[-1].replace(":", "-")
    return MODULES.joinpath(*parts[:-1]) / "claims" / f"{stem}.tex"


def _exp_upper_bound(terms: int = 14) -> Fraction:
    """Return an exact rational STRICTLY above ``e``, by the series with a tail.

    ``e = sum_{n>=0} 1/n!`` and the omitted tail after ``T`` terms is below
    ``(1/T!) * (1/T) / (1 - 1/T)``, since every further ratio is at most
    ``1/T``. No library exponential is called: the registry's claim that both
    of DECOY-TOY's weight inequalities reduce to ``e < 4`` is checked against a
    bound a reader can redo.
    """
    total = Fraction(0)
    term = Fraction(1)
    for index in range(terms):
        total += term
        term /= index + 1
    tail = term * Fraction(terms, terms - 1)
    return total + tail


def _partial_trace_q(state: Matrix) -> Matrix:
    """Return ``tr_Q omega`` for a 4x4 operator on a qubit ``A`` (x) qubit ``Q``."""
    return tuple(
        tuple(state[2 * i][2 * j] + state[2 * i + 1][2 * j + 1] for j in range(2))
        for i in range(2)
    )


def _is_product_on_first_vector(state: Matrix) -> bool:
    """Return whether ``omega`` is supported on ``|0> (x) Q`` -- OT3's shape."""
    for i in range(4):
        for j in range(4):
            if (i >= 2 or j >= 2) and state[i][j] != 0:
                return False
    return True


# ---------------------------------------------------------------------------
#  1. Admissibility, well-formedness, traceability
# ---------------------------------------------------------------------------


@pytest.mark.oracle
def test_no_entry_derives_from_an_inadmissible_source() -> None:
    for entry in DECOY_ORACLES:
        blob = f"{entry.subject} {entry.derivation} {entry.observable}".lower()
        for source in INADMISSIBLE_SOURCES:
            assert source.lower() not in blob, (entry.oracle_id, source)


@pytest.mark.oracle
def test_no_entry_was_produced_by_the_implementation_it_pins() -> None:
    """No derivation may cite ``src/`` as the source of one of its numbers."""
    for entry in DECOY_ORACLES:
        assert "certiqs_key" not in entry.derivation, entry.oracle_id


@pytest.mark.oracle
def test_the_ids_are_unique_and_the_entries_are_well_formed() -> None:
    ids = [entry.oracle_id for entry in DECOY_ORACLES]
    assert len(ids) == len(set(ids))
    assert len(ids) == 10, "D-1 to D-5 and OT1 to OT5"
    for entry in DECOY_ORACLES:
        assert entry.kind in DECOY_KINDS, entry.oracle_id
        assert entry.claims, entry.oracle_id
        assert len(entry.subject) > 60, entry.oracle_id
        assert len(entry.derivation) > 800, entry.oracle_id
        assert entry.hypotheses, entry.oracle_id
        assert all(len(h) > 30 for h in entry.hypotheses), entry.oracle_id
        assert len(entry.observable) > 60, entry.oracle_id
        assert decoy_oracle(entry.oracle_id) is entry
        decoy_instance(entry.instance)


@pytest.mark.oracle
def test_a_relation_entry_carries_a_relation_and_no_other_kind_does() -> None:
    for entry in DECOY_ORACLES:
        if entry.kind == "relation":
            assert entry.relation is not None, entry.oracle_id
            assert len(entry.relation) > 60, entry.oracle_id
        else:
            assert entry.relation is None, entry.oracle_id
        if entry.value is not None:
            assert entry.value_closed_form, entry.oracle_id


@pytest.mark.oracle
def test_every_hypothesis_set_fixes_the_reconciliation_and_the_normalisation() -> None:
    """Rule (3) of the brief: no entry may be satisfied by reinterpretation."""
    for entry in DECOY_ORACLES:
        blob = " ".join(entry.hypotheses).lower()
        assert any(
            key in blob for key in ("reconciliation", "feasible", "convention")
        ), entry.oracle_id


@pytest.mark.oracle
def test_every_pinned_claim_resolves_to_a_claim_file() -> None:
    for entry in DECOY_ORACLES:
        for claim_id in entry.claims:
            assert _claim_file(claim_id).is_file(), (entry.oracle_id, claim_id)


@pytest.mark.oracle
def test_the_batch_c3_repins_are_still_open_or_already_pinned() -> None:
    """The ratchet: an id that has appeared since must be pinned, not listed."""
    for entry in DECOY_ORACLES:
        for claim_id in entry.repin_after_c3:
            if _claim_file(claim_id).is_file():
                assert claim_id in entry.claims, (
                    f"{claim_id} now exists: re-pin {entry.oracle_id} against it "
                    "deliberately, in its own commit"
                )


@pytest.mark.oracle
def test_the_c3_repin_is_done_and_recorded() -> None:
    """Every entry re-read against accepted C2b/C3 and says what it found."""
    for entry in DECOY_ORACLES:
        assert entry.repin_after_c3 == (), entry.oracle_id
        assert len(entry.revalidation) > 400, entry.oracle_id
        assert "STAND" in entry.revalidation.upper(), entry.oracle_id


@pytest.mark.oracle
def test_the_mathematics_batch_c3_added_is_pinned_where_it_is_used() -> None:
    """The ids that landed, against the entries whose derivation consumes them."""
    expected = {
        "meat-core/lem:rank-one-sector": {
            "O-DECOY-D1-QUBIT-LIMIT",
            "O-DECOY-D2-VACUUM-BIT",
            "O-DECOY-D3-CUTOFF-MONOTONE",
            "O-DECOY-D4-INFINITE-DECOY-CEILING",
            "O-DECOY-OT1-VACUUM-DEFICIT",
            "O-DECOY-OT2-FLAG-KEY-INERT",
            "O-DECOY-OT3-RANK-ONE-PRODUCT",
            "O-DECOY-OT5-DROPPED-HONEST",
        },
        "meat-core/prop:drop-bound": {
            "O-DECOY-D3-CUTOFF-MONOTONE",
            "O-DECOY-OT2-FLAG-KEY-INERT",
            "O-DECOY-OT5-DROPPED-HONEST",
        },
        "meat-core/cor:drop-program": {"O-DECOY-OT5-DROPPED-HONEST"},
        "meat-core/lem:ensemble-form": {
            "O-DECOY-D5-STATISTICS",
            "O-DECOY-OT1-VACUUM-DEFICIT",
            "O-DECOY-OT4-ONE-PHOTON-BELL",
        },
        "reductions/lem:precomposition": {"O-DECOY-D3-CUTOFF-MONOTONE"},
    }
    for claim_id, holders in expected.items():
        assert _claim_file(claim_id).is_file(), claim_id
        pinned = {e.oracle_id for e in DECOY_ORACLES if claim_id in e.claims}
        assert pinned == holders, claim_id


@pytest.mark.oracle
def test_ot4_does_not_pin_the_rank_one_lemma_it_is_not_covered_by() -> None:
    """The one-photon sector's marginal is rank TWO, so the lemma does not apply."""
    entry = decoy_oracle("O-DECOY-OT4-ONE-PHOTON-BELL")
    assert "meat-core/lem:rank-one-sector" not in entry.claims
    assert "rank TWO" in entry.revalidation
    # And the instance says so: tau^(1)_A = (1/8) 1_2 has rank two.
    assert DECOY_TOY.one_photon_lambdas_exact[0] != 1


@pytest.mark.oracle
def test_both_acceptance_conventions_are_named_and_used() -> None:
    names = {name for name, _ in ACCEPTANCE_CONVENTIONS}
    assert names == {"A", "B"}
    assert {instance.acceptance_convention for instance in DECOY_INSTANCES} == {"A"}
    entry = decoy_oracle("O-DECOY-D2-VACUUM-BIT")
    assert "CONVENTION A" in entry.derivation.upper()
    assert "CONVENTION B" in entry.derivation.upper()


# ---------------------------------------------------------------------------
#  2. The frozen tables are their own closed forms
# ---------------------------------------------------------------------------


#: How far a recomputed closed form may lie from its frozen value, in units in
#: the last place of the frozen value. The closed forms chain a few ``**``,
#: ``math.log2`` and ``math.log`` calls, which the C library evaluates to
#: within about an ulp but not identically on every platform: recomputed with
#: glibc, ``O-DECOY-OT5-DROPPED-HONEST`` at alpha 1.25 lands one ulp below the
#: value frozen with the Windows C runtime. Four ulps (about 9e-16 relative)
#: admit that and still catch any edit of a closed form or of a frozen digit
#: before the last; the frozen values themselves are never regenerated.
FREEZE_ULPS = 4


@pytest.mark.oracle
def test_every_frozen_table_is_its_closed_form_on_the_alpha_grid() -> None:
    seen = 0
    for entry in DECOY_ORACLES:
        if entry.closed_form is None:
            assert entry.frozen_values == (), entry.oracle_id
            continue
        seen += 1
        assert entry.frozen_values, entry.oracle_id
        assert tuple(a for a, _ in entry.frozen_values) == ALPHA_GRID
        for (alpha, frozen), (_, recomputed) in zip(
            entry.frozen_values, _freeze(entry.closed_form), strict=True
        ):
            assert abs(frozen - recomputed) <= FREEZE_ULPS * math.ulp(frozen), (
                entry.oracle_id, alpha, frozen.hex(), recomputed.hex())
    assert seen >= 5


# ---------------------------------------------------------------------------
#  3. DECOY-TOY's arithmetic, in exact rationals where it is rational
# ---------------------------------------------------------------------------


@pytest.mark.oracle
def test_the_declared_weights_are_dyadic_and_sum_to_one() -> None:
    for instance in DECOY_INSTANCES:
        total = instance.tail_weight
        for _, weight in instance.declared_weights:
            total += weight
            # A binary64 number, which cor:emitted-decoy (iv) demands of every
            # formed entry: the denominator is a power of two.
            denominator = weight.denominator
            assert denominator & (denominator - 1) == 0, instance.instance_id
        assert total == 1, instance.instance_id


@pytest.mark.oracle
def test_decoy_toys_weight_inequalities_are_strict_and_reduce_to_e_below_four() -> None:
    """``p~(0|mu) < e^{-1/2}`` and ``p~(1|mu) < (1/2) e^{-1/2}``, both iff e < 4."""
    bound = _exp_upper_bound()
    # e < 4 STRICTLY, hence e^{1/2} < 2, hence e^{-1/2} > 1/2 = p~(0|mu): the
    # first inequality is strict. The second, p~(1|mu) = 1/4 < (1/2) e^{-1/2},
    # is the first divided by two at mu = 1/2, so one bound serves both.
    assert bound < 4, bound
    assert dict(DECOY_TOY.declared_weights)["vacuum"] == Fraction(1, 2)
    assert dict(DECOY_TOY.declared_weights)["one-photon"] == Fraction(1, 4)
    # The second inequality is the first divided by two, at mu = 1/2.
    assert DECOY_TOY.intensity == Fraction(1, 2)


@pytest.mark.oracle
def test_decoy_toys_sector_yields_are_the_threshold_model() -> None:
    eta, dark = DECOY_TOY.efficiency, DECOY_TOY.dark_count
    yields = dict(DECOY_TOY.sector_yields)
    assert yields["vacuum"] == 1 - (1 - dark)
    assert yields["one-photon"] == 1 - (1 - dark) * (1 - eta)
    assert yields["vacuum"] == Fraction(1, 64)
    assert yields["one-photon"] == Fraction(67, 256)


@pytest.mark.oracle
def test_decoy_toys_sifted_generation_probabilities_are_the_products() -> None:
    weights = dict(DECOY_TOY.declared_weights)
    yields = dict(DECOY_TOY.sector_yields)
    coin = 1 - DECOY_TOY.test_coin
    for sector in ("vacuum", "one-photon"):
        expected = coin * weights[sector] * yields[sector]
        assert Fraction(sifted(DECOY_TOY, sector)) == expected, sector
    total = sum(float(value) for _, value in DECOY_TOY.sifted_generation)
    assert total == pytest.approx(
        float(DECOY_TOY.sifted_generation_total), abs=1e-15
    )


@pytest.mark.oracle
def test_the_tail_yield_is_forced_by_d5s_identity() -> None:
    """D-5: the three sector terms reproduce ``1 - (1 - p_dc) e^{-eta mu}``.

    The identity is linear in the one irrational ``x = e^{-1/8}``, so it is
    checked as a pair (constant part, coefficient of x) in EXACT rationals and
    no exponential is evaluated.
    """
    weights = dict(DECOY_TOY.declared_weights)
    yields = dict(DECOY_TOY.sector_yields)
    low = weights["vacuum"] * yields["vacuum"] + (
        weights["one-photon"] * yields["one-photon"]
    )
    assert low == Fraction(75, 1024)
    # Y_tail = 949/256 - (63/16) x, from the registry's closed form.
    tail_constant, tail_coefficient = Fraction(949, 256), Fraction(-63, 16)
    constant = low + DECOY_TOY.tail_weight * tail_constant
    coefficient = DECOY_TOY.tail_weight * tail_coefficient
    # sum_n p_mu(n) Y_n = 1 - (63/64) x.
    assert constant == 1
    assert coefficient == Fraction(-63, 64)
    # And P_gen = (1 - gamma) times that.
    coin = 1 - DECOY_TOY.test_coin
    assert coin * constant == Fraction(1, 2)
    assert coin * coefficient == Fraction(-63, 128)
    evaluated = float(coin * constant) + float(coin * coefficient) * math.exp(-0.125)
    assert evaluated == pytest.approx(
        float(DECOY_TOY.sifted_generation_total), abs=CLOSED_FORM_TOLERANCE
    )


# ---------------------------------------------------------------------------
#  4. The targets, recomputed from their own closed forms
# ---------------------------------------------------------------------------


@pytest.mark.oracle
def test_ot1s_uniform_factor_is_one_minus_two_to_the_one_minus_alpha() -> None:
    entry = decoy_oracle("O-DECOY-OT1-VACUUM-DEFICIT")
    for alpha, frozen in entry.frozen_values:
        assert frozen == pytest.approx(
            1.0 - 2.0 ** (1.0 - alpha), abs=CLOSED_FORM_TOLERANCE
        )
        # H_alpha(pi) = 1 for the uniform binary key value, at every order.
        assert -math.log2(1.0 - frozen) / (alpha - 1.0) == pytest.approx(
            1.0, abs=CLOSED_FORM_TOLERANCE
        )


@pytest.mark.oracle
def test_ot1s_biased_foil_is_strictly_smaller_at_every_alpha() -> None:
    """An unbalanced key bit carries less than one bit -- the foil of OT1."""
    for alpha in ALPHA_GRID:
        uniform = sector_deficit_factor(alpha, (0.5, 0.5))
        biased = sector_deficit_factor(alpha, (0.75, 0.25))
        assert 0.0 < biased < uniform < 1.0, alpha
    entry = decoy_oracle("O-DECOY-OT1-VACUUM-DEFICIT")
    assert "0.12526966037678844" in entry.derivation


@pytest.mark.oracle
def test_ot2s_value_is_exactly_zero_and_is_an_identity() -> None:
    entry = decoy_oracle("O-DECOY-OT2-FLAG-KEY-INERT")
    assert entry.value == 0
    # A point mass gives sum_z pi(z)^alpha = 1, hence a zero factor, at every
    # alpha: the deficit is zero identically and not merely bounded by zero.
    for alpha in ALPHA_GRID:
        assert sector_deficit_factor(alpha, (1.0,)) == 0.0
    assert entry.closed_form is None


@pytest.mark.oracle
def test_ot3s_witness_factorises_and_the_foil_does_not() -> None:
    assert _partial_trace_q(OT3_WITNESS_STATE) == OT3_WITNESS_MARGINAL
    assert _is_product_on_first_vector(OT3_WITNESS_STATE)
    assert _partial_trace_q(OT3_FOIL_STATE) == OT3_FOIL_MARGINAL
    assert not _is_product_on_first_vector(OT3_FOIL_STATE)
    # The marginals are what the statement is about: rank one against rank two.
    assert OT3_WITNESS_MARGINAL[1][1] == 0
    assert OT3_FOIL_MARGINAL[0][0] == OT3_FOIL_MARGINAL[1][1] != 0
    # Both are trace one and diagonally dominant enough to be states.
    for state in (OT3_WITNESS_STATE, OT3_FOIL_STATE):
        assert sum(state[i][i] for i in range(4)) == 1


@pytest.mark.oracle
def test_ot4s_three_exact_checks() -> None:
    for alpha in ALPHA_GRID:
        # (a) a noiseless one-photon channel gives a full bit, exactly.
        assert bell_diagonal_bits((1.0, 0.0, 0.0, 0.0), alpha) == 1.0
        # (b) a maximally mixed block gives none.
        assert bell_diagonal_bits((0.25,) * 4, alpha) == pytest.approx(
            0.0, abs=CLOSED_FORM_TOLERANCE
        )
    # (c) the alpha -> 1+ limit is 1 - H(phase | bit) at the honest lambda.
    limit = 1.0 - ((7 / 8) * binary_entropy(1 / 14) + 1 / 8)
    assert limit == pytest.approx(0.5501717141892338, abs=CLOSED_FORM_TOLERANCE)
    near = bell_diagonal_bits(DECOY_TOY.one_photon_lambdas, 1.0 + 1e-7)
    assert near == pytest.approx(limit, abs=1e-6)
    # And the exact value at alpha = 2, which the derivation writes out.
    exact = 1.0 - math.log2((9 + math.sqrt(13)) / 8)
    assert bell_diagonal_bits(DECOY_TOY.one_photon_lambdas, 2.0) == pytest.approx(
        exact, abs=CLOSED_FORM_TOLERANCE
    )
    assert decoy_oracle("O-DECOY-OT4-ONE-PHOTON-BELL").value == pytest.approx(
        exact, abs=CLOSED_FORM_TOLERANCE
    )


@pytest.mark.oracle
def test_ot4s_lambdas_are_the_declared_error_rate() -> None:
    exact = DECOY_TOY.one_photon_lambdas_exact
    assert sum(exact) == 1
    assert exact[2] + exact[3] == DECOY_TOY.error_rate, "bit error"
    assert exact[1] + exact[3] == DECOY_TOY.error_rate, "phase error"


@pytest.mark.oracle
def test_ot5s_limit_is_the_sum_of_the_sector_contributions() -> None:
    """``lim O^D = g_0 * 1 + g_1 * h_1(1) + g_tail * 0``, and NOT D-4's number."""
    entry = decoy_oracle("O-DECOY-OT5-DROPPED-HONEST")
    g_0 = sifted(DECOY_TOY, "vacuum")
    g_1 = sifted(DECOY_TOY, "one-photon")
    honest_bits = 1.0 - ((7 / 8) * binary_entropy(1 / 14) + 1 / 8)
    limit = g_0 + g_1 * honest_bits
    assert entry.value == pytest.approx(limit, abs=CLOSED_FORM_TOLERANCE)
    assert dropped_objective(1.0 + 1e-6) == pytest.approx(limit, abs=1e-6)
    # The two numbers that must not be confused: the honest point's limit is
    # STRICTLY ABOVE D-4's ceiling, which uses 1 - h2(e_1) instead.
    ceiling = decoy_oracle("O-DECOY-D4-INFINITE-DECOY-CEILING").value
    assert ceiling is not None
    assert ceiling == pytest.approx(
        g_0 + g_1 * (1.0 - binary_entropy(1 / 8)), abs=CLOSED_FORM_TOLERANCE
    )
    assert float(ceiling) < limit


@pytest.mark.oracle
def test_ot5s_objective_decreases_in_alpha_and_stays_below_p_gen() -> None:
    p_gen = float(DECOY_TOY.sifted_generation_total)
    values = [dropped_objective(alpha) for alpha in ALPHA_GRID]
    assert values == sorted(values, reverse=True)
    for value in values:
        assert 0.0 < value < p_gen


@pytest.mark.oracle
def test_d3s_witness_orders_the_two_cutoffs() -> None:
    """Flagging the one-photon sector lowers the objective at every alpha."""
    for alpha in ALPHA_GRID:
        assert flagged_single_photon_objective(alpha) < dropped_objective(alpha)
    assert flagged_single_photon_objective(2.0) == pytest.approx(
        0.002860531747143983, abs=CLOSED_FORM_TOLERANCE
    )


@pytest.mark.oracle
def test_d2s_two_conventions_are_ordered_and_meet_in_the_limit() -> None:
    entry = decoy_oracle("O-DECOY-D2-VACUUM-BIT")
    convention_a = float(DECOY_VACUUM.sifted_generation_total)
    assert entry.value == Fraction(1, 128)
    assert convention_a == 1 / 128
    for alpha, frozen in entry.frozen_values:
        assert frozen < convention_a, alpha
    assert d2_objective_convention_b(1.0 + 1e-6) == pytest.approx(
        convention_a, abs=1e-6
    )


@pytest.mark.oracle
def test_d1s_tail_costs_alpha_independence_and_is_recovered_in_the_limit() -> None:
    entry = decoy_oracle("O-DECOY-D1-QUBIT-LIMIT")
    target = float(sifted(DECOY_IDEAL_TWO_SECTOR, "one-photon"))
    assert entry.value == Fraction(1, 8)
    assert target == 0.125
    for alpha, frozen in entry.frozen_values:
        assert frozen < target, alpha
    assert d1_objective_with_tail(1.0 + 1e-6) == pytest.approx(target, abs=1e-6)
    # T4 does NOT scale: the root of 1 - 2 h2(Q) is where it always was.
    low, high = 0.0, 0.5
    for _ in range(200):
        middle = 0.5 * (low + high)
        if binary_entropy(middle) < 0.5:
            low = middle
        else:
            high = middle
    assert 0.5 * (low + high) == pytest.approx(0.11002786443835955, abs=1e-12)
    assert "0.11002786443835955" in entry.derivation


@pytest.mark.oracle
def test_d4s_ceiling_is_below_the_wider_poisson_one() -> None:
    entry = decoy_oracle("O-DECOY-D4-INFINITE-DECOY-CEILING")
    assert entry.value is not None
    declared = float(entry.value)
    wider = 0.5 * math.exp(-0.5) * (
        1 / 64 + (67 / 512) * (1.0 - binary_entropy(1 / 8))
    )
    assert declared < wider
    assert wider == pytest.approx(0.02285221675422397, abs=CLOSED_FORM_TOLERANCE)
    assert "0.02285221675422397" in entry.derivation
