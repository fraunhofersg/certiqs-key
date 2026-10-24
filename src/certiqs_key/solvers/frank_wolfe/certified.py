"""The certified evaluation of the first-order bound, at the run's final points.

``meat-core/frank-wolfe/req:certified-evaluation``, by ``lem:certified-bracket``
(``lem:certified-bracket-enclosed`` over a companion's enclosures) and
``cor:certified-keylength`` (``cor:certified-keylength-reference`` on a
reference companion). The search stays in binary64; after it the
bracket is formed again at the at most five points the run's first-order number
came from (on a reference companion, the five best contributing points of the
search's and the polish's sets together:
:meth:`~certiqs_key.solvers.frank_wolfe.reference.ReferenceBracket.certification_points`),
every number between the declaration's data and the bracket exact
or rigorously enclosed (:mod:`certiqs_key.foundations.balls`), and the best
certified bracket is the run's certified number. A point failing anywhere is
dropped with its reason, never repaired.

WHAT IS READ (item (ii)). The declaration's data exactly: Alice's slot and
marginal, each measured block as the dyadic rational it is or, on a reference
companion, the centres and radii its compilation carries, recentred, and the
box and core of every factor enclosure it carries. From the
engine only combinatorial structure (alphabets, announcement, sifting, raw key,
the frame's ``iota``, the exact acceptance support, the rows' exact data of
:mod:`~certiqs_key.solvers.frank_wolfe.verified`) and each solve's multipliers.
Zero patterns and key-inertness are read off the enclosures.

THE MAPS IN FACTOR FORM (items (iii), (iv); ``meat-core/lem:kraus-freedom``).
Every element is ``E^dagger X E``, ``X`` positive definite, ``E`` of full row
rank: exact, or, for a block whose rank the factor rule fixes, the box of the
adjoints ``L^dagger`` of its enclosed factors, of rank ``k`` at every factor
(:func:`_companion_element`). A pass class' listing is ``T E~``, ``E~`` the
stack of the ``E_x (x) E_v`` and only ``T^dagger T`` formed; ``E~ = B~ C`` with
``B~`` exact of full column rank (``lem:certified-bracket-enclosed`` (b),
:func:`_class`; rows held through boxes grouped by the tuple of blocks they
are boxed at, each block named by its key and never by its box), and the ball
Cholesky of ``G = B~^dagger T^dagger T B~``
certifies ``B = T B~`` injective (else ``support_not_established``), so
``Q = B R_G^{-1}`` spans a subspace containing the branch operator's support at
every member; the matrix functions act on ``N = Q^dagger X Q`` and the pinched
``Psi_j``, whose certified floors prove the subspaces are the supports (else
``floor_not_certified``). In POVM form the frame's invertible
``R = diag(sqrt tau)`` is moved into the point.

TWO ENCLOSURES OF ONE BLOCK (item (iv)). A companion's block may come with a
factor enclosure (``foundations/def:factor-enclosure``) besides its entrywise
one. The statistics read the entrywise enclosure, the deficits the enclosure
that holds the block's factor form (item (v)(c)); the entrywise rule decides
first and the factor rule only where it leaves the block undecided or fixes no
rank; and wherever a factor enclosure is carried the two are cross-checked: a
contradiction fails every point with ``factor_enclosure_inconsistent``, which
also withdraws the companion's bracket (the caller's,
:mod:`~certiqs_key.solvers.frank_wolfe.general_keyrate`).

THE REORDERED FORM CHECKS ITSELF. Where the engine's reordered form of an
element with a boxed block is inconsistent with itself (parts and block keys
differ in number, a split form where the factor is exact or none where it is
a box, one tuple of block keys at two positions or dimensions), no claim
admits it: every point of the declaration evaluated fails with
``boxed_form_inconsistent`` rather than the evaluation crashing the run. On a
reference companion the fallback of item (i) then runs as for any companion
that certifies no point; on the searched declaration the run's number stays
first order.
"""

from __future__ import annotations

import math
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any, cast

import numpy as np

from certiqs_key.foundations import balls
from certiqs_key.foundations.balls import Ball, NotCertified
from certiqs_key.foundations.dyadic import (
    DyadicMatrix,
    enclosure_eigenvalue_bounds,
    least_eigenvalue_bound,
)
from certiqs_key.foundations.errors import HypothesisError
from certiqs_key.foundations.exact import (
    Cx,
    Matrix,
    factor_form,
    kron,
    rank_factorisation,
)
from certiqs_key.foundations.recentring import hermitian_enclosure, recentred_enclosure
from certiqs_key.foundations.reference import FactorEnclosure, fixes_rank
from certiqs_key.meat_core.acceptance.geometry import SINGLETON
from certiqs_key.meat_core.objective.joint import DroppedSet, JointMaps, JointSector
from certiqs_key.solvers.frank_wolfe.acceptance_iterate import AcceptanceIterate
from certiqs_key.solvers.frank_wolfe.certified_record import (
    ACCEPTANCE_GEOMETRY_NOT_CERTIFIED,
    ACCEPTANCE_ITERATE_NOT_EXACT,
    BLOCK_NOT_POSITIVE_DEFINITE,
    BOXED_FORM_INCONSISTENT,
    CERTIFIER_UNAVAILABLE,
    EVALUATION_OFF,
    FACTOR_ENCLOSURE_INCONSISTENT,
    FLOOR_NOT_CERTIFIED,
    FRAME_NOT_ENCLOSED,
    NOT_CERTIFIED,
    POSITIVITY_NOT_CERTIFIED,
    RANK_NOT_CERTIFIED,
    SUPPORT_NOT_ESTABLISHED,
    WORKING_PRECISION,
    CertifiedEvaluation,
    CertifiedPoint,
)
from certiqs_key.solvers.frank_wolfe.verified import (
    GroupSolve,
    feasible_side_over_enclosure,
)
from certiqs_key.solvers.oracles.acceptance import (
    AcceptanceOracle,
    ExactAcceptanceOracle,
)

#: A point as the evaluation takes it: blocks, ``q_t``, the solves, its iteration.
CandidatePoint = tuple[
    Mapping[JointSector, Any], AcceptanceIterate, Mapping[str, GroupSolve] | None, int
]
_ONE, _NIL = Cx(Fraction(1), Fraction(0)), Cx(Fraction(0), Fraction(0))


class _Fail(Exception):
    """A step not established; ``reason`` is the requirement's string."""

    def __init__(self, reason: str, detail: str) -> None:
        super().__init__(f"{reason}: {detail}")
        self.reason = reason


