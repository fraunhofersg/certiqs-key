"""The optical slice end to end: its exit condition, item by item.

A characterized optical receiver in, a squashed POVM through ``receiver``
and ``reductions``, a bundle on disk, a fixed-length key length out --
WITHOUT a branching construction, which is the whole point of the slice: a
wrong number in a later slice then has one candidate cause instead of two.

The exit condition, and the test that discharges each item:

    a key length at all           ``test_the_slice_emits_a_key_length``
    degrades against loss         ``test_the_key_length_degrades_with_loss``
    degrades against dark counts  ``test_the_key_length_degrades_with_dark_counts``
    the qubit result in the limit ``test_it_reproduces_the_qubit_instance_at_...``
    sector-block-diagonal POVM    ``test_the_squashed_povm_is_sector_block_diagonal``
    every route emits             ``test_every_route_emits_a_key_length``

plus three properties, pinned so that none can regress into
a plausible-looking number:

    the exact window is what makes cutoff 1 usable at all
        ``test_without_the_exact_window_the_cutoff_one_device_yields_no_key``
    the contract's predicted route ordering, where it is RESOLVABLE
        ``test_the_route_ordering_is_the_one_the_contract_predicts``
    what admits the cutoff-3 family at ``eps_op = 0`` (the exact (P) decision)
        ``test_at_cutoff_three_the_exact_positivity_decision_is_what_admits_the_family``

EVERY NUMBER HERE IS AN ESTIMATE AND THE DIRECTION IS STATED, NOT SMOOTHED
=========================================================================
``h_low`` at the ``estimate`` tier bounds the true ``h_low`` from ABOVE
(``meat-core`` Section 4.15), and every solve on this declaration reports
``iteration-limit``. The measured Frank-Wolfe gaps at the default 200 iterations
are ``1.4e-2`` at ``N = 1, m* = 2`` and ``1.6e-3`` on Slice 1's qubit
declaration -- so the optical runs are
the LOOSE ones, by an order of magnitude, and every comparison below states
which side of its own gap it sits on. A difference smaller than the gap is
solver noise rather than physics, and this module asserts none as if it were
physics.

``lambda_EC = 0`` throughout. ``meat-core`` never derives it, and a test that
invented a value would be asserting against a choice it is not entitled to make.
"""

from __future__ import annotations

import math
import shutil
import tempfile
from collections.abc import Iterator
from fractions import Fraction as F
from pathlib import Path

import pytest
from instances.bb84.specification import bb84_specification
from instances.common.optics import ReceiverParameters
from instances.common.passive_device import LATTICE_EXPONENT
from tests.support.lowered_templates import (
    ACCEPTANCE_MAPS,
    ENCODED,
    LICENSED,
    LICENSED_TWO_SECTOR,
    OPTICAL_ACCEPTANCE_ALPHABETS,
    ROUTES,
)
from tests.support.lowered_templates import optical_run_slice as run_slice
from tests.support.lowered_templates import qubit_run_slice as run_qubit_slice
from tests.support.manifest_spelling import assert_bindings_in_declared_spelling
from tests.support.tiers import BRACKET_TIER

from certiqs_key.domain.bundle import read_bundle
from certiqs_key.meat_core.declaration.declaration import KeyLengthParameters
from certiqs_key.runs.config import RunConfig
from certiqs_key.runs.flow import StageStatus, mermaid
from certiqs_key.runs.pipeline import SliceRefusal, SliceResult, SliceStage

# NO TEST HERE IS MARKED xfail. `run_slice` takes a REQUIRED
# `declared_tolerance` and hands it to the instance's snap alone, and NO MODULE
# IS TOLD A TOLERANCE AT ALL (spec/architecture.md 2.8, "modules receive no
# tolerance to reason with"); the compiler emits TAGGED constraint entries.

pytestmark = pytest.mark.slow

# The oracle's own dependency. Imported for the skip, not for the name.
pytest.importorskip("qics")

from certiqs_key.solvers.frank_wolfe import (  # noqa: E402
    GeneralKeyRateResult,
    solve_bundle,
)
from certiqs_key.solvers.frank_wolfe.driver import (  # noqa: E402
    FrankWolfeOptions,
)
from certiqs_key.solvers.oracles.qics import QicsSectorChoiOracle  # noqa: E402

#: ``n``. Small enough that ``statistics``'s exact construction --
#: roughly quadratic in ``n`` -- is not what this module spends its time on, and
#: large enough that the finite-size terms do not swamp the physics.
ROUNDS = 10**4

#: ``eps_PA`` and ``eps_EV``, Slice 1's own values.
EPS = 1e-10

PARAMETERS = KeyLengthParameters(alpha=1.05, eps_pa=EPS, eps_ev=EPS, lambda_ec=0)
BUDGET = F(1, 10**6)
ALPHA = 1.05

#: ``tau``, the ceiling this instance's snap may spend. IT IS NOT WHAT ANY
#: MODULE IS TOLD, and no module is told a tolerance at all
#: (spec/architecture.md 2.8, "modules receive no tolerance to reason
#: with"), so what makes exact admissibility reachable is the INSTANCE'S SNAP,
#: which is what ``test_every_module_on_this_path_is_told_exactly_zero``
#: asserts.
DECLARED_TOLERANCE = 1e-12

#: The measured Frank-Wolfe gap at the default 200 iterations on this
#: declaration. A difference smaller than this is not a difference.
SOLVER_GAP = 6e-3

