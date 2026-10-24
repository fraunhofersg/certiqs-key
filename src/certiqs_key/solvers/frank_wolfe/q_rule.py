"""THE LOOP'S ONE ``q`` RULE: exact partial minimisation, chosen by geometry alone.

THE RULE: exact partial minimisation in ``q`` as the loop's ONE rule for the
acceptance-side variable, with no setting. At every point the loop evaluates,
and at every line-search trial, ``q`` is not stepped toward a vertex of the
acceptance set: it is ``q*(J) = argmin_q f(J, q)`` over the set, and the line
search runs on ``g(J) = f(J, q*(J))``. "Exact" names the rule (``q`` is
re-minimised at every ``J``, never stepped); the point itself is the binary64
closed-form partial minimiser made an exact member of the box (THE EXACT ISLAND
below), not an exact ``argmin``. The rule is NOT a protocol-specific hardcoding
in the solver: it keys on the acceptance set's geometry only.

WHICH GEOMETRY GETS WHAT (:func:`q_rule_for`, which reads the ORACLE'S TYPE AND
ITS DECLARED BOX, and no name of any protocol, instance or route):

* **singleton** -- ``q`` is the one point of the set; there is nothing to
  minimise, the rule is not engaged and the loop is the plain loop, bit for
  bit;
* **canonical box** (a polytope whose declared rows ARE signed coordinate
  bounds, with or without ``box_bounds`` metadata, recognised by
  :func:`~certiqs_key.meat_core.acceptance.box.canonical_box`, and served by
  an oracle exposing that :class:`~certiqs_key.meat_core.acceptance.box.CanonicalBox`)
  -- the closed-form solve below;
* **any other polytope** -- NOT BUILT: :func:`q_rule_for` returns ``None`` and
  the loop keeps its ``q`` update (a Frank-Wolfe step toward the
  exact LP vertex, :mod:`~certiqs_key.solvers.frank_wolfe.acceptance_iterate`).
  The partial minimum over a general polytope is a small convex program
  of its own; building it is owed, and until it is the fallback is the
  documented previous rule, never a refusal.

THE SOLVE ON A BOX (newly-derived implementation argument; it changes which
point is evaluated, never what the bracket means). For fixed ``J`` the
objective ``eq:objective`` read through ``def:dropped`` depends on ``q`` only
through the divergence kernels ``d(u, v) = u log2(u / v)``: a key-live value
contributes ``d(q, P) + d(q, K^D) / (alpha - 1)`` and any other
``(alpha / (alpha - 1)) d(q, P)``. Both are

    ``c q log2 q - q l_chat``, with ``c = alpha / (alpha - 1) > 0`` for EVERY value,

``l_chat = log2 P + log2 K^D / (alpha - 1)`` at a key-live value and
``c log2 P`` otherwise. So ``f(J, .)`` is a separable, strictly convex
entropy plus a linear term, minimised over ``{l <= q <= u, sum q = 1}``. With
``m_chat = l_chat / c`` the KKT conditions give, for one scalar ``theta``,

    ``q_chat(theta) = clip(2^(m_chat + theta), l_chat^-, u_chat^+)``:

stationarity of ``c (log2 q + log2 e) - l_chat + nu`` on a free coordinate,
and each one-dimensional strictly convex term minimised over its interval is
the clip of its unconstrained minimiser. ``sum_chat q_chat(theta)`` is
continuous and non-decreasing in ``theta``, piecewise with breakpoints
``log2 l^- - m`` and ``log2 u^+ - m``; the solve locates the interval in
which the sum crosses one and solves the one equation there in closed form.
(Locating the breakpoint interval is one monotone scalar search, done exactly
once.) A
coordinate whose ``P`` -- or, key-live, ``K^D`` -- is zero has
``d(q, 0) = +inf`` for ``q > 0`` and sits at its lower bound; where the free
coordinates cannot absorb the mass the value is ``+inf`` whatever ``q`` does.

THE EXACT ISLAND: WHY THE POINT IS A MEMBER BY CONSTRUCTION. The solve is
binary64 and only CHOOSES a point; the iterate is formed EXACTLY by
:meth:`BoxPartialMinimum.exact_member`: each coordinate's binary64 value is
taken as the exact rational it is, clipped exactly into ``[l^-, u^+]`` (the
declared bounds as rationals), and the exact residual ``1 - sum q`` is put on
the coordinates with the most room in its direction, largest first, each
moved by at most its room. The result satisfies ``l^- <= q <= u^+`` and
``sum q = 1`` over the rationals, and because ``canonical_box`` admits a box
only when the declared rows ARE its bounds (with ``0 <= l^-``,
``polytope_defect``), that is membership in the declared set, by construction
and with no predicate that could fail. Remark ``rem:acc-side`` (beta) admits
it as the convex combination with weight one of a point established to lie in
the set -- the reading its notes and ``frank-wolfe/interface.yaml``
(``exact_island_bounded_bits``) already record for the shortener -- so
``acceptance_iterate_exact`` stays true and the gate reads it as before. The
view evaluated at is the rounding of the exact point; the residual is a few
ulps, so the view is the binary64 solve up to those ulps.

WHY THE CERTIFICATE IS UNCHANGED. ``thm:firstorder`` holds at ANY checked point
``x_t in acSet x Feas^J(epsilon)`` with its hypotheses met, and
``rem:fo-reachability`` prescribes no optimiser. The gate still pairs the
gradient at ``(q_t, J_t)`` with the exact acceptance vertex and the exact
Choi oracle return. The acceptance half of the pairing,
``<grad_q f, v_t - q_t>``, is never positive (``v_t`` is the LP minimiser of
that linear form over the set); at ``q_t = q*(J_t)`` it is zero up to the
snap, so the gap's acceptance half ``<grad_q f, q_t - v_t>`` is non-negative
and zero up to the snap, which is where the loop gains.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Protocol, runtime_checkable

import numpy as np
import numpy.typing as npt

from certiqs_key.meat_core.acceptance.box import CanonicalBox
from certiqs_key.meat_core.objective.joint import (
    DroppedSet,
    JointBranchValues,
    JointMaps,
    JointSector,
    evaluate_joint_branches,
    joint_objective_value_from_branches,
)
from certiqs_key.meat_core.objective.linalg import Matrix
from certiqs_key.solvers.oracles.acceptance import AcceptanceOracle

FloatArray = npt.NDArray[np.float64]


@runtime_checkable
class BoxAcceptance(Protocol):
    """An acceptance oracle that exposes its set as a canonical box.

    ``box`` is the exact box and ``values`` the acceptance values in the
    declared order, which is the order of every ``q`` the loop carries.
    """

    @property
    def box(self) -> CanonicalBox:
        """Return the exact canonical box the oracle minimises over."""
        ...

    @property
    def values(self) -> tuple[str, ...]:
        """Return the acceptance values, in the declared order."""
        ...


@dataclass(frozen=True)
class BoxPartialMinimum:
    """``q*(J) = argmin_q f(J, q)`` over a canonical box, and its exact member.

    ``live`` flags the key-live values (``maps.chat_key``), whose kernels
    carry ``K^D``. Built by :func:`q_rule_for`; the module docstring derives
    the solve and the snap.
    """

    values: tuple[str, ...]
    lower: tuple[Fraction, ...]
    upper: tuple[Fraction, ...]
    live: tuple[bool, ...]
    alpha: float
    _lower_view: FloatArray = field(init=False, repr=False, compare=False)
    _upper_view: FloatArray = field(init=False, repr=False, compare=False)
    _live_mask: npt.NDArray[np.bool_] = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        """Check the lengths and ``alpha``, and form the binary64 views once."""
        if not (
            len(self.values) == len(self.lower) == len(self.upper) == len(self.live)
        ):
            raise ValueError("the box and the acceptance values disagree in length")
        if not math.isfinite(self.alpha) or self.alpha <= 1.0:
            raise ValueError(f"the q rule needs alpha in (1, inf); got {self.alpha!r}")
        object.__setattr__(
            self, "_lower_view", np.asarray([float(x) for x in self.lower], np.float64)
        )
        object.__setattr__(
            self, "_upper_view", np.asarray([float(x) for x in self.upper], np.float64)
        )
        object.__setattr__(self, "_live_mask", np.asarray(self.live, dtype=np.bool_))

    def exponents(self, values: Mapping[str, JointBranchValues]) -> FloatArray:
        """Return ``m_chat``: ``-inf`` where ``P`` (key-live, ``K^D``) is <= 0."""
        p = np.asarray([values[chat].p for chat in self.values], np.float64)
        k = np.asarray([values[chat].k for chat in self.values], np.float64)
        m = np.full(p.shape, -np.inf, dtype=np.float64)
        positive_p = np.isfinite(p) & (p > 0.0)
        plain = positive_p & ~self._live_mask
        keyed = positive_p & self._live_mask & np.isfinite(k) & (k > 0.0)
        m[plain] = np.log2(p[plain])
        m[keyed] = (
            (self.alpha - 1.0) * np.log2(p[keyed]) + np.log2(k[keyed])
        ) / self.alpha
        return m

    def minimise(self, values: Mapping[str, JointBranchValues]) -> dict[str, float]:
        """Return the binary64 ``q*`` at the point whose branch values these are.

        It CHOOSES a point and is never the iterate: a line-search trial is
        evaluated at it, and a taken step is made exact by
        :meth:`exact_member`.
        """
        q = box_argmin(self.exponents(values), self._lower_view, self._upper_view)
        return dict(zip(self.values, q.tolist(), strict=True))

    def exact_member(self, view: Mapping[str, float]) -> dict[str, Fraction]:
        """Return an exact member of the box next to ``view``, BY CONSTRUCTION.

        Each coordinate is the exact rational its binary64 value is, clipped
        exactly into ``[l^-, u^+]``; the exact residual ``1 - sum q`` is then
        moved onto the coordinates with the most room in its direction,
        largest first, each by at most its room. So ``l^- <= q <= u^+`` and
        ``sum q = 1`` hold over the rationals (the module docstring): the
        point Remark ``rem:acc-side`` (beta) takes with weight one.
        """
        point = [
            min(max(Fraction(view[chat]), low), high)
            for chat, low, high in zip(self.values, self.lower, self.upper, strict=True)
        ]
        residual = 1 - sum(point, Fraction(0))
        if residual != 0:
            bounds = self.upper if residual > 0 else self.lower
            room = [
                abs(bound - value) for value, bound in zip(point, bounds, strict=True)
            ]
            order = sorted(range(len(point)), key=lambda i: (-room[i], i))
            remaining = abs(residual)
            sign = 1 if residual > 0 else -1
            for index in order:
                if remaining == 0 or room[index] <= 0:
                    break
                moved = min(remaining, room[index])
                point[index] += sign * moved
                remaining -= moved
            if remaining != 0:  # pragma: no cover - a validated box is non-empty
                raise ArithmeticError(
                    "the canonical box holds no point with sum q = 1; a validated "
                    "acceptance set is never empty"
                )
        return dict(zip(self.values, point, strict=True))

    def objective_at_statistics(
        self,
        maps: JointMaps,
        choi: Mapping[JointSector, Matrix],
        statistics: Mapping[str, float],
        *,
        dropped: DroppedSet,
        skip_key_inert: bool,
    ) -> float:
        """Return ``g(J) = f(J, q*(J))`` at a line-search trial.

        ``statistics`` stands for ``Phi[chi(J)]`` as in
        :func:`~certiqs_key.meat_core.objective.joint.joint_objective_value_at_statistics`;
        the value only chooses the step.
        """
        values = evaluate_joint_branches(
            maps,
            choi,
            self.alpha,
            dropped=dropped,
            skip_key_inert=skip_key_inert,
            statistics=statistics,
        )
        return joint_objective_value_from_branches(
            maps, self.minimise(values), values, self.alpha
        )

    def exact_at(
        self,
        maps: JointMaps,
        choi: Mapping[JointSector, Matrix],
        *,
        dropped: DroppedSet,
        skip_key_inert: bool,
    ) -> tuple[dict[str, Fraction], float]:
        """Return the exact ``q_t`` at a point and the objective there.

        The branch values are formed by the DIRECT path (``Phi`` at the point
        itself), ``q*`` is solved from them and made exact, and the objective
        is evaluated at the rounding of that exact point -- the value the
        iterate carries.
        """
        values = evaluate_joint_branches(
            maps, choi, self.alpha, dropped=dropped, skip_key_inert=skip_key_inert
        )
        exact = self.exact_member(self.minimise(values))
        view = {chat: float(value) for chat, value in exact.items()}
        return exact, joint_objective_value_from_branches(
            maps, view, values, self.alpha
        )


def box_argmin(m: FloatArray, lower: FloatArray, upper: FloatArray) -> FloatArray:
    """Return ``argmin sum_c q_c (log2 q_c - m_c)`` over ``{l <= q <= u, sum q = 1}``.

    In binary64. ``m`` may hold ``-inf`` (such a coordinate sits at its lower
    bound). The minimiser is ``clip(2^(m + theta), l, u)`` for the ``theta``
    at which the sum is one (the module docstring); ``theta`` is found by
    locating the breakpoint interval the sum crosses one in and solving there.
    Where the finite-``m`` coordinates cannot hold the mass they are all at
    their upper bounds and the rest is left to the caller's exact repair
    (the value there is ``+inf`` whatever ``q`` is).
    """
    q = lower.copy()
    free = np.isfinite(m) & (upper > lower)
    target = 1.0 - float(np.sum(q[~free]))
    if not np.any(free):
        return q
    y_all = m[free]
    low = lower[free]
    high = upper[free]
    if float(np.sum(high)) <= target:
        q[free] = high
        return q
    if float(np.sum(low)) >= target:
        return q
    # Shift so the largest exponent is 0: 2^(m + theta) = 2^(y + t), t = theta + max m.
    y = y_all - float(np.max(y_all))
    with np.errstate(all="ignore"):
        at_lower = np.where(low > 0.0, np.log2(low) - y, -np.inf)
        at_upper = np.log2(high) - y
        points = np.unique(
            np.concatenate([at_lower[np.isfinite(at_lower)], at_upper])
        )
        grid = np.minimum(y[:, np.newaxis] + points[np.newaxis, :], 1000.0)
        sums = np.sum(
            np.clip(np.exp2(grid), low[:, np.newaxis], high[:, np.newaxis]), axis=0
        )
    crossing = int(np.searchsorted(sums, target, side="left"))
    crossing = min(crossing, points.shape[0] - 1)
    hi = float(points[crossing])
    lo = float(points[crossing - 1]) if crossing > 0 else -math.inf
    pinned_up = at_upper <= lo
    pinned_down = at_lower >= hi
    middle = ~(pinned_up | pinned_down)
    rest = target - float(np.sum(high[pinned_up])) - float(np.sum(low[pinned_down]))
    t = hi
    if np.any(middle) and rest > 0.0:
        top = float(np.max(y[middle]))
        scale = float(np.sum(np.exp2(y[middle] - top)))
        t = min(max(math.log2(rest) - top - math.log2(scale), lo), hi)
    with np.errstate(all="ignore"):
        q[free] = np.clip(np.exp2(np.minimum(y + t, 1000.0)), low, high)
    return q


def q_rule_for(
    acceptance: AcceptanceOracle, maps: JointMaps, alpha: float
) -> BoxPartialMinimum | None:
    """Return the exact ``q`` rule the acceptance set's GEOMETRY admits, or ``None``.

    Reads the oracle's type and its declared box only. A singleton oracle
    exposes no box; a general polytope's oracle exposes none either; both get
    ``None`` and the loop keeps its previous ``q`` update. An oracle exposing
    a :class:`~certiqs_key.meat_core.acceptance.box.CanonicalBox` over the
    declaration's acceptance values gets the closed-form box solve.
    """
    if not isinstance(acceptance, BoxAcceptance):
        return None
    # A runtime-checkable protocol checks that the attributes exist, not their
    # types: the box itself is checked here.
    box: object = acceptance.box
    values = tuple(acceptance.values)
    if not isinstance(box, CanonicalBox) or values != tuple(
        maps.declaration.acceptance_values
    ):
        return None
    live = set(maps.chat_key)
    return BoxPartialMinimum(
        values=values,
        lower=tuple(box.lower),
        upper=tuple(box.upper),
        live=tuple(chat in live for chat in values),
        alpha=alpha,
    )


__all__ = [
    "BoxAcceptance",
    "BoxPartialMinimum",
    "box_argmin",
    "q_rule_for",
]
