"""The honest envelope: the box and its completeness over ``[p^-, p^+]``.

The box is restated over a per-outcome range under A-HON-ENV. What
these tests pin:

* the DEGENERATE envelope is the one-law construction, record and all, on every
  route -- which is what keeps every frozen oracle of this module valid;
* a non-degenerate outcome's lower endpoint is the rule at ``p^-`` and its upper
  endpoint the rule at ``p^+``, each with its own guard, while degenerate
  outcomes of the same request are untouched;
* every law of the envelope lies in the emitted set (``thm:box-construction`` (iii));
* ``epsilon_star`` is the lower tails at ``p^-`` plus the upper tails at ``p^+``
  (``thm:completeness-bound``);
* the new code ``honest_envelope_not_admissible`` (``thm:honest-containment`` (iii));
* one HAND-DERIVED oracle, worked in the docstring, never regenerated from code.
"""

from __future__ import annotations

from fractions import Fraction

import pytest

from certiqs_key.statistics import (
    ENVELOPE_MODEL_TAG,
    HONEST_MODEL_TAG,
    AcceptanceConstruction,
    AcceptanceRequest,
    EnvelopeInterval,
    HonestEnvelope,
    HypothesisError,
    InfeasibilityReason,
    InfeasibleInput,
    OutcomeInterval,
    SingletonGeometry,
    construct,
    lower_tail,
    singleton_completeness,
    upper_tail,
)
from certiqs_key.statistics.rules import interval_for_rule, resolve_rule

F = Fraction
ALPHABET = ("a", "b", "c")
POINT = {"a": F(1, 2), "b": F(3, 10), "c": F(1, 5)}
ENVELOPE = HonestEnvelope(
    lower={"a": F(2, 5), "b": F(3, 10), "c": F(1, 10)},
    upper={"a": F(3, 5), "b": F(3, 10), "c": F(3, 10)},
)
ROUTES = (
    ("exact", "sweep"),
    ("exact", "enclosure"),
    ("bernstein", "sweep"),
    ("bernstein", "enclosure"),
)


def _built(
    honest: object, rule: str = "exact", evaluation: str = "sweep", rounds: int = 2000
) -> AcceptanceConstruction:
    result = construct(
        AcceptanceRequest(
            alphabet=ALPHABET,
            honest=honest,  # type: ignore[arg-type]
            rounds=rounds,
            budget=F(1, 10**4),
            endpoint_rule=rule,
            tail_evaluation=evaluation,
        )
    )
    assert isinstance(result, AcceptanceConstruction)
    return result


@pytest.mark.parametrize(("rule", "evaluation"), ROUTES)
def test_the_degenerate_envelope_is_the_one_law_construction(
    rule: str, evaluation: str
) -> None:
    point = _built(POINT, rule, evaluation)
    envelope = _built(HonestEnvelope(lower=POINT, upper=POINT), rule, evaluation)
    assert envelope.acceptance_set == point.acceptance_set
    assert envelope.completeness_certified == point.completeness_certified
    assert envelope.honest_model == point.honest_model
    assert envelope.honest_model.tag == HONEST_MODEL_TAG
    assert envelope.honest_model.as_machine_record() == (
        point.honest_model.as_machine_record()
    )
    assert "honest_envelope" not in point.honest_model.as_machine_record()


@pytest.mark.parametrize(("rule", "evaluation"), ROUTES)
def test_each_side_is_the_rule_at_its_own_end_of_the_envelope(
    rule: str, evaluation: str
) -> None:
    built = _built(ENVELOPE, rule, evaluation)
    box = built.acceptance_set.box_bounds
    assert box is not None
    lower, upper = box
    route = resolve_rule(rule, evaluation)  # type: ignore[arg-type]
    eps = F(1, 10**4) / 6
    for index, chat in enumerate(ALPHABET):
        low = F(ENVELOPE.lower[chat])
        high = F(ENVELOPE.upper[chat])
        at_low = interval_for_rule(2000, low, eps, eps, route)
        at_high = interval_for_rule(2000, high, eps, eps, route)
        assert lower[index] == at_low.box_lower
        assert upper[index] == at_high.box_upper
        record = built.intervals[index]
        if low == high:
            # A degenerate outcome takes the one-law route, unchanged.
            assert isinstance(record, OutcomeInterval)
        else:
            assert isinstance(record, EnvelopeInterval)


