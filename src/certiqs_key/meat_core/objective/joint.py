"""The objective over JOINT SECTORS, in Choi coordinates per Alice sector.

``def:joint-sectors``, ``lem:joint-sectors``, ``lem:choi-factor``,
``thm:choi`` (the general format), ``def:dropped``, ``prop:drop-bound``,
``cor:drop-program`` and ``lem:rank-one-sector``.

WHY THE COORDINATES ARE CHOI COORDINATES AND NOT STATE COORDINATES
==================================================================
``lem:choi-factor`` (iii): with a factor ``W_t`` of ``tau_A^{(t)}`` the
objective, the statistics and their derivatives read Alice's side only through
``N^W_x = W^dagger M_x W``, and (iv): on the FULL frame those are exactly the
operators an ensemble-form declaration DECLARES. So one set of coordinates
serves both forms of (DX4), and in ensemble form **no ``M_x``, no inverse
square root of ``tau_A`` and no rank is ever formed** -- there is no code path
here that could form one, ``eq:ensemblepovm`` appearing nowhere in this
package. In untrusted-source mode ``W_t = 1_{A_t}``, ``J = omega`` and the
coupling is the single scalar equation, which is ``def:untrusted-choi``'s
degenerate reading of the same program.

WHAT IS FORMED IN FLOATING POINT HERE
=====================================
The Kronecker block ``F_v^{(s)} = (x)_f F^{f,(s_f)}_{v_f}`` of (DX3), through
:meth:`~certiqs_key.meat_core.declaration.general.GeneralDeclaration.bob_block`
-- inside the objective, which is the one place the general format licenses,
and never as declared data. The zero predicate of ``def:joint-sectors`` is
decided PER FACTOR and forms nothing.

THE KEY-INERT AND DROPPED RESTRICTIONS, AND WHICH IS WHICH
==========================================================
* **Key-inert joint pairs contribute ``f == 0`` identically**
  (``lem:joint-sectors`` (iii)), so restricting the sum to
  ``J_K(chat)`` is AN IDENTITY and not a bound. :func:`evaluate_joint_branch`
  takes it by default and ``skip_key_inert=False`` computes the
  identity instead, which is what the equal-paths test compares. THE ACCEPTED
  FORMAT'S PATH IS NOT TOUCHED BY THIS: it goes on summing every sector, since
  skipping there would move the last bits of a frozen number for no
  mathematical gain.
* **A dropped pair's deficit is replaced by zero** (``def:dropped``), which is
  a RATE LOSS in the safe direction (``prop:drop-bound``) and is never an
  identity unless the pair was key-inert anyway. The two are kept apart in the
  code as they are in the claims: the dropped set is a run's choice and is
  reported with its own name, ``h_low^D``.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from functools import cached_property
from types import MappingProxyType
from typing import NamedTuple

import numpy as np
import numpy.typing as npt

from certiqs_key.domain.manifest import KeyHolder
from certiqs_key.foundations.exact_admission import is_hermitian_exact, to_exact
from certiqs_key.foundations.kernel import divergence_kernel
from certiqs_key.meat_core.declaration.general import GeneralDeclaration
from certiqs_key.meat_core.errors import DeclarationError
from certiqs_key.meat_core.objective.branch import trace_power_pinched
from certiqs_key.meat_core.objective.choi import ChoiIsometryError, Coupling
from certiqs_key.meat_core.objective.linalg import (
    Matrix,
    as_matrix,
    psd_power,
)
from certiqs_key.meat_core.objective.objective import check_alpha_structural
from certiqs_key.meat_core.objective.support import BranchSupport, branch_support

#: A joint sector ``(t, s)`` of ``def:declaration`` (DX1).
JointSector = tuple[str, str]

#: A pair ``(x, v)`` with ``v`` the PRODUCT letter of (DX3).
OutcomePair = tuple[str, str]

#: A transcript ``kappa = (kappa_1, ..., kappa_L)`` of ``eq:transcript``.
Transcript = tuple[str, ...]


@dataclass(frozen=True)
class AliceFrame:
    """The frame of ONE Alice sector, ``lem:choi-factor`` (i), (ii).

    ``w`` is a factor ``W_t`` with ``W_t W_t^dagger = tau_A^{(t)}`` -- "any
    factor serves" -- and ``input_dim`` is ``d_{A_{0,t}}``. Two constructions
    appear, both of the C11 group applied sector by sector:

    * the DIAGONAL frame, construction (b) of ``lem:choi-marginal``, where
      the declared ``tau_A^{(t)}`` is diagonal bit for bit: ``iota_t`` the
      coordinate injection onto the indices with ``t_i != 0``, in increasing
      order, and ``W_t = (tau_A^{(t)})^{1/2} iota_t``. Tight, recorded as the
      ``support`` frame;
    * the FULL frame, construction (a), ``A_{0,t} = A_t``, ``iota_t = 1`` and
      ``W_t = (tau_A^{(t)})^{1/2}``: in POVM form wherever ``tau_A^{(t)}`` is
      not diagonal, and always in ensemble form, which ``lem:choi-factor``
      (iv) needs, where it is what makes ``N^W_x`` the DECLARED ``N_x``. It
      is non-tight where ``tau_A^{(t)}`` is singular, so its rows are the
      CONJUGATED rows, which "is exact on every frame".

    Neither construction reads a computed spectrum: which one applies, and
    which indices (b) keeps, are bit-level tests of declared entries against
    zero, so no rank of ``tau_A`` is decided at any window.

    In untrusted-source mode there is no marginal and ``W_t = 1_{A_t}``.
    """

    alice_sector: str
    w: Matrix
    iota: Matrix
    input_dim: int
    #: ``G_t = W_t^dagger W_t``, the operator the normalisation clause of
    #: ``frank-wolfe/rem:feas-tol`` (c') reads, kept because it is also what
    #: the rank-one closed form reads.
    gram: Matrix
    is_full_frame: bool


@dataclass(frozen=True)
class JointChoiParametrization:
    """``chi = (+)_{(t,s)} chi_{(t,s)}`` of ``thm:choi``, the general format.

    ONE COUPLING CONSTRAINT PER ALICE SECTOR in trusted-source mode --
    ``sum_s tr_{Q_s} J_{t,s} = 1_{A_{0,t}}`` -- so that ``Feas^J`` is a
    Cartesian product over ``T`` and the linear minimisation splits
    (``frank-wolfe/rem:fo-general-format`` (2)). In
    untrusted-source mode the single scalar equation
    ``sum_{(t,s)} tr J_{t,s} = 1`` couples every joint sector and nothing
    splits, which is the same statement that remark makes.
    """

    declaration: GeneralDeclaration
    frames: Mapping[str, AliceFrame]
    coupling: Coupling

    @property
    def joint_sectors(self) -> tuple[JointSector, ...]:
        """Return the joint sectors in their declared order, ``t`` slowest."""
        return self.declaration.joint_sectors

    def input_dim(self, alice_sector: str) -> int:
        """Return ``d_{A_{0,t}}``."""
        return self.frames[alice_sector].input_dim

    def block_dim(self, pair: JointSector) -> int:
        """Return the size of the Choi block of one joint sector."""
        alice_sector, sector = pair
        return self.input_dim(alice_sector) * self.declaration.sector_dim(sector)

    def alice_choi_operator(self, letter: str, alice_sector: str) -> Matrix:
        """Return ``N^W_x`` of ``eq:NfromW`` on one Alice sector.

        ``lem:choi-factor`` (iii) and (iv). In ensemble form this is the
        DECLARED ``N_x^{(t)}`` returned unchanged -- the frame being the full
        one, ``W_t^dagger M_x W_t = tau^{1/2} M_x tau^{1/2} = N_x`` by
        ``lem:ensemble-form`` (ii) -- and nothing is computed from it. In POVM
        form it is ``W_t^dagger M_x^{(t)} W_t``, formed here.
        """
        block = self.declaration.alice_block(letter, alice_sector)
        if self.declaration.is_ensemble_form:
            return block
        frame = self.frames[alice_sector]
        return np.asarray(frame.w.conj().T @ block @ frame.w, dtype=np.complex128)

    def chi(self, pair: JointSector, choi_block: Matrix) -> Matrix:
        """Return ``omega^{(t,s)} = (W_t (x) 1) J_{t,s} (W_t^dagger (x) 1)``."""
        alice_sector, sector = pair
        width = self.declaration.sector_dim(sector)
        lift = np.kron(self.frames[alice_sector].w, np.eye(width, dtype=np.complex128))
        return np.asarray(lift @ choi_block @ lift.conj().T, dtype=np.complex128)

    def chi_adjoint(self, pair: JointSector, operator: Matrix) -> Matrix:
        """Return ``chi^dagger(A) = (W^dagger (x) 1) A (W (x) 1)``."""
        alice_sector, sector = pair
        width = self.declaration.sector_dim(sector)
        lift = np.kron(self.frames[alice_sector].w, np.eye(width, dtype=np.complex128))
        return np.asarray(lift.conj().T @ operator @ lift, dtype=np.complex128)

    def state_from_choi(
        self, choi: Mapping[JointSector, Matrix]
    ) -> dict[JointSector, Matrix]:
        """Return the joint-sector state list of a Choi point."""
        return {
            pair: self.chi(pair, as_matrix(choi[pair])) for pair in self.joint_sectors
        }


class MarginalFrame(NamedTuple):
    """A declared isometry of ``eq:iota`` and the root of ``tau_A`` it pairs with.

    ``W_tau = root @ iota`` is ``eq:Wtau``. ``full`` names construction (a),
    ``iota = 1``; otherwise the frame is construction (b)'s.
    """

    iota: Matrix
    root: Matrix
    full: bool


def marginal_root(tau: Matrix) -> Matrix:
    """Return ``tau^{1/2}`` of a declared ``tau_A``, with NO RELATIVE CUTOFF.

    ``eq:Wtau`` and ``eq:WWtau`` read the positive semidefinite square root of
    the declared marginal, every positive eigenvalue included. A bit-diagonal
    ``tau`` (every off-diagonal entry the datum ``0``) has the root
    ``diag(sqrt(t_i))``, formed entry by entry with no spectral decomposition.
    Otherwise the root is taken by ``eigh`` and ONLY NEGATIVE computed
    eigenvalues are clamped to ``0`` -- they are representation noise of an
    operator decided positive semidefinite exactly at admission -- and no
    eigenvalue is dropped for being small against the spectral radius, as
    :data:`~certiqs_key.meat_core.objective.linalg.SUPPORT_CUTOFF` would drop
    it. ``tau`` is decided
    exactly Hermitian at admission, so no Hermiticity window is read here.
    """
    matrix = np.asarray(tau, dtype=np.complex128)
    if _is_bit_diagonal(matrix):
        return np.asarray(
            np.diag(np.sqrt(np.maximum(np.real(np.diag(matrix)), 0.0))),
            dtype=np.complex128,
        )
    values, vectors = np.linalg.eigh(matrix)
    roots = np.sqrt(np.maximum(values, 0.0))
    return np.asarray((vectors * roots) @ vectors.conj().T, dtype=np.complex128)


def _is_bit_diagonal(matrix: Matrix) -> bool:
    """Whether every off-diagonal entry is the datum ``0``, at no window.

    ``lem:choi-marginal`` (b)'s precondition, by the bit-level test of
    ``def:classes`` (c): a ``tau_A`` that is only NEARLY diagonal is not
    diagonal.
    """
    off_diagonal = matrix - np.diag(np.diag(matrix))
    return not bool(np.any(off_diagonal))


def marginal_frame(tau: Matrix, *, full: bool) -> MarginalFrame:
    """Build a frame satisfying ``eq:iota`` for a declared ``tau_A``, exactly.

    Implements ``meat-core/lem:choi-marginal``'s two constructions, the ones
    the production path (:func:`joint_choi_parametrization`) builds:

    * (b), the DIAGONAL frame, when ``tau`` is bit-diagonal and ``full`` is
      not asked: ``iota`` the coordinate injection onto the indices with
      ``t_i != 0``, in increasing order. ``iota^dagger iota = 1`` and
      ``iota iota^dagger tau = tau`` are arithmetic in ``{0, 1}`` and hold
      exactly as binary64 data; the frame is tight;
    * (a), the FULL frame, otherwise: ``iota = 1_A``, for which both
      conditions of ``eq:iota`` hold exactly for any admissible ``tau``.

    Whether ``t_i != 0`` and whether ``tau`` is diagonal are bit-level
    comparisons of declared entries against zero, so NO RANK IS COMPUTED and
    no eigenvalue of ``tau`` is decided at a window: a tiny positive ``t_i``
    stays in the frame. The root is :func:`marginal_root`'s, with no relative
    cutoff, so ``W W^dagger = tau`` (``eq:WWtau``) up to the rounding of the
    root alone.

    Args:
        tau: the declared ``tau_A^{(t)}`` of one Alice sector.
        full: whether construction (a) is required, as it is in ensemble form
            (``lem:choi-factor`` (iv)).
    """
    matrix = np.asarray(tau, dtype=np.complex128)
    width = int(matrix.shape[0])
    root = marginal_root(matrix)
    if not full and _is_bit_diagonal(matrix):
        kept = [index for index in range(width) if matrix[index, index] != 0]
        iota = np.asarray(np.eye(width, dtype=np.complex128)[:, kept])
        frame = MarginalFrame(iota=iota, root=root, full=False)
    else:
        frame = MarginalFrame(
            iota=np.eye(width, dtype=np.complex128), root=root, full=True
        )
    _check_frame_identities(frame.iota, matrix)
    return frame


def _check_frame_identities(iota: Matrix, tau: Matrix) -> None:
    """Decide ``eq:iota`` on the constructed frame at exactly 0 (``choi_isometry``).

    ``iota^dagger iota = 1_{A_0}`` and ``iota iota^dagger tau = tau``, entry
    for entry as binary64 data, which both constructions meet by arithmetic
    on zero and one. A failure is ``choi_isometry_inexact``; it is
    unreachable by construction, and decided because the interface row says
    the identities are decided on the isometry this module constructed.
    """
    gram = iota.conj().T @ iota
    fixed = iota @ iota.conj().T @ tau
    if not (
        np.array_equal(gram, np.eye(gram.shape[0], dtype=np.complex128))
        and np.array_equal(fixed, tau)
    ):
        raise ChoiIsometryError(
            "lem:choi-marginal eq:iota and the `choi_isometry` threshold row: "
            "the constructed frame's identities iota^dagger iota = 1 and "
            "iota iota^dagger tau_A = tau_A do not hold EXACTLY as binary64 "
            "data"
        )


def _read_only[ArrayT: npt.NDArray[np.generic]](array: ArrayT) -> ArrayT:
    """Return ``array`` with in-place writes refused, for a cache's mapping.

    The joint caches (:attr:`JointMaps.statistics_map`,
    :meth:`JointMaps.branch_plan`) are built once from the arrays these
    read-only mappings hold, so an element written after first use would leave
    them stale. The mapping refuses a rebinding; this refuses the write.
    """
    array.setflags(write=False)
    return array


def joint_choi_parametrization(
    declaration: GeneralDeclaration,
) -> JointChoiParametrization:
    """Build the per-Alice-sector frames of ``thm:choi``, the general format.

    The frame is "a direct sum of one frame per Alice sector", and which
    construction is used per sector is decided by the DECLARED form and the
    DECLARED entries of ``tau_A`` and by nothing measured
    (:func:`marginal_frame`):

    * ensemble form -> the FULL frame, ``lem:choi-factor`` (iv). NO RANK IS
      COMPUTED: ``lem:choi-marginal``'s no-rank stance stands, and what is
      forgone is the ``W``-free row dividend, "which changes no value";
    * POVM form, trusted -> the diagonal frame (b) of ``lem:choi-marginal``
      where ``tau_A^{(t)}`` is diagonal bit for bit, tight by construction,
      and the full frame (a) otherwise. No rank is computed here either;
    * untrusted -> ``W_t = 1_{A_t}`` and the scalar coupling.
    """
    frames: dict[str, AliceFrame] = {}
    for alice_sector in declaration.alice_sectors:
        width = declaration.alice_dim_of(alice_sector)
        if not declaration.is_trusted_source:
            identity = _read_only(np.eye(width, dtype=np.complex128))
            frames[alice_sector] = AliceFrame(
                alice_sector=alice_sector,
                w=identity,
                iota=identity,
                input_dim=width,
                gram=identity,
                is_full_frame=True,
            )
            continue
        frame = marginal_frame(
            declaration.marginal_block(alice_sector),
            full=declaration.is_ensemble_form,
        )
        w = _read_only(np.asarray(frame.root @ frame.iota, dtype=np.complex128))
        frames[alice_sector] = AliceFrame(
            alice_sector=alice_sector,
            w=w,
            iota=_read_only(np.array(frame.iota, dtype=np.complex128)),
            input_dim=int(w.shape[1]),
            gram=_read_only(np.asarray(w.conj().T @ w, dtype=np.complex128)),
            is_full_frame=frame.full,
        )
    return JointChoiParametrization(
        declaration=declaration,
        # Read-only: JointMaps.statistics_map caches the block sizes it gives.
        frames=MappingProxyType(frames),
        coupling=(
            Coupling.INPUT_IDENTITY
            if declaration.is_trusted_source
            else Coupling.UNIT_TRACE
        ),
    )


# ---------------------------------------------------------------------------
#  The generated maps, per joint sector
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class JointClassBranch:
    """One transcript class' Kraus operator on one joint sector.

    ``eq:kraus`` read on the joint sector: the vertical stack of the row blocks
    ``sqrt(N^W_x) (x) sqrt(F_v^{(s)})`` over the outcome pairs of the class,
    each row remembering its raw-key value, which is all the key pinching
    needs. ``lem:choi-factor`` (iii) licenses the square root of ``N^W_x`` in
    the slot of ``sqrt(M_x)`` AT EVERY RANK -- by a polar decomposition and a
    partial isometry that commutes with the key pinching -- which is why an
    ensemble-form declaration needs neither ``M_x`` nor a rank here.
    """

    transcript: Transcript
    pairs: tuple[OutcomePair, ...]
    kraus: Matrix
    labels: npt.NDArray[np.int64]


@dataclass(frozen=True)
class JointBranchMap:
    """``G_{chat,(t,s)}`` of ``eq:joint-deficit``, held per transcript class."""

    chat: str
    pair: JointSector
    classes: tuple[JointClassBranch, ...]


@dataclass(frozen=True)
class JointMaps:
    """Everything the general-format objective derives from a declaration.

    A function of the declaration and the frames alone: nothing here depends on
    the point or on ``alpha``, so it is built once and shared across a run.
    """

    parametrization: JointChoiParametrization
    chat_key: tuple[str, ...]
    acceptance_support: tuple[str, ...]
    sifting: Mapping[Transcript, bool]
    #: ``Gamma^{(t,s)}_chat`` in CHOI coordinates: ``sum N^W_x (x) F_v^{(s)}``
    #: over the pairs of the acceptance value (``cor:drop-program`` (iii)).
    statistics_operator: Mapping[tuple[str, JointSector], Matrix]
    branches: Mapping[tuple[str, JointSector], JointBranchMap]
    #: ``def:joint-sectors``: which pairs ``(chat, (t, s))`` are key-inert,
    #: decided on DECLARED data -- ``M_x^{(t)}`` or, in ensemble form,
    #: ``N_x^{(t)}`` against zero, and ``F_v^{(s)}`` per factor.
    key_inert: Mapping[tuple[str, JointSector], bool]
    #: ``dim W_{chat,(t,s)}`` of ``eq:Wcs-joint``, one number per joint pair,
    #: computed from the declaration and the frame and never from an iterate
    #: (``frank-wolfe/interface.yaml``, ``general_format_readings``), read at
    #: ``sqrt(support_cutoff)`` on the stack's singular values
    #: (``frank-wolfe/rem:fo-one-ruler``).
    support_references: Mapping[tuple[str, JointSector], int]
    #: Per joint pair, the directions of the stack whose singular value lies in
    #: ``(support_cutoff, sqrt(support_cutoff)]`` relative to the largest,
    #: which that reading sets aside
    #: (:class:`~certiqs_key.meat_core.objective.support.BranchSupport`). A
    #: diagnostic for the run record; nothing reads it to decide anything.
    support_bands: Mapping[tuple[str, JointSector], int]

    @property
    def declaration(self) -> GeneralDeclaration:
        """Return the declaration these maps were generated from."""
        return self.parametrization.declaration

    @property
    def joint_sectors(self) -> tuple[JointSector, ...]:
        """Return the joint sectors in their declared order."""
        return self.parametrization.joint_sectors

    def key_active_pairs(self, chat: str) -> tuple[JointSector, ...]:
        """Return ``J_K(chat)`` of ``def:joint-sectors``."""
        return tuple(
            pair for pair in self.joint_sectors if not self.key_inert[(chat, pair)]
        )

    # -- precomputed evaluation structure ----------------------------------
    #
    # A cache below is a FUNCTION OF THE FIELDS ALONE, built lazily on first
    # use. The dataclass is frozen and nothing writes its mappings after
    # :func:`build_joint_maps` returns, so a cached value cannot go stale;
    # ``dataclasses.replace`` gives a new instance whose caches start empty.
    # A cache changes how a number is computed and never which number.

    @cached_property
    def statistics_map(self) -> JointStatisticsMap:
        """Return ``Phi`` of ``eq:K-joint`` as ONE precomputed linear map."""
        return _build_statistics_map(self)

    @cached_property
    def _branch_plans(
        self,
    ) -> dict[tuple[str, frozenset[tuple[str, JointSector]], bool], JointBranchPlan]:
        return {}

    def branch_plan(
        self,
        chat: str,
        dropped: frozenset[tuple[str, JointSector]],
        skip_key_inert: bool,
    ) -> JointBranchPlan:
        """Return which joint sectors :func:`evaluate_joint_branch` visits.

        The classification the per-sector loop made, in the declared
        joint-sector order: dropped (``def:dropped``, only at a key-live
        value), key-inert and skipped (``lem:joint-sectors`` (iii), only when
        ``skip_key_inert``), or evaluated. Memoised per
        ``(chat, dropped, skip_key_inert)``, on which alone (with the fields)
        it depends.
        """
        key = (chat, dropped, skip_key_inert)
        plan = self._branch_plans.get(key)
        if plan is None:
            evaluated: list[JointSector] = []
            dropped_pairs: list[JointSector] = []
            skipped: list[JointSector] = []
            live = chat in self.chat_key
            for pair in self.joint_sectors:
                if live and (chat, pair) in dropped:
                    dropped_pairs.append(pair)
                elif skip_key_inert and self.key_inert[(chat, pair)]:
                    skipped.append(pair)
                else:
                    evaluated.append(pair)
            plan = JointBranchPlan(
                evaluated=tuple(evaluated),
                dropped_pairs=tuple(dropped_pairs),
                skipped_key_inert=tuple(skipped),
            )
            self._branch_plans[key] = plan
        return plan

    def deficit_pairs(
        self,
        dropped: frozenset[tuple[str, JointSector]],
        skip_key_inert: bool,
    ) -> tuple[JointSector, ...]:
        """Return every joint sector whose Choi block some deficit reads.

        The union over the declared acceptance values of
        :meth:`branch_plan`'s evaluated sectors, in the declared order: the
        blocks :func:`joint_objective_value_at_statistics` needs, and no
        others.
        """
        needed = {
            pair
            for chat in self.declaration.acceptance_values
            for pair in self.branch_plan(chat, dropped, skip_key_inert).evaluated
        }
        return tuple(pair for pair in self.joint_sectors if pair in needed)


@dataclass(frozen=True)
class JointBranchPlan:
    """Which joint sectors one acceptance value's branch sum visits, and why not."""

    evaluated: tuple[JointSector, ...]
    dropped_pairs: tuple[JointSector, ...]
    skipped_key_inert: tuple[JointSector, ...]


