"""The active set of the pairwise step rule: the iterate as a convex combination.

(Which step the rule takes at an iterate -- the better of the pairwise step
and the plain one -- is ``joint_driver._pairwise_iteration``'s; this module
holds the atoms.)

Pairwise Frank-Wolfe keeps the iterate ``x = sum_i w_i a_i`` as an explicit
convex combination of ATOMS, each a point ``a_i = (q_i, A_i)`` of
``acSet x Feas^J``: the start ``(q_0, J_start)`` and the (shrunk) oracle
returns. A step moves weight ``s`` from the AWAY atom -- the active atom at
which the linear form ``<grad, .>`` is largest -- to the new oracle atom, so
the direction is ``a_new - a_away`` and the largest step is ``w_away``. The
feasibility of every iterate is then a convex combination of feasible points
and needs no projection.

WHAT THE ATOMS ARE, AND WHAT THEY ARE NOT
=========================================
An oracle atom is the exact return SHRUNK toward the interior point,
``(1 - delta) S + delta J_0`` and ``(1 - delta) v + delta q_0`` with
``delta = PAIRWISE_SHRINK`` (:mod:`~certiqs_key.solvers.frank_wolfe.joint_options`).
It is a feasible point, being a convex combination of two, and it is used to
MOVE. It is never the pair a bracket consumes: ``<G, S_shrunk>`` is at least
the minimum, which is the unsafe side of ``eq:lmo``, and the driver passes the
exact return to the gate (``joint_driver.run_joint_frank_wolfe``).

WHY PRODUCT ATOMS, i.e. HOW ``q`` MOVES. The ``q`` half of each atom moves with
its ``J`` half: the pairwise direction on the acceptance side is ``v_new -
v_away``. This is pairwise Frank-Wolfe on the product ``acSet x Feas^J`` with
one step size, which is what was measured. A vanilla ``q`` step beside a
pairwise ``J`` step would tie ``q``'s step to ``w_away`` as well and was not
measured. ``q`` stays positive on ``Chat_acc`` for the same reason ``J`` stays
positive definite: every atom carries ``delta`` of ``q_0``. A coordinate on
which every atom agrees is carried EXACTLY, never re-formed (the reason
``driver._combine_q`` short-circuits), so a singleton acceptance set is not
perturbed by an ulp.

ON A CANONICAL BOX THE ATOMS ARE J-ONLY. There ``q`` is not
stepped at all: the loop's ``q`` rule
(:mod:`~certiqs_key.solvers.frank_wolfe.q_rule`) sets it to
``argmin_q f(J, q)`` at every point evaluated, so pairwise Frank-Wolfe runs on
``g(J) = f(J, q*(J))`` over ``Feas^J`` alone. The driver then builds the layout
with NO acceptance values: every atom's ``q`` half is empty, the away score is
``<grad_J, A_i>`` (the gradient of ``g`` at the iterate, ``q_t`` being the
partial minimiser), no exact ``q`` side is carried here, and the accepted
iterate's ``q`` is re-solved at the rebuilt ``J``. What follows about the
exact ``q`` side applies to the geometries still on the vertex step.

ROUNDING, AND WHY THE ITERATE IS ALWAYS REBUILT. The iterate a step proposes
is REBUILT from the proposed weights and atoms, ``sum_i w_i a_i``, rather than
updated incrementally, so it never drifts from what the atoms say; the driver
then re-checks it (PSD, coupling, rows) and re-evaluates its objective directly
before accepting it. Weights below ``PAIRWISE_FOLD_BELOW`` are FOLDED into the
heaviest atom -- the two replaced by their weighted mean with the summed
weight, a feasible point representing the same part of the iterate. That fold
is in practice the only way an atom leaves: the golden-section search never
returns the endpoint ``w_away`` itself, so a pairwise step does not zero the
away atom; an atom of weight exactly zero would contribute nothing and is
removed for exactness.

ON A MOVING ACCEPTANCE GEOMETRY THE q SIDE IS EXACT. Remark
``rem:acc-side`` (beta) asks ``q_t`` to be a convex combination, with EXACT
rational weights, of exact points of the set, and a binary64 rebuild
``sum_i w_i q_i`` is neither. So when the driver hands over an exact start, the
set also carries each atom's ``q`` half and every weight as
:class:`~fractions.Fraction` s: the start ``q_0`` and each shrunk vertex
``(1 - delta) v + delta q_0`` are exact points of the set (``delta`` and every
step being binary64, hence exact dyadic rationals), the weights stay
non-negative and sum to one exactly -- a pairwise step moves ``min(s, w_away)``
exactly, a plain step scales by ``1 - s`` -- and a fold merges the ``q`` halves
with exact shares. Then :meth:`ActiveSet.exact_point` is in the set by
construction. The binary64 weights are the roundings of the exact ones, and
the ``J`` side is formed with them as before: that side is checked, not
constructed. Without an exact start (a singleton) nothing below changes.

THE EXACT NUMBERS ARE KEPT SHORT (:meth:`ActiveSet.bounded`). Every step
multiplies a dyadic denominator into the weights, and a fold into the folded
``q`` half. Weights are shortened with NO predicate: the exact values of their
binary64 roundings, the residual put on the largest, are again non-negative and
sum to one, so the rebuilt point is again a convex combination of the same
points of the set. A long ``q`` half (a folded atom) is replaced by a short
exact member next to it, admitted by the oracle's exact membership predicate
(:class:`~certiqs_key.solvers.frank_wolfe.acceptance_iterate.Shortener`), or
kept if none is. Past ``EXACT_BITS_CAP`` the exact side is given up, and the
driver records the iterate off the island (fail-closed).
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction

import numpy as np
import numpy.typing as npt

from certiqs_key.meat_core.objective.joint import JointSector
from certiqs_key.meat_core.objective.linalg import Matrix, as_matrix, hermitian_part
from certiqs_key.solvers.frank_wolfe.acceptance_iterate import (
    EXACT_BITS_CAP,
    SHORTEN_ABOVE_BITS,
    exact_bits,
    short_convex_weights,
)
from certiqs_key.solvers.frank_wolfe.joint_options import (
    PAIRWISE_FOLD_BELOW,
    PAIRWISE_SHRINK,
)

ComplexArray = npt.NDArray[np.complex128]
FloatArray = npt.NDArray[np.float64]


@dataclass(frozen=True)
class FlatLayout:
    """How a point's blocks and frequencies lie in one flat vector."""

    pairs: tuple[JointSector, ...]
    dims: tuple[int, ...]
    offsets: tuple[int, ...]
    values: tuple[str, ...]

    @classmethod
    def of(
        cls,
        pairs: Sequence[JointSector],
        dims: Sequence[int],
        values: Sequence[str],
    ) -> FlatLayout:
        """Return the layout of these joint sectors and acceptance values."""
        offsets = [0]
        for dim in dims:
            offsets.append(offsets[-1] + dim * dim)
        return cls(tuple(pairs), tuple(dims), tuple(offsets), tuple(values))

    @property
    def width(self) -> int:
        """Return the length of the flat ``J`` vector."""
        return self.offsets[-1]

    def flatten(self, blocks: Mapping[JointSector, Matrix]) -> ComplexArray:
        """Return the blocks as one complex vector, in the layout's order."""
        return np.concatenate(
            [as_matrix(blocks[pair]).ravel() for pair in self.pairs]
        ).astype(np.complex128, copy=False)

    def unflatten(self, vector: ComplexArray) -> dict[JointSector, Matrix]:
        """Return the Hermitian blocks a flat vector describes."""
        return {
            pair: hermitian_part(
                np.asarray(
                    vector[self.offsets[k] : self.offsets[k + 1]].reshape(dim, dim),
                    dtype=np.complex128,
                )
            )
            for k, (pair, dim) in enumerate(zip(self.pairs, self.dims, strict=True))
        }

    def frequencies(self, q: Mapping[str, float]) -> FloatArray:
        """Return ``q`` as a vector in the layout's order."""
        return np.asarray([float(q[value]) for value in self.values], dtype=np.float64)