def test_every_law_of_the_envelope_is_accepted() -> None:
    built = _built(ENVELOPE)
    box = built.acceptance_set.box_bounds
    assert box is not None
    lower, upper = box
    # The envelope's vertices on the simplex, and an interior law.
    laws = [
        (F(2, 5), F(3, 10), F(3, 10)),
        (F(3, 5), F(3, 10), F(1, 10)),
        (F(1, 2), F(3, 10), F(1, 5)),
        (F(9, 20), F(3, 10), F(1, 4)),
    ]
    for law in laws:
        assert sum(law) == 1
        assert all(
            lo <= value <= hi for lo, value, hi in zip(lower, law, upper, strict=True)
        )


def test_epsilon_star_reads_the_lower_tail_at_p_minus_and_the_upper_at_p_plus() -> None:
    built = _built(ENVELOPE)
    total = F(0)
    exact = True
    for record in built.intervals:
        assert record is not None
        if isinstance(record, EnvelopeInterval):
            below = lower_tail(record.rounds, record.honest_lower, record.k_lower)
            above = upper_tail(record.rounds, record.honest_upper, record.k_upper)
        else:
            below = lower_tail(record.rounds, record.honest, record.k_lower)
            above = upper_tail(record.rounds, record.honest, record.k_upper)
        exact = exact and below.exact and above.exact
        total += below.upper + above.upper
    assert built.completeness_exact is exact
    assert built.completeness_certified == total
    assert total <= F(1, 10**4)


def test_the_record_names_the_envelope_and_the_tag() -> None:
    built = _built(ENVELOPE)
    record = built.honest_model.as_machine_record()
    assert record["tag"] == ENVELOPE_MODEL_TAG
    assert record["honest_distribution"] is None
    assert record["honest_envelope"] == {
        "lower": tuple(F(ENVELOPE.lower[chat]) for chat in ALPHABET),
        "upper": tuple(F(ENVELOPE.upper[chat]) for chat in ALPHABET),
    }


def test_the_hand_derived_envelope_oracle() -> None:
    """``n = 4``, ``Chat = {a, b}``, ``p^-(a) = 1/2``, ``p^+(a) = 3/4``, ecomp = 9/10.

    The envelope of ``b`` is the mirror, ``[1/4, 1/2]``. The uniform rule gives
    every tail the share ``eps = (9/10) / 4 = 9/40``. By hand, with the exact rule:

    * ``a``, lower side, ``Bin(4, 1/2)`` with masses ``(1, 4, 6, 4, 1)/16``:
      ``Pr[N < 1] = 1/16 <= 9/40`` and ``Pr[N < 2] = 5/16 > 9/40``, so
      ``kappa^- = 1``; the guard ``min{1, floor(4 * 1/2)} = 1``: ``k^- = 1``.
    * ``a``, upper side, ``Bin(4, 3/4)`` with masses ``(1, 12, 54, 108, 81)/256``:
      ``Pr[N > 3] = 81/256 > 9/40``, so ``kappa^+ = 4`` and ``k^+ = 4``.
    * ``b``, lower side, ``Bin(4, 1/4)``: ``Pr[N < 1] = 81/256 > 9/40``, so
      ``kappa^- = 0`` and ``k^- = 0``.
    * ``b``, upper side, ``Bin(4, 1/2)``: ``Pr[N > 3] = 1/16 <= 9/40`` and
      ``Pr[N > 2] = 5/16 > 9/40``, so ``kappa^+ = 3``; the guard
      ``max{3, ceil(4 * 1/2)} = 3``: ``k^+ = 3``.

    So ``q(a) in [1/4, 1]``, ``q(b) in [0, 3/4]``, and ``epsilon_star =
    1/16 + 0 + 0 + 1/16 = 1/8``.
    """
    result = construct(
        AcceptanceRequest(
            alphabet=("a", "b"),
            honest=HonestEnvelope(
                lower={"a": F(1, 2), "b": F(1, 4)},
                upper={"a": F(3, 4), "b": F(1, 2)},
            ),
            rounds=4,
            budget=F(9, 10),
        )
    )
    assert isinstance(result, AcceptanceConstruction)
    assert result.acceptance_set.box_bounds == (
        (F(1, 4), F(0)),
        (F(1), F(3, 4)),
    )
    assert result.completeness_certified == F(1, 8)
    assert result.completeness_exact


