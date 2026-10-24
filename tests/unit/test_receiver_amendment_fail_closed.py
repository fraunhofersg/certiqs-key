"""The registry-0.2.0 amendment's structural fail-closed properties.

STRUCTURAL, NOT REPLAYS. What is on trial here is that the PROPERTIES the
amendment adds hold for data the freeze never saw, and that the five things the
contract says are never done are not done anywhere in the package:

1. NO TOLERANCE IS DEFAULTED. Every one of the declared six is required, on
   every route, and no member has a default anywhere.
2. ``c`` IS NEVER CLAMPED. An admitted negative ``c`` enters Eq. ``eq:beta`` as
   it stands (Def. ``def:tolmap`` (iv); Rem. ``rem:cdirection``).
3. ``r_min`` IS NEVER MODIFIED, and ``rbar`` is never floored at 0
   (``interface.yaml`` ``outputs.dark_count_channel``; Req.
   ``req:dark-channel-record``; Rem. ``rem:d2slack``).
4. ``r_1`` AND ``r_3`` ARE ABSENT ON ROUTE (i) -- absent, never zero
   (Req. ``req:residual-emission``).
5. EVERY REFUSAL IS A RECORD NAMING ITS CHECK, and a refusal emits NO artifact
   (the ``fail_closed`` convention).

The per-case evidence is replayed against the registry in
``tests/golden/test_receiver_povm_*_against_registry.py``; nothing here reads a
frozen expected value except the declared tolerance fixture.
"""

from __future__ import annotations

import inspect
from dataclasses import replace
from fractions import Fraction as F

import numpy as np
import pytest
from receiver_povm_support import (
    TOLERANCE,
    bb84_channel_only_request,
    probe_receiver_request,
)
from registry_receiver_povm import TOLERANCE_FIXTURE_0_3_0, is_superseded_0_3_0

from certiqs_key.receiver import (
    TOLERANCE_KEYS,
    BoundData,
    DarkCountChannel,
    DarkCountRoute,
    GramFamily,
    NumericalTolerances,
    ReceiverRequest,
    Refusal,
    RefusalReason,
    bound_function,
    capped_coefficient,
    check_dark_channel,
    composition_correction,
    construct_receiver,
    minimum_multiclick_mass,
    port_grams,
    restrict_to_inputs,
)
from certiqs_key.receiver.graph import compile_element_graph


def _route_one_request(**overrides: object) -> ReceiverRequest:
    """Return a route-(i) request: the BB84 Grams, declared directly."""
    seed = bb84_channel_only_request(photon_cutoff=1)
    assert seed.element_graph is not None
    gamma = compile_element_graph(seed.element_graph, len(seed.mode_space))
    gamma_inp = restrict_to_inputs(gamma, seed.input_modes.subsystem_order())
    rows = [modes for _, modes in seed.port_map.entries]
    family = GramFamily(seed.port_map.labels, port_grams(gamma_inp, rows))
    return replace(seed, element_graph=None, port_grams=family, **overrides)


# ---------------------------------------------------------------------------
#  1. no tolerance is defaulted
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_every_one_of_the_six_is_required_on_every_route() -> None:
    """The inputs table: declared, never defaulted, including the unused two."""
    assert TOLERANCE_KEYS == ("eps_1", "eps_2", "eps_3", "eps_4", "eps_5", "eps_gap")
    builders = (
        bb84_channel_only_request(),
        probe_receiver_request(),
        _route_one_request(),
    )
    for request in builders:
        for missing in TOLERANCE_KEYS:
            declared = {
                key: value
                for key, value in request.numerical_tolerances.items()
                if key != missing
            }
            emission = construct_receiver(
                replace(request, numerical_tolerances=declared)
            )
            assert emission.artifact is None, missing
            assert emission.refusal is not None
            assert emission.refusal.reason is (
                RefusalReason.NUMERICAL_TOLERANCE_MISSING
            ), missing
            assert missing in emission.refusal.detail, missing


