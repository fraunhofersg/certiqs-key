"""Section 2.2 and Eq. ``eq:weightroute``, replayed against the FROZEN registry.

The four ``WeightRouteCase`` entries and the descent counterexample are rebuilt
FROM THE RAW DECLARED DATA -- the per-port dark-count probabilities or the
declared column-stochastic matrix, and the coarse-graining -- rather than from
the frozen ``R^cg``. That is the stronger check: the frozen descended matrix is
then an OUTPUT of the implementation and not an input to it, and Section 4.14's
"tested directly, not via the shortcut Eq. ``eq:canonicalcg``" is exercised on
the very declarations the shortcut would mis-handle.
"""

from __future__ import annotations

from fractions import Fraction

import pytest
from registry_reductions import (
    DESCENT_COUNTEREXAMPLE,
    RC1MIN,
    RC2,
    RC3,
    RCABS,
    WEIGHT_ROUTE_CASES,
)

from certiqs_key.reductions.inputs import (
    ClickPattern,
    CoarseGraining,
    DarkCountChannel,
    HighPhotonBound,
    ProbeDeclaration,
    canonical_coarse_graining,
    patterns,
    product_form_dark_counts,
)
from certiqs_key.reductions.reasons import RefusalReason
from certiqs_key.reductions.validation import (
    rule_probe_weights,
)
from certiqs_key.reductions.wpfss.validation import (
    rule_absorbing,
    rule_descent,
    rule_fibre,
    rule_total_weight,
)
from certiqs_key.reductions.wpfss.weights import (
    bounded_letters,
    descend,
    is_monotone,
    minimum_off_letter_rate,
    weight_route,
)

F = Fraction

#: THE FIXTURE LATTICE EXPONENTS, and neither is a platform value: the contract
#: "fixes no value". Two are used so that no assertion below can hold at one
#: exponent only -- the relation p = lat(p^) <= p^ is the claim, not a number.
KAPPA: int = 12
KAPPA_COARSE: int = 6


def _rc2_declaration() -> tuple[DarkCountChannel, CoarseGraining]:
    """RC2: ``K = 2``, the canonical ``cg``, product dark counts 1/5 and 1/4."""
    channel = product_form_dark_counts(2, {1: F(1, 5), 2: F(1, 4)})
    coarse = canonical_coarse_graining(
        2,
        empty_letter="y_empty",
        single_letters={1: "y_1", 2: "y_2"},
        multiclick_letter="y_mc",
    )
    return channel, coarse


def _rcabs_declaration() -> tuple[DarkCountChannel, CoarseGraining]:
    """RCABS: the sub-case Remark ``rem:absorbneeded`` names, ``p_dc|1 = 0``."""
    channel = product_form_dark_counts(2, {1: F(0), 2: F(1, 4)})
    coarse = canonical_coarse_graining(
        2,
        empty_letter="y_empty",
        single_letters={1: "y_1", 2: "y_2"},
        multiclick_letter="y_mc",
    )
    return channel, coarse


def _rc1min_declaration() -> tuple[DarkCountChannel, CoarseGraining]:
    """RC1MIN: the same channel with a ``cg`` CONSTANT on all of ``2^[K]``."""
    channel = product_form_dark_counts(2, {1: F(1, 5), 2: F(1, 4)})
    coarse = CoarseGraining(
        ports=2,
        letters=("y_1",),
        assignment=dict.fromkeys(patterns(2), "y_1"),
    )
    return channel, coarse


