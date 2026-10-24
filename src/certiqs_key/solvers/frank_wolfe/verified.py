"""The verified feasible side of a bracket: Lemma D in exact dyadic arithmetic.

``meat-core/frank-wolfe/req:verified-feasible-side``, by
``meat-core/frank-wolfe/lem:feasible-side-dual``. ``thm:firstorder`` (iv) lets
any real ``b^F_t`` at most the minimum of ``<G_t, J'>`` over the EXACT
``Feas^J`` stand in for the pairing with the oracle's return; Lemma D gives one
from any multipliers, and this module forms it:

* per group (one per Alice sector in trusted-source mode, one in
  untrusted-source mode), ``R_p = herm(G_p) - Y (x) 1 - sum_r sigma_r
  L*_r(Lambda_r)`` and ``b = d_in lambda + tr Y + sum_r sigma_r tr[Lambda_r
  Theta_r]``, with ``lambda`` from ``foundations/lem:least-eigenvalue-bound``;
* the rows' data (``Theta``, the lifted operators, ``D = O - c 1``) TAKEN
  EXACTLY from the declaration and never from the binary64 arrays the oracle
  was handed, which form ``c tau`` and ``O - c 1`` with rounding (item (i));
* the frame ``W_t`` the engine's binary64 ``W~_t``, its error charged by
  Lemma D (iv): ``kappa_r = d_in eps (2 ||W~|| + eps) ||Lambda_r|| max_s
  ||O_{r,s}||`` where a dyadic ``eps >= ||W~ - W||`` is formed (item (iv)),
  and every row multiplier of the sector set to zero where it is not;
* the multipliers read off the backend's :class:`OracleDual` (item (ii)), each
  replaced by its exact Hermitian part, an inequality row's shifted exactly
  into the cone, and zero where the backend gave none, on a one-dimensional
  coupling without rows, or for the rows of a sector with no ``eps``.

Everything from the binary64 data on is exact (item (v)); the bound enters the
binary64 bracket rounded toward ``-inf`` (:func:`~certiqs_key.foundations.
dyadic.float_down`). Nothing here reads the oracle's returned point, its status
or its objective.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from fractions import Fraction
from typing import Any

import numpy as np

from certiqs_key.domain.manifest import ConstraintRelation
from certiqs_key.foundations.dyadic import (
    DyadicMatrix,
    dyadic_upper,
    largest_eigenvalue_bound,
    least_eigenvalue_bound,
)
from certiqs_key.meat_core.declaration.general import GeneralDeclaration, GeneralRhsTag
from certiqs_key.meat_core.objective.joint import (
    AliceFrame,
    JointChoiParametrization,
    JointSector,
)
from certiqs_key.meat_core.objective.joint_rows import (
    factor_position,
    other_factor_label,
    split_dims,
)
from certiqs_key.meat_core.objective.linalg import Matrix
from certiqs_key.solvers.oracles.joint_rows import joint_label
from certiqs_key.solvers.oracles.protocol import (
    OracleDual,
    SectorChoiProblem,
    hermitian_basis,
)

__all__ = [
    "MULTIPLIERS_BACKEND",
    "MULTIPLIERS_ROWS_ZEROED",
    "MULTIPLIERS_ZERO",
    "FeasibleSideBound",
    "GroupSolve",
    "feasible_side_over_enclosure",
    "verified_feasible_side",
]

#: The values of ``feasible_side_multipliers`` per group (the frank-wolfe
#: interface's ``feasible_side_bound.record``): the backend's multipliers, zero
#: multipliers, or the backend's with the row multipliers set to zero.
MULTIPLIERS_BACKEND = "backend"
MULTIPLIERS_ZERO = "zero"
MULTIPLIERS_ROWS_ZEROED = "rows_zeroed"


@dataclass(frozen=True)
class GroupSolve:
    """One group's subproblem and the dual its backend returned (``None``: none)."""

    problem: SectorChoiProblem | None
    dual: OracleDual | None


