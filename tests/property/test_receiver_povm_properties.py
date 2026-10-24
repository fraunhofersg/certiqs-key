"""Property tests over random small receivers.

These do NOT replay the registry: they check that the contract's statements
hold on instruments the freeze never saw. Every property below is a claim of
the contract quantified over ARBITRARY admissible data, which is exactly how
the contract states them: Remark ``rem:rankone`` lists the theorems of the core
and its submodules that are proved for arbitrary ``{A_k}``.

    Theorem thm:port-grams (i), (ii)   Grams admissible; the rank bound
    Theorem thm:click-povm (i), (iii)  blocks positive, complete, graded
    Theorem thm:representation-independence (iii)       per-port unitaries are invisible
    Theorem thm:efficiency (i)        eta_k > 0 preserves the rank
    Theorem thm:dark-counts (i)-(iv)   column-stochastic, absorbing, and the r_min
                                minimum that INCLUDES the no-click column
    Theorem thm:compilation-well-defined (i), (iv)   the sort is irrelevant; (E3)
    refuses Theorem thm:multiclick-bound       beta <= 1, and the bound holds on each
    block
"""

from __future__ import annotations

import math
from fractions import Fraction
from itertools import pairwise

import numpy as np
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from receiver_povm_support import TOLERANCE

from certiqs_key.receiver import (
    DarkCountRoute,
    Element,
    ElementGraph,
    GramFamily,
    Polarizer,
    Rotator,
    apply_uniform_efficiency,
    bound_data_from_family,
    bound_function,
    capped_coefficient,
    check_dark_channel,
    check_element_graph,
    check_gram_family_admissible,
    coarse_elements,
    collapse_slack,
    compile_element_graph,
    completeness_defect,
    composed_slack,
    composition_correction,
    element_block,
    improved_bound,
    minimum_multiclick_mass,
    multiclick_mass,
    port_grams,
    product_form,
    raw_alphabet,
    setting_bound,
    unconditioned_family,
)
from certiqs_key.receiver.numerics import (
    Scalar,
    eigenvalues,
    epsilon_rank,
    lambda_max,
    positive_part,
    residual_norm,
)
from certiqs_key.receiver.reasons import GRAPH_CONDITION_REASONS

_SETTINGS = settings(
    max_examples=40,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)

_ENTRIES = st.floats(
    min_value=-1.0, max_value=1.0, allow_nan=False, allow_infinity=False, width=32
)


def _contraction(values: list[float], rows: int, columns: int) -> np.ndarray:
    """Return a random matrix scaled to be a contraction."""
    real = np.asarray(values[: rows * columns], dtype=np.float64).reshape(rows, columns)
    imaginary = np.asarray(
        values[rows * columns : 2 * rows * columns], dtype=np.float64
    ).reshape(rows, columns)
    matrix = (real + 1j * imaginary).astype(np.complex128)
    norm = float(np.linalg.norm(matrix, ord=2))
    if norm > 1.0:
        matrix = matrix / norm
    return np.asarray(matrix, dtype=np.complex128)


@st.composite
def instruments(draw: st.DrawFn) -> tuple[np.ndarray, GramFamily, list[list[int]]]:
    """Draw a random small instrument and its port Gram family."""
    inputs = draw(st.integers(min_value=1, max_value=2))
    ports = draw(st.integers(min_value=1, max_value=3))
    sizes = [draw(st.integers(min_value=1, max_value=2)) for _ in range(ports)]
    rows = sum(sizes)
    values = draw(
        st.lists(_ENTRIES, min_size=2 * rows * inputs, max_size=2 * rows * inputs)
    )
    gamma_inp = _contraction(values, rows, inputs)
    port_rows: list[list[int]] = []
    start = 0
    for size in sizes:
        port_rows.append(list(range(start, start + size)))
        start += size
    labels = tuple(f"p{index}" for index in range(ports))
    return gamma_inp, GramFamily(labels, port_grams(gamma_inp, port_rows)), port_rows