#: The cutoff-1 device with the 0.3.0 exact window at ``m* = N + 1``, which is
#: the configuration the whole slice runs at. The depth is measured to suffice:
#: at ``N = 1`` the binding term is the exact ``beta*(2) = 1/2``.
DEVICE = ReceiverParameters(photon_cutoff=1, exact_window=2)

#: The QBER every run below uses unless it is the axis.
QBER = F(1, 50)

_ORACLE = QicsSectorChoiOracle()
_RUNS: dict[tuple[object, ...], SliceResult | SliceRefusal] = {}
_ROOT: Path | None = None


@pytest.fixture(scope="module", autouse=True)
def _bundle_root() -> Iterator[None]:
    """One scratch tree for every bundle this module writes.

    :func:`certiqs_key.domain.write_bundle` never overwrites, so each run needs its
    own directory and the tree has to outlive the individual test that made it
    -- the results are cached and shared.
    """
    global _ROOT
    _ROOT = Path(tempfile.mkdtemp(prefix="optical-bb84-slice-"))
    try:
        yield
    finally:
        shutil.rmtree(_ROOT, ignore_errors=True)
        _ROOT = None


def _run(
    *,
    qber: F = QBER,
    transmittance: F = F(1),
    receiver: ReceiverParameters = DEVICE,
    route: str = ENCODED,
    rounds: int = ROUNDS,
) -> SliceResult | SliceRefusal:
    """Run one point, or return the cached outcome of an identical earlier one.

    EVERY DEVICE PARAMETER REACHING THIS FUNCTION IS DYADIC, and that is not
    cosmetic: the operator bundle round-trips through binary64, so a non-dyadic
    device parameter comes back a different exact rational and ``meat-core``
    refuses it against a tolerance of exactly zero -- which is the tolerance
    spec/architecture.md 6 requires this slice to run at.
    """
    key = (
        qber,
        transmittance,
        receiver.photon_cutoff,
        receiver.exact_window,
        receiver.dark_count,
        receiver.basis_split,
        route,
        rounds,
    )
    if key not in _RUNS:
        assert _ROOT is not None
        _RUNS[key] = run_slice(
            qber=qber,
            transmittance=transmittance,
            receiver=receiver,
            rounds=rounds,
            completeness_budget=BUDGET,
            parameters=PARAMETERS,
            oracle=_ORACLE,
            declared_tolerance=DECLARED_TOLERANCE,
            directory=_ROOT / f"run-{len(_RUNS):03d}",
            alpha=ALPHA,
            route=route,
        )
    return _RUNS[key]


#: The iteration budget the qubit-limit comparison re-solves at. Chosen by
#: measurement and not by taste: at 200 iterations the combined gap (1.5e-2) is
#: comparable to the deficit being measured (1.9e-2) and nothing can be
#: concluded; at 800 the combined gap is 2.7e-3 against a deficit of 2.3e-2,
#: eight times over. 3000 sharpens it to eleven times at four times the wall
#: time and changes no conclusion.
CONVERGED_ITERATIONS = 800


def _converged(directory: Path) -> GeneralKeyRateResult:
    """Re-solve a bundle a run already wrote, at a budget that resolves it.

    THE SAME BUNDLE, not a reconstruction: what is read is what the run put on
    disk. See :func:`test_it_reproduces_the_qubit_instance_at_the_ideal_device`
    for why the budget cannot be set through the pipeline instead.
    """
    return solve_bundle(
        read_bundle(directory),
        _ORACLE,
        alpha=ALPHA,
        options=FrankWolfeOptions(max_iterations=CONVERGED_ITERATIONS),
    )


def _length(outcome: SliceResult | SliceRefusal) -> int:
    """Return the emitted key length, failing with the refusing stage if none."""
    if isinstance(outcome, SliceRefusal):
        pytest.fail(f"refused at {outcome.stage}: {outcome.reason}: {outcome.detail}")
    assert outcome.key_rate.key_length is not None, outcome.key_rate.key_length_reason
    return outcome.key_rate.key_length


# ===========================================================================
#  The exit condition.
# ===========================================================================


def test_the_slice_emits_a_key_length() -> None:
    """A characterized optical receiver produces a positive fixed-length key.

    The whole slice, in one assertion. Every module boundary is crossed --
    ``receiver``, ``reductions``, ``protocol-compiler``,
    ``statistics``, ``meat-core`` -- and the run record shows all
    five, which the next test asserts.
    """
    outcome = _run()
    assert _length(outcome) > 0


def test_the_run_crosses_and_records_every_module_boundary() -> None:
    """Four artifacts, four contract versions, and no stage skipped."""
    outcome = _run()
    assert isinstance(outcome, SliceResult)
    assert outcome.receiver_artifact is not None
    assert outcome.reduction_artifact is not None
    assert outcome.rows_adaptation is not None
    assert outcome.receiver_artifact.mathematical_spec_version.startswith("receiver@")
    assert outcome.reduction_artifact.mathematical_spec_version.startswith(
        "reductions@"
    )
    assert outcome.key_rate.mathematical_spec_version.startswith("meat-core@")