@pytest.mark.contract
def test_the_tolerance_type_and_its_consumers_carry_no_default() -> None:
    """A default anywhere would be a substituted datum."""
    for field in NumericalTolerances.__dataclass_fields__.values():
        assert repr(field.default).startswith("<dataclasses._MISSING"), field.name
        assert repr(field.default_factory).startswith("<dataclasses._MISSING")
    # No function of the package takes a tolerance with a default value.
    from certiqs_key.receiver import bound, catalogue, dark, grams, numerics, residuals

    for module in (bound, catalogue, dark, grams, numerics, residuals):
        for _, obj in inspect.getmembers(module, inspect.isfunction):
            if obj.__module__ != module.__name__:
                continue
            for name, parameter in inspect.signature(obj).parameters.items():
                if name in {"tolerances", "tolerance", "epsilon"}:
                    assert parameter.default is inspect.Parameter.empty, (
                        module.__name__,
                        obj.__name__,
                    )


# ---------------------------------------------------------------------------
#  2. c is never clamped
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_an_admitted_negative_c_enters_eq_beta_unchanged() -> None:
    """Def. def:tolmap (iv): "the computed c enters eq:beta EXACTLY AS IT STANDS".

    Checked on data the freeze never saw: for every admitted ``c`` in
    ``[-eps_2, 0)`` the evaluated ``beta(1)`` is STRICTLY BELOW its value at
    ``c = 0``, which a clamped evaluation could not produce.
    """
    for numerator in (1, 2, 5, 9, 10):
        c = -numerator * TOLERANCE.eps_2 / 10.0
        data = BoundData(3, 1.0, (1.0, 1.0, 1.0), c, (0.5, 0.5, 0.5))
        at_zero = BoundData(3, 1.0, (1.0, 1.0, 1.0), 0.0, (0.5, 0.5, 0.5))
        assert bound_function(data, 1) < bound_function(at_zero, 1)
        # ... and strictly ABOVE at even n, which is the other half of
        # rem:cdirection and the half a one-sided description would hide.
        assert bound_function(data, 2) > bound_function(at_zero, 2)
        # The deficit and the excess are the stated magnitudes.
        assert bound_function(at_zero, 1) - bound_function(data, 1) == pytest.approx(
            2.0 * abs(c), abs=1e-15
        )
        assert bound_function(data, 2) - bound_function(at_zero, 2) == pytest.approx(
            2.0 * c * c, abs=1e-15
        )


# ---------------------------------------------------------------------------
#  3. r_min is never modified and rbar is never floored
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_r_min_is_emitted_as_computed_and_rbar_is_only_capped() -> None:
    """`outputs.dark_count_channel` and Rem. rem:d2slack, on unfrozen channels."""
    for mass in (-0.5, -1e-9, 0.0, 0.25, 1.0, 1.5, 7.0):
        assert capped_coefficient(mass) == min(mass, 1.0)
        # NOT FLOORED: a negative coefficient survives.
        if mass < 0.0:
            assert capped_coefficient(mass) == mass
            assert capped_coefficient(mass) < 0.0
        # 1 - rbar >= 0 always, which is the whole of the work eq:rbar does.
        assert 1.0 - capped_coefficient(mass) >= 0.0
        # rbar <= r_min and rbar <= 1, both sides of eq:rbar.
        assert capped_coefficient(mass) <= mass
        assert capped_coefficient(mass) <= 1.0


@pytest.mark.contract
def test_the_emitted_dark_record_reports_and_never_repairs() -> None:
    """The emitted r_min is Eq. eq:rmin's value and the record is complete."""
    emission = construct_receiver(
        bb84_channel_only_request(dark_counts=(F(1, 10), F(1, 5), 0, 0))
    )
    assert emission.artifact is not None
    record = emission.artifact.dark_count_channel
    channel = emission.artifact  # for readability below
    del channel
    assert record.route is DarkCountRoute.PER_PORT_PRODUCT_FORM
    assert record.delta_dc == 0.0
    assert record.r_bar == min(record.r_min, 1.0)
    assert record.conditions_derived == ("D1", "D2")
    assert record.conditions_checked == ()
    assert "eq:darkpmcslack" in record.composition_rule
    payload = emission.artifact.as_payload()["dark_count_channel"]
    assert isinstance(payload, dict)
    assert set(payload) >= {"r_min", "r_bar", "delta_dc", "route", "composition_rule"}


