"""The bases the corollary EXHIBITS, at zero, one and two photons.

spec/modules/transmitter/decoy/: Corollary ``cor:emitted-decoy`` (iv)(b) and its
proof, and Requirement ``req:signal-dyads``, which has the emission form the
signal dyads by this construction and take none from a request. With every
polarisation one of the four vectors of ``D`` and ``|Pol| >= n + 1``, ``S_1`` is
the one-photon space with the basis ``{|1,H>, |1,V>}`` and ``S_2`` the
two-photon space with a basis in which ``|2,a><2,a| = (1/2) v_a v_a^T``. At
``n >= 3`` nothing is constructed and the emission refuses ``N_ent >= 3``.

WHY THE CONSTRUCTION IS IN THE MODULE AND NOT IN AN INSTANCE. It is the
corollary's own construction, derived in its proof, and it is what the refusal at
``N_ent >= 3`` is the absence of; an instance that rebuilt it would be
re-deriving a claim of this submodule. What belongs to a declarer instead -- and
is deliberately NOT here -- is a helper that ROUNDS a supplier's Poisson weights
down onto a dyadic grid: nothing in either interface names one, the interface's
own remedy for an unrepresentable product is that "a declarer for which a product
is not representable removes the refusal by declaring on a coarser dyadic grid",
and that choice of grid is the declarer's act. See the module docstring of
:mod:`certiqs_key.transmitter.decoy.emit`.

THE ENTRIES ARE EXACTLY WHAT THE PROOF WRITES, and they are checked against it
rather than recomputed from amplitudes: no ``1/sqrt 2`` is formed anywhere below,
which is the whole reason the corollary exhibits a basis instead of asserting
that one exists.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Final

from certiqs_key.foundations.errors import MalformedInputError
from certiqs_key.foundations.exact import Matrix, matrix

__all__ = [
    "BB84_POLARISATION_ORDER",
    "EXHIBITED_PHOTON_NUMBERS",
    "exhibited_overlap",
    "exhibited_signal_dyad",
]

_HALF: Final[Fraction] = Fraction(1, 2)

#: The photon numbers at which ``cor:emitted-decoy`` (iv)(b) exhibits a basis.
#: ABOVE THEM NOTHING IS ASSERTED, which is the stated reason the emission
#: refuses ``N_ent >= 3`` (``rem:cutoffs``, "What is generic and what is
#: refused").
EXHIBITED_PHOTON_NUMBERS: Final[tuple[int, ...]] = (0, 1, 2)

#: The order the two-photon construction is written in. The proof matches the
#: Gram matrix of ``|2,H>, |2,V>, |2,+>, |2,->`` with the four rational unit
#: vectors ``(1,1,0)``, ``(1,-1,0)``, ``(1,0,1)``, ``(1,0,-1)`` over root two, in
#: THAT correspondence; a caller declares its own labels and this tuple says
#: which of them plays which part.
BB84_POLARISATION_ORDER: Final[tuple[str, ...]] = ("H", "V", "+", "-")

#: ``r_a`` of the proof, as the coordinates of ``sqrt 2 r_a``, so that the dyad's
#: entries come out as ``(r_a)_i conj((r_a)_j) = +/- 1/2`` with no square root
#: formed: ``r_a = (1/sqrt 2) v_a`` gives ``r_a r_a^dagger = (1/2) v_a v_a^T``.
_TWO_PHOTON_VECTORS: Final[dict[str, tuple[int, int, int]]] = {
    "H": (1, 1, 0),
    "V": (1, -1, 0),
    "+": (1, 0, 1),
    "-": (1, 0, -1),
}

#: The one-photon dyads in the declared basis ``{|1,H>, |1,V>}`` of the
#: one-photon space, read off the proof: ``|1,H><1,H|``, ``|1,V><1,V|`` and
#: ``(1/2)(|1,H><1,H| + |1,V><1,V| +/- |1,H><1,V| +/- |1,V><1,H|)``.
_ONE_PHOTON_DYADS: Final[dict[str, tuple[tuple[Fraction, ...], ...]]] = {
    "H": ((Fraction(1), Fraction(0)), (Fraction(0), Fraction(0))),
    "V": ((Fraction(0), Fraction(0)), (Fraction(0), Fraction(1))),
    "+": ((_HALF, _HALF), (_HALF, _HALF)),
    "-": ((_HALF, -_HALF), (-_HALF, _HALF)),
}


#: ``|<a|b>|^2`` for two distinct vectors of ``D``: ``0`` for the orthogonal
#: pairs ``{H, V}`` and ``{+, -}``, ``1/2`` for every pair across the two bases.
#: The diagonal is one.
_ONE_PHOTON_SQUARED_OVERLAPS: Final[dict[frozenset[str], Fraction]] = {
    frozenset({"H", "V"}): Fraction(0),
    frozenset({"+", "-"}): Fraction(0),
    frozenset({"H", "+"}): _HALF,
    frozenset({"H", "-"}): _HALF,
    frozenset({"V", "+"}): _HALF,
    frozenset({"V", "-"}): _HALF,
}


def exhibited_overlap(photon_number: int, part_a: str, part_b: str) -> Fraction:
    """Return ``|<a|b>|^(2n)`` for two vectors of ``D``, exactly.

    ``req:signal-dyads`` decides of the formed dyads that
    ``tr[|n,a><n,a| |n,b><n,b|] = |<a|b>|^(2n)``, the value
    ``def:wcp-model`` (W3) gives by ``cor:emitted-decoy`` (iv)(b)
    (``|<n,a|n,b>|^2 = |<a|b>|^(2n)``); for two vectors of ``D`` it is ``0``,
    ``2^-n`` or ``1``. It is formed from the one-photon overlaps of ``D``
    alone, independently of the matrices :func:`exhibited_signal_dyad`
    returns, so that the decision is a check of the construction and not a
    restatement of it.
    """
    for part in (part_a, part_b):
        if part not in BB84_POLARISATION_ORDER:
            raise MalformedInputError(
                f"the overlaps of cor:emitted-decoy (iv)(b) are written for "
                f"{list(BB84_POLARISATION_ORDER)}; {part!r} is not one of them"
            )
    if photon_number not in EXHIBITED_PHOTON_NUMBERS or photon_number == 0:
        raise MalformedInputError(
            "cor:emitted-decoy (iv)(b) constructs the dyads at one and at two "
            f"photons; there is no construction here for n = {photon_number}"
        )
    if part_a == part_b:
        return Fraction(1)
    return _ONE_PHOTON_SQUARED_OVERLAPS[frozenset({part_a, part_b})] ** photon_number


def exhibited_signal_dyad(photon_number: int, polarisation_part: str) -> Matrix:
    """Return ``|n,a><n,a|`` in the basis the corollary's proof exhibits.

    ``polarisation_part`` is one of :data:`BB84_POLARISATION_ORDER` and names
    which part of the construction a declared polarisation label plays; a
    declaration's own labels may be anything.

    * ``n = 0``: ``S_0 = C|vac>`` is one dimensional and every polarisation
      shares the vacuum, so the dyad is the number ``1`` and does not depend on
      the polarisation at all (``def:wcp-model`` (W3)).
    * ``n = 1``: the two-dimensional one-photon space in the basis
      ``{|1,H>, |1,V>}``, entries ``0`` and ``+/- 1/2``.
    * ``n = 2``: the three-dimensional ``S_2`` in the basis the proof builds as
      the inverse image under ``U`` of the standard basis of ``C^3``, entries
      ``0`` and ``+/- 1/2``.

    A PHOTON NUMBER ABOVE TWO RAISES rather than returning something, and that
    is the point: at ``n >= 3`` no construction is given and none is asserted,
    and the emission refuses ``N_ent >= 3`` (``req:entropy-cutoff``).
    """
    if polarisation_part not in BB84_POLARISATION_ORDER:
        raise MalformedInputError(
            f"the construction of cor:emitted-decoy (iv)(b) is written for the "
            f"four polarisations {list(BB84_POLARISATION_ORDER)}; "
            f"{polarisation_part!r} is not one of them"
        )
    if photon_number == 0:
        return matrix(((1,),))
    if photon_number == 1:
        return matrix(_ONE_PHOTON_DYADS[polarisation_part])
    if photon_number == 2:
        vector = _TWO_PHOTON_VECTORS[polarisation_part]
        return matrix(
            tuple(
                tuple(_HALF * vector[i] * vector[j] for j in range(3))
                for i in range(3)
            )
        )
    raise MalformedInputError(
        f"cor:emitted-decoy (iv)(b) exhibits a declared basis at "
        f"{list(EXHIBITED_PHOTON_NUMBERS)} photons and asserts nothing at three "
        f"or above; there is no construction here for n = {photon_number}, and "
        "the emission refuses N_ent >= 3 for exactly that reason"
    )
