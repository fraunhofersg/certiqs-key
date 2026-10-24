"""Fail-closed: every frozen refusal, produced by the code, with its check named.

Golden replay of ``REFUSAL_CASES`` (oracle entry ``O-RP-INTERFACE``, marked
``reframed`` at registry 0.2.0: every interface case it carries is unchanged)
and of the registry-0.2.0 rows ``REFUSAL_CASES_0_2_0`` (oracle entry
``O-RP-REASONS``), plus the structural properties of the ``fail_closed``
convention (``interface.yaml`` ``conventions``): "every failed validation
produces a refusal with a machine-readable reason and no artifact. No default
is substituted for a missing datum, no parameter is clipped into its domain, no
cycle is resolved, and no tolerance is ignored." A registry version is one of
tests/oracles/registry_receiver_povm.py, the frozen record, and not a version
of this module.

THE SPELLING TRAP DID NOT GO AWAY, IT MOVED. At registry 0.1.3 the contract
named exactly ONE machine-readable reason verbatim; the registry-0.2.0 refusal
table spells FIVE refusal reasons and names a SIXTH string beside them that is
a TIER FALLBACK and not a refusal. Everywhere else the contract still fixes the
naming OBLIGATION and the IDENTITY of the failing check, and the spelling stays
code's (``refusals.named_without_a_spelling_note``). Each test below asserts
the identifier or the contract-verbatim key, never the registry's prose.

TWO REGISTRY-0.1.3 OBJECTS ARE RETIRED HERE, DELIBERATELY AND ONE BY ONE
========================================================================
* ``REF-EPS-HYP-MISSING`` is marked ``superseded`` and is RETIRED OUTRIGHT, with
  NO successor: the input whose absence it refused does not exist at registry
  0.2.0 or in this module. There is no declared margin among the inputs
  (Remark ``rem:pmc-branch-choice``), and Requirement ``req:window-declaration``
  names the one window refusal.
* ``REFUSAL_REASONS_VERBATIM`` (the registry's one-element 0.1.3 tuple) is
  marked ``superseded``: it IS the statement that the contract spells exactly
  one machine-readable reason string, true of registry 0.1.3 and FALSE of
  registry 0.2.0. REPLACED BY ``REFUSAL_REASONS_VERBATIM_0_2_0``,
  ``TIER_FALLBACK_REASON_VERBATIM`` and ``REASON_VOCABULARY_0_2_0``, replayed
  below.
* ``TOLERANCE_FIXTURE`` is marked ``superseded`` and its only use in this file
  was building the ``eps_hyp``-less declaration above; it is REPLACED BY
  ``TOLERANCE_FIXTURE_0_2_0``, whose members are the registry-0.2.0 six.

``REF-WINDOW-MISSING`` is marked ``reframed`` -- its verdict stands and only its
quoted registry-0.1.3 sentence is stale -- and is REWRITTEN to its successor
``REF-WINDOW-MISSING-0-2-0``, which quotes the registry-0.2.0 text.

ONE FROZEN CASE IS NOT EXERCISED HERE: the certified-to-estimate FALLBACK was a
TIER FALLBACK rather than a refusal -- an artifact WAS emitted, at the lower
tier -- and it belonged to the request-to-artifact pass. The
code does not spell it at all; what is checked here is that the string is
not in the enum, the frozen nine being the registry's record, and that no further
string is claimed to be the contract's.
"""

from __future__ import annotations

import math
from fractions import Fraction as F

import numpy as np
import pytest
from receiver_povm_support import TOLERANCE
from registry_receiver_povm import (
    REASON_EMITS_ARTIFACT_0_3_0,
    REASON_VOCABULARY_0_3_0,
    REASON_VOCABULARY_RECEIVER_0_1_2,
    REFUSAL_CASES,
    REFUSAL_CASES_0_2_0,
    REFUSAL_REASONS_VERBATIM_0_3_0,
    REFUSALS_NAMED_WITHOUT_A_SPELLING_0_3_0,
    RETIRED_FROM_THE_CODE_RECEIVER_0_1_2,
    TIER_FALLBACK_REASON_VERBATIM,
    TOLERANCE_FIXTURE_0_3_0,
    is_superseded,
    is_superseded_0_3_0,
    rp_oracle,
)