def test_every_module_on_this_path_is_told_exactly_zero() -> None:
    """The optical slice's requirement under the number model.

    ``reductions`` carries NO TOLERANCE ROW and its request carries
    ``lattice_exponent``, which "fixes a SET of representable values" and is
    not a distance. The requirement is the statement spec/architecture.md 2.8
    makes:
    "modules receive no tolerance to reason with", ``meat-core`` is passed
    ``0``, and what makes that reachable is the INSTANCE'S SNAP.

    Three halves are asserted, because a run could satisfy any two of them and
    still be wrong: the run declared a positive ceiling; the module was told
    zero all the same; and the instance actually snapped, onto the lattice the
    producer was independently handed.
    """
    outcome = _run()
    assert isinstance(outcome, SliceResult)
    assert outcome.declared_tolerance == DECLARED_TOLERANCE > 0.0
    assert outcome.rows_adaptation is not None
    assert outcome.rows_adaptation["lattice_exponent"] == LATTICE_EXPONENT
    # The producer establishes (D-LAT) on the SAME lattice the instance
    # declared, which is what makes one number rather than two.
    assert outcome.reduction_artifact is not None
    assert (
        outcome.reduction_artifact.emission_record.lattice_exponent == LATTICE_EXPONENT
    )


def test_the_key_length_degrades_with_loss() -> None:
    """Strictly, at every halving of the transmittance. Dyadic throughout."""
    lengths = [
        _length(_run(transmittance=transmittance))
        for transmittance in (F(1), F(1, 2), F(1, 4))
    ]
    assert lengths == sorted(lengths, reverse=True)
    assert lengths[0] > lengths[-1]


def test_the_key_length_degrades_with_dark_counts() -> None:
    """A dark count is an error Bob cannot tell from a signal, so it must cost.

    The rates are powers of two for the reason :func:`_run` gives: at
    ``p_dc = 1/1000`` the bundle's round trip through binary64 makes
    ``eps_op = 0`` unreachable and the run refuses with ``delta_cpl = 1.11e-16``.
    """
    lengths = [
        _length(
            _run(
                receiver=ReceiverParameters(
                    photon_cutoff=1, exact_window=2, dark_count=(rate,) * 4
                )
            )
        )
        for rate in (F(0), F(1, 256), F(1, 64), F(1, 16))
    ]
    assert lengths == sorted(lengths, reverse=True)
    assert lengths[0] > lengths[-1]


def test_it_reproduces_the_qubit_instance_at_the_ideal_device() -> None:
    """The limit case: unit efficiency, no dark counts, no loss.

    At ``eta = 1`` and ``p_dc = 0`` this receiver's squashed statistics are the
    qubit BB84 receiver's, so the two instances are about the same physics. They
    are DIFFERENT declarations -- ``d_Q = 9`` against ``d_Q = 2``, four Bob
    announcements against three -- so an agreement is a real check on the
    squasher and not a tautology.

    IT DOES NOT REPRODUCE IT EXACTLY AT FINITE CUTOFF, AND THAT IS THE FINDING.

    At the default 200 iterations the optical run's own Frank-Wolfe gap is
    ``5.9e-2`` and the deficit against the qubit run is ``2.0e-2`` -- SMALLER
    than the gap -- so at that budget nothing can be concluded and an equality
    would be asserting against noise. This test therefore RE-SOLVES the two
    bundles the runs already wrote, at :data:`CONVERGED_ITERATIONS`, where the
    gaps fall below the deficit and the comparison becomes a measurement.

    Measured at ``Q = 1/50``, ``n = 1e4``, three budgets:

        iterations   qubit h_low (gap)      optical h_low (gap)     deficit
        200          0.186721 (1.6e-3)      0.167435 (1.4e-2)       1.93e-2
        800          0.186146 (6.9e-4)      0.163089 (2.0e-3)       2.31e-2
        3000         0.185837 (2.6e-4)      0.162099 (1.8e-3)       2.37e-2

    The optical estimates agree to five digits at 800 and 3000. The deficit
    is stable.

    At 3000 iterations the deficit is eleven times the combined gap and is
    still growing as both estimates descend. **The optical squashed model gives
    strictly less entropy than the qubit model at finite cutoff, in the ideal
    limit, and the difference is physical rather than numerical.**

    WHY THAT IS THE RIGHT ANSWER RATHER THAN A DEFECT. The squashed model hands
    the adversary the deterministic-click flag sectors, and what bounds their
    weight is ``p_mc``, which is ``0.499`` here and not ``1``. The deficit
    shrinks as ``p_mc`` rises -- ``2.37e-2`` at ``p_mc = 0.499`` against
    ``1.87e-2`` at ``p_mc = 0.750``, both at 3000 iterations and both far
    outside the gaps -- so "the appropriate limit" of spec/architecture.md 6's
    exit condition is not ``eta = 1, p_dc = 0`` alone: it is that limit AT
    ``p_mc -> 1``, i.e. ``N -> infinity``. The exit condition is met in the
    sense that the residual is accounted for and closes in the right direction;
    it is NOT an equality at finite ``N``.

    WHY THIS RE-SOLVES INSTEAD OF ASKING THE PIPELINE FOR MORE ITERATIONS.
    What is compared here are two runs at DIFFERENT budgets, so re-solving
    the written bundle keeps the comparison on THE SAME BUNDLE the run wrote
    rather than on a second run of the same point -- and the two-tier record
    of the original run is left describing the budget it was actually driven
    at.
    """
    optical = _run()
    assert isinstance(optical, SliceResult)

    assert _ROOT is not None
    qubit = run_qubit_slice(
        bb84_specification(F(1, 2), F(1, 2), F(1, 2), F(1, 2)),
        qber=QBER,
        rounds=ROUNDS,
        completeness_budget=BUDGET,
        parameters=PARAMETERS,
        oracle=_ORACLE,
        declared_tolerance=DECLARED_TOLERANCE,
        directory=_ROOT / "qubit-limit",
        alpha=ALPHA,
    )
    assert isinstance(qubit, SliceResult)

    # The generation mass is the same on both, which is what makes the two
    # h_low values comparable at all: p_gen = p^A_Z p^B_Z = 1/4 either way.
    assert optical.honest_distribution["gen"] == qubit.honest_distribution["gen"]

    optical_converged = _converged(optical.bundle_directory)
    qubit_converged = _converged(qubit.bundle_directory)
    deficit = qubit_converged.h_low - optical_converged.h_low
    # THE RESOLUTION IS THE CERTIFIED BRACKET WIDTH h_low - h_lb, not the
    # Frank-Wolfe gap of the LAST iterate. The bracket width is at most the
    # gap at every contributing iterate, so it is the tighter of the two and
    # the one both tiers stand behind; the last gap zig-zags (with the exact q
    # rule on this canonical box the optical run's last-iterate gap at 800
    # iterations spans 1.4e-3 to 2.3e-2). The certified widths are optical
    # 1.37e-3 and qubit 3.8e-8; the deficit is 2.28e-2.
    assert optical_converged.h_lb is not None
    assert qubit_converged.h_lb is not None
    gaps = (optical_converged.h_low - optical_converged.h_lb) + (
        qubit_converged.h_low - qubit_converged.h_lb
    )
    assert deficit > 0, "the squashed model cannot give MORE entropy than the qubit one"
    assert deficit > 3 * gaps, (
        f"deficit {deficit!r} is not resolvable against combined gap {gaps!r}"
    )

    # And it closes as p_mc rises, which is what makes it the flag sectors'
    # residual freedom rather than an unexplained offset.
    deeper = _run(receiver=ReceiverParameters(photon_cutoff=2, exact_window=3))
    assert isinstance(deeper, SliceResult)
    deeper_deficit = qubit_converged.h_low - _converged(deeper.bundle_directory).h_low
    assert 0 < deeper_deficit < deficit


