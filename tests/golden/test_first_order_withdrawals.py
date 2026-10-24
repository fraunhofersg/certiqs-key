"""The FOUR withdrawal rows of ``req:first-order-withdrawal``, one at a time.

Every row is reached through
:func:`~certiqs_key.solvers.frank_wolfe.joint_driver.run_joint_frank_wolfe`
-- the solver, not the gate function -- so what is asserted is what a CONSUMER
sees: a result that exists, an estimate that survived, and the machine-readable
reason ``h_lb`` was withdrawn for. The two facts are inseparable and the
contract states them together: "``h_lb`` is WITHDRAWN, and the tier falls to
``estimate`` WITH A MACHINE-READABLE REASON", and Section 1.3 item (1) that a
failure "withdraws ``h_lb`` and LEAVES THE ESTIMATE".

WHY THAT SECOND HALF NEEDS A TEST OF ITS OWN. It is the half an implementation
loses silently. A hypothesis that fails cannot produce a gradient, so the
natural thing for the code to do is RAISE -- and a run that raises reports no
result at all: no estimate, no tier, no reason, nothing a caller can route on.
Every row below therefore asserts a ``JointFrankWolfeResult`` came back and that its
``objective`` is finite, before it asserts anything about the reason.

WHAT IS STUBBED AND WHY IT IS NOT A WEAKENING.
``tests/support/withdrawal_toys.py`` supplies the two oracles. Three of the five
rows are properties of an ORACLE or of the SOLVER OPTIONS rather than of a
declaration -- a status that does not assert optimality, an acceptance factor
not formed on the exact island, an applied perturbation -- and the driver takes
both oracles as arguments precisely so that they can be supplied. Every point a
stub returns is genuinely what it claims to be, so the gate measures what it
would measure of a backend.

TOY-1 runs as the degenerate general declaration it is, on the joint driver.
"""

from __future__ import annotations

import math
from collections.abc import Mapping

import numpy as np
import pytest
from registry import FO_WITHDRAWAL_REASONS
from withdrawal_toys import (
    StubAcceptanceOracle,
    StubLinearOracle,
    interior_start,
    singular_start,
    toy_setup,
    with_negative_block,
)

from certiqs_key.meat_core import thresholds
from certiqs_key.meat_core.errors import GradientHypothesisError
from certiqs_key.meat_core.objective.branch import BranchValues
from certiqs_key.meat_core.objective.gradient import check_gradient_hypotheses
from certiqs_key.meat_core.objective.support import acceptance_support
from certiqs_key.meat_core.reasons import WITHDRAWAL_REASONS, AssuranceReason
from certiqs_key.solvers.frank_wolfe.driver import (
    STATUS_HYPOTHESIS_WITHDRAWN,
    STATUS_OBJECTIVE_INFINITE_AT_START,
    STATUSES_OUTSIDE_THE_GAP_RULE,
    FrankWolfeOptions,
)
from certiqs_key.solvers.frank_wolfe.joint_driver import (
    JointFrankWolfeResult,
    run_joint_frank_wolfe,
)

pytestmark = [pytest.mark.contract, pytest.mark.oracle]


def _run(
    *,
    start: Mapping[tuple[str, str], np.ndarray] | None = None,
    oracle_blocks: Mapping[tuple[str, str], np.ndarray] | None = None,
    status: str = "optimal",
    frequencies: Mapping[str, float] | None = None,
    exact_island: bool = True,
    options: FrankWolfeOptions | None = None,
    toy_id: str = "TOY-1",
) -> JointFrankWolfeResult:
    """Run the driver once on a frozen toy with the stubs a row needs."""
    declaration, maps = toy_setup(toy_id)
    point = interior_start(declaration) if start is None else start
    vertex = point if oracle_blocks is None else oracle_blocks
    acceptance = StubAcceptanceOracle(
        frequencies=(
            dict.fromkeys(declaration.acceptance_values, 1.0)
            if frequencies is None
            else frequencies
        ),
        exact_island=exact_island,
    )
    return run_joint_frank_wolfe(
        maps,
        StubLinearOracle(blocks=vertex, status=status),
        acceptance,
        point,
        alpha=1.5,
        options=options or FrankWolfeOptions(max_iterations=1),
    )