from certiqs_key.receiver import (
    REASON_VOCABULARY as MODULE_VOCABULARY,
)
from certiqs_key.receiver import (
    REFUSAL_REASONS_VERBATIM as MODULE_VERBATIM,
)
from certiqs_key.receiver import (
    Beamsplitter,
    DarkCountChannel,
    DarkCountRoute,
    Element,
    ElementGraph,
    GenericBlock,
    GramFamily,
    Loss,
    PhaseShifter,
    Polarizer,
    Refusal,
    RefusalReason,
    Rotator,
    block_positivity_residual,
    check_dark_channel,
    check_dark_count_source,
    check_element_graph,
    check_exactly_one_route,
    check_parameter_tolerances,
    check_rank_against_port_sizes,
    check_residuals,
    check_tail_window,
    deficiency_identity,
    port_grams,
    splitting_ratio_presentation,
    tolerances_from_declaration,
)
from certiqs_key.receiver.residuals import deficiency_residual

_ANGLE = math.atan2(0.8, 0.6)


def _refusal_for(case_id: str) -> Refusal:
    """Return the refusal the module produces for one frozen refusal case."""
    if case_id == "REF-TWO-ROUTES":
        outcome = check_exactly_one_route(
            {"port_grams": True, "element_graph": True, "instrument_matrix": False}
        )
    elif case_id == "REF-NONZERO-TOLERANCE":
        element = Beamsplitter(F(1, 2), 0, 0, 0, tolerances={"x": F(1, 1000)})
        outcome = check_parameter_tolerances((("bs_1", element),))
    elif case_id == "REF-OUT-OF-DOMAIN-NOT-CLIPPED":
        graph = ElementGraph(
            (Element("bs", Beamsplitter(F(3, 2), 0, 0, 0), (0, 1, 2, 3)),)
        )
        outcome = check_element_graph(graph, 4, TOLERANCE)
    elif case_id == "REF-C10-NOT-A-CONTRACTION":
        graph = ElementGraph(
            (Element("blk", GenericBlock.of(((2, 0), (0, 0))), (0, 1)),)
        )
        outcome = check_element_graph(graph, 2, TOLERANCE)
    elif case_id == "REF-CYCLE":
        graph = ElementGraph(
            (
                Element("e", PhaseShifter((math.pi,)), (0,)),
                Element("f", Loss((F(1, 4),)), (1,)),
            ),
            (("e", "f"), ("f", "e")),
        )
        outcome = check_element_graph(graph, 2, TOLERANCE)
    elif case_id == "REF-SUPPORT-INCOMPARABLE":
        graph = ElementGraph(
            (
                Element("e", Rotator(_ANGLE), (0, 1)),
                Element("f", Polarizer(0, 1, 0), (0, 1)),
            )
        )
        outcome = check_element_graph(graph, 2, TOLERANCE)
    elif case_id == "REF-WINDOW-TOO-SMALL":
        outcome = check_tail_window(2, ("on",), {"on": False}, {"on": 2})
    elif case_id == "REF-WINDOW-MISSING-0-2-0":
        # REWRITTEN FROM the reframed REF-WINDOW-MISSING: same verdict, and the
        # text of req:window-declaration (def:pmc's "Refusals" at registry
        # 0.2.0), which names this one refusal only.
        outcome = check_tail_window(1, ("on",), {"on": False}, {})
    elif case_id == "REF-TOLERANCE-MISSING":
        declared = {
            key: value
            for key, value in TOLERANCE_FIXTURE_0_3_0.items()
            if key != "eps_5"
        }
        # `exact_window_declared=False`: the declaration carries no depth, so
        # the two CONDITIONALLY required members are not required and what is
        # refused here is one of the ALWAYS-required six.
        result = tolerances_from_declaration(declared, False)
        assert isinstance(result, Refusal)
        outcome = result
    elif case_id == "REF-TOLERANCE-OUTSIDE-DOMAIN":
        declared = dict(TOLERANCE_FIXTURE_0_3_0) | {"eps_5": F(1)}
        result = tolerances_from_declaration(declared, False)
        assert isinstance(result, Refusal)
        outcome = result
    elif case_id == "REF-DARK-DECLARED-TWICE":
        outcome = check_dark_count_source(
            DarkCountChannel(
                2,
                DarkCountRoute.DECLARED_MATRIX,
                {
                    frozenset(): {frozenset(): 1.0},
                    frozenset({0}): {frozenset({0}): 1.0},
                    frozenset({1}): {frozenset({1}): 1.0},
                    frozenset({0, 1}): {frozenset({0, 1}): 1.0},
                },
            ),
            [F(1, 10), 0],
        )
    elif case_id == "REF-SPLITTING-RATIO":
        outcome = splitting_ratio_presentation((9, 1))
    elif case_id == "REF-RANK-EXCEEDS-PORT-SIZE":
        family = GramFamily(
            ("1",),
            (np.asarray([[0.5, 0.0], [0.0, 0.002]], dtype=np.complex128),),
        )
        outcome = check_rank_against_port_sizes(family, [1], TOLERANCE)
    elif case_id == "REF-R5-ABOVE-TOLERANCE":
        block = np.asarray([[0.5, 0.25], [0.0, 0.5]], dtype=np.complex128)
        outcome = check_residuals(
            (block_positivity_residual([{"mc": block}], TOLERANCE),)
        )
    elif case_id == "REF-DARK-NOT-MONOTONE":
        channel = DarkCountChannel(
            2,
            DarkCountRoute.DECLARED_MATRIX,
            {
                frozenset(): {frozenset(): 1.0},
                frozenset({0}): {frozenset({0}): 1.0},
                frozenset({1}): {frozenset({1}): 1.0},
                frozenset({0, 1}): {frozenset({0}): 0.5, frozenset({0, 1}): 0.5},
            },
        )
        outcome = check_dark_channel(channel, TOLERANCE)
    elif case_id == "REF-RESIDUAL-ABOVE-TOLERANCE":
        gamma_inp = np.asarray([[0.5, 0.0], [0.0, 0.5]], dtype=np.complex128)
        family = GramFamily(("1",), port_grams(gamma_inp, [(0,)]))
        # The unmonitored term dropped: residual r_3 = 1/4 against eps_3.
        outcome = check_residuals(
            (
                deficiency_residual(
                    deficiency_identity(gamma_inp, family, ()), TOLERANCE
                ),
            )
        )
    else:
        raise AssertionError(f"no builder for {case_id}")
    assert outcome is not None, case_id
    return outcome