def _rc3_declaration() -> tuple[DarkCountChannel, CoarseGraining]:
    """RC3: ``K = 3``, a DECLARED monotone matrix acting on the empty pattern."""
    empty: ClickPattern = frozenset()
    entries: dict[tuple[ClickPattern, ClickPattern], Fraction] = {
        (empty, empty): F(1, 2),
        (frozenset({1}), empty): F(1, 4),
        (frozenset({1, 2}), empty): F(1, 4),
    }
    for pattern in patterns(3):
        if pattern == empty:
            continue
        entries[(pattern, pattern)] = F(1)
    channel = DarkCountChannel(ports=3, entries=entries)
    assignment: dict[ClickPattern, str] = {}
    for pattern in patterns(3):
        if len(pattern) == 0:
            assignment[pattern] = "y_0"
        elif len(pattern) == 1:
            assignment[pattern] = "y_s"
        else:
            assignment[pattern] = "y_mc"
    coarse = CoarseGraining(
        ports=3, letters=("y_0", "y_s", "y_mc"), assignment=assignment
    )
    return channel, coarse


DECLARATIONS = {
    "RC2": _rc2_declaration,
    "RC1MIN": _rc1min_declaration,
    "RC3": _rc3_declaration,
    "RCABS": _rcabs_declaration,
}


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("case", WEIGHT_ROUTE_CASES, ids=lambda case: str(case.case_id))
def test_the_descended_matrix_is_reproduced_from_the_raw_declaration(
    case: object,
) -> None:
    """Lemma ``lem:descent``, TESTED DIRECTLY on the declared ``R`` and ``cg``."""
    channel, coarse = DECLARATIONS[case.case_id]()  # type: ignore[attr-defined]
    assert is_monotone(channel)
    descended = descend(channel, coarse)
    assert descended is not None
    assert descended.letters == case.letters  # type: ignore[attr-defined]
    for column, rows in case.descended_matrix:  # type: ignore[attr-defined]
        for row, value in rows:
            assert descended.value(row, column) == value, (column, row)
    assert descended.is_column_stochastic()
    assert rule_descent(channel, coarse) is None


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("case", WEIGHT_ROUTE_CASES, ids=lambda case: str(case.case_id))
def test_the_bounded_letters_absorbing_flags_and_r_min(case: object) -> None:
    """Eq. ``eq:absorbing`` and ``r_min,i``, read off the recomputed ``R^cg``.

    ``r_min`` is INDEXED BY THE BOUNDED LETTER -- "a property of row ``y_i`` of
    ``R^cg`` read across the columns ``y' != y_i``, and one entry's value is not
    another's" (Section 2.2, fact (a)).
    """
    channel, coarse = DECLARATIONS[case.case_id]()  # type: ignore[attr-defined]
    descended = descend(channel, coarse)
    assert descended is not None
    settings = tuple(setting for setting, _ in case.probe_weights)  # type: ignore[attr-defined]
    bounds = tuple(
        HighPhotonBound.uniform(coarse.fibre(letter), weight, settings)
        for letter, weight in case.slot_weights  # type: ignore[attr-defined]
    )
    assert rule_fibre(bounds, coarse) is None
    letters = bounded_letters(bounds, coarse, descended)
    assert letters is not None
    frozen = {
        letter: (absorbing, r_min)
        for letter, absorbing, r_min in case.bounded_letters  # type: ignore[attr-defined]
    }
    assert {letter.letter for letter in letters} == set(frozen)
    for letter in letters:
        expected_absorbing, expected_r_min = frozen[letter.letter]
        assert letter.absorbing is expected_absorbing
        assert letter.r_min == expected_r_min
        assert minimum_off_letter_rate(descended, letter.letter) == expected_r_min


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("case", WEIGHT_ROUTE_CASES, ids=lambda case: str(case.case_id))
def test_eq_weightroute_reproduces_every_frozen_emitted_weight(
    case: object,
) -> None:
    """Eq. ``eq:weightroute``, and the refusal where a letter is not absorbing."""
    channel, coarse = DECLARATIONS[case.case_id]()  # type: ignore[attr-defined]
    descended = descend(channel, coarse)
    assert descended is not None
    settings = tuple(setting for setting, _ in case.probe_weights)  # type: ignore[attr-defined]
    bounds = tuple(
        HighPhotonBound.uniform(coarse.fibre(letter), weight, settings)
        for letter, weight in case.slot_weights  # type: ignore[attr-defined]
    )
    letters = bounded_letters(bounds, coarse, descended)
    assert letters is not None
    probe = ProbeDeclaration(
        settings=tuple(setting for setting, _ in case.probe_weights),  # type: ignore[attr-defined]
        weights=dict(case.probe_weights),  # type: ignore[attr-defined]
    )
    # NEW AT 1.0.0: the probe row decides Eq. eq:latinv on every declared q_t.
    # TWO OF THE FROZEN BAND-1 CASES DECLARE q_t IN {2/3, 1/3}, which is on no
    # dyadic lattice, so 1.0.0 REFUSES them -- correctly, and this asserts the
    # refusal rather than xfailing the case. def:exactadm (b) names the q_t
    # among the declared real scalars the invariant is about, and it is the one
    # of them that is EMITTED: cor:entries (ii)'s probe-expectation entry
    # carries c = q_t, so an off-lattice q_t would put an off-lattice constant
    # in the emitted list.
    on_the_lattice = all(
        (weight * 2**KAPPA).denominator == 1 for weight in probe.weights.values()
    )
    refusal = rule_probe_weights(probe, lattice_exponent=KAPPA)
    if not on_the_lattice:
        assert refusal is not None, case.case_id  # type: ignore[attr-defined]
        assert refusal.reason is RefusalReason.PROBE_WEIGHTS_ILL_FORMED
        assert "eq:latinv" in refusal.detail or "ROUNDS" in refusal.detail
        # THE ROW REFUSES THESE WEIGHTS WITH OR WITHOUT A DECLARED LATTICE, and
        # the second refusal is the SHARPER of the two: 2/3 is not a binary64
        # number AT ALL, so def:exactadm (e)'s condition on the ADDITIONS fails
        # before Eq. eq:latinv is even reached. def:exactadm (a): "every
        # numerical datum this module reads, forms or emits IS an IEEE-754
        # binary64 value", so 2/3 is not a declarable datum on any lattice.
        assert rule_probe_weights(probe) is not None, case.case_id  # type: ignore[attr-defined]
        return
    assert refusal is None
    joint = tuple(
        (letter, setting) for setting in probe.settings for letter in coarse.letters
    )
    # KAPPA IS A FIXTURE CHOICE AND EVERY ASSERTION BELOW IS INDEPENDENT OF
    # IT: what is asserted is the RELATION between p^ and lat(p^), not a value
    # at one exponent, and the two exponents are run so that no assertion can
    # be true only at one.
    weights = weight_route(letters, probe, joint, lattice_exponent=KAPPA)
    coarser = weight_route(letters, probe, joint, lattice_exponent=KAPPA_COARSE)
    if case.refusal_reason is not None:  # type: ignore[attr-defined]
        assert weights is None
        assert coarser is None
        refusal = rule_absorbing(letters)
        assert refusal is not None
        assert str(refusal.reason) == case.refusal_reason  # type: ignore[attr-defined]
        assert case.emitted_weights == ()  # type: ignore[attr-defined]
        return
    assert weights is not None
    assert coarser is not None
    assert rule_absorbing(letters) is None
    # WHAT BAND 1 FROZE IS p^, NOT p, AND 1.0.0 IS WHERE THE TWO SEPARATE.
    # Eq. eq:weightroute now reads p^ = q_t((1 - r_min) p_i + r_min) followed
    # by p = lat(p^) of Eq. eq:latdown, and "THE EMITTED WEIGHT IS p AND NOT
    # p^". Band 1's frozen `emitted_weights` are the 0.3.0 emitted values,
    # which are 1.0.0's PRE-ROUNDING ones -- the amendment renamed the
    # quantity it froze. THE FROZEN NUMBERS ARE NOT EDITED (the two-instance
    # freeze) AND ARE NOT ASSERTED TO BE THE EMITTED ONES EITHER: they are
    # asserted to be p^, and the emitted p is asserted against the contract's
    # rounding rule. SCOPE_MARKS_1_0_0 does not mark this group.
    hat = dict(case.emitted_weights)  # type: ignore[attr-defined]
    for outcome, value in weights.items():
        expected_hat = hat.get(outcome, F(0))
        step = F(1, 2**KAPPA)
        assert value == (expected_hat // step) * step, outcome
        # lat ONLY LOWERS, which is the whole of what makes it safe: "
        # eq:certweights IS PRESERVED WHEN A CERTIFIED WEIGHT IS LOWERED AND
        # DESTROYED WHEN ONE IS RAISED, and lat(.) ONLY LOWERS".
        assert value <= expected_hat, outcome
        assert expected_hat - value < step, outcome
        # AND IT IS NON-NEGATIVE WITHOUT A CLAMP: "the largest lattice number
        # at most a non-negative rational is itself non-negative".
        assert value >= 0, outcome
        # A COARSER LATTICE NEVER EMITS MORE.
        assert coarser[outcome] <= value, outcome
    # p_(y,t) = 0 for EVERY OTHER (y, t): a zero p^ rounds to a zero p, so the
    # support can only SHRINK, and at these fixtures it does not move.
    assert {outcome for outcome, value in weights.items() if value != 0} <= set(hat)
    # AND THE TOTAL IS AT MOST THE FROZEN ONE, strictly below it wherever any
    # p^ is off the lattice -- which at every fixture here it is, none of the
    # frozen values being dyadic.
    total = sum(weights.values(), start=F(0))
    assert total <= case.total_weight  # type: ignore[attr-defined]
    assert total < 1
    assert rule_total_weight(list(weights.values())) is None


@pytest.mark.contract
@pytest.mark.oracle
def test_the_empty_minimum_convention_is_the_conservative_value() -> None:
    """RC1MIN: ``r_min := 0`` when ``Y = {y_i}``, the un-improved bound."""
    channel, coarse = _rc1min_declaration()
    descended = descend(channel, coarse)
    assert descended is not None
    assert descended.letters == ("y_1",)
    assert descended.value("y_1", "y_1") == 1
    assert minimum_off_letter_rate(descended, "y_1") == 0
    slot = dict(RC1MIN.slot_weights)["y_1"]
    for setting, q_t in RC1MIN.probe_weights:
        assert dict(RC1MIN.emitted_weights)[("y_1", setting)] == q_t * slot


@pytest.mark.contract
@pytest.mark.oracle
def test_cor_oneabsorbing_forces_every_r_min_to_vanish_at_two_letters() -> None:
    """Corollary ``cor:oneabsorbing``: at ``r >= 2`` no weight is sharpened."""
    channel, coarse = _rc3_declaration()
    descended = descend(channel, coarse)
    assert descended is not None
    assert len(RC3.bounded_letters) >= 2
    for letter, absorbing, r_min in RC3.bounded_letters:
        assert absorbing is True
        assert minimum_off_letter_rate(descended, letter) == r_min == 0
    # RC2 is the ONLY frozen case with a positive r_min, and it has r = 1.
    improved = [
        case
        for case in WEIGHT_ROUTE_CASES
        if any(r_min > 0 for _, _, r_min in case.bounded_letters)
    ]
    assert [case.case_id for case in improved] == ["RC2"]
    assert len(RC2.bounded_letters) == 1


@pytest.mark.contract
@pytest.mark.oracle
def test_the_dark_counts_sharpen_the_weight_by_the_frozen_amount() -> None:
    """RC2: ``29/200 > 1/10``, and the improvement comes from ``R^cg`` alone."""
    channel, coarse = _rc2_declaration()
    descended = descend(channel, coarse)
    assert descended is not None
    r_min = minimum_off_letter_rate(descended, "y_mc")
    slot = dict(RC2.slot_weights)["y_mc"]
    improved = (1 - r_min) * slot + r_min
    assert improved == RC2.total_weight == F(29, 200)
    assert improved > slot


@pytest.mark.contract
@pytest.mark.oracle
def test_the_descent_counterexample_really_fails_to_descend() -> None:
    r"""Remark ``rem:descentneedsconstant``, rebuilt at ``K = 4``, ``p = 1/3``.

    ``cg`` is injective on ``2^[K] \\ MC`` and ``cg^{-1}({y_a, y_b}) = MC``, so
    TWO of Eq. ``eq:canonicalcg``'s three clauses hold; the CONSTANCY clause
    fails, and that is enough to break descent. An implementation testing the
    shortcut would ACCEPT this declaration.
    """
    probability = DESCENT_COUNTEREXAMPLE["dark_count_probability"]
    channel = product_form_dark_counts(4, dict.fromkeys((1, 2, 3, 4), probability))
    assert is_monotone(channel)
    fibre_of_y_a = {
        frozenset({1, 2}),
        frozenset({1, 2, 4}),
        frozenset({1, 2, 3, 4}),
    }
    assignment: dict[ClickPattern, str] = {}
    letters: list[str] = []
    for pattern in patterns(4):
        if len(pattern) >= 2:
            letter = "y_a" if pattern in fibre_of_y_a else "y_b"
        else:
            letter = "y_" + "".join(str(port) for port in sorted(pattern))
        assignment[pattern] = letter
        if letter not in letters:
            letters.append(letter)
    coarse = CoarseGraining(ports=4, letters=tuple(letters), assignment=assignment)

    # The two columns with the same cg-image and different values.
    def probability_of_y_a(source: ClickPattern) -> Fraction:
        return sum(
            (channel.value(target, source) for target in fibre_of_y_a),
            start=F(0),
        )

    assert (
        probability_of_y_a(frozenset({1, 2}))
        == (DESCENT_COUNTEREXAMPLE["p_ya_given_12"])
    )
    assert (
        probability_of_y_a(frozenset({1, 2, 4}))
        == (DESCENT_COUNTEREXAMPLE["p_ya_given_124"])
    )
    assert descend(channel, coarse) is None
    refusal = rule_descent(channel, coarse)
    assert refusal is not None
    assert refusal.reason is RefusalReason.DARK_COUNTS_DO_NOT_DESCEND
    assert str(refusal.reason) == DESCENT_COUNTEREXAMPLE["refusal_reason"]


@pytest.mark.contract
@pytest.mark.oracle
def test_the_rcabs_refusal_is_in_the_unsafe_direction() -> None:
    """Remark ``rem:absorbneeded``, with the numbers the registry freezes.

    The formula WOULD assert ``q_t (1/5)`` while the truth is ``q_t (3/20)``, a
    gap of ``q_t/20`` in the direction that certifies a weight the device does
    not have. Version 1 takes Eq. ``eq:absorbing`` as a declared input validity
    condition and REFUSES; it states no bound for that case.
    """
    channel, coarse = _rcabs_declaration()
    descended = descend(channel, coarse)
    assert descended is not None
    assert descended.value("y_1", "y_1") == F(3, 4)
    assert not descended.is_absorbing_at("y_1")
    assert minimum_off_letter_rate(descended, "y_1") == 0
    slot = dict(RCABS.slot_weights)["y_1"]
    would_assert = (1 - F(0)) * slot + F(0)
    truth = descended.value("y_1", "y_1") * slot
    assert would_assert == F(1, 5)
    assert truth == F(3, 20)
    assert would_assert > truth
    bounds = (HighPhotonBound.uniform(coarse.fibre("y_1"), slot, ("t",)),)
    letters = bounded_letters(bounds, coarse, descended)
    assert letters is not None
    refusal = rule_absorbing(letters)
    assert refusal is not None
    assert refusal.reason is RefusalReason.BOUNDED_LETTER_NOT_ABSORBING

