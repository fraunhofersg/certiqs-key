"""Port Grams: THE CANONICAL OBJECT, and what depends only on it.

Definition ``def:gram`` with Theorems ``thm:port-grams`` and
``thm:representation-independence``.

    (A_k)_{j j'} = sum over i in P_k of conj(Gamma_{i j}) Gamma_{i j'}

The ``matrix_convention`` (``interface.yaml`` ``conventions``) fixes that index
order: rows of ``Gamma`` are OUTPUTS and columns are INPUTS, so that
``alpha^dagger A_k alpha`` is the mean photon number a coherent input of
amplitude ``alpha`` delivers to port ``k``. A transposed index here would be
silent everywhere else.

THE ONE STRUCTURAL FACT
=======================
Theorem ``thm:representation-independence`` (i): the click-pattern POVM depends on the
instrument ONLY through ``{A_k}``, and every admissible family arises from some
instrument. So the Gram family is the canonical object, an instrument matrix is a
presentation of it, and the three input routes converge here
(``interface.yaml`` ``input_routes.convergence``) BEFORE any photon-number
reasoning begins. No output key of the outputs table carries ``Gamma``.

VACUUM ELIMINATION IS EXACT, NOT AN APPROXIMATION
=================================================
Theorem ``thm:port-grams`` (iv): the pullback depends on the instrument only through
``Gamma_Inp``, the columns indexed by the DECLARED input modes, so dropping the
others is EXACT, an identity and not an approximation (Lemma ``lem:vacelim``,
Assumption ``ass:vac``). And (v): any unitary dilation whose block from ``Inp``
to the port modes agrees with ``Gamma``'s induces the SAME measurement, so the
sub-unitary and unitary-dilation descriptions are interchangeable.

A DECLARED SOURCE MODE IS NOT A VACUUM ANCILLA. Remark ``rem:lossvsprobe``:
eliminating a probe mode would silently replace the probe by vacuum, so the
derived POVM would describe a different device than the one deployed, and since
the probe is a countermeasure, that mismatch is SECURITY-RELEVANT. The column
restriction of :func:`restrict_to_inputs` therefore keeps every declared input
column, channel and source alike, and the probe is handled downstream by
the construction of the setting family
(:func:`certiqs_key.receiver.settings.setting_construction`).

THE RANK-ONE BRANCH IS A CERTIFIED BRANCH, NEVER A DEFAULT
===========================================================
Remark ``rem:rankone``, Requirement ``req:one-mode-per-port`` and
spec/architecture.md section 3.2 (the receiver core). Nothing in this
package computes differently when a rank is one: :func:`one_mode_per_port`
REPORTS the Theorem ``thm:representation-independence`` (iv) verdict and no caller
consumes it. Remark ``rem:effrank`` names the one operation that can change the answer
-- a non-uniform within-port attenuation -- and requires the rank to be recomputed
AFTER every efficiency, never before, which is why
:mod:`certiqs_key.receiver.efficiency` returns a new family rather than a
correction.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

from certiqs_key.receiver.errors import HypothesisError
from certiqs_key.receiver.numerics import (
    Matrix,
    NumericalTolerances,
    epsilon_rank,
    hermitian_part,
    identity,
    lambda_max,
    lambda_min,
    residual_norm,
)
from certiqs_key.receiver.reasons import Refusal, RefusalReason

__all__ = [
    "DeficiencyIdentity",
    "ExtinctionVerdict",
    "GramFamily",
    "check_gram_family_admissible",
    "check_rank_against_port_sizes",
    "deficiency_identity",
    "extinction_criterion",
    "one_mode_per_port",
    "port_grams",
    "realizing_instrument",
    "restrict_to_inputs",
    "unitary_dilation",
]


def restrict_to_inputs(gamma: Matrix, input_indices: Sequence[int]) -> Matrix:
    """Return ``Gamma_Inp``: the columns of ``Gamma`` at the declared inputs.

    The columns are taken in the SUBSYSTEM ORDER -- ``Inp_C`` before ``Inp_S``
    -- because that is the order that indexes ``C^Inp`` and therefore every
    Gram (the ``subsystem_order`` convention). Theorem ``thm:port-grams`` (iv)
    makes the restriction exact.
    """
    return np.asarray(gamma[:, list(input_indices)], dtype=np.complex128)


def port_grams(
    gamma_inp: Matrix, port_rows: Sequence[Sequence[int]]
) -> tuple[Matrix, ...]:
    """Return ``{A_k}`` from ``Gamma_Inp`` by Eq. ``eq:gramdef``.

    ``port_rows`` gives, per port, the OUTPUT-mode row indices the port
    collects. A row in no port contributes to no ``A_k``, which is Remark
    ``rem:unmonitored``: the partition is a DECLARATION with no observable
    content beyond the ``A_k`` it produces.
    """
    grams: list[Matrix] = []
    for rows in port_rows:
        block = gamma_inp[list(rows), :]
        grams.append(np.asarray(block.conj().T @ block, dtype=np.complex128))
    return tuple(grams)


@dataclass(frozen=True)
class GramFamily:
    """An ordered family ``{A_k}`` on ``C^Inp``, with its port labels."""

    labels: tuple[str, ...]
    matrices: tuple[Matrix, ...]

    def __post_init__(self) -> None:
        """Check that the family is a rectangular list of square matrices."""
        if len(self.labels) != len(self.matrices):
            raise HypothesisError("each port Gram needs exactly one port label")
        dimensions = {matrix.shape for matrix in self.matrices}
        if len(dimensions) > 1:
            raise HypothesisError(f"the Grams have differing shapes {dimensions}")

    @property
    def port_count(self) -> int:
        """Return ``K``."""
        return len(self.matrices)

    @property
    def dimension(self) -> int:
        """Return ``|Inp|``."""
        return int(self.matrices[0].shape[0]) if self.matrices else 0

    def subset(self, ports: Sequence[int]) -> Matrix:
        """Return ``A_J = sum_{k in J} A_k`` -- Definition ``def:gram``."""
        total = np.zeros((self.dimension, self.dimension), dtype=np.complex128)
        for index in ports:
            total = total + self.matrices[index]
        return np.asarray(total, dtype=np.complex128)

    @property
    def a_sigma(self) -> Matrix:
        """Return ``A_Sigma = A_{[K]}``."""
        return self.subset(range(self.port_count))

    @property
    def deficiency(self) -> Matrix:
        """Return ``1 - A_Sigma`` -- Eq. ``eq:deficiency``."""
        return np.asarray(identity(self.dimension) - self.a_sigma, dtype=np.complex128)

    def ranks(self, epsilon: float) -> tuple[int, ...]:
        """Return ``rk_{eps_2}(A_k)`` per port -- Eq. ``eq:eps2rank``.

        THE DECLARED ``eps_2`` DECIDES IT AND NOTHING ELSE. Requirement
        ``req:tolerance-tests``: every rank statement this module decides on
        floating-point data is decided by Eq. ``eq:eps2rank``, and NO OTHER RULE
        IS LICENSED, there or at Theorem ``thm:representation-independence``
        (iv). The argument is REQUIRED and has no default: a library default
        such as NumPy's machine-epsilon cutoff is RELATIVE, UNDECLARED, AND
        INVISIBLE IN THE ARTIFACT (Remark ``rem:ranktwosided``).
        """
        return tuple(epsilon_rank(matrix, epsilon) for matrix in self.matrices)


def check_gram_family_admissible(
    family: GramFamily, tolerances: NumericalTolerances
) -> Refusal | None:
    """Return a refusal if ``{A_k}`` is not admissible -- Def. ``def:tolmap`` (i).

    Admissible means ``A_k >= 0`` for every ``k`` and ``sum_k A_k <= 1``
    (Definition ``def:gram``). THE CONTRACT NAMES THE TOLERANCE THAT DECIDES
    IT: Definition ``def:tolmap`` (i), "the family is admitted when
    ``lmin(A_k) >= -eps_2`` for every ``k`` and ``lmax(A_Sigma) <= 1 + eps_2``".

    BOTH COMPARISONS ARE NON-STRICT AND ARE WRITTEN THE WAY THE ITEM WRITES
    THEM. A family with ``lmin(A_k) = -eps_2`` exactly is ADMITTED, and so is
    one with ``lmax(A_Sigma) = 1 + eps_2`` exactly -- which the exact condition
    ``sum_k A_k <= 1`` excludes, deliberately: the argument is the one Remark
    ``rem:bound-data-band`` gives for widening item (iv), that a lossless
    receiver has ``lmax = 1`` exactly and a computed value one rounding unit
    above 1 would refuse the simplest legitimate device.

    ONE TEST, ONE VERDICT. Item (i) closes with the reason no separate tolerance
    is added: Eq. ``eq:res2`` gives ``r_2 = max_k max{0, -lmin(A_k)}``, so THE
    SAME DECLARED NUMBER BOUNDS THE RESIDUAL AND DECIDES THE ADMISSION, IN THE
    SAME UNITS -- a family refused here has ``r_2 > eps_2`` and would refuse at
    the residual too.

    On routes (ii) and (iii) ``sum_k A_k <= 1`` is an exact consequence of
    ``Gamma^dagger Gamma <= 1`` (Theorem ``thm:port-grams`` (i)), and route (ii)
    carries no separate Gram admissibility check; that implication between exact
    quantities transports NO ADMISSION between computed ones (Remark
    ``rem:bound-data-band``; ``interface.yaml``
    ``inputs.instrument_matrix.what_the_derivation_transports``).
    """
    for label, matrix in zip(family.labels, family.matrices, strict=True):
        if matrix.shape[0] != matrix.shape[1]:
            return Refusal(
                RefusalReason.PORT_GRAMS_NOT_ADMISSIBLE,
                f"the Gram of port {label!r} is not square",
            )
        # THE SPECTRAL NORM, WHICH IS THE ONE THE CONTRACT NAMES. Definition
        # def:residuals fixes ||.|| as the spectral norm throughout eq:res1 to
        # eq:rhodef, and eq:rhodef's first entry is exactly this quantity,
        # ||X - X^dagger||. Measuring it entrywise here and spectrally at
        # eq:rhodef would be two readings of one defect at two sites -- a drift
        # the one named norm exists to prevent -- and numerics.is_hermitian
        # already reads it spectrally.
        defect = residual_norm(matrix - matrix.conj().T)
        if defect > tolerances.eps_2:
            return Refusal(
                RefusalReason.PORT_GRAMS_NOT_ADMISSIBLE,
                f"the Gram of port {label!r} is not Hermitian: "
                f"||A - A^dagger|| is {defect} in the spectral norm, above the "
                f"declared eps_2 = {tolerances.eps_2}",
            )
        smallest = lambda_min(matrix)
        if smallest < -tolerances.eps_2:
            return Refusal(
                RefusalReason.PORT_GRAMS_NOT_ADMISSIBLE,
                f"the Gram of port {label!r} is not positive semidefinite: "
                f"lmin = {smallest}, below -eps_2 = {-tolerances.eps_2}",
            )
    largest = lambda_max(family.a_sigma)
    if largest > 1.0 + tolerances.eps_2:
        return Refusal(
            RefusalReason.PORT_GRAMS_NOT_ADMISSIBLE,
            f"sum_k A_k is not bounded by the identity: lmax(A_Sigma) = "
            f"{largest}, above 1 + eps_2 = {1.0 + tolerances.eps_2}",
        )
    return None


def check_rank_against_port_sizes(
    family: GramFamily, port_sizes: Sequence[int], tolerances: NumericalTolerances
) -> Refusal | None:
    """Return a refusal if ``rk_{eps_2}(A_k) > |P_k|`` -- Def. ``def:tolmap`` (ii).

    The route-(i) consistency condition between the declared Gram family and
    the declared port map. Theorem ``thm:port-grams`` (ii) is the full bound
    ``rk A_k <= min(|Inp|, |P_k|)``; the ``|Inp|`` half holds by construction
    for a square Gram, and this is the half that constrains DECLARED data
    against a DECLARED port map.

    **THE THRESHOLD IS DECLARED, AND IT IS** ``eps_2``, never a library's
    relative machine-epsilon cutoff. Definition ``def:tolmap`` (ii): the check
    is ``rk_{eps_2}(A_k) <= |P_k|`` with the ``eps_2``-rank of
    Eq. ``eq:eps2rank``, THE THRESHOLD ABSOLUTE AND EQUAL TO ``eps_2``, and the
    comparison inside the count is STRICT
    (:func:`certiqs_key.receiver.numerics.epsilon_rank`).

    THE CUTOFF IS STILL TWO-SIDED, and Remark ``rem:ranktwosided`` says so
    rather than repairing it. Over-reported: an exactly singular declared Gram
    whose zero eigenvalue evaluates at ``+2 tau`` is counted as one rank
    higher, and A DECLARATION CONSISTENT WITH ITS PORT MAP IS REFUSED -- this
    refusal, with the contract-verbatim ``port_gram_rank_exceeds_port_size``.
    Under-reported: a Gram whose exact rank is 2 but whose second eigenvalue is
    genuinely small, below ``tau``, is counted as rank 1, and A DECLARATION
    INCONSISTENT WITH ITS PORT MAP IS ADMITTED on a single-mode port. So the
    check is NOT REFUSE-ONLY, and the choice of ``tau`` is a choice about which
    declarations are accepted, not a numerical detail. What the rule buys is
    that both directions are consequences of a DECLARED number: "the rank the
    check used is a function of ``{A_k}`` and ``eps_2`` alone."
    """
    for label, rank, size in zip(
        family.labels, family.ranks(tolerances.eps_2), port_sizes, strict=True
    ):
        if rank > size:
            return Refusal(
                RefusalReason.PORT_GRAM_RANK_EXCEEDS_PORT_SIZE,
                f"port {label!r} collects {size} mode(s) but its declared Gram "
                f"has eps_2-rank {rank} at the declared eps_2 = "
                f"{tolerances.eps_2}; Def. def:tolmap (ii) requires "
                f"rk_{{eps_2}}(A_k) <= |P_k|",
            )
    return None


@dataclass(frozen=True)
class DeficiencyIdentity:
    """The two summands of Eq. ``eq:deficiencyid``, and the identity's defect.

    ``left_through_dilation`` is ``1 - Gamma_Inp^dagger Gamma_Inp`` and
    ``reached_unmonitored`` is ``Gamma_Inp^dagger E_un Gamma_Inp``. Lemma
    ``lem:deficiency``: both are positive semidefinite, and the identity holds
    for EVERY receiver instrument and is the correct check that loss was
    accounted for exactly once (also Theorem ``thm:efficiency`` (v)). Remark
    ``rem:wrongcheck`` is why a product of declared transmittances is NOT that
    check.
    """

    deficiency: Matrix
    left_through_dilation: Matrix
    reached_unmonitored: Matrix

    @property
    def defect(self) -> Matrix:
        """Return the residual matrix of Eq. ``eq:res3``."""
        return np.asarray(
            self.deficiency - self.reached_unmonitored - self.left_through_dilation,
            dtype=np.complex128,
        )


def deficiency_identity(
    gamma_inp: Matrix, family: GramFamily, unmonitored_rows: Sequence[int]
) -> DeficiencyIdentity:
    """Return the two summands of Eq. ``eq:deficiencyid`` and the deficiency."""
    unmonitored = gamma_inp[list(unmonitored_rows), :]
    reached = np.asarray(unmonitored.conj().T @ unmonitored, dtype=np.complex128)
    through = np.asarray(
        identity(int(gamma_inp.shape[1])) - gamma_inp.conj().T @ gamma_inp,
        dtype=np.complex128,
    )
    return DeficiencyIdentity(family.deficiency, through, reached)


def unitary_dilation(gamma: Matrix) -> Matrix:
    """Return the unitary extension ``U_Gamma`` of Eq. ``eq:dilationmatrix``.

    Lemma ``lem:dilation``: with the defect operators
    ``D_out = (1 - Gamma Gamma^dagger)^{1/2}`` and
    ``D_in = (1 - Gamma^dagger Gamma)^{1/2}``, the block matrix
    ``[[Gamma, D_out], [D_in, -Gamma^dagger]]`` is unitary and its block from
    the inputs ``M`` to the outputs ``M`` is ``Gamma``. Theorem ``thm:port-grams`` (v)
    is why the choice does not matter.
    """
    size = int(gamma.shape[0])
    d_out = _psd_square_root(identity(size) - gamma @ gamma.conj().T)
    d_in = _psd_square_root(identity(size) - gamma.conj().T @ gamma)
    top = np.hstack([gamma, d_out])
    bottom = np.hstack([d_in, -gamma.conj().T])
    return np.asarray(np.vstack([top, bottom]), dtype=np.complex128)


def realizing_instrument(family: GramFamily) -> Matrix:
    """Return the instrument of Theorem ``thm:representation-independence`` (ii): the rows of A_k^{1/2}.

    Every admissible family is the port-Gram family of some instrument, in
    which port ``k`` collects at most ``rk A_k <= |Inp|`` modes. The
    construction is ``C_k = A_k^{1/2}``, stacked as the rows of port ``k``;
    the returned matrix has ``K |Inp|`` rows, port ``k`` occupying the ``k``-th
    block of ``|Inp|`` of them.
    """  # noqa: E501
    blocks = [_psd_square_root(matrix) for matrix in family.matrices]
    return np.asarray(np.vstack(blocks), dtype=np.complex128)


@dataclass(frozen=True)
class ExtinctionVerdict:
    """The Corollary ``cor:extinction`` reading, with its dimension caveat."""

    input_dimension: int
    has_null_direction: bool
    rank: int
    criterion_applies: bool


def extinction_criterion(gram: Matrix, tolerance: float) -> ExtinctionVerdict:
    """Return the Corollary ``cor:extinction`` verdict for one port Gram.

    At ``|Inp| = 2``, ``rk A_k <= 1`` holds iff ``A_k = 0`` or some unit vector
    is completely extinguished. For ``|Inp| > 2`` THE TWO CONDITIONS ARE NOT
    EQUIVALENT: the existence of one null direction of a positive semidefinite
    ``A_k`` says only ``rk A_k <= |Inp| - 1``, and ``criterion_applies``
    carries exactly that caveat rather than leaving a reader to over-read the
    first sentence.

    ``tolerance`` is the DECLARED ``eps_2``: the null direction and the rank are
    two readings of the same spectrum, and Definition ``def:tolmap`` (ii) makes
    ``eps_2`` the one number that decides a rank here (Eq. ``eq:eps2rank``).
    """
    dimension = int(gram.shape[0])
    smallest = lambda_min(gram)
    return ExtinctionVerdict(
        input_dimension=dimension,
        has_null_direction=bool(smallest <= tolerance),
        rank=epsilon_rank(gram, tolerance),
        criterion_applies=dimension == 2,
    )


def one_mode_per_port(family: GramFamily, epsilon: float) -> bool:
    """Return the Theorem ``thm:representation-independence`` (iv) verdict, and never a default.

    ``True`` exactly when every ``rk_{eps_2}(A_k) <= 1``, in which case a
    one-mode-per-port instrument reproduces the POVM and the single row of
    port ``k`` is ``e^{i varphi_k} sqrt(lambda_k) u_k^dagger``, unique up to
    that phase. Requirement ``req:one-mode-per-port``: this is a CERTIFIED
    branch, used only where the criterion holds, and no computation in this
    package takes a different path when it holds.

    ``epsilon`` IS THE DECLARED ``eps_2`` AND IS REQUIRED. Requirement
    ``req:tolerance-tests`` names Theorem ``thm:representation-independence``
    (iv) explicitly: every rank statement this module decides on floating-point
    data is decided by Eq. ``eq:eps2rank``, and no other rule is licensed,
    THERE OR AT Theorem ``thm:representation-independence`` (iv).
    """  # noqa: E501
    return all(rank <= 1 for rank in family.ranks(epsilon))


def _psd_square_root(operator: Matrix) -> Matrix:
    """Return the positive semidefinite square root of a PSD operator."""
    spectrum, vectors = np.linalg.eigh(hermitian_part(operator))
    roots = np.sqrt(np.maximum(spectrum, 0.0))
    return np.asarray(
        vectors @ np.diag(roots.astype(np.complex128)) @ vectors.conj().T,
        dtype=np.complex128,
    )