def _expected() -> dict[str, RefusalReason]:
    """Return the contract's identifier for the failing check, per frozen case.

    A function rather than a module constant so that nothing here loads the
    implementation at collection time; see the `test_receiver_support` module
    docstring.
    """
    return {
        "REF-TWO-ROUTES": RefusalReason.INPUT_ROUTES_NOT_EXACTLY_ONE,
        "REF-NONZERO-TOLERANCE": RefusalReason.PARAMETER_TOLERANCE_NOT_ZERO,
        "REF-OUT-OF-DOMAIN-NOT-CLIPPED": RefusalReason.GRAPH_CONDITION_E1_FAILED,
        "REF-C10-NOT-A-CONTRACTION": RefusalReason.GRAPH_CONDITION_E1_FAILED,
        "REF-CYCLE": RefusalReason.GRAPH_CONDITION_E2_FAILED,
        "REF-SUPPORT-INCOMPARABLE": RefusalReason.GRAPH_CONDITION_E3_FAILED,
        "REF-WINDOW-TOO-SMALL": RefusalReason.TAIL_WINDOW_NOT_ABOVE_CUTOFF,
        "REF-DARK-NOT-MONOTONE": RefusalReason.DARK_CONDITION_D2_FAILED,
        "REF-RESIDUAL-ABOVE-TOLERANCE": RefusalReason.RESIDUAL_R3_ABOVE_TOLERANCE,
    }


def _expected_0_2_0() -> dict[str, RefusalReason]:
    """Return the reason each registry-0.2.0 refusal row emits.

    Five are contract-VERBATIM (the refusal rules, ``interface.yaml``
    ``refusals``) and the sixth, ``REF-WINDOW-MISSING-0-2-0``, is one of the
    conditions ``refusals.named_without_a_spelling`` lists WITHOUT a spelling,
    so it carries this module's key. ``REF-TOLERANCE-MISSING`` is not a frozen
    row -- the same list names "a missing declared tolerance" -- and is
    exercised beside them.
    """
    return {
        "REF-DARK-DECLARED-TWICE": (RefusalReason.DARK_COUNT_CHANNEL_DECLARED_TWICE),
        "REF-SPLITTING-RATIO": (RefusalReason.SPLITTING_RATIO_PRESENTATION_UNSUPPORTED),
        "REF-RANK-EXCEEDS-PORT-SIZE": (RefusalReason.PORT_GRAM_RANK_EXCEEDS_PORT_SIZE),
        "REF-R5-ABOVE-TOLERANCE": (
            RefusalReason.PHOTON_BLOCK_POSITIVITY_RESIDUAL_ABOVE_TOLERANCE
        ),
        "REF-TOLERANCE-OUTSIDE-DOMAIN": (
            RefusalReason.TOLERANCE_OUTSIDE_DECLARED_DOMAIN
        ),
        "REF-WINDOW-MISSING-0-2-0": RefusalReason.TAIL_WINDOW_MISSING,
    }


