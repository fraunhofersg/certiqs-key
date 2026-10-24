"""The qubit slice against a published fixed-length curve, at the one shared point.

WHAT IS COMPARED. ``tests/oracles/data/navarro2025conic-fixedlength/`` holds
twenty fixed-length qubit BB84 rates regenerated from the public code of
``navarro2025conic`` at the paper's Fig. 1 parameters (its ``PROVENANCE.md``
says how). One of them is reachable here with nothing reinterpreted:
``n = 1e5``, ``Q = 0.015``, zero loss, ``p_K = 0.589`` for both parties. This
file runs the qubit instance there, with their security parameters and their
error-correction leakage as ``lambda_EC``, and sets the two rates side by side.

IT IS A LOOSE REFERENCE, AND THE LOOSENESS IS A FINDING, NOT A TOLERANCE
CHOSEN HERE. The two numbers are different
mathematical objects: their acceptance set is a Bretagnolle-Huber-Carol ball of
one radius across all outcomes, this engine's is the exact per-outcome binomial
box at the same completeness budget, which is narrower and so constrains the
adversary more; and their accumulation carries no marginal constraint. Both
deltas push this engine's rate ABOVE theirs. So what is asserted is an
ordering and two ceilings, each of which would fail on a real defect:

* the run completes at the ``first-order`` tier and reports a key length;
* bits per pulse lie strictly ABOVE their rate at the same point;
* bits per pulse lie strictly BELOW the diluted Devetak-Winter ceiling
  ``p_gen (1 - 2 h2(Q))``, and ``h_low`` below the von Neumann limit
  ``p_gen (1 - h2(Q))``;
* ``h_low`` reproduces its pinned value ``0.285595`` to six decimals. That
  number is a MEASUREMENT and not a derivation, a regression pin. It is
  the result of exact partial minimisation in ``q``, the loop's one ``q`` rule
  on a canonical box: ``h_low = 0.2855950``, ``h_lb = 0.2855950`` (the bracket
  closes to 1e-9) and 22 818 bits;
* ``h_lb`` does not exceed the independent estimate ``0.286092`` (plus the
  same band). That estimate is the objective at a point of the same problem,
  computed by another code base, so it bounds the minimum from above and
  ``h_lb``, a lower bound on that minimum, may not pass it.

WHICH ASSERTION IS AN ORACLE. The ``oracle`` marker (pyproject.toml: "compares
against the independent oracle registry") sits only on the tests that read the
registry row of ``navarro2025conic``. The pinned ``h_low`` is THIS ENGINE'S OWN
MEASUREMENT, a regression pin that catches a change and says nothing about
correctness, so its test carries no ``oracle`` marker; the independent
estimate is an independent upper bound but not a registry entry, so its test
carries none either.

THE BASIS WEIGHT IS THE BINARY64 DATUM OF 0.589 AND NOT 589/1000. The compiler
refuses a declaration whose weighted POVM products are not binary64 numbers
(``emitted_value_not_representable``; spec/architecture.md 2.9: a module does
not snap its own emission), and ``589/1000`` is not one. The nearest binary64
number is what a caller typing ``0.589`` declares, its complement to one is
exact, and the difference from the decimal is below ``1e-16``.

THE KEY LENGTH IS NOT COMPARED WITH AN ``h_low``-BASED FIGURE (22 868 bits
read off ``h_low``): the headline comes from ``h_lb``, which bounds from
below, so it is lower by construction.
"""

from __future__ import annotations

import csv
import math
import shutil
import tempfile
from collections.abc import Iterator
from fractions import Fraction
from pathlib import Path

import pytest
from instances.bb84.surface import default_config, runner
from tests.support.tiers import BRACKET_TIER

from certiqs_key.meat_core.declaration.declaration import KeyLengthParameters
from certiqs_key.runs.pipeline import SliceResult

pytest.importorskip("qics")

#: ``oracle`` is NOT file-wide: see "WHICH ASSERTION IS AN ORACLE" above.
pytestmark = [pytest.mark.requires_qics, pytest.mark.slow]

DATA = (
    Path(__file__).resolve().parents[1]
    / "oracles"
    / "data"
    / "navarro2025conic-fixedlength"
    / "results.csv"
)

#: The shared point.
ROUNDS = 10**5
QBER = Fraction(3, 200)

#: ``p_K`` as the binary64 number a caller typing ``0.589`` declares; see the
#: module docstring.
P_KEY = Fraction(0.589)

#: The paper's Eqs. (49)-(51), which its Fig. 1 uses.
EPS_EV = 1e-11
EPS_PA = 9e-11
EPS_COMP = Fraction(9, 10**11)

#: The Renyi order of the head-to-head, the best of its grid;
#: their continuous optimum at this point is 1.0318.
ALPHA = 1.03

