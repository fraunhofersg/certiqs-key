"""``receiver-povm`` fail-closed: the four clauses, and the tier that cannot rise.

The ``fail_closed`` convention (``interface.yaml`` ``conventions``): "every
failed validation produces a refusal with a machine-readable reason and no
artifact. No default is substituted for a missing datum, no parameter is
clipped into its domain, no cycle is resolved, and no tolerance is ignored."

Structural tests, not registry replays: what is on trial here is that the
PROPERTY holds for data the freeze never saw, and that the refusal is a RECORD
rather than an exception. The frozen refusal cases are replayed in
``tests/golden/test_receiver_povm_refusals_against_registry.py``.
"""

from __future__ import annotations

import math
from dataclasses import MISSING, fields, replace
from fractions import Fraction as F

import pytest
from probe_presence import requires_probe, with_probe
from receiver_povm_support import (
    TOLERANCE,
    bb84_channel_only_request,
    probe_receiver_request,
)
from registry_receiver_povm import (
    TOLERANCE_FIXTURE_0_3_0,
    TOLERANCES_ALWAYS_REQUIRED_0_3_0,
    is_superseded,
    is_superseded_0_3_0,
)

from certiqs_key.receiver import TOLERANCE_DOMAIN as MODULE_TOLERANCE_DOMAIN
from certiqs_key.receiver import (
    Assurance,
    Beamsplitter,
    Element,
    ElementGraph,
    Loss,
    Mode,
    ModeSpace,
    PhaseShifter,
    Polarization,
    Refusal,
    RefusalReason,
    Retarder,
    check_exactly_one_route,
    check_mode_space,
    check_parameter_tolerances,
    construct_receiver,
    tolerances_from_declaration,
)
from certiqs_key.receiver.artifact import (
    BOUND_EVALUATION,
    MATHEMATICAL_SPEC_VERSION,
    ReceiverMeasurementArtifact,
)
from certiqs_key.receiver.errors import HypothesisError
from certiqs_key.receiver.numerics import PiMultiple


@pytest.mark.contract
def test_no_tolerance_is_ignored_and_exactly_zero_is_the_one_admitted_value() -> None:
    """`parameters.exactness`, and Assumption ass:exact."""
    admitted = (
        Beamsplitter(F(1, 2), 0, 0, 0),
        Beamsplitter(F(1, 2), 0, 0, 0, tolerances={"x": 0}),
        Beamsplitter(F(1, 2), 0, 0, 0, tolerances={"x": F(0, 7), "y_1": 0.0}),
    )
    for element in admitted:
        assert check_parameter_tolerances((("bs", element),)) is None
    refused = (
        Beamsplitter(F(1, 2), 0, 0, 0, tolerances={"x": F(1, 10**9)}),
        Beamsplitter(F(1, 2), 0, 0, 0, tolerances={"y_1": 1e-30}),
    )
    for element in refused:
        outcome = check_parameter_tolerances((("bs", element),))
        assert outcome is not None
        assert outcome.reason is RefusalReason.PARAMETER_TOLERANCE_NOT_ZERO
        assert "parameter uncertainty sets are out of scope" in outcome.detail


@pytest.mark.contract
def test_no_parameter_is_clipped_into_its_domain() -> None:
    """`parameters.domains`: the clipped value would be admissible and WRONG."""
    outside = Beamsplitter(F(3, 2), 0, 0, 0)
    refusal = outside.check_domain(TOLERANCE)
    assert refusal is not None
    assert refusal.reason is RefusalReason.GRAPH_CONDITION_E1_FAILED
    assert Beamsplitter(1, 0, 0, 0).check_domain(TOLERANCE) is None
    # The half-open endpoint trap: delta = 2 pi is OUT, delta = 0 is IN. The
    # endpoint itself is declared as a coefficient of pi; a radian value is the
    # dyadic rational it denotes, so the double math.tau (below 2 pi) and the
    # double math.pi (below pi) are IN and the next doubles above them OUT.
    assert Retarder(PiMultiple(2), 0, 0).check_domain(TOLERANCE) is not None
    assert Retarder(0, 0, 0).check_domain(TOLERANCE) is None
    assert Retarder(math.tau, 0, 0).check_domain(TOLERANCE) is None
    above_tau = math.nextafter(math.tau, math.inf)
    assert Retarder(above_tau, 0, 0).check_domain(TOLERANCE) is not None
    assert Retarder(math.pi, PiMultiple(1), 0).check_domain(TOLERANCE) is not None
    assert Retarder(math.pi, math.pi, 0).check_domain(TOLERANCE) is None
    above_pi = math.nextafter(math.pi, math.inf)
    assert Retarder(math.pi, above_pi, 0).check_domain(TOLERANCE) is not None
    assert Retarder(math.pi, math.pi - 1e-9, 0).check_domain(TOLERANCE) is None


