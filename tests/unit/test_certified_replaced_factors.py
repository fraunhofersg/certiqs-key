"""Every replaced factor is read, however many are known through enclosures.

``meat-core/frank-wolfe/lem:certified-bracket-enclosed`` is stated for the set
of replaced factors of ``meat-core/prop:reference-companion``: the compiled
companion replaces every measured factor that carries one, both stations of
bbm92. CONTRACT TESTS of
:func:`~certiqs_key.solvers.frank_wolfe.certified._bob_elements`:

* two replaced factors each read through an enclosure of positive radius are
  both read, and their product carries a factor form;
* a replaced factor whose every block is exact is read exactly, even though it
  carries a factor enclosure with a positive radius beside them. That
  enclosure is cross-checked, never read; the bbm92 canaries' Alice station
  is this case;
* one enclosed replaced factor beside a factor the companion does not replace
  is certified as before;
* an inconsistency of a block's two enclosures, at any letter of any replaced
  factor, fails every point with ``factor_enclosure_inconsistent``;
* every block held through a box is named by its factor, its letter and its
  sector (``req:certified-evaluation`` (iii)(a)), so two distinct blocks with
  equal boxes are distinct entries of the tuples and one block shared by two
  elements is one entry.
"""

from __future__ import annotations

import math
from fractions import Fraction as F
from types import SimpleNamespace
from typing import Any

import pytest

pytest.importorskip("flint")

from certiqs_key.foundations import balls
from certiqs_key.foundations.exact import Cx
from certiqs_key.foundations.reference import FactorEnclosure
from certiqs_key.solvers.frank_wolfe import certified
from certiqs_key.solvers.frank_wolfe.certified_record import (
    FACTOR_ENCLOSURE_INCONSISTENT,
)

pytestmark = pytest.mark.contract

ZERO = F(0)
HALF = F(1, 2)
TINY = F(1, 2**100)
#: A factor enclosure of the block ``(1/2)``: ``L = (1 +- 2^-100)``, ``W = 1/2``.
ROOT_HALF = FactorEnclosure(((Cx(F(1), ZERO),),), ((TINY,),), (HALF,))
#: One whose members, about ``2``, are disjoint from the block ``(1/2 +- tiny)``.
DISJOINT = FactorEnclosure(((Cx(F(2), ZERO),),), ((TINY,),), (HALF,))


LETTERS = ("0", "1")


def _maps() -> Any:
    """Two two-letter factors, one sector each; one sector pair."""
    item = SimpleNamespace(
        alphabet=LETTERS,
        sectors=SimpleNamespace(labels=("s",)),
        blocks={letter: {"s": [[0.5]]} for letter in LETTERS},
    )
    declaration = SimpleNamespace(
        factors=[item, item],
        bob_outcomes=tuple(a + b for a in LETTERS for b in LETTERS),
        sector_index_set=("ss",),
        split_letter=lambda v: tuple(v),
        split_sector=lambda s: tuple(s),
    )
    return SimpleNamespace(declaration=declaration)


def _replaced(
    position: int,
    label: str,
    radius: F,
    factors: dict[str, FactorEnclosure] | None = None,
) -> Any:
    """Every letter the block ``(1/2)`` with ``radius``; ``factors`` carried."""
    return SimpleNamespace(
        position=position,
        label=label,
        alphabet=LETTERS,
        centres={letter: (((Cx(HALF, ZERO),),),) for letter in LETTERS},
        radii=dict.fromkeys(LETTERS, (((radius,),),)),
        factor_enclosures={
            letter: (factor,) for letter, factor in (factors or {}).items()
        },
    )


def _elements(*factors: Any) -> Any:
    with balls.precision(128):
        return certified._bob_elements(_maps(), SimpleNamespace(factors=factors))


def _read(element: Any) -> None:
    assert element.zero is False and element.form is not None


def _failure(*factors: Any) -> certified._Fail:
    with pytest.raises(certified._Fail) as caught:
        _elements(*factors)
    return caught.value


def test_two_enclosed_replaced_factors_are_both_read() -> None:
    elements = _elements(
        _replaced(0, "alice_station", TINY), _replaced(1, "bob_station", TINY)
    )
    assert set(elements) == {(v, "ss") for v in ("00", "01", "10", "11")}
    for element in elements.values():
        _read(element)


