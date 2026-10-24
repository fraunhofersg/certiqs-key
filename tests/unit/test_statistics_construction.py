"""SA4, SA5, SA6, SA7 -- the construction map's own behaviour.

Three things live here that the frozen registry cannot pin.

* THE REPORTING RULE OF REMARK ``rem:epsstar``, including its CLAMP. Every
  frozen ``epsilon_star`` is exact, so no frozen case exercises the clamp, and
  the registry says so ("a gap in COVERAGE, not in the contract"). The rule is a
  named function here and both of its branches are tested directly.
* THE THREE IMPLEMENTATION CHOICES ``interface.yaml`` records as OPEN. Each is
  decided at one site in the source, with the decision written into that site's
  docstring, and each is pinned here: the empty-selector allocation, the
  serialized sub-keys of ``acceptance_set``, and the sub-keys of
  ``honest_model``.
* THE LINE BETWEEN A REPORT AND A REFUSAL. The TEN codes of Theorem
  ``thm:honest-containment`` (iii) are the whole vocabulary, so an argument that is not
  a presentation of an input at all must NOT acquire an ELEVENTH code; it
  raises.

THE CLAIMS CITED. There is no assumption A-RATIONAL: the condition is the
definition ``def:conservative-evaluation``, decided by requirements, and its
"Consequently" sentence is ``binomial-box/lem:widening``; this file names
those, so that a test and the line it tests name the same claim.
(``receiver/ass:exact`` owns A-EXACT for a different assumption, the exact
window; the frozen registry keeps A-EXACT wherever a derivation names it, and
says at its own site why.)
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from fractions import Fraction

import pytest

from certiqs_key.statistics import (
    AcceptanceRequest,
    BudgetAllocation,
    EnclosureParameters,
    HonestModel,
    InfeasibilityReason,
    MalformedInputError,
    canonical_box,
    construct,
    lower_tail,
    report_completeness,
    resolve,
    uniform_allocation,
    upper_tail,
    validate_request,
)
from certiqs_key.statistics import tails as tails_module

TWO_LETTER = ("c0", "c1")
FAIR = {"c0": Fraction(1, 2), "c1": Fraction(1, 2)}


def request(**overrides: object) -> AcceptanceRequest:
    """Return an admissible request with the named fields replaced."""
    fields: dict[str, object] = {
        "alphabet": TWO_LETTER,
        "honest": FAIR,
        "rounds": 8,
        "budget": Fraction(1, 5),
    }
    fields.update(overrides)
    return AcceptanceRequest(**fields)


# ---------------------------------------------------------------------------
#  Remark rem:epsstar -- the reporting rule and its clamp
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_the_completeness_reporting_rule_clamps_at_the_budget() -> None:
    """Remark rem:epsstar: report ``min{ecomp, tilde-epsilon}``, always.

    The clamp exists for one situation and the remark names it: upward rounding
    can carry the reported figure ABOVE ``ecomp`` -- "in the degenerate case
    where every tail meets its allocation exactly and the allocation sums to
    exactly ``ecomp``, any strict over-estimate exceeds the budget and leaves
    the declared output domain ``[0, ecomp]``". Both branches are exercised
    here, on the function itself, because on the exact evaluation route the
    clamp CANNOT bind: ``epsilon_star <= ecomp`` is part of Eq.
    ``eq:completeness``, so a frozen case cannot reach it.
    """
    budget = Fraction(1, 10)
    # The ordinary branch: an exactly evaluated epsilon_star is already inside.
    assert report_completeness(Fraction(1, 100), budget) == Fraction(1, 100)
    assert report_completeness(budget, budget) == budget
    assert report_completeness(Fraction(0), budget) == 0
    # The clamp: an upward-rounded evaluation above the budget. Still a valid
    # bound -- both numbers are at least the true epsilon_star -- and back
    # inside the declared output domain.
    assert report_completeness(Fraction(11, 100), budget) == budget
    assert report_completeness(Fraction(1), budget) == budget
    for reported in (Fraction(1, 100), budget, Fraction(11, 100), Fraction(1)):
        assert 0 <= report_completeness(reported, budget) <= budget


@pytest.mark.contract
def test_epsilon_star_is_summed_at_the_emitted_endpoints() -> None:
    """Remark rem:epsstar's first paragraph, as a number.

    ``epsilon_star`` is the sum of the tails AT THE EMITTED ENDPOINTS -- not at
    ``kappa^{+-}`` and not at the allocation. The integrality of ``k^{+-}`` and
    the guard both leave budget unspent, so the reported figure is generally
    strictly below ``ecomp``, and here it is far below: ``9/10`` is allocated to
    one tail and the guard then moves that endpoint DOWN, where the tail is
    smaller still.
    """
    result = construct(
        request(
            rounds=10,
            constrained=("c0",),
            budget=Fraction(19, 20),
            allocation=BudgetAllocation(
                lower=(Fraction(9, 10),), upper=(Fraction(1, 20),)
            ),
        )
    )
    assert result.completeness_certified == Fraction(397, 1024)
    assert result.completeness_certified < Fraction(19, 20)
    assert result.completeness_exact is True


@pytest.mark.contract
def test_epsilon_star_is_summed_from_the_upper_ends_of_the_enclosures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Remark rem:epsstar: the reported figure ROUNDS UP, never down.

    Every frozen case takes the exact route, where an enclosure's two ends
    coincide, so no frozen case can see which end ``epsilon_star`` is summed
    from. Forcing the enclosure route separates them: summing the LOWER ends
    gives a figure strictly below the exact ``epsilon_star``, which is the
    downward-rounded report Remark ``rem:epsstar`` rules out in as many words --
    "reporting a downward-rounded epsilon_star would claim a completeness the
    set does not have".
    """
    exact = construct(request())
    assert exact.completeness_exact is True
    reference = exact.completeness_certified
    monkeypatch.setattr(tails_module, "EXACT_TAIL_BIT_BUDGET", 0)
    enclosed = construct(request())
    assert enclosed.completeness_exact is False
    # The figure is a valid bound: at least the exact one, and still inside the
    # declared output domain [0, ecomp] after the clamp.
    assert enclosed.completeness_certified >= reference
    assert enclosed.completeness_certified <= request().budget
    # And the other end would NOT be: this is what the assertion above buys.
    lower_ends = sum(
        (
            lower_tail(8, Fraction(1, 2), interval.k_lower).lower
            + upper_tail(8, Fraction(1, 2), interval.k_upper).lower
            for interval in enclosed.intervals
            if interval is not None
        ),
        Fraction(0),
    )
    assert lower_ends < reference


