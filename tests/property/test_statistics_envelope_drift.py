"""A drifting honest channel is accepted as often as ``epsilon_star`` promises.

``thm:completeness-bound`` under A-HON-ENV: if
the conditional law of every round given the past lies in the envelope, the honest
run is rejected with probability at most ``epsilon_star``. This simulates three
honest channels that SATISFY A-HON-ENV and none of which is i.i.d.:

* ``between runs`` -- each run draws one of the family's laws and keeps it;
* ``within a run`` -- every round draws a fresh mixture weight;
* ``chasing the boundary`` -- a past-dependent drift that, round by round,
  moves toward whichever family law pushes the constrained count that is
  currently closest to leaving the box further out. It is the adapted drift
  ``lem:envelope-dominance`` allows and an i.i.d. analysis would not cover.

The envelope is the entrywise min and max of the family, so every mixture lies
in it. The test is statistical: the empirical rejection rate must stay below
``epsilon_star`` plus four binomial standard deviations. The budget is chosen
large so that the bound is tight enough to be informative at a few thousand
trials; the seed is fixed.
"""

from __future__ import annotations

import math
from fractions import Fraction

import numpy as np
import pytest

from certiqs_key.statistics import (
    AcceptanceConstruction,
    AcceptanceRequest,
    HonestEnvelope,
    construct,
)

F = Fraction
ALPHABET = ("a", "b", "c")
FAMILY = np.array(
    [
        [0.50, 0.30, 0.20],
        [0.40, 0.30, 0.30],
        [0.60, 0.25, 0.15],
    ]
)
ROUNDS = 400
TRIALS = 4000


def _envelope() -> HonestEnvelope:
    exact = [[F(value).limit_denominator(100) for value in row] for row in FAMILY]
    return HonestEnvelope(
        lower={chat: min(row[i] for row in exact) for i, chat in enumerate(ALPHABET)},
        upper={chat: max(row[i] for row in exact) for i, chat in enumerate(ALPHABET)},
    )


def _box() -> tuple[np.ndarray, np.ndarray, float]:
    built = construct(
        AcceptanceRequest(
            alphabet=ALPHABET, honest=_envelope(), rounds=ROUNDS, budget=F(3, 10)
        )
    )
    assert isinstance(built, AcceptanceConstruction)
    box = built.acceptance_set.box_bounds
    assert box is not None
    lower = np.array([float(value) * ROUNDS for value in box[0]])
    upper = np.array([float(value) * ROUNDS for value in box[1]])
    return lower, upper, float(built.completeness_certified)


def _draw(laws: np.ndarray, uniforms: np.ndarray) -> np.ndarray:
    """Return one outcome index per trial from per-trial laws."""
    cumulative = np.cumsum(laws, axis=1)
    return (uniforms[:, None] > cumulative[:, :-1]).sum(axis=1)


def _rejections(mode: str, lower: np.ndarray, upper: np.ndarray) -> int:
    rng = np.random.default_rng(20260924)
    counts = np.zeros((TRIALS, len(ALPHABET)))
    fixed = FAMILY[rng.integers(0, len(FAMILY), TRIALS)]
    centre = (lower + upper) / 2
    for round_index in range(ROUNDS):
        if mode == "between runs":
            laws = fixed
        elif mode == "within a run":
            weights = rng.dirichlet(np.ones(len(FAMILY)), TRIALS)
            laws = weights @ FAMILY
        else:
            # Push the coordinate whose projected count sits furthest from the
            # box centre further out, choosing the family law that does so.
            remaining = ROUNDS - round_index
            projected = counts + remaining * FAMILY[0]
            drift = (projected - centre) / np.maximum(upper - lower, 1.0)
            target = np.abs(drift).argmax(axis=1)
            direction = np.sign(drift[np.arange(TRIALS), target])
            scores = FAMILY[:, target].T * direction[:, None]
            laws = FAMILY[scores.argmax(axis=1)]
        outcome = _draw(laws, rng.random(TRIALS))
        counts[np.arange(TRIALS), outcome] += 1
    outside = (counts < lower - 1e-9) | (counts > upper + 1e-9)
    return int(outside.any(axis=1).sum())


MODES = ["between runs", "within a run", "chasing the boundary"]


@pytest.mark.parametrize("mode", MODES)
def test_a_drifting_honest_run_is_rejected_at_most_as_often_as_promised(
    mode: str,
) -> None:
    lower, upper, epsilon_star = _box()
    rejected = _rejections(mode, lower, upper)
    rate = rejected / TRIALS
    slack = 4 * math.sqrt(epsilon_star * (1 - epsilon_star) / TRIALS)
    assert rate <= epsilon_star + slack, (mode, rate, epsilon_star)
