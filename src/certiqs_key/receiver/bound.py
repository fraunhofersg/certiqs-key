"""The high-photon multiclick bounds -- thm:multiclick-bound and thm:emitted-bound.

This is the module's one quantitative deliverable and the place where an error
would propagate furthest: what a weight-preserving squasher consumes is a
lower bound on the smallest eigenvalue of the multiclick element, valid on
EVERY photon-number block above the declared cutoff -- ONE PER DECLARED PROBE
SETTING, each guaranteed at its own setting (Theorem ``thm:emitted-bound``,
Eq. ``eq:pmcsetting``), together with their minimum, guaranteed at every
setting (Eq. ``eq:pmcstatement``).

THE PER-SETTING WEIGHTS ARE THE GUARANTEED CONTENT
==================================================
Theorem ``thm:emitted-bound`` states ``blk M^{(>N)}_{mc|t} >= p_mc^(t) 1`` at
every setting as its first conclusion, and Definition ``def:slot`` carries one
weight per entry and setting: :func:`emitted_weights` is that conclusion and
:func:`emitted_weight` the minimum it implies. At a probe-free receiver
``T = {off}`` and the two are one number.

    beta(n) = 1 + (K - 1) gamma c^n - sum_k beta_k d_k^n ,  with 0^0 = 1
                                                            (Eq. eq:beta)
    c = 1 - lmax(B) ,  d_k = 1 - lmin(B_k)                  (Eq. eq:cd)

Theorem ``thm:multiclick-bound`` gives ``lmin(blk M_mc^{(=n)}) >= beta(n)`` under
Eq. ``eq:bbkhyp`` (``0 <= B_k <= B <= 1``) and ``gamma <= beta_k``, and both
hypotheses hold at every setting of a setting family (Definition
``def:setting-family`` (b)): at the unconditioned receiver with
``gamma = beta_k = 1`` (Theorem ``thm:port-grams`` (i), Corollary
``cor:unconditioned-family``), and at a setting family a submodule constructs
because that submodule proves it is one.

THE QUANTIFIER IS THE WORK, NOT THE BOUND
=========================================
What the consumer needs is ``inf_{n > N} beta(n)``, and a squashing request
whose bounds are not uniform over ALL photon numbers above the cutoff fails
(spec/architecture.md section 5.4; the lead-in of Lemma ``lem:collapse``).
``beta`` is not monotone in general -- it is a non-increasing term plus a
non-decreasing one -- so the infimum is discharged by one of two branches:

* BRANCH 1, Lemma ``lem:collapse``: under Eq. ``eq:collapsehyp``
  (``beta(0) <= 0``) the infimum is ATTAINED at the first index above the
  cutoff, exactly: ``max{0, inf_{n>N} beta(n)} = max{0, beta(N+1)}``;
* BRANCH 2, Lemma ``lem:windowtail``: a window minimum and a tail, valid for
  EVERY admissible bound data with NO hypothesis at all, monotone in the window
  and convergent for ``c < 1``.

The selector is predicate (X) of Definition ``def:pmc``, and where it fails
the value comes from branch 2, WHICH IS UNCONDITIONALLY VALID (Remark
``rem:pmc-branch-choice``).

(X) ALONE SELECTS BRANCH 1
==========================
Predicate (X) is the setting's exact flag (Definition ``def:setting-family``
(c)) -- at the two instances this module constructs, ``Inp_S`` empty or
``Gamma^(t) = 0`` -- decided ON THE DECLARATION before any arithmetic; branch 2,
valid for every admissible bound data with no hypothesis (Lemma
``lem:windowtail`` (i)), serves every other setting. There is no computed
companion to (X) and no declared margin among the inputs (Remark
``rem:pmc-branch-choice``).

:func:`collapse_slack` IS A DIAGNOSTIC AND NOTHING ELSE. It is the quantity
``sigma = sum_k beta_k - 1 - (K-1) gamma`` of Eq. ``eq:collapsehyp``, which
Remark ``rem:noslack`` proves equals ``-beta(0)`` and is therefore ``<= 0`` at
every receiver, every setting and every parameter value: ``beta(0)`` is the
channel-vacuum block of the multiclick element, a diagonal block of a positive
operator and hence a NON-NEGATIVE REAL, so Eq. ``eq:collapsehyp`` holds IF AND
ONLY IF ``beta(0) = 0`` exactly. No branch consults it, no refusal turns on it,
and no declared margin exists for it to be compared against.

A NON-STRICT companion test ``|beta(0)| <= eps`` would be a change of
mathematical substance and is not made. Its absence costs tightness and never
safety: branch 2 recovers branch 1's value in the limit of a widening window
whenever ``c < 1`` (Remark ``rem:noslack``, its last paragraph).

WHAT THE BRANCH RECORD CARRIES
==============================
``interface.yaml`` ``outputs.bound_quantifier_domain`` asks, per setting, for
which branch of Definition ``def:pmc`` was taken -- BRANCH 1 EXACTLY WHERE
PREDICATE (X) HOLDS -- and the declared window ``m_t`` where branch 2 was, and
its ``one_predicate_note`` makes (X) the only predicate to report. So
:class:`SettingBound` carries the branch, ``(X)`` and the window, and NOT a
selecting-predicate field or a margin. The branch record and the value of (X)
at that setting determine each other: a biconditional rather than a default.

THE EXACT WINDOW, AND IT IS OPT-IN
==================================
Eq. ``eq:mcbound`` bounds three operators separately and is therefore slack --
and at the cutoffs a caller actually wants it can be VACUOUS. On the worked
BB84 receiver ``beta(n) = 1 - 2^{2-n}``, so at the cutoff ``N = 1`` Eq.
``eq:pmcdef`` emits ``p_mc = 0`` while the exact minimum eigenvalue of the
two-photon block OF THAT SAME DEVICE IS 1/2 (Examples ``ex:bb84bound`` and
``ex:bb84exact``; ``interface.yaml`` ``inputs.photon_cutoff``). Widening the
analytic window recovers nothing: at ``c = 0`` Lemma ``lem:windowtail`` (iii)
makes the residual gap exactly zero, so all the remaining slack sits inside
Eq. ``eq:mcbound`` itself (the lead-in of Definition ``def:exactbnd``).

The exact window answers it by COMPUTING THE BLOCK on finitely many indices
and keeping an analytic remainder above them:

* :func:`exact_block_bound` is ``beta*(n) = lmin(blk M_mc^{(=n)})``
  (Definition ``def:exactbnd``), built from the SAME ``Fock(.)^{(n)}``
  construction Eq. ``eq:blockMS`` already uses for the emitted blocks at
  ``n <= N``, EVALUATED AT AN INDEX ABOVE THE CUTOFF INSTEAD OF BELOW IT;
* :func:`window_floor` is ``ell(n) = max{beta(n), beta-hat*(n) - eps_eig}``
  (Eq. ``eq:elldef``), a maximum of two lower bounds on ``beta*(n)`` OF TWO
  DIFFERENT KINDS: the first is Theorem ``thm:multiclick-bound``, an inequality
  between exact quantities holding with no hypothesis about any computation;
  the second is Assumption ``ass:eig``, which Remark ``rem:exacteig`` states is
  NOT A THEOREM OF THIS CONTRACT AND CANNOT BE MADE ONE HERE;
* :func:`setting_bound` emits Eq. ``eq:pmcex`` where a depth is declared and
  Eq. ``eq:pmcdef`` where none is.

**WHERE NO DEPTH IS DECLARED NOTHING CHANGES, AND THE CONTRACT SAYS SO.**
Definition ``def:pmc``, last paragraph: a declaration carrying no depth at any
setting is governed by Eq. ``eq:pmcdef`` ALONE -- no ``beta*`` is formed, no
eigenvalue of any block above the cutoff is computed, and Assumption ``ass:eig``
is not invoked (also Theorem ``thm:exact-and-evaluated`` (v) and the lead-in of
Assumption ``ass:eig``). This module realizes that by CONSTRUCTION rather than
by a branch that happens to agree: :func:`setting_bound` takes an
``exact_window`` argument that is ``None`` unless a depth was declared, and the
caller (:mod:`certiqs_key.receiver.construct`) forms no block above the cutoff
unless it has a depth to form it at.

WHY EACH BRANCH KEEPS ITS OWN REMAINDER
=======================================
Remark ``rem:exact-window-remainders``: the exact window covers
``N < n <= m*_t`` AND NOTHING ABOVE IT, so a remainder admissible in the sense
of Eq. ``eq:tailadm`` is still required, and each branch already has one.
Branch 1 has Eq. ``eq:collapsehyp`` exactly, by predicate (X), and takes
``beta(m*_t + 1)`` by Lemma ``lem:exactwindow`` (ii). Branch 2 has no
hypothesis available and keeps its own analytic window ``m*_t < n <= m_t`` and
tail ``T_{m_t}`` -- which is why ``m*_t <= m_t`` is required there, so that the
two windows compose into the single window ``N < n <= m_t``. NEITHER REMAINDER
IS NEW AND NEITHER IS WEAKENED. An implementation that dropped ``T_{m_t}``
because an exact window was declared would be unsound.

THE EMPTY MIDDLE MINIMUM IS ``+inf`` AND INACTIVE, NEVER ZERO
=============================================================
Definition ``def:pmcex``: the middle minimum of branch 2 runs over THE EMPTY
INDEX SET when ``m*_t = m_t``, and is then ``+infinity`` and INACTIVE. That
declaration is legal, and an implementation that read the empty minimum as
``0`` would emit ``0``: valid, strictly worse, and a violation of Proposition
``prop:exactnoworse`` at the one place the contract states a convention.
:class:`ExactWindowRecord` carries ``middle_minimum = None`` there and
:func:`setting_bound` omits the argument from the minimum rather than
supplying a number for it.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum

from certiqs_key.receiver.errors import HypothesisError
from certiqs_key.receiver.numerics import (
    Matrix,
    NumericalTolerances,
    lambda_max,
    lambda_min,
)
from certiqs_key.receiver.povm import NoClickFamily, multiclick_block
from certiqs_key.receiver.reasons import Refusal, RefusalReason

__all__ = [
    "BoundData",
    "Branch",
    "ExactWindowRecord",
    "SettingBound",
    "StrengtheningSlot",
    "bound_data_from_family",
    "bound_function",
    "check_bound_data",
    "check_bound_data_admissible",
    "collapse_slack",
    "emitted_weight",
    "emitted_weights",
    "exact_block_bound",
    "exact_composite",
    "exact_window_values",
    "multiclick_eigenvalue",
    "residual_gap",
    "setting_bound",
    "tail_value",
    "underline_beta",
    "window_floor",
    "window_indices",
    "window_minimum",
]


class Branch(StrEnum):
    """Which branch of Definition ``def:pmc`` produced the emitted value."""

    #: max{0, beta(N+1)} -- Lemma lem:collapse, under predicate (X) ALONE.
    COLLAPSE = "1"
    #: max{0, underline-beta_{N, m}} -- Lemma lem:windowtail, always valid.
    WINDOW_AND_TAIL = "2"


@dataclass(frozen=True)
class BoundData:
    """Admissible bound data of Definition ``def:bounddata``.

    ``0 <= gamma <= beta_k <= 1`` and ``0 <= c <= d_k <= 1``
    (Eq. ``eq:bounddata``).
    """

    port_count: int
    gamma: float
    betas: tuple[float, ...]
    c: float
    ds: tuple[float, ...]


def check_bound_data(data: BoundData) -> None:
    """Raise unless the tuple has the SHAPE Definition ``def:bounddata`` gives it.

    ``K >= 1`` entries, one ``beta_k`` and one ``d_k`` per port. That is a
    statement about the record and not about its numbers, and it is the whole
    of what this function checks.

    NO INEQUALITY OF Eq. ``eq:bounddata`` IS TESTED HERE. Definition
    ``def:tolmap`` (iv): the remaining inequalities of Eq. ``eq:bounddata``,
    ``gamma <= beta_k <= 1`` and ``c <= d_k <= 1``, are NOT SEPARATELY TESTED
    and NO THRESHOLD DECIDES THEM; they are redundant by theorem, discharged by
    the admissibility paragraph of Theorem ``thm:multiclick-bound`` from
    Eq. ``eq:bbkhyp`` and from ``gamma <= beta_k``, both hypotheses of the
    setting family (Definition ``def:setting-family`` (b)), and their
    floating-point evaluation is governed by Theorem
    ``thm:exact-and-evaluated`` (ii) like every other computed quantity.
    Definition ``def:bounddata`` says the same of every part but one: the one
    part of it that the contract decides on computed data is ``0 <= c``, and
    the other parts are not separately tested. That one decided part,
    ``0 <= c`` at ``-eps_2``, is :func:`check_bound_data_admissible`'s, a
    refusal and not an exception.
    """
    if data.port_count < 1:
        raise HypothesisError("Definition def:bounddata carries K >= 1 entries")
    if len(data.betas) != data.port_count or len(data.ds) != data.port_count:
        raise HypothesisError("one beta_k and one d_k per port are needed")


def check_bound_data_admissible(data: BoundData, tolerance: float) -> Refusal | None:
    """Return a refusal if Def. ``def:tolmap`` (iv) does not admit the data.

    Item (iv): "*Bound-data admissibility*, ``0 <= c`` in Eq. ``eq:bounddata``,
    is decided at ``eps_2``: the data are admitted when
    ``c = 1 - lmax(B) >= -eps_2``." ``tolerance`` is the declared ``eps_2`` and
    has no default. Requirement ``req:tolerance-tests``: "Bound data failing
    item (iv) of Definition def:tolmap are a failed validation, so
    ``fail_closed`` applies at this site: no artifact is emitted" -- so a
    failure is a REFUSAL, returned as data and turned into a refused emission
    by :func:`certiqs_key.receiver.construct.construct_receiver`, never an
    exception.

    ITEM (iv) DECIDES THIS ADMISSION ALONE, ON EVERY INPUT ROUTE. Whenever
    ``eps_1 > eps_2`` the band ``c in [-eps_1, -eps_2)`` of Eq.
    ``eq:tolmapband`` is non-empty: a route-(ii) instrument there is admitted by
    item (v)'s test at ``eps_1``, and its bound data are refused here. Item (iv)
    wins on it and the band is refused (Definition ``def:tolmap``; Remark
    ``rem:bound-data-band`` derives why). Nothing intercepts in between, since
    route (ii) carries no separate Gram admissibility check.

    THE REASON STRING IS THIS MODULE'S. The interface's refusal rules tabulate
    none for this check (``refusals.named_without_a_spelling``), and
    ``req:tolerance-tests`` leaves the reason string the implementer's to name:
    ``bound_data_not_admissible``, the analogue of item (i)'s
    ``port_grams_not_admissible``. The detail names the contract label, the
    measured ``c`` and the declared ``eps_2``, so that a reader of the refusal
    can re-derive the decision.

    NOTHING IS CLAMPED. An admitted ``c`` in ``[-eps_2, 0)`` is returned to the
    caller untouched and enters Eq. ``eq:beta`` "exactly as it stands";
    Remark ``rem:cdirection`` states the direction of that evaluation on both
    sides. This function decides admission and never repairs the datum it
    decided on.
    """
    if data.c < -tolerance:
        return Refusal(
            RefusalReason.BOUND_DATA_NOT_ADMISSIBLE,
            f"Def. def:tolmap (iv) does not admit the bound data: the computed "
            f"c = 1 - lmax(B) is {data.c}, below -eps_2 = {-tolerance} at the "
            f"declared eps_2 = {tolerance}",
        )
    return None


def bound_data_from_family(family: NoClickFamily) -> BoundData:
    r"""Return the bound data Eq. ``eq:cd`` reads off a no-click family.

    ``B = B_{[K]}`` and ``B_k = B_{[K] \ {k}}`` are the effective Grams, and
    ``gamma`` and ``beta_k`` the matching prefactors (Definition
    ``def:setting-family`` (b)). Unconditioned this is ``B = A_Sigma``,
    ``B_k = A_{[K] \ {k}}`` with ``gamma = beta_k = 1`` (Corollary
    ``cor:unconditioned-family``); at a setting a submodule constructs the
    effective Grams need not be subset sums, so the additive hypothesis does
    not in general cover them.
    """
    ports = range(family.port_count)
    gamma, whole = family.pair(ports)
    betas: list[float] = []
    ds: list[float] = []
    for port in ports:
        others = frozenset(ports) - {port}
        beta_k, block = family.pair(others)
        betas.append(beta_k)
        ds.append(1.0 - lambda_min(block))
    data = BoundData(
        port_count=family.port_count,
        gamma=gamma,
        betas=tuple(betas),
        c=1.0 - lambda_max(whole),
        ds=tuple(ds),
    )
    check_bound_data(data)
    return data


def _power(base: float, exponent: int) -> float:
    """Return ``base ** exponent`` with the convention ``0^0 = 1``."""
    if exponent == 0:
        return 1.0
    return base**exponent


def bound_function(data: BoundData, photons: int) -> float:
    """Return ``beta(n)`` of Eq. ``eq:beta``, with the convention ``0^0 = 1``."""
    if photons < 0:
        raise HypothesisError("beta is defined for n >= 0")
    subtracted = sum(
        beta_k * _power(d_k, photons)
        for beta_k, d_k in zip(data.betas, data.ds, strict=True)
    )
    return (
        1.0 + (data.port_count - 1) * data.gamma * _power(data.c, photons) - subtracted
    )


def collapse_slack(data: BoundData) -> float:
    """Return ``sigma = sum_k beta_k - 1 - (K-1) gamma`` -- Rem. ``rem:noslack``.

    The slack in Eq. ``eq:collapsehyp``, and A DIAGNOSTIC AND NOTHING ELSE: no
    branch of Definition ``def:pmc`` consults it, no refusal turns on it, and
    there is no declared margin to compare it against.

    ``sigma = -beta(0)`` EXACTLY, by Eq. ``eq:beta`` at ``n = 0`` under
    ``0^0 = 1``, and Remark ``rem:noslack`` proves ``beta(0) >= 0`` always --
    it is the vacuum block of the multiclick element, a diagonal block of a
    positive operator and hence a NON-NEGATIVE REAL. So

    * ``sigma <= 0`` at every receiver, every setting and every parameter;
    * Eq. ``eq:collapsehyp`` holds IF AND ONLY IF ``beta(0) = 0`` exactly;
    * a test demanding ``sigma >= eps > 0`` is UNSATISFIABLE, and one demanding
      ``sigma >= 0`` is satisfied only in the exact-equality case, WHICH IS
      WHAT (X) ALREADY GUARANTEES FROM THE DECLARATION WITHOUT COMPUTING
      ANYTHING.

    That is why no computed margin test selects branch 1: by the same remark,
    branch 1 is taken only through (X), and it is by design that no arithmetic
    decides it.
    """
    return sum(data.betas) - 1.0 - (data.port_count - 1) * data.gamma


def window_minimum(data: BoundData, cutoff: int, window: int) -> float:
    """Return ``W_{N,m} = min_{N < n <= m} beta(n)`` -- Eq. ``eq:windowtail``.

    The window ``{n : N < n <= m}`` is non-empty for every ``m > N``; at
    ``m = N + 1`` it is the single index ``N + 1``. The convention
    ``N < n <= m`` is Lemma ``lem:windowtail``'s, in BOTH Eq. ``eq:windowtail``
    and Eq. ``eq:resgap``.
    """
    if window <= cutoff:
        raise HypothesisError(
            f"the window m = {window} must exceed the cutoff N = {cutoff}"
        )
    return min(bound_function(data, n) for n in range(cutoff + 1, window + 1))


def tail_value(data: BoundData, window: int) -> float:
    """Return ``T_m = 1 - sum_k beta_k d_k^m`` -- Eq. ``eq:windowtail``."""
    return 1.0 - sum(
        beta_k * _power(d_k, window)
        for beta_k, d_k in zip(data.betas, data.ds, strict=True)
    )


def underline_beta(data: BoundData, cutoff: int, window: int) -> float:
    """Return ``min{W_{N,m}, T_m}`` -- Lemma ``lem:windowtail``.

    Part (i): this is ``<= inf_{n>N} beta(n)`` for every ``m > N``, WITH NO
    HYPOTHESIS -- which is what makes branch 2 unconditionally valid and the
    right direction for the selector to fail toward. Part (ii): it is
    non-decreasing in ``m`` and converges to the infimum whenever ``c < 1``.
    """
    return min(window_minimum(data, cutoff, window), tail_value(data, window))


def residual_gap(data: BoundData, cutoff: int, window: int) -> float:
    """Return ``g_{N,m} = max{0, W_{N,m} - T_m}`` -- Eq. ``eq:resgap``.

    Lemma ``lem:windowtail`` (ii): a FINITE non-negative real for every
    ``m > N``, equal to ``(K-1) gamma c^{N+1}`` at the minimal window
    ``m = N + 1``, and bounding "what widening the window could still recover".
    ``interface.yaml`` ``outputs.validation_results`` emits it at each setting
    that declares a window.
    """
    return max(0.0, window_minimum(data, cutoff, window) - tail_value(data, window))


# ---------------------------------------------------------------------------
#  The exact window -- Definition def:exactbnd, Eq. eq:elldef, Eq. eq:pmcex
# ---------------------------------------------------------------------------


def window_indices(cutoff: int, depth: int) -> tuple[int, ...]:
    """Return the exact-window index set ``{n : N < n <= m*}``.

    The convention is Definition ``def:pmcex``'s and it is the same one
    Eq. ``eq:windowtail`` uses: the window is HALF-OPEN AT THE LEFT and CLOSED
    AT THE RIGHT, so at the minimal depth ``m* = N + 1`` it is the single index
    ``N + 1`` -- the depth Example ``ex:bb84exact`` declares.

    ``m* > N`` is a validated declaration (``interface.yaml``
    ``inputs.exact_window``), so reaching this function with ``m* <= N`` is a
    hypothesis failure and not a refusal:
    :func:`certiqs_key.receiver.validation.check_exact_window` is where the
    refusal is produced, before any block is formed.
    """
    if depth <= cutoff:
        raise HypothesisError(
            f"the exact-window depth m* = {depth} must exceed the cutoff "
            f"N = {cutoff}; the inputs table validates m*_t > N"
        )
    return tuple(range(cutoff + 1, depth + 1))


def exact_block_bound(family: NoClickFamily, photons: int) -> float:
    r"""Return ``beta-hat*(n)`` -- the computed value of Eq. ``eq:exactbnd``.

        beta*(n) = lmin( blk M_mc^{(=n)} )
                 = lmin( id^{(=n)} + (K-1) gamma Fock(id - B)^{(n)}
                                   - sum_k beta_k Fock(id - B_k)^{(n)} )

    **NO NEW OBJECT IS INTRODUCED**, and Definition ``def:exactbnd`` says so:
    each ``Fock(.)^{(n)}`` is the construction Eq. ``eq:blockMS`` ALREADY USES
    for the blocks the artifact emits at ``n <= N``, in the occupation basis and
    order that Definition ``def:fock`` and the interface conventions fix,
    EVALUATED AT AN INDEX ABOVE THE CUTOFF INSTEAD OF BELOW IT. So this function
    calls :func:`certiqs_key.receiver.povm.multiclick_block` -- the very
    function the emitted blocks come from -- at an index above the cutoff, and
    forms no second construction that could disagree with it. The matrix is
    Hermitian and has dimension ``binom(D + n - 1, n)`` with ``D = |Inp_C|``,
    which is the ``dimension`` of the setting family at every declared
    setting (Definition ``def:setting-family``; ``Inp = Inp_C`` where no
    probe is declared, Corollary ``cor:unconditioned-family``).

    WHICH EXTREME-EIGENVALUE ROUTINE, DECIDED HERE
    ==============================================
    Definition ``def:exactbnd`` names the object and NO ALGORITHM, no
    convergence criterion, no iteration bound, and **this is the choice
    Assumption ass:eig is stated about**: the value whatever routine is used
    computes must satisfy Eq. ``eq:eigassumption`` at the declared ``eps_eig``,
    WHICH THIS MODULE CANNOT VERIFY (the lead-in of ``ass:eig``). So the choice
    decides where A-EIG's risk sits and is recorded rather than made silently.

    **THE DECISION: the same direct dense Hermitian eigensolver this module
    already uses everywhere else,** :func:`certiqs_key.receiver.numerics.lambda_min`
    over ``numpy.linalg.eigvalsh`` (LAPACK's divide-and-conquer ``zheevd``).
    Four reasons, in order of weight:

    1. **The unsafe direction is the one an ITERATIVE routine cannot bound.**
       Assumption ``ass:eig`` is one-sided: an overshoot above the true
       ``lmin`` by more than ``eps_eig`` raises the emitted ``p_mc`` above
       ``inf_{n>N} lmin(blk M_mc^{(=n)})``, and Remark ``rem:exacteig`` says an
       overshoot of any size "is caught by nothing" -- ``r_6`` fires only
       downward. A Lanczos-type extremal solver stopped by a residual test can
       return a Ritz value on either side of the true one, and the same remark
       names AN ITERATION THAT HAS NOT CONVERGED among the failure modes; a
       direct eigensolver has no iteration to stop early and no stopping test
       to be wrong about.
    2. **It introduces no undeclared number.** It takes no tolerance, no
       iteration cap, no restart count and no random start, so nothing
       undeclared enters the emitted value -- which is the property Definition
       ``def:tolmap`` insists on for every threshold (each decided by a declared
       number and by no other threshold; the ``numerical_tolerance_assignment``
       convention adds that NO LIBRARY DEFAULT decides any of them) and Remark
       ``rem:ranktwosided`` insists on for every rank. The value is a function
       of the declared data and the substrate alone.
    3. **It is one substrate, not two.** ``lambda_min`` and ``lambda_max``
       already compute Eq. ``eq:cd``'s ``c`` and ``d_k``, Eq. ``eq:eps2rank``'s
       rank and ``r_5``'s defect. Adding a second spectral routine would put
       A-EIG's risk on a substrate no other claim of this module rests on.
    4. **The cost the contract states is affordable at the declared
       dimensions.** Theorem ``thm:emitted-bound`` prices the window at the
       ``m*_t - N`` extreme eigenvalues of Hermitian matrices of dimension
       ``binom(D + n - 1, n)``, ``D = |Inp_C|`` at both instances; a full
       symmetric decomposition at those dimensions is a fraction of the cost of
       forming the block, and the block must be formed either way.

    **THIS IS NOT AN ENCLOSURE AND IS NOT PRESENTED AS ONE.**
    ``interface.yaml`` ``outputs.bound_evaluation`` is ``floating_point``
    (Definition ``def:evaluation-model``), and Theorem ``thm:exact-and-evaluated`` (ii)
    "asserts no bound on the difference" between a computed quantity and the
    exact one -- for this quantity exactly as for every other. The backward
    stability of a symmetric eigensolver is a REASON FOR THE CHOICE, not a
    claim this module makes: nothing here discharges Assumption ``ass:eig``,
    and the named extension points (``interface.yaml``
    ``named_extension_points``; Remark ``rem:ia``, its fifth direction) name
    the two later claims -- a rigorous LOWER enclosure of ``beta*(n)``, or an
    exact rational PSD certificate on route (i) -- that would.

    Nothing is clamped: the computed value is returned as it stands and is
    carried into the artifact unmodified, so that a reader can recompute Eq.
    ``eq:elldef`` and see what the slack cost (Requirement
    ``req:exact-window-record``).
    """
    return lambda_min(multiclick_block(family, photons))


def exact_window_values(
    family: NoClickFamily, cutoff: int, depth: int
) -> tuple[tuple[int, float], ...]:
    """Return ``(n, beta-hat*(n))`` over the exact window ``N < n <= m*``.

    One extreme eigenvalue per index, which is exactly what Theorem
    ``thm:emitted-bound``'s computability clause prices the window at. The
    pairs are what ``bound_quantifier_domain`` carries EXACTLY AS COMPUTED
    (Requirement ``req:exact-window-record``).
    """
    return tuple(
        (photons, exact_block_bound(family, photons))
        for photons in window_indices(cutoff, depth)
    )


def window_floor(analytic: float, computed: float, eps_eig: float) -> float:
    """Return ``ell(n) = max{beta(n), beta-hat*(n) - eps_eig}`` -- Eq. eq:elldef.

    A MAXIMUM OF TWO LOWER BOUNDS ON ``beta*(n)`` OF TWO DIFFERENT KINDS, and
    Remark ``rem:exacteig`` is careful about which is which:

    * ``beta(n) <= beta*(n)`` is Theorem ``thm:multiclick-bound`` -- an
      inequality between exact quantities, holding with NO HYPOTHESIS about any
      computation. It is the FLOOR, and it is why a computed eigenvalue that
      lands too LOW "costs tightness and nothing else";
    * ``beta-hat*(n) - eps_eig <= beta*(n)`` is Assumption ``ass:eig`` and is
      NOT A THEOREM OF THIS CONTRACT, AND CANNOT BE MADE ONE HERE.

    ``eps_eig`` IS SUBTRACTED AND DECIDES NOTHING. In the remark's words, it
    decides nothing, it lowers a number -- so this function performs no
    comparison against it; Definition ``def:tolmap``'s preamble records that
    ``eps_eig`` decides nothing at all, and the
    ``numerical_tolerance_assignment`` convention that it appears in no item of
    the tolerance map. That convention names exactly two places where a declared
    tolerance changes a NUMBER rather than a decision, this one and
    Eq. ``eq:darkpmcslack`` (its ``rbar`` and ``delta_dc``), and in both "the
    computed quantity itself is emitted unmodified beside the number the
    inequality uses".

    NOTHING IS CLAMPED INTO ``[0, 1]``. Remark ``rem:exacteig`` (its Range
    paragraph) gives ``0 <= p_mc^(t) <= 1`` for the emitted value exactly,
    whatever the computed ``beta-hat*`` and whether or not ``ass:eig`` holds:
    the outer ``max{0, .}`` of Eq. ``eq:pmcex`` gives the lower end, and every
    branch's inner minimum contains an analytic remainder at most ``1`` that
    does not depend on ``beta-hat*`` -- ``beta(m*_t + 1)`` on branch 1,
    ``T_{m_t}`` on branch 2. Lemma ``lem:exactwindow`` gives the same range
    only through Eq. ``eq:ellhyp``, which at a setting carrying a depth IS
    ``ass:eig``. The same remark adds that no computed value is clamped into
    ``[0, 1]`` to make them look true; the outer ``max{0, .}`` is part of the
    emitted expression and is applied there, not here.
    """
    return max(analytic, computed - eps_eig)


def exact_composite(window: Sequence[float], remainder: float) -> float:
    """Return ``P`` of Eq. ``eq:exactcomposite`` -- Lemma ``lem:exactwindow``.

        P = max{ 0, min{ min_{N < n <= m*} ell(n), tau } }

    ``window`` is the finitely many ``ell(n)`` of Eq. ``eq:ellhyp`` and
    ``remainder`` is a ``tau`` admissible in the sense of Eq. ``eq:tailadm`` --
    ``tau <= 0`` OR ``tau <= inf_{n > m*} beta*(n)``. The lemma then gives
    ``0 <= P <= 1`` and ``blk M_mc^{(>N)} >= P id^{(>N)}``.

    THE OUTER MAXIMUM IS NOT COSMETIC. It is the ONE step of the lemma's proof
    that uses Eq. ``eq:mcpos`` (``M_mc >= 0``): if ``P = 0`` the assertion is
    ``blk M_mc^{(>N)} >= 0``, and the proof's step 2 says this is the one step
    that uses Eq. ``eq:mcpos``. Remark ``rem:exactscope`` records that the
    hypothesis enters nowhere else, and Theorem ``thm:emitted-bound``
    discharges it at every setting, ``M_mc|t`` being a sum of POVM elements
    there. The maximum is also what forecloses Proposition
    ``prop:slotvalid``'s ``p_y < 0`` condition.

    THE FIRST DISJUNCT OF Eq. ``eq:tailadm`` IS EASY TO MISS AND IS NOT A
    DEFECT. A NON-POSITIVE ``tau`` is admissible with no further hypothesis
    whatever, and it then drives the whole expression to ``0`` however good the
    window is -- the frozen ``EX-PROBE-ON-N1-M2-MSTAR2-ZERO`` is the
    receiver-level instance, where ``T_2 = -3/125`` and the emitted value is
    ``0``. The first disjunct is what lets a branch that cannot bound the tail
    at all still yield a VALID, if useless, statement rather than an invalid
    one.

    THE MINIMUM RUNS OVER THE WHOLE WINDOW, not over its first index: ``beta*``
    is not monotone in general, Lemma ``lem:collapse`` being a statement about
    ``beta`` under Eq. ``eq:collapsehyp``.
    """
    if not window:
        raise HypothesisError(
            "the exact window is non-empty for every m* > N; Lem. "
            "lem:exactwindow reads ell at N + 1 to prove P <= 1"
        )
    return max(0.0, min(min(window), remainder))


@dataclass(frozen=True)
class ExactWindowRecord:
    """The per-setting exact-window record of Def. ``def:pmcex``.

    ``interface.yaml`` ``outputs.bound_quantifier_domain`` asks, where an
    exact-window depth ``m*_t`` was declared, for THE DEPTH AND THE COMPUTED
    WINDOW VALUES ``beta-hat*^(t)(n)``, ``N < n <= m*_t``, that Eq.
    ``eq:elldef`` read ``p_mc^(t)`` from, and THE FACT THAT Assumption
    ``ass:eig`` WAS INVOKED AT THAT SETTING. Everything below is that content;
    the field names are this module's (the exact-window wire form of
    :mod:`certiqs_key.receiver.artifact`), since the interface fixes the
    content and no field names, no nesting and no encoding.

    ``rows`` carries ``(n, beta(n), beta-hat*(n), ell(n))``: the computed
    eigenvalue UNMODIFIED beside the analytic bound and the value
    Eq. ``eq:elldef`` produced from the two, so that a reader can recompute
    Eq. ``eq:elldef`` AND SEE WHAT THE SLACK COST (Requirement
    ``req:exact-window-record``).

    ``middle_minimum`` is branch 2's analytic window ``m*_t < n <= m_t`` and is
    ``None`` -- ``+infinity``, INACTIVE -- when that index set is empty, which
    happens exactly at ``m*_t = m_t``. It is ``None`` on branch 1 too, which has
    no such window at all.
    """

    #: The declared depth m*_t.
    depth: int
    #: (n, beta(n), beta-hat*(n), ell(n)) over N < n <= m*_t, increasing n.
    rows: tuple[tuple[int, float, float, float], ...]
    #: min over the exact window of ell -- the first argument of Eq. eq:pmcex.
    window_minimum: float
    #: Branch 2's ANALYTIC middle window min over m*_t < n <= m_t; None where
    #: the index set is empty (m*_t = m_t) and None on branch 1.
    middle_minimum: float | None
    #: True exactly where m*_t = m_t on branch 2 -- the case Def. def:pmcex
    #: states a convention for: the middle minimum is +infinity and inactive.
    middle_window_empty: bool
    #: The branch's OWN remainder: beta(m*_t + 1) on branch 1, T_{m_t} on
    #: branch 2. Neither remainder is new and NEITHER IS WEAKENED (Remark
    #: rem:exact-window-remainders).
    remainder: float
    #: Which of the two it is, named as Lem. lem:exactwindow names them.
    remainder_kind: str
    #: Ass. ass:eig is invoked at every setting carrying a depth, and at no
    #: other. The field is always True on this record, which exists only there;
    #: it is carried so that the artifact STATES the fact rather than leaving a
    #: reader to infer it from the record's presence.
    assumption_eig_invoked: bool = True

    def computed_values(self) -> tuple[tuple[int, float], ...]:
        """Return ``(n, beta-hat*(n))`` -- the values carried unmodified."""
        return tuple((photons, computed) for photons, _, computed, _ in self.rows)

    def window_consistency_defects(self) -> tuple[float, ...]:
        """Return ``(beta(n) - beta-hat*(n))_+`` over the window -- Eq. eq:res6.

        The per-index terms of ``r_6``, whose exact value is ``0`` by
        Lemma ``lem:exactbasic``. Computed from this record so that the residual
        is a statement about the SAME numbers the emitted value was read from
        and cannot drift from them.
        """
        return tuple(
            max(0.0, analytic - computed) for _, analytic, computed, _ in self.rows
        )


@dataclass(frozen=True)
class SettingBound:
    """The per-setting record of Def. ``def:pmc``/``def:pmcex``.

    Every field ``interface.yaml`` ``outputs.bound_quantifier_domain`` asks
    for, per setting: WHICH BRANCH was taken -- branch 1 exactly where
    predicate (X) holds -- the declared window where branch 2 was, and, where
    an exact-window depth was declared, the depth, the computed window values
    and the fact that Assumption ``ass:eig`` was invoked at that setting.

    THERE IS NO SELECTING-PREDICATE FIELD AND NO MARGIN: the branch-1 selector
    is predicate (X) alone (``outputs.bound_quantifier_domain``,
    ``one_predicate_note``). ``predicate_x`` and ``branch`` are kept together
    and determine each other, which is the biconditional the outputs table
    states rather than two independent facts. ``eps_eig`` DOES NOT REOPEN
    THAT: Remark ``rem:noslack`` says in its own text that it is NOT A MARGIN
    OF THIS KIND AND DECIDES NO PREDICATE, the exact window being selected by
    THE PRESENCE OF A DECLARED DEPTH, which is again a property of the
    declaration.

    ``exact_window`` IS ``None`` AT EVERY SETTING CARRYING NO DEPTH, AND THAT
    IS THE OPT-IN INVARIANT MADE STRUCTURAL. Where it is ``None`` the weight is
    Eq. ``eq:pmcdef``'s, no ``beta*`` was formed and Assumption ``ass:eig`` was
    not invoked; where it is present the weight is Eq. ``eq:pmcex``'s.

    ``window_minimum``, ``tail`` and ``residual_gap`` are branch 2's ANALYTIC
    window ``N < n <= m_t``, its tail and Eq. ``eq:resgap``, and they are
    present exactly where branch 2 was taken -- with or without a depth,
    because branch 2 keeps its own window and tail either way (Remark
    ``rem:exact-window-remainders``).
    """

    setting: str
    branch: Branch
    predicate_x: bool
    window: int | None
    window_minimum: float | None
    tail: float | None
    residual_gap: float | None
    weight: float
    #: The exact-window record, present exactly at a setting whose declaration
    #: carries a depth m*_t, and None everywhere else.
    exact_window: ExactWindowRecord | None = None
    #: ``receiver/req:rigorous-weight`` (vi): ``rigorous`` where ``weight`` is
    #: the enclosed weight rounded down, ``floating_point`` otherwise, with
    #: the fallback reason; at a rigorous setting the enclosed data, window
    #: bounds and weight as exact rationals and the floating-point weight as a
    #: diagnostic that enters no number (item (v)).
    evaluation: str = "floating_point"
    fallback_reason: str | None = None
    enclosed: Mapping[str, object] | None = None
    floating_point_weight: float | None = None

    @property
    def assumption_eig_invoked(self) -> bool:
        """Return whether Ass. ``ass:eig`` was invoked at this setting.

        True exactly where a depth was declared and the weight is evaluated in
        floating point (``req:eig-ledger-row``: a setting with an enclosed
        weight does not invoke it, whatever its depth). Assumption ``ass:eig``
        is invoked only where a caller declares an exact-window depth;
        ``interface.yaml``
        ``outputs.bound_quantifier_domain`` asks the artifact to record the fact
        per setting, and Requirement ``req:eig-ledger-row`` asks the ledger to
        carry the settings at which it was invoked.
        """
        return self.exact_window is not None and self.evaluation != "rigorous"

    @property
    def definition(self) -> str:
        """Return which definition produced the emitted value at this setting.

        Requirement ``req:weight-provenance``: the artifact says WHICH of
        Definitions ``def:pmc`` and ``def:pmcex`` PRODUCED EACH weight AND AT
        WHAT DEPTH.
        """
        return "def:pmcex" if self.exact_window is not None else "def:pmc"


def setting_bound(
    setting: str,
    data: BoundData,
    cutoff: int,
    predicate_x: bool,
    tolerances: NumericalTolerances,
    window: int | None = None,
    exact_depth: int | None = None,
    computed_window: Sequence[tuple[int, float]] | None = None,
) -> SettingBound:
    """Return ``p_mc^{(t)}`` and its record -- Eq. eq:pmcdef or Eq. eq:pmcex.

    **BRANCH 1 EXACTLY WHERE PREDICATE (X) HOLDS, BRANCH 2 OTHERWISE.** (X) is a
    property of the DECLARATION -- the setting's exact flag, set by the
    construction that produced the setting (Remark ``rem:flag-instances``) --
    and is decided by :mod:`certiqs_key.receiver.settings` at input
    validation, before any Gram is computed; nothing here recomputes it and
    no arithmetic can override it. The positive part is taken in both
    branches and under both definitions, and ``0 <= p_mc <= 1`` follows from it
    together with ``beta <= 1`` (Theorem ``thm:multiclick-bound``) or, on the opt-in
    route, with the analytic remainder at most ``1`` that every branch of
    Eq. ``eq:pmcex`` keeps (Remark ``rem:exacteig``, Range) -- not from Lemma
    ``lem:exactwindow``'s own ``0 <= P <= 1``, which holds only through
    Eq. ``eq:ellhyp``, that is, under ``ass:eig``.

    WHERE (X) FAILS THE SELECTOR FALLS TO BRANCH 2, WHICH IS UNCONDITIONALLY
    VALID (Lemma ``lem:windowtail`` (i)), which is why (X) may be SUFFICIENT
    AND NOT NECESSARY: a setting whose prefactors are one in fact but not by
    construction fails (X) on the declaration, and is served by branch 2 --
    "That is conservative" (Remark ``rem:pmc-branch-choice``).

    A branch-2 setting REQUIRES a declared window: Requirement
    ``req:window-declaration`` refuses, rather than defaults, a declaration
    supplying no window ``m_t`` at a setting where predicate (X) fails, and
    that condition is decidable at input validation from declared data alone
    (Remark ``rem:flag-instances``). Reaching this function without
    one is therefore a hypothesis failure and not a refusal --
    :func:`certiqs_key.receiver.validation.check_tail_window` is where the refusal
    is produced.

    THE EXACT WINDOW IS SELECTED BY THE PRESENCE OF A DEPTH, AND BY NOTHING
    ELSE
    ======================================================================
    ``exact_depth is None`` is the analytic path, taken EXPRESSION FOR
    EXPRESSION: Eq. ``eq:pmcdef``, no ``ell``, no ``beta*``, no ``eps_eig``.
    Definition ``def:pmc`` states the invariant and this function realizes it
    by having no other route to the value.

    Where a depth IS declared, ``computed_window`` supplies the
    ``beta-hat*^(t)(n)`` for ``N < n <= m*_t`` -- one per index, computed by
    :func:`exact_window_values` from the SAME conditioned family the bound data
    came from -- and Eq. ``eq:pmcex`` is evaluated:

    * BRANCH 1 (predicate (X) holds): ``max{0, min{min ell, beta(m*_t + 1)}}``.
      The remainder is admissible by Lemma ``lem:exactwindow`` (ii), whose
      hypothesis Eq. ``eq:collapsehyp`` predicate (X) supplies with equality.
    * BRANCH 2: ``max{0, min{min ell, min_{m*_t < n <= m_t} beta(n),
      T_{m_t}}}``, the middle minimum being over the EMPTY index set -- and so
      ``+infinity`` and INACTIVE -- when ``m*_t = m_t``. This function realizes
      "inactive" by omitting the argument rather than by supplying a number for
      it; treating it as ``0`` would emit ``0``.

    ``m*_t <= m_t`` on branch 2 is a validated declaration, so that the two
    windows compose into the single window ``N < n <= m_t`` (Remark
    ``rem:exact-window-remainders``), and reaching this function with a
    violation is a hypothesis failure --
    :func:`certiqs_key.receiver.validation.check_exact_window` refuses it.
    """
    check_bound_data(data)
    if cutoff < 0:
        raise HypothesisError("the photon cutoff N is non-negative")
    if exact_depth is None:
        if computed_window is not None:
            raise HypothesisError(
                "computed window values were supplied at a setting declaring no "
                "exact-window depth; Def. def:pmc forms no block above the "
                "cutoff there"
            )
        return _analytic_setting_bound(setting, data, cutoff, predicate_x, window)
    if computed_window is None:
        raise HypothesisError(
            f"setting {setting!r} declares the exact-window depth "
            f"{exact_depth} and no computed window values were supplied"
        )
    if tolerances.eps_eig is None:
        raise HypothesisError(
            f"setting {setting!r} declares an exact-window depth and the "
            f"declaration supplies no eps_eig; the inputs table refuses that at "
            f"input validation rather than defaulting one"
        )
    return _exact_setting_bound(
        setting,
        data,
        cutoff,
        predicate_x,
        window,
        exact_depth,
        computed_window,
        tolerances.eps_eig,
    )


def _analytic_setting_bound(
    setting: str,
    data: BoundData,
    cutoff: int,
    predicate_x: bool,
    window: int | None,
) -> SettingBound:
    """Return Eq. ``eq:pmcdef``'s value -- the analytic path."""
    if predicate_x:
        return SettingBound(
            setting=setting,
            branch=Branch.COLLAPSE,
            predicate_x=True,
            window=window,
            window_minimum=None,
            tail=None,
            residual_gap=None,
            weight=max(0.0, bound_function(data, cutoff + 1)),
        )
    if window is None:
        raise HypothesisError(
            f"setting {setting!r} fails predicate (X) and needs a declared "
            f"tail_window; Definition def:pmc refuses rather than defaults one"
        )
    return SettingBound(
        setting=setting,
        branch=Branch.WINDOW_AND_TAIL,
        predicate_x=False,
        window=window,
        window_minimum=window_minimum(data, cutoff, window),
        tail=tail_value(data, window),
        residual_gap=residual_gap(data, cutoff, window),
        weight=max(0.0, underline_beta(data, cutoff, window)),
    )