@pytest.mark.contract
def test_delta_dc_follows_the_route_and_not_the_channel() -> None:
    """Eq. eq:darkdelta is a two-case definition ON THE ROUTE."""
    for ports in (1, 2, 4, 7):
        assert (
            composition_correction(
                DarkCountRoute.PER_PORT_PRODUCT_FORM, ports, TOLERANCE
            )
            == 0.0
        )
        assert composition_correction(
            DarkCountRoute.DECLARED_MATRIX, ports, TOLERANCE
        ) == pytest.approx(TOLERANCE.eps_4 + (ports + 1) * TOLERANCE.eps_2)
    # A DECLARED channel that uses NO slack at all still carries the term.
    identity_channel = DarkCountChannel(
        2,
        DarkCountRoute.DECLARED_MATRIX,
        {
            frozenset(): {frozenset(): 1.0},
            frozenset({0}): {frozenset({0}): 1.0},
            frozenset({1}): {frozenset({1}): 1.0},
            frozenset({0, 1}): {frozenset({0, 1}): 1.0},
        },
    )
    assert check_dark_channel(identity_channel, TOLERANCE) is None
    assert minimum_multiclick_mass(identity_channel) == 0.0
    assert (
        composition_correction(
            identity_channel.route, identity_channel.port_count, TOLERANCE
        )
        > 0.0
    )


# ---------------------------------------------------------------------------
#  4. r_1 and r_3 are absent on route (i)
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_route_one_emits_no_key_for_r_1_or_r_3() -> None:
    """Def. def:residuals: "absent, not zero"."""
    emission = construct_receiver(_route_one_request())
    assert emission.artifact is not None
    rows = emission.artifact.validation_results.residuals
    identifiers = [row.residual_id for row in rows]
    assert set(identifiers) == {"r_2", "r_4", "r_5"}
    assert "r_1" not in identifiers
    assert "r_3" not in identifiers
    # AND THE WIRE FORM CARRIES NO KEY FOR EITHER: a consumer reading the
    # payload sees no row, rather than a row whose value is 0.
    payload = emission.artifact.as_payload()["validation_results"]
    assert isinstance(payload, dict)
    emitted = {row["residual"] for row in payload["residuals"]}  # type: ignore[index]
    assert emitted == {"r_2", "r_4", "r_5"}
    # On a route that DOES supply a Gamma, all five exist.
    other = construct_receiver(bb84_channel_only_request())
    assert other.artifact is not None
    assert {row.residual_id for row in other.artifact.validation_results.residuals} == {
        "r_1",
        "r_2",
        "r_3",
        "r_4",
        "r_5",
    }


# ---------------------------------------------------------------------------
#  5. every refusal is a record naming its check, and emits no artifact
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_every_amendment_refusal_is_a_record_with_no_artifact() -> None:
    """The `fail_closed` convention, on the conditions the amendment adds.

    THE DECLARED TUPLE IS THE REGISTRY-0.3.0 EIGHT. ``TOLERANCE_FIXTURE_0_2_0``
    is marked in ``SUPERSEDED_BY_0_3_0`` -- as the enumeration of a SIX-member
    tuple, not as a value -- and this file is repointed at its replacement
    rather than silently left on it. The declarations below carry no
    ``exact_window`` depth, so the two conditionally required members are
    supplied and UNUSED, which the inputs table admits exactly as it admits an
    unused ``eps_1`` on route (i).
    """
    assert is_superseded_0_3_0("TOLERANCE_FIXTURE_0_2_0")
    base = bb84_channel_only_request()
    cases: list[tuple[str, object, RefusalReason]] = [
        (
            "a tolerance outside [0, 1)",
            replace(
                base,
                numerical_tolerances=dict(TOLERANCE_FIXTURE_0_3_0) | {"eps_2": F(1)},
            ),
            RefusalReason.TOLERANCE_OUTSIDE_DECLARED_DOMAIN,
        ),
        (
            "a missing declared tolerance",
            replace(
                base,
                numerical_tolerances={
                    key: value
                    for key, value in TOLERANCE_FIXTURE_0_3_0.items()
                    if key != "eps_5"
                },
            ),
            RefusalReason.NUMERICAL_TOLERANCE_MISSING,
        ),
    ]
    for description, request, reason in cases:
        emission = construct_receiver(request)  # type: ignore[arg-type]
        assert emission.artifact is None, description
        assert emission.refusal is not None, description
        assert emission.refusal.reason is reason, description
        assert emission.refusal.detail.strip(), description
        assert isinstance(emission.refusal, Refusal)
        assert not isinstance(emission.refusal, BaseException)
        record = emission.refusal.as_machine_record()
        assert record["reason"] == str(reason)