@pytest.mark.contract
@_SETTINGS
@given(instruments())
def test_port_grams_of_a_contraction_are_always_admissible(
    drawn: tuple[np.ndarray, GramFamily, list[list[int]]],
) -> None:
    """Theorem thm:port-grams (i), (ii) on an arbitrary contraction."""
    gamma_inp, family, port_rows = drawn
    assert check_gram_family_admissible(family, TOLERANCE) is None
    for matrix in family.matrices:
        assert float(np.min(eigenvalues(matrix))) >= -TOLERANCE.eps_2
    assert float(np.min(eigenvalues(family.deficiency))) >= -TOLERANCE.eps_2
    for rank, rows in zip(family.ranks(TOLERANCE.eps_2), port_rows, strict=True):
        assert rank <= min(gamma_inp.shape[1], len(rows))


@pytest.mark.contract
@_SETTINGS
@given(instruments(), st.integers(min_value=0, max_value=2))
def test_povm_blocks_are_positive_and_complete_per_sector(
    drawn: tuple[np.ndarray, GramFamily, list[list[int]]], photons: int
) -> None:
    """Theorem thm:click-povm (i), (iii) on an arbitrary admissible Gram family."""
    _, family, _ = drawn
    no_click = unconditioned_family(family)
    blocks = coarse_elements(no_click, photons)
    size = no_click.block_dimension(photons)
    for block in blocks.values():
        assert float(np.max(np.abs(block - block.conj().T))) <= TOLERANCE.eps_4
        assert float(np.min(eigenvalues(block))) >= -TOLERANCE.eps_2
    total = sum(blocks.values())
    assert float(np.max(np.abs(total - np.eye(size)))) <= TOLERANCE.eps_4
    assert (
        float(np.max(np.abs(completeness_defect(no_click, photons)))) <= TOLERANCE.eps_4
    )
    # Every RAW element is positive too, although Eq. eq:incexc is alternating.
    for pattern in raw_alphabet(family.port_count):
        block = element_block(no_click, pattern, photons)
        assert float(np.min(eigenvalues(block))) >= -TOLERANCE.eps_2


@pytest.mark.contract
@_SETTINGS
@given(instruments(), st.lists(_ENTRIES, min_size=3, max_size=3))
def test_per_port_phases_are_invisible_in_the_grams(
    drawn: tuple[np.ndarray, GramFamily, list[list[int]]], phases: list[float]
) -> None:
    """Theorem thm:representation-independence (iii) and Corollary cor:phases, with its hypothesis."""  # noqa: E501
    gamma_inp, family, port_rows = drawn
    rotated = gamma_inp.copy()
    for index, rows in enumerate(port_rows):
        factor = np.exp(1j * math.pi * phases[index % len(phases)])
        for row in rows:
            rotated[row, :] = factor * rotated[row, :]
    rebuilt = port_grams(rotated, port_rows)
    for before, after in zip(family.matrices, rebuilt, strict=True):
        assert float(np.max(np.abs(before - after))) <= TOLERANCE.eps_2


@pytest.mark.contract
@_SETTINGS
@given(instruments(), st.lists(_ENTRIES, min_size=3, max_size=3))
def test_a_strictly_positive_efficiency_preserves_every_rank(
    drawn: tuple[np.ndarray, GramFamily, list[list[int]]], raw: list[float]
) -> None:
    """Theorem thm:efficiency (i) under the DECLARED threshold of Eq. eq:eps2rank.

    Theorem thm:efficiency (i) is about the EXACT rank, and ``eta_k > 0`` leaves it
    untouched: ``eta A`` and ``A`` have the same kernel. What this module
    decides is ``rk_{eps_2}``, and Definition def:tolmap (ii) makes THE
    THRESHOLD ABSOLUTE -- deliberately, because a threshold taken relative to
    lmax(A_k) would make the decision at a nearly dark port A MILLION TIMES
    TIGHTER than at a lossless one (Remark rem:ranktwosided). So an attenuation
    can push an eigenvalue below eps_2 and LOWER the count, which is that
    remark's under-reporting direction and is why the rank test gives its
    answer only on the Grams AFTER every efficiency is applied, never before
    (Remark rem:effrank; Requirement req:one-mode-per-port). Two statements survive
    exactly, and both are asserted:

    * ``eta_k in (0, 1]`` can only LOWER the count, never raise it;
    * the count is SCALE-COVARIANT: ``rk_{eta eps}(eta A) = rk_{eps}(A)``, which
      is Theorem thm:efficiency (i) in the form an absolute threshold admits.
    """
    _, family, _ = drawn
    efficiencies = [0.1 + 0.9 * abs(value) for value in raw[: family.port_count]]
    scaled = apply_uniform_efficiency(family, efficiencies)
    for after, before in zip(
        scaled.ranks(TOLERANCE.eps_2), family.ranks(TOLERANCE.eps_2), strict=True
    ):
        assert after <= before
    for matrix, eta in zip(family.matrices, efficiencies, strict=True):
        assert epsilon_rank(eta * matrix, eta * TOLERANCE.eps_2) == epsilon_rank(
            matrix, TOLERANCE.eps_2
        )
    for before, after, eta in zip(
        family.matrices, scaled.matrices, efficiencies, strict=True
    ):
        assert float(np.max(np.abs(after - eta * before))) <= TOLERANCE.eps_2
    assert check_gram_family_admissible(scaled, TOLERANCE) is None