def _assert_estimate_survived(
    result: JointFrankWolfeResult, reason: AssuranceReason
) -> None:
    """Assert the shape EVERY withdrawal must have, whatever caused it.

    Remark ``rem:fo-interface``: the bracket is absent, the reason names
    which hypothesis failed, and the ESTIMATE -- the objective at the point the
    run returned -- is still there. "Withdrawal is never a weakening of what
    ``h_lb`` means; THERE IS NO REDUCED FORM OF THE CLAIM", so a result carrying
    a smaller or hedged ``h_lb`` is a different defect and is refused here too.
    """
    assert isinstance(result, JointFrankWolfeResult)
    assert result.h_lb is None, "a withdrawn bracket is ABSENT, never reduced"
    assert result.withdrawal == str(reason)
    assert result.withdrawal in FO_WITHDRAWAL_REASONS
    assert math.isfinite(result.objective), "the estimate must survive the withdrawal"
    # No iterate contributed, which is what "the index set is empty" means.
    assert not any(gate.contributes for gate in result.gates)


# ===========================================================================
#  Row 1 -- (H-POS): gradient_hypothesis_positivity.
# ===========================================================================


def test_h_pos_is_decided_on_chat_acc_and_not_on_the_support_of_the_iterate() -> None:
    """(H-POS) fails at a ``Chat_acc`` coordinate the ITERATE has driven to 0.

    Theorem ``thm:firstorder`` states (H-POS) as ``q_t(chat) > 0`` for every
    ``chat in Chat_acc``, and ``Chat_acc`` of Eq. ``eq:chacc-def`` is a property
    of the DECLARED acceptance set: it does not move with the iterate. So an
    iterate carrying ``q_t(chat) == 0.0`` at a coordinate that IS in
    ``Chat_acc`` violates the hypothesis and the gate must withdraw.

    THE DEFECT THIS CATCHES IS A VACUOUS CLAUSE. Reading the quantifier off
    ``supp(q_t)`` -- skipping the coordinates where ``q_t`` is zero, which is
    what a filter on the iterate's own support does -- makes the test pass in
    exactly the case it exists to catch, and that is the unsafe side: the run
    would report ``h_lb`` under a hypothesis that does not hold.
    """
    declaration, _maps = toy_setup()
    support = acceptance_support(declaration)
    assert support, "the toy's Chat_acc must be non-empty for this to bite"
    zeroed = dict.fromkeys(support, 0.0)

    result = _run(frequencies=zeroed)
    _assert_estimate_survived(result, AssuranceReason.GRADIENT_HYPOTHESIS_POSITIVITY)
    # The iterate really does carry a zero ON Chat_acc: the premise, asserted.
    assert all(result.q[chat] == 0.0 for chat in support)


def test_h_pos_quantifies_over_chat_acc_and_not_over_the_declared_chat() -> None:
    """C22b at the check itself: the two index sets, and the string it carries.

    ``q_t(chat) > 0`` is readable from the iterate; ``P^J_chat(J_t) > 0`` and
    ``K^J_chat(J_t) > 0`` are not -- they are branch values the gradient routine
    computes, and it cannot return a number when one vanishes, so it RAISES and
    the driver converts the failure into a withdrawal. This test reads the
    check directly, because that is where Lemma ``lem:fo-khyp`` (iii) lives:
    ``q(chat) > 0`` and ``P_chat > 0`` for every ``chat in Chat_acc``,
    ``K_chat > 0`` for every ``chat in Chat_key n Chat_acc``, AND NOT ONE
    QUANTIFIER WIDER.

    THE TWO DIRECTIONS ARE BOTH ASSERTED. A vanishing value INSIDE
    ``Chat_acc`` must raise -- the hypothesis really does fail there -- and the
    same value at a coordinate OUTSIDE it must not, because on ``Chat`` the
    hypothesis "would be UNSATISFIABLE whenever ``Chat_acc`` is a proper
    subset". The exception carries the machine-readable reason, which is what
    lets the driver name the right row without matching prose.
    """
    values = {
        "in-support": BranchValues(p=0.0, t=0.0, trace_g=0.0, k=1.0, deficits={}),
        "outside": BranchValues(p=0.0, t=0.0, trace_g=0.0, k=1.0, deficits={}),
        "fine": BranchValues(p=1.0, t=1.0, trace_g=0.0, k=1.0, deficits={}),
    }
    q = {"in-support": 1.0, "outside": 0.0, "fine": 1.0}

    # OUTSIDE Chat_acc the same vanishing P is not read at all.
    check_gradient_hypotheses(q, values, ("fine",), ("fine",))

    # INSIDE it, the hypothesis fails and the reason is the contract's.
    with pytest.raises(GradientHypothesisError) as failure:
        check_gradient_hypotheses(q, values, ("fine",), ("in-support", "fine"))
    assert failure.value.reason == str(AssuranceReason.GRADIENT_HYPOTHESIS_POSITIVITY)
    assert "lem:fo-khyp" in str(failure.value)

    # And the K clause is read only on Chat_key n Chat_acc.
    zero_k = {"fine": BranchValues(p=1.0, t=0.0, trace_g=0.0, k=0.0, deficits={})}
    check_gradient_hypotheses({"fine": 1.0}, zero_k, (), ("fine",))
    with pytest.raises(GradientHypothesisError):
        check_gradient_hypotheses({"fine": 1.0}, zero_k, ("fine",), ("fine",))