#: A factor ``E`` of a factor form: exact, or the box of an enclosed factor's
#: adjoints (the third kind of ``lem:certified-bracket-enclosed``).
_Factor = Matrix | Ball

#: A block named as a block: ``(factor position, the factor's letter, its
#: sector)``, the requirement's ``(factor, sector, letter)``. Two keys agree
#: exactly when they name the same block, whatever the blocks' boxes.
_BlockKey = tuple[int, str, str]


@dataclass(frozen=True)
class _Split:
    """An element with a block of the third kind, in the lemma's reordered form.

    ``lem:certified-bracket-enclosed`` (b), the reordering:
    ``E_v = R_v (E^ex_v (x) E^box_beta) Sigma_beta(n)``. ``exact`` is
    ``E^ex_v``, the Kronecker product, in factor order, of the parts whose
    ``E`` is exact (``[[1]]`` where every part is boxed); ``box`` the Kronecker
    product, in factor order, of the boxed parts' boxes, which contains
    ``E^box_beta`` at every member; ``blocks`` the tuple ``beta(v)``, the keys of
    the boxed parts in factor order; ``boxed`` the positions of ``beta`` among
    the factors; ``rows`` and ``columns`` each part's ``p_j`` and ``n_j``, which
    fix ``R_v`` and ``Sigma_beta(n)``.
    """

    exact: Matrix
    box: Ball
    blocks: tuple[_BlockKey, ...]
    boxed: tuple[bool, ...]
    rows: tuple[int, ...]
    columns: tuple[int, ...]


@dataclass(frozen=True)
class _Element:
    """One element: its enclosure, its zero decision, its factor form ``(E, X)``."""

    full: Ball
    #: Decided zero (True), decided non-zero (False), undecided (None).
    zero: bool | None
    form: tuple[_Factor, Ball] | None = None
    #: Why no rank is fixed, where ``form`` is absent and the element not zero.
    cause: str | None = None
    #: The reordered form, where ``E`` is held through a box (:func:`_product`).
    split: _Split | None = None


def _exact_element(block: Matrix) -> _Element:
    """Return an element on exact data (``cor:least-eigenvalue-over-enclosure``)."""
    try:
        form = factor_form(block)
    except HypothesisError as failure:
        return _Element(Ball.of(block), False, cause=f"not PSD: {failure}")
    if form is None:
        return _Element(Ball.of(block), True)
    return _Element(Ball.of(block), False, (form[0], Ball.of(form[1])))


def _enclosed_element(centre: Matrix, radii: Sequence[Sequence[Any]]) -> _Element:
    """Return an element known through an enclosure: item (iv)(a), the entrywise rule.

    ``foundations/cor:least-eigenvalue-over-enclosure`` (iv) on the recentred,
    Hermitian-centred enclosure: the rows whose every centre and radius is 0
    are dropped (``E`` the coordinate selection) and the rest needs a positive
    lower bound on its least eigenvalue over the enclosure. Decided zero where
    every centre and radius is 0, decided non-zero where some ``|C| > r``
    (``lem:certified-bracket-enclosed``), undecided otherwise.
    """
    hermitian = hermitian_enclosure(centre, tuple(map(tuple, radii)))
    enclosure, _ = recentred_enclosure(hermitian)
    c, r = enclosure.centre, enclosure.radii
    if enclosure.is_exact:
        return _exact_element(c)
    n, full = len(c), Ball.enclosure(c, r)
    pairs = [(c[i][j], r[i][j]) for i in range(n) for j in range(n)]
    zero = (
        False
        if any(x.squared_modulus > rad * rad for x, rad in pairs)
        else True
        if all(x.is_zero and rad == 0 for x, rad in pairs)
        else None
    )
    kept = [
        i for i in range(n) if any(not c[i][j].is_zero or r[i][j] for j in range(n))
    ]
    if not kept:
        return _Element(full, True)
    block = [[c[i][j] for j in kept] for i in kept]
    rads = [[r[i][j] for j in kept] for i in kept]
    low = enclosure_eigenvalue_bounds(block, rads)[0]
    if not low > 0:
        cause = f"no positive floor on its block ({float(low):.2e})"
        return _Element(full, zero, cause=cause)
    select = tuple(tuple(_ONE if j == i else _NIL for j in range(n)) for i in kept)
    return _Element(full, zero, (select, Ball.enclosure(block, rads)))


def _core(factor: FactorEnclosure) -> Ball:
    """Return the exact core ``W`` of a factor enclosure as balls."""
    k = factor.columns
    return Ball.of(
        [[Cx(factor.core[i], Fraction(0)) if i == j else _NIL for j in range(k)]
         for i in range(k)]
    )


def _factor_rule(
    factor: FactorEnclosure,
) -> tuple[bool | None, tuple[Ball, Ball] | None]:
    """Return item (iv)(b)'s decision on a block from its factor enclosure.

    ``foundations/cor:rank-over-factor-enclosure``: with no column the block
    is zero, ``(True, None)`` (part (i)); with ``k >= 1`` columns and a Gram
    floor established (:func:`~certiqs_key.foundations.reference.fixes_rank`,
    part (ii) with part (iii)'s ``G`` and ``rho``) it is not zero, with factor
    form ``L^dagger``, held through the box of the adjoints, and the exact core
    as ``X~`` (part (ii): ``X = E^dagger W E``, ``E = L^dagger`` of rank ``k``
    at every factor); otherwise it decides nothing, ``(None, None)``.
    """
    if factor.columns == 0:
        return True, None
    if not fixes_rank(factor):
        return None, None
    box = Ball.enclosure(factor.centre, factor.radii)
    return False, (box.adjoint, _core(factor))


def _members(factor: FactorEnclosure) -> Ball:
    """Return an entrywise enclosure of ``L W L^dagger`` for every factor ``L``.

    Item (iv)(c): the product of the box, the core and the box's adjoint in
    ball arithmetic, rigorously enclosed; the zero matrix with no column.
    """
    if factor.columns == 0:
        return Ball.zeros(factor.dimension)
    box = Ball.enclosure(factor.centre, factor.radii)
    return box @ _core(factor) @ box.adjoint


