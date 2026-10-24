"""The Slice-1 closed forms, against ``meat-core``'s own machinery. No solver.

Everything here is an EVALUATION and not an optimization, so nothing here needs
QICS and nothing here is slow. That separation is deliberate: it puts the
derivations of ``tests/support/bb84_targets.py`` under test against an
independent implementation of the same mathematics -- ``meat-core``'s objective
and its C16 limit oracle, on the declaration the compiler actually emitted --
before any of them is used to judge a solver run in
``tests/integration/test_bb84_slice.py``.

A disagreement here means one of the two derivations is wrong. A disagreement
there, with these passing, means the solver did not converge.

TARGET 1 LIVES HERE, and that is a deviation worth stating in the file that
carries it. The first analytic target is "``Q = 0`` implies the
exact closed-form key length", and at ``Q = 0`` the SOLVER cannot be run on this
declaration at all: the honest ``Phi(err)`` is exactly ``0``, so
``statistics-acceptance`` constructs the degenerate interval ``[0, 0]`` for that
outcome -- a binomial with ``p = 0`` is deterministic, and Theorem ``thm:sa3``
(v) says so -- and ``meat-core`` then refuses to differentiate at a point with
``q(chat) = 0`` (Corollary ``cor:full-gradient``). That refusal is asserted in
the integration module, where it belongs. The ``Q = 0`` target is therefore
discharged EXACTLY rather than numerically: the objective at the honest point is
a rational number, ``meat-core``'s own ``objective_value`` reproduces it, and
the key length that follows is an exact integer.
"""

from __future__ import annotations

import math
from fractions import Fraction as F
from itertools import pairwise

import numpy as np
import pytest
from bb84_targets import (
    AMBIENT_BRANCH_DIMENSION,
    CLOSED_FORM_TOLERANCE,
    Q_STAR,
    bell_diagonal_objective,
    bell_diagonal_state,
    binary_entropy,
    devetak_winter_ceiling,
    honest_point_objective,
    limit_at_depolarized_state,
    reduced_h_low_singleton,
    von_neumann_limit,
)
from instances.bb84.declare import declare_acceptance_frequencies
from instances.bb84.specification import bb84_specification
from instances.common.honest.depolarized_bell_pair import (
    depolarized_state,
    honest_distribution,
)

from certiqs_key.meat_core.declaration.declaration import (
    AcceptanceSet,
    KeyLengthParameters,
)
from certiqs_key.meat_core.declaration.validation import validate_declaration
from certiqs_key.meat_core.docking import compiler_emission, dock_declaration
from certiqs_key.meat_core.finitekey.keylength import key_length_for_declaration
from certiqs_key.meat_core.objective.branch import generate_maps, statistics
from certiqs_key.meat_core.objective.limit import (
    check_limit_hypotheses,
    limit_objective,
)
from certiqs_key.meat_core.objective.objective import objective_value
from certiqs_key.meat_core.objective.support import ambient_branch_dimension
from certiqs_key.protocol_compiler import compile_specification

#: THE SNAP'S TWO DECLARED NUMBERS, AND NEITHER HAS A DEFAULT.
#:
#: ``meat-core``'s ``acceptance_data_exact`` row decides the declared
#: acceptance data at "exactly 0" in exact rational arithmetic (the exact
#: island, spec/architecture.md 2.8), and a vector obtained by converting exact
#: rationals coordinatewise to binary64 has an exact sum a hair away from one.
#: ``meat-core`` refuses it and never repairs it -- "a producer emits exact
#: rationals, or SNAPS AT THE INSTANCE before this module sees the data" -- so
#: the remedy is the PRODUCER'S:
#: :func:`instances.bb84.declare.declare_acceptance_frequencies` runs the
#: shared snapping table of spec/architecture.md 2.9 and emits a dyadic vector
#: whose exact sum IS one, with the displacement recorded per coordinate.
#:
#: ``kappa = 40`` is that section's measured value, at which the per-coordinate
#: displacement is at most ``2^-41 = 4.5e-13``; ``tau = 0`` is what this slice
#: declares everywhere else, and the snap needs no more of it -- the lattice
#: step is not decided by ``tau``, and the pre-snap defects of this family are
#: exactly ``0`` in binary64. Both are passed explicitly because neither has a
#: default anywhere on this platform.
SNAP_LATTICE_EXPONENT = 40
SNAP_TOLERANCE = 0.0