@dataclass(frozen=True)
class FeasibleSideBound:
    """``b^F_t`` and the record of ``req:verified-feasible-side`` (vi)."""

    #: ``b^F_t``, exact: at most the minimum over the exact ``Feas^J``.
    bound: Fraction
    #: The sum of the frame deductions ``kappa_r`` it contains.
    frame_deduction: Fraction
    #: The sum of the dyadic bounds on ``||Lambda_r||`` it used.
    row_multiplier_norm: Fraction
    #: Per group, ``backend``, ``zero`` or ``rows_zeroed``.
    multipliers: Mapping[str, str]


@dataclass(frozen=True)
class _LiftedRow:
    """A row read through its lifted operator, or a scalar row (untrusted)."""

    relation: ConstraintRelation
    #: ``Theta_k^{(t)}`` exactly, or ``c_k`` for a scalar row.
    theta: DyadicMatrix | Fraction
    #: Per block, ``O^{up(s)}`` (trusted) or ``1_{A_t} (x) O^{up(s)}`` (scalar).
    operators: Mapping[str, DyadicMatrix]
    #: A dyadic bound on ``max_s ||O_{r,s}||`` (the scoped blocks' Frobenius).
    norm: Fraction


@dataclass(frozen=True)
class _PartyLocalRow:
    """One party-local row at one ``s_{f^c}``; ``W`` is the group's frame."""

    relation: ConstraintRelation
    label: str
    comparison: int
    #: Per block: ``D = O^{(s_f)} - c_k 1`` exactly, and ``(left, scoped, right)``.
    blocks: Mapping[str, tuple[DyadicMatrix, tuple[int, int, int]]]
    norm: Fraction


@dataclass(frozen=True)
class _Group:
    """The exact data of one group, built once per parametrization."""

    unit: bool
    input_dim: int
    #: Block label -> joint sector, and the dimension ``Y (x) 1`` pads with.
    pairs: Mapping[str, JointSector]
    pad: Mapping[str, int]
    lifted: tuple[_LiftedRow, ...]
    party_local: tuple[_PartyLocalRow, ...]
    #: The frame ``W~`` (``None`` untrusted), the dyadic ``eps`` where it is
    #: formed, and a dyadic bound on ``||W~||``.
    frame: DyadicMatrix | None
    frame_error: Fraction | None
    frame_norm: Fraction


def _exact(values: Matrix) -> DyadicMatrix:
    return DyadicMatrix.from_array(np.asarray(values, dtype=np.complex128))


def _lifted(declaration: GeneralDeclaration, index: int, sector: str) -> DyadicMatrix:
    entry = declaration.constraint_list[index]
    left, _, right = split_dims(declaration, entry.scope, sector)
    scoped = declaration.split_sector(sector)[factor_position(declaration, entry.scope)]
    return (
        DyadicMatrix.identity(left)
        .kron(_exact(entry.operator_blocks[scoped]))
        .kron(DyadicMatrix.identity(right))
    )


def _scoped_norm(declaration: GeneralDeclaration, index: int) -> Fraction:
    entry = declaration.constraint_list[index]
    return max(
        _exact(block).frobenius_upper() for block in entry.operator_blocks.values()
    )


def _party_local_rows(
    declaration: GeneralDeclaration, index: int, alice_sector: str, *, joint: bool
) -> tuple[_PartyLocalRow, ...]:
    """Lemma D (ii)(a)/(b)'s party-local rows of one entry and Alice sector.

    One per ``s_{f^c}``, in the order the oracle boundary builds them
    (:func:`certiqs_key.solvers.oracles.joint_rows._party_local_rows`), whose
    label each carries so that the multipliers are matched to their row.
    """
    entry = declaration.constraint_list[index]
    constant = Fraction(entry.scalar_bound)
    position = factor_position(declaration, entry.scope)
    by_other: dict[str, list[str]] = {}
    for sector in declaration.sector_index_set:
        by_other.setdefault(
            other_factor_label(declaration, entry.scope, sector), []
        ).append(sector)
    rows: list[_PartyLocalRow] = []
    for other, sectors in by_other.items():
        left, _, right = split_dims(declaration, entry.scope, sectors[0])
        blocks: dict[str, tuple[DyadicMatrix, tuple[int, int, int]]] = {}
        for sector in sectors:
            dims = split_dims(declaration, entry.scope, sector)
            block = _exact(
                entry.operator_blocks[declaration.split_sector(sector)[position]]
            )
            deviation = block - DyadicMatrix.identity(dims[1], constant)
            label = joint_label((alice_sector, sector)) if joint else sector
            blocks[label] = (deviation, dims)
        rows.append(
            _PartyLocalRow(
                relation=entry.relation,
                label=f"party_local[{index}]@{alice_sector}|{other}",
                comparison=declaration.alice_dim_of(alice_sector) * left * right,
                blocks=blocks,
                norm=max(
                    deviation.frobenius_upper() for deviation, _ in blocks.values()
                ),
            )
        )
    return tuple(rows)