# ===========================================================================
#  Row 2 -- (H-SUPP): gradient_hypothesis_support.
# ===========================================================================


def test_a_rank_deficient_key_active_block_withdraws_as_hypothesis_support() -> None:
    """(H-SUPP): ``rank X_{chat,s} = dim W_{chat,s}``, and here it is not.

    At ``w0 = 0`` on TOY-1 the key-active branch operator is
    ``X_chat0,s0 = 0``, "whose rank is 0, while ``dim W_chat0,s0 = 1``" --
    ``O-FO-BRACKET-UNCONSTRAINED`` derives exactly this, and calls it the reason
    the supremum of the bracket "IS NOT ATTAINED". The iterate is feasible and
    positive semidefinite, so nothing else refuses it; what fails is the support
    hypothesis alone.

    Remark ``rem:fo-danger``: "the failure of (H-SUPP) is on the UNSAFE side,
    which is why it withdraws rather than adjusts".
    """
    declaration, _maps = toy_setup()
    result = _run(start=singular_start(declaration))
    _assert_estimate_survived(result, AssuranceReason.GRADIENT_HYPOTHESIS_SUPPORT)


# ===========================================================================
#  Row 3 -- (H-NOPERT): gradient_perturbation_applied.
# ===========================================================================


def test_an_applied_perturbation_withdraws_rather_than_adjusting() -> None:
    """(H-NOPERT): the gradient is taken AT ``x_t`` itself, or not used.

    Remark ``rem:fo-nopert`` CLOSES the perturbation route at 1.0.0 -- "the
    consequence of applying one is a WITHDRAWAL and not a weakening" -- so a run
    configured with a non-zero ``gradient_perturbation`` may still report its
    estimate and may not report a bracket. The withdrawal fires on the OPTION
    being set, not on a perturbation happening to be applied at some iterate,
    which is the conservative reading: the hypothesis is that none was applied.
    """
    result = _run(
        options=FrankWolfeOptions(max_iterations=1, gradient_perturbation=1e-8)
    )
    _assert_estimate_survived(result, AssuranceReason.GRADIENT_PERTURBATION_APPLIED)


# ===========================================================================
#  Row 4 -- membership: iterate_not_feasible, by both of its routes.
# ===========================================================================


def test_a_negative_iterate_eigenvalue_withdraws_as_iterate_not_feasible() -> None:
    """Per-block positivity is one of THE THREE CHECKS, and it is NOT (H-POS).

    Remark ``rem:fo-iterate-checks`` lists per-block positive semidefiniteness
    with the coupling residual and the declared rows as the three checks whose
    failure -- when the point is not repairable under ``req:iterate-repair`` --
    withdraws under
    ``iterate_not_feasible``. Section 2.6 decides it "at exactly 0 and at no
    window", because "at a positive window ``w`` this rule would accept a point
    with ``lambda_min in (-w, 0)``, which lies in NO ``Feas^J(epsilon)``".

    THE REASON IS THE DEFECT THIS CATCHES. (H-POS) is a condition on ``q_t``,
    ``P^J_chat`` and ``K^J_chat`` and says nothing about ``J >= 0``; emitting
    ``gradient_hypothesis_positivity`` for a negative eigenvalue tells a
    consumer that a different hypothesis failed, and a consumer routes on these
    strings.
    """
    declaration, _maps = toy_setup()
    # Shallower than iterate_repair_window, so the point reaches the gate: this
    # is exactly the drift the contract says must not "pass silently". The
    # COUPLING IS KEPT EXACTLY -- the mass taken below zero on one block is put
    # on the other -- so the only condition of Eq. eq:choi-feas this point
    # fails is per-block positivity, and the reason cannot be confused with a
    # coupling failure that carries the same string for a different cause.
    depth = thresholds.declared(thresholds.ITERATE_REPAIR_WINDOW) / 10.0
    point = with_negative_block(interior_start(declaration), "s1", depth)
    point[("t0", "s0")] = np.array([[1.0 + depth]], dtype=np.complex128)
    result = _run(start=point, oracle_blocks=point)

    _assert_estimate_survived(result, AssuranceReason.ITERATE_NOT_FEASIBLE)
    gate = result.gates[0]
    assert gate.min_block_eigenvalue < 0.0
    # And it is emphatically NOT the positivity-hypothesis string.
    assert gate.withdrawal != str(AssuranceReason.GRADIENT_HYPOTHESIS_POSITIVITY)


