"""The gradients of C12 (Theorem ``thm:gradient``, Corollary ``cor:full-gradient``).

contract.tex Eq. ``eq:gradT``, with ``p = 1/alpha`` and ``Y = Z(X^p)``::

    grad T(X) = alpha * D X^p [ Z( Y^{alpha-1} ) ]

and its divided-difference form Eq. ``eq:gradT-kernel``. Eq. ``eq:grad-q`` and
Eq. ``eq:grad-J`` assemble the gradient of the whole objective from it, with the
pieces ``Gamma`` and ``Delta`` of Eq. ``eq:grad-pieces``.

THE SPLIT FACE RULE, WHICH IS THE CONTRACT'S OWN
===============================================
Theorem ``thm:gradient`` (i) states the face rule in the SPLIT form that its
proof supports, and calls it "the rule an implementation must realize":

  (a) the divided-difference map ``D X^p[.]`` is compressed to ``S = supp X`` --
      equivalently, the kernel sum of Eq. ``eq:gradT-kernel`` runs over the
      STRICTLY POSITIVE eigenvalues of ``X`` only, where ``X`` is positive
      definite and ``f^{[1]}`` is finite;
  (b) ``Y = Z(X^p)``, ``Y^{alpha-1}`` and ``Z(Y^{alpha-1})`` are formed on the
      AMBIENT branch space and are NOT compressed to ``S``.

That split is what makes the gradient available on a face without assuming
``Z``-invariance, and the contract exhibits the rank-one witness that separates
it from the discarded "compress everything to ``supp X``" reading: for
``X = |eta><eta|`` with ``|eta>`` spread over two raw-key values, ``Z(X^p)`` has
rank two while ``X`` has rank one, the ambient value is ``T = 2^{1-alpha}`` and
the fully compressed one ``2^{-alpha}`` -- a factor of two, at every alpha, in
the UNSAFE direction (a smaller ``T`` gives a smaller ``K`` and, since the
kernel ``d(u, v)`` is non-increasing in ``v``, a larger key). The statement
carries this; the code below computes (a) and (b) and cites them as the
contract's words.

Full compression to a subspace ``S'`` is licensed exactly when
``S ⊆ S'`` and ``S'`` is ``Z``-invariant. :func:`z_invariant_face` builds the
smallest such ``S'`` above the branch range, which is what the perturbation path
uses; the default path needs no ``S'`` at all.

WHY THE KEY-ACTIVE RESTRICTION IS TAKEN HERE AND NOT IN THE OBJECTIVE
====================================================================
Remark ``rem:classes`` (i) licenses evaluating "over key-active sectors only --
an identity, C7", and :mod:`certiqs_key.meat_core.declaration.sectors` deliberately does
NOT take it for the objective: summing the deficits over every declared sector
is the same number, and computing an identity does not rely on the key-inert
predicate being right. That reasoning is sound for ``f`` and DOES NOT TRANSFER
TO ``grad f``.

On a key-inert sector the deficit ``f_{chat,s}`` is identically zero
(Proposition ``prop:exact-cancellation``), so its gradient is zero too -- but
EVALUATING it
requires the differentiability hypothesis of Theorem ``thm:gradient`` (ii), and
that hypothesis fails at exactly the points where the term vanishes. Adding a
zero is free; deriving it is not. So :func:`state_gradient` takes the
restriction the remark grants, and takes it only for the deficit term: the
statistics piece ``Gamma`` is unaffected and is summed over every sector as
before.

WHAT MADE THIS REACHABLE. A class branch is built from ALL outcome pairs of its
announcement class, so on a sector where every ``F_v^{(s)}`` of the class
vanishes the Kraus operator is present but IDENTICALLY ZERO -- non-empty, and
therefore past the ``kraus.size == 0`` guard in
:func:`pullback_trace_power_gradient`, which then met a vanishing branch
operator and refused. A declaration with one sector per emitted letter has such
a sector for every letter that announces no key basis, so this is generic in a
flag-state-squashed receiver declaration and absent from a single-sector one.

WHERE THE GRADIENT EXISTS, AND HOW THIS MODULE STAYS INSIDE THAT
================================================================
Theorem ``thm:gradient`` (ii) is explicit: the one-sided directional derivative
"can equal ``+inf`` only when ``H`` strictly enlarges the support of ``X``", and
"solvers must therefore evaluate gradients only at iterates whose support is
(kept) maximal, e.g. after an explicit perturbation". spec/architecture.md
spec/architecture.md 7.2 (4) says the same and adds the prohibition: "via perturbation
or face
compression -- **not** by silent eigenvalue clipping".

The DIVIDED-DIFFERENCE sum may be restricted to the strictly positive spectrum
of ``X`` whenever the direction ``H`` satisfies ``supp H ⊆ supp X``, since the
dropped terms carry a factor ``P_i H P_j = 0``. For the composite object this
module actually needs -- the pullback ``G^dagger[grad T(X)]``, i.e.
``A^dagger grad T(X) A`` -- the same argument applies to ``A`` itself, and
Corollary ``cor:full-gradient``'s own proof makes it: "the components of
``grad T`` outside that face never enter Eq. ``eq:grad-pieces``, because
``chi^dagger . G^dagger`` sandwiches its argument between the operators
``K_kappa (W_tau x 1)`` and their adjoints, whose ranges lie in ``W_{chat,s}``".
Nothing is clipped: the terms that are not formed are the terms multiplied by
zero.

MAXIMAL SUPPORT, READ ON THE ADMISSIBLE SUBSPACE
================================================
The condition is ``supp X_{chat,s} = W_{chat,s}`` of Eq. ``eq:Wcs``, and
Eq. ``eq:Wcs`` builds ``W_{chat,s}`` from the ADMISSIBLE ALICE SUBSPACE ``S_A``
of Eq. ``eq:SA`` -- ``supp tau_A`` in trusted-source mode, all of ``H(A)`` in
untrusted-source mode. Eq. ``eq:Wcs-bound`` records when it is attained:
"whenever the Choi block satisfies ``J_s > 0`` (trusted-source mode),
respectively whenever ``omega_s > 0`` on ``H(A Q_s)`` (untrusted-source mode);
these are the same condition, ``J_s = omega_s``".

So the check below is not "``omega_s`` positive definite on ``A (x) Q_s``",
which would be wrong for a SINGULAR ``tau_A``: no feasible ``omega_s`` is ever
positive definite there, because every feasible state is supported in
``supp tau_A (x) H(Q_s)``. It is "``omega_s`` positive definite ON
``S_A (x) H(Q_s)``", i.e. the compression by the admissible isometry is positive
definite -- which is ``J_s > 0`` exactly, since ``W_tau`` restricted to ``A_0``
is invertible onto that subspace. For a full-rank ``tau_A`` and in
untrusted-source mode the isometry is the identity and this is the plain
condition verbatim. A block failing it fails closed with
:class:`~certiqs_key.meat_core.errors.SupportError`.

SCALE
=====
``T`` is positively homogeneous of degree one (``T(cX) = c T(X)``, used in the
proof of Theorem ``thm:gradient`` (ii)), so ``grad T`` is homogeneous of degree
ZERO: ``grad T(cX) = grad T(X)`` exactly. The gradient is therefore evaluated at
``X / tr X``, which keeps every eigenvalue of order one no matter how lightly a
sector is weighted. This is an identity, not an approximation.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass, field

import numpy as np
import numpy.typing as npt

from certiqs_key.foundations.kernel import (
    divergence_kernel_du,
    divergence_kernel_dv,
)
from certiqs_key.meat_core.errors import GradientHypothesisError, SupportError
from certiqs_key.meat_core.objective.branch import (
    BranchValues,
    ClassBranch,
    GeneratedMaps,
    admissible_isometry,
    aggregate_branch_operator,
    branch_operator,
    evaluate_branches,
)
from certiqs_key.meat_core.objective.choi import ChoiParametrization
from certiqs_key.meat_core.objective.linalg import (
    Matrix,
    as_matrix,
    divided_difference,
    factor_support,
    hermitian_part,
    is_positive_definite,
    pinch,
    psd_power,
    support_rank,
    support_spectrum,
)
from certiqs_key.meat_core.objective.objective import check_alpha_structural

#: The two withdrawal reasons of ``req:first-order-withdrawal`` this module
#: can raise, SPELLED HERE AS STRINGS. They are the contract's spellings and
#: not this module's; :class:`certiqs_key.meat_core.reasons.AssuranceReason`
#: is the enum a consumer reads them through, and it is not imported here
#: because ``finitekey`` sits above ``objective`` and the dependency must not
#: be turned round. ``tests`` compare the two, so a divergence is caught.
_POSITIVITY_REASON = "gradient_hypothesis_positivity"
_SUPPORT_REASON = "gradient_hypothesis_support"


@dataclass(frozen=True)
class ObjectiveGradient:
    """The gradient of ``O_alpha`` at a point, in one set of coordinates.

    ``q`` is Eq. ``eq:grad-q``; ``blocks`` is Eq. ``eq:grad-J`` when the
    coordinates are Choi blocks and its ``chi``-conjugate when they are state
    blocks ("the same formulas conjugated by ``chi`` give the state-form
    gradients", Corollary ``cor:full-gradient``).
    """

    #: Eq. ``eq:grad-q`` "READ AS A VECTOR IN ``R^{Chat_acc}``" (Lemma
    #: ``lem:fo-khyp`` (iii)), so this mapping is keyed by ``Chat_acc`` and not
    #: by the whole declared ``Chat``. A component indexed outside it "is, in
    #: every pairing of this section, multiplied by a component of a feasible
    #: direction that is 0, so it contributes nothing and its value -- finite,
    #: undefined or ``-inf`` -- IS NEVER READ". Absent rather than zero,
    #: because a zero here would read as a computed derivative.
    q: Mapping[str, float]
    blocks: Mapping[str, Matrix]
    #: Perturbations actually applied, per ``(chat, sector)``. Empty on the
    #: default face-compression path. spec/architecture.md 2.5 requires a
    #: repair to be recorded explicitly rather than folded into the result.
    perturbations: Mapping[tuple[str, str], float] = field(default_factory=dict)


def z_invariant_face(branch: ClassBranch, admissible: Matrix | None = None) -> Matrix:
    """Return the projector onto the smallest ``Z``-invariant space over the face.

    The ZERO projector where the branch spans nothing -- see the guards in the
    body, which is where the two ways that happens are named.

    ``W_{chat,s}`` of Eq. ``eq:Wcs`` is ``K_kappa(S_A (x) H(Q_s))`` summed over
    the pass classes -- the image of the ADMISSIBLE Alice subspace, not of all
    of ``A``. ``admissible`` is an isometry onto ``S_A (x) H(Q_s)``; ``None``
    means the whole block, which is right in untrusted-source mode and for a
    full-rank ``tau_A``.

    Returned is the projector onto ``sum_j Z_j W_{chat,s}``, the smallest
    ``Z``-invariant space containing it -- ``Z``-invariant because
    ``Z_i Z_j = delta_{ij} Z_i``, which is the ``S'`` Theorem
    ``thm:gradient`` (i) names for "a solver that prefers to work in a
    compressed ambient space". It is a property of the DECLARATION and does not
    move as the iterate moves, which is what makes the support check of
    spec/architecture.md 7.2 (5) a check rather than a moving target.
    """
    if branch.kraus.size == 0:
        return np.zeros((0, 0), dtype=np.complex128)
    restricted = (
        branch.kraus if admissible is None else branch.kraus @ np.asarray(admissible)
    )
    rows = int(restricted.shape[0])
    basis, singular, _ = np.linalg.svd(restricted, full_matrices=False)
    # A branch whose Kraus operator is present but VANISHES on the admissible
    # subspace spans nothing, so ``W_{chat,s}`` is the zero space and the face
    # is the zero projector. Reached where a class has outcome pairs but every
    # ``F_v^{(s)}`` of the class is zero on the sector -- which is exactly a
    # key-inert sector with a non-empty pair list, and is generic in a
    # flag-state-squashed declaration. Without this the singular values are all
    # zero, no column survives the relative threshold, and the second
    # decomposition below takes ``max`` of an empty array.
    if singular.size == 0 or float(np.max(singular)) == 0.0:
        return np.zeros((rows, rows), dtype=np.complex128)
    # ONE RULER, THE ONE (H-SUPP) USES (frank-wolfe/rem:fo-one-ruler).
    # Both windows below read singular values of a FACTOR, and a factor's
    # singular values are the square roots of the eigenvalues of the operator
    # it generates -- here the face K K^dagger and, second, the pinched face
    # projector sum_j Z_j P Z_j. So each is read at sqrt(support_cutoff),
    # which is the support_cutoff row on that operator and the reading of
    # dim W_{chat,s} in branch_support. A hard-coded 1e-12 on sigma counted
    # directions whose weight, sigma^2, no support_cutoff reading of an
    # operator can see. This projector serves the ESTIMATE path's explicit
    # perturbation only; no first-order bound is formed on it.
    keep = basis[:, factor_support(singular)]
    pieces = []
    for label in np.unique(branch.labels):
        mask = (branch.labels == label).astype(np.float64)
        pieces.append(keep * mask[:, None])
    stacked = np.concatenate(pieces, axis=1) if pieces else keep
    left, values, _ = np.linalg.svd(stacked, full_matrices=False)
    if values.size == 0 or float(np.max(values)) == 0.0:
        return np.zeros((rows, rows), dtype=np.complex128)
    columns = left[:, factor_support(values)]
    return np.asarray(columns @ columns.conj().T, dtype=np.complex128)


def perturb_onto_face(operator: Matrix, face: Matrix, delta: float) -> Matrix:
    """Return ``(1-delta) X + delta (tr X / dim S') Pi_{S'}``.

    The "explicit perturbation" of Theorem ``thm:gradient`` (ii): it makes ``X``
    positive definite on the ``Z``-invariant working face ``S'`` so that the
    unrestricted formulas apply there. It is the ESTIMATE path's perturbation
    and carries no accounting, so a positive ``delta`` is recorded in the result
    and never silently folded into a value. A trace-scaled mixing whose domination
    is proved, so that its soundness penalty is zero, belongs to the certificate
    chain, which is not built (PRINCIPLES.md section 10).
    """
    if not 0.0 <= delta < 1.0:
        raise ValueError(f"the perturbation must lie in [0, 1); got {delta!r}")
    if delta == 0.0:
        return operator
    dimension = float(np.real(np.trace(face)))
    if dimension <= 0.0:
        return operator
    scale = float(np.real(np.trace(operator))) / dimension
    return np.asarray(
        (1.0 - delta) * operator + delta * scale * face, dtype=np.complex128
    )


def trace_power_gradient(
    operator: Matrix,
    alpha: float,
    labels: npt.NDArray[np.int64],
    *,
    normalize: bool = True,
) -> Matrix:
    """Return ``grad T(X)`` of Eq. ``eq:gradT`` for a positive definite ``X``.

    Raises:
        SupportError: if ``X`` is not positive definite. Theorem
            ``thm:gradient`` states the formula at ``X > 0``; on a singular
            argument the operator has divergent entries in the kernel block and
            returning a finite matrix there would be a silent repair. The
            composite gradients below never need it -- see
            :func:`pullback_trace_power_gradient`.
    """
    check_alpha_structural(alpha)
    if not is_positive_definite(operator):
        raise SupportError(
            "Theorem thm:gradient states grad T at a positive definite "
            "argument; this operator is singular on the ambient space, where "
            "the kernel block of the divided-difference kernel diverges "
            "(Theorem thm:gradient (ii))"
        )
    working = operator
    if normalize:
        trace = float(np.real(np.trace(operator)))
        if trace <= 0.0:
            raise SupportError("grad T is undefined at the zero operator")
        working = np.asarray(operator / trace, dtype=np.complex128)
    exponent = 1.0 / alpha
    values, vectors = support_spectrum(working)
    pinched = pinch(psd_power(working, exponent), labels)
    outer = pinch(psd_power(pinched, alpha - 1.0), labels)
    compressed = vectors.conj().T @ outer @ vectors
    kernel = divided_difference(values, exponent)
    return np.asarray(
        alpha * vectors @ (kernel * compressed) @ vectors.conj().T,
        dtype=np.complex128,
    )


def attains_the_reference_rank(operator: Matrix, reference: int) -> bool:
    """Return whether Eq. ``eq:hsupp-check`` holds for one branch operator.

    THE CLAIM'S OWN DECIDER, AND BOTH SIDES ARE COMPUTED.
    ``frank-wolfe/rem:fo-one-ruler``: (H-SUPP) says
    ``supp X_{chat,s} = W_{chat,s}``, and since ``supp X_{chat,s}`` is
    contained in ``W_{chat,s}`` always (Eq. ``eq:Wcs-bound``) it is equivalent
    to the RANK EQUALITY ``rank X_{chat,s} = dim W_{chat,s}``. The left side is
    "the count of eigenvalues of ``X_{chat,s}`` above the ``support_cutoff``
    row of the declared thresholds, read RELATIVE TO THAT BLOCK'S OWN SPECTRAL
    RADIUS", which is :func:`support_rank` exactly; the right side is the
    reference computed once per pair
    (:func:`certiqs_key.meat_core.objective.branch.branch_support_reference`),
    ``rank K_{chat,s}`` read at ``sqrt(support_cutoff)`` -- the same row read
    on ``X(1) = K K^dagger``, so both sides are measured with one ruler.

    ONE COMPARISON PER ``(chat, s)``, ON THE AGGREGATE OPERATOR, and the caller
    forms it (:func:`certiqs_key.meat_core.objective.branch.aggregate_branch_operator`).
    BOTH WINDOWS ARE RELATIVE, so what they are relative to is part of the
    rule: comparing class by class measures each against its OWN spectral
    radius and admits a point the claim refuses whenever the classes differ in
    scale by more than ``1 / support_cutoff``. ``X_1 = [1.0]``, ``X_2 =
    [1e-15]`` with ``dim W = 2`` is the witness: per class the ranks are 1 and
    1, and the aggregate rank is 1.

    "IT IS NOT, AND MUST NOT BE READ AS, STRICT POSITIVITY OF ``X_{chat,s}`` ON
    ITS AMBIENT SPACE": that test is never satisfied, the ambient spectrum
    always containing 0, which is why the row needs a REFERENCE and why the
    reference is not the ambient dimension.

    THE TWO ONE-SIDED EXPOSURES THE CLAIM NAMES ARE NOT REMOVED BY THIS and are
    not hidden by it: an eigenvalue of a genuinely rank-deficient block
    reported above ``support_cutoff``, and a reference computed TOO SMALL -- a
    genuine direction whose relative weight in ``X(1)`` is at most
    ``support_cutoff`` -- each pass a block that should fail. A reference
    computed too LARGE can only withdraw ``h_lb``.
    """
    return support_rank(operator) == reference


def is_support_maximal(omega_s: Matrix, admissible: Matrix | None) -> bool:
    """Return whether ``omega_s`` attains the maximal support of Eq. ``eq:Wcs-bound``.

    A SUFFICIENT CONDITION AND NOT THE DECIDER. ``eq:Wcs-bound`` records that
    ``supp G_{chat,s}(omega_s)`` equals ``W_{chat,s}`` WHENEVER ``J_s > 0`` in
    trusted-source mode, respectively ``omega_s > 0`` in untrusted-source mode
    -- "these are the same condition" -- so what this decides implies (H-SUPP)
    and can never admit a point the rank equality refuses. It is used as a FAST
    ADMIT PATH for that reason and for no other: where it holds, Eq.
    ``eq:hsupp-check`` holds by the claim's own inclusion and need not be
    computed; where it fails, nothing follows, and the rank equality is what
    decides.

    AS THE DECIDER IT WOULD REFUSE TOO MUCH: a block failing
    ``J_s > 0`` may still attain maximal support, and withdrawing ``h_lb``
    there would withdraw it from a run the claim admits. That would be safe --
    withdrawal is never a weakening -- and it is not the claim's rule.

    ``admissible`` is an isometry onto ``S_A (x) H(Q_s)`` (contract
    Eq. ``eq:SA``), or ``None`` for the whole block. The test is positive
    definiteness of the compression ``V^dagger omega_s V``, which
    Eq. ``eq:Wcs-bound`` records as the same condition as ``J_s > 0`` in
    trusted-source mode and ``omega_s > 0`` in untrusted-source mode. It does
    not depend on WHICH orthonormal basis of ``S_A`` the isometry carries: two
    admissible bases differ by a unitary on ``A_0``, and congruence by a unitary
    preserves definiteness (Remark ``rem:basis-invariance`` (a)-(b)).
    """
    block = as_matrix(omega_s)
    if admissible is None:
        return is_positive_definite(block)
    lift = np.asarray(admissible, dtype=np.complex128)
    return is_positive_definite(as_matrix(lift.conj().T @ block @ lift))


def pullback_trace_power_gradient(
    branch: ClassBranch,
    omega_s: Matrix,
    alpha: float,
    *,
    admissible: Matrix | None = None,
    perturbation: float = 0.0,
    support_established: bool = False,
) -> Matrix:
    """Return ``A^dagger (grad T(X) - 1) A`` for one announcement class.

    The object Eq. ``eq:grad-pieces`` needs: ``G^dagger[grad T(X) - 1]`` for
    ``G(sigma) = A sigma A^dagger``. The identity term is
    ``grad_X tr[X] = 1``, whose pullback is ``A^dagger A``. In trusted-source
    mode Eq. ``eq:grad-pieces`` conjugates the result by ``chi^dagger``, which
    the caller does; Eq. ``eq:grad-pieces-un`` drops that conjugation and this
    IS the Choi-form piece.

    At maximal support the divided-difference sum is restricted to the strictly
    positive spectrum of ``X`` -- rule (a) of Theorem ``thm:gradient`` (i) --
    while ``Y`` and ``Z(Y^{alpha-1})`` stay ambient, rule (b). See the module
    docstring.

    Args:
        branch: the announcement class' Kraus operator.
        omega_s: the state block ``omega_s`` on ``A (x) Q_s``.
        alpha: the Renyi order, in the structural domain ``(1, inf)``.
        admissible: an isometry onto ``S_A (x) H(Q_s)`` of Eq. ``eq:SA``, or
            ``None`` for the whole block. It is what makes the maximal-support
            test correct for a SINGULAR ``tau_A``, where no feasible ``omega_s``
            is positive definite on the ambient block.
        perturbation: the explicit perturbation of Theorem ``thm:gradient``
            (ii); ``0.0`` selects exact face compression.
        support_established: whether the CALLER has already decided (H-SUPP)
            for this ``(chat, s)`` by Eq. ``eq:hsupp-check``.
            :func:`deficit_gradient` does, on the AGGREGATE operator the claim
            names, which is the only place the aggregate exists; this function
            sees one class and cannot form it. Left ``False`` -- a caller
            entering this module's API directly -- the SUFFICIENT condition
            ``J_s > 0`` of Eq. ``eq:Wcs-bound`` is used instead, which implies
            (H-SUPP) exactly and so refuses more than the claim does and never
            less.

    Raises:
        GradientHypothesisError: if (H-SUPP) was not established and the
            sufficient condition fails at this iterate, with no perturbation
            requested. Theorem ``thm:gradient`` (ii) forbids evaluating a
            gradient there.
        SupportError: if the branch operator vanishes at this iterate.
    """
    check_alpha_structural(alpha)
    dimension = branch.kraus.shape[1]
    if branch.kraus.size == 0:
        return np.zeros((dimension, dimension), dtype=np.complex128)
    operator = branch_operator(branch, as_matrix(omega_s))
    # (H-SUPP) IS DECIDED BY THE CALLER, ON THE AGGREGATE, OR BY THE SUFFICIENT
    # CONDITION HERE. Eq. eq:hsupp-check compares rank X_{chat,s} -- the
    # aggregate over the passing classes, counted against THAT block's own
    # spectral radius -- with dim W_{chat,s}, and this function holds one
    # class, so it cannot form either side
    # (comparing class by class measures each against its own radius and
    # admits where the claim refuses). :func:`deficit_gradient` decides it once
    # per pair and says so; a direct caller who has not gets the SUFFICIENT
    # condition J_s > 0, which implies (H-SUPP) exactly and therefore refuses
    # more and never less.
    if (
        perturbation == 0.0
        and not support_established
        and not is_support_maximal(omega_s, admissible)
    ):
        raise GradientHypothesisError(
            "Theorem thm:gradient (ii): gradients may be evaluated only at "
            "iterates whose support is maximal, in the sense of Eq. eq:Wcs. "
            "The state block is singular on the admissible Alice subspace S_A "
            "of Eq. eq:SA, so J_s > 0 -- the SUFFICIENT condition of "
            "Eq. eq:Wcs-bound -- does not hold, and (H-SUPP) was not "
            "established by the caller. Eq. eq:hsupp-check is the claim's own "
            "decider and is taken on the AGGREGATE operator over the passing "
            "classes, which this function does not hold; deficit_gradient is "
            "where a run decides it. Supply an explicit perturbation, or move "
            "the iterate",
            reason=_SUPPORT_REASON,
        )
    if perturbation > 0.0:
        operator = perturb_onto_face(
            operator, z_invariant_face(branch, admissible), perturbation
        )
    trace = float(np.real(np.trace(operator)))
    if trace <= 0.0:
        raise SupportError(
            "the branch operator vanishes at this iterate, where T is not "
            "differentiable (Theorem thm:gradient (ii))"
        )
    normalized = np.asarray(operator / trace, dtype=np.complex128)
    exponent = 1.0 / alpha
    values, vectors = support_spectrum(normalized)
    positive = values > 0.0
    support_values = values[positive]
    support_vectors = vectors[:, positive]
    # Y = Z(X^p) is formed on the AMBIENT space: the pinching moves weight out
    # of supp X and compressing it here would compute a different number.
    pinched = pinch(psd_power(normalized, exponent), labels=branch.labels)
    outer = pinch(psd_power(pinched, alpha - 1.0), labels=branch.labels)
    pulled = branch.kraus.conj().T @ support_vectors
    compressed = support_vectors.conj().T @ outer @ support_vectors
    kernel = divided_difference(support_values, exponent)
    gradient = alpha * pulled @ (kernel * compressed) @ pulled.conj().T
    identity_part = branch.kraus.conj().T @ branch.kraus
    return np.asarray(
        hermitian_part(np.asarray(gradient - identity_part, dtype=np.complex128)),
        dtype=np.complex128,
    )


def admissible_isometries(maps: GeneratedMaps) -> dict[str, Matrix]:
    """Return, per sector, an isometry onto ``S_A (x) H(Q_s)`` (Eq. ``eq:SA``).

    Built from the declaration alone, so it is the same in every coordinate
    system and does not move with the iterate. In untrusted-source mode and for
    a full-rank ``tau_A`` every one of them is the identity.
    """
    return {
        sector: admissible_isometry(maps.declaration, sector)
        for sector in maps.sectors
    }


def deficit_gradient(
    maps: GeneratedMaps,
    chat: str,
    sector: str,
    omega_s: Matrix,
    alpha: float,
    *,
    admissible: Matrix | None = None,
    perturbation: float = 0.0,
) -> Matrix:
    """Return ``grad_{omega_s} f_{chat,s}``, the state-form deficit gradient.

    ``f = T - tr G`` (Eq. ``eq:f-def``), so the gradient is
    ``G^dagger[grad T(X) - 1]`` summed over the announcement classes of the
    branch (which occupy orthogonal output blocks; see
    :mod:`certiqs_key.meat_core.objective.branch`). ``admissible`` defaults to the
    isometry the declaration itself determines (Eq. ``eq:SA``).
    """
    branch = maps.branches[chat][sector]
    dimension = maps.declaration.block_dim(sector)
    lift = admissible_isometries(maps)[sector] if admissible is None else admissible
    # (H-SUPP), DECIDED ONCE FOR THE PAIR AND BY Eq. eq:hsupp-check.
    #
    # THE REFERENCE IS READ AND NOT RECOMPUTED: it is a function of the
    # declaration and W_tau, built once per (chat, s) when the maps were
    # generated, and frank-wolfe/req:support-rank-check requires it to be
    # computed "never from an iterate". Reading it here is what makes that
    # true of every gradient evaluation rather than of the first.
    #
    # THE LEFT SIDE IS THE AGGREGATE X_{chat,s}: lem:fo-face defines X as the
    # sum over the passing classes, and the remark counts its eigenvalues
    # "RELATIVE TO THAT BLOCK'S OWN SPECTRAL RADIUS". Both windows being
    # relative, comparing class by class would measure each against its own
    # radius and admit a point the claim refuses whenever two classes differ in
    # scale by more than 1 / support_cutoff.
    # THIS IS THE ONE PLACE THE AGGREGATE EXISTS, so it is the one place
    # the hypothesis can be decided as the claim states it.
    #
    # THE SUFFICIENT CONDITION IS NOT USED AS A FAST ADMIT PATH HERE: J_s > 0
    # implies the EXACT equality, but the computed aggregate rank can still
    # fall short of dim W when a class is small, so admitting on it would admit
    # what the claim's computed decider refuses.
    # It remains the test for a direct caller of pullback_trace_power_gradient,
    # where it refuses more and never less.
    reference = maps.support_references[(chat, sector)]
    established = perturbation > 0.0
    if not established:
        aggregate = aggregate_branch_operator(branch, as_matrix(omega_s))
        if not attains_the_reference_rank(aggregate, reference):
            raise GradientHypothesisError(
                "Theorem thm:gradient (ii) and frank-wolfe/rem:fo-interface "
                "(2): gradients may be evaluated only at iterates whose "
                "support is maximal, and Eq. eq:hsupp-check fails at this one "
                f"-- rank X_{{chat,s}} = {support_rank(aggregate)} against "
                f"dim W_{{chat,s}} = {reference}, the rank counted on the "
                "AGGREGATE over the passing classes at the support_cutoff row "
                "and the reference as rank K at sqrt(support_cutoff), the same "
                "row read on K K^dagger. "
                "supp G(omega) is then a proper subspace of W_{chat,s} and a "
                "direction leaving it has an infinite one-sided derivative. "
                "Supply an explicit perturbation, or move the iterate",
                reason=_SUPPORT_REASON,
            )
        established = True
    total = np.zeros((dimension, dimension), dtype=np.complex128)
    for klass in branch.classes:
        total = total + pullback_trace_power_gradient(
            klass,
            omega_s,
            alpha,
            admissible=lift,
            perturbation=perturbation,
            support_established=established,
        )
    return total


def state_gradient(
    maps: GeneratedMaps,
    q: Mapping[str, float],
    omega: Mapping[str, Matrix],
    alpha: float,
    *,
    perturbation: float = 0.0,
) -> ObjectiveGradient:
    """Return the state-form gradient of ``O_alpha`` (Corollary cor:full-gradient).

    The hypotheses are enforced AS LEMMA ``lem:fo-khyp`` (iii) WEAKENS THEM
    (claim C22b): ``q(chat) > 0`` and ``P_chat > 0`` for every
    ``chat in Chat_acc``, ``K_chat > 0`` for every
    ``chat in Chat_key n Chat_acc``, and each branch operator support-maximal
    in the sense of Eq. ``eq:Wcs``. A point failing them raises
    :class:`~certiqs_key.meat_core.errors.GradientHypothesisError`, which carries the
    machine-readable withdrawal reason, rather than returning a number.

    ``Gamma^{(s)}_chat`` is taken in its STATE form ``sum M_x (x) F_v^{(s)}``,
    which is Eq. ``eq:grad-pieces-un`` outright in untrusted-source mode and, in
    trusted-source mode, the operator whose ``chi^dagger``-conjugate is
    Eq. ``eq:grad-pieces``'s ``(W^dagger M_x W) (x) F_v^{(s)}`` -- Corollary
    ``cor:full-gradient``: "in trusted-source mode the same formulas conjugated
    by ``chi`` give the state-form gradients". :func:`choi_gradient` performs
    that conjugation, which is why the two coordinate systems share one formula
    here.
    """
    check_alpha_structural(alpha)
    values = evaluate_branches(maps, omega, alpha)
    # LEMMA lem:fo-khyp (iii), CLAIM C22b, IN BOTH ITS HALVES. The hypothesis
    # is checked on Chat_acc, and the two sums below are RESTRICTED to it --
    # "Eq. eq:grad-q is read as a vector in R^{Chat_acc} and the sums of
    # Eq. eq:grad-J are restricted to Chat_acc, respectively to
    # Chat_key n Chat_acc; BOTH RESTRICTIONS ARE IDENTITIES ON THAT SET, NOT
    # TRUNCATIONS" (lem:fo-khyp (ii) proves the identity).
    #
    # THE TWO HALVES STAND OR FALL TOGETHER. Weakening only the hypothesis
    # would leave the sums evaluating d(q, P) and its derivatives at a
    # chat OUTSIDE Chat_acc, where q(chat) = 0 at every point of AcceptSet by
    # (i) -- and the kernel derivatives of Eq. eq:grad-q and Eq. eq:grad-J are
    # stated for u > 0 and refuse u = 0 rather than returning a number. So a
    # declaration with Chat_acc a proper subset would still fail, one line
    # further down, and the rung would still be "unreachable for a whole class
    # of declarations for no mathematical reason".
    support = maps.acceptance_support
    check_gradient_hypotheses(q, values, maps.chat_key, support)
    live = set(maps.key_acceptance_support)
    admissible = admissible_isometries(maps)
    applied: dict[tuple[str, str], float] = {}

    q_gradient: dict[str, float] = {}
    for chat in support:
        weight = q[chat]
        value = values[chat]
        if chat in live:
            q_gradient[chat] = divergence_kernel_du(weight, value.p) + (
                divergence_kernel_du(weight, value.k) / (alpha - 1.0)
            )
        else:
            q_gradient[chat] = (alpha / (alpha - 1.0)) * divergence_kernel_du(
                weight, value.p
            )

    blocks: dict[str, Matrix] = {}
    for sector in maps.sectors:
        dimension = maps.declaration.block_dim(sector)
        total = np.zeros((dimension, dimension), dtype=np.complex128)
        for chat in support:
            weight = q[chat]
            value = values[chat]
            gamma = as_matrix(maps.statistics_operator[chat][sector])
            if chat in live:
                total = total + divergence_kernel_dv(weight, value.p) * gamma
                # C7 / Remark ``rem:classes`` (i): the deficit is IDENTICALLY
                # ZERO on a key-inert sector, so it is not evaluated there. See
                # the module docstring, "WHY THE KEY-ACTIVE RESTRICTION IS TAKEN
                # HERE AND NOT IN THE OBJECTIVE".
                if maps.key_inert[(chat, sector)]:
                    deficit = np.zeros((dimension, dimension), dtype=np.complex128)
                else:
                    deficit = deficit_gradient(
                        maps,
                        chat,
                        sector,
                        as_matrix(omega[sector]),
                        alpha,
                        admissible=admissible[sector],
                        perturbation=perturbation,
                    )
                    if perturbation > 0.0:
                        applied[(chat, sector)] = perturbation
                total = total + (
                    divergence_kernel_dv(weight, value.k) / (alpha - 1.0)
                ) * (gamma + deficit)
            else:
                total = (
                    total
                    + (alpha / (alpha - 1.0))
                    * divergence_kernel_dv(weight, value.p)
                    * gamma
                )
        blocks[sector] = hermitian_part(total)
    return ObjectiveGradient(q=q_gradient, blocks=blocks, perturbations=applied)


def choi_gradient(
    maps: GeneratedMaps,
    parametrization: ChoiParametrization,
    q: Mapping[str, float],
    choi: Mapping[str, Matrix],
    alpha: float,
    *,
    perturbation: float = 0.0,
) -> ObjectiveGradient:
    """Return the Choi-form gradient of Eq. ``eq:grad-J``.

    Corollary ``cor:full-gradient`` gives the Choi form directly, with
    ``Gamma^{(s)}_chat = sum_{(x,v)} (W^dagger M_x W) x F_v^{(s)}`` and
    ``Delta^{(s)}_chat = chi^dagger(G^dagger[grad T - 1])``. Both are the
    ``chi``-conjugates of the state-form pieces, which is why this function
    conjugates the state-form gradient rather than re-deriving it: one formula,
    two coordinate systems, and the agreement of the two paths is testable.

    In UNTRUSTED-source mode ``chi`` is the identity, so this returns the state
    form unchanged -- which is what Eq. ``eq:grad-pieces-un`` says: the pieces
    "lose their ``W_tau`` conjugation", and the state form is primary there,
    "the Choi form being its pullback rather than the other way round".
    """
    omega = parametrization.state_from_choi(choi)
    gradient = state_gradient(maps, q, omega, alpha, perturbation=perturbation)
    blocks = {
        sector: parametrization.chi_adjoint(sector, block)
        for sector, block in gradient.blocks.items()
    }
    return ObjectiveGradient(
        q=gradient.q, blocks=blocks, perturbations=gradient.perturbations
    )


def check_gradient_hypotheses(
    q: Mapping[str, float],
    values: Mapping[str, BranchValues],
    chat_key: tuple[str, ...],
    acceptance_support: tuple[str, ...],
) -> None:
    """Raise unless (H-POS) holds at a point, QUANTIFIED ON ``Chat_acc``.

    Hypothesis (H-POS) of Theorem ``thm:firstorder`` (ii), as Lemma
    ``lem:fo-khyp`` (iii) -- claim C22b -- weakens Corollary
    ``cor:full-gradient``'s "for all ``chat``" to: ``q(chat) > 0`` and
    ``P_chat > 0`` for every ``chat in Chat_acc``, and ``K_chat > 0`` for every
    ``chat in Chat_key n Chat_acc``.

    THE WEAKENING IS NOT AN OPTIMIZATION AND THE SET IS NOT INTERCHANGEABLE
    WITH ``Chat``. The theorem states it on ``Chat_acc`` "because on Chat it
    would be UNSATISFIABLE whenever Chat_acc is a proper subset, a case
    def:admissible-acceptance-set admits ... so that the first-order rung would be
    unreachable for a whole class of declarations for no mathematical reason". Every
    ``q`` in ``AcceptSet`` vanishes off ``Chat_acc`` by ``lem:fo-khyp`` (i), so on
    ``Chat`` the first clause fails at the first such coordinate at EVERY
    admissible iterate.

    Args:
        q: the acceptance-side iterate ``q_t``.
        values: ``P_chat`` and ``K_chat`` at the point.
        chat_key: ``Chat_key``, the key-live acceptance values.
        acceptance_support: ``Chat_acc`` of Eq. ``eq:chacc-def``, from
            :func:`certiqs_key.meat_core.objective.support.acceptance_support`.

    Raises:
        GradientHypothesisError: carrying the machine-readable withdrawal
            reason ``gradient_hypothesis_positivity`` of Requirement
            ``req:first-order-withdrawal``. The DRIVER converts it into a withdrawal
            that leaves the estimate standing; letting it escape a run would
            report nothing at all, which that rule forbids.
    """
    live = set(chat_key)
    for chat in acceptance_support:
        weight = q[chat]
        value = values[chat]
        if weight <= 0.0 or value.p <= 0.0 or not math.isfinite(value.p):
            raise GradientHypothesisError(
                "hypothesis (H-POS) of Theorem thm:firstorder, weakened to the "
                "acceptance support by Lemma lem:fo-khyp (iii): q(chat) > 0 "
                f"and P_chat > 0 are required for every chat in Chat_acc; at "
                f"{chat!r} they are {weight!r} and {value.p!r}. Corollary "
                "cor:full-gradient is stated at such a point",
                reason=_POSITIVITY_REASON,
            )
        if chat in live and value.k <= 0.0:
            raise GradientHypothesisError(
                "hypothesis (H-POS) of Theorem thm:firstorder, weakened by "
                "Lemma lem:fo-khyp (iii): K_chat > 0 is required for every "
                f"chat in Chat_key n Chat_acc; at {chat!r} it is {value.k!r}. "
                "Corollary cor:full-gradient is stated at such a point",
                reason=_POSITIVITY_REASON,
            )