#: ``h_low`` at this point, pinned to six decimals, and the half-unit of the
#: last decimal plus one more unit for the binary64 weight: a measurement.
#: Measured with the exact q rule: 0.28559498159619245.
#: A REGRESSION PIN of this engine's own measurement, not an oracle.
PINNED_H_LOW = 0.285595
PINNED_H_LOW_BAND = 2e-6

#: What an independent estimate printed for ``h_low`` at this point:
#: the objective at a point of the same problem, found by another code base,
#: hence an independent UPPER bound on its minimum and on ``h_lb``. Its band is
#: the pin's (half a unit of the last printed decimal plus one for the weight).
INDEPENDENT_H_LOW = 0.286092

_ROOT = Path(tempfile.mkdtemp(prefix="certiqs-navarro-"))


@pytest.fixture(scope="module", autouse=True)
def _clean_bundles() -> Iterator[None]:
    yield
    shutil.rmtree(_ROOT, ignore_errors=True)


def _binary_entropy(p: float) -> float:
    return -p * math.log2(p) - (1 - p) * math.log2(1 - p)


def _reference_row() -> dict[str, str]:
    with DATA.open(encoding="utf-8", newline="") as handle:
        rows = [
            row
            for row in csv.DictReader(handle)
            if float(row["n"]) == ROUNDS
            and float(row["Q"]) == float(QBER)
            and row["dB"] == "0"
        ]
    assert len(rows) == 1, rows
    return rows[0]


@pytest.fixture(scope="module")
def reference() -> dict[str, str]:
    return _reference_row()


@pytest.fixture(scope="module")
def result(reference: dict[str, str]) -> SliceResult:
    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    # THEIR LEAKAGE, IN BITS, AS THIS ENGINE'S lambda_EC: per pulse times n,
    # rounded UP, since a deduction rounded down would favour this side.
    leakage = math.ceil(float(reference["leak_EC"]) * ROUNDS)
    config = default_config(
        rounds=ROUNDS,
        completeness_budget=EPS_COMP,
        parameters=KeyLengthParameters(
            alpha=ALPHA, eps_pa=EPS_PA, eps_ev=EPS_EV, lambda_ec=leakage
        ),
        model={"qber": QBER},
        device={
            "alice_z": P_KEY,
            "alice_x": 1 - P_KEY,
            "bob_z": P_KEY,
            "bob_x": 1 - P_KEY,
        },
        alpha=ALPHA,
    )
    run = runner(QicsSectorChoiOracle(), _ROOT, created_by="test_navarro_head_to_head")
    outcome = run(config, 0)
    assert isinstance(outcome, SliceResult), outcome
    return outcome


@pytest.mark.oracle
def test_the_reference_row_is_the_one_the_provenance_describes(
    reference: dict[str, str],
) -> None:
    """The frozen row, stated so that the target is readable in the tree."""
    assert float(reference["pK"]) == 0.589
    assert float(reference["v"]) == 0.97
    assert reference["SKR_bits_per_pulse"] == "1.2820648873e-01"
    assert math.ceil(float(reference["leak_EC"]) * ROUNDS) == 4559


def test_the_run_reports_a_first_order_key_length(result: SliceResult) -> None:
    rate = result.key_rate
    # Certified where python-flint is installed.
    assert rate.reported_tier is BRACKET_TIER
    assert rate.key_length is not None and rate.key_length > 0
    assert result.honest_distribution["gen"] == P_KEY * P_KEY


@pytest.mark.oracle
def test_the_rate_lies_above_the_published_one_and_below_the_ceiling(
    result: SliceResult, reference: dict[str, str]
) -> None:
    rate = result.key_rate
    assert rate.key_length is not None
    per_pulse = rate.key_length / ROUNDS
    p_gen = float(P_KEY * P_KEY)
    ceiling = p_gen * (1 - 2 * _binary_entropy(float(QBER)))
    assert float(reference["SKR_bits_per_pulse"]) < per_pulse < ceiling
    # The same decade, which is what makes the ordering informative: a rate
    # ten times theirs would be a defect and not a tighter acceptance set.
    assert per_pulse < 2 * float(reference["SKR_bits_per_pulse"])


def test_the_entropy_lies_below_the_von_neumann_limit_and_the_independent_h_low(
    result: SliceResult,
) -> None:
    rate = result.key_rate
    p_gen = float(P_KEY * P_KEY)
    assert rate.h_lb is not None
    # NO ORDERING BETWEEN THE TWO TIERS IS ASSERTED: spec/architecture.md 2.8
    # makes h_lb <= h_low a diagnostic to record, never an assertion.
    limit = p_gen * (1 - _binary_entropy(float(QBER)))
    assert rate.h_lb < limit
    assert rate.h_low < limit
    assert rate.h_lb <= INDEPENDENT_H_LOW + PINNED_H_LOW_BAND


def test_h_low_has_not_moved_from_its_regression_pin(result: SliceResult) -> None:
    """A regression pin of this engine's own measurement; not an oracle."""
    assert abs(result.key_rate.h_low - PINNED_H_LOW) < PINNED_H_LOW_BAND