def _exact_setting_bound(
    setting: str,
    data: BoundData,
    cutoff: int,
    predicate_x: bool,
    window: int | None,
    depth: int,
    computed_window: Sequence[tuple[int, float]],
    eps_eig: float,
) -> SettingBound:
    """Return Eq. ``eq:pmcex``'s value -- the opt-in path.

    The two branches differ ONLY in their remainder and in branch 2's extra
    analytic middle window; the exact window ``N < n <= m*_t`` and its
    Eq. ``eq:elldef`` floor are the same on both.
    """
    indices = window_indices(cutoff, depth)
    supplied = tuple(computed_window)
    if tuple(photons for photons, _ in supplied) != indices:
        raise HypothesisError(
            f"setting {setting!r} supplies computed window values at "
            f"{[n for n, _ in supplied]} where Def. def:pmcex names "
            f"{list(indices)}"
        )
    rows = tuple(
        (
            photons,
            bound_function(data, photons),
            computed,
            window_floor(bound_function(data, photons), computed, eps_eig),
        )
        for photons, computed in supplied
    )
    exact_minimum = min(floor for *_, floor in rows)

    if predicate_x:
        remainder = bound_function(data, depth + 1)
        record = ExactWindowRecord(
            depth=depth,
            rows=rows,
            window_minimum=exact_minimum,
            middle_minimum=None,
            middle_window_empty=False,
            remainder=remainder,
            remainder_kind=f"beta(m* + 1) = beta({depth + 1})",
        )
        return SettingBound(
            setting=setting,
            branch=Branch.COLLAPSE,
            predicate_x=True,
            window=window,
            window_minimum=None,
            tail=None,
            residual_gap=None,
            weight=exact_composite([exact_minimum], remainder),
            exact_window=record,
        )

    if window is None:
        raise HypothesisError(
            f"setting {setting!r} fails predicate (X) and needs a declared "
            f"tail_window; Definition def:pmc refuses rather than defaults one"
        )
    if depth > window:
        raise HypothesisError(
            f"setting {setting!r} fails predicate (X) and declares m* = {depth} "
            f"above m_t = {window}; Def. def:pmcex requires m*_t <= m_t there "
            f"so that the two windows compose"
        )
    # THE MIDDLE MINIMUM, over m*_t < n <= m_t. EMPTY at m*_t = m_t, where
    # Def. def:pmcex makes it +infinity and INACTIVE -- so it is omitted from
    # the minimum below rather than given a value. Reading it as 0 would emit 0.
    middle_empty = depth == window
    middle = None if middle_empty else window_minimum(data, depth, window)
    tail = tail_value(data, window)
    # Thm. thm:emitted-bound's proof, step 2: on branch 2 Lem. lem:exactwindow
    # is applied with m* = m_t, tau = T_{m_t} admissible by part (i), and THE
    # WINDOW FUNCTION ell(n) = ell^(t)(n) for N < n <= m*_t,
    # ell(n) = beta^(t)(n) for m*_t < n <= m_t, the two ranges together being
    # N < n <= m_t because m*_t <= m_t is required there. So the composite
    # window is the exact window's ell together with the analytic middle, and
    # the remainder is the tail; the middle is OMITTED where its index set is
    # empty.
    composite_window = [exact_minimum] if middle is None else [exact_minimum, middle]
    record = ExactWindowRecord(
        depth=depth,
        rows=rows,
        window_minimum=exact_minimum,
        middle_minimum=middle,
        middle_window_empty=middle_empty,
        remainder=tail,
        remainder_kind=f"T_(m_t) = T_{window}",
    )
    return SettingBound(
        setting=setting,
        branch=Branch.WINDOW_AND_TAIL,
        predicate_x=False,
        window=window,
        window_minimum=window_minimum(data, cutoff, window),
        tail=tail,
        residual_gap=residual_gap(data, cutoff, window),
        weight=exact_composite(composite_window, tail),
        exact_window=record,
    )


