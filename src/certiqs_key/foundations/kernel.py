"""The extended divergence kernel ``d(u, v) = u log2(u / v)`` of foundations/lem:kernel.

contract.tex Lemma ``foundations/lem:kernel`` defines

    d(u, v) = u log2(u/v)   for u, v > 0,
    d(0, v) = 0             for every v >= 0, INCLUDING v = 0,
    d(u, 0) = +inf          for u > 0,

and proves that this extension -- the closed perspective of ``g(t) = t log2 t``
-- is jointly convex, lower semicontinuous, and non-increasing in ``v``. Those
three properties are exactly what Theorem ``thm:convexity`` uses to carry
convexity through the CONCAVE ``K_chat``, so the extension is part of claim C9b
and not a defensive afterthought.

Two values are load-bearing and are easy to get wrong:

* ``d(0, 0) = 0``, not ``NaN`` and not ``+inf``;
* a single term may be NEGATIVE (``d(1/4, 1/2) = -1/4``). Only the full sum over
  a pair of probability vectors is non-negative. Clamping individual terms at
  zero computes a larger objective and overstates the key.
"""

from __future__ import annotations

import math

#: The base-2 logarithm of e, the conversion factor that appears wherever a
#: derivative of ``d`` is taken (contract.tex Corollary ``cor:full-gradient``).
LOG2_E = 1.0 / math.log(2.0)


def divergence_kernel(u: float, v: float) -> float:
    """Return ``d(u, v)`` of contract.tex Lemma ``foundations/lem:kernel``.

    Raises:
        ValueError: if either argument is negative. The kernel is stated on the
            non-negative quadrant only, and a negative probability or a
            negative ``K_chat`` is a defect upstream, not something to round.
    """
    if u < 0.0 or v < 0.0:
        raise ValueError(
            "the divergence kernel of Lemma foundations/lem:kernel is defined on the "
            f"non-negative quadrant; got d({u!r}, {v!r})"
        )
    if u == 0.0:
        return 0.0
    if v == 0.0:
        return math.inf
    return u * math.log2(u / v)


def divergence_kernel_du(u: float, v: float) -> float:
    """Return ``d/du d(u, v) = log2(u/v) + log2(e)``.

    contract.tex Corollary ``cor:full-gradient``, the ``q`` block of
    Eq. ``eq:grad-q``. Defined for ``u > 0`` and ``v > 0`` only: the corollary
    states the gradient at a point with ``q(chat) > 0``, ``P_chat > 0`` and
    ``K_chat > 0``, and at ``u = 0`` the derivative is ``-inf``.
    """
    if u <= 0.0 or v <= 0.0:
        raise ValueError(
            "Corollary cor:full-gradient states the q-gradient at a point with "
            f"q(chat) > 0, P_chat > 0 and K_chat > 0; got u={u!r}, v={v!r}"
        )
    return math.log2(u / v) + LOG2_E


def divergence_kernel_dv(u: float, v: float) -> float:
    """Return ``d/dv d(u, v) = -(u/v) log2(e)``.

    contract.tex Corollary ``cor:full-gradient``, the coefficient multiplying
    the operator gradients ``Gamma`` and ``Gamma + Delta`` in Eq. ``eq:grad-J``.
    """
    if u <= 0.0 or v <= 0.0:
        raise ValueError(
            "Corollary cor:full-gradient states the J-gradient at a point with "
            f"q(chat) > 0, P_chat > 0 and K_chat > 0; got u={u!r}, v={v!r}"
        )
    return -(u / v) * LOG2_E
