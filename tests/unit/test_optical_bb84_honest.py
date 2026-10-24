"""The optical channel model: one photon, a depolarizer, loss, and the guards.

Slice 1's channel model is a qubit depolarizer; this one is the same physics on
a truncated two-mode Fock space, and the difference is the whole point of
spec/architecture.md 6. What is checked here is that the state is a state, that
the induced distribution is a distribution, and -- above all -- the four guards
this module refuses through, because each of them is a place where a silently
substituted number would produce a run that looked fine and meant nothing:

    a ``float`` parameter        widened into the nearest binary rational, and
                                 the whole exact substrate downstream then does
                                 exact arithmetic on a number nobody wrote down;
    a parameter out of domain    ``Q`` at or above 1/2 inverts the visibility;
    ``d_A != 2``                 the model replaces ONE qubit source;
    a ``tau_A`` mismatch         the state is outside Eq. ``eq:feas``, so the
                                 distribution it induces is reachable by NO
                                 feasible state and the acceptance set built
                                 around it would be unreachable (``meat-core``
                                 Remark ``rem:hlow-range``).

The state's exactness is asserted on the ``Fraction`` entries themselves rather
than through a float tolerance. There is no tolerance to choose: every entry of
every matrix in this module is an exact rational by construction, and a test
that allowed 1e-15 of slack would pass on an implementation that had stopped
being exact.
"""

from __future__ import annotations

from fractions import Fraction as F

import numpy as np
import pytest
from instances.common.errors import OpticalModelError
from instances.common.honest.single_photon_loss_depolarizing import (
    PHI_PLUS_FOCK,
    channel_state,
    honest_distribution,
    honest_provider,
    preserved_dimension,
    visibility,
)
from instances.common.optics import ReceiverParameters
from optical_bb84_prologue import run_prologue
from tests.support.lowered_templates import ANNOUNCEMENT_RESOLVED

from certiqs_key.foundations.exact import Cx
from certiqs_key.protocol_compiler.declaration import CandidateDeclaration

_CACHE: dict[tuple[int, int | None], CandidateDeclaration] = {}


# NO TEST BELOW IS MARKED xfail. Contract Section 2.6's `acceptance_data_exact`
# row decides the declared acceptance data at EXACTLY 0, so the instance
# declares its receiver family through `certiqs_key.foundations.snap`, which
# produces exact admissibility (spec/architecture.md 2.9) rather than reducing
# a defect.


def _declaration(cutoff: int = 1, depth: int | None = 2) -> CandidateDeclaration:
    """Return a real compiled declaration for this device, built once."""
    key = (cutoff, depth)
    if key not in _CACHE:
        _CACHE[key] = run_prologue(
            ReceiverParameters(photon_cutoff=cutoff, exact_window=depth)
        ).declaration
    return _CACHE[key]


def _trace(matrix: tuple[tuple[Cx, ...], ...]) -> F:
    """Return the exact trace, which must be real for a state."""
    total = F(0)
    for index, row in enumerate(matrix):
        assert row[index].im == 0, "a diagonal entry of a state is real"
        total += row[index].re
    return total


def _is_hermitian(matrix: tuple[tuple[Cx, ...], ...]) -> bool:
    """Exactly, entry by entry. No tolerance, because none is needed."""
    size = len(matrix)
    return all(
        matrix[row][column].re == matrix[column][row].re
        and matrix[row][column].im == -matrix[column][row].im
        for row in range(size)
        for column in range(size)
    )


def _smallest_eigenvalue(matrix: tuple[tuple[Cx, ...], ...]) -> float:
    """Return the smallest eigenvalue -- the one float measurement here.

    Positivity of a general Hermitian matrix has no cheap exact test, and this
    module is not the one that has to certify it -- ``reductions`` decides
    admissibility exactly, three stages downstream, on the DECLARED family.
    Here it is a sanity check on the model's own arithmetic.
    """
    dense = np.array(
        [[complex(entry.re, entry.im) for entry in row] for row in matrix],
        dtype=complex,
    )
    return float(np.linalg.eigvalsh(dense)[0])


# ===========================================================================
#  The two closed forms.
# ===========================================================================