def _frame_error(tau: Matrix, frame: AliceFrame, w: DyadicMatrix) -> Fraction | None:
    """Return a dyadic ``eps >= ||W~ - W||_op``, decided exactly, or ``None``.

    ``req:verified-feasible-side`` (iv): where ``tau`` is diagonal, the frame
    is the full or the diagonal frame, and ``W~`` vanishes exactly wherever
    ``W = tau^{1/2} iota`` does, both have at most one non-zero entry per row
    and per column, and the norm of the difference is the largest modulus of
    the entrywise difference, at most ``|w~^2 - tau_ii| / w~`` at each entry.
    ``0`` where every ``w~^2 = tau_ii`` exactly. ``None`` everywhere else.
    """
    marginal = np.asarray(tau, dtype=np.complex128)
    width = marginal.shape[0]
    diagonal = np.diag(marginal)
    if np.any(marginal - np.diag(diagonal)) or np.any(diagonal.imag):
        return None
    kept = [i for i in range(width) if diagonal[i] != 0]
    expected = np.eye(width)[:, list(range(width)) if frame.is_full_frame else kept]
    if not np.array_equal(np.asarray(frame.iota, dtype=np.complex128), expected):
        return None
    error = Fraction(0)
    for i in range(width):
        for j in range(expected.shape[1]):
            real, imag = w.entry(i, j)
            if expected[i, j] == 0 or diagonal[i] == 0:
                if real or imag:
                    return None
                continue
            if imag or real <= 0:
                return None
            target = Fraction(float(diagonal[i].real))
            error = max(error, abs(real * real - target) / real)
    return dyadic_upper(error)


def _frame_norm(w: DyadicMatrix) -> Fraction:
    """``||W~||_op`` where at most one entry per row and column is non-zero."""
    largest = Fraction(0)
    rows, cols = w.shape
    for i in range(rows):
        for j in range(cols):
            real, imag = w.entry(i, j)
            largest = max(largest, abs(real) + abs(imag))
    return largest


def _trusted_group(
    parametrization: JointChoiParametrization, alice_sector: str
) -> _Group:
    declaration = parametrization.declaration
    frame = parametrization.frames[alice_sector]
    w = _exact(frame.w)
    lifted: list[_LiftedRow] = []
    party_local: list[_PartyLocalRow] = []
    for index, entry in enumerate(declaration.constraint_list):
        if entry.is_party_local:
            party_local.extend(
                _party_local_rows(declaration, index, alice_sector, joint=False)
            )
            continue
        theta = (
            _exact(entry.operator_bound(alice_sector))
            if entry.rhs_tag is GeneralRhsTag.GENERAL
            # THE EXACT PRODUCT c_k tau, not the binary64 one the oracle was
            # handed (req:verified-feasible-side (i)).
            else _exact(declaration.marginal_block(alice_sector)).scale(
                Fraction(entry.scalar_bound)
            )
        )
        lifted.append(
            _LiftedRow(
                relation=entry.relation,
                theta=theta,
                operators={
                    sector: _lifted(declaration, index, sector)
                    for sector in declaration.sector_index_set
                },
                norm=_scoped_norm(declaration, index),
            )
        )
    has_rows = bool(lifted or party_local)
    error = (
        _frame_error(declaration.marginal_block(alice_sector), frame, w)
        if has_rows
        else None
    )
    return _Group(
        unit=False,
        input_dim=frame.input_dim,
        pairs={
            sector: (alice_sector, sector) for sector in declaration.sector_index_set
        },
        pad={
            sector: declaration.sector_dim(sector)
            for sector in declaration.sector_index_set
        },
        lifted=tuple(lifted),
        party_local=tuple(party_local),
        frame=w,
        frame_error=error,
        frame_norm=_frame_norm(w) if error is not None else Fraction(0),
    )