def shrink_blocks(
    layout: FlatLayout, vertex: Mapping[JointSector, Matrix], anchor: ComplexArray
) -> ComplexArray:
    """Return ``(1 - delta) S + delta J_0`` as a flat vector."""
    return (1.0 - PAIRWISE_SHRINK) * layout.flatten(vertex) + PAIRWISE_SHRINK * anchor


def shrink_frequencies(vertex: FloatArray, anchor: FloatArray) -> FloatArray:
    """Return ``(1 - delta) v + delta q_0``, carrying equal coordinates exactly."""
    mixed = (1.0 - PAIRWISE_SHRINK) * vertex + PAIRWISE_SHRINK * anchor
    return np.where(vertex == anchor, vertex, mixed)


def shrink_frequencies_exact(
    vertex: Sequence[Fraction], anchor: Sequence[Fraction]
) -> tuple[Fraction, ...]:
    """Return ``(1 - delta) v + delta q_0`` over the rationals.

    A convex combination, with the exact dyadic weight ``delta``, of two exact
    points of the acceptance set, hence one itself (Remark ``rem:acc-side``
    (beta)). A coordinate on which the two agree is that coordinate.
    """
    delta = Fraction(PAIRWISE_SHRINK)
    return tuple(
        v if v == a else v + delta * (a - v)
        for v, a in zip(vertex, anchor, strict=True)
    )


