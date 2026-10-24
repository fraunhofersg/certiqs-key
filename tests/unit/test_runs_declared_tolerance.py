"""``RunConfig.declared_tolerance``: the one number a run declares, with no default.

No marker. The ``runs`` tier has no mathematical contract and states no claim
(spec/architecture.md 3.3, PRINCIPLES.md section 4); what is asserted here is that it
declines to invent a number it does not own.

The number is spec/architecture.md 2.8's ``tau`` -- "the **ceiling on the
pre-snap defect an instance may repair**" -- and §3.8 says of it that it "has
**no default and no fallback**: a run whose configuration does not declare it
is refused, because a defaulted ceiling on repair decides a security-relevant
act on nobody's authority". spec/architecture.md 2.8 says the same thing about this
field by name. Three refusals follow from that, and each names its own reason:

* nothing declared           -> ``declared_tolerance_absent``
* declared, but not a float  -> ``declared_tolerance_not_binary64``
* a float outside ``[0, 1)`` -> ``declared_tolerance_out_of_domain``

WHAT IS NOT TESTED HERE: that the modules receive ``0`` rather than this number
(spec/architecture.md 2.8). No code of this tier wires it, and a test here
asserting the wiring would assert something no code does.
"""

from __future__ import annotations

import math
from fractions import Fraction as F

import pytest

from certiqs_key.meat_core.declaration.declaration import KeyLengthParameters
from certiqs_key.runs.config import NO_DECLARED_TOLERANCE, RunConfig, RunConfigError

PARAMETERS = KeyLengthParameters(
    alpha=1.1, eps_pa=2.0**-30, eps_ev=2.0**-30, lambda_ec=0
)


def config(**changes: object) -> RunConfig:
    """Return a run config with everything but the tolerance filled in."""
    return RunConfig(
        rounds=2_000,
        completeness_budget=F(1, 1_000_000),
        parameters=PARAMETERS,
        **changes,  # type: ignore[arg-type]
    )


# ---------------------------------------------------------------------------
#  Absent is refused, and refused by name
# ---------------------------------------------------------------------------


def test_a_config_that_declares_no_tolerance_is_refused():
    with pytest.raises(RunConfigError) as caught:
        config()
    assert caught.value.reason == "declared_tolerance_absent"


def test_the_refusal_quotes_the_rule_it_is_enforcing():
    """A caller must be able to see that this is policy and not a bug."""
    with pytest.raises(RunConfigError) as caught:
        config()
    message = str(caught.value)
    assert "no default and no fallback" in message
    assert "spec/architecture.md 2.8" in message


def test_the_absence_sentinel_is_not_a_number_anyone_can_compute_with():
    """A sentinel that behaved like a float would be a default in disguise.

    ``NO_DECLARED_TOLERANCE`` is annotated ``float`` so that every reader of
    the field sees a ``float``; what keeps that from being a lie with
    consequences is that the object supports no arithmetic, so a path that
    somehow skipped ``__post_init__`` fails loudly instead of comparing a
    defect against a sentinel.
    """
    with pytest.raises(TypeError):
        _ = NO_DECLARED_TOLERANCE < 1.0
    with pytest.raises(TypeError):
        _ = NO_DECLARED_TOLERANCE + 0.0


# ---------------------------------------------------------------------------
#  The two values the brief names, and the interval they sit in
# ---------------------------------------------------------------------------


def test_zero_constructs_and_is_the_exact_reading():
    run = config(declared_tolerance=0.0)
    assert run.declared_tolerance == 0.0
    assert isinstance(run.declared_tolerance, float)


def test_a_small_dyadic_tolerance_constructs():
    run = config(declared_tolerance=2.0**-40)
    assert run.declared_tolerance == 2.0**-40


@pytest.mark.parametrize("value", [0.0, 2.0**-40, 0.5, 1.0 - 2.0**-53])
def test_every_value_in_the_half_open_interval_is_admitted(value: float):
    assert config(declared_tolerance=value).declared_tolerance == value


@pytest.mark.parametrize("value", [1.0, 1.5, -0.0000001, -1.0, math.inf, -math.inf])
def test_a_value_outside_the_interval_is_refused(value: float):
    """§3.8 fixes ``[0, 1)`` repo-wide and DERIVES the upper limit.

    At ``tau >= 1`` a completeness condition is satisfied by the all-zero
    family, so the admission rule would stop constraining the family at all.
    """
    with pytest.raises(RunConfigError) as caught:
        config(declared_tolerance=value)
    assert caught.value.reason == "declared_tolerance_out_of_domain"


def test_nan_is_refused_rather_than_compared():
    """``nan > tau`` is ``False``, so a NaN would pass every later refusal."""
    with pytest.raises(RunConfigError) as caught:
        config(declared_tolerance=math.nan)
    assert caught.value.reason == "declared_tolerance_out_of_domain"


# ---------------------------------------------------------------------------
#  It is a binary64 datum, and is not widened into one
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("value", [0, 1, F(0), F(1, 100), True, "0.0"])
def test_a_value_that_is_not_a_float_is_refused(value: object):
    """The engine is binary64 end to end; a declared value IS its float.

    ``0`` and ``Fraction(0)`` denote the same real number as ``0.0`` and are
    refused anyway, because accepting them would let the field's type drift
    back to an exact-rational reading --
    silently, and at a boundary whose whole job is to be explicit.
    """
    with pytest.raises(RunConfigError) as caught:
        config(declared_tolerance=value)
    assert caught.value.reason == "declared_tolerance_not_binary64"


# ---------------------------------------------------------------------------
#  The sweep primitive re-decides, and the deprecated alias
# ---------------------------------------------------------------------------


def test_a_sweep_axis_cannot_walk_the_config_out_of_the_interval():
    base = config(declared_tolerance=0.0)
    with pytest.raises(RunConfigError) as caught:
        base.with_(declared_tolerance=2.0)
    assert caught.value.reason == "declared_tolerance_out_of_domain"


def test_the_deprecated_alias_is_gone_and_left_no_second_name_behind():
    """``operator_tolerance`` is removed outright, not renamed.

    It survived the 0.3.0 rename as a read-only alias for ONE caller,
    ``runs/record.py``, which wrote the run record's ``operator_tolerance`` key.
    Record schema 0.4.0 records ``declared_tolerance`` under its own name, so
    the alias has no reader and is deleted with the key it fed.

    ASSERTED AS AN ABSENCE, and deliberately: two names for one number is how a
    caller ends up declaring one of them and reading the other. The property is
    that ``declared_tolerance`` is the ONLY way in, on the attribute, on the
    field list, and on the sweep primitive.
    """
    run = config(declared_tolerance=2.0**-40)
    assert not hasattr(run, "operator_tolerance")
    assert "operator_tolerance" not in RunConfig.__dataclass_fields__
    assert "declared_tolerance" in RunConfig.__dataclass_fields__
    with pytest.raises(TypeError):
        config(declared_tolerance=0.0).with_(operator_tolerance=0.5)