@pytest.mark.parametrize(
    ("cutoff", "expected"), [(0, 1), (1, 3), (2, 6), (3, 10), (4, 15), (5, 21)]
)
def test_the_preserved_dimension_is_the_triangular_number(
    cutoff: int, expected: int
) -> None:
    """The ``m``-photon block of two modes has dimension ``m + 1``, summed."""
    assert preserved_dimension(cutoff) == expected
    assert preserved_dimension(cutoff) == sum(m + 1 for m in range(cutoff + 1))


def test_a_negative_cutoff_has_no_preserved_space() -> None:
    with pytest.raises(OpticalModelError, match="non-negative"):
        preserved_dimension(-1)


@pytest.mark.parametrize("qber", [F(0), F(1, 50), F(1, 10), F(1, 4), F(49, 100)])
def test_the_visibility_is_one_minus_twice_the_qber(qber: F) -> None:
    """``v = 1 - 2Q``, exactly, which is the depolarizing model's own identity."""
    assert visibility(qber) == 1 - 2 * qber


# ===========================================================================
#  The state is a state.
# ===========================================================================


@pytest.mark.parametrize("qber", [F(0), F(1, 50), F(1, 10)])
@pytest.mark.parametrize("transmittance", [F(1), F(1, 2), F(1, 16), F(0)])
def test_the_channel_state_is_an_exact_normalized_hermitian_psd_state(
    qber: F, transmittance: F
) -> None:
    """Trace one EXACTLY, Hermitian exactly, and positive to the float floor."""
    state = channel_state(qber=qber, transmittance=transmittance, cutoff=1, q_dim=9)
    assert _trace(state) == 1
    assert _is_hermitian(state)
    assert _smallest_eigenvalue(state) > -1e-15


@pytest.mark.parametrize("transmittance", [F(1), F(1, 2), F(0)])
def test_the_alice_marginal_is_the_maximally_mixed_qubit_at_every_loss(
    transmittance: F,
) -> None:
    """``tau_A = 1_A/2`` is what the declaration declares, at EVERY ``eta``.

    Loss must not tilt Alice's marginal: the vacuum branch carries
    ``(1 - eta) tau_A (x) |vac><vac|`` for exactly this reason, and a branch that
    got the weight wrong would move the state outside Eq. ``eq:feas`` without
    changing its trace.
    """
    q_dim = 9
    state = channel_state(
        qber=F(1, 50), transmittance=transmittance, cutoff=1, q_dim=q_dim
    )
    for alice_row in range(2):
        for alice_column in range(2):
            entry = sum(
                state[alice_row * q_dim + c][alice_column * q_dim + c].re
                for c in range(q_dim)
            )
            assert entry == (F(1, 2) if alice_row == alice_column else F(0))


def test_at_zero_error_and_no_loss_the_state_is_phi_plus_in_the_photon_block() -> None:
    """``v = 1`` leaves the projector alone; the padding carries no weight."""
    q_dim = 9
    state = channel_state(qber=F(0), transmittance=F(1), cutoff=1, q_dim=q_dim)
    for alice_row in range(2):
        for photon_row in range(2):
            for alice_column in range(2):
                for photon_column in range(2):
                    assert (
                        state[alice_row * q_dim + 1 + photon_row][
                            alice_column * q_dim + 1 + photon_column
                        ]
                        == PHI_PLUS_FOCK[alice_row * 2 + photon_row][
                            alice_column * 2 + photon_column
                        ]
                    )
    assert _trace(state) == 1


def test_the_flag_sectors_and_the_higher_photon_blocks_carry_no_weight() -> None:
    """This source sends one photon, so everything above ``C_1`` is zero.

    That is what makes the state a state OF THE SQUASHED MODEL with the physical
    statistics rather than an arbitrary padding.
    """
    q_dim = 9
    state = channel_state(qber=F(1, 50), transmittance=F(3, 4), cutoff=1, q_dim=q_dim)
    occupied = {0, 1, 2}  # the vacuum and the two one-photon basis vectors
    for alice in range(2):
        for c in range(q_dim):
            if c in occupied:
                continue
            index = alice * q_dim + c
            assert all(entry == Cx(F(0), F(0)) for entry in state[index])


# ===========================================================================
#  The induced distribution.
# ===========================================================================