def test_an_exact_replaced_factor_with_a_factor_enclosure_is_read_exactly() -> None:
    """Alice's blocks exact, their factor enclosures of positive radius beside them."""
    elements = _elements(
        _replaced(0, "alice_station", ZERO, {"0": ROOT_HALF}),
        _replaced(1, "bob_station", TINY),
    )
    for element in elements.values():
        _read(element)


def test_one_enclosed_replaced_factor_beside_a_declared_one_is_read() -> None:
    for element in _elements(_replaced(1, "bob_station", TINY)).values():
        _read(element)


@pytest.mark.parametrize("position", [0, 1])
@pytest.mark.parametrize("letter", LETTERS)
def test_an_inconsistency_anywhere_is_the_reason_given(
    position: int, letter: str
) -> None:
    """At either letter of either station, both stations read through enclosures."""
    factors = [_replaced(0, "alice_station", TINY), _replaced(1, "bob_station", TINY)]
    factors[position] = _replaced(
        position, factors[position].label, TINY, {letter: DISJOINT}
    )
    assert _failure(*factors).reason == FACTOR_ENCLOSURE_INCONSISTENT


def test_a_replaced_factor_is_read_at_its_position() -> None:
    """The companion's one factor at position 1 replaces factor 1, not the first listed.

    Factor 0 is declared with the blocks ``(0)`` and ``(1)``; the companion
    replaces factor 1 only. Element ``00`` is zero, through factor 0's
    declared block; read by list index, factor 0 would take the companion's
    ``(1/2)`` and the element would not be.
    """
    first = SimpleNamespace(
        alphabet=LETTERS,
        sectors=SimpleNamespace(labels=("s",)),
        blocks={"0": {"s": [[0.0]]}, "1": {"s": [[1.0]]}},
    )
    maps = _maps()
    maps.declaration.factors = [first, maps.declaration.factors[1]]
    with balls.precision(128):
        elements = certified._bob_elements(
            maps, SimpleNamespace(factors=(_replaced(1, "bob_station", TINY),))
        )
    assert elements[("00", "ss")].zero is True
    assert elements[("10", "ss")].zero is False


def _analyser(angle: float) -> tuple[F, F]:
    """Return ``(cos, sin)`` of ``angle`` as dyadics of ``2^-110``: off the grid."""
    scale = 2**110
    return (
        F(round(math.cos(angle) * scale), scale),
        F(round(math.sin(angle) * scale), scale),
    )


def _projectors(position: int, directions: dict[str, tuple[F, F]]) -> Any:
    """Return a factor whose every letter is ``q q^T``, read through the box of ``q``.

    No entrywise floor fixes the rank of ``q q^T``, so the factor rule does:
    every block is of the third kind, held through a box.
    """

    def centre(q: tuple[F, F]) -> Any:
        return tuple(tuple(Cx(q[i] * q[j], ZERO) for j in range(2)) for i in range(2))

    return SimpleNamespace(
        position=position,
        label=f"station{position}",
        alphabet=LETTERS,
        centres={x: (centre(q),) for x, q in directions.items()},
        radii=dict.fromkeys(directions, (((TINY, TINY), (TINY, TINY)),)),
        factor_enclosures={
            x: (
                FactorEnclosure(
                    tuple((Cx(e, ZERO),) for e in q), ((TINY,), (TINY,)), (F(1),)
                ),
            )
            for x, q in directions.items()
        },
    )


def test_every_boxed_block_is_named_by_its_factor_letter_and_sector() -> None:
    """``req:certified-evaluation`` (iii)(a): the tuples name blocks, never boxes.

    Factor 1's letters 0 and 1 carry EQUAL enclosures, so a naming by the
    boxes, or one that drops the letter, would merge two distinct blocks into
    one group; a naming by the joint letter would split one block.
    """
    q, p = _analyser(math.pi / 7), _analyser(math.pi / 5)
    elements = _elements(
        _projectors(0, {"0": q, "1": p}), _projectors(1, {"0": q, "1": q})
    )
    for v in ("00", "01", "10", "11"):
        split = elements[(v, "ss")].split
        assert split is not None, v
        assert split.blocks == ((0, v[0], "s"), (1, v[1], "s")), v
    first, second = elements[("00", "ss")].split, elements[("01", "ss")].split
    assert first is not None and second is not None
    assert first.blocks[0] == second.blocks[0], "one block, one entry"
    assert first.blocks[1] != second.blocks[1], "equal boxes, distinct blocks"