def test_the_squashed_povm_is_sector_block_diagonal() -> None:
    """Every emitted element IS its sector-block list, and nothing else exists.

    Eq. ``eq:sectors``' whole purpose: the target POVM acts within
    ``{(m)} u {(f)}`` and never between them, which is what lets ``meat-core``
    parametrize the Choi matrix sector by sector.

    THE PROPERTY IS CHECKED THROUGH THE OPERATOR FORM. By spec/architecture.md
    2.9 an operator IS "a list of sector blocks plus the sector map that names
    them", and "sector-block-diagonality holds BY CONSTRUCTION: nothing
    verifies that the off-sector entries are zero, because nothing can write
    them". There is no entry off the blocks to find, so the check is the
    SECTOR MAP one: one square block per sector, in the
    map's order, of the map's dimensions, summing to the declared target
    dimension. A producer that emitted a different decomposition from the one
    it declared would be caught here.
    """
    outcome = _run()
    assert isinstance(outcome, SliceResult)
    descriptor = outcome.reduction_artifact.target_descriptor
    dimensions = tuple(descriptor.sectors.dimensions)
    assert sum(dimensions) == descriptor.dimension

    for label, element in outcome.reduction_artifact.target_povm.items():
        assert len(element) == len(dimensions), label
        for block, dimension in zip(element, dimensions, strict=True):
            assert len(block) == dimension, label
            for row in block:
                assert len(row) == dimension, label


@pytest.mark.parametrize("route", ROUTES)
def test_every_route_emits_a_key_length(route: str) -> None:
    """All three arms run to a number over one unchanged apparatus."""
    assert _length(_run(route=route)) > 0


def test_the_assurance_tier_and_its_reason_are_legible() -> None:
    """The tier is REPORTED, never silently upgraded, and says why.

    The ``certified`` tier is the third rung (PRINCIPLES.md section 10),
    reached by the solver's certified evaluation; this run reaches it where
    the ball arithmetic is installed. The run says which tier it reports and
    says what that means, rather than emitting a number with no tier.
    """
    outcome = _run()
    assert isinstance(outcome, SliceResult)
    certificate = outcome.key_rate.certificate
    # THE HEADLINE TIER IS `certified` where python-flint is installed and
    # `first-order` where not (tests/support/tiers.py); the first-order rung is
    # earned either way, which `assurance_reason` says.
    assert outcome.key_rate.assurance is BRACKET_TIER
    assert outcome.key_rate.reported_tier is BRACKET_TIER
    assert certificate["assurance_reason"] == "first_order_reported"
    # BOTH LIVE TIERS ARE ON THE RESULT (spec/architecture.md 2.8), and
    # their difference is recorded WITH ITS SIGN rather than refused on.
    assert outcome.key_rate.h_lb is not None
    assert outcome.key_rate.first_order_minus_estimate == pytest.approx(
        outcome.key_rate.h_lb - outcome.key_rate.h_low
    )
    assert math.isfinite(outcome.key_rate.as_payload()["first_order_minus_estimate"])


# ===========================================================================
#  The exact window and the exact positivity decision.
# ===========================================================================


def test_without_the_exact_window_the_cutoff_one_device_yields_no_key() -> None:
    """What ``receiver`` 0.3.0 is FOR, measured on both sides of it.

    At ``N = 1`` the analytic bound gives ``p_mc = 0``, so nothing in the docked
    declaration bounds the target state's weight on the deterministic-click flag
    sectors, an attack supported there is feasible, and ``h_low`` is exactly
    zero. Declaring the exact window at ``m* = 2`` replaces the analytic
    ``beta(2) = 0`` with the true ``lmin = 1/2`` and the same device yields a
    key.

    Both halves are asserted. The zero is not a defect and must not be "fixed":
    it is the correct value of the 0.2.0 bound, and an implementation that
    silently raised it would be unsafe and would look like an improvement.
    """
    without = _run(receiver=ReceiverParameters(photon_cutoff=1))
    assert isinstance(without, SliceResult)
    # Not asserted as EXACTLY zero: the true value is zero and the solver
    # reports a residual of ~1.5e-7 on it, which is what an estimate that
    # bounds from above looks like at a true optimum of zero.
    assert without.key_rate.h_low < 1e-6
    assert not without.key_rate.key_length

    with_window = _run()
    assert _length(with_window) > 0


