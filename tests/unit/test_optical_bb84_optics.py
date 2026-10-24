"""The optical receiver as this instance declares it, and the ``p_mc`` it emits.

Three things are checked here and nowhere else.

1. **The compiled element graph is the device it claims to be.** The graph is
   evaluated in floating point by ``receiver``; the four port Grams of the
   ideal device are known in closed form and written down exactly by
   :func:`~instances.common.optics.analytic_port_grams`, which is
   consumed by no run. A comparison whose two halves shared an implementation
   would compare nothing, so the closed form is stated from the physics -- ``A_k
   = eta_k w_k P_k`` -- and the graph is what is measured against it.

2. **``p_mc`` against its closed form**. At this probe-free receiver
   Definition ``def:pmc`` takes branch 1 by predicate (X), its one setting's
   exact flag being set by Corollary ``cor:unconditioned-family``, and Eq.
   ``eq:bb84beta`` collapses to

       p_mc(N) = max{0, 1 - 2 x^(N+1) - 2 (1-x)^(N+1)}

   with ``x`` the splitting ratio. Four cases of that formula are FROZEN in the
   the frozen oracle registry as ``BD-BB84-N1-ZERO``, ``BD-BB84-N2``,
   ``BD-BB84-N3`` and ``BD-BB84-PZ-QUARTER-N2``; the values are restated here as
   literals with their derivation, and the registry is not imported, so that
   this file is a second opinion rather than a second reading.

3. **The exact window is OPT-IN, and its opt-in-ness is the safety
   property.** A declaration carrying no depth is governed by Eq.
   ``eq:pmcdef`` alone, expression for expression (Definition ``def:pmc``,
   last paragraph; Theorem ``thm:exact-and-evaluated`` (v)). A test suite
   that only checked the new path would not notice the exact window silently
   raising every number of Eq. ``eq:pmcdef``, which is the failure mode
   ``BD-BB84-N1-ZERO`` was frozen against: "AN IMPLEMENTATION THAT SILENTLY
   RAISED A ZERO BOUND TO SOMETHING POSITIVE WOULD BE UNSAFE AND WOULD LOOK
   LIKE AN IMPROVEMENT."
"""

from __future__ import annotations

from fractions import Fraction as F

import pytest
from instances.common.errors import OpticalReceiverError
from instances.common.optics import (
    DECLARED_EXACT_WINDOW_TOLERANCES,
    DECLARED_TOLERANCES,
    PORTS,
    ReceiverParameters,
    analytic_port_grams,
    receiver_request,
)

from certiqs_key.receiver.construct import construct_receiver
from certiqs_key.receiver.settings import OFF_SETTING

#: The float evaluation's own noise floor. ``receiver`` Theorem
#: ``thm:exact-and-evaluated`` (ii) asserts NO BOUND between its emitted floats and the
#: exact quantities, so this is a measurement of this device on this build and not a
#: guarantee: the largest deviation observed across the cases below is ~4.4e-16.
FLOAT_NOISE = 1e-12


def _artifact(parameters: ReceiverParameters):  # noqa: ANN202 - module's own type
    """Build the receiver, or fail with the module's own refusal reason."""
    emission = construct_receiver(receiver_request(parameters))
    if emission.artifact is None:
        refusal = emission.refusal
        assert refusal is not None
        pytest.fail(f"receiver refused: {refusal.reason}: {refusal.detail}")
    return emission.artifact


def _emitted_p_mc(parameters: ReceiverParameters) -> float:
    """Return the single ``(MC_K, p_mc)`` entry's weight."""
    entries = _artifact(parameters).high_photon_bounds.entries
    assert len(entries) == 1, "the declaration has exactly one strengthening entry"
    return entries[0].weight