@dataclass(frozen=True)
class JointStatisticsMap:
    """``Phi`` of ``eq:K-joint`` as a dense complex matrix over stacked blocks.

    Row ``chat``, in the declared acceptance order, holds
    ``(Gamma^{(t,s)}_chat)^T`` flattened row-major for every joint sector in
    the declared order, so that
    ``Re(matrix @ concat_p vec(J_p)) = sum_p Re tr[Gamma_p J_p]`` for ANY square
    blocks of the declared sizes -- Hermitian or not, since
    ``tr[G J] = sum_ij G_ij J_ji``. The array is read-only.
    """

    acceptance_values: tuple[str, ...]
    pairs: tuple[JointSector, ...]
    dims: tuple[int, ...]
    matrix: npt.NDArray[np.complex128]


def _build_statistics_map(maps: JointMaps) -> JointStatisticsMap:
    """Stack the statistics operators of ``maps`` into one read-only matrix."""
    pairs = tuple(maps.joint_sectors)
    values = tuple(maps.declaration.acceptance_values)
    dims = tuple(maps.parametrization.block_dim(pair) for pair in pairs)
    width = sum(dim * dim for dim in dims)
    matrix = np.zeros((len(values), width), dtype=np.complex128)
    for row, chat in enumerate(values):
        offset = 0
        for pair, dim in zip(pairs, dims, strict=True):
            operator = as_matrix(maps.statistics_operator[(chat, pair)])
            matrix[row, offset : offset + dim * dim] = operator.T.ravel()
            offset += dim * dim
    matrix.setflags(write=False)
    return JointStatisticsMap(
        acceptance_values=values, pairs=pairs, dims=dims, matrix=matrix
    )


