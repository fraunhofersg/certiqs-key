"""The four analytic comparison targets of spec/architecture.md 6, derived here.

Not frozen and not a registry entry: ``tests/oracles/`` is the frozen tree and
this file is not in it. It is written in that tree's STYLE -- claim,
derivation, value -- because the reason a number is right has to travel
with the number, and a slice whose comparison points are unexplained is not a
parity check.

Every function below is a CLOSED FORM in the declaration's own quantities. None
of them calls the solver, the objective module, or anything under
``src/certiqs_key/meat``: they are the independent half of the comparison, and a
comparison whose two halves share an implementation compares nothing.

THE STRUCTURAL FACT THE WHOLE FILE RESTS ON
===========================================
For the Band-A BB84 declaration of ``protocol-compiler`` Definition
``def:bb84spec``, THREE OF THE FOUR ACCEPTANCE COORDINATES ARE THE SAME FOR EVERY
STATE. Alice's family sums basis by basis to ``sum_a M_{(b,a)} = p^A_b 1_A`` and
Bob's to ``sum_y F_{(b',y)} = p^B_{b'} 1_Q``, so

    Phi[omega](gen)  = p^A_Z p^B_Z                      for every omega,
    Phi[omega](disc) = p^A_Z p^B_X + p^A_X p^B_Z        for every omega,
    Phi[omega](ok) + Phi[omega](err) = p^A_X p^B_X      for every omega,

and the single free coordinate is the X-basis error mass. Write

    e_X(omega) = Phi[omega](err) / (p^A_X p^B_X)

for the one number a state gets to choose. The whole acceptance side of the
problem is one scalar, which is why the programs below are one- and
three-parameter and not semidefinite.

Notice what the declaration does NOT record: ``phi`` maps the entire ``(Z, Z)``
announcement class to ``gen``, so THERE IS NO Z-BASIS ERROR STATISTIC AT ALL. The
key is Alice's Z-basis bit (``key_holder = A``, ``r((Z,a), v) = a``), and what
bounds Eve's knowledge of it is the X-basis error rate -- the phase error --
exactly as in the textbook argument. The Z-basis error costs error-correction
leakage, and ``lambda_EC`` is a DECLARED parameter that no part of ``meat-core``
derives.

THE FOUR TARGETS
================
T1  ``Q = 0``   the exact, alpha-independent value of the objective at the
                honest point: :func:`honest_point_objective`.
T2  ``alpha -> 1+``  the blockwise relative-entropy program of ``meat-core``
                C16: :func:`von_neumann_limit`, with
                :func:`limit_at_depolarized_state` for the same functional at
                the honest state rather than at the infimum.
T3  Devetak-Winter  the ``n -> infinity`` ceiling on the rate per TOTAL channel
                use: :func:`devetak_winter_ceiling`.
T4  zero crossing  :data:`Q_STAR`, where that ceiling vanishes.

and, running through T1 and T2 at finite ``alpha``,
:func:`reduced_h_low_singleton` -- the one-dimensional program the full
optimization collapses to on a singleton acceptance set.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from fractions import Fraction

import numpy as np
import numpy.typing as npt

__all__ = [
    "AMBIENT_BRANCH_DIMENSION",
    "BELL_FAMILY_TOLERANCE",
    "BELL_STATES",
    "CLOSED_FORM_TOLERANCE",
    "Q_STAR",
    "SOLVER_TOLERANCE",
    "bell_diagonal_objective",
    "bell_diagonal_state",
    "binary_entropy",
    "binary_kl",
    "devetak_winter_ceiling",
    "honest_phi",
    "honest_point_objective",
    "limit_at_depolarized_state",
    "minimize_unimodal",
    "reduced_h_low_singleton",
    "reduced_objective_singleton",
    "renyi_pair_entropy",
    "shannon_entropy",
    "von_neumann_limit",
]


# ===========================================================================
#  Tolerances. Each is a named constant with the measurement that justifies it.
# ===========================================================================

#: Agreement between a Frank-Wolfe ``h_low`` and the closed form it should
#: reach. JUSTIFICATION, measured rather than assumed: over the whole comparison
#: grid of this file -- two weight pairs, ``Q in {1/50, 1/20}``,
#: ``alpha in {1.01, 1.05, 1.1, 1.25, 1.5, 1.9}`` -- the largest observed
#: ``h_low - reduced_h_low_singleton`` was ``6.9e-9``, at ``alpha = 1.01`` where
#: the ``alpha/(alpha-1)`` prefactor is 101 and the driver's residual is
#: correspondingly amplified. The bar is one order above that.
SOLVER_TOLERANCE = 1e-8

#: Agreement between two evaluations of the SAME closed form -- one by the
#: formula here, one by ``meat-core``'s own machinery on the compiled
#: declaration. Nothing is optimized on either side, so the only error is
#: floating-point: a handful of ``log2``/``exp`` calls and one 16x16
#: eigendecomposition, whose accumulated rounding is at the level of a few
#: hundred ulp of a quantity of order one. Measured deviations were below
#: ``2e-14``; the bar is ``1e-12``.
CLOSED_FORM_TOLERANCE = 1e-12

#: How far a golden-section search on the one-dimensional program of
#: :func:`reduced_h_low_singleton` is trusted. 300 golden-section iterations
#: shrink a bracket of width ``1/2`` by ``0.618^300``, i.e. far below the
#: floating-point resolution of the objective; the residual is the objective's
#: own conditioning near a flat minimum, ``~1e-12``.
BELL_FAMILY_TOLERANCE = 1e-12


# ===========================================================================
#  T0 -- the honest distribution.
# ===========================================================================


def honest_phi(
    alice_z: Fraction,
    alice_x: Fraction,
    bob_z: Fraction,
    bob_x: Fraction,
    qber: Fraction,
) -> dict[str, Fraction]:
    """Return ``Phi_D[omega(Q)]`` on ``(gen, ok, err, disc)``, exactly.

    CLAIM.  For the Band-A BB84 declaration at basis weights
    ``(p^A_Z, p^A_X, p^B_Z, p^B_X)`` and the depolarized honest state
    ``omega(Q) = v |Phi^+><Phi^+| + (1-v) 1/4`` with ``v = 1 - 2Q``,

        Phi(gen)  = p^A_Z p^B_Z
        Phi(ok)   = p^A_X p^B_X (1 - Q)
        Phi(err)  = p^A_X p^B_X Q
        Phi(disc) = p^A_Z p^B_X + p^A_X p^B_Z .

    DERIVATION.  The emitted elements are ``M_{(b,a)} = p^A_b |conj(a^b)><conj(a^b)|``
    and ``F_{(b',y)} = p^B_{b'} |y^{b'}><y^{b'}|`` (Eq. ``eq:bb84data``).  Write
    the joint probability of Eq. ``eq:jointdist`` at ``omega(Q)`` as the two
    terms of the mixture:

    * on ``|Phi^+> = (|00> + |11>)/sqrt2``, the amplitude
      ``(<conj(a)| (x) <y|) |Phi^+> = <y|a> / sqrt2``.  (This is where the
      conjugation earns its keep: it is what makes the source-replacement
      measurement PREPARE ``|a^b>`` rather than its conjugate.)  So the term is
      ``p^A_b p^B_{b'} v |<y^{b'}|a^b>|^2 / 2``;
    * on ``1/4`` it is ``p^A_b p^B_{b'} (1 - v) / 4``, because
      ``tr[(|a><a| (x) |y><y|) 1/4] = 1/4``.

    In a MATCHED basis ``|<y^b|a^b>|^2 = delta_{a,y}``, giving
    ``p^A_b p^B_b (1-Q)/2`` when ``a = y`` and ``p^A_b p^B_b Q/2`` when
    ``a != y`` (using ``(1+v)/4 = (1-Q)/2`` and ``(1-v)/4 = Q/2``).  In a
    MISMATCHED basis ``|<y^{b'}|a^b>|^2 = 1/2`` and both terms collapse to
    ``p^A_b p^B_{b'} / 4``, independent of ``Q``.

    Summing over the fibres of ``phi`` (Definition ``def:bb84spec``: the
    ``(Z,Z)`` class is ``gen``; two ``(X,*)`` classes are ``ok`` when the
    announced outcomes agree and ``err`` when they do not; every mixed class is
    ``disc``) gives the four values above:
    ``gen`` sums four matched Z cells, ``2 (1-Q)/2 + 2 Q/2 = 1``, times
    ``p^A_Z p^B_Z``; ``ok`` sums the two agreeing X cells; ``err`` the two
    disagreeing ones; ``disc`` the eight mismatched cells,
    ``4 p^A_Z p^B_X / 4 + 4 p^A_X p^B_Z / 4``.

    VALUE.  At ``Q = 0`` and symmetric weights this is ``(1/4, 1/4, 0, 1/2)``,
    which is the frozen ``phi_vector`` of ``BB84-w1-symmetric-dyadic``; at
    ``(7/8, 1/8) x (3/4, 1/4)`` it is ``(21/32, 1/32, 0, 5/16)`` and at
    ``(2/3, 1/3) x (4/5, 1/5)`` it is ``(8/15, 1/15, 0, 2/5)`` -- the other two
    frozen rows.
    """
    return {
        "gen": alice_z * bob_z,
        "ok": alice_x * bob_x * (1 - qber),
        "err": alice_x * bob_x * qber,
        "disc": alice_z * bob_x + alice_x * bob_z,
    }


# ===========================================================================
#  T1 -- Q = 0, the exact objective at the honest point.
# ===========================================================================


def honest_point_objective(alice_z: Fraction, bob_z: Fraction) -> Fraction:
    """Return ``O_alpha`` at the ``Q = 0`` honest point: ``p^A_Z p^B_Z``, exactly.

    CLAIM.  On the Band-A BB84 declaration, at ``q = Phi[omega(0)]`` and
    ``omega = omega(0) = |Phi^+><Phi^+|``,

        O_alpha(q, omega) = p^A_Z p^B_Z          for EVERY alpha in (1, inf).

    Exact, rational, and independent of the Renyi order.

    DERIVATION.  ``Chat_key = {gen}``: sifting passes the ``(Z,Z)`` class alone
    (Definition ``def:bb84spec``), and ``gen`` is the only acceptance value that
    class maps to.  Eq. ``eq:objective`` therefore reads

        O_alpha = (alpha/(alpha-1)) [ d(q_ok,P_ok) + d(q_err,P_err) + d(q_disc,P_disc) ]
                  + d(q_gen, P_gen) + d(q_gen, K_gen)/(alpha-1) .

    (i) THE FOUR ``d(q, P)`` TERMS VANISH.  ``q = Phi[omega]`` by construction,
    and ``d(u, u) = u log2(u/u) = 0``; at ``Q = 0`` the ``err`` term is
    ``d(0, 0) = 0`` by the kernel's own convention.

    (ii) ``K_gen = 2^{1-alpha} p^A_Z p^B_Z``.  The branch Kraus operator of the
    ``(Z,Z)`` class stacks the row blocks ``sqrt(M_{(Z,a)}) (x) sqrt(F_{(Z,y)})``
    over the four pairs ``(a, y)``, and

        (sqrt(M_{(Z,a)}) (x) sqrt(F_{(Z,y)})) |Phi^+>
            = sqrt(p^A_Z p^B_Z) delta_{a,y} |aa> / sqrt2 ,

    so ``G_gen = |w><w|`` is RANK ONE, supported on the two rows ``(0,0)`` and
    ``(1,1)`` with equal weight ``p^A_Z p^B_Z / 2`` each and
    ``||w||^2 = p^A_Z p^B_Z``.  Writing ``p = p^A_Z p^B_Z``:
    ``G^{1/alpha} = p^{1/alpha} |w><w| / ||w||^2``, whose diagonal in the two
    rows is ``p^{1/alpha}/2`` twice.  The pinching ``Z`` keeps exactly that
    diagonal, because the two rows carry the raw-key values ``r = 0`` and
    ``r = 1``.  Hence

        T_gen = tr[(Z(G^{1/alpha}))^alpha] = 2 (p^{1/alpha}/2)^alpha
              = 2^{1-alpha} p .

    Eq. ``eq:fK`` gives ``K = T + P - tr G``, and here ``P_gen = tr G_gen = p``
    (the ``gen`` fibre IS the pass class), so ``K_gen = T_gen``.

    (iii) THE LAST TERM IS ``p``.  ``d(q_gen, K_gen)/(alpha-1)
    = p log2(p / (2^{1-alpha} p)) / (alpha-1) = p (alpha-1)/(alpha-1) = p``.

    Every alpha-dependence cancels between the ``2^{1-alpha}`` inside the
    logarithm and the ``1/(alpha-1)`` outside it, which is why the value is a
    rational number and not merely a real one.

    WHAT THIS IS AND IS NOT.  It is the objective AT A FEASIBLE POINT, so by
    contract Section 4.15 it bounds ``h_low`` from ABOVE and never from below.
    It is not ``h_low(0)``, and ``h_low`` at ``Q = 0`` is strictly smaller for
    every finite alpha: :func:`reduced_h_low_singleton` at ``Q = 0`` finds a
    Bell-diagonal state whose Renyi-order trade -- an infinite-slope gain in
    ``K_gen`` against a linear-slope loss in ``d(q_ok, P_ok)`` -- pays.  The two
    agree only in the limit ``alpha -> 1+``, where
    :func:`von_neumann_limit` at ``Q = 0`` is ``p (1 - h2(0)) = p``.
    """
    return alice_z * bob_z


# ===========================================================================
#  Entropies. Written out because they are the whole content of T2-T4.
# ===========================================================================


def binary_entropy(x: float) -> float:
    """Return ``h2(x) = -x log2 x - (1-x) log2(1-x)``, in bits."""
    if x <= 0.0 or x >= 1.0:
        return 0.0
    return -x * math.log2(x) - (1.0 - x) * math.log2(1.0 - x)


def shannon_entropy(weights: Sequence[float]) -> float:
    """Return ``H(p) = -sum p log2 p``, in bits, over a finite distribution."""
    return -math.fsum(w * math.log2(w) for w in weights if w > 0.0)


def binary_kl(p: float, q: float) -> float:
    """Return ``D(p || q)`` for two Bernoulli distributions, in bits.

    ``+inf`` where ``p`` puts mass on an outcome ``q`` does not, which is the
    same extended-real convention ``meat-core``'s kernel uses and is what makes
    the ``alpha -> 1+`` limit of :func:`reduced_objective_singleton` pin
    ``t = Q``.
    """
    total = 0.0
    for a, b in ((p, q), (1.0 - p, 1.0 - q)):
        if a > 0.0:
            if b <= 0.0:
                return math.inf
            total += a * math.log2(a / b)
    return total


def renyi_pair_entropy(t: float, alpha: float) -> float:
    """Return ``H_{1/alpha}({t, 1-t})``, the Renyi entropy of order ``1/alpha``.

    ``H_beta(p) = (1/(1-beta)) log2 sum_i p_i^beta`` at ``beta = 1/alpha``, so
    with ``beta < 1`` for every ``alpha > 1``:

        H_{1/alpha}({t, 1-t})
            = (alpha/(alpha-1)) log2( t^{1/alpha} + (1-t)^{1/alpha} ) .

    It appears in :func:`reduced_objective_singleton` because the ``K_gen`` of a
    Bell-diagonal state is exactly ``2^{1-alpha} p_gen`` times the quantity whose
    logarithm this is -- see that function's derivation -- and it decreases to
    ``h2(t)`` as ``alpha -> 1+``.
    """
    beta = 1.0 / alpha
    return (alpha / (alpha - 1.0)) * math.log2(t**beta + (1.0 - t) ** beta)


# ===========================================================================
#  The Bell-diagonal reduction, and the one-dimensional program.
# ===========================================================================

#: The four Bell states on ``A (x) Q``, with the ``A`` factor FIRST -- the
#: subsystem order contract Section 2.5 fixes and
#: :mod:`certiqs_key.protocol_compiler.statistics` reads. In the order
#: ``(Phi^+, Phi^-, Psi^+, Psi^-)``, which is the order every ``lambda`` in this
#: file is written in.
BELL_STATES: tuple[tuple[float, ...], ...] = (
    (1.0, 0.0, 0.0, 1.0),
    (1.0, 0.0, 0.0, -1.0),
    (0.0, 1.0, 1.0, 0.0),
    (0.0, 1.0, -1.0, 0.0),
)


def bell_diagonal_state(
    weights: Sequence[float],
) -> npt.NDArray[np.complex128]:
    """Return the Bell-diagonal state with the given weights, as a ``4 x 4`` array.

    Every state in this family has ``omega_A = 1_A/2``, which is the ``tau_A``
    the BB84 declaration emits, so the whole family lies in the feasible set of
    Eq. ``eq:feas`` -- and the depolarized honest state
    ``omega(Q) = v |Phi^+><Phi^+| + (1-v)1/4`` is its member at
    ``lambda = (1 - 3Q/2, Q/2, Q/2, Q/2)``.
    """
    out = np.zeros((4, 4), dtype=np.complex128)
    for weight, amplitudes in zip(weights, BELL_STATES, strict=True):
        vector = np.asarray(amplitudes, dtype=np.complex128) / math.sqrt(2.0)
        out += float(weight) * np.outer(vector, vector.conj())
    return out


def bell_diagonal_objective(
    weights: Sequence[float],
    *,
    alpha: float,
    p_gen: float,
    p_test: float,
    qber: float,
) -> float:
    """Return ``O_alpha`` at a Bell-diagonal state, on a SINGLETON acceptance set.

    CLAIM.  Let ``omega`` be Bell-diagonal with weights
    ``lambda = (lambda_{Phi+}, lambda_{Phi-}, lambda_{Psi+}, lambda_{Psi-})``, let
    ``p_gen = p^A_Z p^B_Z``, ``p_test = p^A_X p^B_X``, and let the acceptance set
    be the singleton at the honest distribution of :func:`honest_phi`. Then,
    with ``beta = 1/alpha`` and

        S(lambda) = (lambda_1^beta + lambda_2^beta)^alpha
                  + (lambda_3^beta + lambda_4^beta)^alpha ,

        O_alpha(lambda) = (alpha/(alpha-1)) p_test D(Q || lambda_2 + lambda_4)
                        + p_gen [ 1 - log2 S(lambda) / (alpha - 1) ] .

    DERIVATION, in four steps.

    (1) FEASIBILITY IS FREE.  Every Bell-diagonal state has ``omega_A = 1_A/2``,
    which is the emitted ``tau_A``; the Band-A constraint list is empty
    (Definition ``def:bandA``).  So the whole family lies in ``W``.

    (2) THE STATISTICS.  ``Phi(gen)`` and ``Phi(disc)`` are state-independent
    (see the module docstring), so their ``d(q, P)`` terms vanish at the honest
    singleton.  In the X basis ``|Phi^+>`` and ``|Psi^+>`` are correlated and
    ``|Phi^-> , |Psi^->`` anti-correlated, so
    ``e_X = lambda_2 + lambda_4``, giving
    ``P_ok = p_test (1 - e_X)`` and ``P_err = p_test e_X``.  With
    ``q_ok = p_test(1-Q)`` and ``q_err = p_test Q`` the two surviving
    non-key terms sum to ``p_test D(Q || e_X)``, the binary relative entropy.

    (3) THE KEY TERM.  In the ``(Z,Z)`` branch the four output rows are indexed
    by ``(a, y)`` and carry the raw-key label ``a``.  ``|Phi^{+-}>`` populate the
    rows ``(0,0)`` and ``(1,1)``; ``|Psi^{+-}>`` populate ``(0,1)`` and ``(1,0)``.
    So ``G_gen`` is block diagonal with two 2x2 blocks,

        p_gen/2 [[ l1+l2, l1-l2 ], [ l1-l2, l1+l2 ]]   on rows (0,0), (1,1),
        p_gen/2 [[ l3+l4, l3-l4 ], [ l3-l4, l3+l4 ]]   on rows (0,1), (1,0),

    whose eigenvalues are ``p_gen lambda_i`` with eigenvectors the symmetric and
    antisymmetric combinations.  In BOTH blocks the two rows carry DIFFERENT
    key labels (``(0,0)`` and ``(0,1)`` are labelled 0; ``(1,1)`` and ``(1,0)``
    are labelled 1), so the pinching ``Z`` deletes both off-diagonals, leaving
    ``Z(G^{1/alpha})`` diagonal with entries
    ``p_gen^{beta}(lambda_1^beta + lambda_2^beta)/2`` twice and
    ``p_gen^{beta}(lambda_3^beta + lambda_4^beta)/2`` twice.  Raising to the
    ``alpha`` and tracing gives ``T_gen = 2^{1-alpha} p_gen S(lambda)``, and
    ``K_gen = T_gen`` as in :func:`honest_point_objective`.

    (4) ASSEMBLY.  ``d(q_gen, K_gen)/(alpha-1)`` with ``q_gen = p_gen`` is
    ``p_gen [ (alpha-1) - log2 S ] / (alpha - 1)``, which is the second line.

    A CHECK BUILT IN.  At ``lambda = (1, 0, 0, 0)`` and ``Q = 0``, ``S = 1`` and
    ``D(0||0) = 0``, so the value is ``p_gen`` -- :func:`honest_point_objective`
    again, reached by a different route.
    """
    lam = tuple(float(w) for w in weights)
    if len(lam) != 4:
        raise ValueError("a Bell-diagonal state has four weights")
    beta = 1.0 / alpha
    total = 0.0
    for pair in (lam[0:2], lam[2:4]):
        if pair[0] > 0.0 or pair[1] > 0.0:
            total += (pair[0] ** beta + pair[1] ** beta) ** alpha
    error = lam[1] + lam[3]
    return (alpha / (alpha - 1.0)) * p_test * binary_kl(qber, error) + p_gen * (
        1.0 - math.log2(total) / (alpha - 1.0)
    )


def reduced_objective_singleton(
    t: float, *, alpha: float, p_gen: float, p_test: float, qber: float
) -> float:
    """Return :func:`bell_diagonal_objective` on the family ``(1-t, t, 0, 0)``.

    CLAIM.  With ``lambda_3 = lambda_4 = 0`` the expression collapses to

        O_alpha(t) = (alpha/(alpha-1)) p_test D(Q || t)
                   + p_gen [ 1 - H_{1/alpha}({t, 1-t}) ] ,

    and the minimum of ``O_alpha`` over the WHOLE Bell-diagonal simplex is
    attained on this one-parameter family.

    DERIVATION of the collapse: at ``lambda_3 = lambda_4 = 0`` the second
    summand of ``S`` is ``0``, so
    ``log2 S / (alpha-1) = alpha log2(t^beta + (1-t)^beta)/(alpha-1)``, which is
    :func:`renyi_pair_entropy` verbatim.

    WHY THE FAMILY IS ENOUGH -- and how far that is checked.  Mass on
    ``lambda_3`` or ``lambda_4`` buys the adversary nothing: ``lambda_4`` costs
    the same error budget as ``lambda_2`` while contributing
    ``(lambda_3^beta + lambda_4^beta)^alpha`` in place of pooling with
    ``lambda_1``, and at ``lambda_3 = 0`` that term is just ``lambda_4``, i.e.
    ``S <= 1``; ``lambda_3`` costs no error budget but splits ``S`` into two
    strictly sub-additive pieces.  A scan of the full three-dimensional simplex
    at ``alpha = 1.5``, ``Q = 0.02`` on a 1/90 grid found its minimum at
    ``lambda_3 = lambda_4 = 0``, and every solver run this file is compared
    against agrees with the family value to ``7e-9`` or better -- which is the
    real check, since the solver optimizes over ALL feasible states and not only
    the Bell-diagonal ones.  The claim is stated as what it is: a reduction whose
    optimality is checked numerically and against the solver, not proved here.
    """
    return bell_diagonal_objective(
        (1.0 - t, t, 0.0, 0.0),
        alpha=alpha,
        p_gen=p_gen,
        p_test=p_test,
        qber=qber,
    )


def minimize_unimodal(
    function: object, low: float, high: float, iterations: int = 300
) -> tuple[float, float]:
    """Return ``(minimum, argmin)`` of a unimodal function by golden section.

    Written out rather than imported so that the independent half of every
    comparison stays independent: SciPy is not a dependency of this repository,
    and the driver's own line search is the thing being checked.
    """
    call = function  # type: ignore[assignment]
    golden = 0.5 * (math.sqrt(5.0) - 1.0)
    left = high - golden * (high - low)
    right = low + golden * (high - low)
    f_left = call(left)  # type: ignore[operator]
    f_right = call(right)  # type: ignore[operator]
    for _ in range(iterations):
        if f_left <= f_right:
            high, right, f_right = right, left, f_left
            left = high - golden * (high - low)
            f_left = call(left)  # type: ignore[operator]
        else:
            low, left, f_left = left, right, f_right
            right = low + golden * (high - low)
            f_right = call(right)  # type: ignore[operator]
    if f_left <= f_right:
        return f_left, left
    return f_right, right


def reduced_h_low_singleton(
    *, alpha: float, p_gen: float, p_test: float, qber: float
) -> float:
    """Return ``min_t`` of :func:`reduced_objective_singleton` -- ``h_low``.

    The bracket is ``[0, 1/2]``.  The left end is included and costs nothing:
    ``D(Q || 0) = +inf`` for ``Q > 0``, so the search is pushed off it
    automatically, while at ``Q = 0`` the value there is exactly ``p_gen`` --
    :func:`honest_point_objective` -- and excluding it would leave the minimum
    reported as ``p_gen`` plus whatever the excluded endpoint's neighbourhood
    happens to add.  The right end is ``1/2`` because ``H_{1/alpha}`` is maximal
    there and ``D(Q || t)`` increases beyond it, so no minimizer lies above.
    """

    def evaluate(t: float) -> float:
        return reduced_objective_singleton(
            t, alpha=alpha, p_gen=p_gen, p_test=p_test, qber=qber
        )

    value, _ = minimize_unimodal(evaluate, 0.0, 0.5)
    return min(value, evaluate(0.0))


# ===========================================================================
#  T2 -- the alpha -> 1+ limit.
# ===========================================================================


def von_neumann_limit(p_gen: float, qber: float) -> float:
    """Return ``lim_{alpha -> 1+} h_low`` on a singleton acceptance set.

    CLAIM.  ``lim_{alpha -> 1+} h_low(alpha) = p_gen (1 - h2(Q))``.

    DERIVATION, twice over, which is what makes it a target rather than a guess.

    ONE.  From :func:`reduced_objective_singleton`.  As ``alpha -> 1+``,
    ``H_{1/alpha}({t,1-t}) -> h2(t)`` and the prefactor ``alpha/(alpha-1)``
    diverges, so any ``t != Q`` sends the first term to ``+infinity``: the limit
    program is ``min`` over ``t = Q`` alone of ``p_gen (1 - h2(t))``.

    TWO.  From ``meat-core`` C16, Eq. ``eq:oracle``, which states the limit
    independently as ``inf over Feas_1`` of
    ``sum_chat sum_s D(G_{chat,s} || Z(G_{chat,s}))``.  For a Bell-diagonal
    ``omega``, ``G_gen / p_gen`` is a state with spectrum ``lambda`` and its
    pinching has spectrum ``((l1+l2)/2, (l1+l2)/2, (l3+l4)/2, (l3+l4)/2)``, so

        D(G || Z(G)) = p_gen [ H(Z(sigma)) - H(sigma) ]
                     = p_gen [ 1 + h2(lambda_1 + lambda_2) - H(lambda) ] .

    ``Feas_1`` at the honest singleton is ``{lambda : lambda_2 + lambda_4 = Q}``,
    and on it the expression is minimized at ``lambda = (1-Q, Q, 0, 0)``: the
    derivative in ``lambda_3`` at ``lambda_3 = 0`` is
    ``log2((1-u)/(1-Q-u))`` at ``u = 0``, which is ``0`` from below and positive
    thereafter.  The value there is ``p_gen [1 + h2(1) - h2(Q)]
    = p_gen (1 - h2(Q))``.

    HYPOTHESES.  Theorem ``thm:oracle`` carries two that Remark ``rem:oracle``
    does not repeat, and both hold here: (H1) the uniform floor is
    ``p_0 = p_gen > 0``, since ``q(gen) = p_gen`` for every point of the declared
    set; (H2) ``Feas_1`` is nonempty, witnessed by the honest state itself.
    Both are checked against ``meat-core``'s own
    :func:`~certiqs_key.meat_core.objective.limit.check_limit_hypotheses` rather than
    asserted.
    """
    return p_gen * (1.0 - binary_entropy(qber))


def limit_at_depolarized_state(p_gen: float, qber: float) -> float:
    """Return Eq. ``eq:oracle``'s functional AT the honest state, not at its infimum.

    CLAIM.  ``sum_chat sum_s D(G || Z(G))`` evaluated at ``omega(Q)`` is

        p_gen [ 1 + h2(Q) - H(1 - 3Q/2, Q/2, Q/2, Q/2) ] .

    DERIVATION.  ``omega(Q) = v |Phi^+><Phi^+| + (1-v)1/4`` with ``v = 1-2Q`` is
    Bell-diagonal with ``lambda = (1 - 3Q/2, Q/2, Q/2, Q/2)`` -- the identity
    contributes ``(1-v)/4 = Q/2`` to each of the four Bell states and the
    projector adds ``v`` to the first.  Substituting into the second derivation
    of :func:`von_neumann_limit`, ``lambda_1 + lambda_2 = 1 - Q``, so the
    bracket is ``1 + h2(1-Q) - H(lambda) = 1 + h2(Q) - H(lambda)``.

    WHY IT IS HERE.  Because it is STRICTLY LARGER than
    :func:`von_neumann_limit` for every ``Q > 0``: the depolarized honest state
    is not the state that minimizes the limit program, and a test that compared
    the solver's limit against the honest state's value would be comparing
    against the wrong number.  At ``Q = 1/50`` and ``p_gen = 1/4`` the two are
    ``0.2248749524`` and ``0.2146398644``.  The distinction is exactly the
    difference between evaluating a program and solving it.
    """
    q = float(qber)
    weights = (1.0 - 1.5 * q, q / 2.0, q / 2.0, q / 2.0)
    return p_gen * (1.0 + binary_entropy(1.0 - q) - shannon_entropy(weights))


# ===========================================================================
#  T3, T4 -- the Devetak-Winter ceiling and where it vanishes.
# ===========================================================================


def devetak_winter_ceiling(p_gen: float, qber: float) -> float:
    """Return the ``n -> infinity`` ceiling on the key rate PER TOTAL CHANNEL USE.

    CLAIM.  ``lim sup_n l(n)/n <= p_gen (1 - 2 h2(Q))``, with
    ``p_gen = p^A_Z p^B_Z``.  THE CEILING IS DILUTED BY THE SIFTING FACTOR, and
    the undiluted ``1 - 2h2(Q)`` is the rate per SIFTED round, not per channel
    use.

    DERIVATION.  Eq. ``eq:keylength`` divided by ``n``:

        l/n = h_low - lambda_EC/n - ceil(log2(1/eps_EV))/n
              - (alpha/(alpha-1)) log2(1/eps_PA)/n + 1/n .

    Three inputs.  (a) ``h_low(alpha) <= lim_{alpha -> 1+} h_low
    = p_gen (1 - h2(Q))`` on the honest singleton, by
    :func:`von_neumann_limit`; and the acceptance POLYTOPE of a finite run
    contains that singleton, so its infimum is no larger.  (b) At the Shannon
    limit the error-correction transcript for the sifted key is
    ``lambda_EC = ceil(n p_gen h2(Q))`` bits: ``n p_gen`` rounds land in the
    ``(Z,Z)`` class and each costs ``h2(Q)`` bits to reconcile.  ``lambda_EC`` is
    a DECLARED parameter that ``meat-core`` never derives, so this is a choice
    the caller makes and the ceiling is a statement about that choice.  (c) The
    two epsilon terms and the ``+1`` are ``O(1/n)`` and vanish.

    Together: ``l/n <= p_gen(1 - h2(Q)) - p_gen h2(Q) + O(1/n)``.

    WHY THE DILUTION IS NOT OPTIONAL HERE.  Assumption A-TSM binds the
    ``output_state`` test-statistics model, so every per-round public choice --
    the basis choices among them -- enters as a WEIGHT INSIDE the POVM elements
    and never as a state-independent fraction applied afterwards.  The declared
    statistics are therefore per total channel use throughout
    (spec/architecture.md 4.3: "total channel uses, not merely sifted
    detections"), ``n`` in Eq. ``eq:keylength`` counts channel uses, and the
    generation mass ``p_gen`` is already inside ``h_low``.  Multiplying by
    ``1/p_gen`` at the end to recover the textbook figure is a presentation
    step; doing it INSIDE the comparison would compare two different quantities.

    THE INEQUALITY IS STRICT AT EVERY FINITE ``n``, on three counts at once: the
    acceptance polytope is strictly larger than the honest singleton, the
    admissible ``alpha`` is bounded away from 1 by ``eps_PA``'s cost, and the
    ``O(1/n)`` terms are positive deductions.  So a test asserts an ENVELOPE and
    an approach, never an equality.
    """
    return p_gen * (1.0 - 2.0 * binary_entropy(qber))


def _zero_crossing() -> float:
    """Return the ``Q`` at which ``1 - 2 h2(Q)`` vanishes, by bisection."""
    low, high = 0.0, 0.5
    for _ in range(200):
        middle = 0.5 * (low + high)
        if binary_entropy(middle) < 0.5:
            low = middle
        else:
            high = middle
    return 0.5 * (low + high)


#: ``Q*``: the error rate at which the Devetak-Winter ceiling of
#: :func:`devetak_winter_ceiling` reaches zero, i.e. the root of
#: ``h2(Q) = 1/2``.  ``0.1100278644...``, and INDEPENDENT of the basis weights:
#: ``p_gen`` multiplies the ceiling and cannot move its root.  The textbook
#: figure for one-way BB84 with a symmetric depolarizing channel, quoted as
#: ``approx 0.11`` in spec/architecture.md 6.
Q_STAR = _zero_crossing()


# ===========================================================================
#  The certificate's ambient dimension on this declaration.
# ===========================================================================

#: ``d_{chat,s} = dim H(R XY C_A C_B A Q_s)`` of ``meat-core`` Eq. ``eq:Wcs``,
#: for the Band-A BB84 declaration.  Factor by factor, from the DECLARED
#: alphabets: ``dim R = d_Z + 1 = 3``; ``dim XY = |X| |V| = 4 * 4 = 16``;
#: ``dim C_A C_B = |C_A| |C_B| = 3 * 3 = 9`` (the announcements ``Z``, ``(X,0)``
#: and ``(X,1)`` on each side); ``dim A Q_s = d_A d_s = 2 * 2 = 4``.  Product:
#: ``3 * 16 * 9 * 4 = 1728``, and it does not depend on the basis weights.
#:
#: It is recorded here because it is the reason no ``certified`` run appears in
#: this slice's tests: the enclosure assembly of ``prop:budget`` evaluates a
#: matrix series in interval arithmetic on operators of this size, and a
#: ``1728 x 1728`` ball-matrix product per series term is out of reach where the
#: frozen toys' handful-of-dimensions products are not.  Measured: no certified
#: BB84 run completed in seven minutes, stopped inside ``_block_horner``.
AMBIENT_BRANCH_DIMENSION = 3 * (4 * 4) * (3 * 3) * (2 * 2)


def honest_floats(distribution: Mapping[str, Fraction]) -> tuple[float, ...]:
    """Return an exact honest distribution as floats, in ``(gen, ok, err, disc)``."""
    return tuple(float(distribution[c]) for c in ("gen", "ok", "err", "disc"))
