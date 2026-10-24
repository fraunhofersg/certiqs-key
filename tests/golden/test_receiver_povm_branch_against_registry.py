"""The (X)-only branch selector of Definition ``def:pmc``, against the registry.

Golden replay of ``PMC_BRANCH_CASES``, ``PMC_X_CLAUSE_CASES``,
``COLLAPSE_SLACK_CASES``, ``COLLAPSE_SLACK_COUNTS`` and ``NOSLACK_STATEMENTS``
(oracle entry ``O-RP-PMC-BRANCH``), first frozen at registry 0.2.0 (a registry
version is one of tests/oracles/registry_receiver_povm.py, the frozen record,
not a version of this module).

PREDICATE (C) WAS DELETED at registry 0.2.0, and the delta note the registry
records states the consequence in bold: "NO COMPUTED VALUE CHANGES: every
setting that took branch 1 took it by (X), and every setting that failed (X)
took branch 2 already." ``PMC_BRANCH_CASES`` is that statement checked against
the thirteen registry-0.1.3 bound-data cases whose branch Definition
``def:pmc`` decides -- nine by (X), four by the window -- and NOT ONE of them
was ever selected by (C).

REMARK ``rem:noslack`` IS NOW THE CONTRACT'S OWN ARGUMENT, and it is replayed
here as arithmetic rather than as prose: ``sigma = -beta(0)``, ``beta(0) >= 0``
at every frozen tuple, so ``sigma <= 0`` always and a margin test on it is
UNSATISFIABLE.

THESE TWO TABLES ARE THE REPLACEMENTS the freeze names for the two
registry-0.1.3 objects superseded in ``test_receiver_povm_bound_against_registry.py``
-- the beta(0)/slack tuple, whose fourth field was "whether (C) fires", and the
window-requirement table, whose fourth row quoted the registry-0.1.3 sentence
in which a receiver "fails (X), FAILS (C), and is served by branch 2". Both
marks are recorded there; this file names neither object.
"""

from __future__ import annotations

from fractions import Fraction as F

import pytest
from probe_presence import requires_probe
from receiver_povm_support import TOLERANCE
from registry_receiver_povm import (
    BOUND_DATA_CASES,
    COLLAPSE_SLACK_CASES,
    COLLAPSE_SLACK_COUNTS,
    NOSLACK_STATEMENTS,
    PMC_BRANCH_CASES,
    PMC_X_CLAUSE_CASES,
    rp_oracle,
)

from certiqs_key.receiver import (
    BoundData,
    Branch,
    SettingBound,
    bound_function,
    collapse_slack,
    setting_bound,
)


def _data(case_id: str) -> BoundData:
    """Return the frozen bound-data tuple as the module's own record."""
    case = next(c for c in BOUND_DATA_CASES if c.case_id == case_id)
    return BoundData(
        port_count=case.port_count,
        gamma=float(case.gamma),
        betas=tuple(float(value) for value in case.betas),
        c=float(case.c),
        ds=tuple(float(value) for value in case.ds),
    )


@pytest.mark.contract
@pytest.mark.oracle
def test_branch_one_is_taken_exactly_where_predicate_x_holds() -> None:
    """Def. def:pmc: (X) alone, and branch 2 everywhere else."""
    assert rp_oracle("O-RP-PMC-BRANCH").claims == ("RC8",)
    for case_id, predicate_x, branch, lemma, needs_window in PMC_BRANCH_CASES:
        case = next(c for c in BOUND_DATA_CASES if c.case_id == case_id)
        record = setting_bound(
            case_id,
            _data(case_id),
            case.photon_cutoff,
            predicate_x,
            TOLERANCE,
            case.window,
        )
        assert str(record.branch) == branch, case_id
        assert record.predicate_x is predicate_x, case_id
        # The branch and (X) determine each other, which is the biconditional
        # `outputs.bound_quantifier_domain` states (`one_predicate_note`) in
        # place of the removed "which predicate" field.
        assert (record.branch is Branch.COLLAPSE) is predicate_x, case_id
        assert (record.window_minimum is not None) is needs_window, case_id
        assert (lemma == "lem:collapse") is predicate_x, case_id
        # The emitted value is unchanged from registry 0.1.3.
        assert record.weight == pytest.approx(float(case.p_mc), abs=TOLERANCE.eps_2), (
            case_id
        )


@pytest.mark.contract
@pytest.mark.oracle
@requires_probe
def test_predicate_x_has_two_clauses_and_is_decided_on_the_declaration() -> None:
    """Def. def:pmc (X); Rem. rem:windowdecidable -- before any arithmetic."""
    from certiqs_key.receiver import (
        ProbeDeclaration,
        ProbeSetting,
        predicate_x_holds,
    )

    assert len(PMC_X_CLAUSE_CASES) == 3
    clauses = {row[0]: row[1] for row in PMC_X_CLAUSE_CASES}
    # The registry's first clause: no probe modes are declared (Inp_S
    # empty), where Corollary cor:unconditioned-family sets the exact flag.
    assert "first" in clauses["BD-BB84-N2"]
    probe_free = ProbeDeclaration.probe_free()
    assert predicate_x_holds(probe_free, "off", 0) is True
    # The registry's second clause: the setting carries the vacuum probe
    # (Gamma^(t) = 0), where Proposition prop:conditioned-family sets it.
    assert "second" in clauses["BD-PROBE-OFF-N1"]
    declared = ProbeDeclaration(
        (ProbeSetting("off", (0,)), ProbeSetting("on", (F(1, 2),)))
    )
    assert predicate_x_holds(declared, "off", 1) is True
    # (X) is SUFFICIENT AND NOT NECESSARY: a probe that is ON fails it on the
    # declaration, whatever its Grams turn out to be.
    assert predicate_x_holds(declared, "on", 1) is False
    decoupled = next(
        clause for case, clause in clauses.items() if case.startswith("a probe on but")
    )
    assert "NEITHER" in decoupled