pytestmark = pytest.mark.contract

#: Two weight pairs: the symmetric dyadic one and an asymmetric one. Both are
#: frozen-registry rows, so the honest distribution behind each is pinned.
SYMMETRIC = (F(1, 2), F(1, 2), F(1, 2), F(1, 2))
ASYMMETRIC = (F(7, 8), F(1, 8), F(3, 4), F(1, 4))

#: The documented alpha grid. The registry's own :data:`ALPHA_GRID` plus the two
#: ends of the interval this slice cares about: ``1.01`` is as close to the
#: ``alpha -> 1+`` limit as the key-length gate's ``(1, 2)`` domain and the
#: ``alpha/(alpha-1)`` privacy-amplification cost make worthwhile, and ``1.9``
#: is the far end.
ALPHA_GRID = (1.01, 1.05, 1.25, 1.5, 1.75, 1.9)

PARAMETERS = KeyLengthParameters(
    alpha=1.5, eps_pa=2.0**-30, eps_ev=2.0**-30, lambda_ec=200_000
)


def docked_at(weights: tuple[F, F, F, F], qber: F, *, rounds: int = 1_000_000):
    """Return the declaration docked with the SINGLETON at the honest point.

    A singleton, not a constructed polytope: this module evaluates closed forms
    and never optimizes, and the acceptance set it needs is the one the closed
    forms are stated over.
    """
    result = compile_specification(bb84_specification(*weights))
    assert result.declaration is not None
    honest = honest_distribution(result.declaration, qber)
    # THE INSTANCE DECLARES, AND THE SNAP IS THE INSTANCE'S. What is docked is
    # a DYADIC vector whose exact sum is one, not the coordinatewise float of
    # an exact rational one -- Section 2.6's acceptance_data_exact row is at
    # exactly 0 over the rationals and admits nothing a window would have
    # admitted. The closed forms below are compared against `honest`, the exact
    # model, and the displacement between the two is bounded by 2^-41.
    frequencies, _ = declare_acceptance_frequencies(
        honest,
        result.declaration.acceptance_alphabet,
        tolerance=SNAP_TOLERANCE,
        lattice_exponent=SNAP_LATTICE_EXPONENT,
    )
    docked = dock_declaration(
        result.declaration,
        acceptance_set=AcceptanceSet(geometry="singleton", frequencies=frequencies),
        rounds=rounds,
        parameters=PARAMETERS,
    )
    validate_declaration(docked)
    return result.declaration, docked, honest


def state_blocks(matrix: np.ndarray) -> dict[str, np.ndarray]:
    """Return a ``4 x 4`` state as the single-sector block map the engine reads."""
    return {"s0": np.asarray(matrix, dtype=np.complex128)}


def exact_state(qber: F) -> dict[str, np.ndarray]:
    """Return ``omega(Q)`` as machine numbers, converted from the exact substrate."""
    return state_blocks(
        np.array(
            [
                [complex(float(entry.re), float(entry.im)) for entry in row]
                for row in depolarized_state(qber)
            ],
            dtype=np.complex128,
        )
    )


# ===========================================================================
#  TARGET 1 -- Q = 0, exactly.
# ===========================================================================


@pytest.mark.parametrize("weights", [SYMMETRIC, ASYMMETRIC])
@pytest.mark.parametrize("alpha", ALPHA_GRID)
def test_the_zero_error_honest_objective_is_p_gen_for_every_alpha(
    weights: tuple[F, F, F, F], alpha: float
) -> None:
    """``O_alpha(Phi[omega(0)], omega(0)) = p^A_Z p^B_Z``, exactly and for every alpha.

    The derivation is in :func:`bb84_targets.honest_point_objective`: the four
    ``d(q, P)`` terms vanish because ``q = Phi[omega]``, the ``(Z,Z)`` branch
    operator is rank one with two equally weighted rows carrying the two key
    values, so ``K_gen = 2^{1-alpha} p_gen``, and the ``2^{1-alpha}`` cancels
    against the ``1/(alpha-1)`` outside the logarithm. That cancellation is the
    content: an implementation that got the pinching, the ``T + P - tr G``
    bookkeeping, or the ``alpha`` placement wrong would leave a residual
    ``alpha`` dependence, and this test sweeps ``alpha`` precisely to see it.
    """
    _, docked, honest = docked_at(weights, F(0))
    maps = generate_maps(docked)
    omega = exact_state(F(0))
    q = {c: float(honest[c]) for c in docked.acceptance_values}
    expected = float(honest_point_objective(weights[0], weights[2]))
    assert objective_value(maps, q, omega, alpha) == pytest.approx(
        expected, abs=CLOSED_FORM_TOLERANCE
    )