@pytest.mark.parametrize(
    ("lower", "upper"),
    [
        # p^- > p^+ at an outcome.
        ({"a": F(1, 2), "b": F(1, 2)}, {"a": F(2, 5), "b": F(3, 5)}),
        # an entry outside [0, 1].
        ({"a": F(-1, 10), "b": F(1, 2)}, {"a": F(1, 2), "b": F(1, 2)}),
        # sum p^- > 1.
        ({"a": F(3, 5), "b": F(3, 5)}, {"a": F(3, 5), "b": F(3, 5)}),
        # sum p^+ < 1.
        ({"a": F(1, 5), "b": F(1, 5)}, {"a": F(2, 5), "b": F(2, 5)}),
        # a coordinate outside Chat.
        ({"a": F(1, 2), "z": F(1, 2)}, {"a": F(1, 2), "b": F(1, 2)}),
    ],
)
def test_an_envelope_no_law_lies_in_is_refused(
    lower: dict[str, Fraction], upper: dict[str, Fraction]
) -> None:
    result = construct(
        AcceptanceRequest(
            alphabet=("a", "b"),
            honest=HonestEnvelope(lower=lower, upper=upper),
            rounds=10,
            budget=F(1, 10),
        )
    )
    assert isinstance(result, InfeasibleInput)
    assert (
        result.infeasibility_report.reason
        is InfeasibilityReason.HONEST_ENVELOPE_NOT_ADMISSIBLE
    )


def test_a_float_in_the_envelope_is_not_rational() -> None:
    result = construct(
        AcceptanceRequest(
            alphabet=("a", "b"),
            honest=HonestEnvelope(
                lower={"a": 0.25, "b": F(1, 2)},  # type: ignore[dict-item]
                upper={"a": F(1, 2), "b": F(3, 4)},
            ),
            rounds=10,
            budget=F(1, 10),
        )
    )
    assert isinstance(result, InfeasibleInput)
    assert result.infeasibility_report.reason is InfeasibilityReason.INPUTS_NOT_RATIONAL


def test_the_singleton_refuses_a_non_degenerate_envelope() -> None:
    """``rem:singleton-honest``: the point form only; a degenerate envelope is its law.

    The interface row names the refusal ``honest_envelope_not_degenerate``;
    a bare ``TypeError`` would not be it.
    """
    geometry = SingletonGeometry(outcomes=("a", "b"), frequencies=(F(1, 2), F(1, 2)))
    law = {"a": F(1, 2), "b": F(1, 2)}
    degenerate = singleton_completeness(
        geometry, HonestEnvelope(lower=law, upper=law), 4
    )
    assert degenerate == singleton_completeness(geometry, (F(1, 2), F(1, 2)), 4)
    envelope = HonestEnvelope(
        lower={"a": F(2, 5), "b": F(1, 2)}, upper={"a": F(1, 2), "b": F(3, 5)}
    )
    with pytest.raises(HypothesisError, match="honest_envelope_not_degenerate"):
        singleton_completeness(geometry, envelope, 4)