def test_the_exact_window_at_cutoff_one_recovers_most_of_cutoff_two() -> None:
    """And at a smaller target dimension, which is why it is worth declaring.

    ``d_Q = 9`` against ``12``. The measured recovery on this device is ~99.5%
    of the cutoff-2 key; what is asserted is the qualitative claim -- most of
    it, at a strictly smaller dimension -- because the exact ratio is a number
    carrying the solver gap.
    """
    shallow = _run()
    deep = _run(receiver=ReceiverParameters(photon_cutoff=2))
    assert isinstance(shallow, SliceResult)
    assert isinstance(deep, SliceResult)
    assert (
        shallow.reduction_artifact.target_descriptor.dimension
        < deep.reduction_artifact.target_descriptor.dimension
    )
    assert _length(shallow) > 0.9 * _length(deep)


def test_the_route_ordering_is_the_one_the_contract_predicts() -> None:
    """``encoded >= licensed+two-sector >= licensed``, ASSERTED WHERE IT IS RESOLVABLE.

    Proposition ``prop:chain`` (ii) with Corollary ``cor:monotone`` makes
    ``F^FSS`` strictly cleaner than ``F^WP`` and a cleaner target hands the
    adversary more; Remark ``rem:published`` proves the ``a > 0`` entry
    unconditionally stronger than ``a = 0``.

    THE DEVICE IS NOISY ON PURPOSE. The published entry's ``a`` is
    ``lmin(blk M^{<=N}_e)``, which is ~5.7e-6 at ``p_dc = 1/1024`` -- three
    orders BELOW the solver gap, where the two licensed arms are
    indistinguishable and any ordering between them would be noise. At
    ``p_dc = 1/16`` it is ~2.2e-2, two orders above the gap, and the ordering
    is a measurement.
    """
    noisy = ReceiverParameters(
        photon_cutoff=1, exact_window=2, dark_count=(F(1, 16),) * 4
    )
    lengths = {route: _length(_run(receiver=noisy, route=route)) for route in ROUTES}
    # The measured triple is 540 / 92 / 53 key bits. Only the first separation
    # clears the gap in bits (SOLVER_GAP * n = 60): encoded beats the two-sector arm
    # by 448, which is a measurement. The two-sector arm beats the plain licensed one
    # by 39, which is INSIDE the gap -- so it is asserted as an ordering that
    # holds as measured, not as a separation, and the report says which is
    # which.
    assert lengths[ENCODED] > lengths[LICENSED_TWO_SECTOR] + SOLVER_GAP * ROUNDS
    assert lengths[LICENSED_TWO_SECTOR] >= lengths[LICENSED]


def test_at_cutoff_three_the_exact_positivity_decision_is_what_admits_the_family() -> (
    None
):
    """The exact positivity decision (P) is what admits the ``N = 3`` family.

    A refusal ``delta_pos = 8.5e-18 > tau_num = 0`` at ``N = 3`` is no property
    of the declaration (spec/architecture.md 2.9). The declared family at
    ``N = 3`` is positive semidefinite by an exact rational decision; what is
    negative is ``numpy.linalg.eigvalsh`` on a rank-deficient block, and
    comparing THAT to zero would refuse the run.

    Because (P) is decided exactly, ``N = 3`` runs. Three things are asserted
    together, because any one of them alone would leave the reason ambiguous:

    (i)   the run emits a key length at ``tau_num = 0``;
    (ii)  every declared block is exactly Hermitian and exactly positive
          semidefinite -- the decision that admits it;
    (iii) the float measurement is negative on the block that a float
          comparison would refuse, so the reported ``delta_pos`` has not been
          suppressed, smoothed or repaired. If (iii) ever stops holding, this
          test is passing for a different reason than it says.

    The declared numbers are untouched. Section 2.5 still repairs nothing.
    """
    import numpy as np

    from certiqs_key.foundations.exact_admission import is_hermitian_exact, is_psd_exact

    outcome = _run(receiver=ReceiverParameters(photon_cutoff=3, exact_window=4))
    assert isinstance(outcome, SliceResult)
    assert _length(outcome) > 0

    blocks = [
        (outcome_label, sector, np.asarray(block))
        for outcome_label, sectors in outcome.reread.bob_povm.items()
        for sector, block in sectors.items()
    ]
    assert blocks
    for outcome_label, sector, block in blocks:
        assert is_hermitian_exact(block), (outcome_label, sector)
        assert is_psd_exact(block), (outcome_label, sector)

    floors = {
        (outcome_label, sector): float(
            np.min(np.linalg.eigvalsh((block + block.conj().T) / 2))
        )
        for outcome_label, sector, block in blocks
        if block.size
    }
    # The two rank-deficient 4x4 photon-number blocks that a float comparison
    # would refuse. The value measured at this device is -8.53e-18 on both; the bar is
    # written as "negative and tiny" rather than as that constant, because the
    # eigensolver's residue is a property of LAPACK and not of this repository.
    negative = {where: value for where, value in floors.items() if value < 0.0}
    assert negative, "the float measurement does not reproduce the refusal"
    assert min(negative.values()) > -1e-15