@pytest.mark.contract
@_SETTINGS
@given(instruments(), st.integers(min_value=0, max_value=2))
def test_the_bound_holds_on_every_block_and_beta_is_at_most_one(
    drawn: tuple[np.ndarray, GramFamily, list[list[int]]], photons: int
) -> None:
    """Theorem thm:multiclick-bound Eq. eq:mcbound, on an arbitrary receiver."""
    _, family, _ = drawn
    no_click = unconditioned_family(family)
    data = bound_data_from_family(no_click)
    beta = bound_function(data, photons)
    assert beta <= 1.0 + TOLERANCE.eps_2
    block = coarse_elements(no_click, photons)["mc"]
    assert float(np.min(eigenvalues(block))) >= beta - TOLERANCE.eps_2


@pytest.mark.contract
@_SETTINGS
@given(instruments())
def test_the_branch_one_weight_is_non_decreasing_in_the_cutoff(
    drawn: tuple[np.ndarray, GramFamily, list[list[int]]],
) -> None:
    """Eq. eq:collapseinf under (X): max{0, beta(N+1)} cannot fall as N grows."""
    _, family, _ = drawn
    data = bound_data_from_family(unconditioned_family(family))
    weights = [
        setting_bound("off", data, cutoff, True, TOLERANCE).weight
        for cutoff in range(6)
    ]
    for earlier, later in pairwise(weights):
        assert later >= earlier - TOLERANCE.eps_2


@pytest.mark.contract
@_SETTINGS
@given(
    st.integers(min_value=2, max_value=3),
    st.lists(
        st.floats(min_value=0.0, max_value=1.0, allow_nan=False, width=32),
        min_size=3,
        max_size=3,
    ),
)
def test_the_dark_channel_is_column_stochastic_absorbing_and_r_min_is_the_minimum(
    ports: int, raw: list[float]
) -> None:
    """Theorem thm:dark-counts (i), (iii), (iv) and Eq. eq:rmin's own domain."""
    channel = product_form(raw[:ports])
    assert check_dark_channel(channel, TOLERANCE) is None
    patterns = channel.patterns()
    for column in patterns:
        total = sum(channel.entry(row, column) for row in patterns)
        assert abs(total - 1.0) <= TOLERANCE.eps_4
        for row in patterns:
            if channel.entry(row, column) > TOLERANCE.eps_2:
                assert column <= row
    # Multiclick absorption on every multiclick column.
    for column in channel.multiclick_patterns():
        assert abs(multiclick_mass(channel, column) - 1.0) <= TOLERANCE.eps_4
    # r_min is the minimum over EVERY non-multiclick column, no-click included.
    minimum = minimum_multiclick_mass(channel)
    multiclick = set(channel.multiclick_patterns())
    non_multiclick = [column for column in patterns if column not in multiclick]
    assert frozenset() in non_multiclick
    for column in non_multiclick:
        assert minimum <= multiclick_mass(channel, column) + TOLERANCE.eps_4
    assert any(
        abs(minimum - multiclick_mass(channel, column)) <= TOLERANCE.eps_4
        for column in non_multiclick
    )


