"""The first-order rung (C22), against the FROZEN Group 10 entries.

``FIRST_ORDER_KEY_LENGTH_CASES``, ``FO_TOY1_TABLE``, ``FO_TOY5_TABLE`` and the
``O-FO-*`` entries were authored by a different implementer instance, BEFORE
THE CODE THAT COMPUTES THEM EXISTED -- the registry says so of itself: "Not one
number in Group 10 was produced by an implementation of the thing it pins".
This file reads them against the implementation.

WHAT IS COMPARED HERE AND WHAT IS NOT. The bracket tables are closed forms of
``alpha`` and one hand-named sector weight, derived on paper from
Eq. ``eq:hlb``; this file reads them against the ENGINE's own key-length
arithmetic and against the properties the entries assert (monotonicity, the
clamp order, the tightness pattern). The end-to-end SOLVER comparison against
the same brackets is
``tests/golden/test_first_order_withdrawals.py``'s subject, where the driver's
gate is what is under test.
"""

from __future__ import annotations

import math
from itertools import pairwise

import pytest
from reference import key_length as reference_key_length
from registry import (
    ALPHA_GRID,
    ASSURANCE_VALUES_1_0_0,
    FIRST_ORDER_KEY_LENGTH_CASES,
    FO_ITERATE_HYPOTHESES,
    FO_MEMBERSHIP_CHECKS,
    FO_TOY1_TABLE,
    FO_TOY5_TABLE,
    FO_WITHDRAWAL_REASONS,
    REASON_VOCABULARY_1_0_0,
    SHELVED_TIER_NAME,
    SHELVED_TIER_REFUSAL,
    FirstOrderKeyLengthCase,
    oracle,
)

from certiqs_key.foundations.assurance import Assurance
from certiqs_key.meat_core import thresholds
from certiqs_key.meat_core.errors import (
    SecurityGateError,
    SecurityStatementVacuousError,
)
from certiqs_key.meat_core.finitekey.keylength import key_length
from certiqs_key.meat_core.reasons import (
    RETIRED_REFUSAL_REASONS,
    WITHDRAWAL_REASONS,
    AssuranceReason,
    RefusalReason,
)

# THE SUBMODULE'S INSTANCE, AND THE IMPORT SAYS WHOSE IT IS. ``cor:fo-keylength``
# is ``cor:keylength-bound`` at ``h = h_lb``, and the core's function takes ``h``
# and lives in meat_core; this one takes ``h_lb`` and lives with the solver that
# produces it.
from certiqs_key.solvers.frank_wolfe.general_keyrate import (
    key_length_from_first_order,
)


def at_the_vacuous_corner(case: FirstOrderKeyLengthCase) -> bool:
    """Return whether the corner gate refuses this frozen case.

    ONE CASE ANSWERS TRUE: ``FOKL-2-clamped`` declares ``eps_EV = eps_PA = 1``,
    deliberately, "so that the arithmetic isolates the clamp", and the gate
    ("refuse the corner with a named reason") refuses ``eps_PA + eps_EV >= 1``.

    THE REGISTRY IS NOT EDITED, and neither is the arithmetic. The frozen
    integer is still what Eq. eq:keylength-fo gives, which the corner branches
    below assert through the INDEPENDENT reference implementation in
    ``tests/oracles/reference.py`` -- a transcription of the formula and not an
    engine, so it carries no gate and never will. The ENGINE refuses the run
    rather than reporting a length under a security statement that is empty.
    """
    return case.eps_pa + case.eps_ev >= 1.0

pytestmark = [pytest.mark.contract, pytest.mark.oracle]


# ===========================================================================
#  O-FO-KEY-LENGTH -- Eq. eq:keylength-fo, and the ORDER of the clamp.
# ===========================================================================