def test_the_published_entry_is_present_where_it_helps_and_absent_where_it_cannot() -> (
    None
):
    """The two-sector arm asks for nothing at the ideal device, and one entry at noise.

    Driven through ``reduce()`` and out the other side into a key length, which
    is the first time Eq. ``eq:two-sector-entry`` has crossed the module boundary at
    all: before this band only its builder was exercised.
    """
    ideal = _run(route=LICENSED_TWO_SECTOR)
    assert isinstance(ideal, SliceResult)
    assert len(ideal.reduction_artifact.constraint_list) == 1

    noisy = _run(
        receiver=ReceiverParameters(
            photon_cutoff=1, exact_window=2, dark_count=(F(1, 16),) * 4
        ),
        route=LICENSED_TWO_SECTOR,
    )
    assert isinstance(noisy, SliceResult)
    assert len(noisy.reduction_artifact.constraint_list) == 2


# ===========================================================================
#  The provenance graph and the record schema, ON THE DEVICE ROUTE
# ===========================================================================
#
# WHY THESE ARE HERE AND NOT IN tests/unit/test_runs_flow.py. Everything that
# needs no oracle IS asserted there, on this same route and in the default
# tier: the prologue's three stages, the edges across them, the rendering, and
# a forced refusal inside the prologue. What is left needs a COMPLETED RUN --
# the executed list against the planned one, the solve's children, and a record
# with the device route's own keys in it -- and a completed optical run is what
# this module is for.


def _surface_config(**overrides: object) -> RunConfig:
    """Return this instance's own default configuration, at this module's point.

    THROUGH THE INSTANCE'S UNIFORM SURFACE (FI-6), because a ``RunConfig`` is
    what the record and the planned stage list are about, while the rest of
    this module drives the instance's lowering with loose arguments
    (``tests/support/lowered_templates.py`` ``optical_run_slice``). The
    device is the cutoff-1 one with the exact window at ``m* = N + 1``, which
    is the configuration the whole slice runs at.

    THE WINDOW IS THE INSTANCE'S OWN DEFAULT and is not set here: a copy of a
    value its owner supplies is a second place for it to be wrong, and setting
    it here would hide a regression in the default this module is supposed to
    be running at.
    """
    from instances.optical_bb84.surface import default_config

    device = dict(default_config().device)
    assert device["exact_window"] == device["photon_cutoff"] + 1
    base: dict[str, object] = {
        "rounds": ROUNDS,
        "completeness_budget": BUDGET,
        "parameters": PARAMETERS,
        "declared_tolerance": DECLARED_TOLERANCE,
        "alpha": ALPHA,
        "device": device,
    }
    return default_config(**{**base, **overrides})


def _surface_run() -> SliceResult | SliceRefusal:
    """Run one point through this instance's runner, and remember it."""
    key = ("surface",)
    if key not in _RUNS:
        from instances.optical_bb84.surface import runner

        assert _ROOT is not None
        _RUNS[key] = runner(
            _ORACLE,
            _ROOT / "surface",
            created_by="tests.integration.test_optical_bb84_slice",
        )(_surface_config(), 0)
    return _RUNS[key]


def _acceptance_run(acceptance_map: str) -> SliceResult | SliceRefusal:
    """Run one point on one acceptance arm through the runner, and remember it."""
    key = ("acceptance", acceptance_map)
    if key not in _RUNS:
        from instances.optical_bb84.surface import runner

        assert _ROOT is not None
        config = _surface_config()
        _RUNS[key] = runner(
            _ORACLE,
            _ROOT / f"acceptance-{acceptance_map}",
            created_by="tests.integration.test_optical_bb84_slice",
        )(
            config.with_(device={**config.device, "acceptance_map": acceptance_map}),
            0,
        )
    return _RUNS[key]


@pytest.mark.parametrize("acceptance_map", list(ACCEPTANCE_MAPS))
def test_every_acceptance_arm_solves_and_reports_its_own_alphabet(
    acceptance_map: str,
) -> None:
    """The whole slice runs on all three arms, and the record says which.

    WHAT THIS ASSERTS AND WHAT IT DELIBERATELY DOES NOT. It asserts that a
    resolved acceptance alphabet reaches the solver and comes back -- the
    acceptance box grows from four coordinates to six or fifteen, several of
    which carry an honest mass of exactly zero at this device, and a solver
    that could not take that would refuse here rather than in a sweep. IT PINS
    NO KEY RATE AND COMPARES NONE. Where each arm's no-key region begins is
    a physics question this repository declines to pin here, and at this
    module's iteration budget a difference between two arms would be
    inside the solver gap and therefore not physics.
    """
    outcome = _acceptance_run(acceptance_map)
    assert isinstance(outcome, SliceResult), outcome
    alphabet = outcome.declaration.acceptance_alphabet
    assert alphabet == OPTICAL_ACCEPTANCE_ALPHABETS[acceptance_map]
    # The acceptance set is built over the SAME letters the declaration
    # carries; the run tier cross-checks this too, and a mismatch there is an
    # assembly error rather than a refusal. Constraining ALL of them is the
    # declared default, so a resolved arm really does give every new letter
    # its own interval rather than declaring it and leaving it vacuous.
    honest_model = outcome.acceptance.honest_model
    assert tuple(honest_model.constrained_outcomes) == alphabet
    assert set(outcome.honest_distribution) == set(alphabet)