@dataclass(frozen=True)
class ActiveSet:
    """Atoms and their weights. Immutable: a step returns a new set."""

    blocks: ComplexArray
    frequencies: FloatArray
    weights: FloatArray
    #: The atoms' ``q`` halves and the weights, EXACT, on a moving geometry;
    #: ``None`` otherwise. When present, ``weights`` are their roundings and
    #: ``frequencies`` the roundings of these (the module docstring).
    exact_frequencies: tuple[tuple[Fraction, ...], ...] | None = None
    exact_weights: tuple[Fraction, ...] | None = None
    #: ``sum_i w_i q_i`` over the rationals, CARRIED rather than re-summed: each
    #: step updates it by the same exact algebra it applies to the weights, so
    #: it equals the sum exactly while costing one update per coordinate
    #: instead of one per atom and coordinate.
    exact_q: tuple[Fraction, ...] | None = None

    @classmethod
    def single(
        cls,
        blocks: ComplexArray,
        frequencies: FloatArray,
        exact: Sequence[Fraction] | None = None,
    ) -> ActiveSet:
        """Return the set holding one atom with weight one: the start.

        ``exact`` is the start's ``q`` as exact rationals, on a moving
        geometry; ``frequencies`` is then its rounding.
        """
        return cls(
            blocks[np.newaxis, :].copy(),
            frequencies[np.newaxis, :].copy(),
            np.ones(1, dtype=np.float64),
            None if exact is None else (tuple(exact),),
            None if exact is None else (Fraction(1),),
            None if exact is None else tuple(exact),
        )

    @property
    def size(self) -> int:
        """Return the number of active atoms."""
        return int(self.weights.shape[0])

    def away_index(self, gradient_blocks: ComplexArray, gradient_q: FloatArray) -> int:
        """Return the atom at which the linear form ``<grad, .>`` is largest.

        ``<G, A> = Re sum_ij conj(G_ij) A_ij`` for Hermitian ``G``; the score
        only CHOOSES the away atom and enters no reported number. Ties go to
        the first atom.
        """
        scores = np.real(self.blocks @ np.conj(gradient_blocks)) + (
            self.frequencies @ gradient_q
        )
        return int(np.argmax(scores))

    def pairwise(
        self,
        away: int,
        blocks: ComplexArray,
        frequencies: FloatArray,
        step: float,
        exact: Sequence[Fraction] | None = None,
    ) -> ActiveSet:
        """Return the set after moving ``step`` from atom ``away`` to a new atom.

        On an exact set the step moved is ``min(step, w_away)`` over the
        rationals: the binary64 cap the search ran under is a rounding of
        ``w_away`` and may exceed it, and a weight must not go negative.
        """
        if self.exact_weights is not None:
            if exact is None or self.exact_frequencies is None:
                raise RuntimeError(_EXACT_ATOM_NEEDED)
            moved = min(Fraction(step), self.exact_weights[away])
            exact_weights = list(self.exact_weights)
            exact_weights[away] = exact_weights[away] - moved
            exact_weights.append(moved)
            # q + s (q_new - q_away), the weights' own update applied to the sum.
            return self._extended(
                blocks,
                frequencies,
                exact,
                exact_weights,
                _moved(self.exact_q, exact, self.exact_frequencies[away], moved),
            )
        weights = self.weights.copy()
        weights[away] = weights[away] - step
        return ActiveSet(
            np.vstack([self.blocks, blocks[np.newaxis, :]]),
            np.vstack([self.frequencies, frequencies[np.newaxis, :]]),
            np.append(weights, step),
        ).tidied()

    def frank_wolfe(
        self,
        blocks: ComplexArray,
        frequencies: FloatArray,
        step: float,
        exact: Sequence[Fraction] | None = None,
    ) -> ActiveSet:
        """Return the set after a plain step ``(1 - step) x + step a_new``."""
        if self.exact_weights is not None:
            if exact is None or self.exact_q is None:
                raise RuntimeError(_EXACT_ATOM_NEEDED)
            moved = Fraction(step)
            exact_weights = [(1 - moved) * weight for weight in self.exact_weights]
            exact_weights.append(moved)
            # (1 - s) q + s q_new = q + s (q_new - q).
            return self._extended(
                blocks,
                frequencies,
                exact,
                exact_weights,
                _moved(self.exact_q, exact, self.exact_q, moved),
            )
        return ActiveSet(
            np.vstack([self.blocks, blocks[np.newaxis, :]]),
            np.vstack([self.frequencies, frequencies[np.newaxis, :]]),
            np.append((1.0 - step) * self.weights, step),
        ).tidied()

    def _extended(
        self,
        blocks: ComplexArray,
        frequencies: FloatArray,
        exact: Sequence[Fraction],
        exact_weights: Sequence[Fraction],
        exact_q: tuple[Fraction, ...],
    ) -> ActiveSet:
        """Return the exact set with one more atom and these exact weights."""
        assert self.exact_frequencies is not None
        return ActiveSet(
            np.vstack([self.blocks, blocks[np.newaxis, :]]),
            np.vstack([self.frequencies, frequencies[np.newaxis, :]]),
            np.asarray([float(weight) for weight in exact_weights], np.float64),
            (*self.exact_frequencies, tuple(exact)),
            tuple(exact_weights),
            exact_q,
        ).tidied()

    def tidied(self) -> ActiveSet:
        """Remove atoms of weight <= 0 and fold those below the threshold.

        An atom of weight exactly zero contributes nothing and is removed. No
        NEGATIVE weight arises: a pairwise step subtracts ``s <= w_away``, and
        the binary64 difference of ``w >= s`` is ``>= 0``; a plain step scales
        by ``1 - s > 0``. Atoms of weight in ``(0, PAIRWISE_FOLD_BELOW)`` are
        FOLDED into the heaviest atom.

        On an exact set every decision is taken on the EXACT weights, the
        folded ``q`` half is the exact weighted mean, and the folded weight the
        exact sum, so the exact iterate is unchanged by a fold.
        """
        if self.exact_weights is not None:
            return self._tidied_exact()
        weights = self.weights
        keep = weights > 0.0
        blocks, frequencies, weights = (
            self.blocks[keep],
            self.frequencies[keep],
            weights[keep],
        )
        tiny = weights < PAIRWISE_FOLD_BELOW
        if not np.any(tiny) or weights.shape[0] < 2:
            return ActiveSet(blocks, frequencies, weights)
        heaviest = int(np.argmax(weights))
        tiny[heaviest] = False
        if not np.any(tiny):
            return ActiveSet(blocks, frequencies, weights)
        group = tiny.copy()
        group[heaviest] = True
        total = float(np.sum(weights[group]))
        share = weights[group] / total
        merged_blocks = share @ blocks[group]
        merged_frequencies = _mean_carrying_equal(frequencies[group], share)
        keep_rest = ~group
        return ActiveSet(
            np.vstack([blocks[keep_rest], merged_blocks[np.newaxis, :]]),
            np.vstack([frequencies[keep_rest], merged_frequencies[np.newaxis, :]]),
            np.append(weights[keep_rest], total),
        )

    def _tidied_exact(self) -> ActiveSet:
        """:meth:`tidied` on an exact set: the same rule, decided exactly."""
        assert self.exact_weights is not None and self.exact_frequencies is not None
        keep = [index for index, w in enumerate(self.exact_weights) if w > 0]
        exact_weights = [self.exact_weights[index] for index in keep]
        exact_frequencies = [self.exact_frequencies[index] for index in keep]
        blocks = self.blocks[keep]
        frequencies = self.frequencies[keep]
        weights = self.weights[keep]
        threshold = Fraction(PAIRWISE_FOLD_BELOW)
        tiny = [weight < threshold for weight in exact_weights]
        unfolded = ActiveSet(
            blocks,
            frequencies,
            weights,
            tuple(exact_frequencies),
            tuple(exact_weights),
            self.exact_q,
        )
        if not any(tiny) or len(exact_weights) < 2:
            return unfolded
        heaviest = max(range(len(exact_weights)), key=lambda i: (exact_weights[i], -i))
        tiny[heaviest] = False
        if not any(tiny):
            return unfolded
        group = [index for index, flag in enumerate(tiny) if flag or index == heaviest]
        rest = [index for index in range(len(exact_weights)) if index not in group]
        total = sum((exact_weights[index] for index in group), Fraction(0))
        merged_exact = tuple(
            sum(
                (
                    exact_weights[index] * exact_frequencies[index][column]
                    for index in group
                ),
                Fraction(0),
            )
            / total
            for column in range(len(exact_frequencies[0]))
        )
        share = weights[group] / float(np.sum(weights[group]))
        merged_blocks = share @ blocks[group]
        merged_frequencies = np.asarray([float(x) for x in merged_exact], np.float64)
        return ActiveSet(
            np.vstack([blocks[rest], merged_blocks[np.newaxis, :]]),
            np.vstack([frequencies[rest], merged_frequencies[np.newaxis, :]]),
            np.asarray(
                [float(exact_weights[index]) for index in rest] + [float(total)],
                np.float64,
            ),
            (*(exact_frequencies[index] for index in rest), merged_exact),
            (*(exact_weights[index] for index in rest), total),
            # A fold replaces a group by its exact mean at its exact total
            # weight, which leaves sum_i w_i q_i unchanged.
            self.exact_q,
        )

    def bounded(
        self,
        shorten: Callable[[Sequence[Fraction]], tuple[Fraction, ...] | None] | None,
    ) -> ActiveSet:
        """Return this set with its exact numbers kept short, or its exact side dropped.

        A ``q`` half longer than a quarter of ``SHORTEN_ABOVE_BITS`` is
        shortened by ``shorten`` where it finds a member, the carried exact
        point moving by the same exact algebra. When the weights or the point
        pass ``SHORTEN_ABOVE_BITS``, the weights are shortened by
        :func:`short_convex_weights` and the exact point is rebuilt as
        ``sum_i w_i q_i`` from them. A set whose exact numbers still
        pass ``EXACT_BITS_CAP`` comes back WITHOUT its exact side, and the
        driver records its iterate off the island.
        """
        if self.exact_weights is None or self.exact_frequencies is None:
            return self
        # The halves are held to a QUARTER of the threshold, because the point
        # sum_i w_i q_i carries the least common multiple of their
        # denominators: halves of a few hundred bits each, all different (a
        # fold's mean has its own), were measured to rebuild a point of over a
        # thousand bits from 118 atoms. A shortened half is the exact value of
        # a binary64 rounding (moved toward q_0 where needed), so the halves
        # share their denominators and the point stays near their size.
        long_atoms = [
            index
            for index, row in enumerate(self.exact_frequencies)
            if exact_bits(row) > SHORTEN_ABOVE_BITS // 4
        ]
        exact_frequencies = list(self.exact_frequencies)
        frequencies = self.frequencies.copy()
        exact_q = self.exact_q
        assert exact_q is not None
        if shorten is not None:
            for index in long_atoms:
                short = shorten(exact_frequencies[index])
                if short is not None:
                    # sum_i w_i q_i moves by w_index (short - old), exactly.
                    exact_q = tuple(
                        value + self.exact_weights[index] * (new - old)
                        for value, new, old in zip(
                            exact_q, short, exact_frequencies[index], strict=True
                        )
                    )
                    exact_frequencies[index] = short
                    frequencies[index] = [float(value) for value in short]
        # THE CAP READS ALL THREE EXACT QUANTITIES: the carried point, the
        # weights and every atom's half. The point carries the least common
        # multiple of the halves' denominators and can outgrow every one of
        # them, so a cap on the rows alone would let it run ~8x past the bound
        # before giving up.
        if (
            exact_bits(exact_q) > EXACT_BITS_CAP
            or exact_bits(self.exact_weights) > EXACT_BITS_CAP
            or any(exact_bits(row) > EXACT_BITS_CAP for row in exact_frequencies)
        ):
            return ActiveSet(self.blocks, self.frequencies, self.weights)
        if (
            exact_bits(self.exact_weights) <= SHORTEN_ABOVE_BITS
            and exact_bits(exact_q) <= SHORTEN_ABOVE_BITS
        ):
            if not long_atoms:
                return self
            return ActiveSet(
                self.blocks,
                frequencies,
                self.weights,
                tuple(exact_frequencies),
                self.exact_weights,
                exact_q,
            )
        exact_weights = short_convex_weights(self.exact_weights)
        columns = len(exact_frequencies[0])
        exact_q = tuple(
            sum(
                (
                    weight * row[column]
                    for weight, row in zip(
                        exact_weights, exact_frequencies, strict=True
                    )
                ),
                Fraction(0),
            )
            for column in range(columns)
        )
        return ActiveSet(
            self.blocks,
            frequencies,
            np.asarray([float(weight) for weight in exact_weights], np.float64),
            tuple(exact_frequencies),
            exact_weights,
            exact_q,
        ).tidied()

    def point(self) -> tuple[ComplexArray, FloatArray]:
        """Return the iterate ``sum_i w_i a_i``, rebuilt from the atoms.

        On an exact set the ``q`` half returned is the rounding of
        :meth:`exact_point`, which is the iterate's ``q``.
        """
        blocks = self.weights @ self.blocks
        exact = self.exact_point()
        if exact is not None:
            frequencies = np.asarray([float(x) for x in exact], np.float64)
        else:
            frequencies = _mean_carrying_equal(self.frequencies, self.weights)
        return np.asarray(blocks, dtype=np.complex128), frequencies

    def exact_point(self) -> tuple[Fraction, ...] | None:
        """Return ``q = sum_i w_i q_i`` over the rationals, or ``None``.

        Remark ``rem:acc-side`` (beta): exact non-negative weights summing to
        one on exact points of the set, so the point is in the set. ``None``
        on a set without exact atoms. Carried by every step (``exact_q``),
        and equal to the sum exactly.
        """
        return self.exact_q


_EXACT_ATOM_NEEDED = "an exact active set takes a new atom only with its exact q half"


def _moved(
    point: tuple[Fraction, ...] | None,
    target: Sequence[Fraction],
    origin: Sequence[Fraction],
    step: Fraction,
) -> tuple[Fraction, ...]:
    """Return ``point + step (target - origin)`` exactly, equal coordinates carried."""
    assert point is not None
    return tuple(
        value if end == start else value + step * (end - start)
        for value, end, start in zip(point, target, origin, strict=True)
    )


def _mean_carrying_equal(rows: FloatArray, weights: FloatArray) -> FloatArray:
    """Return ``weights @ rows``, carrying a column all rows agree on exactly."""
    combined = np.asarray(weights @ rows, dtype=np.float64)
    constant = np.all(rows == rows[0], axis=0)
    return np.where(constant, rows[0], combined)


__all__ = [
    "ActiveSet",
    "FlatLayout",
    "shrink_blocks",
    "shrink_frequencies",
    "shrink_frequencies_exact",
]