def emitted_weights(settings: Sequence[SettingBound]) -> tuple[tuple[str, float], ...]:
    """Return ``(t, p_mc^(t))`` for every declared setting -- Eq. ``eq:pmcsetting``.

    Theorem ``thm:emitted-bound``, its first conclusion:
    ``blk M^{(>N)}_{mc|t} >= p_mc^(t) 1^{(>N)}`` FOR EVERY ``t`` in ``T``, each
    weight being that setting's Eq. ``eq:pmcdef`` or, at a setting carrying a
    declared depth, Eq. ``eq:pmcex`` (under Assumption ``ass:eig`` there). The
    weights are the per-setting records' own, in the declared order of ``T``,
    and nothing is recomputed: this is the per-setting conclusion READ, not a
    second evaluation of it.

    Which instantiation of the theorem a run rests on is selected by the
    declaration and not by this function: ``cor:emitted-unconditioned`` where
    ``Inp_S`` is empty (one setting, ``T = {off}``), and the emission claim of
    the submodule that constructs the setting family where it is not -- and
    only that one reads the occupation-diagonal probe states of
    Def. ``def:probe``.
    """
    if not settings:
        raise HypothesisError("the probe alphabet T is non-empty")
    return tuple((record.setting, record.weight) for record in settings)


def emitted_weight(settings: Sequence[SettingBound]) -> float:
    """Return the uniform weight ``p_mc = min_t p_mc^{(t)}`` -- Eq. ``eq:pmcstatement``.

    Theorem ``thm:emitted-bound``: since ``p_mc <= p_mc^(t)`` at every ``t``,
    Eq. ``eq:pmcsetting`` at ``t`` gives ``blk M^{(>N)}_{mc|t} >= p_mc 1`` there
    with no further hypothesis, so the minimum carries the guarantee for every
    ``t`` in ``T`` -- one weight at every setting. It is the UNIFORM WEIGHT of
    the single entry of Definition ``def:slot`` and is DERIVED FROM
    :func:`emitted_weights`, never evaluated beside it; at a one-setting family
    the two are one number.
    """
    return min(weight for _, weight in emitted_weights(settings))