def test_the_device_route_s_executed_graph_has_no_edge_to_nothing() -> None:
    """FI-14's first property on a COMPLETED run of the route with a prologue.

    Every stage ran, every consumed artefact id was emitted by an earlier
    stage, and all nine artefact kinds appear -- including the two only a
    device route has.
    """
    outcome = _surface_run()
    assert isinstance(outcome, SliceResult), outcome
    emitted: dict[str, int] = {}
    for index, record in enumerate(outcome.stages):
        assert record.status is StageStatus.EXECUTED, record.stage
        for identifier in record.consumes_artefacts:
            assert identifier in emitted, (record.stage, identifier)
            assert emitted[identifier] <= index
        for artefact in record.emits:
            emitted.setdefault(artefact.identifier, index)
    kinds = {
        str(artefact.kind) for record in outcome.stages for artefact in record.emits
    }
    # ``docked_declaration`` is in the set because the docking stage emits it
    # and ``bundle_write`` consumes it, so the recorded graph shows the honest
    # model reaching the solve. This expectation is what makes a new artefact
    # kind a decision rather than a slip, so it is listed and the assertion is
    # not loosened. The device-route twin of the same check is in
    # ``tests/unit/test_runs_flow.py``.
    assert kinds == {
        "receiver_artifact",
        "reduction_chain",
        "transmitter_artifact",
        "declaration",
        "honest_distribution",
        "acceptance_set",
        "docked_declaration",
        "bundle",
        "key_rate_result",
    }


def test_the_planned_list_matches_the_executed_one_on_this_route() -> None:
    """FI-14's fourth property, where the planned list has three more stages.

    The preparation runs the prologue and stops; the run runs all ten. What is
    compared is the stage order, the consumed configuration keys and the
    consumed artefact KINDS, so a stage that started reading a new key or
    consuming a new kind on the DEVICE route fails here.

    THE KINDS ARE ``PLANNED_ARTEFACT_KINDS``. A planned
    stage cannot name artefact ids -- an id is of something computed -- so the
    planned graph had configuration edges alone; the table is a declaration
    and this is the device route's half of holding it against a real run. The
    comparison is in ORDER and not as sets, because a stage handed two
    artefacts of one kind consumed two things.
    """
    from instances.optical_bb84.surface import preparation

    planned = preparation(_surface_config())
    executed = _surface_run()
    assert isinstance(executed, SliceResult), executed
    assert not isinstance(planned, SliceRefusal), planned
    assert [record.stage for record in planned.stages] == [
        record.stage for record in executed.stages
    ]
    from certiqs_key.runs.flow import PLANNED_ARTEFACT_KINDS, PLANNED_CONFIG_KEYS

    for plan, run in zip(planned.stages, executed.stages, strict=True):
        assert set(plan.consumes_config) == set(run.consumes_config), plan.stage
        assert plan.consumes_artefact_kinds == run.consumes_artefact_kinds, plan.stage
        # AND BOTH AGAINST THE DECLARED TABLES, which is the third source that
        # would otherwise be free to drift from the two. On THIS route the
        # prologue kinds are promised and not filtered, and the four rows a
        # preparation has already executed -- the three prologue stages and the
        # compilation -- are asserted here and nowhere else.
        assert set(run.consumes_config) == set(PLANNED_CONFIG_KEYS[run.stage])
        assert run.consumes_artefact_kinds == PLANNED_ARTEFACT_KINDS[run.stage], (
            run.stage
        )


def test_the_solve_stage_carries_its_children_on_this_route_too() -> None:
    """The five children this tier serialises from the result, unchanged."""
    outcome = _surface_run()
    assert isinstance(outcome, SliceResult), outcome
    solve = next(
        record for record in outcome.stages if record.stage is SliceStage.SOLVE
    )
    assert [child.name for child in solve.children] == [
        "bundle_validation",
        "map_generation_and_cross_validation",
        "frank_wolfe",
        "alpha",
        "key_length_assembly",
    ]
    alpha = next(child for child in solve.children if child.name == "alpha")
    assert alpha.detail["searched"] is False


def test_a_device_route_record_validates_against_the_checked_in_schema() -> None:
    """The schema is validated against a produced record on one route.

    The keys that exist only HERE -- ``stages.reduction``, the receiver's
    structured modes, a non-null ``channel_interface``, a snaps block -- are
    checked against the schema. The schema is read from the INSTALLED package
    data, which is what a consumer generates types from.
    """
    import json

    import certiqs_key.runs as runs_package

    jsonschema = pytest.importorskip("jsonschema")
    from certiqs_key.runs.record import record_run

    outcome = _surface_run()
    assert isinstance(outcome, SliceResult), outcome
    record = record_run(
        outcome, _surface_config(), created_by="tests.integration"
    ).as_dict()
    schema = json.loads(
        (Path(runs_package.__file__).resolve().parent / "record.schema.json").read_text(
            encoding="utf-8"
        )
    )
    jsonschema.validate(record, schema)
    assert json.loads(json.dumps(record)) == record
    # One value per bound name, in the declared spelling.
    assert_bindings_in_declared_spelling(record)

    payload = record["payload"]
    assert payload["stages"]["reduction"]
    assert payload["channel_interface"] is not None
    # The instance snaps its receiver
    # family against the receiver's reference, whose defects are zero on the
    # reference's ground, so no MEASURED pre-snap defect is recorded and the
    # maximum is null; the snap itself is recorded per setting and block.
    assert payload["snaps"]["snap_max_defect"] is None
    # A snap names each block kept or moved, and
    # no status of its own; the shipped default keeps every block.
    (snap,) = payload["snaps"]["instance"]["measurement_snaps"]
    assert {block["status"] for block in snap["blocks"]} == {"kept"}
    assert {block["reference_kind"] for block in snap["blocks"]} == {"exact"}
    assert payload["composition_flow"]["mermaid"] == mermaid(outcome.stages)