@pytest.mark.contract
def test_bound_data_inadmissibility_refuses_and_never_raises() -> None:
    """Def. def:tolmap (iv) at the REQUEST boundary, under `fail_closed`.

    Item (v) admits route (ii) at eps_1 while item (iv) decides c = 1 - lmax(B)
    at eps_2, and Rem. rem:bound-data-band says an eps_1-admitted Gamma does not
    thereby satisfy any test stated at eps_2. So a declarer with eps_1 > eps_2
    -- the ordinary case, since the contract tells one who wants a single slack
    to declare eps_1 = eps_2 -- can supply a Gamma this module admits and bound
    data item (iv) does not.  `fail_closed` makes that a REFUSAL with a
    machine-readable reason and no artifact; construct_receiver must not
    propagate a HypothesisError.
    """
    from certiqs_key.receiver.numerics import lambda_max

    seed = bb84_channel_only_request(photon_cutoff=1)
    assert seed.element_graph is not None
    compiled = compile_element_graph(seed.element_graph, len(seed.mode_space))
    scaled = np.asarray(np.sqrt(1.4) * compiled, dtype=np.complex128)
    request = replace(
        seed,
        element_graph=None,
        instrument_matrix=scaled,
        numerical_tolerances=dict(TOLERANCE_FIXTURE_0_3_0) | {"eps_1": F(1, 2)},
    )
    # Item (v) ADMITS it: lmax(Gamma^dagger Gamma) = 1.4 <= 1 + eps_1 = 1.5.
    assert lambda_max(scaled.conj().T @ scaled) <= 1.5
    # Item (iv) does NOT: c = 1 - lmax(A_Sigma) < -eps_2.
    gamma_inp = restrict_to_inputs(scaled, seed.input_modes.subsystem_order())
    rows = [modes for _, modes in seed.port_map.entries]
    family = GramFamily(seed.port_map.labels, port_grams(gamma_inp, rows))
    a_sigma = sum(family.matrices[1:], family.matrices[0])
    assert 1.0 - lambda_max(a_sigma) < -float(TOLERANCE_FIXTURE_0_3_0["eps_2"])

    emission = construct_receiver(request)  # MUST NOT RAISE
    assert emission.artifact is None
    assert emission.refusal is not None
    assert isinstance(emission.refusal, Refusal)
    assert not isinstance(emission.refusal, BaseException)
    assert emission.refusal.detail.strip()


@pytest.mark.contract
def test_a_declared_channel_beside_dark_counts_refuses_the_whole_request() -> None:
    """Req. req:dark-route-exclusive, at the REQUEST boundary, not only the checker."""
    declared = DarkCountChannel(
        4,
        DarkCountRoute.DECLARED_MATRIX,
        {
            frozenset(pattern): {frozenset(pattern): 1.0}
            for pattern in (
                (),
                *((index,) for index in range(4)),
                *(tuple(sorted({a, b})) for a in range(4) for b in range(4) if a < b),
                (0, 1, 2),
                (0, 1, 3),
                (0, 2, 3),
                (1, 2, 3),
                (0, 1, 2, 3),
            )
        },
    )
    request = bb84_channel_only_request(dark_counts=(F(1, 10), 0, 0, 0))
    emission = construct_receiver(replace(request, dark_count_channel=declared))
    assert emission.artifact is None
    assert emission.refusal is not None
    assert emission.refusal.reason is RefusalReason.DARK_COUNT_CHANNEL_DECLARED_TWICE
    # And with every p_dc|k = 0 the declared route is taken and admitted.
    clean = bb84_channel_only_request(dark_counts=(0, 0, 0, 0))
    admitted = construct_receiver(replace(clean, dark_count_channel=declared))
    assert admitted.artifact is not None
    assert admitted.artifact.dark_count_channel.route is DarkCountRoute.DECLARED_MATRIX
    assert admitted.artifact.dark_count_channel.delta_dc > 0.0


@pytest.mark.contract
def test_a_block_failing_positivity_refuses_and_is_not_repaired() -> None:
    """Def. def:residuals: refuse-only, with the contract's own reason."""
    from certiqs_key.receiver import block_positivity_residual, check_residuals

    block = np.asarray([[0.75, 0.0], [0.0, -0.125]], dtype=np.complex128)
    before = block.copy()
    residual = block_positivity_residual([{"mc": block}], TOLERANCE)
    outcome = check_residuals((residual,))
    assert isinstance(outcome, Refusal)
    assert outcome.reason is (
        RefusalReason.PHOTON_BLOCK_POSITIVITY_RESIDUAL_ABOVE_TOLERANCE
    )
    assert np.array_equal(block, before)
