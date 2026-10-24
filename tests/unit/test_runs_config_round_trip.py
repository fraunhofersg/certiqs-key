"""``RunConfig`` as a value: the JSON round trip, the digest, the new fields.

What is asked for is that a record's configuration DETERMINES ITS RUN --
everything a sweep may vary lives in the configuration -- and that the
configuration survives JSON, so that a caller can re-run one, submit one, or recognise
two identical requests.

The property that carries the file is the round trip:
``from_payload(to_payload(c)) == c`` for every configuration the class can
construct, including the ones with the awkward halves -- an exact rational in
``model``, a route NAME in ``device``, a declared tolerance at the edge of its
domain, a solver budget that is half chosen.
"""

from __future__ import annotations

import json
from fractions import Fraction as F

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from certiqs_key.meat_core.declaration.declaration import KeyLengthParameters
from certiqs_key.runs.config import (
    NO_DECLARED_TOLERANCE,
    AdvancedSolverSettings,
    RunConfig,
    RunConfigError,
    SolverSettings,
    canonical_json,
    config_digest,
)
from certiqs_key.runs.record import record_run
from certiqs_key.statistics.rules import EndpointRuleName, TailEvaluation

pytestmark = pytest.mark.contract

PARAMETERS = KeyLengthParameters(
    alpha=1.5, eps_pa=2.0**-30, eps_ev=2.0**-30, lambda_ec=7
)


def config(**changes: object) -> RunConfig:
    """Return a configuration with the defaults this file varies from."""
    base = {
        "rounds": 10_000,
        "completeness_budget": F(1, 1_000_000),
        "parameters": PARAMETERS,
        "declared_tolerance": 1e-12,
    }
    return RunConfig(**{**base, **changes})  # type: ignore[arg-type]


# ===========================================================================
#  Everything a sweep may vary lives here
# ===========================================================================


def test_the_solver_budget_is_a_config_field_and_none_means_the_solver_s_own() -> None:
    """The solver budget is a config field, not an option passed beside it.

    ``None`` is not a pair of numbers written down here: the defaults are the
    solver's to move, and a configuration that copied them would assert a
    budget it was never given.
    """
    assert config().solver is None
    chosen = config(
        solver=SolverSettings(
            max_iterations=2_000, advanced=AdvancedSolverSettings(gap_tolerance=1e-9)
        )
    )
    assert chosen.solver is not None
    assert chosen.solver.max_iterations == 2_000
    assert chosen.solver.advanced is not None
    assert chosen.solver.advanced.gap_tolerance == 1e-9


def test_the_budget_carries_two_fields_and_not_the_solver_s_nine() -> None:
    """The line is where a caller's authority ends.

    ``FrankWolfeOptions`` carries nine, seven of which are numbers of the
    solver's own -- thresholds the ``meat-core`` interface declares, and a
    gradient perturbation that WITHDRAWS the first-order number when it fires.
    A sweep axis over those would let a caller change what a reported tier
    means.

    Three NAMED CHOICES of the general format sit beside the budget -- ``oracle``,
    ``step_rule`` and ``warm_start`` -- which pick the loop's path and not what
    a tier means (``SolverSettings``' docstring argues it). The solver's own
    numbers are still absent: none of the seven, and none of the new
    constants (the pairwise shrink, the fold threshold, the warm-start mix).

    ``certified_evaluation`` is frank-wolfe/req:certified-evaluation's one
    option; it decides whether a tier is reached, never what a tier means.

    The ordinary tier is the method, the wall budget and the work cap; every
    other choice is in the ``advanced`` block (record schema 0.43.0).
    """
    fields = set(SolverSettings.__dataclass_fields__)
    assert fields == {"method", "budget_seconds", "max_iterations", "advanced"}
    assert set(AdvancedSolverSettings.__dataclass_fields__) == {
        "method",
        "oracle",
        "gap_tolerance",
        "warm_start",
        "certified_evaluation",
    }


@pytest.mark.parametrize(
    ("changes", "reason"),
    [
        ({"max_iterations": 0}, "solver_budget_not_positive"),
        ({"budget_seconds": 0.0}, "solver_budget_not_positive"),
    ],
)
def test_a_budget_that_is_not_one_is_refused_and_not_clamped(
    changes: dict[str, object], reason: str
) -> None:
    with pytest.raises(RunConfigError) as caught:
        SolverSettings(**changes)  # type: ignore[arg-type]
    assert caught.value.reason == reason