def _cross_check(
    centre: Matrix,
    radii: Sequence[Sequence[Any]],
    entrywise_zero: bool | None,
    factor: FactorEnclosure,
    factor_zero: bool | None,
    where: str,
) -> None:
    """Raise ``factor_enclosure_inconsistent`` where a block's two enclosures clash.

    ``req:certified-evaluation`` (iv)(c): inconsistent where the enclosure of
    ``L W L^dagger`` (:func:`_members`) and the block's entrywise enclosure as
    the compilation carries it are disjoint at some entry -- ``|M_il - C_il|``
    certainly above ``r_il`` -- or where the entrywise rule (a) and the factor
    rule decide the block, one zero and the other not zero. The companion's
    own block lies in both by (H-FAC) and the enclosure property, so either is
    a defect of a carrier; no rule tells which enclosure is wrong, so every
    point fails, and the caller withdraws the companion's bracket.
    """
    if {entrywise_zero, factor_zero} == {True, False}:
        raise _Fail(
            FACTOR_ENCLOSURE_INCONSISTENT,
            f"{where}: the entrywise rule decides it "
            + ("zero" if entrywise_zero else "not zero")
            + " and the factor rule "
            + ("zero" if factor_zero else "not zero"),
        )
    members = _members(factor)
    for i, row in enumerate(centre):
        for j, value in enumerate(row):
            if members.beyond(i, j, value, radii[i][j]):
                raise _Fail(
                    FACTOR_ENCLOSURE_INCONSISTENT,
                    f"{where}: L W L^dagger and the entrywise enclosure are "
                    f"disjoint at entry ({i}, {j})",
                )


def _companion_element(
    centre: Matrix,
    radii: Sequence[Sequence[Any]],
    factor: FactorEnclosure | None,
    where: str,
) -> _Element:
    """Return a block a companion carries, by item (iv)'s rule over an enclosure.

    ``meat-core/frank-wolfe/req:certified-evaluation`` (iv), which establishes
    the hypotheses "decided" and "of fixed rank" of
    ``lem:certified-bracket-enclosed`` block by block. (a) The entrywise rule,
    :func:`_enclosed_element`, comes first. (b) Where it leaves the block
    undecided or fixes no rank and the compilation carries a factor enclosure
    of the block, the factor rule (:func:`_factor_rule`) follows: no column
    is zero, a certified Gram floor not zero of the third kind of fixed rank.
    (c) Wherever a factor enclosure is carried, whichever rule fixes the rank,
    the cross-check (:func:`_cross_check`) raises
    ``factor_enclosure_inconsistent`` on a contradiction. That the block is a
    member of its factor enclosure, (H-FAC), is decided by no rule here.
    """
    entrywise = _enclosed_element(centre, radii)
    if factor is None:
        return entrywise
    decided, form = _factor_rule(factor)
    _cross_check(centre, radii, entrywise.zero, factor, decided, where)
    if entrywise.zero is True or (
        entrywise.zero is False and entrywise.form is not None
    ):
        return entrywise
    if decided is None:
        return entrywise
    return _Element(entrywise.full, decided, form)


def _kron_factor(a: _Factor, b: _Factor) -> _Factor:
    """Return ``a (x) b``: exact where both are, else as balls."""
    if isinstance(a, Ball) or isinstance(b, Ball):
        left = a if isinstance(a, Ball) else Ball.of(a)
        right = b if isinstance(b, Ball) else Ball.of(b)
        return left.kron(right)
    return kron(a, b)


def _shape(factor: _Factor) -> tuple[int, int]:
    """Return the rows and columns of a factor ``E``, exact or a box."""
    if isinstance(factor, Ball):
        return factor.shape
    return len(factor), len(factor[0])


def _product(parts: Sequence[_Element], blocks: Sequence[_BlockKey]) -> _Element:
    """Return the tensor product of factor elements, ``blocks`` naming each part.

    ``lem:certified-bracket-enclosed`` (b): a tensor product of factor forms
    is a factor form, the cores' tensor product positive definite, of the
    same rank at every member however many parts are of the third kind (an
    enclosed factor): "the tensor product, in the order of F, of one matrix
    for each block". ``E`` is then held through the Kronecker product of the
    parts' boxes (``req:certified-evaluation`` (iii)), which contains it at
    every member. A part is of the third kind exactly when its ``E`` is a box,
    which only the factor rule of (iv)(b) gives (the kind
    ``req:certified-evaluation`` (iii)(a) fixes: a block that rule decides not
    zero, fixing its rank); an entrywise-rule part's ``E`` is an exact
    selection and it is of the second kind. Such an element also carries its
    reordered form (:class:`_Split`, "(b), the reordering"): the exact parts'
    Kronecker product, the boxed parts' one, the tuple ``beta(v)`` of the boxed
    parts' block keys, and the dimensions; :func:`_class` groups by the tuple.
    No box is compared. A part decided zero decides the element zero, whatever
    its other parts: the lemma asks "decided" and "of fixed rank" of no block
    of an element another of whose blocks is zero for every member, and
    ``req:certified-evaluation`` (iv) waives its rule there.
    """
    if len(blocks) != len(parts):
        raise _Fail(
            BOXED_FORM_INCONSISTENT,
            f"{len(parts)} parts named by {len(blocks)} block keys",
        )
    full = parts[0].full
    for part in parts[1:]:
        full = full.kron(part.full)
    if any(part.zero for part in parts):
        return _Element(full, True)
    zero = None if any(part.zero is None for part in parts) else False
    if any(part.form is None for part in parts):
        cause = next(p.cause for p in parts if p.form is None)
        return _Element(full, zero, cause=cause)
    forms = [cast(tuple[_Factor, Ball], part.form) for part in parts]
    e, core = forms[0]
    for factor, factor_core in forms[1:]:
        e, core = _kron_factor(e, factor), core.kron(factor_core)
    boxed = tuple(isinstance(factor, Ball) for factor, _ in forms)
    if not any(boxed):
        return _Element(full, zero, (e, core))
    exact: Matrix = ((_ONE,),)
    box: Ball | None = None
    for factor, _ in forms:
        if isinstance(factor, Ball):
            box = factor if box is None else box.kron(factor)
        else:
            exact = kron(exact, factor)
    shapes = [_shape(factor) for factor, _ in forms]
    split = _Split(
        exact,
        cast(Ball, box),
        tuple(key for key, held in zip(blocks, boxed, strict=True) if held),
        boxed,
        tuple(p for p, _ in shapes),
        tuple(n for _, n in shapes),
    )
    return _Element(full, zero, (e, core), split=split)


def _exact_rows(values: Any) -> Matrix:
    """Return the exact copy of a binary64 array."""
    array = np.asarray(values, dtype=np.complex128)
    return tuple(
        tuple(Cx(Fraction(z.real), Fraction(z.imag)) for z in row.tolist())
        for row in array
    )