@pytest.mark.parametrize("weights", [SYMMETRIC, ASYMMETRIC])
def test_the_zero_error_statistics_are_the_declared_ones(
    weights: tuple[F, F, F, F],
) -> None:
    """``Phi[omega(0)]`` through ``meat-core``'s machinery, not the compiler's.

    The two implementations of Eq. ``eq:Phimap`` -- exact rationals on one side,
    ``complex128`` operators on the other -- agree, which is what makes it
    legitimate to state the closed forms of ``bb84_targets`` in the compiler's
    quantities and check them against the engine's.
    """
    _, docked, honest = docked_at(weights, F(0))
    predicted = statistics(generate_maps(docked), exact_state(F(0)))
    for chat in docked.acceptance_values:
        assert predicted[chat] == pytest.approx(
            float(honest[chat]), abs=CLOSED_FORM_TOLERANCE
        )


@pytest.mark.parametrize(
    ("weights", "expected_length"),
    [
        # l = floor(n h_low - lambda_EC - ceil(log2(1/eps_EV))
        #           - (alpha/(alpha-1)) log2(1/eps_PA) + 1), at
        # n = 10^6, h_low = p_gen, lambda_EC = 200000, eps_EV = eps_PA = 2^-30,
        # alpha = 3/2 so alpha/(alpha-1) = 3:
        #   symmetric  p_gen = 1/4:    250000 - 200000 - 30 - 90 + 1 =  49881
        #   asymmetric p_gen = 21/32:  656250 - 200000 - 30 - 90 + 1 = 456131
        (SYMMETRIC, 49_881),
        (ASYMMETRIC, 456_131),
    ],
)
def test_the_zero_error_key_length_is_an_exact_integer(
    weights: tuple[F, F, F, F], expected_length: int
) -> None:
    """Eq. ``eq:keylength`` on a rational ``h_low``, compared as an INTEGER.

    ``p_gen`` is a dyadic rational at both weight pairs, so ``n h_low`` is an
    exact integer at ``n = 10^6`` and every other term of Eq. ``eq:keylength`` is
    an integer or a quotient of machine numbers. There is nothing to round, and
    the assertion is an integer equality rather than a tolerance.

    The trailing constant is ``+1`` and not ``+2``: C14 of the accepted contract
    buys accepted-state secrecy at the cost of one bit (Remark ``rem:plus2``),
    and a ``+2`` here would overstate the key by one bit in the UNSAFE
    direction.
    """
    emitted, docked, _ = docked_at(weights, F(0))
    h_low = float(honest_point_objective(weights[0], weights[2]))
    # The declaration is the compiler's emission, docked: the token the run
    # tier would pass (req:compiled-declaration-only), minted the same way.
    compiled = compiler_emission(emitted)
    assert (
        key_length_for_declaration(docked, h_low, compiled=compiled, alpha=1.5)
        == expected_length
    )


def test_the_zero_error_infimum_is_strictly_below_the_honest_point() -> None:
    """The honest point is not the minimizer, and the gap is not small.

    :func:`bb84_targets.honest_point_objective` bounds ``h_low`` from above
    (contract Section 4.15) and does not equal it: a Bell-diagonal state with a
    little ``|Phi^-># mass buys an INFINITE-slope gain in ``K_gen`` -- the Renyi
    entropy ``H_{1/alpha}`` has infinite derivative at ``t = 0`` for every
    ``alpha > 1`` -- against a merely LINEAR loss in ``d(q_ok, P_ok)``. At
    ``alpha = 3/2`` and symmetric weights the trade is worth 20% of the rate.

    It is asserted because the alternative reading -- that ``h_low(0) = p_gen``
    -- is the plausible one, and a test suite that did not say otherwise would
    leave it standing.
    """
    p_gen = p_test = 0.25
    honest_value = float(honest_point_objective(F(1, 2), F(1, 2)))
    infimum = reduced_h_low_singleton(alpha=1.5, p_gen=p_gen, p_test=p_test, qber=0.0)
    assert infimum < honest_value - 0.04
    assert infimum == pytest.approx(0.2002, abs=5e-4)
    # And the gap closes as alpha -> 1+, where the Renyi term becomes h2.
    near_one = reduced_h_low_singleton(
        alpha=1.001, p_gen=p_gen, p_test=p_test, qber=0.0
    )
    assert honest_value - near_one < 1e-3
    assert von_neumann_limit(p_gen, 0.0) == pytest.approx(honest_value, abs=1e-15)