def effective_outcomes(
    declaration: GeneralDeclaration, kappa: Transcript, pair: JointSector
) -> tuple[OutcomePair, ...]:
    """Return ``E^{(t,s)}_kappa`` of ``eq:joint-effective``.

    The pairs of the class whose operators do not vanish on the JOINT sector:
    Alice's declared block non-zero on ``A_t`` -- ``M_x^{(t)} != 0``, or
    ``N_x^{(t)} != 0`` in ensemble form, which decide the same thing by
    ``lem:ensemble-form`` (iii) -- and ``F_v^{(s)} != 0``, decided PER FACTOR
    so that no product is formed. As on the accepted path, dust counts as
    non-zero, which can only ENLARGE ``E`` and therefore only classify a pair
    as key-active: the conservative direction.
    """
    alice_sector, sector = pair
    pairs: list[OutcomePair] = []
    for x in declaration.alice_alphabet:
        if declaration.alice_block_is_zero(x, alice_sector):
            continue
        for v in declaration.bob_outcomes:
            if declaration.announcement(x, v) != kappa:
                continue
            if declaration.bob_block_is_zero(v, sector):
                continue
            pairs.append((x, v))
    return tuple(pairs)


def is_key_inert(
    declaration: GeneralDeclaration,
    sifting: Mapping[Transcript, bool],
    chat: str,
    pair: JointSector,
) -> bool:
    """Return whether ``(chat, (t, s))`` is key-inert (``def:joint-sectors``).

    ``r`` is constant on ``E^{(t,s)}_kappa`` for every pass class of ``chat``:
    a finite combinatorial predicate on declared data.
    """
    for kappa, passes in sifting.items():
        if not passes or declaration.accept_statistic[kappa] != chat:
            continue
        values = {
            declaration.raw_key(x, v)
            for x, v in effective_outcomes(declaration, kappa, pair)
        }
        if len(values) > 1:
            return False
    return True