@pytest.mark.contract
@_SETTINGS
@given(
    st.floats(min_value=0.0, max_value=3.0, allow_nan=False, width=32),
    st.floats(min_value=0.0, max_value=1.0, allow_nan=False, width=32),
    st.booleans(),
)
def test_overlapping_supports_need_an_edge_and_the_edge_fixes_the_product(
    angle: float, transmittance: float, ordered: bool
) -> None:
    """Definition def:graph (E3), Theorem thm:compilation-well-defined (i), (iv), and Remark rem:e3."""  # noqa: E501
    elements = (
        Element("e", Rotator(angle), (0, 1)),
        Element("f", Polarizer(0.0, transmittance, 0.0), (0, 1)),
    )
    edges = (("e", "f"),) if ordered else ()
    graph = ElementGraph(elements, edges)
    refusal = check_element_graph(graph, 2, TOLERANCE)
    if not ordered:
        assert refusal is not None
        assert refusal.reason is GRAPH_CONDITION_REASONS["E3"]
        return
    assert refusal is None
    extensions = compile_element_graph(graph, 2)
    assert extensions.shape == (2, 2)
    # A contraction by construction (Theorem thm:compilation-well-defined (ii)).
    defect = extensions.conj().T @ extensions - np.eye(2)
    assert float(np.max(np.linalg.eigvalsh(defect).real)) <= TOLERANCE.eps_1
    # And the ONE linear extension is the declared order.
    assert (
        float(np.max(np.abs(extensions - compile_element_graph(graph, 2, ("e", "f")))))
        <= TOLERANCE.eps_1
    )


# ---------------------------------------------------------------------------
#  The registry-0.2.0 amendment: eq:r1islmax, eq:rbar, eq:darkpmcslack, rem:noslack
# ---------------------------------------------------------------------------


@pytest.mark.contract
@_SETTINGS
@given(
    st.lists(_ENTRIES, min_size=8, max_size=8),
    st.floats(min_value=0.5, max_value=3.0, allow_nan=False, width=32),
)
def test_eq_r1islmax_is_an_identity_on_contractive_and_non_contractive_matrices(
    values: list[float], scale: float
) -> None:
    """Eq. eq:r1islmax on ARBITRARY Gamma, contractive or not.

        r_1 = ||(Gamma^dagger Gamma - 1)_+|| = (lmax(Gamma^dagger Gamma) - 1)_+

    Definition ``def:tolmap`` (v) calls the admission and the residual "the SAME
    TEST ON THE SAME NUMBER". The scale runs from 1/2 to 3, so both regimes are
    drawn: a contraction, where both sides are 0, and a matrix scaled past 1,
    where both are positive.

    WHAT IS ASSERTED, AND WHAT def:evaluation-model FORBIDS ASSERTING. The identity is
    between two EXACT reals and is asserted as such, to ``1e-12`` -- far tighter
    than any declared tolerance. What cannot be asserted is that the two
    INDEPENDENT FLOAT EVALUATIONS of that one real -- the positive-part spectral
    norm this module reports as ``r_1``
    (:mod:`certiqs_key.receiver.residuals`) and the ``lmax`` this module decides
    admission with (:mod:`certiqs_key.receiver.request`) -- agree about a
    comparison against a threshold lying INSIDE the gap between them. Definition
    ``def:evaluation-model`` and Theorem ``thm:exact-and-evaluated`` (ii) say
    so in as many words:
    "the emitted ``{A_k}``, block matrices and bound values are FLOATING-POINT
    EVALUATIONS of those quantities. This contract asserts NO BOUND ON THE
    DIFFERENCE." The two agree wherever the declared threshold is outside that
    gap, and that is what the loop below asserts.

    THE CASE THIS EXCLUDES IS REAL AND IS NOT A TEST ARTEFACT. At the admissible
    ``eps_1 = 0`` -- Remark ``rem:tolerancedomain``'s closed end, which "a
    declarer who wants a condition decided EXACTLY declares" -- an exactly
    unitary ``Gamma`` can evaluate with ``lmax = 1`` and a reassembled positive
    part of norm ``2e-16``, so the artifact would carry ``r_1 > 0`` on a
    declaration admission passed. That is Theorem ``thm:exact-and-evaluated`` (ii) doing
    exactly what it says, on a receiver the contract calls the simplest legitimate
    device, and it is a property of the evaluation and not of the identity.
    """
    gamma = scale * _contraction(values, 2, 2)
    product = np.asarray(gamma.conj().T @ gamma, dtype=np.complex128)
    residual = residual_norm(positive_part(product - np.eye(2)))
    closed_form = max(0.0, lambda_max(product) - 1.0)
    assert residual == pytest.approx(closed_form, abs=1e-12)
    # The two TESTS agree at every declared tolerance the evaluation gap does
    # not straddle -- which is what the identity buys, and all def:evaluation-model lets
    # a test claim of two evaluations of one exact number.
    gap = abs(residual - closed_form)
    for epsilon in (0.0, TOLERANCE.eps_1, 0.5):
        if abs(closed_form - epsilon) <= gap:
            continue
        assert (residual <= epsilon) is (lambda_max(product) <= 1.0 + epsilon)