# ===========================================================================
#  The Bell-diagonal reduction, against meat-core's objective.
# ===========================================================================


@pytest.mark.parametrize("weights", [SYMMETRIC, ASYMMETRIC])
@pytest.mark.parametrize("alpha", ALPHA_GRID)
@pytest.mark.parametrize(
    "lam",
    [
        (0.98, 0.02, 0.0, 0.0),
        (0.90, 0.10, 0.0, 0.0),
        (0.70, 0.10, 0.15, 0.05),
        (0.40, 0.30, 0.20, 0.10),
    ],
    ids=["family-small", "family-large", "with-psi", "spread"],
)
def test_the_bell_diagonal_closed_form_is_meat_cores_objective(
    weights: tuple[F, F, F, F], alpha: float, lam: tuple[float, float, float, float]
) -> None:
    """The reduction of ``bb84_targets`` against an independent evaluation.

    This is the single most load-bearing check in the slice: every solver
    comparison downstream compares a Frank-Wolfe run against
    :func:`bb84_targets.reduced_h_low_singleton`, which is a minimum of
    :func:`bb84_targets.bell_diagonal_objective` -- and if that formula were
    wrong, the comparison would be a check of one error against another. Here
    the formula is checked pointwise against ``meat-core``'s own
    ``objective_value`` on the compiled declaration, at four Bell-diagonal
    states, six Renyi orders and two weight pairs, including states with
    ``|Psi^{+-}>`` mass where the second summand of ``S(lambda)`` is not
    degenerate.
    """
    alice_z, alice_x, bob_z, bob_x = weights
    qber = F(1, 20)
    _, docked, honest = docked_at(weights, qber)
    maps = generate_maps(docked)
    omega = state_blocks(bell_diagonal_state(lam))
    q = {c: float(honest[c]) for c in docked.acceptance_values}
    expected = bell_diagonal_objective(
        lam,
        alpha=alpha,
        p_gen=float(alice_z * bob_z),
        p_test=float(alice_x * bob_x),
        qber=float(qber),
    )
    assert objective_value(maps, q, omega, alpha) == pytest.approx(
        expected, rel=1e-11, abs=CLOSED_FORM_TOLERANCE
    )


# ===========================================================================
#  TARGET 2 -- the alpha -> 1+ limit.
# ===========================================================================


@pytest.mark.parametrize("weights", [SYMMETRIC, ASYMMETRIC])
@pytest.mark.parametrize("qber", [F(1, 50), F(1, 20), F(1, 10)])
def test_the_limit_functional_at_the_honest_state_is_the_closed_form(
    weights: tuple[F, F, F, F], qber: F
) -> None:
    """Eq. ``eq:oracle``'s summand at ``omega(Q)``, against the derivation.

    ``omega(Q)`` is Bell-diagonal with ``lambda = (1-3Q/2, Q/2, Q/2, Q/2)``, and
    the blockwise relative entropy is
    ``p_gen [1 + h2(lambda_1 + lambda_2) - H(lambda)]``.
    """
    alice_z, _, bob_z, _ = weights
    _, docked, _ = docked_at(weights, qber)
    maps = generate_maps(docked)
    expected = limit_at_depolarized_state(float(alice_z * bob_z), float(qber))
    assert limit_objective(maps, exact_state(qber)) == pytest.approx(
        expected, abs=CLOSED_FORM_TOLERANCE
    )


