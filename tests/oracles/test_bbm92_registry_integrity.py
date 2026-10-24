"""The BBM92 registry is well formed, admissible, and internally consistent.

The same four things ``test_registry_integrity.py`` pins for the original
freeze, and the same four this instance's sibling
``test_decoy_bb84_registry_integrity.py`` pins for the decoy one.

1. **Admissibility.** No expected value comes from MATLAB, OpenQKDSecurity,
   CVX, MOSEK or Julia; the guard reuses ``registry.INADMISSIBLE_SOURCES``.
2. **Well-formedness.** Unique ids, a kind from
   ``registry_instances_bbm92.BBM92_KINDS``, an instance that exists, a
   derivation long enough to redo on paper, hypotheses that are stated, an
   observable named for the implementer's test, and B-3's equality carrying
   ``recorded_not_asserted``.
3. **Traceability.** Every claim id resolves to a claim file under
   ``spec/modules/``; every batch-C3 re-pin that has since appeared is pinned.
4. **The freeze.** The alpha-dependent table is its own closed form on
   ``ALPHA_GRID``; the Bell weights are exactly the declared error rates; the
   independent-error state really is the maximiser of ``H(phase | bit)``, so
   B-2's ``1 - h2(e)`` is the minimum and not a guess; and the party-local
   separation witness is recomputed in exact rational arithmetic from the
   state and the observable, not transcribed.

**Nothing here runs the engine**: no assertion imports ``certiqs_key``, and
these tests pass before any implementation of a two-station declaration
exists. That is the point of freezing first (``PRINCIPLES.md`` section 2.3).
"""

from __future__ import annotations

import math
from fractions import Fraction
from pathlib import Path

import pytest
from registry import ALPHA_GRID, INADMISSIBLE_SOURCES
from registry_instances_bbm92 import (
    BBM92_IDEAL,
    BBM92_INSTANCES,
    BBM92_KINDS,
    BBM92_ORACLES,
    BBM92_SYMMETRIC_ERROR,
    PARTY_LOCAL_SEPARATION,
    Matrix,
    _freeze,
    bbm92_instance,
    bbm92_oracle,
    bell_diagonal_bits,
    binary_entropy,
    conditional_phase_entropy,
    honest_point_bits,
    independent_error_bits,
)

MODULES = Path(__file__).resolve().parents[2] / "spec" / "modules"

#: Two evaluations of one closed form by the same route differ by the last bits
#: of a handful of ``log2`` calls on quantities of order one.
CLOSED_FORM_TOLERANCE = 1e-12


def _claim_file(claim_id: str) -> Path:
    """Return the claim file ``spec/modules/<module>/claims/<kind>-<name>.tex``."""
    parts = claim_id.split("/")
    stem = parts[-1].replace(":", "-")
    return MODULES.joinpath(*parts[:-1]) / "claims" / f"{stem}.tex"


def _partial_trace_second(state: Matrix) -> Matrix:
    """Return ``tr_{Q_f} X`` for a 4x4 operator with ``Q_f`` the SECOND factor."""
    return tuple(
        tuple(state[2 * i][2 * j] + state[2 * i + 1][2 * j + 1] for j in range(2))
        for i in range(2)
    )


def _weighted_partial_trace(state: Matrix, observable: Matrix) -> Matrix:
    """Return ``tr_{Q_f}[(1 (x) O) X]`` for ``O`` acting on the SECOND factor."""
    out = []
    for i in range(2):
        row = []
        for j in range(2):
            total = Fraction(0)
            for q in range(2):
                for r in range(2):
                    total += observable[r][q] * state[2 * i + q][2 * j + r]
            row.append(total)
        out.append(tuple(row))
    return tuple(out)


def _is_psd_two_by_two(operator: Matrix) -> bool:
    """Exact positivity for a 2x2 Hermitian rational matrix: trace and det."""
    if operator[0][1] != operator[1][0]:
        return False
    determinant = operator[0][0] * operator[1][1] - operator[0][1] * operator[1][0]
    return (
        operator[0][0] >= 0
        and operator[1][1] >= 0
        and determinant >= 0
    )


# ---------------------------------------------------------------------------
#  1. Admissibility, well-formedness, traceability
# ---------------------------------------------------------------------------