def build_joint_maps(
    parametrization: JointChoiParametrization,
    *,
    acceptance_support: Sequence[str] | None = None,
) -> JointMaps:
    """Build the joint-sector maps of a validated general declaration.

    ``acceptance_support`` is ``Chat_acc`` of ``eq:chacc-def``; absent, every
    declared acceptance value is taken to be in it, which is the conservative
    reading (a larger index set asks the positivity hypothesis of more
    coordinates, never of fewer).
    """
    declaration = parametrization.declaration
    by_class: dict[Transcript, list[OutcomePair]] = {}
    sifting: dict[Transcript, bool] = {}
    for x in declaration.alice_alphabet:
        for v in declaration.bob_outcomes:
            kappa = declaration.announcement(x, v)
            by_class.setdefault(kappa, []).append((x, v))
            passes = declaration.raw_key(x, v) is not None
            if kappa in sifting and sifting[kappa] != passes:
                raise DeclarationError(
                    "def:admissible-declaration (v): sifting is not "
                    "announcement-determined at "
                    f"the transcript {kappa}"
                )
            sifting[kappa] = passes
    live = {
        declaration.accept_statistic[kappa]
        for kappa, passes in sifting.items()
        if passes
    }
    chat_key = tuple(c for c in declaration.acceptance_values if c in live)

    statistics: dict[tuple[str, JointSector], Matrix] = {}
    branches: dict[tuple[str, JointSector], JointBranchMap] = {}
    for chat in declaration.acceptance_values:
        for pair in parametrization.joint_sectors:
            alice_sector, sector = pair
            dim = parametrization.block_dim(pair)
            total = np.zeros((dim, dim), dtype=np.complex128)
            classes: list[JointClassBranch] = []
            for kappa, pairs in by_class.items():
                if declaration.accept_statistic[kappa] != chat:
                    continue
                for x, v in pairs:
                    total = total + np.kron(
                        parametrization.alice_choi_operator(x, alice_sector),
                        declaration.bob_block(v, sector),
                    )
                if sifting[kappa]:
                    classes.append(_class_branch(parametrization, kappa, pair, pairs))
            statistics[(chat, pair)] = _read_only(total)
            branches[(chat, pair)] = JointBranchMap(
                chat=chat, pair=pair, classes=tuple(classes)
            )

    key_inert = {
        (chat, pair): is_key_inert(declaration, sifting, chat, pair)
        for chat in declaration.acceptance_values
        for pair in parametrization.joint_sectors
    }
    supports = {
        (chat, pair): _joint_support(branches[(chat, pair)].classes)
        for chat in declaration.acceptance_values
        for pair in parametrization.joint_sectors
    }
    return JointMaps(
        parametrization=parametrization,
        chat_key=chat_key,
        acceptance_support=(
            tuple(declaration.acceptance_values)
            if acceptance_support is None
            else tuple(acceptance_support)
        ),
        # The mappings are READ-ONLY, and so is every array in them
        # (_read_only): statistics_map and branch_plan cache values derived
        # from statistics_operator and key_inert, so an in-place write after
        # first use would leave them stale.
        sifting=MappingProxyType(sifting),
        statistics_operator=MappingProxyType(statistics),
        branches=MappingProxyType(branches),
        key_inert=MappingProxyType(key_inert),
        support_references=MappingProxyType(
            {key: support.dimension for key, support in supports.items()}
        ),
        support_bands=MappingProxyType(
            {key: support.band for key, support in supports.items()}
        ),
    )