def test_the_two_routes_record_the_same_keys(tmp_path: Path) -> None:
    """FI-7's uniformity rule, stated as a test: ONE SHAPE FOR EVERY INSTANCE.

    "An instance that lacks a stage omits the key or sets it to null, never a
    differently shaped key". What is
    compared is the key SETS of two records made on the two routes -- the
    device route here, the direct finite POVM route through the qubit
    instance's own surface -- at the top level, in the configuration, in the
    composition flow, in the snaps block and in the receiver's own stage.

    The qubit run is made here rather than shared, because what this test needs
    is not a number but a record with the other route's shape.
    """
    from instances.bb84.surface import default_config as qubit_config
    from instances.bb84.surface import runner as qubit_runner

    from certiqs_key.runs.record import record_run

    optical = _surface_run()
    assert isinstance(optical, SliceResult), optical
    config = qubit_config(rounds=2_000, alpha=ALPHA)
    qubit = qubit_runner(_ORACLE, tmp_path / "qubit", created_by="tests.integration")(
        config, 0
    )
    assert isinstance(qubit, SliceResult), qubit

    here = record_run(optical, _surface_config(), created_by="t").as_dict()["payload"]
    there = record_run(qubit, config, created_by="t").as_dict()["payload"]

    assert set(here) == set(there)
    assert set(here["config"]) == set(there["config"])
    assert set(here["composition_flow"]) == set(there["composition_flow"])
    assert set(here["snaps"]) == set(there["snaps"])
    # THE RECEIVER STAGE IS WHERE THE ROUTES DIFFER MOST, which is why FI-7
    # names it: the same keys, a ``route`` saying which one was taken, and the
    # keys the other route cannot fill set to null rather than dropped.
    assert set(here["stages"]["receiver_construction"]) == set(
        there["stages"]["receiver_construction"]
    )
    assert here["stages"]["receiver_construction"]["route"] == "compiled_receiver"
    assert there["stages"]["receiver_construction"]["route"] == "declared_finite_povm"
    assert there["stages"]["receiver_construction"]["modes"] is None
    assert here["stages"]["receiver_construction"]["modes"]
    # And every stage entry of the flow has the same keys on both routes,
    # whatever became of the stage.
    assert {key for entry in here["composition_flow"]["stages"] for key in entry} == {
        key for entry in there["composition_flow"]["stages"] for key in entry
    }


# ===========================================================================
#  Warm starts across a licensed route's constraint rows.
# ===========================================================================


def test_a_licensed_seed_chains_to_the_next_loss_point() -> None:
    """A seed with constraint rows warm-starts a point with the SAME rows.

    The licensed route's rows come from the receiver and do not move with the
    channel, so two loss points share them and a seed from one lives in the
    other's feasible set: admitted (its rows digest matches), mixed toward the
    point's cold start -- the zero-cost vertex, which satisfies the rows -- and
    the chained point's certificate stands in full. A seed of those rows is
    refused, by name, on the route without rows (rows that differ are refused
    the same way; tests/unit/test_joint_solver_options.py holds that case).
    """
    from certiqs_key.runs.iterate_file import (
        ITERATE_FILE_NAME,
        load_warm_start,
        seed_of,
        write_final_iterate,
    )
    from certiqs_key.solvers.frank_wolfe.joint_options import (
        JointFrankWolfeOptions,
    )

    assert _ROOT is not None
    budget = 12

    def point(
        transmittance: F, route: str, options: FrankWolfeOptions, name: str
    ) -> SliceResult | SliceRefusal:
        assert _ROOT is not None
        return run_slice(
            qber=QBER,
            transmittance=transmittance,
            receiver=DEVICE,
            rounds=ROUNDS,
            completeness_budget=BUDGET,
            parameters=PARAMETERS,
            oracle=_ORACLE,
            declared_tolerance=DECLARED_TOLERANCE,
            directory=_ROOT / name,
            alpha=ALPHA,
            route=route,
            options=options,
        )

    first = point(
        F(1), LICENSED, JointFrankWolfeOptions(max_iterations=budget), "chain-0"
    )
    assert isinstance(first, SliceResult)
    assert first.key_rate.final_iterate_rows_sha256 is not None
    seed_directory = _ROOT / "chain-seed"
    seed_directory.mkdir()
    write_final_iterate(seed_directory / ITERATE_FILE_NAME, first.key_rate)
    seed = load_warm_start(seed_of(seed_directory))
    assert seed.constraint_count > 0 and seed.rows_sha256 is not None

    chained = point(
        F(1, 2),
        LICENSED,
        JointFrankWolfeOptions(max_iterations=budget, warm_start=seed),
        "chain-1",
    )
    assert isinstance(chained, SliceResult), chained
    rate = chained.key_rate
    assert rate.final_iterate_rows_sha256 == seed.rows_sha256
    report = rate.certificate["joint_solver"]
    assert report["warm_start"]["rows_sha256"] == seed.rows_sha256
    assert rate.h_lb is not None
    assert rate.assurance is BRACKET_TIER  # certified where installed
    assert any(gate["withdrawal"] is None for gate in rate.certificate["per_iterate"])

    refused = point(
        F(1, 2),
        ENCODED,
        JointFrankWolfeOptions(max_iterations=budget, warm_start=seed),
        "chain-encoded",
    )
    assert isinstance(refused, SliceRefusal)
    assert refused.stage is SliceStage.SOLVE
    assert refused.reason == "warm_start_constraint_rows_mismatch"