@pytest.mark.oracle
def test_no_entry_derives_from_an_inadmissible_source() -> None:
    for entry in BBM92_ORACLES:
        blob = f"{entry.subject} {entry.derivation} {entry.observable}".lower()
        for source in INADMISSIBLE_SOURCES:
            assert source.lower() not in blob, (entry.oracle_id, source)


@pytest.mark.oracle
def test_no_entry_was_produced_by_the_implementation_it_pins() -> None:
    for entry in BBM92_ORACLES:
        assert "certiqs_key" not in entry.derivation, entry.oracle_id


@pytest.mark.oracle
def test_the_ids_are_unique_and_the_entries_are_well_formed() -> None:
    ids = [entry.oracle_id for entry in BBM92_ORACLES]
    assert len(ids) == len(set(ids))
    assert len(ids) == 6, "B-1 to B-6"
    for entry in BBM92_ORACLES:
        assert entry.kind in BBM92_KINDS, entry.oracle_id
        assert entry.claims, entry.oracle_id
        assert len(entry.subject) > 60, entry.oracle_id
        assert len(entry.derivation) > 800, entry.oracle_id
        assert entry.hypotheses, entry.oracle_id
        assert all(len(h) > 30 for h in entry.hypotheses), entry.oracle_id
        assert len(entry.observable) > 60, entry.oracle_id
        assert bbm92_oracle(entry.oracle_id) is entry
        bbm92_instance(entry.instance)


@pytest.mark.oracle
def test_a_relation_entry_carries_a_relation_and_no_other_kind_does() -> None:
    relations = set()
    for entry in BBM92_ORACLES:
        if entry.kind == "relation":
            assert entry.relation is not None, entry.oracle_id
            assert len(entry.relation) > 60, entry.oracle_id
            relations.add(entry.oracle_id)
        else:
            assert entry.relation is None, entry.oracle_id
        if entry.value is not None:
            assert entry.value_closed_form, entry.oracle_id
    assert relations == {
        "O-BBM92-B3-UNTRUSTED-IS-LARGER",
        "O-BBM92-B6-PARTY-LOCAL-GAIN",
    }


@pytest.mark.oracle
def test_only_b3s_equality_is_recorded_rather_than_asserted() -> None:
    """The plan marks B-3's equality 'recorded, not asserted'; nothing else."""
    marked = {
        entry.oracle_id for entry in BBM92_ORACLES if entry.recorded_not_asserted
    }
    assert marked == {"O-BBM92-B3-UNTRUSTED-IS-LARGER"}
    entry = bbm92_oracle("O-BBM92-B3-UNTRUSTED-IS-LARGER")
    assert "RECORDED" in entry.derivation
    assert entry.relation is not None
    assert "<=" in entry.relation


@pytest.mark.oracle
def test_every_hypothesis_set_fixes_the_stations_and_the_normalisation() -> None:
    for entry in BBM92_ORACLES:
        blob = " ".join(entry.hypotheses).lower()
        assert any(
            key in blob
            for key in ("station", "reconciliation", "sifted", "public choice")
        ), entry.oracle_id


@pytest.mark.oracle
def test_every_pinned_claim_resolves_to_a_claim_file() -> None:
    for entry in BBM92_ORACLES:
        for claim_id in entry.claims:
            assert _claim_file(claim_id).is_file(), (entry.oracle_id, claim_id)


@pytest.mark.oracle
def test_the_batch_c3_repins_are_still_open_or_already_pinned() -> None:
    for entry in BBM92_ORACLES:
        for claim_id in entry.repin_after_c3:
            if _claim_file(claim_id).is_file():
                assert claim_id in entry.claims, (
                    f"{claim_id} now exists: re-pin {entry.oracle_id} against it "
                    "deliberately, in its own commit"
                )


@pytest.mark.oracle
def test_the_c3_repin_is_done_and_recorded() -> None:
    """Every entry re-read against accepted C2b/C3 and says what it found."""
    for entry in BBM92_ORACLES:
        assert entry.repin_after_c3 == (), entry.oracle_id
        assert len(entry.revalidation) > 400, entry.oracle_id
        assert "STAND" in entry.revalidation.upper(), entry.oracle_id