def _joint_support_reference(classes: Sequence[JointClassBranch]) -> int:
    """Return ``dim W_{chat,(t,s)}`` of one joint pair; see :func:`_joint_support`."""
    return _joint_support(classes).dimension


def _joint_support(classes: Sequence[JointClassBranch]) -> BranchSupport:
    """Embed compact classes in their disjoint transcript output spaces.

    The shared helper horizontally stacks operators into a common ambient
    output. Here each class stores only its own transcript block, so padding
    those ranges into the direct sum is essential. One global SVD then reads
    the stack at ``sqrt(support_cutoff)`` relative to its largest singular
    value, the ruler ``frank-wolfe/rem:fo-one-ruler`` fixes; ranks are
    never added from independently thresholded classes.
    """
    height = sum(klass.kraus.shape[0] for klass in classes)
    embedded = []
    offset = 0
    for klass in classes:
        rows, columns = klass.kraus.shape
        operator = np.zeros((height, columns), dtype=np.complex128)
        operator[offset : offset + rows] = klass.kraus
        embedded.append(operator)
        offset += rows
    return branch_support(embedded)


def _class_branch(
    parametrization: JointChoiParametrization,
    kappa: Transcript,
    pair: JointSector,
    pairs: Sequence[OutcomePair],
) -> JointClassBranch:
    """Assemble one class' Kraus operator on one joint sector."""
    declaration = parametrization.declaration
    alice_sector, sector = pair
    dim = parametrization.block_dim(pair)
    # Only exact declared zeros are omitted. Their Kraus rows vanish for every
    # state, so their trace-power term is the constant zero function. Keeping
    # positive-size zero rows would incorrectly ask the gradient helper to
    # differentiate a nonconstant branch at a zero iterate. No formed product,
    # norm, eigentolerance, or iterate value decides this filtering.
    pairs = tuple(
        (x, v)
        for x, v in pairs
        if not declaration.alice_block_is_zero(x, alice_sector)
        and not declaration.bob_block_is_zero(v, sector)
    )
    blocks: list[Matrix] = []
    labels: list[int] = []
    for x, v in pairs:
        root_alice = psd_power(
            parametrization.alice_choi_operator(x, alice_sector), 0.5
        )
        root_bob = psd_power(declaration.bob_block(v, sector), 0.5)
        blocks.append(np.asarray(np.kron(root_alice, root_bob), dtype=np.complex128))
        value = declaration.raw_key(x, v)
        if value is None:
            raise DeclarationError(
                "def:admissible-declaration (v): a pass class must not contain an "
                "unsifted "
                f"outcome pair, but {(x, v)} in the class {kappa} is perp"
            )
        labels.extend([value] * dim)
    kraus = np.vstack(blocks) if blocks else np.zeros((0, dim), dtype=np.complex128)
    return JointClassBranch(
        transcript=kappa,
        pairs=tuple(pairs),
        kraus=_read_only(np.asarray(kraus, dtype=np.complex128)),
        labels=_read_only(np.asarray(labels, dtype=np.int64)),
    )