def _closed_form_p_mc(split: F, cutoff: int) -> F:
    """Return ``max{0, beta(N+1)}`` of Eq. ``eq:bb84beta`` at this receiver.

    DERIVATION (not a restatement of the implementation). This receiver declares
    ``Inp_S`` empty, so ``T = {off}`` by Corollary ``cor:unconditioned-family``
    and predicate (X) holds, that setting's exact flag being set there.
    Definition ``def:bounddata`` then has ``gamma = beta_k = 1`` and
    ``A_Sigma = 1``, so ``c = 1 - lmax(A_Sigma) = 0`` and the ``c^n`` term of
    Eq. ``eq:beta`` vanishes identically. Each port's
    ``A_Sigma - A_k = 1 - w_k P_k`` has ``lmin = 1 - w_k``, so ``d_k = w_k``,
    and the four weights are ``(x, x, 1-x, 1-x)``. Hence

        beta(n) = 1 - 2 x^n - 2 (1-x)^n ,

    and Definition ``def:pmc`` branch 1 emits ``max{0, beta(N+1)}``.
    """
    n = cutoff + 1
    return max(F(0), 1 - 2 * split**n - 2 * (1 - split) ** n)


# ===========================================================================
#  1. The compiled graph is the declared device.
# ===========================================================================


@pytest.mark.parametrize(
    "parameters",
    [
        ReceiverParameters(),
        ReceiverParameters(basis_split=F(1, 4)),
        ReceiverParameters(efficiency=(F(9, 10), F(4, 5), F(1), F(1, 2))),
    ],
    ids=["ideal", "unbalanced-split", "unequal-efficiency"],
)
def test_the_compiled_graph_reproduces_the_analytic_port_grams(
    parameters: ReceiverParameters,
) -> None:
    """``A_k = eta_k w_k P_k``, from the optics, against the compiled graph."""
    emitted = dict(_artifact(parameters).port_grams)
    for label, expected in analytic_port_grams(parameters):
        measured = emitted[label]
        for row, expected_row in enumerate(expected):
            for column, entry in enumerate(expected_row):
                assert abs(complex(measured[row][column]) - float(entry)) < FLOAT_NOISE


def test_the_port_grams_are_declared_in_the_declared_port_order() -> None:
    """The order is load-bearing: 1-based click patterns are read off it."""
    labels = tuple(label for label, _gram in _artifact(ReceiverParameters()).port_grams)
    assert labels == tuple(label for label, _modes in PORTS)


def test_the_analytic_cross_check_refuses_a_device_it_is_not_stated_for() -> None:
    """A closed form that quietly returned ideal values would compare nothing."""
    with pytest.raises(OpticalReceiverError, match="cos 4theta"):
        analytic_port_grams(ReceiverParameters(half_wave_angle=F(1, 16)))
    with pytest.raises(OpticalReceiverError, match="perfect polarizing"):
        analytic_port_grams(ReceiverParameters(pbs_leak_transmitted=F(1, 10)))
    with pytest.raises(OpticalReceiverError, match="perfect polarizing"):
        analytic_port_grams(ReceiverParameters(pbs_leak_reflected=F(1, 10)))


# ===========================================================================
#  2. p_mc against the closed form, and against the four frozen cases.
# ===========================================================================


@pytest.mark.parametrize(
    ("split", "cutoff"),
    [
        (F(1, 2), 1),
        (F(1, 2), 2),
        (F(1, 2), 3),
        (F(1, 4), 1),
        (F(1, 4), 2),
        (F(3, 4), 2),
        (F(1, 8), 2),
    ],
)
def test_the_emitted_p_mc_is_the_closed_form(split: F, cutoff: int) -> None:
    """Eq. ``eq:bb84beta`` evaluated exactly, against the emitted float."""
    parameters = ReceiverParameters(basis_split=split, photon_cutoff=cutoff)
    assert abs(_emitted_p_mc(parameters) - float(_closed_form_p_mc(split, cutoff))) < (
        FLOAT_NOISE
    )


@pytest.mark.oracle
@pytest.mark.parametrize(
    ("split", "cutoff", "frozen", "case"),
    [
        # beta(2) = 1 - 2(1/2)^2 - 2(1/2)^2 = 0. The bound is VALID and USELESS,
        # and Definition def:pmc's positive part is what keeps it valid.
        (F(1, 2), 1, F(0), "BD-BB84-N1-ZERO"),
        # beta(3) = 1 - 2^{2-3} = 1/2.
        (F(1, 2), 2, F(1, 2), "BD-BB84-N2"),
        # beta(4) = 1 - 2^{2-4} = 3/4.
        (F(1, 2), 3, F(3, 4), "BD-BB84-N3"),
        # beta(3) = 1 - 2(1/4)^3 - 2(3/4)^3 = 1 - 2/64 - 54/64 = 1/8.
        (F(1, 4), 2, F(1, 8), "BD-BB84-PZ-QUARTER-N2"),
    ],
)
def test_the_closed_form_reproduces_the_frozen_bound_data_cases(
    split: F, cutoff: int, frozen: F, case: str
) -> None:
    """The four ``BD-BB84-*`` values, restated from the derivation not the file.

    The registry is deliberately NOT imported. These are the numbers a reader
    can recompute from Eq. ``eq:bb84beta`` with a pencil, and their agreement
    with the frozen cases is what makes this instance's device the one Example
    ``ex:bb84bound`` is about.
    """
    assert _closed_form_p_mc(split, cutoff) == frozen, case