@pytest.mark.oracle
def test_the_consumers_side_of_the_party_local_form_is_pinned() -> None:
    """What C3 added and C2a did not have: the consumer of a tagged entry."""
    entry = bbm92_oracle("O-BBM92-B6-PARTY-LOCAL-GAIN")
    for claim_id in (
        "meat-core/def:homog",
        "meat-core/def:declaration",
        "meat-core/def:roundmodel",
        "meat-core/lem:range",
        "reductions/def:licensed",
        "reductions/def:attset",
        "reductions/thm:licence",
        "reductions/lem:party-local",
    ):
        assert _claim_file(claim_id).is_file(), claim_id
        assert claim_id in entry.claims, claim_id


@pytest.mark.oracle
def test_the_two_party_shape_and_the_transcript_are_pinned() -> None:
    """The ids that replaced `thm:tensor-instance` and `def:transcript`."""
    for claim_id, holders in (
        (
            "protocol-compiler/ex:two-party-shape",
            {"O-BBM92-B1-IDEAL-ONE-BIT", "O-BBM92-B4-STATION-EXCHANGE"},
        ),
        ("protocol-compiler/ex:transcript", {"O-BBM92-B5-COIN-MASS"}),
        ("reductions/thm:two-sided", {"O-BBM92-B3-UNTRUSTED-IS-LARGER"}),
    ):
        assert _claim_file(claim_id).is_file(), claim_id
        pinned = {e.oracle_id for e in BBM92_ORACLES if claim_id in e.claims}
        assert pinned == holders, claim_id
    # The guessed ids do not exist, which is why the re-pin was a lookup.
    for absent in (
        "reductions/thm:tensor-instance",
        "reductions/def:licensed-party-local",
        "meat-core/def:homog-party-local",
        "protocol-compiler/def:transcript",
    ):
        assert not _claim_file(absent).is_file(), absent


@pytest.mark.oracle
def test_no_bbm92_entry_pins_the_trusted_mode_rank_one_lemma() -> None:
    """It is stated in trusted mode with default readouts; BBM92 has neither."""
    assert _claim_file("meat-core/lem:rank-one-sector").is_file()
    for entry in BBM92_ORACLES:
        assert "meat-core/lem:rank-one-sector" not in entry.claims, entry.oracle_id


@pytest.mark.oracle
def test_no_entry_asserts_that_a_sector_is_removable() -> None:
    """thm:removal is off with two measured factors or a party-local entry."""
    for entry in BBM92_ORACLES:
        blob = f"{entry.subject} {entry.derivation} {entry.observable}"
        assert "meat-core/thm:removal" not in entry.claims, entry.oracle_id
        assert "removable" not in blob, entry.oracle_id


@pytest.mark.oracle
def test_the_party_local_lemma_is_pinned_where_it_is_used() -> None:
    entry = bbm92_oracle("O-BBM92-B6-PARTY-LOCAL-GAIN")
    assert "reductions/lem:party-local" in entry.claims
    assert PARTY_LOCAL_SEPARATION["claim"] == "reductions/lem:party-local"


# ---------------------------------------------------------------------------
#  2. The frozen table is its own closed form
# ---------------------------------------------------------------------------


@pytest.mark.oracle
def test_every_frozen_table_is_its_closed_form_on_the_alpha_grid() -> None:
    seen = 0
    for entry in BBM92_ORACLES:
        if entry.closed_form is None:
            assert entry.frozen_values == (), entry.oracle_id
            continue
        seen += 1
        assert tuple(a for a, _ in entry.frozen_values) == ALPHA_GRID
        for (alpha, frozen), (_, recomputed) in zip(
            entry.frozen_values, _freeze(entry.closed_form), strict=True
        ):
            assert frozen == recomputed, (entry.oracle_id, alpha)
    assert seen == 1, "only B-2 depends on alpha"


# ---------------------------------------------------------------------------
#  3. The instances' arithmetic, exactly
# ---------------------------------------------------------------------------


@pytest.mark.oracle
def test_the_instances_basis_weights_and_sifted_mass_agree() -> None:
    for instance in BBM92_INSTANCES:
        assert sum(instance.alice_basis_weights) == 1, instance.instance_id
        assert sum(instance.bob_basis_weights) == 1, instance.instance_id
        expected = (
            (1 - instance.test_coin)
            * instance.alice_basis_weights[0]
            * instance.bob_basis_weights[0]
        )
        assert instance.sifted_generation == expected, instance.instance_id
        assert instance.sifted_generation == Fraction(1, 5), instance.instance_id