# ---------------------------------------------------------------------------
#  The three implementation choices interface.yaml records as OPEN
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_the_empty_selector_allocation_is_the_pair_of_empty_vectors() -> None:
    """The first open choice: ``ecomp / (2 |Chat_con|)`` at ``|Chat_con| = 0``.

    The rule's denominator vanishes, and the resolution is that the division is
    performed ONCE PER CONSTRAINED OUTCOME -- so on an empty selector it is
    never performed at all. No special case, no chosen value: there is nothing
    to evaluate the rule at.
    """
    allocation = uniform_allocation((), Fraction(3, 10))
    assert allocation.lower == ()
    assert allocation.upper == ()
    # And the same input runs end to end: Theorem thm:monotonicity-limits (vi)'s second
    # branch, where epsilon_star is an EMPTY SUM rather than a sum of zeros.
    result = construct(request(constrained=()))
    assert result.acceptance_set is not None
    assert result.acceptance_set.box_bounds == ((Fraction(0),) * 2, (Fraction(1),) * 2)
    assert result.completeness_certified == 0
    assert result.honest_model is not None
    assert result.honest_model.constrained_outcomes == ()


@pytest.mark.contract
def test_the_acceptance_set_record_carries_the_decided_sub_keys() -> None:
    """The second open choice: the serialized sub-keys of ``acceptance_set``.

    contract.tex fixes ``geometry_tag`` and ``box_bounds`` and names the rest by
    SYMBOL alone. The keys are the consumer's own field names for the same
    objects, so that one object does not acquire two vocabularies.
    """
    result = construct(request())
    assert result.acceptance_set is not None
    record = result.acceptance_set.as_machine_record()
    assert set(record) == {"geometry_tag", "box_bounds", "m_row", "rows", "rhs"}
    assert record["geometry_tag"] == "polytope"
    assert record["m_row"] == 4
    # A polytope NOT in canonical box form omits the key rather than writing
    # null: the key's presence is what claims the sub-form.
    general = canonical_box(TWO_LETTER, (Fraction(0), Fraction(0)), (Fraction(1),) * 2)
    without_box = type(general)(
        outcomes=general.outcomes, rows=general.rows, rhs=general.rhs
    )
    assert "box_bounds" not in without_box.as_machine_record()