@pytest.mark.parametrize("weights", [SYMMETRIC, ASYMMETRIC])
@pytest.mark.parametrize("qber", [F(1, 50), F(1, 20), F(1, 10)])
def test_the_limit_program_is_minimized_at_the_pure_dephasing_state(
    weights: tuple[F, F, F, F], qber: F
) -> None:
    """``inf over Feas_1`` is ``p_gen (1 - h2(Q))``, attained at ``(1-Q, Q, 0, 0)``.

    Two claims at once, both from :func:`bb84_targets.von_neumann_limit`: the
    value at ``lambda = (1-Q, Q, 0, 0)`` IS the von-Neumann limit, and that state
    is in ``Feas_1`` -- its statistics are the honest ones, so it discharges
    (H2). Every other member of ``Feas_1`` scores higher, which the honest
    depolarized state demonstrates by scoring strictly higher.
    """
    alice_z, _, bob_z, _ = weights
    p_gen = float(alice_z * bob_z)
    _, docked, honest = docked_at(weights, qber)
    maps = generate_maps(docked)
    q = float(qber)
    minimizer = state_blocks(bell_diagonal_state((1.0 - q, q, 0.0, 0.0)))

    predicted = statistics(maps, minimizer)
    for chat in docked.acceptance_values:
        assert predicted[chat] == pytest.approx(
            float(honest[chat]), abs=CLOSED_FORM_TOLERANCE
        )
    assert limit_objective(maps, minimizer) == pytest.approx(
        von_neumann_limit(p_gen, q), abs=CLOSED_FORM_TOLERANCE
    )
    assert limit_objective(maps, exact_state(qber)) > von_neumann_limit(p_gen, q)


@pytest.mark.parametrize("weights", [SYMMETRIC, ASYMMETRIC])
def test_the_two_c16_hypotheses_hold_on_the_bb84_declaration(
    weights: tuple[F, F, F, F],
) -> None:
    """(H1) and (H2) of Theorem ``thm:oracle``, decided by ``meat-core`` itself.

    ``tests/oracles/registry.py`` records both in ``C16_EXTRA_HYPOTHESES`` and
    calls them load-bearing; here they are discharged rather than assumed. (H1)
    is the uniform floor on ``q(gen)``, which on the honest singleton is
    ``p_gen`` exactly -- and ``p_gen`` is the same number for every point of the
    declared set, because ``Phi(gen)`` is state-independent. (H2) is witnessed by
    the honest state.
    """
    alice_z, _, bob_z, _ = weights
    _, docked, _ = docked_at(weights, F(1, 20))
    maps = generate_maps(docked)
    assert maps.chat_key == ("gen",)
    floor = check_limit_hypotheses(maps, exact_state(F(1, 20)))
    assert floor == pytest.approx(float(alice_z * bob_z), abs=CLOSED_FORM_TOLERANCE)


@pytest.mark.parametrize("qber", [0.0, 0.02, 0.05, 0.10])
def test_the_reduced_program_rises_to_the_von_neumann_limit_as_alpha_falls(
    qber: float,
) -> None:
    """Monotone in ``alpha``, and with the right destination.

    The closed-form half of Target 2. It is checked here, without a solver,
    because the monotonicity is a property of the PROGRAM and not of the driver;
    the integration module then asserts the same shape of the solver's own
    ``h_low``, where a failure would mean the driver rather than the
    mathematics.
    """
    p_gen = p_test = 0.25
    values = [
        reduced_h_low_singleton(alpha=a, p_gen=p_gen, p_test=p_test, qber=qber)
        for a in (1.9, 1.5, 1.25, 1.1, 1.05, 1.01, 1.001)
    ]
    limit = von_neumann_limit(p_gen, qber)
    # NON-DECREASING everywhere and NEVER ABOVE the limit: the program's value
    # is the limit's approach from below, and at Q = 0 it SATURATES -- the last
    # two orders both return p_gen exactly, because the minimizer is t = 0 there
    # and the objective is p_gen at that point for every alpha
    # (honest_point_objective again). A strict inequality would be asserting a
    # separation that floating point does not have.
    assert all(b >= a for a, b in pairwise(values))
    assert all(value <= limit for value in values)
    assert limit - values[-1] < 2e-3
    if qber > 0.0:
        assert all(b > a for a, b in pairwise(values))
        assert values[-1] < limit
    else:
        assert values[-1] == pytest.approx(limit, abs=1e-15)


# ===========================================================================
#  TARGET 3, TARGET 4 -- the ceiling and its root, as closed forms.
# ===========================================================================