@pytest.mark.parametrize("qber", [F(0), F(1, 100), F(1, 50), F(1, 10)])
@pytest.mark.parametrize("transmittance", [F(1), F(1, 2), F(1, 8)])
def test_the_honest_distribution_is_exact_and_sums_to_one(
    qber: F, transmittance: F
) -> None:
    """Over the WHOLE alphabet, discarded rounds included -- loss goes there."""
    distribution = honest_distribution(
        _declaration(), qber=qber, transmittance=transmittance, cutoff=1
    )
    assert all(isinstance(value, F) for value in distribution.values())
    assert sum(distribution.values()) == 1
    assert all(value >= 0 for value in distribution.values())


def test_loss_moves_mass_out_of_the_generation_class_and_into_discard() -> None:
    """Strictly monotone in ``eta``, which is the exit condition's first half."""
    declaration = _declaration()
    generated = []
    discarded = []
    for transmittance in (F(1), F(3, 4), F(1, 2), F(1, 4), F(1, 8)):
        distribution = honest_distribution(
            declaration, qber=F(1, 50), transmittance=transmittance, cutoff=1
        )
        generated.append(distribution["gen"])
        discarded.append(distribution["disc"])
    assert generated == sorted(generated, reverse=True)
    assert generated[0] > generated[-1]
    assert discarded == sorted(discarded)
    assert discarded[0] < discarded[-1]


def test_loss_inflates_the_merged_bucket_while_the_multiclick_rate_falls() -> None:
    """WHY THE MERGED ACCEPTANCE MAP HAS NOTHING TO SAY ABOUT LOSS.

    The only handle anything here has on the adversary's above-cutoff weight is
    ``receiver`` Definition ``def:slot``'s single entry ``(MC_K, p_mc)``: the
    above-cutoff blocks put at least ``p_mc`` of their mass on multi-click. So
    the multi-click RATE is the observable that prices that weight -- and under
    ``merged-discard`` it is never reported on its own. It is summed into
    ``disc`` together with the no-click rounds and every basis-mismatched
    round, and ``statistics`` can give a confidence interval only to a letter
    that EXISTS (``RunConfig.constrained`` selects among letters; it does not
    create one).

    What this measures is that the two move in OPPOSITE directions in ``eta``.
    The merged bucket rises towards one, because loss lands in it; the honest
    multi-click rate falls, because a multi-click needs coincident detections
    and loss makes those rarer. So the coarsest map's one discard coordinate
    says least exactly where a caller most needs it to say something, and the
    ratio between the two is how much the acceptance data is diluted at that
    point.

    NO KEY RATE IS ASSERTED HERE AND NONE IS IMPLIED. Whether resolving the
    multi-click rate moves the loss wall, and where to, is a measurement that
    this tree does not carry. This is a
    statement about the HONEST distribution, which is not proof-critical, and
    it is here because it is the cheapest executable form of the reason the
    resolved arms exist.

    Dark counts are declared, and must be: at the ideal device no state of at
    most ``N`` photons can multi-click at all, so the multi-click mass is
    exactly zero and there is no ratio to measure.
    """
    ports = ReceiverParameters().dark_count
    device = ReceiverParameters(
        photon_cutoff=1,
        exact_window=2,
        dark_count=tuple(F(1, 1_000_000) for _ in ports),
    )
    merged = run_prologue(device).declaration
    resolved = run_prologue(device, acceptance_map=ANNOUNCEMENT_RESOLVED).declaration

    discarded = []
    multiclick = []
    for transmittance in (F(1), F(1, 2), F(1, 10), F(1, 100)):
        coarse = honest_distribution(
            merged, qber=F(1, 32), transmittance=transmittance, cutoff=1
        )
        fine = honest_distribution(
            resolved, qber=F(1, 32), transmittance=transmittance, cutoff=1
        )
        # The merged letter IS the resolved ones summed over its fibre, which
        # is what makes the two comparable at all.
        assert coarse["disc"] == fine["mis"] + fine["nc"] + fine["mc"]
        discarded.append(coarse["disc"])
        multiclick.append(fine["mc"])

    assert discarded == sorted(discarded), "loss lands in the merged bucket"
    assert multiclick == sorted(multiclick, reverse=True), "and not in mc"
    # The dilution the resolved arm removes, at the two ends of the sweep.
    assert discarded[0] / multiclick[0] > F(10) ** 5
    assert discarded[-1] / multiclick[-1] > F(10) ** 7