def test_the_default_device_at_cutoff_one_bounds_the_flag_weight_by_nothing() -> None:
    """Pinned so it cannot regress silently.

    At ``N = 1`` the analytic bound is exactly zero, so nothing in the docked
    declaration bounds the target state's weight on the deterministic-click flag
    sectors -- which is why the slice returned ``h_low = 0`` before the exact
    window. This asserts the DIAGNOSIS, not a defect: the value is correct and
    the exact window is what makes it useful.
    """
    assert _emitted_p_mc(ReceiverParameters(photon_cutoff=1)) < FLOAT_NOISE


# ===========================================================================
#  3. The exact window: opt-in, and what opting in buys.
# ===========================================================================


def test_a_declaration_without_a_depth_emits_the_def_pmc_value() -> None:
    """Def. ``def:pmc``, last paragraph: Eq. eq:pmcdef, expression for expression.

    Asserted through the artifact's OWN report of which definition produced the
    value, not inferred from the number: two definitions can agree on a number
    and still be different claims, and Requirement ``req:weight-provenance`` asks
    the artifact to say which one ran.
    """
    for cutoff in (1, 2, 3):
        row = _artifact(
            ReceiverParameters(photon_cutoff=cutoff)
        ).bound_quantifier_domain.per_setting[0]
        assert row.definition == "def:pmc"
        assert row.assumption_eig_invoked is False
        assert row.exact_window is None


@pytest.mark.parametrize(
    ("cutoff", "depth", "expected"),
    [
        # beta(2) = 0 is replaced by the exact lmin of the two-photon multiclick
        # block, 1/2. The weight is the enclosed one
        # (receiver/def:enclosed-weight: l(n) = max{beta(n), w(n)}, no
        # eps_eig), so the emitted value is 1/2 rounded down.
        (1, 2, 0.5),
        # At N = 2 the window value 0.8125 - eps beats the tail beta(4) = 3/4,
        # so the MINIMUM is the tail and the emitted value is unchanged at 3/4.
        (2, 3, 0.75),
    ],
)
def test_the_exact_window_emits_the_window_tail_minimum(
    cutoff: int, depth: int, expected: float
) -> None:
    """``l(n) = max{beta(n), w(n)}`` (enclosed), then min with the tail."""
    parameters = ReceiverParameters(photon_cutoff=cutoff, exact_window=depth)
    assert abs(_emitted_p_mc(parameters) - expected) < FLOAT_NOISE
    assert _emitted_p_mc(parameters) <= expected
    row = _artifact(parameters).bound_quantifier_domain.per_setting[0]
    assert row.definition == "def:pmcex"
    assert row.evaluation == "rigorous"
    assert row.assumption_eig_invoked is False


def test_the_exact_window_never_emits_less_than_the_analytic_bound() -> None:
    """Proposition ``prop:exactnoworse``, on this device at four settings.

    ``ell(n) >= beta(n)`` pointwise by Eq. ``eq:elldef``'s ``max``, and the tail
    is the same term on both routes, so opting in cannot lose bound. This is the
    property that makes the depth safe to declare without re-deciding it per
    device.
    """
    for split in (F(1, 2), F(1, 4)):
        for cutoff in (1, 2):
            without = _emitted_p_mc(
                ReceiverParameters(basis_split=split, photon_cutoff=cutoff)
            )
            with_depth = _emitted_p_mc(
                ReceiverParameters(
                    basis_split=split, photon_cutoff=cutoff, exact_window=cutoff + 1
                )
            )
            assert with_depth >= without - FLOAT_NOISE