@pytest.mark.parametrize("qber", [0.0, 0.01, 0.02, 0.05, 0.08])
def test_the_ceiling_is_the_diluted_devetak_winter_rate(qber: float) -> None:
    """``p_gen (1 - 2 h2(Q))``, and the dilution is not optional.

    The undiluted ``1 - 2h2(Q)`` is the rate per SIFTED round. The rate this
    project reports is per TOTAL CHANNEL USE -- Assumption A-TSM binds the
    ``output_state`` model, so the basis choices are weights inside the POVM
    elements and the generation mass ``p_gen`` is already inside ``h_low``.
    Dividing by ``p_gen`` recovers the textbook figure, and the identity is
    asserted so that the relationship between the two is written down.
    """
    for p_gen in (0.25, float(F(21, 32))):
        ceiling = devetak_winter_ceiling(p_gen, qber)
        assert ceiling == pytest.approx(
            p_gen * (1.0 - 2.0 * binary_entropy(qber)), abs=1e-15
        )
        assert ceiling / p_gen == pytest.approx(
            1.0 - 2.0 * binary_entropy(qber), abs=1e-15
        )
    # And it is the von-Neumann limit minus the Shannon-limit leakage.
    assert devetak_winter_ceiling(0.25, qber) == pytest.approx(
        von_neumann_limit(0.25, qber) - 0.25 * binary_entropy(qber), abs=1e-15
    )


def test_the_ceiling_vanishes_at_the_textbook_crossing() -> None:
    """``Q* = 0.1100278...``, the root of ``h2(Q) = 1/2``, weight-independent."""
    assert pytest.approx(0.1100278644, abs=1e-9) == Q_STAR
    assert binary_entropy(Q_STAR) == pytest.approx(0.5, abs=1e-12)
    for p_gen in (0.25, 0.5, float(F(21, 32))):
        assert devetak_winter_ceiling(p_gen, Q_STAR) == pytest.approx(0.0, abs=1e-12)
        assert devetak_winter_ceiling(p_gen, Q_STAR - 1e-4) > 0.0
        assert devetak_winter_ceiling(p_gen, Q_STAR + 1e-4) < 0.0


# ===========================================================================
#  Why no certified run appears anywhere in this slice.
# ===========================================================================


def test_the_certificate_ambient_dimension_on_this_declaration() -> None:
    """``d_{chat,s} = 1728``, and that is why no ``certified`` BB84 run is attempted.

    Eq. ``eq:Wcs``'s ambient space is ``R XY C_A C_B A Q_s``, and on the Band-A
    BB84 declaration every factor is fixed by Definition ``def:bb84spec``:
    ``dim R = d_Z + 1 = 3``, ``dim XY = 4 * 4 = 16``,
    ``dim C_A C_B = 3 * 3 = 9``, ``dim A Q_s = 2 * 2 = 4``. The product is
    ``1728``, independent of the basis weights.

    The enclosure assembly of Proposition ``prop:budget`` evaluates a matrix
    series in ball arithmetic on operators of that size, so one series term is a
    ``1728 x 1728`` ball-matrix product at 192-bit precision. MEASURED: a
    certified request on this declaration did not complete in seven minutes and
    was stopped inside ``certiqs_key.meat_core.certificate.budget._block_horner``. The
    frozen toys, whose ambient dimensions are one to two orders of magnitude
    smaller, certify in seconds.

    Nothing is weakened to work around it: the estimate path is what this slice
    exercises, its tier is reported honestly, and the reason is legible. This
    test pins the DIMENSION so that the constraint is visible in the suite and
    so that the day it changes -- a coarser announcement alphabet, a cheaper
    enclosure -- the change is noticed here rather than inferred.
    """
    _, docked, _ = docked_at(SYMMETRIC, F(1, 20))
    for sector in docked.sector_index_set:
        assert ambient_branch_dimension(docked, sector) == AMBIENT_BRANCH_DIMENSION
    assert AMBIENT_BRANCH_DIMENSION == 1728
    assert AMBIENT_BRANCH_DIMENSION == 3 * 16 * 9 * 4
    # The dimension is the same at every weight pair: it depends on the declared
    # ALPHABETS, not on the numbers in the POVM.
    _, asymmetric, _ = docked_at(ASYMMETRIC, F(1, 20))
    assert ambient_branch_dimension(asymmetric, "s0") == AMBIENT_BRANCH_DIMENSION
    assert math.isclose(AMBIENT_BRANCH_DIMENSION / 1728.0, 1.0)
