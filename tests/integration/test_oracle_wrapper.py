"""A delegating wrapper around the oracle IS an oracle.

A delegating wrapper around ``QicsSectorChoiOracle`` -- forwarding
``capabilities()`` and ``minimize()`` and counting the calls -- passes the
capability probe and gives identical results.

WHY IT MATTERS. It is how a caller gets solver progress without touching
accepted module code. The Frank-Wolfe driver deliberately exposes no
per-iteration callback; progress comes from the oracle seam instead: one
``minimize`` call per iterate, in the caller's own object. If the probe or
the driver checked the CONCRETE TYPE of the oracle rather than what it
declares, that route would be closed and the run tier would owe a callback
inside ``solvers/`` after all.

NOTHING UNDER ``src/certiqs_key/solvers`` IS TOUCHED BY THIS FILE, and the probe
does not check the concrete type -- ``require_capabilities``
is a function of an :class:`OracleCapabilities` RECORD and never sees the object
that produced it, and the driver's only contact with the oracle is the two
Protocol methods -- so what this file does is pin that property where a change
to it would be caught, rather than assert it in prose.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction as F
from pathlib import Path
from typing import Any

import pytest
from instances.bb84.specification import bb84_specification
from tests.support.lowered_templates import qubit_run_slice as run_slice

from certiqs_key.meat_core.declaration.declaration import KeyLengthParameters
from certiqs_key.runs.pipeline import SliceResult
from certiqs_key.solvers.capabilities.probe import (
    SECTOR_CHOI_REQUIREMENTS,
    probe_environment,
    require_capabilities,
)
from certiqs_key.solvers.oracles.protocol import LinearOracle, SectorChoiProblem

pytestmark = [pytest.mark.requires_qics, pytest.mark.contract]

#: The point the two runs below are taken at: the symmetric dyadic BB84
#: instance at a 2% depolarizing channel, the same one
#: ``tests/integration/test_bb84_slice.py`` is built on. No number from it is
#: asserted here -- what is asserted is that two runs agree -- so this file
#: owns no target and duplicates no claim.
WEIGHTS = (F(1, 2), F(1, 2), F(1, 2), F(1, 2))
QBER = F(1, 50)
ROUNDS = 2_000
BUDGET = F(1, 1_000_000)
EPS = 2.0**-30
DECLARED_TOLERANCE = 0.0


@dataclass
class CountingOracle:
    """A DELEGATING wrapper: it forwards both methods and counts the calls.

    Deliberately NOT a subclass of anything. :class:`LinearOracle` is a
    :class:`typing.Protocol` -- structural, not nominal -- so an object that
    forwards the two methods IS one, and writing it as a plain dataclass is the
    point: a caller who wants progress must not have to inherit from a class a
    module owns, nor to be recognised by it.
    """

    inner: LinearOracle
    calls: list[str] = field(default_factory=list)

    def capabilities(self) -> Any:
        """Forward the declaration, unchanged.

        UNCHANGED IS LOAD-BEARING. The declaration ends up in the run record as
        the identity of what solved the problem (spec/architecture.md 7.3), so
        a wrapper that rewrote it would put a name in the record for a backend
        that did no work.
        """
        return self.inner.capabilities()

    def minimize(self, problem: SectorChoiProblem) -> Any:
        """Forward the minimization, counting it.

        The count is the progress signal: one call per Frank-Wolfe iterate,
        plus the one that produces the initial point.
        """
        self.calls.append(f"minimize:{len(problem.blocks)}")
        return self.inner.minimize(problem)


def oracle() -> LinearOracle:
    """Return a fresh QICS-backed linear oracle."""
    from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle

    return QicsSectorChoiOracle()


def run(active: LinearOracle, directory: Path) -> SliceResult:
    """Run the BB84 slice once through ``active`` and return the result."""
    outcome = run_slice(
        bb84_specification(*WEIGHTS),
        qber=QBER,
        rounds=ROUNDS,
        completeness_budget=BUDGET,
        parameters=KeyLengthParameters(alpha=1.5, eps_pa=EPS, eps_ev=EPS, lambda_ec=0),
        oracle=active,
        directory=directory,
        declared_tolerance=DECLARED_TOLERANCE,
        alpha=1.5,
    )
    assert isinstance(outcome, SliceResult), outcome
    return outcome


# ===========================================================================
#  The probe: it reads what an oracle DECLARES, not what it is.
# ===========================================================================


def test_the_capability_gate_reads_a_declaration_and_not_a_type() -> None:
    """A wrapper's declaration is the inner oracle's, and the gate takes it.

    The gate is permissive:
    :func:`require_capabilities` takes an ``OracleCapabilities`` record and
    never sees the object that produced it, so a delegating wrapper passes
    exactly when what it wraps passes. The probe is left untouched.
    """
    wrapped = CountingOracle(oracle())
    assert wrapped.capabilities() == oracle().capabilities()
    # Neither call raises, which is what the gate passing means.
    require_capabilities(wrapped.capabilities(), SECTOR_CHOI_REQUIREMENTS)
    require_capabilities(oracle().capabilities(), SECTOR_CHOI_REQUIREMENTS)


def test_the_probe_record_of_a_wrapper_is_the_inner_oracle_s() -> None:
    """The capability identity that reaches the record is the real backend's."""
    wrapped = CountingOracle(oracle())
    assert probe_environment(wrapped.capabilities()) == probe_environment(
        oracle().capabilities()
    )


def test_a_wrapper_satisfies_the_oracle_protocol_structurally() -> None:
    """``isinstance`` against the runtime-checkable Protocol, on a plain object.

    A wrapper that satisfied the probe but not the protocol would type-check
    nowhere, and a caller would be writing code mypy refuses.
    """
    assert isinstance(CountingOracle(oracle()), LinearOracle)


# ===========================================================================
#  The run: identical numbers, and the caller learns how many calls there were.
# ===========================================================================


@pytest.mark.oracle
def test_a_wrapped_run_gives_identical_results_and_counts_the_calls(
    tmp_path: Path,
) -> None:
    """The same numbers through the wrapper as without it, to the last bit.

    IDENTICAL AND NOT MERELY CLOSE: same driver, same oracle, same iterates, so
    ``pytest.approx`` here would be hiding exactly the thing the test is for. A
    wrapper that changed a number would not be a wrapper.

    The call count is the progress signal: one ``minimize`` per
    Frank-Wolfe iterate plus the one that builds the initial point, which is
    the bound asserted -- an inequality rather than an equality because the
    loop can leave before its oracle call when a hypothesis of
    ``thm:firstorder`` fails at an iterate, and this file is not the place that
    pins WHEN that happens.
    """
    wrapped = CountingOracle(oracle())
    through_wrapper = run(wrapped, tmp_path / "wrapped")
    direct = run(oracle(), tmp_path / "direct")

    rate, plain = through_wrapper.key_rate, direct.key_rate
    assert rate.h_low == plain.h_low
    assert rate.h_lb == plain.h_lb
    assert rate.key_length == plain.key_length
    assert rate.optimized_q == plain.optimized_q
    assert rate.certificate["iterations"] == plain.certificate["iterations"]
    assert str(rate.reported_tier) == str(plain.reported_tier)

    # The wrapper SAW the work: one call for the initial point, then at most
    # one per iterate.
    assert wrapped.calls
    assert len(wrapped.calls) <= rate.certificate["iterations"] + 1
    assert len(wrapped.calls) >= 2, "the run solved once and never iterated"
    # ... and every call was the sector-Choi subproblem, on the declaration's
    # own sector layout rather than a flattened one.
    assert set(wrapped.calls) == {wrapped.calls[0]}