def test_the_error_mass_rises_with_the_qber_and_vanishes_at_zero() -> None:
    """The one free coordinate of the acceptance side, behaving as declared."""
    declaration = _declaration()
    errors = [
        honest_distribution(declaration, qber=qber, transmittance=F(1), cutoff=1)["err"]
        for qber in (F(0), F(1, 100), F(1, 50), F(1, 20), F(1, 10))
    ]
    assert errors[0] == 0
    assert errors == sorted(errors)
    assert errors[1] < errors[-1]


def test_the_provider_is_the_distribution_bound_to_its_parameters() -> None:
    """A provider is a closure over the model, not a second model."""
    declaration = _declaration()
    provider = honest_provider(qber=F(1, 50), transmittance=F(3, 4), cutoff=1)
    assert provider(declaration) == honest_distribution(
        declaration, qber=F(1, 50), transmittance=F(3, 4), cutoff=1
    )


# ===========================================================================
#  The four guards. Each is a number this module refuses to invent.
# ===========================================================================


@pytest.mark.parametrize(
    ("qber", "transmittance", "message"),
    [
        (0.02, F(1), "exact rational"),
        (F(1, 50), 0.75, "exact rational"),
        (F(1, 2), F(1), r"\[0, 1/2\)"),
        (F(3, 4), F(1), r"\[0, 1/2\)"),
        (F(-1, 50), F(1), r"\[0, 1/2\)"),
        (F(1, 50), F(3, 2), r"\[0, 1\]"),
        (F(1, 50), F(-1), r"\[0, 1\]"),
    ],
)
def test_a_float_or_an_out_of_domain_parameter_is_refused(
    qber: object, transmittance: object, message: str
) -> None:
    """A float would be widened silently into the nearest binary rational."""
    with pytest.raises(OpticalModelError, match=message):
        honest_distribution(
            _declaration(),
            qber=qber,  # type: ignore[arg-type]
            transmittance=transmittance,  # type: ignore[arg-type]
            cutoff=1,
        )


def test_a_cutoff_below_one_has_nowhere_to_put_the_photon() -> None:
    with pytest.raises(OpticalModelError, match="at least 1"):
        channel_state(qber=F(1, 50), transmittance=F(1), cutoff=0, q_dim=9)


def test_a_declaration_too_small_for_the_preserved_space_is_refused() -> None:
    """``d_Q`` below ``(N+1)(N+2)/2`` is not a declaration of this model."""
    with pytest.raises(OpticalModelError, match="preserved dimension"):
        channel_state(qber=F(1, 50), transmittance=F(1), cutoff=2, q_dim=5)


def test_a_declaration_that_is_not_a_qubit_source_is_refused() -> None:
    """The model replaces ONE qubit source, so ``d_A = 2`` or nothing."""

    class _NotAQubitSource:
        alice_dim = 4

    with pytest.raises(OpticalModelError, match="d_A = 2"):
        honest_distribution(
            _NotAQubitSource(),  # type: ignore[arg-type]
            qber=F(1, 50),
            transmittance=F(1),
            cutoff=1,
        )


def test_a_state_whose_marginal_is_not_the_declared_tau_a_is_refused() -> None:
    """Eq. ``eq:feas`` again: an unreachable acceptance set is worse than none.

    Forced by handing the model a declaration whose ``tau_A`` has been replaced
    with an unbalanced one. Nothing about the state changes; what changes is
    whether it is FEASIBLE for the declaration it is being evaluated against.
    """
    declaration = _declaration()
    tilted = Cx(F(3, 4), F(0)), Cx(F(0), F(0))
    other = Cx(F(0), F(0)), Cx(F(1, 4), F(0))
    with pytest.raises(OpticalModelError, match="not the declared tau_A"):
        honest_distribution(
            declaration.__class__(
                **{
                    **{
                        name: getattr(declaration, name)
                        for name in declaration.__dataclass_fields__
                    },
                    "alice_marginal": (tilted, other),
                }
            ),
            qber=F(1, 50),
            transmittance=F(1),
            cutoff=1,
        )


def test_an_untrusted_source_declaration_declares_no_tau_a_to_check_against() -> None:
    """Nothing here stands in for a marginal the declaration did not make."""
    declaration = _declaration()
    with pytest.raises(OpticalModelError, match="untrusted-source mode"):
        honest_distribution(
            declaration.__class__(
                **{
                    **{
                        name: getattr(declaration, name)
                        for name in declaration.__dataclass_fields__
                    },
                    "alice_marginal": None,
                }
            ),
            qber=F(1, 50),
            transmittance=F(1),
            cutoff=1,
        )