@pytest.mark.parametrize("gap", [0.0, -1e-9, float("nan"), float("inf")])
def test_a_gap_target_that_is_not_one_is_refused_and_not_clamped(gap: float) -> None:
    with pytest.raises(RunConfigError) as caught:
        AdvancedSolverSettings(gap_tolerance=gap)
    assert caught.value.reason == "solver_gap_tolerance_not_positive"


@pytest.mark.parametrize(
    ("ordinary", "expert"),
    [(m, None) for m in ("auto", "fw")]
    + [(None, m) for m in ("pairwise", "factor", "entropy", "corrective")],
)
def test_each_method_is_chosen_in_its_own_tier(
    ordinary: str | None, expert: str | None
) -> None:
    """The methods auto and fw are ordinary; the four expert ones only advanced."""
    settings = SolverSettings(
        method=ordinary, advanced=AdvancedSolverSettings(method=expert)
    )
    assert settings.chosen_method == (ordinary or expert)
    assert SolverSettings.from_payload(settings.as_payload()) == settings
    misplaced = ordinary or expert
    with pytest.raises(RunConfigError) as caught:
        if ordinary is not None:
            AdvancedSolverSettings(method=misplaced)
        else:
            SolverSettings(method=misplaced)
    assert caught.value.reason == "solver_method_not_admitted"
    where = "solver.method" if ordinary is not None else "solver.advanced.method"
    assert where in caught.value.message


def test_both_methods_set_is_refused() -> None:
    with pytest.raises(RunConfigError) as caught:
        SolverSettings(method="auto", advanced=AdvancedSolverSettings(method="factor"))
    assert caught.value.reason == "solver_method_set_twice"


def test_an_advanced_block_choosing_nothing_is_absent() -> None:
    """It is normalised away, so it neither serialises nor moves the digest."""
    empty = SolverSettings(max_iterations=7, advanced=AdvancedSolverSettings())
    assert empty.advanced is None
    assert empty == SolverSettings(max_iterations=7)
    assert empty.as_payload() == {"max_iterations": 7}
    assert config(solver=empty).digest() == config(
        solver=SolverSettings(max_iterations=7)
    ).digest()


@pytest.mark.parametrize(
    ("payload", "named"),
    [
        ({"oracle": "spectral"}, "solver.advanced"),
        ({"gap_tolerance": None}, "solver.advanced"),
        ({"certified_evaluation": "on"}, "solver.advanced"),
        ({"advance": {"oracle": "spectral"}}, "advance"),
        ({"advanced": {"orcale": "spectral"}}, "orcale"),
    ],
)
def test_a_solver_key_the_settings_do_not_read_is_refused(
    payload: dict[str, object], named: str
) -> None:
    """A flat expert key, or a misspelt one, is refused and never ignored."""
    with pytest.raises(RunConfigError) as caught:
        SolverSettings.from_payload(payload)
    assert caught.value.reason == "solver_key_not_admitted"
    assert named in caught.value.message


def test_from_choices_places_each_choice_in_its_tier() -> None:
    expert = SolverSettings.from_choices(method="pairwise", oracle="spectral")
    assert expert == SolverSettings(
        advanced=AdvancedSolverSettings(method="pairwise", oracle="spectral")
    )
    assert SolverSettings.from_choices(method="auto", budget_seconds=5.0) == (
        SolverSettings(method="auto", budget_seconds=5.0)
    )
    with pytest.raises(RunConfigError):
        SolverSettings.from_choices(method="away")


def test_the_two_statistics_request_fields_default_to_that_module_s_own() -> None:
    """``exact`` and ``sweep``: the statistics module's own defaults."""
    assert config().endpoint_rule == str(EndpointRuleName.EXACT)
    assert config().tail_evaluation == str(TailEvaluation.SWEEP)
    assert config().endpoint_rule == "exact"
    assert config().tail_evaluation == "sweep"