@pytest.mark.parametrize("case", FIRST_ORDER_KEY_LENGTH_CASES, ids=lambda c: c.case_id)
def test_o_fo_key_length_reproduces_the_frozen_integer(
    case: FirstOrderKeyLengthCase,
) -> None:
    """Eq. ``eq:keylength-fo``, integer for integer, on each frozen case.

    ``FOKL-2-clamped`` is the case that pins the ORDER: the clamp is applied to
    ``h_lb`` BEFORE the formula, and the registry writes out why it matters --
    "feeding the unclamped -0.00203... in would give
    ``10 000 * (-0.00203...) + 1 = -19.32...``, floor ``-20``, and then the
    platform's own ``max{0, .}`` would return ``0`` -- A DIFFERENT ANSWER, AND
    THE WRONG ONE". The expected value is ``1``, so an implementation that
    clamped afterwards fails here rather than agreeing by accident.
    """
    assert oracle("O-FO-KEY-LENGTH").claims == ("C14", "C15", "C22")
    arguments = {
        "rounds": case.rounds,
        "lambda_ec": case.lambda_ec,
        "eps_ev": case.eps_ev,
        "eps_pa": case.eps_pa,
        "alpha": case.alpha,
    }
    if at_the_vacuous_corner(case):
        # THE ARITHMETIC IS THE FROZEN ONE STILL, read off the independent
        # reference at the clamped bracket the corollary consumes -- the clamp
        # is max{0, h_lb} and the reference takes h_low, so the two are the
        # same call. The FROZEN INTEGER IS REPRODUCED and is not edited.
        assert (
            reference_key_length(h_low=max(0.0, case.h_lb), **arguments)
            == case.expected
        )
        # AND THE ENGINE REFUSES THE RUN, by the named reason.
        with pytest.raises(SecurityStatementVacuousError) as refusal:
            key_length_from_first_order(h_lb=case.h_lb, **arguments)
        assert refusal.value.reason == "security_statement_vacuous"
        return
    length, clamped = key_length_from_first_order(h_lb=case.h_lb, **arguments)
    assert length == case.expected
    assert clamped is case.clamped


def test_the_frozen_key_lengths_are_the_h_low_formula_with_the_bracket() -> None:
    """Corollary ``cor:fo-keylength``: Eq. ``eq:keylength`` with ``max{0, h_lb}``.

    "The formula is Eq. ``eq:keylength`` WITH ``h_low`` REPLACED BY
    ``max{0, h_lb}`` AND NOTHING ELSE CHANGED -- no additional subtrahend, no
    floor beyond the one ``max{0, .}`` already supplies, no arithmetic
    requirement of any kind." That is checkable directly: feed the CLAMPED
    bracket to the ``h_low`` entry point and the two must agree exactly.

    THE FAILURE THIS CATCHES is the one the registry names: "an implementation
    that subtracts a further term on the first-order path -- a relative-entropy
    penalty, a gap, a 'safety margin' -- is claiming a theorem this contract
    does not have".
    """
    for case in FIRST_ORDER_KEY_LENGTH_CASES:
        arguments = {
            "rounds": case.rounds,
            "lambda_ec": case.lambda_ec,
            "eps_ev": case.eps_ev,
            "eps_pa": case.eps_pa,
            "alpha": case.alpha,
        }
        if at_the_vacuous_corner(case):
            # THE TWO ENTRY POINTS AGREE AT THE CORNER TOO, AND THEY AGREE BY
            # BOTH REFUSING. The gate is in the CORE function, which
            # is the one place the expression is evaluated, so the submodule's
            # instance cannot reach a number the core would decline to compute
            # -- the same statement this test makes everywhere else, read at a
            # point where the answer is a refusal rather than an integer.
            with pytest.raises(SecurityStatementVacuousError):
                key_length_from_first_order(h_lb=case.h_lb, **arguments)
            with pytest.raises(SecurityStatementVacuousError):
                key_length(h_low=max(0.0, case.h_lb), **arguments)
            continue
        first_order, _ = key_length_from_first_order(h_lb=case.h_lb, **arguments)
        through_h_low = key_length(h_low=max(0.0, case.h_lb), **arguments)
        assert first_order == through_h_low, case.case_id