@pytest.mark.contract
def test_the_honest_model_record_carries_the_decided_sub_keys() -> None:
    """The third open choice: the sub-keys of ``honest_model``.

    The outputs table fixes the ITEMS and the tag's value and no machine key
    for any item beside the tag. The first five keys are the INPUT-TABLE
    machine keys of the same five objects, which are the contract's own names
    for exactly these things.

    EIGHT ITEMS, and the last three are named here rather than the assertion
    being loosened: the rule, the evaluation and the evaluation parameters,
    which ``binomial-box/req:honest-model-record`` requires the record to
    carry, because the emitted endpoints and the figure are functions of
    them. The default route records an empty parameter tuple: the
    sweep has none of its own.
    """
    result = construct(request())
    assert result.honest_model is not None
    record = result.honest_model.as_machine_record()
    assert list(record) == [
        "tag",
        "honest_distribution",
        "rounds",
        "constrained_outcomes",
        "budget_allocation",
        "endpoint_rule",
        "tail_evaluation",
        "evaluation_parameters",
    ]
    assert record["tag"] == "iid_honest_rounds"
    assert record["rounds"] == 8
    assert record["constrained_outcomes"] == TWO_LETTER
    assert record["endpoint_rule"] == "exact"
    assert record["tail_evaluation"] == "sweep"
    assert record["evaluation_parameters"] == ()


# ---------------------------------------------------------------------------
#  SA6 (iii) -- reports, refusals, and the line between them
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_a_malformed_presentation_raises_rather_than_acquiring_a_code() -> None:
    """The ten codes are the whole vocabulary; an eleventh is not invented.

    Each argument below is not a presentation of an input the contract types, so
    no domain clause can be READ against it -- ``|Chat|``, ``p^hon in
    Delta(Chat)`` and ``Chat_con subset Chat`` are untestable rather than false.
    """
    with pytest.raises(MalformedInputError, match="repeats a label"):
        construct(request(alphabet=("c0", "c0"), honest={"c0": Fraction(1)}))
    with pytest.raises(MalformedInputError, match="is a str"):
        construct(request(alphabet="c0c1"))
    with pytest.raises(MalformedInputError, match="no fixed enumeration"):
        construct(request(alphabet={"c0", "c1"}))
    with pytest.raises(MalformedInputError, match="must be presented as a mapping"):
        construct(request(honest=(Fraction(1, 2), Fraction(1, 2))))
    with pytest.raises(MalformedInputError, match="repeats a label"):
        construct(request(constrained=("c0", "c0")))
    with pytest.raises(MalformedInputError, match="pair of vectors ON Chat_con"):
        construct(
            request(
                constrained=("c0",),
                allocation=BudgetAllocation(
                    lower=(Fraction(0), Fraction(0)), upper=(Fraction(0),)
                ),
            )
        )


@pytest.mark.contract
def test_the_failure_branch_has_no_acceptance_set_to_read() -> None:
    """Section 2.2: a report is emitted INSTEAD OF a set, never beside one.

    Structural rather than conventional: the failure branch is a different type
    whose four output slots are fixed at ``None``, so a caller cannot reach a
    box past a report by ignoring a flag, and a "best-effort" box beside a
    warning is not expressible.
    """
    result = construct(request(rounds=0))
    assert result.infeasibility_report is not None
    assert result.acceptance_set is None
    assert result.acceptance_support is None
    assert result.completeness_certified is None
    assert result.honest_model is None
    with pytest.raises(FrozenInstanceError):
        result.acceptance_set = object()  # type: ignore[misc]