def test_an_acceptance_iterate_off_the_exact_island_carries_the_same_reason() -> None:
    """The SECOND route to ``iterate_not_feasible``, and it is the same string.

    Requirement ``req:first-order-withdrawal`` (iv) writes "in each case": a
    ``J`` factor that fails its checks, an acceptance factor "not formed on the
    exact island under (alpha) and (beta) of Remark ``rem:acc-side``", and an
    oracle return that fails a check of ``req:iterate-checks`` all withdraw
    under this one reason; the first two leave the membership in the product
    ``AcceptSet x Feas^J(epsilon)`` unestablished. An implementation that
    invented a sixth reason for the acceptance case would have left the
    contract's vocabulary.

    The acceptance factor is RECORDED, never measured (Section 2.2), so the
    stub declaring ``exact_island = False`` is precisely what a geometry forming
    ``q_t`` in binary64 looks like to the gate.
    """
    result = _run(exact_island=False)
    _assert_estimate_survived(result, AssuranceReason.ITERATE_NOT_FEASIBLE)
    assert result.gates[0].acceptance_iterate_exact is False


# ===========================================================================
#  The oracle's status, which withdraws nothing.
# ===========================================================================


@pytest.mark.parametrize(
    "status", ["near_optimal", "suboptimal_but_feasible", "unknown"]
)
def test_a_status_that_does_not_assert_optimality_withdraws_nothing(
    status: str,
) -> None:
    """A status that asserts no optimality changes neither the tier nor the bound.

    Derived by hand from ``req:first-order-withdrawal``: it has no item
    "the oracle status does not assert optimality", and it says "Neither the
    point the oracle returned at that
    iterate nor its status removes the iterate from I". The feasible side of
    the bracket is the bound ``req:verified-feasible-side`` forms "without its
    return or its status", so the same run with an optimal status reports the
    same ``h_lb``.
    """
    result = _run(status=status)
    control = _run()
    assert result.withdrawal is None
    assert result.h_lb is not None
    assert result.h_lb == control.h_lb
    assert result.gates[0].contributes
    assert result.gates[0].oracle_optimal is False
    assert result.gates[0].oracle_status == status


# ===========================================================================
#  The positive control, and the ORDER of the four.
# ===========================================================================


def test_an_iterate_meeting_every_hypothesis_contributes_a_bracket() -> None:
    """The control: without a defect the same run REPORTS ``h_lb``.

    Every test above asserts an absence, and an absence is also what a run that
    silently never computes a bracket produces. This is the run that shows the
    gate is not simply always withdrawing: the same toy, the same alpha, an
    interior start and an optimal status, and ``h_lb`` is present with no
    reason beside it.
    """
    result = _run()
    assert result.withdrawal is None
    assert result.h_lb is not None
    assert math.isfinite(result.h_lb)
    assert any(gate.contributes for gate in result.gates)
    # thm:firstorder (ii): the bracket is a LOWER bound on h_low, and the
    # objective at the returned point is an UPPER estimate of it, so on a run
    # that reaches both the bracket does not exceed the estimate by more than
    # the arithmetic rem:fo-arithmetic declares unbudgeted.
    assert result.h_lb <= result.objective + 1e-9