@pytest.mark.contract
def test_no_default_is_substituted_for_a_missing_datum() -> None:
    """The inputs table: the tolerances are declared, NEVER defaulted.

    THE TUPLE IS THE REGISTRY-0.3.0 EIGHT, OF WHICH SIX ARE REQUIRED ALWAYS.
    `TOLERANCE_FIXTURE` is marked in `SUPERSEDED_BY_0_2_0` and
    `TOLERANCE_FIXTURE_0_2_0` in `SUPERSEDED_BY_0_3_0`; the replacement adds
    `eps_6` and `eps_eig` and removes nothing. This test drops one ALWAYS-required
    member at a time and requires a refusal for every one of the six, then does
    the same for the two CONDITIONALLY required ones -- which refuse under a
    DIFFERENT, contract-verbatim reason and only where a depth is declared.
    """
    assert is_superseded("TOLERANCE_FIXTURE")
    assert is_superseded_0_3_0("TOLERANCE_FIXTURE_0_2_0")
    for missing in TOLERANCES_ALWAYS_REQUIRED_0_3_0:
        declared = {k: v for k, v in TOLERANCE_FIXTURE_0_3_0.items() if k != missing}
        outcome = tolerances_from_declaration(declared, False)
        assert isinstance(outcome, Refusal), missing
        assert outcome.reason is RefusalReason.NUMERICAL_TOLERANCE_MISSING, missing
        assert missing in outcome.detail, missing
    # THE TWO CONDITIONALLY REQUIRED ONES. Missing WHERE A DEPTH IS DECLARED is
    # refused, with the contract's own row-6 string; missing where none is is
    # "NEITHER REQUIRED NOR AN ERROR", and the field is then ABSENT, not zero.
    for missing in ("eps_6", "eps_eig"):
        declared = {k: v for k, v in TOLERANCE_FIXTURE_0_3_0.items() if k != missing}
        refused = tolerances_from_declaration(declared, True)
        assert isinstance(refused, Refusal), missing
        assert refused.reason is (
            RefusalReason.EXACT_WINDOW_DECLARED_WITHOUT_REQUIRED_TOLERANCE
        ), missing
        assert str(refused.reason) == (
            "exact_window_declared_without_required_tolerance"
        )
        admitted = tolerances_from_declaration(declared, False)
        assert not isinstance(admitted, Refusal), missing
        assert getattr(admitted, missing) is None, missing
    # There is no `eps_hyp` to be missing or non-positive, and no declared
    # margin anywhere among the inputs (Rem. rem:pmc-branch-choice; Rem.
    # rem:noslack adds that eps_eig is not a margin of this kind).
    assert "eps_hyp" not in TOLERANCE_FIXTURE_0_3_0
    assert not hasattr(RefusalReason, "EPS_HYP_MISSING")
    assert not hasattr(RefusalReason, "EPS_HYP_NOT_POSITIVE")
    assert not isinstance(
        tolerances_from_declaration(dict(TOLERANCE_FIXTURE_0_3_0), True), Refusal
    )


@pytest.mark.contract
def test_the_declared_tolerance_domain_is_half_open_and_refuses_both_sides() -> None:
    """Rem. rem:tolerancedomain: [0, 1), with the contract's verbatim reason.

    0 IS ADMISSIBLE -- a declarer who wants a condition decided EXACTLY declares
    0 -- and 1 IS NOT (``interface.yaml`` ``numerical_tolerances.domain_note``);
    a negative value refuses too, because it would make Def. def:tolmap (iii)'s
    entrywise test STRICTER than the exact condition, which is not a tolerance
    at all. The refusal reason is contract text.
    """
    low, high = MODULE_TOLERANCE_DOMAIN
    assert (low, high) == (0.0, 1.0)
    # ALL EIGHT members share the domain, the two conditional ones included:
    # the inputs table declares [0, 1) for each (`numerical_tolerances`;
    # Req. req:tolerance-domain).
    for key in TOLERANCE_FIXTURE_0_3_0:
        exact = dict(TOLERANCE_FIXTURE_0_3_0) | {key: 0}
        assert not isinstance(tolerances_from_declaration(exact, True), Refusal), key
        for bad in (F(1), F(3, 2), F(-1, 1000)):
            outcome = tolerances_from_declaration(
                dict(TOLERANCE_FIXTURE_0_3_0) | {key: bad}, True
            )
            assert isinstance(outcome, Refusal), (key, bad)
            assert outcome.reason is (
                RefusalReason.TOLERANCE_OUTSIDE_DECLARED_DOMAIN
            ), (key, bad)
            assert str(outcome.reason) == "tolerance_outside_declared_domain"
    # ADMITTED AND UNWISE, which the contract distinguishes: "the domain is A
    # FLOOR, NOT SIZING ADVICE". `eps_eig = 0` is the other end of the same
    # rule: admissible, and it makes Ass. ass:eig read "the eigenvalue routine
    # never overshoots at all" -- which this module does not second-guess.
    near_one = dict(TOLERANCE_FIXTURE_0_3_0) | {"eps_gap": F(999, 1000)}
    assert not isinstance(tolerances_from_declaration(near_one, True), Refusal)
    zero_eig = dict(TOLERANCE_FIXTURE_0_3_0) | {"eps_eig": F(0)}
    admitted = tolerances_from_declaration(zero_eig, True)
    assert not isinstance(admitted, Refusal)
    assert admitted.eps_eig == 0.0