# ---------------------------------------------------------------------------
#  The dropped set and the values
# ---------------------------------------------------------------------------

#: A dropped set ``D`` of ``def:dropped``: pairs of a key-live acceptance value
#: and a joint sector. A RUN'S FORMULATION CHOICE AND NOT A DECLARED DATUM.
DroppedSet = frozenset[tuple[str, JointSector]]

#: ``D = empty``, which is today's run and gives ``K_chat``, ``O_alpha`` and
#: ``h_low`` (``def:dropped``, the closing sentence).
NOTHING_DROPPED: DroppedSet = frozenset()


def normalise_dropped_set(
    maps: JointMaps, dropped: Iterable[tuple[str, JointSector]] | None
) -> DroppedSet:
    """Return the dropped set, refusing a pair no declaration names.

    ``def:dropped``: ``D`` is a subset of ``Chat_key x (T x S)``. A pair naming
    an acceptance value that is not key-live, or a joint sector that is not
    declared, is REFUSED rather than ignored: a run that believes it dropped
    something it did not would report ``h_low^D`` for a ``D`` that is not the
    one it recorded.
    """
    if dropped is None:
        return NOTHING_DROPPED
    chosen = frozenset(dropped)
    live = set(maps.chat_key)
    declared = set(maps.joint_sectors)
    for chat, pair in chosen:
        if chat not in live:
            raise DeclarationError(
                f"def:dropped: {chat!r} is not a key-live acceptance value, so "
                f"the pair ({chat!r}, {pair}) is not a member of "
                "Chat_key x (T x S) and cannot be dropped. Only a key-live "
                "value carries a deficit to give up"
            )
        if pair not in declared:
            raise DeclarationError(
                f"def:dropped: {pair} is not a declared joint sector {sorted(declared)}"
            )
    return chosen


@dataclass(frozen=True)
class JointBranchValues:
    """``P``, ``T``, ``tr G``, ``K`` and the per-joint-pair deficits.

    :attr:`k` is ``K^D_chat`` of ``eq:KD`` -- which is ``K_chat`` of
    ``eq:K-joint`` at ``D = empty`` -- and :attr:`dropped_pairs` records which
    deficits were replaced by zero, so that a caller can report ``D`` beside
    the number as ``def:dropped`` requires.
    """

    p: float
    k: float
    deficits: Mapping[JointSector, float]
    dropped_pairs: tuple[JointSector, ...]
    skipped_key_inert: tuple[JointSector, ...]

    @property
    def k_from_pairs(self) -> float:
        """Return ``P + sum f`` over the pairs whose deficit was formed."""
        return self.p + sum(self.deficits.values())


def joint_statistics(
    maps: JointMaps, choi: Mapping[JointSector, Matrix]
) -> dict[str, float]:
    """Return ``Phi[chi(J)]`` per acceptance value, ``eq:K-joint``.

    A sum over the joint sectors of ``tr[Gamma^{(t,s)}_chat J_{t,s}]``, which
    is ``tr[(M_x (x) F_v) omega]`` by ``lem:choi-factor`` (iii). EVERY JOINT
    SECTOR ENTERS WITH ITS FULL WEIGHT, a dropped one included
    (``def:dropped``, "What is not changed").

    Evaluated as ONE matrix-vector product with the precomputed
    :attr:`JointMaps.statistics_map`: the same real-linear function as the
    per-term loop :func:`_joint_statistics_reference`, summed in a different
    order, so the two agree to rounding (a property test compares them).
    """
    layout = maps.statistics_map
    blocks = [as_matrix(choi[pair]) for pair in layout.pairs]
    for pair, dim, block in zip(layout.pairs, layout.dims, blocks, strict=True):
        if block.shape[0] != dim:
            raise ValueError(
                f"the Choi block on {pair} has shape {block.shape}, expected "
                f"({dim}, {dim})"
            )
    vector = np.concatenate([block.ravel() for block in blocks])
    values = np.real(layout.matrix @ vector)
    return dict(zip(layout.acceptance_values, values.tolist(), strict=True))


def _joint_statistics_reference(
    maps: JointMaps, choi: Mapping[JointSector, Matrix]
) -> dict[str, float]:
    """Return :func:`joint_statistics` by the per-term loop it replaced.

    Kept as the reference the vectorised path is tested against: one
    ``Re tr[Gamma J]`` per (acceptance value, joint sector), summed in the
    declared order.
    """
    out: dict[str, float] = {}
    for chat in maps.declaration.acceptance_values:
        total = 0.0
        for pair in maps.joint_sectors:
            operator = maps.statistics_operator[(chat, pair)]
            total += float(np.real(np.trace(operator @ as_matrix(choi[pair]))))
        out[chat] = total
    return out


def joint_deficit(
    maps: JointMaps, chat: str, pair: JointSector, choi_block: Matrix, alpha: float
) -> float:
    """Return ``f_{chat,(t,s)}`` at one joint sector, ``eq:joint-deficit``.

    ``T(G) - tr G`` over the pass classes of the value, each class occupying
    its own orthogonal output block, so both quantities add over classes
    (``lem:joint-sectors`` (ii)).
    """
    branch = maps.branches[(chat, pair)]
    block = as_matrix(choi_block)
    t_total = 0.0
    trace_total = 0.0
    for klass in branch.classes:
        operator = np.asarray(
            klass.kraus @ block @ klass.kraus.conj().T, dtype=np.complex128
        )
        t_total += trace_power_pinched(operator, alpha, klass.labels)
        trace_total += float(np.real(np.trace(operator)))
    return t_total - trace_total