@pytest.mark.contract
def test_a_float_is_refused_and_an_explicit_rational_is_not() -> None:
    """Exact data at the boundary, and what the refusal costs a caller.

    ``def:conservative-evaluation``'s input half, refused with
    ``inputs_not_rational``. A binary64 value IS an exact rational, so refusing
    it is stricter than the letter of that definition; what it buys is that
    ``0.1`` never silently becomes ``1/10``. The caller converts explicitly,
    which is the caller SAYING which rational it means -- and both readings are
    then accepted, because both are exact.
    """
    for report in (
        construct(request(budget=0.2)).infeasibility_report,
        construct(
            request(honest={"c0": 0.5, "c1": Fraction(1, 2)})
        ).infeasibility_report,
        construct(
            request(
                constrained=("c0",),
                allocation=BudgetAllocation(lower=(0.05,), upper=(Fraction(1, 20),)),
            )
        ).infeasibility_report,
    ):
        assert report is not None
        assert report.reason is InfeasibilityReason.INPUTS_NOT_RATIONAL
    assert construct(request(budget=Fraction(1, 5))).infeasibility_report is None
    assert construct(request(budget=Fraction(0.2))).infeasibility_report is None
    assert construct(request(budget=0)).infeasibility_report is None


@pytest.mark.contract
def test_one_round_is_admissible_and_zero_rounds_is_not() -> None:
    """Section 2.1: ``n >= 1``. The left end is admissible and not an edge case.

    Theorem ``thm:binomial-tails`` is stated for ``n >= 1`` and the tails are trivial
    there. ``n = 0`` is refused because every construction step divides by
    ``n``, and the proof of Theorem ``thm:completeness-bound``'s event-inclusion step
    says "using ``n > 0``" in as many words.
    """
    result = construct(request(rounds=1))
    assert result.infeasibility_report is None
    assert result.acceptance_set is not None
    for rounds in (0, -3):
        report = construct(request(rounds=rounds)).infeasibility_report
        assert report is not None
        assert report.reason is InfeasibilityReason.ROUNDS_OUT_OF_RANGE


@pytest.mark.contract
def test_the_default_selector_is_the_whole_alphabet() -> None:
    """Section 2.1: ``Chat_con`` has DEFAULT ``Chat`` -- and ``()`` is not it.

    ``None`` means "the declared default" and the empty selector is an input in
    its own right (Theorem ``thm:monotonicity-limits`` (vi)), so the two must not
    collapse.
    """
    default = construct(request())
    explicit = construct(request(constrained=TWO_LETTER))
    empty = construct(request(constrained=()))
    assert default.acceptance_set == explicit.acceptance_set
    assert default.acceptance_set != empty.acceptance_set
    assert resolve(request()).constrained == TWO_LETTER
    assert resolve(request(constrained=())).constrained == ()


@pytest.mark.contract
def test_the_default_allocation_is_the_uniform_rule() -> None:
    """Section 2.1's default, materialized where the request leaves it open."""
    resolved = resolve(request(budget=Fraction(1, 5)))
    assert resolved.eps_lower == (Fraction(1, 20), Fraction(1, 20))
    assert resolved.eps_upper == (Fraction(1, 20), Fraction(1, 20))
    assert sum(resolved.eps_lower) + sum(resolved.eps_upper) == resolved.budget


# ---------------------------------------------------------------------------
#  SA7 -- the parameter behaviour, off the frozen pairs
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_the_set_is_non_increasing_in_the_budget() -> None:
    """Theorem thm:monotonicity-limits (i): a LARGER budget buys a SMALLER set.

    Under the default uniform rule, which Definition ``def:monotone-rule``
    records as monotone. The direction is the one a reader expecting "budget
    buys room" would guess wrong, so it is asserted over a sweep rather than on
    one pair.
    """
    previous = None
    for index in range(20):
        budget = Fraction(index, 20)
        result = construct(request(rounds=12, budget=budget))
        assert result.acceptance_set is not None
        assert result.acceptance_set.box_bounds is not None
        lower, upper = result.acceptance_set.box_bounds
        if previous is not None:
            for before, after in zip(previous[0], lower, strict=True):
                assert before <= after
            for before, after in zip(previous[1], upper, strict=True):
                assert after <= before
        previous = (lower, upper)


@pytest.mark.contract
def test_a_zero_budget_buys_the_whole_simplex() -> None:
    """Theorem thm:monotonicity-limits (iii), and the reading the contract attaches to it.

    With ``0 < p^hon(chat) < 1`` on every constrained outcome the emitted set is
    the whole simplex and ``epsilon_star = 0``: the bound is met with equality
    at ``0``, by giving up everything. "A protocol that will not tolerate ANY
    chance of an honest abort cannot test anything."
    """  # noqa: E501
    result = construct(request(budget=Fraction(0)))
    assert result.acceptance_set is not None
    assert result.acceptance_set.box_bounds == (
        (Fraction(0), Fraction(0)),
        (Fraction(1), Fraction(1)),
    )
    assert result.completeness_certified == 0


