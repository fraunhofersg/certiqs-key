"""The two singleton-overshoot points: the verified bracket lies below the ceiling.

``meat-core/frank-wolfe/req:verified-feasible-side`` on the evidence of the
singleton-overshoot diagnosis (``tests/data/singleton-overshoot/README.md``). At these
two points a bracket formed from the oracle's return was PRINTED above the proved
finite-alpha ceiling ``U`` -- the oracle's return paired above the feasible side's
minimum on costs of size ``1e7`` and ``1e8``. Here the feasible side is formed as the
requirement forms it: from the dual of a solve of the saved cost (the original call's
dual was not saved, so QICS is called again on the same cost), verified by Lemma D in
exact arithmetic, rounded toward ``-inf``. The verified bracket must lie below ``U``,
compared in exact rationals; the printed one is asserted above it, which is what the
data records.
"""

from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path

import numpy as np
import pytest

from certiqs_key.foundations.dyadic import float_down
from certiqs_key.solvers.frank_wolfe.verified import GroupSolve, _Group, _group_bound
from certiqs_key.solvers.oracles.protocol import Coupling, SectorChoiProblem

pytestmark = [pytest.mark.contract, pytest.mark.requires_qics]

DATA = Path(__file__).resolve().parents[1] / "data" / "singleton-overshoot"
POINTS = json.loads((DATA / "points.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("tag", sorted(POINTS))
def test_the_verified_bracket_lies_below_the_proved_ceiling(tag: str) -> None:
    pytest.importorskip("qics")
    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    meta = POINTS[tag]
    arrays = np.load(DATA / f"{tag}.npz")
    sectors = [sector for _, sector in meta["pairs"]]
    gradient = {("A", s): arrays[f"gradient_{i}"] for i, s in enumerate(sectors)}
    point = {("A", s): arrays[f"point_{i}"] for i, s in enumerate(sectors)}
    input_dim = 2
    problem = SectorChoiProblem(
        input_dim=input_dim,
        block_dims={s: gradient[("A", s)].shape[0] // input_dim for s in sectors},
        cost={s: gradient[("A", s)] for s in sectors},
        rows=(),
        coupling=Coupling.INPUT_IDENTITY,
    )
    solution = QicsSectorChoiOracle().minimize(problem)
    assert solution.dual is not None
    # One trusted Alice sector with an operator coupling of dimension 2 and no
    # rows: Lemma D (i) with the coupling multiplier alone.
    group = _Group(
        unit=False,
        input_dim=input_dim,
        pairs={s: ("A", s) for s in sectors},
        pad=dict(problem.block_dims),
        lifted=(),
        party_local=(),
        frame=None,
        frame_error=None,
        frame_norm=Fraction(0),
    )
    bound, _, _, source = _group_bound(
        group, gradient, GroupSolve(problem, solution.dual), "A"
    )
    assert source == "backend"
    pairing = sum(
        float(np.real(np.trace(gradient[pair] @ point[pair]))) for pair in gradient
    )
    verified = meta["objective"] - pairing + float_down(bound)
    ceiling = Fraction(meta["ceiling"])
    assert Fraction(verified) <= ceiling
    # And the bracket A-LMO allowed, as printed by the run, lay above it.
    assert Fraction(meta["printed_bracket"]) > ceiling
    # The verified bracket from zero multipliers is a bound too (Lemma D (i)).
    zero, _, _, _ = _group_bound(group, gradient, GroupSolve(problem, None), "A")
    assert Fraction(meta["objective"] - pairing + float_down(zero)) <= ceiling