def _untrusted_group(parametrization: JointChoiParametrization) -> _Group:
    declaration = parametrization.declaration
    pairs = {joint_label(pair): pair for pair in parametrization.joint_sectors}
    lifted: list[_LiftedRow] = []
    party_local: list[_PartyLocalRow] = []
    for index, entry in enumerate(declaration.constraint_list):
        if entry.is_party_local:
            for alice_sector in declaration.alice_sectors:
                party_local.extend(
                    _party_local_rows(declaration, index, alice_sector, joint=True)
                )
            continue
        lifted.append(
            _LiftedRow(
                relation=entry.relation,
                theta=Fraction(entry.scalar_bound),
                operators={
                    label: DyadicMatrix.identity(declaration.alice_dim_of(t)).kron(
                        _lifted(declaration, index, s)
                    )
                    for label, (t, s) in pairs.items()
                },
                norm=_scoped_norm(declaration, index),
            )
        )
    return _Group(
        unit=True,
        input_dim=1,
        pairs=pairs,
        pad={
            label: declaration.joint_block_dim(*pair) for label, pair in pairs.items()
        },
        lifted=tuple(lifted),
        party_local=tuple(party_local),
        frame=None,
        frame_error=None,
        frame_norm=Fraction(0),
    )


#: The exact data per parametrization, built once per run: only the gradient
#: and the multipliers change from bracket to bracket. Keyed by identity, the
#: object itself kept so that a reused id cannot alias.
_GROUPS: dict[int, tuple[JointChoiParametrization, Mapping[str, _Group]]] = {}


def _groups(parametrization: JointChoiParametrization) -> Mapping[str, _Group]:
    cached = _GROUPS.get(id(parametrization))
    if cached is not None and cached[0] is parametrization:
        return cached[1]
    declaration = parametrization.declaration
    groups: Mapping[str, _Group] = (
        {t: _trusted_group(parametrization, t) for t in declaration.alice_sectors}
        if declaration.is_trusted_source
        else {"*": _untrusted_group(parametrization)}
    )
    if len(_GROUPS) >= 16:
        _GROUPS.clear()
    _GROUPS[id(parametrization)] = (parametrization, groups)
    return groups


def _in_cone(multiplier: DyadicMatrix, relation: ConstraintRelation) -> DyadicMatrix:
    """Shift an inequality row's multiplier exactly into its cone.

    ``req:verified-feasible-side`` (ii): ``Lambda_r + mu_r 1`` with a dyadic
    ``mu_r >= max{0, -l_r}``, ``l_r`` the lemma's lower bound on the least
    eigenvalue. In the Lagrangian sign of :class:`OracleDual` a ``preceq``
    row's multiplier is ``-Lambda_r``, so it is shifted down instead.
    """
    size = multiplier.shape[0]
    if relation is ConstraintRelation.SUCCEQ:
        low = least_eigenvalue_bound(multiplier)
        if low < 0:
            return multiplier + DyadicMatrix.identity(size, dyadic_upper(-low))
    elif relation is ConstraintRelation.PRECEQ:
        high = largest_eigenvalue_bound(multiplier)
        if high > 0:
            return multiplier - DyadicMatrix.identity(size, dyadic_upper(high))
    return multiplier


def _scalar_in_cone(value: Fraction, relation: ConstraintRelation) -> Fraction:
    if relation is ConstraintRelation.SUCCEQ:
        return max(value, Fraction(0))
    if relation is ConstraintRelation.PRECEQ:
        return min(value, Fraction(0))
    return value


def _check_layout(group: _Group, solve: GroupSolve, name: str) -> None:
    """Refuse a dual whose rows are not the group's rows, an engine defect."""
    dual = solve.dual
    assert dual is not None
    labels = tuple(row.label for row in group.party_local)
    problem = solve.problem
    if (
        len(dual.rows) != len(group.lifted)
        or len(dual.general_rows) != len(group.party_local)
        or (
            problem is not None
            and tuple(row.label for row in problem.general_rows) != labels
        )
    ):
        raise ValueError(
            f"group {name!r}: the backend's dual names rows that are not the "
            "declaration's rows (req:verified-feasible-side (i))"
        )


