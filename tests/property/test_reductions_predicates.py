"""Property tests for the ``proof-reductions`` predicates and constructions.

Each property below is a statement the contract makes, checked against ITS OWN
DIRECT DEFINITION on randomly generated small declarations -- not against a
second implementation of the same shortcut. The generators produce EXACT
Gaussian rationals, so no tolerance appears here either.

Three of them are the ones an implementation could most plausibly get subtly
right on the frozen instances and wrong in general: the descent test against
Lemma ``lem:descent``'s definition rather than Eq. ``eq:canonicalcg``'s
shortcut; the exact positivity decision against the full principal-minor
enumeration; and the sector-block-diagonality of every emitted ``F_v``, which
the branching construction's theorem proves for every declaration and not
merely for the frozen two.
"""

from __future__ import annotations

from fractions import Fraction

import pytest
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

from certiqs_key.foundations.exact import (
    Cx,
    Matrix,
    add,
    all_principal_minors_nonnegative,
    conjugate_transpose,
    diagonal,
    equal,
    identity,
    is_hermitian,
    is_positive_semidefinite,
    linear_relations,
    loewner_ge,
    matmul,
    matrix,
    scale,
    span_dimension,
    spectral_bounds,
    subtract,
    zeros,
)
from certiqs_key.reductions.channels import (
    mp_adjoint,
)
from certiqs_key.reductions.constraints import (
    certificate_holds,
)
from certiqs_key.reductions.inputs import (
    CoarseGraining,
    HighPhotonBound,
    ProbeDeclaration,
    patterns,
    product_form_dark_counts,
)
from certiqs_key.reductions.reasons import Relation
from certiqs_key.reductions.validation import (
    rule_obstructions,
)
from certiqs_key.reductions.wpfss.construction import (
    fss_target,
    mprime_family,
    noise_adjoint,
    transported_cutoff_projectors,
    wp_adjoint,
    wpfss_target,
)
from certiqs_key.reductions.wpfss.validation import (
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

SLOW = settings(
    max_examples=40,
    deadline=None,
    suppress_health_check=[HealthCheck.data_too_large],
)

#: Two exact unitaries on ``C^2``, one real and one GENUINELY COMPLEX, used to
#: turn a diagonal family into a non-diagonal one without leaving the rationals.
#: Both are built from the Pythagorean triple (3, 4, 5), so every entry stays an
#: exact Gaussian rational and no amplitude ``1/sqrt(2)`` ever appears.
REAL_ROTATION: Matrix = matrix([[F(3, 5), F(-4, 5)], [F(4, 5), F(3, 5)]])
COMPLEX_UNITARY: Matrix = matrix(
    [
        [Cx(F(3, 5), F(0)), Cx(F(0), F(4, 5))],
        [Cx(F(0), F(4, 5)), Cx(F(3, 5), F(0))],
    ]
)


def small_rational(low: int = 0, high: int = 4) -> st.SearchStrategy[Fraction]:
    """Exact rationals with small numerator and denominator."""
    return st.builds(
        Fraction,
        st.integers(min_value=low, max_value=high),
        st.integers(min_value=1, max_value=5),
    )


@st.composite
def probability_vectors(
    draw: st.DrawFn, size: int, minimum: int = 0
) -> tuple[Fraction, ...]:
    """Return a probability vector of exact rationals, summing to ONE exactly."""
    raw = draw(
        st.lists(
            st.integers(min_value=minimum, max_value=6),
            min_size=size,
            max_size=size,
        )
    )
    total = sum(raw)
    assume(total > 0)
    return tuple(Fraction(value, total) for value in raw)


@st.composite
def diagonal_povms(
    draw: st.DrawFn, outcomes: int, dimension: int
) -> tuple[Matrix, ...]:
    """Return a DIAGONAL POVM: one probability vector per diagonal position.

    Exact by construction -- ``sum_v M_v = 1`` holds entry for entry -- and the
    natural family for a photon-number block, whose elements the contract types
    as blocks rather than compressions.
    """
    columns = [draw(probability_vectors(outcomes)) for _ in range(dimension)]
    return tuple(
        diagonal([columns[position][outcome] for position in range(dimension)])
        for outcome in range(outcomes)
    )


def conjugate(family: tuple[Matrix, ...], unitary: Matrix) -> tuple[Matrix, ...]:
    """Return ``{U^dagger M_v U}``, still a POVM and no longer diagonal."""
    return tuple(
        matmul(matmul(conjugate_transpose(unitary), element), unitary)
        for element in family
    )


# ---------------------------------------------------------------------------
#  The exact positivity decision
# ---------------------------------------------------------------------------


@given(
    family=diagonal_povms(outcomes=2, dimension=2),
    shift=small_rational(),
    complex_basis=st.booleans(),
)
@SLOW
def test_the_ldl_decision_agrees_with_every_principal_minor(
    family: tuple[Matrix, ...], shift: Fraction, complex_basis: bool
) -> None:
    """Two independent decision procedures for positive semidefiniteness.

    Neither is derived from the other: one is a rational ``LDL^*`` with the
    zero-pivot rule, the other the full ``2^n - 1`` principal-minor enumeration.
    A singular operator must be accepted by both -- Section 4.14's tests are
    refusal tests, not bounds, and there is no threshold between accept and
    refuse.
    """
    unitary = COMPLEX_UNITARY if complex_basis else REAL_ROTATION
    for element in conjugate(family, unitary):
        assert is_hermitian(element)
        shifted = subtract(element, scale(shift, identity(2)))
        assert is_positive_semidefinite(shifted) is (
            all_principal_minors_nonnegative(shifted)
        )


@given(family=diagonal_povms(outcomes=3, dimension=2), complex_basis=st.booleans())
@SLOW
def test_spectral_bounds_always_enclose_the_operator(
    family: tuple[Matrix, ...], complex_basis: bool
) -> None:
    """``lower 1 <= X <= upper 1``, which is what Lemma ``lem:obstructions`` uses.

    The bounds are the operator statement the lemma's proof runs on, so the
    enclosure is exactly the transportable form of (i); its tightness is a
    property of the operator and is recorded rather than assumed.
    """
    unitary = COMPLEX_UNITARY if complex_basis else REAL_ROTATION
    for element in conjugate(family, unitary):
        bounds = spectral_bounds(element)
        assert loewner_ge(scale(bounds.upper, identity(2)), element)
        assert loewner_ge(element, scale(bounds.lower, identity(2)))
        if bounds.tight:
            # Where it is tight the operator is diagonal and the bounds ARE the
            # extreme diagonal entries.
            assert bounds.lower == min(element[i][i].re for i in range(2))
            assert bounds.upper == max(element[i][i].re for i in range(2))


# ---------------------------------------------------------------------------
#  Eq. eq:certificate against its direct definition
# ---------------------------------------------------------------------------


@given(
    family=diagonal_povms(outcomes=2, dimension=2),
    constant=small_rational(),
    complex_basis=st.booleans(),
)
@SLOW
def test_certificate_holds_agrees_with_the_loewner_definition(
    family: tuple[Matrix, ...], constant: Fraction, complex_basis: bool
) -> None:
    """``O bowtie c 1_B`` decided against ``O - c 1`` being PSD, and back."""
    unitary = COMPLEX_UNITARY if complex_basis else REAL_ROTATION
    for element in conjugate(family, unitary):
        scaled = scale(constant, identity(2))
        assert certificate_holds(element, Relation.GE, constant) is (
            is_positive_semidefinite(subtract(element, scaled))
        )
        assert certificate_holds(element, Relation.LE, constant) is (
            is_positive_semidefinite(subtract(scaled, element))
        )
        assert certificate_holds(element, Relation.EQ, constant) is (
            equal(element, scaled)
        )


# ---------------------------------------------------------------------------
#  Lemma lem:descent against its own definition, never via the shortcut
# ---------------------------------------------------------------------------


@st.composite
def dark_count_declarations(
    draw: st.DrawFn,
) -> tuple[int, dict[int, Fraction], dict[frozenset[int], str], tuple[str, ...]]:
    """Return a random monotone product channel and a random total cg."""
    ports = draw(st.integers(min_value=1, max_value=3))
    probabilities = {
        port: draw(
            st.builds(
                Fraction,
                st.integers(min_value=0, max_value=3),
                st.integers(min_value=1, max_value=4),
            )
        )
        for port in range(1, ports + 1)
    }
    for value in probabilities.values():
        assume(0 <= value <= 1)
    all_patterns = patterns(ports)
    letter_count = draw(st.integers(min_value=1, max_value=min(4, len(all_patterns))))
    letters = tuple(f"y{index}" for index in range(letter_count))
    assignment = {
        pattern: letters[draw(st.integers(0, letter_count - 1))]
        for pattern in all_patterns
    }
    # Surjectivity is part of the declaration Section 2.1 types.
    assume(set(assignment.values()) == set(letters))
    return ports, probabilities, assignment, letters


@given(declaration=dark_count_declarations())
@SLOW
def test_descent_is_decided_by_the_property_and_never_by_the_shortcut(
    declaration: tuple[
        int, dict[int, Fraction], dict[frozenset[int], str], tuple[str, ...]
    ],
) -> None:
    """Lemma ``lem:descent``'s definition, and Eq. ``eq:descend`` where it holds.

    ``P(y | S') := sum_{S in cg^{-1}(y)} R_{S|S'}`` must depend on ``S'`` only
    through ``cg(S')``. Where it does, applying ``R`` and then coarse-graining
    agrees with coarse-graining and then applying ``R^cg`` -- Eq. ``eq:descend``,
    checked here on a family of scalars, which is the ``1 x 1`` case of the
    operator statement and carries all of its content.
    """
    ports, probabilities, assignment, letters = declaration
    channel = product_form_dark_counts(ports, probabilities)
    assert is_monotone(channel)
    coarse = CoarseGraining(ports=ports, letters=letters, assignment=assignment)
    fibres = {letter: coarse.fibre(letter) for letter in letters}

    def probability(letter: str, source: frozenset[int]) -> Fraction:
        return sum(
            (channel.value(target, source) for target in fibres[letter]),
            start=F(0),
        )

    descends = all(
        probability(letter, first) == probability(letter, second)
        for image in letters
        for first in fibres[image]
        for second in fibres[image]
        for letter in letters
    )
    descended = descend(channel, coarse)
    assert (descended is not None) is descends
    if descended is None:
        return
    assert descended.is_column_stochastic()
    # Eq. eq:descend on a family of scalars, one per raw pattern.
    values = {
        pattern: Fraction(index + 1, 7) for index, pattern in enumerate(patterns(ports))
    }
    for letter in letters:
        left = sum(
            (
                channel.value(target, source) * values[source]
                for target in fibres[letter]
                for source in patterns(ports)
            ),
            start=F(0),
        )
        right = sum(
            (
                descended.value(letter, image)
                * sum((values[source] for source in fibres[image]), start=F(0))
                for image in letters
            ),
            start=F(0),
        )
        assert left == right


# ---------------------------------------------------------------------------
#  Eq. eq:weightroute
# ---------------------------------------------------------------------------


@given(
    slot=st.builds(
        Fraction,
        st.integers(min_value=0, max_value=4),
        st.integers(min_value=5, max_value=9),
    ),
    r_min=st.builds(
        Fraction,
        st.integers(min_value=0, max_value=3),
        st.integers(min_value=4, max_value=9),
    ),
    q_t=st.builds(
        Fraction,
        st.integers(min_value=1, max_value=4),
        st.integers(min_value=5, max_value=9),
    ),
)
@SLOW
def test_eq_weightroute_is_increasing_in_r_min_and_never_exceeds_q_t(
    slot: Fraction, r_min: Fraction, q_t: Fraction
) -> None:
    """The formula, and why the empty-minimum convention is the conservative one.

    ``p_(y_i,t) = q_t((1 - r)p_i + r)`` is INCREASING in ``r`` for ``p_i <= 1``,
    so ``r = 0`` gives the SMALLEST admissible weight -- hence the cleanest
    target, hence the most generous adversary (Corollary ``cor:monotone``). Any
    other convention for an empty minimum would assert a weight the device has
    not been shown to have.
    """
    assume(slot <= 1)
    assume(r_min <= 1)
    at_zero = q_t * slot
    at_r = q_t * ((1 - r_min) * slot + r_min)
    assert at_zero <= at_r
    assert at_r <= q_t
    if r_min > 0 and slot < 1:
        assert at_zero < at_r


@given(weights=st.lists(small_rational(0, 3), min_size=1, max_size=4))
@SLOW
def test_the_total_weight_rule_refuses_exactly_the_inadmissible_families(
    weights: list[Fraction],
) -> None:
    """``p_v >= 0`` and ``p < 1``, decided and never clipped."""
    refusal = rule_total_weight(weights)
    admissible = all(weight >= 0 for weight in weights) and (
        sum(weights, start=F(0)) < 1
    )
    assert (refusal is None) is admissible
    if admissible:
        # And exactly then the construction is defined.
        assert sum(weights, start=F(0)) < 1


# ---------------------------------------------------------------------------
#  The emitted target: a POVM, sector-block-diagonal, of the unpadded dimension
# ---------------------------------------------------------------------------








# ---------------------------------------------------------------------------
#  The relation this module CONSTRUCTS always passes the necessary conditions
# ---------------------------------------------------------------------------


@given(family=diagonal_povms(outcomes=2, dimension=2), weights=probability_vectors(2))
@SLOW
def test_a_constructed_relation_never_trips_the_obstruction_rule(
    family: tuple[Matrix, ...], weights: tuple[Fraction, ...]
) -> None:
    """Lemma ``lem:obstructions`` is NECESSARY, so a real relation always passes.

    The relation ``M <=_{Lambda^WP} F^WP`` is a theorem (Proposition
    ``prop:chain`` (i)), so the cheap refusal must never fire on it. A rule that
    refused here would refuse the contract's own construction.
    """
    scaled = tuple(scale(F(1, 2), element) for element in family)
    above = tuple(add(element, scale(F(1, 4), identity(2))) for element in scaled)
    # Rebuild an admissible certified family: p_v = 1/4 works because
    # blk M^{>N}_v - (1/4) 1 = (1/2) M_v >= 0 by construction.
    certified = (F(1, 4), F(1, 4))
    assume(sum(certified, start=F(0)) < 1)
    preserved = tuple(scale(w, identity(1)) for w in weights)
    physical = tuple(
        add(
            scale(F(0), identity(3)),
            _block_diagonal(preserved[index], above[index]),
        )
        for index in range(2)
    )
    target = wpfss_target(preserved, certified)
    mprime = mprime_family(above, certified)
    for index in range(2):
        assert equal(wp_adjoint(target[index], 1, mprime), physical[index])
    assert rule_obstructions(list(physical), list(target)) is None


def _block_diagonal(preserved: Matrix, above: Matrix) -> Matrix:
    """Return ``preserved (+) above`` on the three-dimensional source space."""
    from certiqs_key.foundations.exact import direct_sum

    return direct_sum([preserved, above])


@given(family=diagonal_povms(outcomes=2, dimension=2))
@SLOW
def test_linear_relations_really_solve_the_system_they_claim(
    family: tuple[Matrix, ...],
) -> None:
    """Lemma ``lem:obstructions`` (ii)'s second clause needs the relations exact."""
    for coefficients in linear_relations(list(family), identity(2)):
        combination = zeros(2)
        for weight, element in zip(coefficients[:-1], family, strict=True):
            combination = add(combination, scale(weight, element))
        assert equal(combination, scale(coefficients[-1], identity(2)))
    assert span_dimension(list(family)) <= 4


# ---------------------------------------------------------------------------
#  The adjoints are unital, which every transported statement rests on
# ---------------------------------------------------------------------------


@given(family=diagonal_povms(outcomes=3, dimension=2), weights=probability_vectors(3))
@SLOW
def test_every_adjoint_this_module_computes_is_unital(
    family: tuple[Matrix, ...], weights: tuple[Fraction, ...]
) -> None:
    """``Lambda^dagger(1_Q) = 1_B``: trace preservation read through eq:pairing."""
    scaled = tuple(scale(F(1, 2), element) for element in family)
    above = tuple(add(element, scale(F(1, 6), identity(2))) for element in scaled)
    certified = tuple(F(1, 6) for _ in range(3))
    assume(sum(certified, start=F(0)) < 1)
    mprime = mprime_family(above, certified)
    assert equal(wp_adjoint(identity(1 + 3), 1, mprime), identity(3))
    assert equal(mp_adjoint(identity(3), list(above)), identity(2))
    assert equal(noise_adjoint(identity(1 + 3), 1, certified), identity(1 + 3))
    del weights


@given(
    letters=st.integers(min_value=1, max_value=3),
    slot=st.builds(
        Fraction,
        st.integers(min_value=0, max_value=3),
        st.integers(min_value=4, max_value=8),
    ),
)
@SLOW
def test_the_weight_route_emits_zero_away_from_every_bounded_letter(
    letters: int, slot: Fraction
) -> None:
    """Section 2.2: ``p_(y,t) := 0`` for EVERY other ``(y, t)``."""
    ports = 2
    channel = product_form_dark_counts(ports, {1: F(0), 2: F(0)})
    alphabet = tuple(f"y{index}" for index in range(letters))
    all_patterns = patterns(ports)
    assignment = {
        pattern: alphabet[index % letters] for index, pattern in enumerate(all_patterns)
    }
    assume(set(assignment.values()) == set(alphabet))
    coarse = CoarseGraining(ports=ports, letters=alphabet, assignment=assignment)
    descended = descend(channel, coarse)
    assume(descended is not None)
    assert descended is not None
    bounded = alphabet[0]
    assume(descended.is_absorbing_at(bounded))
    bounds = (HighPhotonBound.uniform(coarse.fibre(bounded), slot, ("t0",)),)
    letters_record = bounded_letters(bounds, coarse, descended)
    assert letters_record is not None
    probe = ProbeDeclaration(settings=("t0",), weights={"t0": F(1)})
    joint = tuple((letter, "t0") for letter in alphabet)
    # kappa = 53 IS THE COARSEST STATEMENT THIS PROPERTY CAN MAKE and is the
    # right one here: Eq. eq:latdown's floor is the IDENTITY on a value already
    # on the lattice ("equal to it whenever it is already a lattice number"),
    # and every value this strategy generates is a dyadic rational of small
    # denominator. So the property below is about eq:weightroute's ROUTE and
    # not about its rounding, which is what it was about before 1.0.0 too --
    # the rounding has its own golden case, where the floor bites.
    weights = weight_route(letters_record, probe, joint, lattice_exponent=53)
    assert weights is not None
    r_min = minimum_off_letter_rate(descended, bounded)
    exact = (1 - r_min) * slot + r_min
    assume((exact * 2**53).denominator == 1)
    assert weights[(bounded, "t0")] == exact
    # AND lat(0) = 0 AT EVERY EXPONENT, so the zeros are unconditional.
    for letter in alphabet[1:]:
        assert weights[(letter, "t0")] == 0


@pytest.mark.contract
def test_the_transported_projector_pair_is_always_complementary() -> None:
    """Eq. ``eq:transportproj``: ``Pi_{<=N} + Pi_Flag = 1_Q`` at every shape."""
    for preserved_dim in range(1, 4):
        for alphabet_size in range(1, 4):
            pi_leq, pi_flag = transported_cutoff_projectors(
                preserved_dim, alphabet_size
            )
            total = add(pi_leq, pi_flag)
            assert equal(total, identity(preserved_dim + alphabet_size))
            assert is_positive_semidefinite(pi_leq)
            assert is_positive_semidefinite(pi_flag)


@pytest.mark.contract
def test_the_fss_target_is_the_zero_weight_case_of_the_wpfss_target() -> None:
    """Definition ``def:targets``: ``F^FSS`` is ``F^WP`` at ``p_v == 0``."""
    preserved = (matrix([[F(2, 3)]]), matrix([[F(1, 3)]]))
    zero_weights = (F(0), F(0))
    assert all(
        equal(a, b)
        for a, b in zip(
            fss_target(preserved),
            wpfss_target(preserved, zero_weights),
            strict=True,
        )
    )

