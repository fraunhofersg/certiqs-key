"""The rigorous evaluation of the high-photon multiclick weight.

``receiver/req:rigorous-weight``, by ``receiver/thm:enclosed-weight`` and
``receiver/def:enclosed-weight`` (exposures N5 and N6). Wherever the port
Grams are enclosed (:func:`~certiqs_key.receiver.reference.enclose_port_grams`, the
reference's own enclosure), every setting's weight is formed again in exact rational
arithmetic: the pairs ``(gamma, B)``, ``(beta_k, B_k)`` and the window blocks
``blk M_mc^(=n) = 1 + (K-1) gamma Fock(1-B)^(n) - sum_k beta_k Fock(1-B_k)^(n)``
enclosed by the rules of ``lem:enclosure-arithmetic`` and Hermitian-centred;
``u >= lmax(B)``, ``l_k <= lmin(B_k)`` and ``lambda_n <= lmin(block)`` by
``foundations/cor:least-eigenvalue-over-enclosure`` (i), (ii); ``g <= gamma``
and ``b_k >= beta_k`` from centres and radii; the enclosed bound data
``eq:enclosed-construction``, each clipped to ``[0, 1]``, the window bounds
``max{0, lambda_n}``, and :func:`enclosed_weight`, with no computed eigenvalue
and no ``eps_eig``. A setting with no enclosure keeps the floating-point weight
with item (i)'s reason.

THE PAIRS ARE THE CONSTRUCTION'S. Each setting's enclosed no-click pairs
``(gamma, B)``, ``(beta_k, B_k)`` come from the construction that produced the
setting family, through the one seam
:func:`~certiqs_key.receiver.settings.setting_construction`, and the window
block is enclosed from them in the prefactor form of Definition
``def:setting-family`` (b). ``thm:exact-and-evaluated`` (vii) states that the
weight so formed is an enclosed weight for a receiver without a probe, from
the port Grams (:func:`~certiqs_key.receiver.generic.unconditioned_pairs`);
for a setting family a submodule constructs, that submodule states it for
its own enclosures (``req:rigorous-weight``).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from fractions import Fraction

from certiqs_key.foundations.dyadic import enclosure_eigenvalue_bounds
from certiqs_key.receiver.enclosure import Ball, hermitian_centred
from certiqs_key.receiver.generic import (
    BallField,
    NoEnclosure,
    fock_block,
)
from certiqs_key.receiver.reference import enclose_port_grams
from certiqs_key.receiver.request import ValidatedRequest
from certiqs_key.receiver.settings import setting_construction

__all__ = [
    "BOUND_INPUTS_NOT_ENCLOSED",
    "PORT_GRAMS_NOT_ENCLOSED",
    "EnclosedWeight",
    "enclosed_weight",
    "rigorous_weights",
]

#: Item (i)'s fallback reasons: no model admissible exactly, or a reciprocal of
#: the conditioned prefactors or Grams that receives no enclosure.
PORT_GRAMS_NOT_ENCLOSED = "port_grams_not_enclosed"
BOUND_INPUTS_NOT_ENCLOSED = "bound_inputs_not_enclosed"

_ZERO = Fraction(0)


@dataclass(frozen=True)
class EnclosedWeight:
    """One setting's rigorous evaluation, every number exact (item (vi))."""

    gamma: Fraction
    betas: tuple[Fraction, ...]
    c: Fraction
    ds: tuple[Fraction, ...]
    #: ``(n, w(n))``, the rigorous window bounds over ``N < n <= m*``.
    window: tuple[tuple[int, Fraction], ...]
    weight: Fraction = _ZERO

    def as_record(self) -> dict[str, object]:
        """Return the exact rationals as ``p/q`` strings, for a reader to recompute."""
        return {
            "gamma": str(self.gamma),
            "betas": [str(x) for x in self.betas],
            "c": str(self.c),
            "ds": [str(x) for x in self.ds],
            "window_bounds": [{"photons": n, "bound": str(w)} for n, w in self.window],
            "enclosed_weight": str(self.weight),
        }


def _clip(value: Fraction) -> Fraction:
    """Return ``value`` clipped to ``[0, 1]`` (``eq:enclosed-construction``)."""
    return min(Fraction(1), max(_ZERO, value))


def _beta(data: EnclosedWeight, n: int) -> Fraction:
    """Return ``eq:beta`` on enclosed bound data, ``0^0 = 1``."""
    pairs = zip(data.betas, data.ds, strict=True)
    subtracted = sum((b * d**n for b, d in pairs), _ZERO)
    return 1 + (len(data.betas) - 1) * data.gamma * data.c**n - subtracted


