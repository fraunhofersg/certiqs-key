"""The verified first-order bound, against the FROZEN hand-derived ``h_low``.

``meat-core/frank-wolfe/thm:firstorder`` (iv) with
``req:verified-feasible-side``: every bracket's feasible side is a lower bound
on the feasible-side minimum over the exact set, verified from the oracle's
dual, so the reported ``h_lb`` must lie at or below ``h_low`` -- up to the
binary64 arithmetic of everything else in the bracket (the objective, the
gradient and the pairing with the point), which are unbudgeted in the bracket
(``rem:fo-arithmetic``).

THE MARGIN, RECORDED: ``1e-13`` absolute. The verified bracket was measured at
most ``7.5e-15`` above the exact ``h_low`` on these toys and alpha grid,
about ``alpha / (alpha - 1)`` times the unit roundoff; the margin is a
factor of ten above it and four orders below the overshoot (``3e-12`` to
``2.1e-9`` on the same runs) that an unverified feasible side would show,
the reason this file exists. A failure here is a bracket above the value, which is the
unsafe
direction.

Every expected value is ``tests/oracles/registry.py``'s, unmodified, through
the entry each existing golden test reads for the same toy
(``test_hlow_against_registry.py``, ``test_source_modes_against_registry.py``).
"""

from __future__ import annotations

from collections.abc import Callable

import pytest
from dummy_bundles import build_bundle as build_trusted_bundle
from mode_bundles import build_bundle as build_mode_bundle
from registry import (
    ALPHA_GRID,
    O_HLOW_DEPHASED_TABLE,
    O_UNTRUSTED_CONSERVATIVE_UNTRUSTED_VALUE,
    oracle,
)
from toy_declarations import SOURCE_MODE_TOYS, toy

from certiqs_key.meat_core.declaration.bundle import declaration_from_bundle
from certiqs_key.solvers.frank_wolfe import solve
from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

pytestmark = [pytest.mark.contract, pytest.mark.oracle, pytest.mark.requires_qics]

#: The binary64 noise of the bracket's other terms; see the module docstring.
MARGIN = 1e-13


def _frozen(entry_id: str) -> Callable[[float], float]:
    values = dict(oracle(entry_id).frozen_values)
    return lambda alpha: values[alpha]


def _closed(entry_id: str) -> Callable[[float], float]:
    entry = oracle(entry_id)
    assert entry.closed_form is not None
    return entry.closed_form


def _constant(value: float) -> Callable[[float], float]:
    return lambda alpha: value


#: Each toy with the hand-derived h_low the golden tests compare it against.
EXPECTED: dict[str, Callable[[float], float]] = {
    # O-HLOW-RETENTION: TOY-1 keeps the constraint-active sector, h_low = 0.
    "TOY-1": _constant(0.0),
    # O-HLOW-DETERMINISTIC.
    "TOY-2": _constant(0.0),
    # O-HLOW-NO-AVERAGING: the averaged sector is one bit.
    "TOY-2-AVG": _constant(1.0),
    # O-HLOW-FULLY-DEPHASED at m = 2.
    "TOY-3(m=2)": _constant(dict(O_HLOW_DEPHASED_TABLE)[2]),
    # O-HLOW-ZERO-GENERATION.
    "TOY-4a": _constant(0.0),
    "TOY-4b": _closed("O-HLOW-DIVERGENCE-ONLY"),
    "TOY-5": _frozen("O-HLOW-CONSTRAINED"),
    "TOY-6": _frozen("O-HLOW-REMOVAL"),
    "TOY-8-T": _frozen("O-UNTRUSTED-CONSERVATIVE"),
    "TOY-8-UN": _constant(O_UNTRUSTED_CONSERVATIVE_UNTRUSTED_VALUE),
}


@pytest.mark.parametrize("alpha", ALPHA_GRID)
@pytest.mark.parametrize("toy_id", list(EXPECTED))
def test_the_verified_bound_lies_below_the_hand_derived_value(
    toy_id: str, alpha: float
) -> None:
    candidate = toy(toy_id)
    builder = (
        build_mode_bundle if candidate in SOURCE_MODE_TOYS else build_trusted_bundle
    )
    result = solve(
        declaration_from_bundle(builder(candidate)), QicsSectorChoiOracle(), alpha=alpha
    )
    assert result.h_lb is not None
    assert result.h_lb <= EXPECTED[toy_id](alpha) + MARGIN
    # Every contributing bracket, not only the largest, carries its verified side.
    for gate in result.certificate["per_iterate"]:
        if gate["withdrawal"] is None:
            assert gate["feasible_side_bound"] is not None
            assert gate["linearization"] <= EXPECTED[toy_id](alpha) + MARGIN