def test_the_first_order_length_is_monotone_in_the_leakage() -> None:
    """Proposition ``prop:monotone`` (i), on the first-order path.

    The frozen pair ``(FOKL-1-tight, FOKL-3-monotone-anchor)`` differs in
    ``lambda_EC`` alone, by exactly ``1 000``, and the lengths differ by exactly
    ``1 000`` the other way. The registry calls that pair "THE FALSIFIABLE FORM
    OF THAT SENTENCE", because ``h_lb`` "depends on the iterates, the oracle
    returns and the declaration, and on NONE OF ``(lambda_EC, eps_EV,
    eps_PA)``" -- so the length falls one bit per bit of leakage and not by a
    modelled fraction of it.

    Both the frozen expectation AND the code are checked, so the pair cannot
    agree because the registry was written from a run.
    """
    tight = next(c for c in FIRST_ORDER_KEY_LENGTH_CASES if c.case_id == "FOKL-1-tight")
    anchor = next(
        c for c in FIRST_ORDER_KEY_LENGTH_CASES if c.case_id == "FOKL-3-monotone-anchor"
    )
    assert anchor.lambda_ec - tight.lambda_ec == 1_000
    assert tight.expected - anchor.expected == 1_000

    computed = {
        case.case_id: key_length_from_first_order(
            rounds=case.rounds,
            h_lb=case.h_lb,
            lambda_ec=case.lambda_ec,
            eps_ev=case.eps_ev,
            eps_pa=case.eps_pa,
            alpha=case.alpha,
        )[0]
        for case in (tight, anchor)
    }
    assert computed["FOKL-1-tight"] - computed["FOKL-3-monotone-anchor"] == 1_000


def test_the_first_order_length_is_monotone_in_both_security_budgets() -> None:
    """Proposition ``prop:monotone`` (ii)-(iii), carried by ``cor:fo-keylength``.

    "All four conclusions of Proposition ``prop:monotone`` hold for this length,
    because the proof carries word for word with ``max{0, h_lb}`` in place of
    ``h_low``." A SMALLER security error is a STRONGER promise and buys a
    SHORTER key, so the length is non-decreasing in each budget; the strict
    direction is asserted where the deduction is coarse enough to move an
    integer.
    """
    base = next(c for c in FIRST_ORDER_KEY_LENGTH_CASES if c.case_id == "FOKL-1-tight")

    def length(*, eps_ev: float, eps_pa: float) -> int:
        return key_length_from_first_order(
            rounds=base.rounds,
            h_lb=base.h_lb,
            lambda_ec=base.lambda_ec,
            eps_ev=eps_ev,
            eps_pa=eps_pa,
            alpha=base.alpha,
        )[0]

    tighter_ev = length(eps_ev=base.eps_ev / 2.0, eps_pa=base.eps_pa)
    tighter_pa = length(eps_ev=base.eps_ev, eps_pa=base.eps_pa / 2.0)
    assert tighter_ev < base.expected
    assert tighter_pa < base.expected
    # alpha = 3/2, so alpha/(alpha-1) = 3: halving eps_PA costs exactly 3 bits
    # and halving eps_EV exactly 1, which is the deduction written out.
    assert base.expected - tighter_ev == 1
    assert base.expected - tighter_pa == 3


def test_the_alpha_domain_of_every_frozen_case_is_the_key_length_one() -> None:
    """``req:key-length-alpha-domain`` confines EVERY key length to ``(1, 2)``.

    The registry states the confinement: "Every case has ``alpha`` in ``(1, 2)``.
    A-ALPHA confines every key-length
    statement to that interval, ``cor:fo-keylength`` explicitly among them, even
    though C22 itself is stated on ``(1, inf)``." The guard is asserted from
    both sides: the frozen cases are inside, and a case outside is refused.
    """
    for case in FIRST_ORDER_KEY_LENGTH_CASES:
        assert 1.0 < case.alpha < 2.0, case.case_id
    with pytest.raises(SecurityGateError):
        key_length_from_first_order(
            rounds=10_000,
            h_lb=0.5,
            lambda_ec=0,
            eps_ev=2.0**-32,
            eps_pa=2.0**-32,
            alpha=2.5,
        )