def test_the_gate_decides_in_the_order_the_contract_lists_the_reasons() -> None:
    """The order of the checks is the order of the reasons, and it is testable.

    A withdrawal is ONE withdrawal, so when two hypotheses fail at one iterate
    the recorded reason is the FIRST in ``req:first-order-withdrawal``'s order.
    A run with a block below zero and a near-optimal status has one failure,
    the membership check, and the status beside it on the record, a
    diagnostic.

    The record "carries every measured quantity beside it so nothing is hidden
    by the order", which is asserted too: the oracle's status is still on the
    gate.
    """
    assert tuple(str(r) for r in WITHDRAWAL_REASONS) == FO_WITHDRAWAL_REASONS
    declaration, _maps = toy_setup()
    depth = thresholds.declared(thresholds.ITERATE_REPAIR_WINDOW) / 10.0
    point = with_negative_block(interior_start(declaration), "s1", depth)
    point[("t0", "s0")] = np.array([[1.0 + depth]], dtype=np.complex128)
    result = _run(start=point, oracle_blocks=point, status="near_optimal")

    _assert_estimate_survived(result, AssuranceReason.ITERATE_NOT_FEASIBLE)
    gate = result.gates[0]
    # BOTH MEASURED QUANTITIES ARE ON THE RECORD even though only one reason
    # is: "the record carries every measured quantity beside it SO NOTHING IS
    # HIDDEN BY THE ORDER".
    assert gate.min_block_eigenvalue < 0.0
    assert gate.oracle_status == "near_optimal"
    assert gate.oracle_optimal is False
    # Derived by hand from req:first-order-withdrawal: four items in the
    # order (i) (H-POS), (ii) (H-SUPP), (iii) the perturbation, (iv) the
    # membership; no oracle item.
    reasons = list(FO_WITHDRAWAL_REASONS)
    assert reasons == [
        "gradient_hypothesis_positivity",
        "gradient_hypothesis_support",
        "gradient_perturbation_applied",
        "iterate_not_feasible",
    ]


# ===========================================================================
#  The status a withdrawal exits under.
# ===========================================================================


def test_a_hypothesis_failure_reports_its_own_status_with_iterations_left() -> None:
    """A withdrawal is not an iteration limit, and does not say it is.

    Requirement ``req:first-order-withdrawal`` REQUIRES this exit: a hypothesis
    fails, the
    bracket is withdrawn, and the run reports the estimate with a
    machine-readable reason. Contract Section 2.6's ``optimizer_gap`` row
    decides two statuses -- ``converged`` when its stopping rule fired,
    ``iteration-limit`` when the run spent its budget -- and NEITHER is true
    here: this run stops at iteration 1 of 5.

    Reporting ``iteration-limit`` would name a cause that had not occurred.
    The exception is recorded at ``STATUS_HYPOTHESIS_WITHDRAWN``: "Section 2.6's two
    status words describe
    what optimizer_gap decides and are not a closed vocabulary; a truthful
    status is reported at exits that threshold does not decide."

    THE REASON STILL TRAVELS, which is the half the status must not displace.
    ``withdrawal`` carries ``gradient_hypothesis_support`` and the estimate
    survives -- the status says why the RUN stopped, never what happened to the
    bracket.
    """
    declaration, _maps = toy_setup()
    result = _run(
        start=singular_start(declaration),
        options=FrankWolfeOptions(max_iterations=5),
    )

    _assert_estimate_survived(result, AssuranceReason.GRADIENT_HYPOTHESIS_SUPPORT)
    assert result.status == STATUS_HYPOTHESIS_WITHDRAWN
    assert result.status not in {"converged", "iteration-limit"}
    assert result.iterations == 1, "it stopped at the failure, not at the limit"
    assert result.iterations < 5, "with iterations left in the budget"


def test_the_statuses_outside_the_gap_rule_are_the_two_that_are_disclosed() -> None:
    """The list is closed, and the strings are the ones the disclosures name.

    Both appear verbatim in the exception recorded at the site
    (``certiqs_key.solvers.frank_wolfe.driver``) and at the ``optimizer_gap`` row
    of ``spec/modules/meat-core/frank-wolfe/interface.yaml``, where the two
    status strings live in this repository -- so a rename here is a
    documentation defect and this assertion is where it surfaces.

    ``objective-infinite-at-start`` is a named constant beside the other; its
    end-to-end assertion on TOY-4c belongs to the run tier.
    """
    assert STATUS_HYPOTHESIS_WITHDRAWN == "hypothesis-withdrawn"
    assert STATUS_OBJECTIVE_INFINITE_AT_START == "objective-infinite-at-start"
    disclosed = {"hypothesis-withdrawn", "objective-infinite-at-start"}
    assert disclosed == STATUSES_OUTSIDE_THE_GAP_RULE
