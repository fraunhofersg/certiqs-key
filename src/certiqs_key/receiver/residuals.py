"""The six residuals of Definition ``def:residuals``.

Definition ``def:residuals`` and Theorem ``thm:exact-and-evaluated``.

    r_1 = || (Gamma^dagger Gamma - 1)_+ ||        contractivity defect
    r_2 = max_k max{0, -lmin(A_k)}                Gram positivity
    r_3 = || 1 - A_Sigma - Gamma_Inp^dagger E_un Gamma_Inp
             - (1 - Gamma_Inp^dagger Gamma_Inp) ||   deficiency identity
    r_4 = || 1 - sum_{S} blk M_S^{(=n)} ||        blockwise POVM completeness
    r_5 = max_{v,n,t} rho( blk M^{(=n)}_{v|t} )   block Hermiticity/positivity
    r_6 = max_{t, N < n <= m*_t} (beta^(t)(n) - beta-hat*^(t)(n))_+
                                                  window consistency

Each residual that exists is compared with its declared receiver tolerance,
and a residual above its tolerance is a REFUSAL, NOT A WARNING (Requirement
``req:residual-refusal``).

THE SIXTH RESIDUAL IS REQUEST-DEPENDENT, NOT ROUTE-DEPENDENT
============================================================
Its presence rule differs from ``r_1``'s and ``r_3``'s, which is why
Definition ``def:residuals`` gives it its own paragraph. ``r_6`` compares two
evaluations of one proved inequality, ``beta^(t)(n) <= beta*^(t)(n)`` (Lemma
``lem:exactbasic``), so its exact value is 0 like the other five, and it
exists on all three routes but ONLY AT THE SETTINGS WHOSE DECLARATION CARRIES
AN EXACT-WINDOW DEPTH, over exactly the indices ``N < n <= m*_t`` that depth
names. A declaration that requests no exact window computes no ``beta-hat*``
and HAS NOTHING TO COMPARE, so ``r_6`` is not defined there, and Requirement
``req:residual-emission`` makes its key ABSENT, not zero, by the same rule as
the keys of ``r_1`` and ``r_3`` on route (i).

AND IT IS ONE-SIDED, WHICH IS THE POINT OF STATING IT
=====================================================
Remark ``rem:exacteig``: ``r_6`` does NOT verify Assumption ``ass:eig``. It
fires when ``beta-hat*`` lands too LOW, and the assumption constrains it from
landing too HIGH; NO TEST IN THE CONTRACT BOUNDS THE UNSAFE DIRECTION, and the
assumption carries it. What ``r_6`` does catch is an evaluation that
contradicts an inequality the contract proves -- a block formed at the wrong
index, a wrongly ordered occupation basis, a conditioned family taken at the
wrong setting, an iteration that has not converged -- which the remark names
the failure mode most likely to be gross. Like ``r_5`` it is REFUSE-ONLY: it
refuses and repairs nothing (Requirement ``req:residual-refusal``).

WHICH RESIDUALS EXIST ON WHICH ROUTE -- ABSENT, NEVER ZERO
==========================================================
A rule about the emitted KEYS and not only about the values. Definition
``def:residuals``, its paragraph on which residuals exist on which route:
``r_2``, ``r_4`` and ``r_5`` are functions of the port Grams and of the
emitted blocks, WHICH EVERY ROUTE PRODUCES, so all three exist on all three
routes. ``r_1`` and ``r_3`` are written on ``Gamma`` and ``Gamma_Inp``, and
ROUTE (i) SUPPLIES NO INSTRUMENT MATRIX: there the Grams are the declared
datum and no ``Gamma`` exists, so ``r_1`` and ``r_3`` are NOT DEFINED, and
SYNTHESIZING A ``Gamma`` FROM Theorem ``thm:representation-independence``
(ii) TO EVALUATE THEM ON WOULD TEST THE SYNTHESIS RATHER THAN THE
DECLARATION. Requirement ``req:residual-emission`` makes their keys ABSENT
from ``validation_results`` -- absent, not zero, because emitting 0 would
report a check that was not made.

:func:`evaluate_residuals` implements the rule by OMISSION: it appends a
``r_1`` or ``r_3`` row only where the object the residual is written on exists,
so the artifact carries no key for either on route (i). ``eps_1`` and ``eps_3``
are still DECLARED there and are simply unused.

THE FIFTH RESIDUAL IS REFUSE-ONLY, AND NOTHING IS REPAIRED
==========================================================
``r_5`` watches the object the artifact actually hands a consumer -- the emitted
photon-number block -- which can fail Hermiticity or positivity at the last
floating-point step even when the four residuals that check the optics pass,
because ``r_4`` constrains only the SUM over ``S`` and ``r_2`` lives on the
Grams, one compilation stage earlier (Remark ``rem:res5why``). Proposition
``prop:res5`` (iv) proves the exact value is 0 on every emitted block before
any dark-count channel (the bare blocks ``r_5`` runs over), so a
non-zero ``r_5`` is always a numerical artefact.

``r_5 > eps_5`` refuses with
``photon_block_positivity_residual_above_tolerance`` (``interface.yaml``
``refusals``), and no block is Hermitized, symmetrized, projected onto the
positive cone, clamped or repaired in any way: the artifact carries the computed
block itself (Requirement ``req:residual-refusal``).
:func:`block_positivity_residual` therefore MEASURES and never returns a
repaired block, and no caller in this package has one to return.

WHAT THEY ARE, AND ARE NOT
==========================
Theorem ``thm:exact-and-evaluated`` (i) says the asserted mathematics is EXACT:
every asserted identity and inequality is between exactly specified quantities
and contains no error term, no tolerance and no numerical hypothesis, except
where a claim's own statement names a receiver tolerance or Assumption
``ass:eig``. Item (ii) says the EVALUATION is not, and that the residuals are
DIAGNOSTICS: passing them is NECESSARY for the artifact to be self-consistent
AND IS NOT SUFFICIENT FOR ANY ENCLOSURE STATEMENT, and the proof of (ii) adds
that a compilation that lost precision uniformly would satisfy every residual.
So nothing in this module treats a zero residual as evidence of anything
beyond self-consistency, and no claim, bound or emitted quantity is a function
of one.

THE NORM IS THE CONTRACT'S AND IS STILL DECLARED WITH THE VERDICT
=================================================================
Definition ``def:residuals`` fixes ``||.||`` as THE SPECTRAL NORM throughout
Eq. ``eq:res1`` to Eq. ``eq:rhodef``, which covers ``r_1``, ``r_3``, ``r_4``
and the ``rho`` of ``r_5`` (``r_2`` and ``r_6`` are scalars and are not
reached by it). :class:`Residual` still carries the norm's name beside the
value and the tolerance, because a verdict a reader cannot reproduce is not a
verdict; the field transcribes the definition.

THE DEFICIENCY IDENTITY IS THE CORRECT CHECK, AND ``r_3`` IS WHERE IT LIVES
===========================================================================
Lemma ``lem:deficiency``: Eq. ``eq:deficiencyid`` holds for EVERY receiver
instrument and is the correct check that loss was accounted for exactly once.
Remark ``rem:wrongcheck`` shows a path-product audit is not that check -- at a
balanced Mach-Zehnder it reports a spurious 50 per cent loss that does not
exist. ``r_3`` is what the artifact reports instead.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

from certiqs_key.receiver.grams import DeficiencyIdentity, GramFamily
from certiqs_key.receiver.numerics import (
    RESIDUAL_NORM,
    Matrix,
    NumericalTolerances,
    hermiticity_positivity_defect,
    identity,
    lambda_min,
    positive_part,
    residual_norm,
)
from certiqs_key.receiver.povm import NoClickFamily, completeness_defect
from certiqs_key.receiver.reasons import RESIDUAL_REASONS, Refusal, RefusalReason

if TYPE_CHECKING:  # pragma: no cover - the artifact module imports this one
    from certiqs_key.receiver.artifact import ResidualGap

__all__ = [
    "Residual",
    "block_positivity_residual",
    "check_residuals",
    "completeness_residual",
    "contractivity_residual",
    "deficiency_residual",
    "evaluate_residuals",
    "positivity_residual",
    "window_consistency_residual",
]


@dataclass(frozen=True)
class Residual:
    """One residual, its declared bound, the norm used, and the verdict.

    ``interface.yaml`` ``outputs.validation_results``: the residuals of
    Definition ``def:residuals`` THAT EXIST ON THE ROUTE TAKEN and for the
    evaluation requested, with their computed values, each with PASS OR FAIL
    AGAINST ITS DECLARED TOLERANCE.
    """

    residual_id: str
    value: float
    tolerance: float
    norm: str
    photons: int | None = None
    #: The declared probe setting this residual was evaluated at, where the
    #: object it is about is per setting. Eq. eq:res4 is a statement about the
    #: elements, and a setting family carries a DIFFERENT POVM at each t
    #: (Def. def:setting-family (a)), so a blockwise completeness residual
    #: belongs to one setting;
    #: r_1, r_2 and r_3 are statements about the unconditioned instrument and
    #: carry None.
    setting: str | None = None

    @property
    def passes(self) -> bool:
        """Return whether the residual is within its declared tolerance."""
        return self.value <= self.tolerance


def contractivity_residual(gamma: Matrix, tolerances: NumericalTolerances) -> Residual:
    """Return ``r_1`` of Eq. ``eq:res1`` -- the contractivity defect.

    The POSITIVE PART of ``Gamma^dagger Gamma - 1`` must vanish: a contraction
    is exactly an operator whose positive part is zero, and the negative part
    carries the loss and must not enter the residual.

    ``gamma`` IS THE FULL INSTRUMENT MATRIX where one exists. Eq. ``eq:res1``
    writes the residual on ``Gamma`` with no restriction to the declared input
    columns, and the restricted defect is a principal submatrix of the full one
    -- hence a LOWER bound on it, which would report a passing ``r_1`` for a
    matrix that overshoots contraction only outside ``Inp``. The emission pass
    supplies ``D_eta Gamma_G``; a caller evaluating the diagnostic on
    ``Gamma_Inp`` gets that submatrix's value and should say so.
    """
    defect = gamma.conj().T @ gamma - identity(int(gamma.shape[1]))
    return Residual(
        residual_id="r_1",
        value=residual_norm(positive_part(defect)),
        tolerance=tolerances.eps_1,
        norm=RESIDUAL_NORM,
    )


def positivity_residual(
    family: GramFamily, tolerances: NumericalTolerances
) -> Residual:
    """Return ``r_2`` of Eq. ``eq:res2`` -- Gram positivity.

    ``max_k max{0, -lmin(A_k)}``. A SCALAR, so the norm Definition
    ``def:residuals`` names does not reach it (``interface.yaml``
    ``outputs.validation_results.residual_norm_note``). The norm field carries
    the contract's name for the norm and is not consumed here.

    IT IS ALSO THE POSITIVITY HALF OF Definition ``def:tolmap`` (i) WRITTEN AS A
    RESIDUAL: the item's closing sentence says the same declared number bounds
    the residual and decides the admission, in the same units, and the
    definition's kind (c) counts ``r_2 <= eps_2`` among the residual tests,
    coinciding with item (i) on route (i), rather than as a further threshold.
    """
    worst = max(
        (max(0.0, -lambda_min(matrix)) for matrix in family.matrices), default=0.0
    )
    return Residual(
        residual_id="r_2",
        value=worst,
        tolerance=tolerances.eps_2,
        norm=RESIDUAL_NORM,
    )


def deficiency_residual(
    terms: DeficiencyIdentity, tolerances: NumericalTolerances
) -> Residual:
    """Return ``r_3`` of Eq. ``eq:res3`` -- the deficiency identity."""
    return Residual(
        residual_id="r_3",
        value=residual_norm(terms.defect),
        tolerance=tolerances.eps_3,
        norm=RESIDUAL_NORM,
    )


def completeness_residual(
    family: NoClickFamily, photons: int, tolerances: NumericalTolerances
) -> Residual:
    """Return ``r_4`` of Eq. ``eq:res4`` at one emitted photon number.

    Summed over the RAW alphabet by Eq. ``eq:incexc``: see
    :func:`certiqs_key.receiver.povm.completeness_defect` for why the multiclick
    element is not taken to be the complement here.
    """
    return Residual(
        residual_id="r_4",
        value=residual_norm(completeness_defect(family, photons)),
        tolerance=tolerances.eps_4,
        norm=RESIDUAL_NORM,
        photons=photons,
    )


def block_positivity_residual(
    blocks: Sequence[Mapping[str, Matrix]], tolerances: NumericalTolerances
) -> Residual:
    """Return ``r_5`` of Eq. ``eq:res5`` -- block Hermiticity and positivity.

        r_5 = max_{v, n, t} rho( blk M^{(=n)}_{v|t} )

    with ``rho`` of Eq. ``eq:rhodef``
    (:func:`certiqs_key.receiver.numerics.hermiticity_positivity_defect`).

    THE MAXIMUM RUNS OVER EXACTLY THE BARE BLOCKS THE ARTIFACT EMITS, before
    any dark-count channel (req:residual-emission), and Definition
    ``def:residuals`` enumerates the index set rather than leaving it to
    inference: every emitted outcome letter ``v`` in ``V``, every photon number
    ``0 <= n <= N``, and every setting ``t`` in ``T`` of the setting family (ONE
    SETTING WHEN ``Inp_S`` IS EMPTY, Corollary ``cor:unconditioned-family``).
    ``n = 0`` is in ``0 <= n <= N`` for every declared ``N >= 0``, so THE
    ONE-DIMENSIONAL VACUUM BLOCKS ARE IN THE MAXIMUM: an implementation that
    skipped them would report a maximum over a smaller set, which is not the
    quantity Eq. ``eq:res5`` defines.

    ``blocks`` is therefore the caller's flattening of the whole emitted family,
    one mapping ``v -> blk M^{(=n)}_{v|t}`` per ``(n, t)``, and the empty family
    gives ``0`` -- the maximum over an empty set of a quantity that is ``>= 0``
    and is emitted only where a block exists.
    """
    worst = max(
        (
            hermiticity_positivity_defect(block)
            for family in blocks
            for block in family.values()
        ),
        default=0.0,
    )
    return Residual(
        residual_id="r_5",
        value=worst,
        tolerance=tolerances.eps_5,
        norm=RESIDUAL_NORM,
    )


def evaluate_residuals(
    tolerances: NumericalTolerances,
    grams: GramFamily,
    no_click: NoClickFamily,
    cutoff: int,
    gamma: Matrix | None = None,
    deficiency: DeficiencyIdentity | None = None,
) -> tuple[Residual, ...]:
    """Return every residual the artifact carries, in the order of def:residuals.

    ``gamma`` is the FULL instrument matrix (Eq. ``eq:res1``) and the
    ``deficiency`` terms are written on ``Gamma_Inp`` (Eq. ``eq:res3``); both
    are absent on route (i), where no instrument matrix exists: Theorem
    ``thm:exact-and-evaluated`` (iv) records that there the compilation error
    of (ii) does not exist, THERE BEING NO COMPILATION, so ``r_1`` and ``r_3``,
    which are statements ABOUT ``Gamma``, have nothing to be evaluated on.

    **THE ABSENCE IS THE RULE, NOT AN OPTIMIZATION.** Requirement
    ``req:residual-emission``: on route (i) the keys of ``r_1`` and ``r_3`` are
    ABSENT, NOT ZERO, because emitting 0 would report a check that was not
    made. This function omits the rows rather than appending zeros, and
    nothing downstream fills them in.

    ``r_4`` is emitted once per emitted block, ``0 <= n <= N``, as Eq.
    ``eq:res4`` writes it, for each emitted ``n``. ``r_5`` is NOT produced
    here: it is a maximum over the emitted blocks of every setting at once, so
    it is evaluated by :func:`block_positivity_residual` where the whole family
    is in hand.
    """
    residuals: list[Residual] = []
    if gamma is not None:
        residuals.append(contractivity_residual(gamma, tolerances))
    residuals.append(positivity_residual(grams, tolerances))
    if deficiency is not None:
        residuals.append(deficiency_residual(deficiency, tolerances))
    residuals.extend(
        completeness_residual(no_click, photons, tolerances)
        for photons in range(cutoff + 1)
    )
    return tuple(residuals)


def check_residuals(
    residuals: Sequence[Residual], gaps: Sequence[ResidualGap] = ()
) -> Refusal | None:
    """Return a refusal naming the first residual or gap above its tolerance.

    Requirement ``req:residual-refusal``, the whole of it at one site: each
    residual that exists is compared with its receiver tolerance, and a
    residual above its tolerance is a REFUSAL, not a warning -- ``r_5`` with
    ``photon_block_positivity_residual_above_tolerance``, ``r_6`` with
    ``window_eigenvalue_consistency_residual_above_tolerance`` -- and in the
    same way the residual gap ``g_{N,m_t}`` of Eq. ``eq:resgap``, at every
    setting where predicate (X) fails and a window is therefore in use, is
    compared with ``eps_gap`` and refuses above it
    (``residual_gap_above_tolerance``). The residuals are decided first and
    the gaps after them, in the order given. NOTHING IS REPAIRED: this
    function reads each value as it was computed and returns a refusal or
    ``None``; no block is Hermitized, symmetrized, projected or clamped
    anywhere on the way to it.

    ``gaps`` is empty by default so that a caller holding residuals only --
    a declaration whose every setting satisfies (X) has no gap at all -- reads
    the same verdict it always did.
    """
    for residual in residuals:
        if not residual.passes:
            where = "" if residual.photons is None else f" at n = {residual.photons}"
            return Refusal(
                RESIDUAL_REASONS[residual.residual_id],
                f"{residual.residual_id}{where} = {residual.value} exceeds its "
                f"declared tolerance {residual.tolerance} under the "
                f"{residual.norm} norm",
            )
    for gap in gaps:
        if not gap.passes:
            return Refusal(
                RefusalReason.RESIDUAL_GAP_ABOVE_TOLERANCE,
                f"the achieved residual gap at setting {gap.setting!r} is "
                f"{gap.gap}, above the declared eps_gap = {gap.tolerance}",
            )
    return None


def window_consistency_residual(
    defects: Sequence[float], tolerances: NumericalTolerances
) -> Residual:
    """Return ``r_6`` of Eq. ``eq:res6`` -- the window consistency defect.

        r_6 = max over t and over N < n <= m*_t of
              ( beta^(t)(n) - beta-hat*^(t)(n) )_+

    ``defects`` is the caller's flattening of the per-index positive parts over
    EVERY setting carrying a depth and every index its depth names, which is
    exactly the index set Eq. ``eq:res6`` maximises over. They come from the
    :class:`~certiqs_key.receiver.bound.ExactWindowRecord` the emitted value was
    read from, so the residual is a statement about the SAME numbers and cannot
    drift from them -- the same rule ``r_5`` follows by being handed the emitted
    blocks.

    THE EXACT VALUE IS ZERO, and that is a theorem rather than a hope (Remark
    ``rem:exacteig``): ``beta(n) <= beta*(n)`` is Lemma ``lem:exactbasic``, so
    the window consistency defect ``r_6`` has exact value 0, and it is a
    residual in exactly the sense of the other five: WHAT IS EMITTED IS ITS
    FLOATING-POINT EVALUATION, and a value above ``eps_6`` refuses.

    NO NORM ENTERS IT. Definition ``def:residuals`` names the spectral norm
    throughout Eq. ``eq:res1`` to Eq. ``eq:rhodef``; ``r_6`` is a maximum of
    differences of two real numbers, and like ``r_2`` it is a scalar the norm
    does not reach. The field carries the contract's name for the four it does
    reach and is not consumed here.

    THIS FUNCTION IS CALLED ONLY WHERE A DEPTH WAS DECLARED. Where none was,
    the emitted ``validation_results`` carries NO KEY for ``r_6`` -- absent, not
    zero -- and ``eps_6`` is not declared either.
    """
    return Residual(
        residual_id="r_6",
        value=max(defects, default=0.0),
        tolerance=tolerances.residual_bound("r_6"),
        norm=RESIDUAL_NORM,
    )