@pytest.mark.contract
@pytest.mark.parametrize("constrained", [None, ()])
def test_a_one_letter_alphabet_is_constant_in_every_parameter(
    constrained: tuple[str, ...] | None,
) -> None:
    """Theorem thm:monotonicity-limits (vi): both branches, and they agree.

    On ``Chat = {c0}`` the input domain FORCES ``p^hon = delta_{c0}``, and the
    emitted set is simultaneously the whole simplex and a single point -- on one
    letter the simplex has one element. Nothing here depends on ``n``,
    ``ecomp`` or the allocation.
    """
    emitted = set()
    for rounds in (1, 7, 30):
        for budget in (Fraction(0), Fraction(3, 10), Fraction(99, 100)):
            result = construct(
                AcceptanceRequest(
                    alphabet=("c0",),
                    honest={"c0": Fraction(1)},
                    rounds=rounds,
                    budget=budget,
                    constrained=constrained,
                )
            )
            assert result.acceptance_set is not None
            assert result.completeness_certified == 0
            assert result.acceptance_support == ("c0",)
            emitted.add(result.acceptance_set.box_bounds)
    # Constant in n, ecomp and the allocation: one box for the whole grid.
    assert len(emitted) == 1


@pytest.mark.contract
def test_a_non_reachable_honest_model_is_not_this_modules_to_detect() -> None:
    """Assumption A-REACH, and the deliberate limit of Theorem thm:honest-containment (ii).

    A-REACH is "an obligation of the honest distribution provider together with
    the declaration; this contract never verifies it", and the frozen registry
    records that no case can be frozen for a violation because "a violating
    input is not distinguishable from an admissible one by anything this module
    can compute". So the construction must succeed on any admissible input,
    and there must be NO REACHABILITY FIELD TO FILL: what carries the honest
    model is the ``honest_model`` record, whose items are exactly the ones the
    contract and ``interface.yaml`` list -- the contract's five plus the three
    that name the route (the rule, the evaluation and the evaluation
    parameters, the sibling test above), and ``honest_upper``, the upper side of
    an honest envelope, which is ``None`` on a one-law request. NONE OF THEM IS A REACHABILITY CLAIM, which is what this
    test is for.
    """  # noqa: E501
    result = construct(request())
    assert result.honest_model is not None
    assert set(vars(result.honest_model)) == {
        "tag",
        "honest_distribution",
        "rounds",
        "constrained_outcomes",
        "budget_allocation",
        "endpoint_rule",
        "tail_evaluation",
        "evaluation_parameters",
        "honest_upper",
    }
    assert validate_request(request()) is None


@pytest.mark.contract
def test_the_honest_model_record_is_immutable() -> None:
    """Completeness is meaningful only relative to this record (Section 2.2)."""
    model = HonestModel(
        tag="iid_honest_rounds",
        honest_distribution=(Fraction(1),),
        rounds=4,
        constrained_outcomes=("c0",),
        budget_allocation=uniform_allocation(("c0",), Fraction(1, 2)),
    )
    with pytest.raises(FrozenInstanceError):
        model.rounds = 5  # type: ignore[misc]


# ---------------------------------------------------------------------------
#  The parameters in force, and the record that names them
# ---------------------------------------------------------------------------


COARSE_ENCLOSURE = EnclosureParameters(
    root_exponent=8,
    root_precision=16,
    wallis_length=8,
    window_start=4,
    window_cap=8,
    window_target_bits=4,
    window_precision=16,
)

#: The setting of the review's own probe, where a coarse enclosure is visible:
#: at ``n = 8`` and a fair coin every route emits the same box, so a test there
#: could not tell a connected seam from a disconnected one.
SKEWED = {"c0": Fraction(1, 4), "c1": Fraction(3, 4)}


def skewed_request(**overrides: object) -> AcceptanceRequest:
    """Return the request the two parameter tests below are probed on."""
    fields: dict[str, object] = {
        "alphabet": TWO_LETTER,
        "honest": SKEWED,
        "rounds": 40,
        "budget": Fraction(1, 10),
    }
    fields.update(overrides)
    return AcceptanceRequest(**fields)