def _same(matrix: DyadicMatrix) -> DyadicMatrix:
    return matrix


def _exact_hermitian(block: Any) -> DyadicMatrix:
    return _exact(block).hermitian_part()


def _group_bound(
    group: _Group,
    gradient: Mapping[JointSector, Any],
    solve: GroupSolve | None,
    name: str,
    *,
    hermitian: Callable[[Any], Any] = _exact_hermitian,
    lift: Callable[[DyadicMatrix], Any] = _same,
    frame: Any = None,
    floor: Callable[[Any], Fraction] | None = None,
    enclosed: bool = False,
) -> tuple[Fraction, Fraction, Fraction, str]:
    """Return ``(b, sum kappa, sum ||Lambda|| bounds, source)`` for one group.

    ``gradient``'s blocks are binary64 here, read as exact dyadic Hermitian
    parts, or a ball enclosure in the certified evaluation (``lem:certified-bracket``
    (iii)), which passes ``hermitian`` and ``lift`` (dyadic data into its
    matrices), its ENCLOSED exact
    frame and ``floor`` (``lambda_min`` over the ball) with ``enclosed``: the
    rows are then built from the exact frame, so no row multiplier is zeroed
    and no deduction ``kappa`` arises. The multipliers are read as
    ``req:verified-feasible-side`` (ii) reads them on both paths.
    """
    has_rows = bool(group.lifted or group.party_local)
    dual = None if solve is None else solve.dual
    if dual is None or not dual.is_finite() or (group.input_dim == 1 and not has_rows):
        source, dual = MULTIPLIERS_ZERO, None
    elif not enclosed and not group.unit and has_rows and group.frame_error is None:
        source = MULTIPLIERS_ROWS_ZEROED
    else:
        source = MULTIPLIERS_BACKEND
    if dual is not None:
        assert solve is not None
        _check_layout(group, solve, name)
    residual = {label: hermitian(gradient[pair]) for label, pair in group.pairs.items()}
    constant = Fraction(0)
    if dual is not None:
        if group.unit:
            scalar = Fraction(float(np.asarray(dual.coupling).real))
            constant += scalar
            for label in residual:
                residual[label] = residual[label] - lift(
                    DyadicMatrix.identity(group.pad[label], scalar)
                )
        else:
            coupling = _exact(np.asarray(dual.coupling)).hermitian_part()
            constant += coupling.trace()
            for label in residual:
                residual[label] = residual[label] - lift(
                    coupling.kron(DyadicMatrix.identity(group.pad[label]))
                )
    deduction = Fraction(0)
    norms = Fraction(0)
    use_rows = dual is not None and source == MULTIPLIERS_BACKEND
    charge = use_rows and not enclosed and not group.unit
    charge = charge and group.frame_error is not None
    error = group.frame_error or Fraction(0)
    w = frame if enclosed else group.frame

    def kappa(multiplier: DyadicMatrix, row_norm: Fraction) -> None:
        """Lemma D (iv)'s deduction for one row, from dyadic norm bounds."""
        nonlocal deduction, norms
        bound = multiplier.frobenius_upper()
        norms += bound
        deduction += (
            group.input_dim * error * (2 * group.frame_norm + error) * bound * row_norm
        )

    if use_rows:
        assert dual is not None
        for row, value in zip(group.lifted, dual.rows, strict=True):
            if group.unit:
                weight = _scalar_in_cone(
                    Fraction(float(np.asarray(value).real)), row.relation
                )
                if weight == 0:
                    continue
                assert isinstance(row.theta, Fraction)
                constant += weight * row.theta
                for label in residual:
                    residual[label] = residual[label] - lift(
                        row.operators[label].scale(weight)
                    )
                continue
            assert w is not None and isinstance(row.theta, DyadicMatrix)
            multiplier = _in_cone(
                _exact(np.asarray(value)).hermitian_part(), row.relation
            )
            constant += multiplier.pairing(row.theta)
            if charge:
                kappa(multiplier, row.norm)
            pulled = w.adjoint @ lift(multiplier) @ w
            for label in residual:
                residual[label] = residual[label] - pulled.kron(
                    lift(row.operators[label])
                )
        for local, weights in zip(group.party_local, dual.general_rows, strict=True):
            size = local.comparison
            combined = np.zeros((size, size), dtype=np.complex128)
            for weight, element in zip(
                np.asarray(weights), hermitian_basis(size), strict=True
            ):
                combined = combined + float(weight) * element
            multiplier = _in_cone(_exact(combined).hermitian_part(), local.relation)
            if charge:
                kappa(multiplier, local.norm)
            if w is None:
                pulled = lift(multiplier)
            else:
                frame_lift = w.kron(lift(DyadicMatrix.identity(size // w.shape[0])))
                pulled = frame_lift.adjoint @ lift(multiplier) @ frame_lift
            for label, (deviation, (left, scoped, right)) in local.blocks.items():
                input_dim = pulled.shape[0] // (left * right)
                residual[label] = residual[label] - pulled.kron(
                    lift(deviation)
                ).permuted((input_dim, left, right, scoped), (0, 1, 3, 2, 4, 5, 7, 6))
    bound_of = least_eigenvalue_bound if floor is None else floor
    smallest = min(bound_of(matrix) for matrix in residual.values())
    bound = group.input_dim * smallest + constant - deduction
    return bound, deduction, norms, source


def verified_feasible_side(
    parametrization: JointChoiParametrization,
    gradient: Mapping[JointSector, Matrix],
    solves: Mapping[str, GroupSolve],
) -> FeasibleSideBound:
    """Return ``b^F_t`` of ``req:verified-feasible-side`` at one bracket.

    Implements ``meat-core/frank-wolfe/req:verified-feasible-side`` and
    evaluates ``meat-core/frank-wolfe/lem:feasible-side-dual`` (i), (ii), (iv):
    the sum over the groups of Lemma D's bound (with its frame deduction) at
    the gradient blocks ``gradient`` as the engine computed them, from the
    multipliers in ``solves`` (a group absent there, or whose dual is
    ``None`` or not finite, is bounded with zero multipliers). The result is
    exact and at most the minimum of ``<G, J'>`` over the exact ``Feas^J``,
    whatever the backend reported.
    """
    total = Fraction(0)
    deduction = Fraction(0)
    norms = Fraction(0)
    sources: dict[str, str] = {}
    for name, group in _groups(parametrization).items():
        bound, kappa, norm, source = _group_bound(
            group, gradient, solves.get(name), name
        )
        total += bound
        deduction += kappa
        norms += norm
        sources[name] = source
    return FeasibleSideBound(total, deduction, norms, sources)


def feasible_side_over_enclosure(
    parametrization: JointChoiParametrization,
    gradient: Mapping[JointSector, Any],
    frames: Mapping[str, Any],
    solves: Mapping[str, GroupSolve],
    *,
    lift: Callable[[DyadicMatrix], Any],
    floor: Callable[[Any], Fraction],
) -> tuple[Fraction, Mapping[str, str]]:
    """Return ``b^F`` of ``meat-core/frank-wolfe/lem:certified-bracket`` (iii).

    The groups, rows and multiplier reading of :func:`verified_feasible_side`
    (``req:certified-evaluation`` (v)(c): the Hermitian parts, zero without a
    finite dual, the exact shift into an inequality row's cone), with
    ``gradient`` an enclosure of the gradient's blocks, ``frames`` an
    enclosure of the exact frame ``W_t`` per Alice sector, and ``floor`` a
    lower bound ``l_p - rho_p`` on ``lambda_min`` over each residual's
    enclosure. No row multiplier is zeroed and no frame deduction is made: the
    rows are built from the exact frame.
    """
    total = Fraction(0)
    sources: dict[str, str] = {}
    for name, group in _groups(parametrization).items():
        frame = None if group.unit else frames[next(iter(group.pairs.values()))[0]]
        bound, _, _, sources[name] = _group_bound(
            group,
            gradient,
            solves.get(name),
            name,
            hermitian=lambda block: block.hermitian_part(),
            lift=lift,
            frame=frame,
            floor=floor,
            enclosed=True,
        )
        total += bound
    return total, sources
