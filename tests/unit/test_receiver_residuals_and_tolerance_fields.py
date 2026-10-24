"""The receiver's code behaviours read off claims.

Each test reads its expectation off a claim:

* ``receiver/def:tolmap`` (iv) and ``def:bounddata``: of Eq. ``eq:bounddata``
  only ``0 <= c`` is decided on computed data, at ``-eps_2``; "the remaining
  inequalities ... are not separately tested and no threshold decides them".
* ``receiver/req:residual-refusal``: every residual that exists, and the
  residual gap of a declared window, refuse above their tolerances.
* ``receiver/req:residual-emission``: ``eps_6`` exists exactly where an
  exact-window depth is declared, as ``r_6`` does.
* ``receiver/req:reserved-tolerance-field``: the reserved tolerance field of
  EVERY declared parameter -- ``ass:exact``: "every declared component
  parameter, efficiency, dark-count probability and probe mean photon
  number" -- is admitted only absent or exactly zero.
"""

from __future__ import annotations

from dataclasses import replace
from fractions import Fraction

import pytest
from receiver_povm_support import TOLERANCE, bb84_channel_only_request

from certiqs_key.receiver import construct_receiver
from certiqs_key.receiver.artifact import ResidualGap
from certiqs_key.receiver.bound import (
    BoundData,
    check_bound_data,
    check_bound_data_admissible,
)
from certiqs_key.receiver.construct import emitted_residuals
from certiqs_key.receiver.errors import HypothesisError
from certiqs_key.receiver.reasons import RefusalReason
from certiqs_key.receiver.request import ValidatedRequest, validate_request
from certiqs_key.receiver.residuals import Residual, check_residuals
from certiqs_key.receiver.settings import ProbeDeclaration, ProbeSetting

# ---------------------------------------------------------------------------
#  def:tolmap (iv): one decided inequality, the others not tested
# ---------------------------------------------------------------------------


def test_the_redundant_inequalities_of_eq_bounddata_are_not_tested() -> None:
    """``gamma <= beta_k <= 1`` and ``c <= d_k <= 1`` decide nothing here.

    Each tuple below violates one of them by far more than any eps_2, and
    check_bound_data passes every one (it does not assert them at an
    eps_2-widened window): def:tolmap (iv) says no threshold decides
    them.
    """
    violations = (
        BoundData(2, 1.0, (0.5, 1.0), 0.0, (0.5, 0.5)),  # beta_0 < gamma
        BoundData(2, 0.5, (1.5, 1.0), 0.0, (0.5, 0.5)),  # beta_0 > 1
        BoundData(2, 1.0, (1.0, 1.0), 0.75, (0.5, 0.5)),  # d_k < c
        BoundData(2, 1.0, (1.0, 1.0), 0.0, (1.5, 0.5)),  # d_0 > 1
        BoundData(2, -0.5, (1.0, 1.0), 0.0, (0.5, 0.5)),  # gamma < 0
    )
    for data in violations:
        check_bound_data(data)


def test_the_shape_of_the_bound_data_is_still_checked() -> None:
    with pytest.raises(HypothesisError):
        check_bound_data(BoundData(0, 1.0, (), 0.0, ()))
    with pytest.raises(HypothesisError):
        check_bound_data(BoundData(2, 1.0, (1.0,), 0.0, (0.5, 0.5)))


def test_zero_le_c_is_the_one_decided_part_and_it_refuses() -> None:
    eps_2 = float(TOLERANCE.eps_2)
    admitted = BoundData(2, 1.0, (1.0, 1.0), -eps_2, (0.5, 0.5))
    assert check_bound_data_admissible(admitted, eps_2) is None
    refused = BoundData(2, 1.0, (1.0, 1.0), -2 * eps_2, (0.5, 0.5))
    outcome = check_bound_data_admissible(refused, eps_2)
    assert outcome is not None
    assert outcome.reason is RefusalReason.BOUND_DATA_NOT_ADMISSIBLE


# ---------------------------------------------------------------------------
#  req:residual-refusal: residuals and gaps at one site
# ---------------------------------------------------------------------------


def _residual(value: float) -> Residual:
    return Residual("r_2", value, 0.5, "spectral")