def evaluate_joint_branch(
    maps: JointMaps,
    chat: str,
    choi: Mapping[JointSector, Matrix],
    alpha: float,
    p_chat: float,
    *,
    dropped: DroppedSet = NOTHING_DROPPED,
    skip_key_inert: bool = True,
) -> JointBranchValues:
    """Return ``P`` and ``K^D_chat`` at one acceptance value.

    ``eq:KD`` with ``eq:K-joint``: ``P_chat`` plus the deficits of the joint
    sectors whose pair is not in ``D``. Two restrictions of that sum, and they
    are different in kind:

    * ``skip_key_inert`` takes the IDENTITY of ``lem:joint-sectors`` (iii) --
      the deficit of a key-inert pair vanishes for every input.
      ``False`` computes the identity instead, and
      :func:`evaluate_joint_branches` is tested both ways.
    * ``dropped`` gives up the deficits of the chosen pairs, which is
      ``def:dropped`` and a rate loss in the safe direction.

    Which sectors fall under which is decided once per
    ``(chat, dropped, skip_key_inert)`` by :meth:`JointMaps.branch_plan`, in
    the declared order, so only the evaluated sectors are visited here and
    the deficits are summed in the order they always were.
    """
    plan = maps.branch_plan(chat, frozenset(dropped), skip_key_inert)
    deficits: dict[JointSector, float] = {
        pair: joint_deficit(maps, chat, pair, choi[pair], alpha)
        for pair in plan.evaluated
    }
    return JointBranchValues(
        p=p_chat,
        k=p_chat + sum(deficits.values()),
        deficits=deficits,
        dropped_pairs=plan.dropped_pairs,
        skipped_key_inert=plan.skipped_key_inert,
    )


def evaluate_joint_branches(
    maps: JointMaps,
    choi: Mapping[JointSector, Matrix],
    alpha: float,
    *,
    dropped: DroppedSet = NOTHING_DROPPED,
    skip_key_inert: bool = True,
    statistics: Mapping[str, float] | None = None,
) -> dict[str, JointBranchValues]:
    """Return :func:`evaluate_joint_branch` at every declared acceptance value.

    ``statistics``, when given, is used as ``Phi[chi(J)]`` in place of
    :func:`joint_statistics` of ``choi``; the caller answers for it being
    that value (see :func:`joint_objective_value_at_statistics`).
    """
    phi = joint_statistics(maps, choi) if statistics is None else statistics
    return {
        chat: evaluate_joint_branch(
            maps,
            chat,
            choi,
            alpha,
            phi[chat],
            dropped=dropped,
            skip_key_inert=skip_key_inert,
        )
        for chat in maps.declaration.acceptance_values
    }


def joint_objective_value(
    maps: JointMaps,
    q: Mapping[str, float],
    choi: Mapping[JointSector, Matrix],
    alpha: float,
    *,
    dropped: DroppedSet = NOTHING_DROPPED,
    skip_key_inert: bool = True,
) -> float:
    """Return ``O^D_alpha(q, chi(J))`` of ``def:dropped``, ``eq:objective``.

    At ``D = empty`` this is ``O_alpha`` of ``eq:objective`` in the Choi
    coordinates of ``thm:choi``'s general format. The value is an
    EXTENDED REAL: ``+inf`` is a legitimate return and is never clamped
    (``rem:hlow-range``).
    """
    check_alpha_structural(alpha)
    values = evaluate_joint_branches(
        maps, choi, alpha, dropped=dropped, skip_key_inert=skip_key_inert
    )
    return _objective_from_values(maps, q, values, alpha)


def joint_objective_value_at_statistics(
    maps: JointMaps,
    q: Mapping[str, float],
    choi: Mapping[JointSector, Matrix],
    alpha: float,
    statistics: Mapping[str, float],
    *,
    dropped: DroppedSet = NOTHING_DROPPED,
    skip_key_inert: bool = True,
) -> float:
    """Return :func:`joint_objective_value` with ``Phi[chi(J)]`` SUPPLIED.

    The same expression, ``eq:objective`` read through ``def:dropped``, with
    ``statistics`` standing for ``Phi[chi(J)]``. It exists because ``Phi`` is
    linear (``eq:K-joint``): along a Frank-Wolfe segment
    ``Phi(J + t (S - J)) = (1 - t) Phi(J) + t Phi(S)``, so a line search can
    interpolate two endpoint evaluations instead of re-forming ``Phi`` at
    every trial point, while the deficits -- which are not linear -- are
    still formed at the trial point itself.

    THE CALLER ANSWERS FOR ``statistics`` BEING ``Phi`` OF ``choi`` (to
    rounding), and ``choi`` need carry only the blocks of
    ``maps.deficit_pairs(dropped, skip_key_inert)``. Numbers a run REPORTS
    come from :func:`joint_objective_value`, which forms ``Phi`` itself.
    """
    check_alpha_structural(alpha)
    values = evaluate_joint_branches(
        maps,
        choi,
        alpha,
        dropped=dropped,
        skip_key_inert=skip_key_inert,
        statistics=statistics,
    )
    return _objective_from_values(maps, q, values, alpha)


def joint_objective_value_from_branches(
    maps: JointMaps,
    q: Mapping[str, float],
    values: Mapping[str, JointBranchValues],
    alpha: float,
) -> float:
    """Return :func:`joint_objective_value` from branch values ALREADY FORMED.

    The same sum, ``eq:objective`` read through ``def:dropped``, at ``q`` and
    at the ``P`` and ``K^D`` of ``values``. It exists for a caller that needs
    the branch values themselves before it chooses ``q`` -- the driver's exact
    partial minimisation in ``q`` reads ``P`` and ``K^D`` to form
    ``argmin_q`` and then evaluates at it -- so the deficits, the expensive
    part, are formed once. THE CALLER ANSWERS FOR ``values`` being those of
    the point it reports: :func:`evaluate_joint_branches` without
    ``statistics`` is the direct path.
    """
    check_alpha_structural(alpha)
    return _objective_from_values(maps, q, values, alpha)


def _objective_from_values(
    maps: JointMaps,
    q: Mapping[str, float],
    values: Mapping[str, JointBranchValues],
    alpha: float,
) -> float:
    """Sum the divergence terms of ``eq:objective`` from ``P`` and ``K^D``."""
    live = set(maps.chat_key)
    total = 0.0
    for chat, weight in q.items():
        value = values[chat]
        if chat in live:
            total += divergence_kernel(weight, value.p)
            total += divergence_kernel(weight, value.k) / (alpha - 1.0)
        else:
            total += (alpha / (alpha - 1.0)) * divergence_kernel(weight, value.p)
        if math.isinf(total):
            return math.inf
    return total