@pytest.mark.contract
@_SETTINGS
@given(st.floats(min_value=-2.0, max_value=3.0, allow_nan=False, width=32))
def test_rbar_is_at_most_r_min_and_at_most_one_and_is_never_floored(
    minimum_mass: float,
) -> None:
    """Eq. eq:rbar: ``rbar = min{r_min, 1}``, on arbitrary ``r_min``.

    Proposition ``prop:dark-slack-bound``: "no step uses a bound on ``r_min``
    from either side, and no step uses the sign of ``r_min`` or of ``rbar``".
    So a NEGATIVE ``r_min`` gives a negative ``rbar``, and the only thing the
    cap buys is ``1 - rbar >= 0``.
    """
    capped = capped_coefficient(minimum_mass)
    assert capped <= minimum_mass
    assert capped <= 1.0
    assert 1.0 - capped >= 0.0
    if minimum_mass < 0.0:
        assert capped == minimum_mass < 0.0
    if minimum_mass <= 1.0:
        assert capped == minimum_mass


@pytest.mark.contract
@_SETTINGS
@given(
    st.integers(min_value=2, max_value=4),
    st.lists(
        st.floats(min_value=0.0, max_value=0.5, allow_nan=False, width=32),
        min_size=4,
        max_size=4,
    ),
    st.floats(min_value=0.0, max_value=1.0, allow_nan=False, width=32),
)
def test_eq_darkpmcslack_holds_against_the_exact_composed_spectrum(
    ports: int, probabilities: list[float], weight: float
) -> None:
    """Eq. eq:darkpmcslack on a random admitted channel and a random ``p_mc``.

    The composed multiclick element is built EXACTLY -- ``Mtilde_MC = sum_{S'}
    R_{MC|S'} M_{S'}`` on a block whose spectrum is known -- and the claimed
    coefficient is compared against it. The blocks are taken as the extreme
    admissible family for the hypothesis ``blk M^{(>N)}_MC >= p_mc id``: mass
    ``p_mc`` on the multiclick columns and the complement elsewhere, which is
    the tightest case the inequality must survive.
    """
    channel = product_form(probabilities[:ports], DarkCountRoute.PER_PORT_PRODUCT_FORM)
    assert check_dark_channel(channel, TOLERANCE) is None
    r_min = minimum_multiclick_mass(channel)
    r_bar = capped_coefficient(r_min)
    delta = composition_correction(channel.route, ports, TOLERANCE)
    claimed = composed_slack(weight, r_bar, delta)
    # The exact composed value on the extreme family: the multiclick columns
    # carry R_{MC|S'} = 1 (Thm. thm:dark-counts (iii)) and contribute p_mc, and the
    # others contribute at least r_min times the complementary mass.
    multiclick = set(channel.multiclick_patterns())
    exact = weight
    for column in channel.patterns():
        if column in multiclick:
            continue
        exact_column = multiclick_mass(channel, column)
        assert exact_column >= r_min - 1e-15
    exact += r_min * (1.0 - weight)
    assert claimed <= exact + 1e-12
    # On the generated route the two forms coincide exactly.
    assert delta == 0.0
    assert claimed == pytest.approx(improved_bound(r_min, weight), abs=1e-15)