@pytest.mark.oracle
def test_the_bell_weights_are_the_declared_error_rates() -> None:
    for instance in BBM92_INSTANCES:
        for label, weights in (
            ("honest", instance.honest_lambdas_exact),
            ("minimiser", instance.minimiser_lambdas_exact),
        ):
            assert sum(weights) == 1, (instance.instance_id, label)
            assert weights[2] + weights[3] == instance.error_rate, (
                instance.instance_id,
                label,
                "bit error",
            )
            assert weights[1] + weights[3] == instance.error_rate, (
                instance.instance_id,
                label,
                "phase error",
            )


@pytest.mark.oracle
def test_the_minimiser_is_the_independent_error_state() -> None:
    error = BBM92_SYMMETRIC_ERROR.error_rate
    expected = (
        (1 - error) ** 2,
        error * (1 - error),
        error * (1 - error),
        error**2,
    )
    assert BBM92_SYMMETRIC_ERROR.minimiser_lambdas_exact == expected
    assert BBM92_SYMMETRIC_ERROR.honest_lambdas_exact != expected


# ---------------------------------------------------------------------------
#  4. The targets, recomputed from their own closed forms
# ---------------------------------------------------------------------------


@pytest.mark.oracle
def test_b1s_value_is_the_sifted_generation_probability() -> None:
    entry = bbm92_oracle("O-BBM92-B1-IDEAL-ONE-BIT")
    assert entry.value == BBM92_IDEAL.sifted_generation == Fraction(1, 5)
    # alpha independence: at lambda = (1, 0, 0, 0) the bits are exactly 1 at
    # every order, so O = P_gen * 1 with no alpha left in it.
    for alpha in ALPHA_GRID:
        assert bell_diagonal_bits(BBM92_IDEAL.honest_lambdas, alpha) == 1.0
    # And the foil B-5 exists to catch: a post-hoc coin fraction would give 1/4.
    assert entry.value != Fraction(1, 4)


@pytest.mark.oracle
def test_b2s_limit_is_one_minus_the_binary_entropy_of_the_error() -> None:
    entry = bbm92_oracle("O-BBM92-B2-SYMMETRIC-ERROR")
    error = float(BBM92_SYMMETRIC_ERROR.error_rate)
    limit = 1.0 - binary_entropy(error)
    assert entry.value == pytest.approx(limit, abs=CLOSED_FORM_TOLERANCE)
    # The independence argument: H(phase | bit) = h2(e) EXACTLY at the
    # minimiser, which is what makes 1 - h2(e) the minimum.
    assert conditional_phase_entropy(
        BBM92_SYMMETRIC_ERROR.minimiser_lambdas
    ) == pytest.approx(binary_entropy(error), abs=CLOSED_FORM_TOLERANCE)
    assert independent_error_bits(error, 1.0 + 1e-6) == pytest.approx(
        limit, abs=1e-6
    )


@pytest.mark.oracle
def test_b2s_honest_point_is_strictly_above_the_minimum_at_every_alpha() -> None:
    """Conditioning cannot increase entropy: H(phase|bit) <= h2(e), strictly here."""
    error = float(BBM92_SYMMETRIC_ERROR.error_rate)
    honest = conditional_phase_entropy(BBM92_SYMMETRIC_ERROR.honest_lambdas)
    assert honest < binary_entropy(error)
    assert 1.0 - honest == pytest.approx(0.8533563491773406, abs=CLOSED_FORM_TOLERANCE)
    for alpha in ALPHA_GRID:
        assert honest_point_bits(error, alpha) > independent_error_bits(error, alpha)
    entry = bbm92_oracle("O-BBM92-B2-SYMMETRIC-ERROR")
    assert "0.8533563491773406" in entry.derivation


@pytest.mark.oracle
def test_b2s_leakage_figure_is_positive_at_this_error_rate() -> None:
    """Why e = 1/32 and not 1/8: at 1/8 the textbook 1 - 2 h2(e) is negative."""
    assert 1.0 - 2.0 * binary_entropy(1 / 32) == pytest.approx(
        0.5987553513745707, abs=CLOSED_FORM_TOLERANCE
    )
    assert 1.0 - 2.0 * binary_entropy(1 / 8) < 0.0
    entry = bbm92_oracle("O-BBM92-B2-SYMMETRIC-ERROR")
    assert "0.5987553513745707" in entry.derivation