@pytest.mark.contract
def test_the_recorded_parameters_are_the_ones_in_force() -> None:
    """``honest_model`` names what produced the number, not a default.

    ``interface.yaml``, ``outputs.honest_model``: two runs with the same inputs
    and different parameters may emit different endpoints and different
    figures, so "a record naming the rule and the evaluation and NOT the
    parameters would not identify what was computed".

    THE SEAM THIS CLOSES: the rule
    was resolved without the caller's parameters, so a coarse setting moved the
    reported figure, did NOT move the endpoints it was passed to compute, and
    was not what the record named. All three now move together.
    """
    fine = construct(skewed_request(tail_evaluation="enclosure"))
    rough = construct(
        skewed_request(tail_evaluation="enclosure"), COARSE_ENCLOSURE
    )
    assert fine.honest_model is not None
    assert rough.honest_model is not None

    # The record names the setting that ran.
    assert fine.honest_model.evaluation_parameters != (
        rough.honest_model.evaluation_parameters
    )
    assert ("the_enclosure_route.root_exponent_j", 8) in (
        rough.honest_model.evaluation_parameters
    )
    assert ("the_enclosure_route.root_exponent_j", 64) in (
        fine.honest_model.evaluation_parameters
    )

    # AND THE ENDPOINTS MOVED WITH IT, which is what makes the record true: a
    # coarser enclosure certifies fewer indices, so the box can only widen
    # (prop:bracketed-endpoints (i)).
    assert fine.acceptance_set is not None
    assert rough.acceptance_set is not None
    assert fine.acceptance_set.box_bounds is not None
    assert rough.acceptance_set.box_bounds is not None
    fine_lower, fine_upper = fine.acceptance_set.box_bounds
    rough_lower, rough_upper = rough.acceptance_set.box_bounds
    for low, high in zip(rough_lower, fine_lower, strict=True):
        assert low <= high
    for low, high in zip(fine_upper, rough_upper, strict=True):
        assert low <= high
    assert (rough_lower, rough_upper) != (fine_lower, fine_upper)


@pytest.mark.contract
def test_the_bernstein_enclosure_route_records_both_parameter_sets() -> None:
    """The union, whichever rule ran.

    On ``bernstein`` + ``enclosure`` the endpoints are the Bernstein rule's and
    the reported figure is the sum of the two ENCLOSURE upper bounds at the
    guarded endpoints (``completeness_report``, its fourth row), so BOTH sets
    decide what is emitted and both are in the record. The two blocks each
    declare a ``root_exponent_j``, so each recorded name carries the block it
    comes from.
    """
    fine = construct(
        skewed_request(endpoint_rule="bernstein", tail_evaluation="enclosure")
    )
    rough = construct(
        skewed_request(endpoint_rule="bernstein", tail_evaluation="enclosure"),
        COARSE_ENCLOSURE,
    )
    assert fine.honest_model is not None
    assert rough.honest_model is not None
    recorded = dict(fine.honest_model.evaluation_parameters)
    assert recorded["the_bernstein_rule.root_exponent_j"] == 32
    assert recorded["the_enclosure_route.root_exponent_j"] == 64
    assert recorded["the_enclosure_route.wallis_length_M"] == 4096
    assert dict(rough.honest_model.evaluation_parameters)[
        "the_enclosure_route.root_exponent_j"
    ] == 8

    # The figure moves with the enclosure parameters; the endpoints do not,
    # because no tail is evaluated to find them on this route.
    assert fine.completeness_certified != rough.completeness_certified
    assert fine.acceptance_set is not None
    assert rough.acceptance_set is not None
    assert fine.acceptance_set.box_bounds == rough.acceptance_set.box_bounds


@pytest.mark.contract
def test_the_sweep_records_no_parameter_and_the_bernstein_sweep_records_two() -> None:
    """The record is the union, so on a route with no enclosure it is shorter.

    ``exact`` + ``sweep`` evaluates no enclosure and the sweep takes no
    parameter of its own, so the list is empty -- which is the honest record
    for the route the frozen oracles pin.
    """
    default = construct(request())
    assert default.honest_model is not None
    assert default.honest_model.evaluation_parameters == ()
    bernstein = construct(request(endpoint_rule="bernstein"))
    assert bernstein.honest_model is not None
    assert dict(bernstein.honest_model.evaluation_parameters) == {
        "the_bernstein_rule.root_exponent_j": 32,
        "the_bernstein_rule.root_precision_bits": 64,
    }
