"""PC2 (iv) -- the declared statistics functional on a candidate declaration.

protocol-compiler 0.3.0 Definition ``def:phi``, Eq. ``eq:jointdist``:

    ``P_D[omega](x, v) = tr[(M_x (x) F_v) omega]``,
    ``Phi[omega](chat) = sum over the fibre phi(a(x, v)) = chat of P_D``.

Theorem ``thm:measurements-and-statistics`` (iv): for every ``omega`` in ``S_=(A Q)``,
``P_D[omega]`` is a probability distribution on ``X x V`` and ``Phi[omega]`` one on
``Chat``; both are AFFINE in ``omega``, and ``Phi`` depends on ``omega`` only through
``P_D``. All three facts are properties of these two functions and are what the
property suite quantifies over.

STATED ON A CANDIDATE, WITH THE SUBSYSTEM ORDER FIXED
=====================================================
Nothing here needs the declaration to have been emitted by Definition
``def:compile``: ``P_D`` is a function of the declared operators and the state.
the ``subsystem_order`` convention fixes that states live on ``A Q`` with ``A``
first and operator pairs are written ``M_x (x) F_v`` with the ``A``-factor
first, so the composite index of ``(i, q)`` is ``i * d_Q + q``. Reversing it
would produce a different -- and silently plausible -- table at every
non-product state.

AND EVALUATED PER SECTOR BLOCK, BECAUSE ``operator_form`` IS BINDING
====================================================================
the ``operator_form`` convention: "no ``d_Q x d_Q`` or
``d_A d_Q x d_A d_Q`` array is formed on any path this contract describes".
``M_x (x) F_v`` is block diagonal in the ``A Q_s`` decomposition, so the trace
splits as ``sum_s tr[(M_x (x) F_v^(s)) omega^(s)]`` -- an identity and not an
approximation, argued at :func:`joint_distribution` -- and the largest array
this module forms is ``d_A d_s x d_A d_s``. It is the same shape
Eq. ``eq:feas-modes`` and :mod:`certiqs_key.protocol_compiler.feasibility` already use.

TOTALITY OF ``phi`` IS LOAD-BEARING AND IS CHECKED, NOT ASSUMED
===============================================================
Remark ``rem:phitotal``: if ``phi`` were partial the fibres would not partition
``X x V`` and ``Phi[omega]`` would be subnormalized -- "a defect that looks
like a lost probability and reads downstream as an acceptance statistic that
does not sum to one". Totality is check V1's, and :func:`phi_distribution`
refuses to compute on a partial table rather than completing it with a default
value: the ``fail_closed`` convention forbids substituting one, and a catch-all
acceptance value is a DECLARED value when the specification declares it (as
the BB84 instance's last case does) and an INVENTED one when the
compiler supplies it.

WHERE THE COMPLEX NUMBERS GO
============================
Every entry of ``P_D`` is real because ``M_x``, ``F_v`` and ``omega`` are
positive semidefinite, and in this module's exact substrate that is a DECIDED
fact: :func:`certiqs_key.foundations.exact.real_part` raises if an imaginary part
survives instead of discarding it. There is therefore no narrowing conversion
anywhere on this path -- no place where a complex value becomes a real one by
losing information -- and nothing for the repository-wide ``filterwarnings =
error`` to catch.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from certiqs_key.domain.families import AliceForm
from certiqs_key.foundations.blocks import JointBlockOperator, Label
from certiqs_key.foundations.errors import HypothesisError
from certiqs_key.foundations.exact import (
    Cx,
    Matrix,
    dimension,
    kron,
    matmul,
    real_part,
    trace,
)
from certiqs_key.protocol_compiler.declaration import CandidateDeclaration
from certiqs_key.protocol_compiler.spec import AnnouncementClass

__all__ = [
    "AcceptanceStatistics",
    "acceptance_fibres",
    "announcement_class_mass",
    "joint_distribution",
    "phi_distribution",
]


def joint_distribution(
    declaration: CandidateDeclaration,
    state: Matrix | JointBlockOperator,
) -> dict[tuple[Label, Label], Fraction]:
    """Return ``P_D[omega]`` of Eq. ``eq:jointdist``, cell by cell and exactly.

    The state lives on ``A Q`` with ``A`` first; a state of the wrong dimension
    is a hypothesis violation rather than a refusal, because Definition
    ``def:phi`` is stated for ``omega in Pos(A Q)`` and no check of Definition
    ``def:validator`` is about the caller's state.

    COMPUTED PER SECTOR BLOCK, AND NO ``d_A d_Q x d_A d_Q`` ARRAY IS FORMED.
    the ``operator_form`` convention is binding: "no ``d_Q x d_Q`` or
    ``d_A d_Q x d_A d_Q`` array is formed on any path this contract describes".
    Until the Stage 2 fix band this function built
    ``kron(M_x, F_v.dense())`` -- a full ``d_A d_Q`` array, on the run tier,
    called by both instances' honest providers -- which was finding F-S2-pc-07
    (a).

    THE DECOMPOSITION, AND WHY IT IS EXACT RATHER THAN AN APPROXIMATION.
    ``F_v`` is a block list, ``F_v = bigoplus_s F_v^(s)``, so with the
    ``A``-first factor order ``M_x (x) F_v`` is block diagonal in the
    ``A Q_s`` decomposition, with blocks ``M_x (x) F_v^(s)``. A trace against a
    block-diagonal operator reads only the matching diagonal blocks of the
    other factor, so

        ``P_D[omega](x, v) = sum_s tr[(M_x (x) F_v^(s)) omega^(s)]``

    for EVERY ``omega``, block diagonal or not: the off-sector blocks of
    ``omega`` meet zero blocks of ``M_x (x) F_v`` and contribute nothing. This
    is the same rearrangement Eq. ``eq:feas-modes`` writes for the constraint
    values and that :func:`certiqs_key.protocol_compiler.feasibility.constraint_value`
    already computes -- "a matrix of size ``d_A`` assembled from ``|S|`` block
    terms". The largest array formed here is ``d_A d_s x d_A d_s``.

    TWO PRESENTATIONS OF THE STATE ARE ACCEPTED, AND THIS MODULE FORMS NEITHER.
    A :class:`~certiqs_key.foundations.blocks.JointBlockOperator` is the conforming
    one and is the type Definition ``def:feasible`` gives ``omega``; its blocks
    are used directly. A full-space :class:`~certiqs_key.foundations.exact.Matrix` is
    accepted for a caller stating a proposition ABOUT a state -- both instances'
    honest providers hand one -- and its diagonal ``A Q_s`` sub-blocks are READ
    OFF an array the CALLER built.
    """
    if declaration.is_general_format:
        return _joint_distribution_general(declaration, state)

    expected = declaration.alice_dim * declaration.q_dim
    blocks = _state_blocks(declaration, state, expected)
    table: dict[tuple[Label, Label], Fraction] = {}
    for x in declaration.alice_alphabet:
        element = declaration.alice_povm[x]
        for v in declaration.bob_alphabet:
            family_member = declaration.bob_povm[v]
            total = Cx(Fraction(0), Fraction(0))
            for position, block in enumerate(blocks):
                joint = kron(element, family_member.blocks[position])
                total = total + trace(matmul(joint, block))
            table[(x, v)] = real_part(
                total, f"the joint probability P_D[omega]({x!r}, {v!r})"
            )
    return table


def _joint_distribution_general(
    declaration: CandidateDeclaration,
    state: Matrix | JointBlockOperator,
) -> dict[tuple[Label, Label], Fraction]:
    """Return the general-format joint table, one joint-sector block at a time.

    The measured operator is supplied by the factorised family's product rule;
    only its block at the current product sector is formed.  Alice's operator is
    read from her declared block list at the current Alice sector.  Thus the
    largest array formed remains one ``A_t Q_s`` block.

    Ensemble form does not declare ``M_x``.  It declares ``N_x`` and defines a
    generally irrational POVM that this package deliberately never forms, so
    this exact statistics functional has no operator it can evaluate there.
    """
    if declaration.alice_form is AliceForm.ENSEMBLE:
        raise HypothesisError(
            "Definition def:phi reads the declared POVM M_x; an ensemble-form "
            "declaration carries N_x and the POVM it denotes is generally "
            "irrational and formed by no one"
        )
    family = declaration.bob_factors
    if family is None:  # pragma: no cover - general-format construction invariant
        raise HypothesisError(
            "a general-format statistics functional requires the declared "
            "factorised measured family"
        )
    blocks = _general_state_blocks(declaration, state)
    q_sector_count = declaration.sectors.count
    table: dict[tuple[Label, Label], Fraction] = {}
    for x in declaration.alice_alphabet:
        alice = declaration.alice_operator(x)
        for outcome, v in enumerate(declaration.bob_alphabet):
            total = Cx(Fraction(0), Fraction(0))
            for alice_sector, alice_block in enumerate(alice.blocks):
                for q_sector in range(q_sector_count):
                    measured = family.product_block(outcome, q_sector)
                    joint = kron(alice_block, measured)
                    block = blocks[alice_sector * q_sector_count + q_sector]
                    total = total + trace(matmul(joint, block))
            table[(x, v)] = real_part(
                total, f"the joint probability P_D[omega]({x!r}, {v!r})"
            )
    return table


def _general_state_blocks(
    declaration: CandidateDeclaration,
    state: Matrix | JointBlockOperator,
) -> tuple[Matrix, ...]:
    """Read ``omega`` as blocks on ``A_t Q_s`` in the declared joint order."""
    if isinstance(state, JointBlockOperator):
        if (
            state.alice_sectors.disagreement(declaration.alice_sectors) is not None
            or state.sector_map.disagreement(declaration.sectors) is not None
        ):
            raise HypothesisError(
                "Definition def:phi is read against the declaration's own "
                "Alice and measured sector maps; the supplied block list "
                "carries a different one"
            )
        return state.blocks
    expected = declaration.alice_dim * declaration.q_dim
    if dimension(state) != expected:
        raise HypothesisError(
            f"Definition def:phi is stated on Lin(A Q) of dimension {expected}; "
            f"a {dimension(state)}-dimensional operator was supplied"
        )
    # A DENSE PRESENTATION IS READ IN THE A-FIRST LAYOUT, which is the one
    # JointBlockOperator.dense() writes and the `subsystem_order` convention
    # fixes: the composite index of (a, s, l), with a in the Alice sector t
    # starting at alice_start_t and l in the Q sector s starting at start_s, is
    # (alice_start_t + a) * d_Q + start_s + l. The block at joint position
    # (t, s) -- t slowest, the flattened product order -- is read off those
    # rows and columns, which generalises :func:`_state_blocks` from one Alice
    # sector to the Alice sectors of the general format.
    #
    # THE DENSE ARRAY IS NOT THE CONTIGUOUS direct sum of the joint
    # blocks (dense()'s layout is that only at d_A = 1); reading it so at
    # d_A = 2 would give a different Phi, both readings summing to one, so
    # nothing would refuse. The off-sector blocks are not read, for the reason
    # _state_blocks gives: they meet zero blocks of every M_x (x) F_v.
    alice_dims = declaration.alice_sectors.dims
    q_dims = declaration.sectors.dims
    q_total = declaration.q_dim
    if sum(alice_dims) * q_total != expected:  # pragma: no cover - invariant
        raise HypothesisError(
            "the Alice sector map does not partition d_A; Definition def:phi "
            "reads omega against the declaration's own maps"
        )
    blocks: list[Matrix] = []
    alice_start = 0
    for alice_dim in alice_dims:
        start = 0
        for dim in q_dims:
            blocks.append(
                tuple(
                    tuple(
                        state[(alice_start + a1) * q_total + start + s1][
                            (alice_start + a2) * q_total + start + s2
                        ]
                        for a2 in range(alice_dim)
                        for s2 in range(dim)
                    )
                    for a1 in range(alice_dim)
                    for s1 in range(dim)
                )
            )
            start += dim
        alice_start += alice_dim
    return tuple(blocks)


def _state_blocks(
    declaration: CandidateDeclaration,
    state: Matrix | JointBlockOperator,
    expected: int,
) -> tuple[Matrix, ...]:
    """Return ``omega``'s diagonal ``A Q_s`` blocks, in the declared order.

    For a :class:`~certiqs_key.foundations.blocks.JointBlockOperator` this is the
    list it already is. For a full-space array it is a READ of the caller's
    array along the ``A``-first index layout -- the composite index of
    ``(a, s, l)`` being ``a * d_Q + start_s + l``, which is the layout
    :meth:`certiqs_key.foundations.blocks.JointBlockOperator.dense` writes and which
    the ``subsystem_order`` convention fixes. The off-sector blocks are not read,
    because they contribute nothing to any trace this module takes.
    """
    if isinstance(state, JointBlockOperator):
        if (
            state.alice_dim != declaration.alice_dim
            or state.sector_map.dims != declaration.sectors.dims
        ):
            raise HypothesisError(
                "Definition def:phi is read against the declaration's own "
                "sector map and its own d_A; the supplied block list carries "
                "a different one"
            )
        return state.blocks
    if dimension(state) != expected:
        raise HypothesisError(
            f"Definition def:phi is stated on Pos(A Q) of dimension {expected}; "
            f"a {dimension(state)}-dimensional operator was supplied"
        )
    alice_dim = declaration.alice_dim
    q_dim = declaration.q_dim
    blocks: list[Matrix] = []
    start = 0
    for dim in declaration.sectors.dims:
        blocks.append(
            tuple(
                tuple(
                    state[a1 * q_dim + start + s1][a2 * q_dim + start + s2]
                    for a2 in range(alice_dim)
                    for s2 in range(dim)
                )
                for a1 in range(alice_dim)
                for s1 in range(dim)
            )
        )
        start += dim
    return tuple(blocks)


def acceptance_fibres(
    declaration: CandidateDeclaration,
) -> dict[Label, tuple[tuple[Label, Label], ...]]:
    """Return the fibres of ``phi o a`` over ``Chat``, in the declared order.

    The fibres PARTITION ``X x V`` exactly when ``phi o a`` is total, which is
    Remark ``rem:phitotal`` and check V1. A pair whose announcement class is
    not tabulated raises rather than being dropped into a residual fibre.
    """
    fibres: dict[Label, list[tuple[Label, Label]]] = {
        value: [] for value in declaration.acceptance_alphabet
    }
    for x, v in declaration.outcome_pairs():
        kappa = declaration.announcement(x, v)
        if kappa not in declaration.tabulated_classes():
            raise HypothesisError(
                f"phi is not tabulated on the announcement class {kappa}; check "
                "V1 refuses such a declaration (Remark rem:phitotal) and no "
                "default acceptance value is substituted for it"
            )
        value = declaration.acceptance_value(kappa)
        if value not in fibres:
            raise HypothesisError(
                f"phi maps into {value!r}, which is not in the declared "
                "acceptance alphabet Chat"
            )
        fibres[value].append((x, v))
    return {value: tuple(pairs) for value, pairs in fibres.items()}


@dataclass(frozen=True)
class AcceptanceStatistics:
    """``Phi[omega]`` with the fibres it was summed over."""

    values: dict[Label, Fraction]
    fibres: dict[Label, tuple[tuple[Label, Label], ...]]

    @property
    def total(self) -> Fraction:
        """Return the total mass, which Theorem ``thm:measurements-and-statistics`` (iv) makes one."""  # noqa: E501
        return sum(self.values.values(), Fraction(0))


def phi_distribution(
    declaration: CandidateDeclaration,
    state: Matrix | JointBlockOperator,
) -> AcceptanceStatistics:
    """Return ``Phi[omega]`` of Eq. ``eq:jointdist``, with its fibres.

    ``Phi`` depends on ``omega`` only through ``P_D`` -- it is a fibre sum of
    the joint table and nothing else -- which is the last clause of Theorem
    ``thm:measurements-and-statistics`` (iv) and is why the two are computed in this
    order rather than independently.
    """
    joint = joint_distribution(declaration, state)
    fibres = acceptance_fibres(declaration)
    values = {
        value: sum((joint[pair] for pair in pairs), Fraction(0))
        for value, pairs in fibres.items()
    }
    return AcceptanceStatistics(values=values, fibres=fibres)


def announcement_class_mass(
    declaration: CandidateDeclaration,
    state: Matrix | JointBlockOperator,
    kappa: AnnouncementClass,
) -> Fraction:
    """Return the mass of one announcement class under ``P_D[omega]``.

    Not a slot of the declaration and not an emitted quantity: it is the
    per-class sum a derivation needs where it must reason about a class rather
    than an acceptance value -- notably the mass Remark ``rem:phitotal`` says a
    partial ``phi`` would lose.
    """
    joint = joint_distribution(declaration, state)
    return sum(
        (
            joint[(x, v)]
            for x, v in declaration.outcome_pairs()
            if declaration.announcement(x, v) == kappa
        ),
        Fraction(0),
    )