@dataclass(frozen=True)
class _Class:
    """A pass class at a pair: ``C``, ``G``, ``R_G``; per raw key ``F_j, R_j``."""

    c: Ball
    gram: Ball
    root: Ball
    labels: tuple[tuple[Ball, Ball], ...]


@dataclass
class _Model:
    """What the evaluation reads of one declaration, built once per run."""

    maps: JointMaps
    support: tuple[str, ...]
    live: tuple[str, ...]
    #: Per Alice sector ``R``'s diagonal (POVM form) or ``None``, and ``W_t``.
    scale: dict[str, list[Any] | None] = field(default_factory=dict)
    frames: dict[str, Ball] = field(default_factory=dict)
    gamma: dict[tuple[str, JointSector], Ball] = field(default_factory=dict)
    evaluated: dict[str, tuple[JointSector, ...]] = field(default_factory=dict)
    classes: dict[tuple[str, JointSector], list[_Class]] = field(default_factory=dict)
    #: A reason that marks every point.
    failure: _Fail | None = None


def _carried(source: Any, letter: str, s: int) -> FactorEnclosure | None:
    """Return the factor enclosure a compiled factor carries on a block, or ``None``.

    Item (ii): the matrix box and core of every factor enclosure the
    compilation carries. One failing the decisions of
    ``foundations/req:snap-reference`` (i) is not carried, so it is not read.
    """
    found = source.factor_enclosures.get(letter)
    factor = None if found is None else found[s]
    return None if factor is None or factor.failures() else factor


def _bob_elements(maps: JointMaps, companion: Any) -> dict[tuple[str, str], _Element]:
    """Return every ``F_v^(s)``; a companion's factors from its enclosures (ii).

    Every block a companion carries goes through :func:`_companion_element`,
    so the cross-check of item (iv)(c) runs on every block with a factor
    enclosure, whatever pair it is a factor at; an inconsistency raises
    :class:`_Fail`, which marks every point.

    The compiled companion replaces every measured factor that carries one
    (both stations of an entanglement-based declaration), any of them read
    through enclosures: ``lem:certified-bracket-enclosed`` is stated for the
    set of replaced factors of ``meat-core/prop:reference-companion``, and
    :func:`_product` forms an element with several blocks of the third kind.
    Each block is formed once, under its key ``(index, wire, sector)``
    (:data:`_BlockKey`), and every element it is a factor of reads that one
    block and is handed that key: the identity by which :func:`_class` groups
    rows (``req:certified-evaluation`` (iii)(a)).
    """
    d = maps.declaration
    replaced = {} if companion is None else {f.position: f for f in companion.factors}
    factor: dict[tuple[int, str, str], _Element] = {}
    for index, item in enumerate(d.factors):
        source = replaced.get(index)
        for w, wire in enumerate(item.alphabet):
            for s, sector in enumerate(item.sectors.labels):
                if source is None:
                    factor[(index, wire, sector)] = _exact_element(
                        _exact_rows(item.blocks[wire][sector])
                    )
                    continue
                letter = source.alphabet[w]
                factor[(index, wire, sector)] = _companion_element(
                    source.centres[letter][s],
                    source.radii[letter][s],
                    _carried(source, letter, s),
                    f"the element {letter} on {sector} of factor {index}",
                )
    elements: dict[tuple[str, str], _Element] = {}
    for v in d.bob_outcomes:
        for joint in d.sector_index_set:
            keys = [
                (i, part, sector)
                for i, (part, sector) in enumerate(
                    zip(d.split_letter(v), d.split_sector(joint), strict=True)
                )
            ]
            elements[(v, joint)] = _product([factor[key] for key in keys], keys)
    return elements


def _alice(model: _Model) -> dict[tuple[str, str], _Element]:
    """Return Alice's elements in the point's coordinates; fill ``R`` and the frames.

    Item (ii): ``W_t = tau^(1/2) iota`` of the support frame the engine built,
    ``tau`` diagonal and its roots enclosed; a non-diagonal marginal has no
    enclosed frame here (``frame_not_enclosed``).
    """
    d = model.maps.declaration
    elements: dict[tuple[str, str], _Element] = {}
    for t in d.alice_sectors:
        kept: list[int] | None = None
        model.scale[t] = None
        if d.is_trusted_source:
            tau = _exact_rows(d.marginal_block(t))
            if any(
                not x.is_zero
                for i, row in enumerate(tau)
                for j, x in enumerate(row)
                if i != j
            ):
                raise _Fail(FRAME_NOT_ENCLOSED, f"sector {t}: tau is not diagonal")
            iota = np.asarray(model.maps.parametrization.frames[t].iota)
            kept = [int(np.flatnonzero(iota[:, j])[0]) for j in range(iota.shape[1])]
            roots = [balls.real(tau[i][i].re).sqrt() for i in kept]
            frame = model.frames[t] = Ball.zeros(len(tau), len(kept))
            for j, i in enumerate(kept):
                frame.m[i, j] = roots[j]
            model.scale[t] = None if d.is_ensemble_form else roots
        for x in d.alice_alphabet:
            block = _exact_rows(d.alice_block(x, t))
            if model.scale[t] is not None and kept is not None:
                block = tuple(tuple(block[i][j] for j in kept) for i in kept)
            elements[(x, t)] = _exact_element(block)
    return elements


@dataclass(frozen=True)
class _Row:
    """One outcome pair of a pass class: ``E_x``, ``E_v``, ``X_x (x) X_v``, key.

    ``split`` is Bob's element in its reordered form (:class:`_Split`) exactly
    where ``bob`` is a box; its tuple of block keys is the row's group.
    """

    alice: Matrix
    #: Bob's ``E_v``: exact, or the Kronecker box of its parts.
    bob: _Factor
    core: Ball
    key: int
    split: _Split | None = None

    def __post_init__(self) -> None:
        """Refuse a boxed ``E_v`` without its reordered form, or the converse."""
        if isinstance(self.bob, Ball) != (self.split is not None):
            raise _Fail(
                BOXED_FORM_INCONSISTENT,
                "a row's split form is present exactly where E_v is a box",
            )