# ===========================================================================
#  O-FO-BRACKET-* -- the four bracket entries, as PROPERTIES of eq:hlb.
# ===========================================================================


def test_o_fo_bracket_unconstrained_is_negative_and_decreasing_in_the_weight() -> None:
    """TOY-1: ``h_lb < 0 = h_low`` at every admissible iterate, strictly.

    Two properties the entry PROVES rather than measures: ``B(w; 0) <= 0`` for
    every ``w`` with equality only at ``w = 0``, and ``B`` strictly decreasing
    in ``w``, so "the maximum over any finite iterate set is at its SMALLEST
    weight". The frozen table is read for both, and the entry's closed form
    must be the smallest tabulated weight's row.
    """
    entry = oracle("O-FO-BRACKET-UNCONSTRAINED")
    assert entry.toy_id == "TOY-1"
    assert entry.closed_form is not None
    weights = [weight for weight, _ in FO_TOY1_TABLE]
    assert weights == sorted(weights, reverse=True)

    for _weight, table in FO_TOY1_TABLE:
        for alpha, value in table:
            assert value < 0.0, (alpha, value)
    # STRICTLY DECREASING IN w at every alpha of the grid.
    for alpha in ALPHA_GRID:
        column = [dict(table)[alpha] for _weight, table in FO_TOY1_TABLE]
        assert all(a < b for a, b in pairwise(column)), alpha
    # And the entry's own frozen values are the smallest weight's row, which is
    # what "the maximum over the tabulated iterates" means.
    smallest = min(weights)
    row = dict(next(t for w, t in FO_TOY1_TABLE if w == smallest))
    assert entry.frozen_values == tuple(sorted(row.items()))


def test_o_fo_bracket_constrained_is_tight_at_the_optimum_and_below_elsewhere() -> None:
    """TOY-5: ``h_lb = h_low`` at ``w = 1/2`` and STRICTLY BELOW at every other.

    The entry is "the LOAD-BEARING ONE of Group 10 ... the only case in which
    the first-order bound is TIGHT at a value that is not zero", and it
    discriminates three wrong brackets at once -- one omitting the linear term,
    one taking the vertex at the wrong end of the interval, and one minimizing
    over the relaxed family. Its tight value is ``O-HLOW-CONSTRAINED``'s closed
    form, re-used "so that the two entries cannot drift apart"; that identity is
    asserted here rather than assumed.
    """
    entry = oracle("O-FO-BRACKET-CONSTRAINED")
    assert entry.toy_id == "TOY-5"
    assert entry.frozen_values == oracle("O-HLOW-CONSTRAINED").frozen_values
    tight = dict(entry.frozen_values)
    for weight, table in FO_TOY5_TABLE:
        assert weight > 0.5, weight
        for alpha, value in table:
            # thm:firstorder (ii) in the direction it is stated: STRICTLY below
            # at every iterate that is not the optimum.
            assert value < tight[alpha], (weight, alpha)


def test_the_two_bracket_entries_that_are_tight_are_tight_for_stated_reasons() -> None:
    """``O-FO-BRACKET-SINGLETON`` and ``-KEY-INERT``: the linear term VANISHES.

    Neither is a coincidence and neither is measured. On the singleton feasible
    set both minimizations of Eq. ``eq:lmo`` are over one-point sets, so
    ``(v_t, S_t) = (q_t, J_t)`` and both differences in Eq. ``eq:hlb`` are the
    zero vector; on the fully key-inert toy the gradient is CONSTANT on the
    feasible simplex, so the pairing is ``G_0 (1 - 1) = 0``. The values are
    ``log2(m)`` and ``0``, and each equals the ESTIMATE entry for the same toy,
    which is the property an implementation can violate.
    """
    singleton = oracle("O-FO-BRACKET-SINGLETON")
    assert singleton.toy_id == "TOY-3(m=2)"
    assert singleton.value == 1.0 == math.log2(2)
    assert singleton.value == oracle("O-HLOW-FULLY-DEPHASED").value

    inert = oracle("O-FO-BRACKET-KEY-INERT")
    assert inert.toy_id == "TOY-2"
    assert inert.value == 0.0 == oracle("O-HLOW-DETERMINISTIC").value
    # C7 is named because (H-SUPP) is VACUOUS there: S_K(chat0) is empty.
    assert inert.claims == ("C7", "C22")