@pytest.mark.parametrize(
    ("changes", "reason"),
    [
        ({"endpoint_rule": "chebyshev"}, "endpoint_rule_not_admitted"),
        ({"tail_evaluation": "closed-form"}, "tail_evaluation_not_admitted"),
    ],
)
def test_a_rule_statistics_does_not_admit_is_refused_here_too(
    changes: dict[str, object], reason: str
) -> None:
    """Decided here as well as there, and the values come from that module.

    A configuration that could hold an inadmissible value would be a RECORD of
    a run that cannot happen -- swept over, serialized, digested and compared,
    all before the module that owns the vocabulary ever sees it.
    """
    with pytest.raises(RunConfigError) as caught:
        config(**changes)
    assert caught.value.reason == reason


def test_the_admitted_values_are_read_from_the_statistics_enums() -> None:
    """So that the two cannot drift: the module renames and this refuses."""
    for rule in EndpointRuleName:
        assert config(endpoint_rule=str(rule)).endpoint_rule == str(rule)
    for evaluation in TailEvaluation:
        assert config(tail_evaluation=str(evaluation)).tail_evaluation == str(
            evaluation
        )


# ===========================================================================
#  The round trip and the digest
# ===========================================================================

tolerances = st.sampled_from([0.0, 1e-16, 1e-12, 0.5, 0.9999999999999999])
rationals = st.fractions(min_value=0, max_value=1, max_denominator=64)
budgets = st.sampled_from(
    [
        None,
        SolverSettings(),
        SolverSettings(max_iterations=7),
        SolverSettings(advanced=AdvancedSolverSettings(gap_tolerance=1e-8)),
        SolverSettings(
            method="auto", advanced=AdvancedSolverSettings(oracle="spectral")
        ),
    ]
)
#: THE THIRD FORM A ``device`` VALUE MAY TAKE: one exact rational PER RECEIVER
#: PORT, keyed by the port map's own labels. The empty mapping is generated too
#: -- a receiver with no ports is not a receiver, but the payload form has to
#: survive it rather than collapsing to ``None`` or to a scalar on the way back.
per_port = st.dictionaries(
    st.sampled_from(["H", "V", "D", "A"]), rationals, max_size=4
)


@given(
    rounds=st.integers(min_value=1, max_value=10**9),
    budget=rationals.filter(lambda value: value < 1),
    tolerance=tolerances,
    qber=rationals,
    route=st.sampled_from(["encoded", "licensed", "licensed+two-sector"]),
    efficiency=per_port,
    solver=budgets,
    rule=st.sampled_from([str(name) for name in EndpointRuleName]),
    evaluation=st.sampled_from([str(name) for name in TailEvaluation]),
    constrained=st.one_of(st.none(), st.just(()), st.just(("ok", "err"))),
    alpha=st.one_of(st.none(), st.floats(min_value=1.01, max_value=1.99)),
)
@settings(max_examples=150, deadline=None)
def test_the_payload_round_trip_is_the_identity(
    rounds: int,
    budget: F,
    tolerance: float,
    qber: F,
    route: str,
    efficiency: dict[str, F],
    solver: SolverSettings | None,
    rule: str,
    evaluation: str,
    constrained: tuple[str, ...] | None,
    alpha: float | None,
) -> None:
    """``from_payload(to_payload(c)) == c``, over every awkward half there is.

    An exact rational in ``model``; ALL THREE FORMS OF A ``device`` VALUE
    together -- a route NAME, a scalar rational and a PER-PORT MAPPING of them,
    the last because the optical instance's own ``default_config()`` carries
    two of them and must be digested; a
    tolerance at both ends of ``[0, 1)``; a budget that is half chosen; every
    admitted rule and evaluation; and the three distinguishable states of
    ``constrained`` -- ``None`` (the declared default), ``()`` (an admissible
    selector in its own right) and a non-empty tuple.
    """
    original = config(
        rounds=rounds,
        completeness_budget=budget,
        declared_tolerance=tolerance,
        model={"qber": qber},
        device={
            "route": route,
            "basis_split": qber,
            "efficiency": efficiency,
        },
        solver=solver,
        endpoint_rule=rule,
        tail_evaluation=evaluation,
        constrained=constrained,
        alpha=alpha,
    )
    assert RunConfig.from_payload(original.to_payload()) == original