@pytest.mark.contract
@pytest.mark.oracle
def test_every_frozen_refusal_is_produced_with_its_check_named() -> None:
    """The `fail_closed` convention, case by case."""
    assert rp_oracle("O-RP-INTERFACE").kind == "fail-closed"
    expected = _expected()
    covered = set(expected)
    frozen = {case.case_id for case in REFUSAL_CASES}
    # The two registry-0.1.3 rows this pass retires are marked in the freeze and are no
    # longer built: REF-EPS-HYP-MISSING outright (its input is gone) and
    # REF-WINDOW-MISSING rewritten to REF-WINDOW-MISSING-0-2-0 below.
    assert is_superseded("REF-EPS-HYP-MISSING")
    assert is_superseded("REF-WINDOW-MISSING")
    retired = {"REF-EPS-HYP-MISSING", "REF-WINDOW-MISSING"}
    assert covered | retired | {"FALLBACK-CERTIFIED-TO-ESTIMATE"} == frozen
    for case in REFUSAL_CASES:
        if case.case_id not in expected:
            continue
        refusal = _refusal_for(case.case_id)
        assert refusal.reason is expected[case.case_id], case.case_id
        assert refusal.detail.strip(), case.case_id
        # A refusal is a RECORD, with a machine-readable reason.
        record = refusal.as_machine_record()
        assert record["reason"] == str(refusal.reason)


@pytest.mark.contract
@pytest.mark.oracle
def test_every_0_2_0_refusal_row_is_produced_with_its_reason() -> None:
    """The registry-0.2.0 refusal table, row by row, plus the one unspelled row."""
    assert rp_oracle("O-RP-REASONS").kind == "fail-closed"
    expected = _expected_0_2_0()
    frozen = {case.case_id: case for case in REFUSAL_CASES_0_2_0}
    # Every frozen registry-0.2.0 row is a refusal here except the tier fallback, which
    # EMITS AN ARTIFACT and belongs to the request-to-artifact pass.
    assert set(expected) | {
        case.case_id for case in REFUSAL_CASES_0_2_0 if case.emits_artifact
    } == set(frozen)
    for case_id, reason in expected.items():
        refusal = _refusal_for(case_id)
        assert refusal.reason is reason, case_id
        assert refusal.detail.strip(), case_id
        case = frozen[case_id]
        assert case.emits_artifact is False, case_id
        if case.reason_is_verbatim:
            assert str(refusal.reason) == case.reason, case_id
        else:
            assert case.reason is None, case_id


@pytest.mark.contract
@pytest.mark.oracle
def test_the_reason_vocabulary_is_the_eight_of_the_nine_the_code_keeps() -> None:
    """The refusal rules at registry 0.3.0: eight refusals; the ninth left the code.

    ``REFUSAL_REASONS_VERBATIM`` -- the registry's ONE-ELEMENT 0.1.3 tuple -- is
    marked in ``SUPERSEDED_BY_0_2_0``, and its registry-0.2.0 replacements are in turn
    marked in ``SUPERSEDED_BY_0_3_0``: each is an ENUMERATION the next amendment
    widens, never a value one changes. Both marks are asserted here so that
    neither supersession is silent.

    The module's vocabulary is compared against
    ``REASON_VOCABULARY_RECEIVER_0_1_2``, the eight it carries;
    ``receiver_grams_not_enclosed`` is not a ``RefusalReason`` (there is no
    ``certified`` tier). Nothing frozen is rewritten.
    """
    assert is_superseded("REFUSAL_REASONS_VERBATIM")
    assert is_superseded_0_3_0("REFUSAL_REASONS_VERBATIM_0_2_0")
    assert is_superseded_0_3_0("REASON_VOCABULARY_0_2_0")
    assert is_superseded_0_3_0("REASON_EMITS_ARTIFACT")
    # receiver 0.7.0 adds ONE contract-verbatim refusal after the frozen
    # eight, the efficiency normalization's
    # (detector-imperfections/req:efficiency-normalization), named here as
    # the delta the frozen registry does not carry.
    added_at_0_7_0 = ("efficiency_normalization_out_of_range",)
    assert (
        tuple(str(reason) for reason in MODULE_VERBATIM)
        == REFUSAL_REASONS_VERBATIM_0_3_0 + added_at_0_7_0
    )
    assert TIER_FALLBACK_REASON_VERBATIM not in {str(r) for r in RefusalReason}
    assert RETIRED_FROM_THE_CODE_RECEIVER_0_1_2 == (TIER_FALLBACK_REASON_VERBATIM,)
    assert (
        tuple(str(reason) for reason in MODULE_VOCABULARY)
        == REASON_VOCABULARY_RECEIVER_0_1_2 + added_at_0_7_0
    )
    # The fallback was the ONLY one of the nine that emitted an artifact, which
    # is why the eight the code keeps are exactly the refusals.
    emits = dict(REASON_EMITS_ARTIFACT_0_3_0)
    assert emits[TIER_FALLBACK_REASON_VERBATIM] is True
    assert not any(emits[reason] for reason in REFUSAL_REASONS_VERBATIM_0_3_0)
    # The five verbatim refusals are exactly the frozen verbatim registry-0.2.0 rows.
    verbatim = {
        case.reason
        for case in REFUSAL_CASES_0_2_0
        if case.reason_is_verbatim and not case.emits_artifact
    }
    # The registry-0.2.0 rows carry the FIVE that table spelled, which is a
    # SUBSET of the eight of registry 0.3.0: it adds three rows and removes none.
    assert verbatim < set(REFUSAL_REASONS_VERBATIM_0_3_0)
    assert len(verbatim) == 5