@pytest.mark.contract
@pytest.mark.oracle
def test_the_collapse_slack_is_never_positive_at_any_frozen_case() -> None:
    """Rem. rem:noslack: sigma = -beta(0) <= 0, so a margin test cannot fire."""
    frozen = {row[0]: row for row in COLLAPSE_SLACK_CASES}
    assert set(frozen) == {case.case_id for case in BOUND_DATA_CASES}
    zeros = 0
    positives = 0
    for case in BOUND_DATA_CASES:
        data = _data(case.case_id)
        _, beta_zero, sigma, holds = frozen[case.case_id]
        assert bound_function(data, 0) == pytest.approx(
            float(beta_zero), abs=TOLERANCE.eps_2
        ), case.case_id
        assert collapse_slack(data) == pytest.approx(
            float(sigma), abs=TOLERANCE.eps_2
        ), case.case_id
        # sigma = -beta(0) EXACTLY, and beta(0) >= 0, so sigma <= 0 ALWAYS.
        assert collapse_slack(data) == pytest.approx(
            -bound_function(data, 0), abs=TOLERANCE.eps_2
        ), case.case_id
        assert bound_function(data, 0) >= -TOLERANCE.eps_2, case.case_id
        assert collapse_slack(data) <= TOLERANCE.eps_2, case.case_id
        # eq:collapsehyp holds iff beta(0) = 0 exactly.
        assert holds is (float(beta_zero) == 0), case.case_id
        if float(beta_zero) == 0:
            zeros += 1
        else:
            positives += 1
    counts = dict(COLLAPSE_SLACK_COUNTS)
    assert counts["total"] == len(COLLAPSE_SLACK_CASES)
    assert counts["beta(0) = 0 exactly, so eq:collapsehyp holds"] == zeros
    assert counts["beta(0) > 0, so eq:collapsehyp fails"] == positives
    assert counts["sigma > 0 anywhere"] == 0


@pytest.mark.contract
def test_no_margin_input_and_no_computed_companion_survives() -> None:
    """Rem. rem:pmc-branch-choice: "there is no declared margin among the inputs"."""
    from certiqs_key.receiver import TOLERANCE_KEYS
    from certiqs_key.receiver import bound as bound_module

    assert "eps_hyp" not in TOLERANCE_KEYS
    assert not hasattr(bound_module, "predicate_c_holds")
    assert not hasattr(bound_module, "predicate_c_slack")
    fields = set(SettingBound.__dataclass_fields__)
    assert "predicate_c" not in fields
    assert "predicate_c_slack" not in fields
    assert "selecting_predicate" not in fields
    assert {"branch", "predicate_x", "window"} <= fields
    # Rem. rem:noslack's six conclusions, as the freeze records them.
    assert len(NOSLACK_STATEMENTS) == 6
    statements = [row[0] for row in NOSLACK_STATEMENTS]
    assert any("UNSATISFIABLE" in text for text in statements)
    assert any("only way branch 1 is ever taken is (X)" in text for text in statements)


@pytest.mark.contract
def test_minus_beta_zero_is_the_slack_a_margin_test_would_have_read() -> None:
    """Rem. rem:noslack, on a frozen case with a STRICTLY POSITIVE beta(0).

    A test demanding ``sigma >= eps > 0`` could not fire there, and one
    demanding ``sigma >= 0`` would be satisfied only in the exact-equality case,
    WHICH IS WHAT (X) ALREADY GUARANTEES FROM THE DECLARATION WITHOUT COMPUTING
    ANYTHING. The setting is served by branch 2, and that is what the module
    does. The case is selected from the frozen tables rather than named, so
    that this file references no registry-0.1.3 object the amendment marks.
    """
    case_id = next(
        cid for cid, x, branch, _, _ in PMC_BRANCH_CASES if not x and branch == "2"
    )
    beta_zero = next(row[1] for row in COLLAPSE_SLACK_CASES if row[0] == case_id)
    assert float(beta_zero) > 0.0
    case = next(c for c in BOUND_DATA_CASES if c.case_id == case_id)
    data = _data(case_id)
    assert bound_function(data, 0) == pytest.approx(float(beta_zero), abs=1e-12)
    assert collapse_slack(data) == pytest.approx(-float(beta_zero), abs=1e-12)
    record = setting_bound(
        "on", data, case.photon_cutoff, False, TOLERANCE, case.window
    )
    assert record.branch is Branch.WINDOW_AND_TAIL
    assert record.predicate_x is False