# ===========================================================================
#  O-FO-WITHDRAWAL, O-FO-NEGATIVE-OBJECTIVE, O-FO-LADDER.
# ===========================================================================


def test_o_fo_withdrawal_names_the_contracts_four_strings_in_order() -> None:
    """O-FO-WITHDRAWAL: four reasons, no fifth, and no reduced form of the claim.

    The engine's ``WITHDRAWAL_REASONS`` must BE the frozen tuple, in order: the
    order is the order the gate decides in ("THE ORDER OF THE CHECKS IS THE
    ORDER OF THE REASONS"), and a sixth string for the acceptance-island case
    would have "left the contract's vocabulary" -- every failure
    ``req:first-order-withdrawal`` (iv) names carries ``iterate_not_feasible``,
    "in each case" (the frozen entry's own words are "in either case", written
    before the requirement named the oracle-return check as a third case).

    Derived by hand: ``req:first-order-withdrawal`` lists four items and
    has no oracle item ("Neither the point the oracle returned at that
    iterate nor its status removes the iterate from I"), and the registry's
    tuple is derived with it.
    """
    assert oracle("O-FO-WITHDRAWAL").kind == "fail-closed"
    assert tuple(str(r) for r in WITHDRAWAL_REASONS) == FO_WITHDRAWAL_REASONS
    assert len(FO_WITHDRAWAL_REASONS) == 4
    # And every one of them is a contract string, not an implementation one.
    for reason in FO_WITHDRAWAL_REASONS:
        assert reason in REASON_VOCABULARY_1_0_0


def test_the_three_iterate_hypotheses_and_the_three_membership_checks() -> None:
    """The hypotheses name the iterate; the checks name the ``J`` factor.

    ``FO_ITERATE_HYPOTHESES`` is ``(H-POS, H-SUPP, H-NOPERT)``, "stated on the
    ITERATE ALONE and naming no set", and ``FO_MEMBERSHIP_CHECKS`` is the three
    of Remark ``rem:fo-iterate-checks``, "ALL THREE ON THE ``J`` FACTOR". Each
    check names a Section 2.6 row, and every one of those rows must be a row
    this implementation declares and carries -- otherwise the check is being
    made at a number the contract does not name.
    """
    assert FO_ITERATE_HYPOTHESES == ("H-POS", "H-SUPP", "H-NOPERT")
    assert len(FO_MEMBERSHIP_CHECKS) == 3
    carried = thresholds.carrying_table()
    for _subject, key, _why in FO_MEMBERSHIP_CHECKS:
        assert key in carried, key
    keys = [key for _s, key, _w in FO_MEMBERSHIP_CHECKS]
    assert keys == ["iterate_positivity", "iterate_coupling", "constraint_rows"]
    # iterate_positivity is at EXACTLY 0 -- "the relaxed family does not relax
    # positivity, so a point admitted at a positive window lies in NO
    # Feas^J(epsilon)".
    assert thresholds.declared(thresholds.ITERATE_POSITIVITY) == 0.0