@pytest.mark.oracle
def test_b2s_bits_decrease_in_alpha() -> None:
    error = float(BBM92_SYMMETRIC_ERROR.error_rate)
    values = [independent_error_bits(error, alpha) for alpha in ALPHA_GRID]
    assert values == sorted(values, reverse=True)
    assert max(values) < 1.0 - binary_entropy(error)


@pytest.mark.oracle
def test_b4s_value_is_an_exact_zero_difference() -> None:
    entry = bbm92_oracle("O-BBM92-B4-STATION-EXCHANGE")
    assert entry.value == 0
    assert entry.kind == "structural-identity"
    # The entry must demand a foil, or the test it describes is vacuous.
    assert "DIFFER" in entry.observable or "differ" in entry.observable


@pytest.mark.oracle
def test_b5s_mass_is_one_minus_the_coin_bias() -> None:
    entry = bbm92_oracle("O-BBM92-B5-COIN-MASS")
    assert entry.value == 1 - BBM92_IDEAL.test_coin == Fraction(4, 5)
    # The split is state dependent and the sum is not: at the honest point the
    # sifted letter carries 1/5 and the unsifted one the remaining 3/5.
    assert BBM92_IDEAL.sifted_generation == Fraction(1, 5)
    assert entry.value - BBM92_IDEAL.sifted_generation == Fraction(3, 5)


@pytest.mark.oracle
def test_b6s_separation_witness_is_exact_and_separates() -> None:
    state = PARTY_LOCAL_SEPARATION["omega"]
    observable = PARTY_LOCAL_SEPARATION["observable"]
    constant = PARTY_LOCAL_SEPARATION["constant"]
    assert isinstance(state, tuple)
    assert isinstance(observable, tuple)
    assert isinstance(constant, Fraction)
    # A state: trace one, and positive (it is diagonal with entries 1/2, 1/2).
    assert sum(state[i][i] for i in range(4)) == 1
    # THE SCALAR ENTRY HOLDS, with equality, which is the sharpest case.
    scalar = sum(
        observable[r][q] * state[2 * i + q][2 * i + r]
        for i in range(2)
        for q in range(2)
        for r in range(2)
    )
    assert scalar == PARTY_LOCAL_SEPARATION["scalar_entry_value"] == Fraction(1, 2)
    assert scalar >= constant * 1
    assert PARTY_LOCAL_SEPARATION["scalar_entry_holds"] is True
    # THE PARTY-LOCAL ENTRY FAILS: tr_{Q_f}[(1 (x) D) omega] is not PSD.
    deficit = tuple(
        tuple(
            observable[r][q] - (constant if q == r else Fraction(0))
            for r in range(2)
        )
        for q in range(2)
    )
    computed = _weighted_partial_trace(state, deficit)
    assert computed == PARTY_LOCAL_SEPARATION["party_local_operator"]
    assert not _is_psd_two_by_two(computed)
    assert PARTY_LOCAL_SEPARATION["party_local_holds"] is False
    # The marginal is the identity/2, so the state is a legitimate two-qubit one.
    assert _partial_trace_second(state) == ((Fraction(1, 2), 0), (0, Fraction(1, 2)))


@pytest.mark.oracle
def test_b6s_relation_points_the_right_way() -> None:
    """A tighter constraint set gives a LARGER lower bound, not a smaller one."""
    entry = bbm92_oracle("O-BBM92-B6-PARTY-LOCAL-GAIN")
    assert entry.relation is not None
    assert ">=" in entry.relation
    assert entry.value is None, "the SIZE of the gain is a record, never an oracle"


@pytest.mark.oracle
def test_b3s_recorded_coincidence_is_b2s_number() -> None:
    """The one point where the two programs are known to agree, at alpha -> 1+."""
    b3 = bbm92_oracle("O-BBM92-B3-UNTRUSTED-IS-LARGER")
    b2 = bbm92_oracle("O-BBM92-B2-SYMMETRIC-ERROR")
    assert b3.value == b2.value
    assert b3.value == pytest.approx(
        1.0 - binary_entropy(float(BBM92_SYMMETRIC_ERROR.error_rate)),
        abs=CLOSED_FORM_TOLERANCE,
    )
    assert math.isfinite(float(b3.value))