# ---------------------------------------------------------------------------
#  lem:rank-one-sector: the closed constants
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RankOneSector:
    """A rank-one Alice sector, ``lem:rank-one-sector``.

    ``tau_A^{(t)} = p_t |v><v|`` with ``p_t > 0``. The vector and the weight
    are read off the DECLARED block; in ensemble form the weights ``mu_x`` are
    ``tr N_x^{(t)} / p_t``, "declared numbers" (part (iii)).
    """

    alice_sector: str
    weight: float
    vector: npt.NDArray[np.complex128]
    mu: Mapping[str, float]


def rank_one_sector(maps: JointMaps, alice_sector: str) -> RankOneSector | None:
    """Return the rank-one data of an Alice sector, or ``None``.

    On exact Gaussian rationals representing the declared binary64 entries,
    require Hermiticity, a positive diagonal pivot p, and
    ``tau[i,j] * tau[p,p] == tau[i,p] * tau[p,j]`` at every entry. This
    identity is equivalent to ``tau = column_p column_p^dagger / tau[p,p]``:
    it proves positivity and rank one without eigenvalues or a tolerance.
    Only after that decision do we numerically normalize the pivot column.
    Near-rank-one blocks use the general matrix route.
    """
    declaration = maps.declaration
    if not declaration.is_trusted_source:
        return None
    tau = declaration.marginal_block(alice_sector)
    if not is_hermitian_exact(tau):
        return None
    exact = to_exact(tau)
    positive = [i for i in range(len(exact)) if exact[i][i].re > 0]
    if not positive:
        return None
    pivot = max(positive, key=lambda i: exact[i][i].re)
    if any(
        exact[i][j] * exact[pivot][pivot] != exact[i][pivot] * exact[pivot][j]
        for i in range(len(exact))
        for j in range(len(exact))
    ):
        return None
    largest = float(sum(exact[i][i].re for i in range(len(exact))))
    # Divide first to avoid underflow in the product of small diagonal values.
    column = np.asarray(tau[:, pivot] / tau[pivot, pivot].real, np.complex128)
    vector = np.asarray(column / np.linalg.norm(column), np.complex128)
    mu: dict[str, float] = {}
    for x in declaration.alice_alphabet:
        block = declaration.alice_block(x, alice_sector)
        if declaration.is_ensemble_form:
            mu[x] = float(np.real(np.trace(block))) / largest
        else:
            mu[x] = float(np.real(vector.conj() @ block @ vector))
    return RankOneSector(
        alice_sector=alice_sector, weight=largest, vector=vector, mu=mu
    )


def rank_one_deficit(
    maps: JointMaps,
    chat: str,
    pair: JointSector,
    choi_block: Matrix,
    alpha: float,
    sector_data: RankOneSector,
) -> float:
    """Return ``f_{chat,(t,s)}`` by the closed form of ``eq:rank-one-deficit``.

    ``lem:rank-one-sector`` (iii): a LINEAR function of the measured block,
    with the constants ``eta_kappa`` and ``m_kappa`` of
    ``eq:rank-one-weights`` computed from declared numbers. No matrix power, no
    eigendecomposition and no support condition is taken -- which is the reason
    33 of 34 Alice sectors of the decoy declaration cost nothing.

    Its hypotheses, which the caller must have: the default readouts, the key
    holder ``A`` (part (ii) proves the pass classes are product sets for EVERY
    transcript protocol under those), and a rank-one ``tau_A^{(t)}``. Part (iv)
    gives the two constants an instance reads: a uniform key bit
    over ``d`` values has ``eta = 1 - d^{1-alpha}``, so the vacuum sector
    contributes as if the conditional entropy were ``log_2 d`` ON THE PASS
    WEIGHT, and a key constant where ``mu_x > 0`` has ``eta = 0``, so a flag
    sector's deficit is identically zero.
    """
    declaration = maps.declaration
    _, sector = pair
    if declaration.key_holder is not KeyHolder.ALICE:
        raise DeclarationError(
            "lem:rank-one-sector (iii) is stated under the hypotheses of (ii), "
            "which include holder = A; this declaration's holder is "
            f"{declaration.key_holder.value}. The general matrix route applies "
            "there and this closed form does not"
        )
    sigma = _measured_block(maps, pair, choi_block, sector_data)
    total = 0.0
    for kappa, passes in maps.sifting.items():
        if not passes or declaration.accept_statistic[kappa] != chat:
            continue
        alice_letters = {
            x
            for x in declaration.alice_alphabet
            if any(
                declaration.announcement(x, v) == kappa
                for v in declaration.bob_outcomes
            )
        }
        bob_letters = {
            v
            for v in declaration.bob_outcomes
            if any(
                declaration.announcement(x, v) == kappa
                for x in declaration.alice_alphabet
            )
        }
        if {(x, v) for x in alice_letters for v in bob_letters} != {
            (x, v)
            for x in declaration.alice_alphabet
            for v in declaration.bob_outcomes
            if declaration.announcement(x, v) == kappa
        }:
            raise DeclarationError(
                "lem:rank-one-sector (ii): the pass class "
                f"{kappa} is not the product set X_kappa x V_kappa its proof "
                "derives from the default readouts, so the closed form of (iii) "
                "is not available at this class. The general matrix route is"
            )
        m_kappa = sum(sector_data.mu[x] for x in alice_letters)
        if m_kappa <= 0.0:
            continue
        by_value: dict[int | None, float] = {}
        for x in alice_letters:
            value = next(
                declaration.raw_key(x, v)
                for v in bob_letters
                if declaration.announcement(x, v) == kappa
            )
            by_value[value] = by_value.get(value, 0.0) + sector_data.mu[x]
        eta = 1.0 - sum((weight / m_kappa) ** alpha for weight in by_value.values())
        mass = sum(
            float(np.real(np.trace(declaration.bob_block(v, sector) @ sigma)))
            for v in bob_letters
        )
        total += eta * m_kappa * mass
    return -total


def _measured_block(
    maps: JointMaps,
    pair: JointSector,
    choi_block: Matrix,
    sector_data: RankOneSector,
) -> Matrix:
    """Return ``sigma_s`` of ``lem:rank-one-sector`` (i) from a Choi block.

    Part (i): every feasible block of a rank-one Alice sector has the form
    ``|v><v| (x) sigma_s``, and ``sigma_s`` is the compression of the STATE
    block by that unit vector. Formed from the Choi block through ``chi``, so
    that the same expression serves both frames.
    """
    _, sector = pair
    width = maps.declaration.sector_dim(sector)
    state = maps.parametrization.chi(pair, choi_block)
    lift = np.kron(
        sector_data.vector.conj().reshape(1, -1), np.eye(width, dtype=np.complex128)
    )
    return np.asarray(lift @ state @ lift.conj().T, dtype=np.complex128)