def test_the_window_record_makes_eq_elldef_recomputable() -> None:
    """Requirement ``req:exact-window-record``: the cost of eps_eig is visible.

    The row carries ``beta(n)``, ``beta*(n)`` and the ``ell`` the inequality
    used, so a reader can recompute the max rather than trust the result of it.
    """
    parameters = ReceiverParameters(photon_cutoff=1, exact_window=2)
    record = _artifact(parameters).bound_quantifier_domain.per_setting[0].exact_window
    assert record is not None
    assert record.depth == 2
    ((photons, analytic, exact, ell),) = record.rows
    assert photons == 2
    assert analytic < FLOAT_NOISE  # beta(2) = 0
    assert abs(exact - 0.5) < FLOAT_NOISE  # beta*(2) = lmin = 1/2
    assert ell == max(analytic, exact - DECLARED_EXACT_WINDOW_TOLERANCES["eps_eig"])


# ===========================================================================
#  The request itself: which keys, and exactly where.
# ===========================================================================


def test_the_two_conditional_tolerances_travel_with_the_depth_and_only_then() -> None:
    """``eps_6`` and ``eps_eig`` are REQUIRED with a depth and REFUSED without.

    So they cannot sit in :data:`DECLARED_TOLERANCES`, and the assertion is that
    they are added exactly where the depth is -- in both directions, because a
    tolerance declared unconditionally would make every no-depth run refuse.
    """
    conditional = frozenset(DECLARED_EXACT_WINDOW_TOLERANCES)
    assert conditional.isdisjoint(DECLARED_TOLERANCES)

    plain = receiver_request(ReceiverParameters(photon_cutoff=1))
    assert plain.exact_window == {}
    assert frozenset(plain.numerical_tolerances) == frozenset(DECLARED_TOLERANCES)

    deep = receiver_request(ReceiverParameters(photon_cutoff=1, exact_window=2))
    assert deep.exact_window == {OFF_SETTING: 2}
    assert frozenset(deep.numerical_tolerances) == (
        frozenset(DECLARED_TOLERANCES) | conditional
    )


def test_the_declared_eps_eig_is_positive_and_costs_in_the_safe_direction() -> None:
    """Assumption ``ass:eig`` at zero would read "the routine never overshoots".

    That is false of a floating ``eigvalsh``, so this instance declares a sized
    slack instead. The whole cost of the choice is that ``ell`` is ``eps_eig``
    below the computed eigenvalue -- downward, which is the safe direction.
    """
    assert DECLARED_EXACT_WINDOW_TOLERANCES["eps_eig"] > 0
    parameters = ReceiverParameters(photon_cutoff=1, exact_window=2)
    record = _artifact(parameters).bound_quantifier_domain.per_setting[0].exact_window
    assert record is not None
    ((_photons, _analytic, exact, ell),) = record.rows
    assert ell < exact


# ===========================================================================
#  The domains this instance owns, refused where it writes them.
# ===========================================================================


def test_a_depth_at_or_below_the_cutoff_is_refused_where_it_is_written() -> None:
    """Definition ``def:pmcex`` needs ``m* > N``; below it the window is empty."""
    for depth in (0, 1, 2):
        with pytest.raises(OpticalReceiverError, match="must exceed"):
            ReceiverParameters(photon_cutoff=2, exact_window=depth)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("basis_split", 0.5, "exact rational"),
        ("half_wave_angle", 0.125, "exact rational"),
        ("basis_split", F(3, 2), r"\[0, 1\]"),
        ("pbs_leak_transmitted", F(3, 4), r"transmitted leak .* \[0, 1/2\]"),
        ("pbs_leak_reflected", F(3, 4), r"reflected leak .* \[0, 1/2\]"),
        ("pbs_leak_reflected", -F(1, 4), r"reflected leak .* \[0, 1/2\]"),
        ("photon_cutoff", -1, "non-negative"),
    ],
)
def test_a_parameter_outside_its_domain_is_refused(
    field: str, value: object, message: str
) -> None:
    """A float would be widened silently into the nearest binary rational."""
    with pytest.raises(OpticalReceiverError, match=message):
        ReceiverParameters(**{field: value})  # type: ignore[arg-type]