@pytest.mark.contract
@pytest.mark.oracle
def test_the_six_unspelled_conditions_carry_no_contract_key() -> None:
    """The unspelled refusals: the identity is contract, the spelling is code's.

    ``interface.yaml`` ``refusals.named_without_a_spelling_note``.

    Each refuses with one of this module's OWN keys, and none of those keys is
    in the contract's vocabulary -- which is what "with a reason string the
    implementer names" means and what an implementation would violate by
    re-using one of the spelled strings for a condition the table does not name.
    """
    ours = (
        RefusalReason.INPUT_ROUTES_NOT_EXACTLY_ONE,
        RefusalReason.GRAPH_CONDITION_E1_FAILED,
        RefusalReason.PARAMETER_TOLERANCE_NOT_ZERO,
        RefusalReason.TAIL_WINDOW_MISSING,
        RefusalReason.NUMERICAL_TOLERANCE_MISSING,
        RefusalReason.PROBE_MEAN_PHOTON_NUMBER_NEGATIVE,
    )
    # SEVEN unspelled conditions at registry 0.3.0 against six enum members exercised
    # here: the seventh is Def. def:tolmap (iv)'s, whose own key is
    # BOUND_DATA_NOT_ADMISSIBLE and which is replayed in the exact-window
    # validation file rather than here.
    assert len(ours) + 1 == len(REFUSALS_NAMED_WITHOUT_A_SPELLING_0_3_0)
    for reason in ours:
        assert str(reason) not in REASON_VOCABULARY_0_3_0
    assert str(RefusalReason.BOUND_DATA_NOT_ADMISSIBLE) not in REASON_VOCABULARY_0_3_0
    # And the missing-tolerance one is really produced, not merely named.
    refusal = _refusal_for("REF-TOLERANCE-MISSING")
    assert refusal.reason is RefusalReason.NUMERICAL_TOLERANCE_MISSING
    assert "eps_5" in refusal.detail


@pytest.mark.contract
def test_the_contract_prose_reason_is_carried_and_is_not_a_machine_key() -> None:
    """`parameters.exactness`: the reason is prose, in its own quotation marks."""
    refusal = _refusal_for("REF-NONZERO-TOLERANCE")
    assert "parameter uncertainty sets are out of scope" in refusal.detail
    assert str(refusal.reason) != "parameter uncertainty sets are out of scope"
    frozen = next(c for c in REFUSAL_CASES if c.case_id == "REF-NONZERO-TOLERANCE")
    assert frozen.reason_is_verbatim is False


@pytest.mark.contract
def test_a_refusal_is_a_record_and_never_an_exception() -> None:
    """`fail_closed`: a refusal is emitted INSTEAD OF an artifact, never raised."""
    assert not issubclass(Refusal, BaseException)
    for case_id in {**_expected(), **_expected_0_2_0()}:
        refusal = _refusal_for(case_id)
        assert isinstance(refusal, Refusal)
        assert not isinstance(refusal, BaseException)