def _radix_split(
    index: int, dims: Sequence[int], boxed: Sequence[bool]
) -> tuple[int, int]:
    """Return ``(i_ex, i_box)``: an index over ``dims`` split at the positions of beta.

    The index of ``u_1 (x) ... (x) u_m`` (the first factor the slower) read as
    the mixed-radix digits over ``dims``; the digits outside the boxed positions
    form ``i_ex`` and those inside ``i_box``, each in factor order. This is
    ``Sigma_beta(dims)`` of ``lem:certified-bracket-enclosed`` (b), the
    reordering, on a standard basis vector: it maps index ``index`` to
    ``i_ex * prod(boxed dims) + i_box``.
    """
    digits = []
    for d in reversed(dims):
        digits.append(index % d)
        index //= d
    digits.reverse()
    i_ex = i_box = 0
    for digit, d, held in zip(digits, dims, boxed, strict=True):
        if held:
            i_box = i_box * d + digit
        else:
            i_ex = i_ex * d + digit
    return i_ex, i_box


def _columns(split: _Split, width: int) -> list[int]:
    """Return the columns of ``C_beta (x) E^box_beta`` that ``U_beta`` reads, in order.

    ``U_beta = 1_a (x) Sigma_beta(n)`` (``lem:certified-bracket-enclosed`` (b),
    the stack): column ``(c_x, c_v)`` of ``(C_beta (x) E^box_beta) U_beta`` is
    column ``(c_x, c_ex, c_box)`` of ``C_beta (x) E^box_beta``, where
    ``(c_ex, c_box)`` is ``Sigma_beta(n)``'s image of ``c_v`` over the columns
    ``n_j`` (:func:`_radix_split`) and ``width`` is ``a`` times their product.
    """
    n_v, n_box = math.prod(split.columns), split.box.shape[1]
    order = []
    for c_x in range(width // n_v):
        for c_v in range(n_v):
            c_ex, c_box = _radix_split(c_v, split.columns, split.boxed)
            order.append(c_x * n_v + c_ex * n_box + c_box)
    return order


@dataclass
class _Group:
    """The rows of a pass class whose elements have one tuple ``beta``."""

    #: The first row's split form: ``E^box_beta``'s box, the positions, ``n_j``.
    split: _Split
    #: ``S_beta``: the rows of ``E_x (x) E^ex_v`` over the group's pairs, in order.
    stack: list[tuple[Cx, ...]] = field(default_factory=list)


def _class(rows: Sequence[_Row]) -> _Class | None:
    """Return a pass class' factorisation from its outcome pairs' rows.

    ``lem:certified-bracket-enclosed`` (b), the stack, and
    ``req:certified-evaluation`` (iii)(a): the stack ``E~`` of the
    ``E_x (x) E_v`` (a row block per pair, in the class' order, its raw key per
    row) is ``B~ C`` with ``B~`` exact of full column rank. The rows whose
    ``E_v`` is exact take one exact rank factorisation together,
    ``S_0 = B_0 C_0``. The rows whose ``E_v`` is held through a box are grouped
    by their element's whole tuple ``beta(v)`` of block keys (:class:`_Split`),
    each block named by its key and never by its box: two elements share a
    group exactly when their tuples name the same blocks, and two distinct
    blocks with equal boxes are distinct entries. The rows of a pair ``(x, v)``
    of a group are ``(1 (x) R_v)((E_x (x) E^ex_v) (x) E^box_beta) U_beta`` with
    ``U_beta = 1_a (x) Sigma_beta(n)``; ``S_beta`` stacks the exact
    ``E_x (x) E^ex_v`` of the group's pairs and its exact rank factorisation
    ``S_beta = B_beta C_beta`` gives ``(B_beta (x) 1)(C_beta (x) E^box_beta)``,
    so that an exact dependence between the exact factors of the group's rows,
    Alice's (a photon-number-tagged sector) or Bob's exact blocks beside one
    shared boxed block, is reduced exactly, which the identity as ``B~`` would
    not do. ``C`` stacks ``C_0`` and each group's ``(C_beta (x) E^box_beta)
    U_beta`` as balls, the columns of each such block permuted by its own
    ``U_beta`` only, containing every member's ``C``; ``B~`` places each row
    back in the stack's order through ``R_v`` (:func:`_radix_split` over the
    rows ``p_j``). ``G = B~^dagger T^dagger T B~`` is certified positive
    definite by its ball Cholesky ``R_G``. Per raw key ``j`` the rows of ``B~``
    with that key are ``B_j C_j`` exactly, giving ``F_j = C_j R_G^{-1}`` and
    ``R_j``, the ball Cholesky factor of ``B_j^dagger (T^dagger T)_jj B_j``.
    ``None`` where ``C`` has no row. Without a boxed ``E_v`` this is the single
    exact factorisation of the stack. A dependence between the rows of ``C``
    that the grouping leaves is not removed: the floor of (iii)(b) fails closed.
    """
    labels: list[int] = []
    exact_stack: list[tuple[Cx, ...]] = []
    groups: dict[tuple[_BlockKey, ...], _Group] = {}
    #: Per stack row: (None, its exact row, 0) or (tuple, row of S_beta, box row).
    places: list[tuple[tuple[_BlockKey, ...] | None, int, int]] = []
    for row in rows:
        split = row.split
        if split is None:
            for exact in kron(row.alice, cast(Matrix, row.bob)):
                places.append((None, len(exact_stack), 0))
                exact_stack.append(exact)
                labels.append(row.key)
            continue
        group = groups.setdefault(split.blocks, _Group(split))
        first = group.split
        if (first.boxed, first.columns, first.box.shape) != (
            split.boxed,
            split.columns,
            split.box.shape,
        ):
            raise _Fail(
                BOXED_FORM_INCONSISTENT,
                f"the tuple {split.blocks} at two positions or dimensions",
            )
        base, height = len(group.stack), len(split.exact)
        group.stack.extend(kron(row.alice, split.exact))
        for alice_row in range(len(row.alice)):
            for bob_row in range(math.prod(split.rows)):
                i_ex, i_box = _radix_split(bob_row, split.rows, split.boxed)
                places.append((split.blocks, base + alice_row * height + i_ex, i_box))
                labels.append(row.key)
    b0, c0 = rank_factorisation(tuple(exact_stack)) if exact_stack else ((), ())
    blocks = [Ball.of(c0)] if c0 else []
    width = len(c0)
    #: Per tuple: B_beta, its first column in B~, the rows k_beta of E^box_beta.
    placed: dict[tuple[_BlockKey, ...], tuple[Matrix, int, int]] = {}
    for blocks_key, group in groups.items():
        box = group.split.box
        b_beta, c_beta = rank_factorisation(tuple(group.stack))
        placed[blocks_key] = (b_beta, width, box.shape[0])
        if c_beta:
            raw = Ball.of(c_beta).kron(box)
            order = _columns(group.split, raw.shape[1])
            blocks.append(raw.block(range(raw.shape[0]), order))
        width += len(c_beta) * box.shape[0]
    if width == 0:
        return None
    b_tilde: list[tuple[Cx, ...]] = []
    for owner, row_index, bob_row in places:
        entries = [_NIL] * width
        if owner is None:
            entries[: len(b0[row_index])] = b0[row_index]
        else:
            b_beta, start, k = placed[owner]
            for column, entry in enumerate(b_beta[row_index]):
                entries[start + column * k + bob_row] = entry
        b_tilde.append(tuple(entries))
    # T^dagger T: the cores X_x (x) X_v on the diagonal, one block per pair.
    cores = Ball.block_diagonal([row.core for row in rows])
    b_ball = Ball.of(b_tilde)
    gram = b_ball.adjoint @ cores @ b_ball
    root = balls.cholesky_upper(gram, "the class' Gram B~^dagger T^dagger T B~")
    inverse = balls.inverse_upper(root)
    pinched: list[tuple[Ball, Ball]] = []
    for key in sorted(set(labels)):
        index = [i for i, label in enumerate(labels) if label == key]
        bj, cj = rank_factorisation(tuple(b_tilde[i] for i in index))
        if cj:
            bj_ball = Ball.of(bj)
            gj = bj_ball.adjoint @ cores.block(index, index) @ bj_ball
            rj = balls.cholesky_upper(gj, f"the pinched Gram at raw key {key}")
            pinched.append((Ball.of(cj) @ inverse, rj))
    return _Class(Ball.stack(blocks), gram, root, tuple(pinched))


def _model(maps: JointMaps, companion: Any, dropped: DroppedSet) -> _Model:
    """Return :class:`_Model`; a failure that marks every point is kept on it.

    Bob's elements (:func:`_bob_elements`) first, so that the cross-check of
    item (iv)(c) runs on every carried factor enclosure whatever else fails;
    then Alice's elements and frames (:func:`_alice`), the statistics operators
    (:func:`_statistics_operators`) and the key's pass classes
    (:func:`_key_classes`). The acceptance support is ``eq:chacc-def``'s, which
    the engine decides exactly (the declared point's support; the union of an
    exact polytope's vertices' supports), so reading it reads no binary64
    quantity (item (ii)).
    """
    support = tuple(maps.acceptance_support)
    model = _Model(maps, support, tuple(c for c in maps.chat_key if c in support))
    try:
        bob = _bob_elements(maps, companion)
        alice = _alice(model)
        classes = _announcement_classes(maps)
        _statistics_operators(model, alice, bob, classes)
        _key_classes(model, alice, bob, classes, dropped)
    except _Fail as failure:
        model.failure = failure
    return model


#: The outcome pairs ``(x, v)`` of each announcement class.
_Announcements = dict[tuple[str, ...], list[tuple[str, str]]]


def _announcement_classes(maps: JointMaps) -> _Announcements:
    """Return the outcome pairs of each announcement class, in declared order."""
    d = maps.declaration
    classes: _Announcements = {}
    for x in d.alice_alphabet:
        for v in d.bob_outcomes:
            classes.setdefault(d.announcement(x, v), []).append((x, v))
    return classes


def _statistics_operators(
    model: _Model,
    alice: Mapping[tuple[str, str], _Element],
    bob: Mapping[tuple[str, str], _Element],
    classes: _Announcements,
) -> None:
    """Fill ``model.gamma``: ``Gamma''`` per acceptance value and joint pair.

    The sum of ``A_x (x) F_v`` over the outcome pairs whose class is accepted as
    that value, neither element decided zero; Bob's elements are summed per
    Alice letter first, so each letter costs one Kronecker product.
    """
    d = model.maps.declaration
    for chat in model.support:
        for t, s in model.maps.joint_sectors:
            per_letter: dict[str, Ball] = {}
            for kappa, members in classes.items():
                if d.accept_statistic[kappa] != chat:
                    continue
                for x, v in members:
                    if alice[(x, t)].zero or bob[(v, s)].zero:
                        continue
                    element = bob[(v, s)].full
                    per_letter[x] = (
                        element if x not in per_letter else per_letter[x] + element
                    )
            for x, summed in per_letter.items():
                term = alice[(x, t)].full.kron(summed)
                old = model.gamma.get((chat, (t, s)))
                model.gamma[(chat, (t, s))] = term if old is None else old + term


def _key_classes(
    model: _Model,
    alice: Mapping[tuple[str, str], _Element],
    bob: Mapping[tuple[str, str], _Element],
    classes: _Announcements,
    dropped: DroppedSet,
) -> None:
    """Fill ``model.evaluated`` and ``model.classes`` (items (iii), (iv)).

    Per key value and joint pair, the outcome pairs of its pass classes with
    Alice's element non-zero. An undecided element fails every point, at a
    key-inert pair too; the pair is key-inert where each class reads one raw
    key on the decided non-zero elements, and is skipped where dropped;
    otherwise every element needs a factor form, and on a key-live value each
    class its factorisation (:func:`_pass_classes`). Raises :class:`_Fail`.
    """
    maps, d = model.maps, model.maps.declaration
    for chat in maps.chat_key:
        model.evaluated[chat] = ()
        passing = [
            members
            for kappa, members in classes.items()
            if maps.sifting[kappa] and d.accept_statistic[kappa] == chat
        ]
        for pair in maps.joint_sectors:
            t, s = pair
            entering = [
                [(x, v) for x, v in members if not d.alice_block_is_zero(x, t)]
                for members in passing
            ]
            undecided = [
                v
                for members in entering
                for _, v in members
                if bob[(v, s)].zero is None
            ]
            if undecided:
                raise _Fail(
                    RANK_NOT_CERTIFIED,
                    f"the element of {undecided[0]} on {s} is undecided ({chat})",
                )
            kept = [
                [(x, v) for x, v in members if not bob[(v, s)].zero]
                for members in entering
            ]
            key_inert = all(
                len({d.raw_key(x, v) for x, v in members}) <= 1 for members in kept
            )
            if key_inert or (chat, pair) in dropped:
                continue
            for x, v in (item for members in kept for item in members):
                a, b = alice[(x, t)], bob[(v, s)]
                if b.form is None or (a.form is None and not a.zero):
                    raise _Fail(
                        RANK_NOT_CERTIFIED,
                        f"{x}, {v} at ({chat}, {pair}): {b.cause or a.cause}",
                    )
            model.evaluated[chat] += (pair,)
            if chat in model.live:
                model.classes[(chat, pair)] = _pass_classes(
                    model, alice, bob, kept, (chat, pair)
                )


def _pass_classes(
    model: _Model,
    alice: Mapping[tuple[str, str], _Element],
    bob: Mapping[tuple[str, str], _Element],
    kept: Sequence[Sequence[tuple[str, str]]],
    where: tuple[str, JointSector],
) -> list[_Class]:
    """Return each pass class' factorisation at a key-active pair (:func:`_class`).

    A class' rows are its pairs' ``E_x``, ``E_v``, ``X_x (x) X_v`` and raw key
    (:class:`_Row`); a pair whose Alice element is zero contributes none. A
    Gram not certified positive definite is ``support_not_established``.
    """
    d = model.maps.declaration
    t, s = where[1]
    built: list[_Class] = []
    for members in kept:
        rows: list[_Row] = []
        for x, v in members:
            element = bob[(v, s)]
            alice_form, bob_form = alice[(x, t)].form, element.form
            if alice_form is None:
                continue
            assert bob_form is not None, "the rank rule holds every kept element"
            assert not isinstance(alice_form[0], Ball), "Alice's factors are exact"
            rows.append(
                _Row(
                    alice_form[0],
                    bob_form[0],
                    alice_form[1].kron(bob_form[1]),
                    cast(int, d.raw_key(x, v)),
                    element.split,
                )
            )
        try:
            factorised = _class(rows)
        except NotCertified as failure:
            raise _Fail(SUPPORT_NOT_ESTABLISHED, f"{where}: {failure}") from failure
        if factorised is not None:
            built.append(factorised)
    return built


def _ratio_bits(u: Any, v: Any) -> Any:
    """Return ``(u/v) log2 e``, the magnitude of ``foundations/lem:kernel``'s ``dv``."""
    return (u / v) / balls.real(2).log()


def _du(u: Any, v: Any) -> Any:
    """Return ``log2(u/v) + log2 e``, ``foundations/lem:kernel``'s ``du``, enclosed."""
    two = balls.real(2).log()
    return (u / v).log() / two + 1 / two


def _choi(model: _Model, pair: JointSector, block: Ball) -> Ball:
    """Return ``(R (x) 1) X (R (x) 1)`` on a POVM-form sector, ``X`` elsewhere."""
    scale = model.scale[pair[0]]
    width = model.maps.declaration.sector_dim(pair[1])
    return (
        block
        if scale is None
        else block.congruence([x for x in scale for _ in range(width)])
    )


def certified_bracket(
    model: _Model,
    alpha: Any,
    point: Mapping[JointSector, Any],
    q_iterate: AcceptanceIterate,
    solves: Mapping[str, GroupSolve] | None,
    acceptance: AcceptanceOracle,
    *,
    index: int,
    iteration: int,
) -> CertifiedPoint:
    """Return the bracket ``b^A + b^F`` at one point (``lem:certified-bracket``).

    ``req:certified-evaluation`` (i), (iii), (v): ``q_t`` exact on the island;
    every Choi block's exact Hermitian part certified positive definite; ``P``,
    the deficits and ``K`` enclosed; (H-POS) with certified signs on the whole
    acceptance support; the gradient of ``cor:full-gradient`` enclosed; then
    ``b^A`` (part (ii)) and ``b^F`` (part (iii)), whose sum is the bracket by
    part (i). A :class:`_Fail` drops the point.
    """
    maps, d = model.maps, model.maps.declaration
    alpha_minus_one = alpha - 1
    if not q_iterate.on_island:
        raise _Fail(ACCEPTANCE_ITERATE_NOT_EXACT, "q_t not formed on the exact island")
    if q_iterate.exact is not None:
        q = dict(q_iterate.exact)
    elif d.acceptance_set.geometry == SINGLETON:
        # Only a singleton's iterate has no exact view on the island: it never
        # moves, and its binary64 view is the declared exact point. Any other
        # geometry fails closed here.
        q = {chat: Fraction(value) for chat, value in q_iterate.view.items()}
    else:
        raise _Fail(
            ACCEPTANCE_ITERATE_NOT_EXACT,
            f"q_t has no exact view on the {d.acceptance_set.geometry} geometry",
        )
    choi: dict[JointSector, Ball] = {}
    for pair in maps.joint_sectors:
        array = np.asarray(point[pair], np.complex128)
        exact = DyadicMatrix.from_array(array).hermitian_part()
        if not least_eigenvalue_bound(exact) > 0:
            raise _Fail(BLOCK_NOT_POSITIVE_DEFINITE, f"the Choi block {pair}")
        choi[pair] = _choi(model, pair, Ball.from_dyadic(exact))
    statistics = {
        chat: sum(
            (
                g.pairing_re(choi[pair])
                for pair in maps.joint_sectors
                if (g := model.gamma.get((chat, pair))) is not None
            ),
            balls.real(0),
        )
        for chat in model.support
    }
    k_value, pieces = dict(statistics), {}
    for chat in model.live:
        for pair in model.evaluated[chat]:
            deficit, pieces[(chat, pair)] = _deficit(
                model.classes[(chat, pair)], choi[pair], alpha, (chat, pair)
            )
            k_value[chat] = k_value[chat] + deficit
    g_q, weight, coefficient = {}, {}, {}
    for chat in model.support:
        u = balls.real(q[chat])
        if not (
            q[chat] > 0
            and statistics[chat] > 0
            and (chat not in model.live or k_value[chat] > 0)
        ):
            raise _Fail(POSITIVITY_NOT_CERTIFIED, f"(H-POS) at {chat}")
        if chat in model.live:
            coefficient[chat] = -_ratio_bits(u, k_value[chat]) / alpha_minus_one
            g_q[chat] = (
                _du(u, statistics[chat]) + _du(u, k_value[chat]) / alpha_minus_one
            )
            weight[chat] = -_ratio_bits(u, statistics[chat]) + coefficient[chat]
        else:
            g_q[chat] = alpha / alpha_minus_one * _du(u, statistics[chat])
            weight[chat] = -alpha / alpha_minus_one * _ratio_bits(u, statistics[chat])
    blocks: dict[JointSector, Ball] = {}
    for pair in maps.joint_sectors:
        total = Ball.zeros(choi[pair].shape[0])
        for chat in model.support:
            if (chat, pair) in model.gamma:
                total = total + model.gamma[(chat, pair)].scale(weight[chat])
            if (chat, pair) in pieces:
                total = total + pieces[(chat, pair)].scale(coefficient[chat])
        blocks[pair] = _choi(model, pair, total).hermitian_part()
    b_f, _ = feasible_side_over_enclosure(
        maps.parametrization,
        blocks,
        model.frames,
        solves or {},
        lift=Ball.from_dyadic,
        floor=balls.least_eigenvalue,
    )
    radius = max(
        [float(x.rad()) for x in g_q.values()]
        + [block.radius() for block in blocks.values()]
    )
    return CertifiedPoint(
        index,
        iteration,
        True,
        _acceptance_side(d, acceptance, g_q),
        b_f,
        gradient_radius=radius,
        gradient_q=g_q,
        gradient_blocks=blocks,
    )


def _deficit(
    classes: list[_Class], choi: Ball, alpha: Any, where: Any
) -> tuple[Any, Ball]:
    """Return ``f`` and its pulled-back gradient at a kept key-active pair (iii).

    Per class: ``N = R_G C J'' C^dagger R_G^dagger``, ``Psi_j = R_j F_j N^p
    F_j^dagger R_j^dagger``, ``f = sum_j tr Psi_j^alpha - tr N`` and the piece
    ``C^dagger (alpha R_G^dagger D_N[H_Q] R_G - G) C``, ``H_Q = sum_j F_j^dagger
    R_j^dagger Psi_j^(alpha - 1) R_j F_j`` (``lem:kraus-freedom`` (iii), (iv)(c)).
    """
    p, value, gradient = 1 / alpha, balls.real(0), Ball.zeros(choi.shape[0])
    for klass in classes:
        compressed = klass.root @ klass.c @ choi @ klass.c.adjoint @ klass.root.adjoint
        try:
            spectrum = balls.spectral(compressed)
            root_power = balls.power(spectrum, p, f"N at {where}")
            h_q = Ball.zeros(compressed.shape[0])
            for f_j, r_j in klass.labels:
                psi = r_j @ f_j @ root_power @ f_j.adjoint @ r_j.adjoint
                pinched = balls.spectral(psi)
                phi = balls.power(pinched, alpha - 1, f"Psi_j at {where}")
                value += balls.trace_power(pinched, alpha, f"Psi_j at {where}")
                h_q = h_q + f_j.adjoint @ (r_j.adjoint @ phi @ r_j) @ f_j
            derivative = balls.deriv_power(spectrum, p, h_q, f"N at {where}")
        except NotCertified as failure:
            raise _Fail(FLOOR_NOT_CERTIFIED, str(failure)) from failure
        inner = (klass.root.adjoint @ derivative @ klass.root).scale(alpha) - klass.gram
        gradient = gradient + klass.c.adjoint @ inner @ klass.c
        value -= compressed.trace_re()
    return value, gradient


def _acceptance_side(
    d: Any, acceptance: AcceptanceOracle, g_q: Mapping[str, Any]
) -> Fraction:
    """Return ``b^A``: the exact minimum at the centre ``g^`` less ``delta`` ((v)(d)).

    ``lem:certified-bracket`` (ii): ``delta >= |g_q - g^|`` on the support; the
    minimum is the declared point of a singleton or the exact vertex an exact
    polytope oracle returns; any other geometry is not certified.
    """
    centre = {c: float(g_q[c].mid()) if c in g_q else 0.0 for c in d.acceptance_values}
    delta = max(
        (balls.upper(abs(ball - balls.real(centre[c]))) for c, ball in g_q.items()),
        default=Fraction(0),
    )
    if d.acceptance_set.geometry == SINGLETON:
        frequencies = map(Fraction, d.acceptance_set.frequencies)
        vertex = dict(zip(d.acceptance_values, frequencies, strict=True))
    elif isinstance(acceptance, ExactAcceptanceOracle):
        vertex = dict(acceptance.exact_minimize(centre))
    else:
        raise _Fail(ACCEPTANCE_GEOMETRY_NOT_CERTIFIED, d.acceptance_set.geometry)
    return (
        sum((Fraction(centre[c]) * vertex[c] for c in d.acceptance_values), Fraction(0))
        - delta
    )


def evaluate(
    maps: JointMaps,
    points: Sequence[CandidatePoint],
    acceptance: AcceptanceOracle,
    alpha: float,
    *,
    option: str = "on",
    companion: Any = None,
    dropped: DroppedSet = frozenset(),
    withheld: Sequence[str] = (),
    precision: int = WORKING_PRECISION,
) -> CertifiedEvaluation:
    """Form the run's certified number: ``req:certified-evaluation`` (i)-(vii).

    ``maps`` are those of the declaration the first-order number is formed on
    (a companion's built from its slots, ``companion`` its compilation), the
    points those item (i) selects, at most five, each with its solve: on a
    companion the five best contributing points of the search and the polish
    together, otherwise the best four of the search and its last.
    ``withheld`` holds item
    (vii)'s reasons the run tier found upstream of the declaration. The
    certified number is the largest certified bracket (``eq:hcert``); no point
    certified, or no arithmetic, leaves the run's numbers as they are.
    """
    if option == "off":
        return EVALUATION_OFF
    library = balls.arithmetic_library()
    if library is None:
        return CertifiedEvaluation(
            option, NOT_CERTIFIED, None, reasons=(NOT_CERTIFIED, CERTIFIER_UNAVAILABLE)
        )
    started, results = time.perf_counter(), []
    with balls.precision(precision):
        model = _model(maps, companion, frozenset(dropped))
        order = balls.real(Fraction(alpha))
        for index, (point, q_iterate, solves, iteration) in enumerate(points):
            try:
                if model.failure is not None:
                    raise model.failure
                results.append(
                    certified_bracket(
                        model,
                        order,
                        point,
                        q_iterate,
                        solves,
                        acceptance,
                        index=index,
                        iteration=iteration,
                    )
                )
            except _Fail as failure:
                results.append(
                    CertifiedPoint(
                        index,
                        iteration,
                        False,
                        reasons=(failure.reason,),
                        detail=(str(failure),),
                    )
                )
    brackets = [b for point in results if (b := point.bracket) is not None]
    best = max(brackets, default=None)
    status, reasons = (
        (NOT_CERTIFIED, (NOT_CERTIFIED,))
        if best is None
        else ("withheld", tuple(withheld))
        if withheld
        else ("certified", ())
    )
    return CertifiedEvaluation(
        option,
        status,
        best,
        tuple(results),
        reasons,
        library,
        precision,
        time.perf_counter() - started,
    )