@pytest.mark.contract
def test_no_declared_parameter_carries_a_default() -> None:
    """The `fail_closed` convention: the contract fixes ONE default, C5's flag.

    Every other declared parameter -- a phase, a loss, an axis angle, a
    leak, a dark-count probability, the reserved tau -- must be supplied or
    the declaration is not one; a Python default here IS a substituted
    datum.
    """
    from certiqs_key.receiver import (
        DetectorPort,
        ElementGraph,
        Mirror,
        Mode,
        Polarizer,
        PolarizingBeamsplitter,
    )

    # `edges`: an empty edge set is an absence the contract types (def:graph),
    # refused by (E3) wherever it could matter and immaterial by
    # thm:compilation-well-defined (i) otherwise; the
    # argument is at the field.
    fixed_by_contract = {"tolerances", "handedness_flip", "edges"}
    for cls in (
        Beamsplitter,
        PolarizingBeamsplitter,
        Retarder,
        Mirror,
        Polarizer,
        DetectorPort,
        Mode,
        ElementGraph,
    ):
        for entry in fields(cls):
            if entry.name in fixed_by_contract:
                continue
            assert entry.default is MISSING and entry.default_factory is MISSING, (
                cls.__name__,
                entry.name,
            )


@pytest.mark.contract
def test_a_second_declared_tau_is_refused() -> None:
    """Definition def:modes with Assumption ass:thresh: a single declared value."""
    space = ModeSpace.declare(
        (Mode("A", Polarization.H, 0), Mode("A", Polarization.V, 1))
    )
    refusal = check_mode_space(space)
    assert refusal is not None
    assert refusal.reason is RefusalReason.MODE_SPACE_TAU_NOT_SINGLE_VALUED


@pytest.mark.contract
def test_the_exactly_one_route_rule_refuses_none_and_two() -> None:
    """`input_routes.rule`: refused rather than resolved by precedence."""
    for present in (
        {},
        {"port_grams": True, "instrument_matrix": True},
        {"port_grams": True, "element_graph": True},
        {"port_grams": True, "instrument_matrix": True, "element_graph": True},
    ):
        outcome = check_exactly_one_route(present)
        assert outcome is not None
        assert outcome.reason is RefusalReason.INPUT_ROUTES_NOT_EXACTLY_ONE
    for route in ("port_grams", "instrument_matrix", "element_graph"):
        assert check_exactly_one_route({route: True}) is None


@pytest.mark.contract
def test_the_reason_vocabulary_is_machine_readable_and_unambiguous() -> None:
    """The `fail_closed` convention: a machine-readable reason, one per check."""
    values = [str(reason) for reason in RefusalReason]
    assert len(set(values)) == len(values)
    for value in values:
        assert value == value.lower()
        assert " " not in value
        assert value.replace("_", "").isalnum()


@pytest.mark.contract
@requires_probe
def test_a_refusal_emits_no_artifact() -> None:
    """`fail_closed`: a refusal is emitted INSTEAD OF an artifact, never beside one."""
    base = probe_receiver_request()
    broken = {
        "two routes": replace(base, port_grams=_grams_of(base)),
        "no tolerances": replace(base, numerical_tolerances={}),
        "negative cutoff": replace(base, photon_cutoff=-1),
        "window too small": replace(base, tail_window={"on": 1}),
        "window missing": replace(base, tail_window={}),
    }
    for label, request in broken.items():
        emission = construct_receiver(request)
        assert emission.refusal is not None, label
        assert emission.artifact is None, label
        assert isinstance(emission.refusal, Refusal)
        assert not isinstance(emission.refusal, BaseException)
        assert emission.refusal.as_machine_record()["reason"], label
        # Even a refused request answers the tier fail-closed.
        assert emission.assurance is Assurance.ESTIMATE, label