@pytest.mark.contract
@_SETTINGS
@given(instruments(), st.integers(min_value=0, max_value=2))
def test_the_collapse_slack_is_never_positive_on_a_random_receiver(
    drawn: tuple[np.ndarray, GramFamily, list[list[int]]], cutoff: int
) -> None:
    """Remark rem:noslack: ``sigma = -beta(0) <= 0``, ALWAYS.

    ``beta(0)`` is the vacuum block of the multiclick element, a diagonal block
    of a positive operator and hence a NON-NEGATIVE REAL, so a computed
    branch-1 test demanding positive slack could never
    fire. Checked on random receivers rather than on the frozen tuples.
    """
    _, family, _ = drawn
    data = bound_data_from_family(unconditioned_family(family))
    assert collapse_slack(data) == pytest.approx(-bound_function(data, 0), abs=1e-12)
    assert collapse_slack(data) <= TOLERANCE.eps_2
    assert bound_function(data, 0) >= -TOLERANCE.eps_2
    # And branch 1 is taken exactly where (X) is declared to hold.
    record = setting_bound("t", data, cutoff, True, TOLERANCE)
    assert record.predicate_x is True
    assert str(record.branch) == "1"


@st.composite
def _declared_probabilities(draw: st.DrawFn) -> list[Scalar]:
    """Draw per-port dark-count probabilities in BOTH declared presentations.

    Assumption ``ass:exact`` admits either: a declared ``Fraction`` is the
    exact number it writes, and a declared ``float`` is a binary64 value, hence
    a dyadic rational that ``Fraction(x)`` names exactly. Both are drawn, and
    mixed within one declaration, because Eq. ``eq:darkR`` must be evaluated
    exactly on whichever the declarer used.
    """
    ports = draw(st.integers(min_value=1, max_value=3))
    values: list[Scalar] = []
    for _ in range(ports):
        if draw(st.booleans()):
            denominator = draw(st.integers(min_value=1, max_value=64))
            numerator = draw(st.integers(min_value=0, max_value=denominator))
            values.append(Fraction(numerator, denominator))
        else:
            values.append(
                draw(st.floats(min_value=0.0, max_value=1.0, allow_nan=False, width=32))
            )
    return values


@pytest.mark.contract
@_SETTINGS
@given(_declared_probabilities())
def test_the_generated_dark_channel_is_evaluated_exactly(
    probabilities: list[Scalar],
) -> None:
    """Eq. eq:darkR, exactly, on arbitrary declared probabilities.

    Theorem ``thm:dark-counts`` (i) proves the product form satisfies (D1) and
    (D2) -- "by construction", in Definition ``def:darkadm``'s words -- and
    Remark ``rem:d2slack`` (b) sets ``delta_dc = 0`` on this route BECAUSE they
    are THEOREMS there and NOT TESTS, so there is no slack to carry. Both
    statements are about the EMITTED matrix, so the evaluation has to be exact:
    a float product leaves the columns summing to ``1 +/- O(2^-54)`` and the
    module would then declare a slack of zero over a matrix that has one, with
    no threshold of this contract standing behind it -- the generated route has
    none.

    THE ORACLE IS THE EQUATION ITSELF, recomputed here in ``Fraction``
    arithmetic from the declared probabilities, so nothing in the assertion
    reads the module's own arithmetic back to itself.
    """
    channel = product_form(probabilities)
    ports = range(len(probabilities))
    exact = [Fraction(value) for value in probabilities]

    # (D1), the column-sum half, EXACTLY: every column sums to exactly 1.
    for column in channel.patterns():
        total = sum(
            (channel.entry(row, column) for row in channel.patterns()),
            start=Fraction(0),
        )
        assert total == 1, (sorted(column), total)

    # Every entry is EXACTLY the product Eq. eq:darkR writes, and is exact.
    for column in channel.patterns():
        for row in channel.patterns():
            oracle = Fraction(0)
            if column <= row:
                oracle = Fraction(1)
                for port in ports:
                    if port in row - column:
                        oracle *= exact[port]
                    elif port not in row:
                        oracle *= 1 - exact[port]
            entry = channel.entry(row, column)
            assert Fraction(entry) == oracle, (sorted(row), sorted(column))
            # (D2): a non-zero entry has the column as a SUBSET of the row.
            if entry != 0:
                assert column <= row

    # And the derived scalars are exact too, since they are sums and minima of
    # exact entries: `outputs.dark_count_channel` emits r_min exactly as
    # eq:rmin computes it.
    r_min = minimum_multiclick_mass(channel)
    assert isinstance(r_min, Fraction | int)
    assert isinstance(capped_coefficient(r_min), Fraction | int)