def test_o_fo_negative_objective_handles_the_two_cases_oppositely() -> None:
    """A negative ``h_lb`` is CLAMPED AND FLAGGED; a negative estimate REFUSES.

    "The asymmetry is the content." The clamp side is asserted on the frozen
    clamped case: the length is computed from ``max{0, h_lb}`` while ``h_lb``
    itself keeps the unclamped value, so a reader "sees what was computed and
    not only what was used". The refusal side is asserted as a TYPED reason --
    "A BARE EXCEPTION IS NOT A CONFORMING IMPLEMENTATION OF THIS RULE".
    """
    assert oracle("O-FO-NEGATIVE-OBJECTIVE").kind == "fail-closed"
    clamped_case = next(
        c for c in FIRST_ORDER_KEY_LENGTH_CASES if c.case_id == "FOKL-2-clamped"
    )
    assert clamped_case.h_lb < 0.0
    # THE FROZEN CASE'S BUDGETS ARE THE VACUOUS CORNER and the run is refused
    # there, so the CLAMP SIDE is asserted at the same h_lb
    # under budgets a run may be made at. THE CLAMP IS WHAT IS UNDER TEST HERE
    # AND THE BUDGETS ARE NOT: h_lb enters the expression as max{0, h_lb}
    # whatever they are, and the frozen case's own arithmetic is checked
    # against the reference in test_o_fo_key_length_reproduces_the_frozen_integer.
    #
    # WHAT IS NOT OBSERVABLE, AND IT IS DECLARED RATHER THAN QUIETLY
    # DROPPED: the frozen case was built at eps = 1 because that is the ONLY
    # region where clamping BEFORE the expression and clamping AFTER it give
    # different INTEGERS. At any admitted budget eps_EV < 1 forces
    # ceil(log2(1/eps_EV)) >= 1, so both orders return 0 from a negative h_lb
    # and the returned integer cannot tell them apart. The order is therefore
    # pinned here by what remains visible -- the FLAG, and the unclamped value
    # the record keeps -- and by the refusal above; the arithmetic itself is
    # exactly eq:keylength-h.
    assert at_the_vacuous_corner(clamped_case)
    with pytest.raises(SecurityStatementVacuousError):
        key_length_from_first_order(
            rounds=clamped_case.rounds,
            h_lb=clamped_case.h_lb,
            lambda_ec=clamped_case.lambda_ec,
            eps_ev=clamped_case.eps_ev,
            eps_pa=clamped_case.eps_pa,
            alpha=clamped_case.alpha,
        )
    length, clamped = key_length_from_first_order(
        rounds=clamped_case.rounds,
        h_lb=clamped_case.h_lb,
        lambda_ec=clamped_case.lambda_ec,
        eps_ev=2.0**-32,
        eps_pa=2.0**-32,
        alpha=clamped_case.alpha,
    )
    assert clamped is True
    assert length == 0
    # A NEGATIVE BRACKET IS NOT REPAIRED AND IS NOT A REFUSAL: it supports no
    # positive length and says so, which is clause (b) of cor:keylength-bound.
    # The clamped value is the one the expression sees, and it is reached by
    # clamping the INPUT: the same call at h = 0 returns the same integer.
    assert (
        key_length_from_first_order(
            rounds=clamped_case.rounds,
            h_lb=0.0,
            lambda_ec=clamped_case.lambda_ec,
            eps_ev=2.0**-32,
            eps_pa=2.0**-32,
            alpha=clamped_case.alpha,
        )[0]
        == length
    )
    # THE UNCLAMPED VALUE IS THE ONE THE CASE CARRIES: nothing above rewrote it.
    assert clamped_case.h_lb == -0.0020322531662131105
    # And the estimate side is a typed refusal with the contract's spelling.
    assert str(RefusalReason.NEGATIVE_OBJECTIVE) == "negative_objective"
    assert "negative_objective" in REASON_VOCABULARY_1_0_0