def _grams_of(request: object) -> object:
    """Return a Gram family for the probe receiver, for the two-route case."""
    from certiqs_key.receiver import GramFamily

    emission = construct_receiver(probe_receiver_request())
    assert emission.artifact is not None
    return GramFamily(
        tuple(label for label, _ in emission.artifact.port_grams),
        tuple(matrix for _, matrix in emission.artifact.port_grams),
    )


@pytest.mark.contract
def test_no_cycle_is_resolved_by_the_emission_pass() -> None:
    """Definition def:graph (E2) and Remark rem:noloops, end to end."""
    request = bb84_channel_only_request()
    graph = request.element_graph
    assert graph is not None
    cyclic = ElementGraph(
        (
            Element("e", PhaseShifter((math.pi,)), (0,)),
            Element("f", Loss((F(1, 4),)), (1,)),
        ),
        (("e", "f"), ("f", "e")),
    )
    emission = construct_receiver(replace(request, element_graph=cyclic))
    assert emission.artifact is None
    assert emission.refusal is not None
    assert emission.refusal.reason is RefusalReason.GRAPH_CONDITION_E2_FAILED


@pytest.mark.contract
def test_no_request_ever_yields_an_artifact_above_estimate() -> None:
    """Theorem thm:exact-and-evaluated (iii): NO PATH here produces a stronger label.

    The frozen registry asked this of a ``certified`` request; the question is
    put to every rung of the ladder (three, def:tiers): each is
    answered ``estimate``, with no fallback reason, and the tier is never an
    artifact key. The artifact's evaluation label is its settings' own
    (req:evaluation-label: `rigorous` on these exact-route receivers).
    """
    for build in (bb84_channel_only_request, *with_probe(probe_receiver_request)):
        for tier in Assurance:
            request = replace(build(), requested_assurance=tier)
            emission = construct_receiver(request)
            assert emission.artifact is not None
            assert emission.assurance is Assurance.ESTIMATE
            assert emission.assurance_reason is None
            assert emission.artifact.bound_evaluation == "rigorous"
            # The tier is not an artifact key, so no consumer can read one off it.
            assert "assurance" not in emission.artifact.payload_keys()


@pytest.mark.contract
def test_bound_evaluation_is_exactly_what_the_settings_say() -> None:
    """`outputs.bound_evaluation`, req:evaluation-label, enforced.

    `rigorous` exactly where every setting's weight is the enclosed one,
    `floating_point` otherwise; no other value, and neither where it is false.
    """
    emission = construct_receiver(bb84_channel_only_request())
    assert emission.artifact is not None
    good = emission.artifact
    assert good.bound_evaluation == "rigorous"
    assert BOUND_EVALUATION == "floating_point"
    for wrong in ("interval", "floating_point", "certified"):
        with pytest.raises(HypothesisError, match="bound_evaluation"):
            replace(good, bound_evaluation=wrong)
    with pytest.raises(HypothesisError, match="mathematical_spec_version"):
        replace(good, mathematical_spec_version="receiver-povm@0.2.0-draft")
    # Nor 0.1.3,
    with pytest.raises(HypothesisError, match="mathematical_spec_version"):
        replace(good, mathematical_spec_version="receiver-povm@0.1.3")
    # nor 0.2.0,
    with pytest.raises(HypothesisError, match="mathematical_spec_version"):
        replace(good, mathematical_spec_version="receiver-povm@0.2.0")
    # nor 0.3.0, whose number this module's accepted version
    # shares.
    with pytest.raises(HypothesisError, match="mathematical_spec_version"):
        replace(good, mathematical_spec_version="receiver-povm@0.3.0")
    # The constants are the contract's, not a caller's: an accepted version of
    # spec/modules/receiver/module.yaml, the one the code implements, written
    # by hand when the pin moves, never regenerated from the code under test.
    assert MATHEMATICAL_SPEC_VERSION == "receiver@0.9.0"
    # And an earlier accepted version is one an artifact may not claim any
    # more: 0.1.2, which did not state the per-setting weights, and 0.2.0,
    # which did.
    with pytest.raises(HypothesisError, match="mathematical_spec_version"):
        replace(good, mathematical_spec_version="receiver@0.1.2")
    with pytest.raises(HypothesisError, match="mathematical_spec_version"):
        replace(good, mathematical_spec_version="receiver@0.2.0")
    assert ReceiverMeasurementArtifact is type(good)