def test_the_payload_is_json_and_rationals_are_strings() -> None:
    """A ``Fraction`` rendered as a float would discard the exactness."""
    payload = config(
        model={"qber": F(3, 100)},
        device={"route": "encoded", "dark_count": {"H": F(1, 1000), "V": F(0)}},
    ).to_payload()
    assert json.loads(json.dumps(payload)) == payload
    assert payload["model"]["qber"] == "3/100"
    assert payload["completeness_budget"] == "1/1000000"
    # The declared tolerance IS its binary64 datum and stays a JSON number.
    assert payload["declared_tolerance"] == 1e-12
    # And a route name stays a name: rendering it as "p/q" would print a number
    # nobody declared.
    assert payload["device"]["route"] == "encoded"
    # A per-port value stays a MAPPING keyed by the port labels, its entries
    # "p/q" strings: flattening it to a list would record the detectors by
    # position, which is the fixed count the per-port kind exists to avoid.
    assert payload["device"]["dark_count"] == {"H": "1/1000", "V": "0"}


def test_an_instance_s_own_default_config_digests_and_round_trips() -> None:
    """THE PER-PORT CASE, at the level where it matters: a per-port default.

    The optical instance's ``default_config()`` carries two per-port mappings,
    and ``digest()`` must not raise ``TypeError`` on them although a mapping of
    ``Fraction`` is not JSON. A configuration an instance offers that its own
    format cannot record is not a configuration.
    """
    from instances.optical_bb84.surface import default_config

    declared = default_config()
    assert len(declared.digest()) == 64
    assert RunConfig.from_payload(declared.to_payload()) == declared
    assert json.loads(json.dumps(declared.to_payload())) == declared.to_payload()


def test_the_absent_tolerance_is_spelled_out_and_refused_on_the_way_back() -> None:
    """The one configuration this class refuses to construct is describable.

    A payload can say "this run declared no tolerance", and reading it back
    gives the constructor's own refusal at the constructor's own place, rather
    than losing the fact.
    """
    payload = config().to_payload()
    payload["declared_tolerance"] = None
    with pytest.raises(RunConfigError) as caught:
        RunConfig.from_payload(payload)
    assert caught.value.reason == "declared_tolerance_absent"
    assert NO_DECLARED_TOLERANCE is not None


def test_the_digest_is_sha256_of_the_canonical_json_and_is_stable() -> None:
    """Sorted keys, no whitespace, and the same value for the same request."""
    from hashlib import sha256

    one = config(model={"qber": F(1, 50)})
    two = config(model={"qber": F(1, 50)})
    assert config_digest(one) == config_digest(two) == one.digest()
    assert config_digest(one) == sha256(
        canonical_json(one.to_payload()).encode("utf-8")
    ).hexdigest()
    assert len(config_digest(one)) == 64


def test_a_different_request_has_a_different_digest() -> None:
    """Including on the three fields a sweep may vary, which is what they are for."""
    base = config()
    for changed in (
        config(rounds=10_001),
        config(endpoint_rule=str(EndpointRuleName.BERNSTEIN)),
        config(tail_evaluation=str(TailEvaluation.ENCLOSURE)),
        config(solver=SolverSettings(max_iterations=2_000)),
    ):
        assert config_digest(changed) != config_digest(base)


def test_the_record_carries_the_three_fields_and_the_digest() -> None:
    """A record's config determines its run, which is what a sweep needs."""
    from certiqs_key.runs.pipeline import SliceRefusal, SliceStage

    outcome = SliceRefusal(
        stage=SliceStage.COMPILATION, reason="whatever", detail="detail"
    )
    recorded = record_run(outcome, config(), created_by="test").payload["config"]
    assert recorded["solver"] is None
    assert recorded["endpoint_rule"] == "exact"
    assert recorded["tail_evaluation"] == "sweep"
    assert recorded["config_digest"] == config_digest(config())


def test_the_request_resolves_the_method_advanced_then_ordinary_then_default() -> None:
    """``solver_request`` is the one place an absent method takes its default."""
    from certiqs_key.runs.surface import DEFAULT_METHOD, solver_request

    assert solver_request(None).method == DEFAULT_METHOD
    assert solver_request(SolverSettings()).method == DEFAULT_METHOD
    assert solver_request(SolverSettings(method="auto")).method == "auto"
    expert = SolverSettings(
        advanced=AdvancedSolverSettings(method="corrective", gap_tolerance=1e-7)
    )
    request = solver_request(expert)
    assert (request.method, request.gap_target) == ("corrective", 1e-7)