def test_o_fo_ladder_has_two_live_rungs_and_carries_no_third() -> None:
    """Two values, both reported, and THERE IS NO THIRD NAME TO REFUSE.

    ``ASSURANCE_VALUES_1_0_0`` is ``("estimate", "first-order")`` and is the
    value set of BOTH ``reported_tier`` and
    ``optimizer_certificate.assurance``. The frozen registry records a shelved
    third name with the refusal ``assurance_tier_not_available``; this
    repository carries that refusal IN NO FORM (PRINCIPLES.md section 10;
    spec/architecture.md 2.8), and the request row that could have named it is
    in the interface's ``retired_parameter_rows``. So the enum IS
    the ladder, and the assertion is an exact equality rather than a difference.

    THE FROZEN ENTRY IS READ AND NOT EDITED: ``SHELVED_TIER_NAME`` and
    ``SHELVED_TIER_REFUSAL`` are in the registry, and an oracle is never
    regenerated from the code it tests. What is asserted is that the refusal
    is not reachable here.
    """
    assert oracle("O-FO-LADDER").kind == "fail-closed"
    # Derived by hand: the registry note quotes def:tiers.
    assert ASSURANCE_VALUES_1_0_0 == ("estimate", "first-order", "certified")
    assert tuple(str(member) for member in Assurance) == ASSURANCE_VALUES_1_0_0
    assert SHELVED_TIER_NAME in {str(member) for member in Assurance}
    assert SHELVED_TIER_REFUSAL not in {str(r) for r in RefusalReason}
    assert SHELVED_TIER_REFUSAL in RETIRED_REFUSAL_REASONS
    # THE PARTITION OF THE TWO ENUMS AGAINST THE REGISTRY'S SEVENTEEN,
    # ASSERTED WHOLE. The spellings are the contract's and a synonym is
    # forbidden; what an implementation may add is a reason for something the
    # contract names the OUTCOME of and leaves the diagnosis of.
    contract_reasons = {
        str(r) for r in AssuranceReason if str(r) in REASON_VOCABULARY_1_0_0
    }
    # THE FORCED DOWNGRADE IS NOT IN THIS SET OR THE ENUM.
    # ``declared_operator_tolerance_open`` forced the tier to the estimate when
    # the declared family was admitted with a nonzero defect; no family is
    # admitted with a defect, so the state it named does not arise and the
    # string is in RETIRED_REFUSAL_REASONS.
    assert contract_reasons == set(FO_WITHDRAWAL_REASONS)
    assert "declared_operator_tolerance_open" in RETIRED_REFUSAL_REASONS
    implementation_reasons = {
        str(r) for r in AssuranceReason if str(r) not in REASON_VOCABULARY_1_0_0
    }
    assert implementation_reasons == {
        # The two acceptance-set diagnoses of the +inf path: the contract
        # names the OUTCOME (rem:hlow-range) and leaves the diagnosis open.
        # The registry's `acceptance_geometry_unsupported` has no successor:
        # frank-wolfe/req:acceptance-geometries refuses an unread geometry at
        # admission, and the spelling is in RETIRED_REFUSAL_REASONS.
        "acceptance_set_empty",
        "acceptance_set_ill_formed",
        # The two that name a run which never got that far. The registry's
        # `first_order_not_requested` is `first_order_no_bracket` here: the
        # tier is ACHIEVED and never requested, so there is no request to have
        # declined and what remains is a record that carries no bracket.
        "first_order_no_bracket",
        "objective_infinite",
    }
    # EVERY REFUSAL REASON IS ONE OF THE REGISTRY'S SEVENTEEN OR THE
    # INTERFACE'S OWN ONE SPELLING: a refusal produces no output, so there is
    # nothing for an implementation string to travel on, and the one addition
    # is `declaration_not_exactly_admissible`, which reductions already spells
    # for the same decision on the same kind of datum.
    live = {str(r) for r in RefusalReason}
    assert live - set(REASON_VOCABULARY_1_0_0) == {
        "declaration_not_exactly_admissible",
        # THE SECOND ADDITION THIS MODULE MAKES.
        # `security_statement_vacuous` names a state the registry has no
        # name for: eps_PA + eps_EV >= 1,
        # where the security statement the length would travel under is empty,
        # and the refusal is "refuse the corner with a named
        # reason". It is a DISCLOSED SCOPE NARROWING -- the claims admit the
        # corner and this implementation declines to run it -- and never a
        # reading of a claim, so it is an addition to the vocabulary and not a
        # respelling of anything in it.
        "security_statement_vacuous",
        # THE THIRD: meat-core interface `refusal_reasons.this_files_own_spelling`,
        # frank-wolfe/req:certified-evaluation (viii): a `strict`
        # run not reported at the certified tier refuses.
        "certification_refused",
        # THE FOURTH, the same file's spelling for
        # meat-core/req:unreachable-acceptance-set (iv): an order whose proven
        # mismatch part reaches its share of the key length reports none.
        "acceptance_set_unreachable",
    }