@dataclass(frozen=True)
class StrengtheningSlot:
    """The high-photon evidence of Definition ``def:slot``, one weight per setting.

    A finite list of pairs ``(O_i, (p_i^(t))_{t in T})`` with the ``O_i``
    PAIRWISE DISJOINT subsets of ``2^[K]`` and every ``p_i^(t) >= 0``, carrying
    the guarantee ``sum_{S in O_i} blk M^{(>N)}_{S|t} >= p_i^(t)`` for every
    ``t`` and every ``i``; the UNIFORM WEIGHT ``p_i = min_t p_i^(t)`` of an
    entry then carries it at every setting. At a one-setting family an entry
    has one weight and is written ``(O_i, p_i)``. The artifact carries
    ``r = 1`` with ``(MC_K, (p_mc^(t))_t)``, whose uniform weight is ``p_mc``;
    a later multi-bound family is a named extension point, additional entries
    in this slot (``interface.yaml`` ``named_extension_points``), and not a
    re-derivation of this one.

    ``entries[i]`` is ``(O_i, ((t, p_i^(t)), ...))`` with the settings in the
    declared order of ``T``; every entry is indexed by the SAME settings.
    """

    entries: tuple[
        tuple[tuple[frozenset[int], ...], tuple[tuple[str, float], ...]], ...
    ]

    def uniform_weights(self) -> tuple[float, ...]:
        """Return ``p_i = min_t p_i^(t)`` per entry -- Definition ``def:slot``."""
        return tuple(
            min(weight for _, weight in weights) for _, weights in self.entries
        )

    def is_valid(self) -> bool:
        """Return the Proposition ``prop:slotvalid`` conditions, at every setting.

        ``p_i^(t) >= 0`` and ``sum_i p_i^(t) <= 1`` AT EVERY SETTING ``t``, hence
        the same for the uniform weights; so the spec/architecture.md 5.4
        failure conditions "``p_y < 0``" and "``sum_y p_y > 1``" cannot be
        triggered by this module's output. The remaining condition of that
        list -- a bound holding at every declared setting it is stated for and
        every photon number above the cutoff -- is Theorem ``thm:emitted-bound``.
        An entry list whose entries are not indexed by one common setting set,
        or an entry with no weight at all, is not a slot of Definition
        ``def:slot`` and is not valid.
        """
        if not self.entries:
            return True
        settings = [setting for setting, _ in self.entries[0][1]]
        if not settings or len(set(settings)) != len(settings):
            return False
        for _, weights in self.entries:
            if [setting for setting, _ in weights] != settings:
                return False
        for index in range(len(settings)):
            column = [weights[index][1] for _, weights in self.entries]
            if any(weight < 0.0 for weight in column):
                return False
            if sum(column) > 1.0:
                return False
        seen: set[frozenset[int]] = set()
        for patterns, _ in self.entries:
            if seen & set(patterns):
                return False
            seen |= set(patterns)
        return True


def multiclick_eigenvalue(block: Matrix) -> float:
    """Return ``lmin(blk M_mc^{(=n)})`` -- the quantity Eq. eq:mcbound bounds.

    Remark ``rem:notsharp``: ``beta(n)`` bounds three operators separately and
    so need not be TIGHT, while the exact per-block eigenvalue can be computed
    from Eq. ``eq:blockMS`` by diagonalizing a matrix of dimension
    ``binom(|Inp_C| + n - 1, n)``. Where no depth is declared the module emits
    the ANALYTIC bound, because it is uniform in ``n`` while a per-block
    computation covers finitely many blocks. Requirement
    ``req:weight-provenance``: where the exact window is not requested the
    engine may ALSO report block eigenvalues AS A DIAGNOSTIC, while the values
    entering the strengthening slot are the per-setting weights ``p_mc^(t)`` --
    at a receiver without a probe the single value ``p_mc`` -- and the artifact
    says which definition produced each and at what depth. This function is
    that diagnostic, and no slot value is computed from it.
    """
    return lambda_min(block)
