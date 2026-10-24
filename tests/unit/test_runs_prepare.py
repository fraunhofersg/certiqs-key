"""``prepare``: everything that needs no oracle, on the path a run takes.

The property that carries the file is not that ``prepare`` returns the right things --
it is that it returns THE SAME things a run does, because the two share one code path
and a preparation that could drift from the run it prepares is worse than none.

The device route is exercised in ``tests/integration/test_optical_bb84_slice.py``,
where a prologue is affordable; here the direct finite route is, because it is
the one that needs no receiver and runs in milliseconds.
"""

from __future__ import annotations

from fractions import Fraction as F

import pytest
from instances.bb84.specification import bb84_specification
from instances.common.honest.depolarized_bell_pair import raw_joint_provider

from certiqs_key.meat_core.declaration.declaration import KeyLengthParameters
from certiqs_key.protocol_compiler import acceptance_fibres
from certiqs_key.runs import RunConfig
from certiqs_key.runs.flow import STAGE_ORDER, StageStatus
from certiqs_key.runs.pipeline import Preparation, prepare

pytestmark = pytest.mark.contract

QBER = F(1, 50)


def specification():
    return bb84_specification(F(1, 2), F(1, 2), F(1, 2), F(1, 2))


def config(**changes: object) -> RunConfig:
    base = {
        "rounds": 10_000,
        "completeness_budget": F(1, 1_000_000),
        "parameters": KeyLengthParameters(
            alpha=1.5, eps_pa=2.0**-30, eps_ev=2.0**-30, lambda_ec=0
        ),
        "declared_tolerance": 0.0,
        "model": {"qber": QBER},
    }
    return RunConfig(**{**base, **changes})  # type: ignore[arg-type]


def prepared() -> Preparation:
    outcome = prepare(
        config(),
        specification=specification(),
        raw_joint_provider=raw_joint_provider(QBER),
    )
    assert isinstance(outcome, Preparation), outcome
    return outcome


# ===========================================================================
#  What a preparation returns
# ===========================================================================


def test_the_acceptance_alphabet_is_available_before_the_run() -> None:
    """The acceptance alphabet is the datum a caller building a table needs first."""
    result = prepared()
    assert result.acceptance_alphabet == ("gen", "ok", "err", "disc")
    assert result.acceptance_alphabet == result.declaration.acceptance_alphabet


def test_the_route_without_a_device_reports_null_and_not_a_missing_key() -> None:
    """One shape for every instance.

    An instance that lacks a stage sets the key to null; it never uses a
    differently shaped key, so a consumer reads one record on every route.
    """
    result = prepared()
    assert result.receiver_artifact is None
    assert result.reduction_artifact is None
    assert result.rows_adaptation is None


def test_no_oracle_is_taken_and_no_solve_happens() -> None:
    """``prepare`` has no oracle parameter at all; ``run_slice`` requires one."""
    import inspect

    from certiqs_key.runs.pipeline import run_slice

    assert "oracle" not in inspect.signature(prepare).parameters
    assert "oracle" in inspect.signature(run_slice).parameters


# ===========================================================================
#  The raw X x V table
# ===========================================================================


def test_the_raw_table_is_over_the_outcome_pairs_and_is_exact() -> None:
    """Before any coarse-graining, and as exact rationals."""
    result = prepared()
    table = result.raw_joint_distribution
    assert table is not None
    declaration = result.declaration
    assert set(table) == {
        (x, v) for x in declaration.alice_alphabet for v in declaration.bob_alphabet
    }
    assert all(isinstance(value, F) for value in table.values())
    assert sum(table.values(), F(0)) == 1


def test_the_coarse_distribution_is_the_raw_one_summed_over_its_fibres() -> None:
    """THE PROPERTY THAT MAKES THE RAW TABLE THE RIGHT OBJECT.

    It is the object from which the honest acceptance-alphabet distribution is
    obtained. If it were a second derivation of the same
    numbers the two could disagree; they are one computation on one state,
    through the compiler's own joint distribution, and this sums one into the
    other over the acceptance fibres the compiler declares.
    """
    from instances.common.honest.depolarized_bell_pair import honest_distribution

    result = prepared()
    table = result.raw_joint_distribution
    assert table is not None
    coarse = honest_distribution(result.declaration, QBER)
    fibres = acceptance_fibres(result.declaration)
    for label, fibre in fibres.items():
        assert sum((table[pair] for pair in fibre), F(0)) == coarse[label]


def test_an_instance_that_supplies_no_raw_model_gets_none_and_not_a_guess() -> None:
    """Coarse-graining is not invertible, so nothing is reconstructed."""
    outcome = prepare(config(), specification=specification())
    assert isinstance(outcome, Preparation)
    assert outcome.raw_joint_distribution is None


# ===========================================================================
#  The planned stage list
# ===========================================================================


def test_the_planned_list_is_this_configuration_s_route() -> None:
    """The same entries, with status ``planned``.

    The three device stages are absent because this route has none -- a route
    that never runs them would otherwise report three stages a reader would ask
    about -- and the stages the preparation ITSELF ran keep what they recorded,
    because reporting those as planned would throw away what happened.
    """
    result = prepared()
    stages = [record.stage for record in result.stages]
    assert stages == [stage for stage in STAGE_ORDER if stage not in STAGE_ORDER[:3]]

    statuses = {record.stage: record.status for record in result.stages}
    assert statuses[STAGE_ORDER[3]] is StageStatus.EXECUTED  # compilation ran
    assert statuses[STAGE_ORDER[-1]] is StageStatus.PLANNED  # solve did not


def test_a_refusal_is_a_refusal_here_too_and_carries_the_module_s_reason() -> None:
    """A preparation refuses where a run would, in the same vocabulary."""
    from instances.bb84.specification import (
        ConjugationConvention,
        conjugation_example_specification,
    )

    outcome = prepare(
        config(),
        specification=conjugation_example_specification(ConjugationConvention.OMITTED),
    )
    assert not isinstance(outcome, Preparation)
    assert outcome.refuses
    assert outcome.reason