def test_a_gap_above_eps_gap_is_refused_by_check_residuals() -> None:
    passing_gap = ResidualGap(setting="off", window=5, gap=0.25, tolerance=0.5)
    failing_gap = ResidualGap(setting="t1", window=5, gap=0.75, tolerance=0.5)
    assert check_residuals([_residual(0.25)], [passing_gap]) is None
    outcome = check_residuals([_residual(0.25)], [passing_gap, failing_gap])
    assert outcome is not None
    assert outcome.reason is RefusalReason.RESIDUAL_GAP_ABOVE_TOLERANCE
    assert "'t1'" in outcome.detail
    # The residuals are decided first: a failing residual names itself even
    # when a gap fails too.
    first = check_residuals([_residual(0.75)], [failing_gap])
    assert first is not None
    assert first.reason is not RefusalReason.RESIDUAL_GAP_ABOVE_TOLERANCE
    # Without gaps the verdict is the residuals' alone, as before.
    assert check_residuals([_residual(0.25)]) is None


# ---------------------------------------------------------------------------
#  req:residual-emission: no r_6 row without its eps_6
# ---------------------------------------------------------------------------


def test_the_residual_emission_requires_eps_6_where_a_depth_is_declared() -> None:
    validated = validate_request(bb84_channel_only_request())
    assert isinstance(validated, ValidatedRequest)
    assert validated.tolerances.eps_6 is None
    # A depth on a request whose validated tolerances carry no eps_6: a state
    # tolerances_from_declaration refuses, and the emission refuses to form
    # rows on it rather than write an r_6 with no declared bound.
    with_depth = replace(
        validated, request=replace(validated.request, exact_window={"off": 4})
    )
    with pytest.raises(HypothesisError, match="eps_6"):
        emitted_residuals(with_depth, None, None, None, {}, (), ())  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
#  req:reserved-tolerance-field: every declared parameter
# ---------------------------------------------------------------------------


def test_a_detector_layer_tolerance_is_refused() -> None:
    request = bb84_channel_only_request()
    first, *rest = request.detector_layer
    ported = replace(
        request,
        detector_layer=(
            replace(first, tolerances={"efficiency": Fraction(1, 1000)}),
            *rest,
        ),
    )
    emission = construct_receiver(ported)
    assert emission.artifact is None
    assert emission.refusal is not None
    assert emission.refusal.reason is RefusalReason.PARAMETER_TOLERANCE_NOT_ZERO
    assert "detector-layer row 'detector_layer.H'" in emission.refusal.detail
    assert "'efficiency'" in emission.refusal.detail
    assert "parameter uncertainty sets are out of scope" in emission.refusal.detail


def test_a_probe_setting_tolerance_is_refused() -> None:
    request = bb84_channel_only_request()
    (off,) = request.probe_declaration.settings
    probed = replace(
        request,
        probe_declaration=ProbeDeclaration(
            (replace(off, tolerances={"mean_photon_numbers": 1e-30}),)
        ),
    )
    emission = construct_receiver(probed)
    assert emission.artifact is None
    assert emission.refusal is not None
    assert emission.refusal.reason is RefusalReason.PARAMETER_TOLERANCE_NOT_ZERO
    assert "probe setting 'probe_declaration.off'" in emission.refusal.detail


def test_exactly_zero_fields_are_admitted_and_recorded_on_the_a_exact_row() -> None:
    request = bb84_channel_only_request()
    first, *rest = request.detector_layer
    (off,) = request.probe_declaration.settings
    zeroed = replace(
        request,
        detector_layer=(
            replace(first, tolerances={"dark_count_probability": 0}),
            *rest,
        ),
        probe_declaration=ProbeDeclaration(
            (ProbeSetting(off.label, off.mean_photon_numbers, tolerances={}),)
        ),
    )
    emission = construct_receiver(zeroed)
    assert emission.refusal is None and emission.artifact is not None
    rows = {str(row.assumption_id): row for row in emission.artifact.assumption_ledger}
    assert dict(rows["A-EXACT"].constrains)["declared_tolerance_fields"] == [
        "detector_layer.H.dark_count_probability"
    ]


def test_every_parameter_record_is_named_once() -> None:
    request = bb84_channel_only_request()
    names = [name for name, _ in request.parameter_records()]
    assert names == [
        "bs",
        "hwp",
        "route",
        "detector_layer.H",
        "detector_layer.V",
        "detector_layer.+",
        "detector_layer.-",
        "probe_declaration.off",
    ]