def enclosed_weight(
    data: EnclosedWeight,
    cutoff: int,
    predicate_x: bool,
    window: int | None,
    depth: int | None,
) -> Fraction:
    """Return ``p_mc`` of ``def:enclosed-weight`` (iii): eq:pmcdef or eq:pmcex.

    The branch is predicate (X)'s; ``beta`` and ``T_m = beta(m) - (K-1) gamma
    c^m`` are the enclosed data's, and the window reads ``l(n) = max{beta(n),
    w(n)}`` (``eq:enclosed-ell``).
    """

    def tail(m: int) -> Fraction:
        return _beta(data, m) - (len(data.betas) - 1) * data.gamma * data.c**m

    lows = dict(data.window)
    top = depth or cutoff
    ell = [max(_beta(data, n), lows[n]) for n in range(cutoff + 1, top + 1)]
    if predicate_x:
        return max(_ZERO, min([*ell, _beta(data, top + 1)]))
    assert window is not None and top <= window
    middle = [_beta(data, n) for n in range(top + 1, window + 1)]
    return max(_ZERO, min([*ell, *middle, tail(window)]))


def _bounds(matrix: Sequence[Sequence[Ball]]) -> tuple[Fraction, Fraction]:
    """Return lower and upper bounds on every Hermitian member's spectrum (iii)."""
    return enclosure_eigenvalue_bounds(*hermitian_centred(matrix))


def _window_block(
    field: BallField,
    pairs: Mapping[frozenset[int], tuple[Ball, list[list[Ball]]]],
    ports: int,
    n: int,
) -> list[list[Ball]]:
    """Return ``blk M_mc^(=n)``, enclosed: the multiclick block at ``n`` photons."""

    def lifted(subset: frozenset[int]) -> list[list[Ball]]:
        prefactor, gram = pairs[subset]
        rest = [
            [Ball(Fraction(i == j)) - x for j, x in enumerate(row)]
            for i, row in enumerate(gram)
        ]
        return [[prefactor * x for x in row] for row in fock_block(field, rest, n)]

    every = frozenset(range(ports))
    total = [
        [
            Ball(Fraction(i == j)) + Ball(Fraction(ports - 1)) * x
            for j, x in enumerate(row)
        ]
        for i, row in enumerate(lifted(every))
    ]
    for k in range(ports):
        total = [
            [a - b for a, b in zip(r, s, strict=True)]
            for r, s in zip(total, lifted(every - {k}), strict=True)
        ]
    return total


def _enclosed_data(
    field: BallField,
    pairs: Mapping[frozenset[int], tuple[Ball, list[list[Ball]]]],
    ports: int,
    cutoff: int,
    depth: int | None,
) -> EnclosedWeight:
    """Return the enclosed bound data of ``eq:enclosed-construction`` (item (iii)).

    From the pair ``(gamma, B)`` of all ports and ``(beta_k, B_k)`` of all but
    port ``k``: ``g`` the lower end of ``gamma``'s ball, ``b_k`` the upper ends
    of the ``beta_k``, ``c = 1 - u`` with ``u >= lmax(B)``, ``d_k = 1 - l_k``
    with ``l_k <= lmin(B_k)``, each clipped to ``[0, 1]``; and the window
    bounds ``max{0, lambda_n}`` with ``lambda_n <= lmin(blk M_mc^(=n))`` for
    ``N < n <= m*``. The weight is left for :func:`enclosed_weight`.
    """
    every = frozenset(range(ports))
    gamma, gram = pairs[every]
    without = [pairs[every - {k}] for k in range(ports)]
    return EnclosedWeight(
        gamma=_clip(gamma.re - gamma.radius),
        betas=tuple(_clip(beta.re + beta.radius) for beta, _ in without),
        c=_clip(1 - _bounds(gram)[1]),
        ds=tuple(_clip(1 - _bounds(gram_k)[0]) for _, gram_k in without),
        window=tuple(
            (n, max(_ZERO, _bounds(_window_block(field, pairs, ports, n))[0]))
            for n in range(cutoff + 1, (depth or cutoff) + 1)
        ),
    )


def rigorous_weights(validated: ValidatedRequest) -> dict[str, EnclosedWeight | str]:
    """Return each setting's :class:`EnclosedWeight`, or item (i)'s fallback reason.

    ``receiver/req:rigorous-weight``; at a setting of a receiver without a
    probe by ``receiver/thm:exact-and-evaluated`` (vii), and at a setting of
    a family a submodule constructs by that submodule's statement for the
    enclosures its construction yields.
    """
    request = validated.request
    settings = request.probe_declaration.settings
    grams = enclose_port_grams(validated)[1]
    if grams is None:
        return {setting.label: PORT_GRAMS_NOT_ENCLOSED for setting in settings}
    ports, cutoff = request.port_map.port_count, request.photon_cutoff
    construction = setting_construction(request.input_modes.source_dimension)
    out: dict[str, EnclosedWeight | str] = {}
    for setting in settings:
        field, depth = BallField(), request.exact_window.get(setting.label)
        try:
            pairs = construction.no_click_pairs(
                field, grams.grams, request.input_modes.channel_dimension, setting
            )
            data = _enclosed_data(field, pairs, ports, cutoff, depth)
        except NoEnclosure:
            out[setting.label] = BOUND_INPUTS_NOT_ENCLOSED
            continue
        out[setting.label] = replace(
            data,
            weight=enclosed_weight(
                data,
                cutoff,
                validated.predicate_x[setting.label],
                request.tail_window.get(setting.label),
                depth,
            ),
        )
    return out
