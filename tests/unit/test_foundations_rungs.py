"""The one copy of the lattice-exponent check, the weight ladder, the round-down list.

:mod:`certiqs_key.foundations.rungs` (spec/architecture.md 2.9): the emission
normaliser reads its weight ladder (``reductions/def:emitnorm`` (2), (3)) and
its round-down candidate list, the fall-back of the last resort
(``def:emitnorm`` (3)). Every number is derived by hand beside its assertion.
"""

from __future__ import annotations

import subprocess
import sys
from fractions import Fraction as F

import pytest

from certiqs_key.foundations.errors import MalformedInputError
from certiqs_key.foundations.exact import (
    is_positive_semidefinite,
    matrix,
    subtract,
)
from certiqs_key.foundations.rungs import (
    checked_lattice_exponent,
    round_down,
    round_down_candidates,
    rung_ladder,
)


def test_the_module_is_numpy_free() -> None:
    """The normaliser imports it, and importing reductions loads no array library."""
    program = (
        "import sys\n"
        "import certiqs_key.foundations.rungs\n"
        "import certiqs_key.reductions.normalizer\n"
        "assert not any(n == 'numpy' or n.startswith('numpy.') for n in sys.modules)\n"
        "print('ok')\n"
    )
    completed = subprocess.run(
        [sys.executable, "-c", program], capture_output=True, text=True, check=True
    )
    assert completed.stdout.strip() == "ok"


def test_the_ladder_and_the_lattice_exponent_check() -> None:
    """``2^-k .. 2^-1`` smallest first; ``1 <= k <= 53``."""
    assert rung_ladder(3) == (F(1, 8), F(1, 4), F(1, 2))
    assert checked_lattice_exponent(40) == 40
    for bad in (0, 54, True, 2.0):
        with pytest.raises(MalformedInputError):
            checked_lattice_exponent(bad)  # type: ignore[arg-type]


def test_the_candidate_list_starts_from_the_element_as_it_stands() -> None:
    """``def:emitnorm`` (3): the element, the shifts and scalings, then ``0``.

    ``X = 3/10`` at ``k = 2``: first ``3/10`` itself (off the lattice, so it
    never qualifies); ``r = 2``: ``3/10 - 1/4 = 1/20 -> 0``, ``(3/4)(3/10) =
    9/40 -> 1/4``; ``r = 1``: ``3/10 - 1/2 = -1/5 -> -1/4``, ``(1/2)(3/10) =
    3/20 -> 1/4`` (a repeat, dropped); then ``0`` (a repeat, dropped).
    """
    x = matrix([[F(3, 10)]])
    quarter, zero, minus = (matrix([[v]]) for v in (F(1, 4), F(0), F(-1, 4)))
    assert round_down_candidates(x, 2) == (x, zero, quarter, minus)

    def below(candidate: object) -> bool:
        return is_positive_semidefinite(subtract(x, candidate))  # type: ignore[arg-type]

    # The zero shift comes first and is returned, as def:emitnorm (3) orders it.
    assert round_down(x, 2, below=below) == zero
