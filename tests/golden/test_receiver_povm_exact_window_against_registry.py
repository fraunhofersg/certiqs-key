"""The emitted exact-window value (registry RC8), against the registry.

Golden replay of group RP-T: ``EXACT_COMPOSITE_CASES``, ``EXACT_WINDOW_CASES``,
``EXACT_WINDOW_ADMISSIBLE_CHOICES``, ``EXACT_WINDOW_BRANCH_REMAINDERS``,
``NO_WORSE_CASES``, ``NO_WORSE_UNDER_EVALUATION``, ``MIXED_SETTING_CASES``,
``OPT_IN_INVARIANT`` and ``BOUND_DATA_CASES_NOT_SUPERSEDED_0_3_0`` (oracle
entry ``O-RP-EXACT-WINDOW``), first frozen at registry 0.3.0 (a registry
version is one of tests/oracles/registry_receiver_povm.py, not of this module).

WHAT Eq. eq:pmcex EMITS, BRANCH BY BRANCH
=========================================
    branch 1, (X) holds:  max{0, min{ min ell(n), beta(m*_t + 1) }}
    branch 2, otherwise:  max{0, min{ min ell(n),
                                      min_{m*_t < n <= m_t} beta(n),
                                      T_{m_t} }}

with ``ell(n) = max{beta(n), beta-hat*(n) - eps_eig}`` (Eq. ``eq:elldef``) on
``N < n <= m*_t``. **Each branch keeps its own remainder** and neither is
weakened: the exact window covers ``N < n <= m*_t`` AND NOTHING ABOVE IT
(Remark ``rem:exact-window-remainders``). The frozen
``EX-PROBE-ON-N1-M2-MSTAR2-ZERO`` is the case an implementation that dropped
``T_{m_t}`` would get wrong -- it would emit ``107/750`` where the contract
emits ``0``, "AND THAT WOULD BE UNSOUND" (the frozen case's own note).

THE EMPTY MIDDLE MINIMUM IS ``+inf`` AND INACTIVE, NEVER ZERO, at ``m*_t =
m_t``. An implementation that read it as ``0`` would emit ``0`` at
``EX-PROBE-ON-N1-M3-MSTAR3-EMPTY-MIDDLE``: valid, strictly worse, and a
violation of Proposition ``prop:exactnoworse`` at the one place the contract
bothered to state a convention for.

THE OPT-IN INVARIANT IS THE OTHER HALF, AND IT IS WHAT MAKES THE EXACT WINDOW
A STRICT EXTENSION (Definition ``def:pmc``, last paragraph): a declaration
carrying no depth at any setting is governed by Eq. ``eq:pmcdef`` ALONE -- no
``beta*`` is formed, no eigenvalue of any block above the cutoff is computed,
and Assumption ``ass:eig`` is not invoked. Every frozen bound-data case
declares none, which is why NOT ONE of them is superseded, and the four the
registry names -- ``p_mc = 0, 1/2, 3/4, 1/8`` -- are re-derived below from
their own bound data.

``beta-hat*`` IS INJECTED FROM THE FREEZE HERE, NOT RECOMPUTED. The frozen
``window`` field of each case carries the computed value the case declares, and
Eq. ``eq:pmcex`` is a function of THAT number: the replay of ``beta-hat*``
against the constructed receiver is
``test_receiver_povm_exact_block_against_registry.py``'s, and separating the two
is what lets the emitted expression be checked at values -- including a violated
Assumption ``ass:eig`` -- that no receiver of this registry produces.
"""

from __future__ import annotations

import pytest
from probe_presence import requires_probe
from receiver_povm_support import (
    MACHINE_AGREEMENT,
    TOLERANCE,
    bound_data_of,
    probe_receiver_request,
    tolerances_at,
)
from registry_receiver_povm import (
    BOUND_DATA_CASES,
    BOUND_DATA_CASES_NOT_SUPERSEDED_0_3_0,
    EXACT_COMPOSITE_CASES,
    EXACT_WINDOW_ADMISSIBLE_CHOICES,
    EXACT_WINDOW_BRANCH_REMAINDERS,
    EXACT_WINDOW_CASES,
    MIXED_SETTING_CASES,
    NO_WORSE_CASES,
    NO_WORSE_UNDER_EVALUATION,
    OPT_IN_INVARIANT,
    rp_oracle,
)

from certiqs_key.receiver import (
    Branch,
    SettingBound,
    bound_function,
    construct_receiver,
    exact_composite,
    setting_bound,
    tail_value,
    window_floor,
    window_indices,
)
from certiqs_key.receiver.errors import HypothesisError


def _record(case: object) -> SettingBound:
    """Return the module's :class:`SettingBound` for one frozen window case."""
    return setting_bound(
        case.case_id,  # type: ignore[attr-defined]
        bound_data_of(case),
        case.photon_cutoff,  # type: ignore[attr-defined]
        case.predicate_x,  # type: ignore[attr-defined]
        tolerances_at(case.eps_eig),  # type: ignore[attr-defined]
        case.tail_window,  # type: ignore[attr-defined]
        case.exact_depth,  # type: ignore[attr-defined]
        tuple(
            (photons, float(computed))
            for photons, _beta, computed, _ell in case.window  # type: ignore[attr-defined]
        ),
    )


@pytest.mark.contract
@pytest.mark.oracle
def test_the_composite_of_lemma_exactwindow_is_the_frozen_value() -> None:
    """Lemma lem:exactwindow, Eq. eq:exactcomposite, on admissible reals.

    ``P = max{0, min{ min ell, tau }}``, evaluated on the abstract numbers the
    lemma is stated about. Four things are exercised here and nowhere else:
    the WINDOW binding, the REMAINDER binding, the ``P = 0`` branch that is the
    one step using Eq. ``eq:mcpos``, and the FIRST disjunct of Eq. ``eq:tailadm``
    -- "a NON-POSITIVE tau is admissible with NO FURTHER HYPOTHESIS WHATEVER",
    and it then drives the whole expression to 0 however good the window is.
    """
    assert rp_oracle("O-RP-EXACT-WINDOW").claims == ("RC8",)
    for case in EXACT_COMPOSITE_CASES:
        window = [float(value) for _n, value in case.ell_values]
        got = exact_composite(window, float(case.tau))
        assert abs(got - float(case.p_value)) <= MACHINE_AGREEMENT, case.case_id
        # The inner minimum, before the outer max{0, .}, is frozen too, so the
        # two operations are checked apart rather than only in combination.
        inner = min(min(window), float(case.tau))
        assert abs(inner - float(case.inner_minimum)) <= MACHINE_AGREEMENT, case.case_id
        assert abs(min(window) - float(case.window_minimum)) <= MACHINE_AGREEMENT, (
            case.case_id
        )
        # The outer maximum FIRES exactly at the frozen P = 0 branch, which is
        # the one step of the proof that uses Eq. eq:mcpos.
        assert (got > inner + MACHINE_AGREEMENT) is case.uses_mcpos_branch, case.case_id
        # Lemma lem:exactwindow's range: 0 <= P <= 1, endpoint included.
        assert -MACHINE_AGREEMENT <= got <= 1.0 + MACHINE_AGREEMENT, case.case_id
        # The index set the window was read over is the lemma's own.
        assert tuple(n for n, _ in case.ell_values) == window_indices(
            case.photon_cutoff, case.exact_depth
        ), case.case_id
    # THE WINDOW IS NON-EMPTY FOR EVERY m* > N, which is what the lemma needs to
    # prove P <= 1; an empty one is a hypothesis failure, not a value.
    with pytest.raises(HypothesisError):
        exact_composite([], 0.5)
    with pytest.raises(HypothesisError):
        window_indices(2, 2)


@pytest.mark.contract
@pytest.mark.oracle
def test_the_two_admissible_remainders_are_the_ones_each_branch_keeps() -> None:
    """Lemma lem:exactwindow (i) and (ii); Def. def:pmcex's own paragraph.

    Branch 1 takes ``beta(m*_t + 1)``, admissible by part (ii) "BECAUSE
    PREDICATE (X) MAKES Eq. ``eq:collapsehyp`` HOLD"; branch 2 keeps its own
    analytic middle window AND its tail ``T_{m_t}``, admissible by part (i)
    "with NO HYPOTHESIS". The record says which it used, so an implementation
    that silently swapped them would be visible in the artifact.
    """
    remainders = {row[0]: row for row in EXACT_WINDOW_BRANCH_REMAINDERS}
    assert remainders["1"][1] is True
    assert remainders["2"][1] is False
    assert len(EXACT_WINDOW_ADMISSIBLE_CHOICES) == 3
    for case in EXACT_WINDOW_CASES:
        record = _record(case)
        exact = record.exact_window
        assert exact is not None, case.case_id
        assert exact.remainder == pytest.approx(
            float(case.remainder), abs=MACHINE_AGREEMENT
        ), case.case_id
        assert exact.remainder_kind == case.remainder_kind.replace(
            "{m_t}", "(m_t)"
        ).replace("m* + 1", "m* + 1"), case.case_id
        if case.predicate_x:
            assert record.branch is Branch.COLLAPSE, case.case_id
            # Branch 1's remainder is beta at ONE INDEX ABOVE THE DEPTH.
            assert exact.remainder == pytest.approx(
                bound_function(bound_data_of(case), case.exact_depth + 1),
                abs=MACHINE_AGREEMENT,
            ), case.case_id
            assert exact.middle_minimum is None, case.case_id
        else:
            assert record.branch is Branch.WINDOW_AND_TAIL, case.case_id
            assert case.tail_window is not None
            assert exact.remainder == pytest.approx(
                tail_value(bound_data_of(case), case.tail_window),
                abs=MACHINE_AGREEMENT,
            ), case.case_id


@pytest.mark.contract
@pytest.mark.oracle
def test_the_emitted_value_is_eq_pmcex_at_every_frozen_declaration() -> None:
    """Definition def:pmcex, Eq. eq:elldef and Eq. eq:pmcex, case by case.

    THIRTEEN DECLARATIONS across both branches, both boundaries of the declared
    ``eps_eig`` domain, the empty middle minimum, and the outer maximum firing
    at a receiver. The ``ell(n)`` are checked term by term BEFORE the minimum,
    so that a value agreeing by cancellation would not pass.
    """
    for case in EXACT_WINDOW_CASES:
        data = bound_data_of(case)
        record = _record(case)
        exact = record.exact_window
        assert exact is not None, case.case_id
        assert exact.depth == case.exact_depth, case.case_id
        assert tuple(n for n, *_ in exact.rows) == window_indices(
            case.photon_cutoff, case.exact_depth
        ), case.case_id
        # Eq. eq:elldef, TERM BY TERM: the analytic bound, the computed
        # eigenvalue UNMODIFIED, and the maximum of the two after the slack.
        for (n, beta, computed, ell), row in zip(case.window, exact.rows, strict=True):
            assert row[0] == n, case.case_id
            assert row[1] == pytest.approx(float(beta), abs=MACHINE_AGREEMENT)
            assert row[2] == pytest.approx(float(computed), abs=MACHINE_AGREEMENT)
            assert row[3] == pytest.approx(float(ell), abs=MACHINE_AGREEMENT)
            assert row[3] == pytest.approx(
                window_floor(row[1], row[2], float(case.eps_eig)), abs=0.0
            )
            # THE COMPUTED VALUE IS CARRIED UNMODIFIED, not the slacked one.
            assert row[2] == pytest.approx(float(computed), abs=0.0)
        assert exact.window_minimum == pytest.approx(
            float(case.window_minimum), abs=MACHINE_AGREEMENT
        ), case.case_id
        # THE MIDDLE MINIMUM: a number where the index set is non-empty, and
        # None -- "+infinity and INACTIVE" -- exactly where m*_t = m_t.
        assert exact.middle_window_empty is case.middle_window_empty, case.case_id
        if case.middle_window_minimum is None:
            assert exact.middle_minimum is None, case.case_id
        else:
            assert exact.middle_minimum == pytest.approx(
                float(case.middle_window_minimum), abs=MACHINE_AGREEMENT
            ), case.case_id
        # THE EMITTED VALUE.
        assert record.weight == pytest.approx(
            float(case.p_mc), abs=MACHINE_AGREEMENT
        ), case.case_id
        assert -MACHINE_AGREEMENT <= record.weight <= 1.0 + MACHINE_AGREEMENT
        # And the record says the value came from Def. def:pmcex, at that depth
        # (Req. req:weight-provenance: "the artifact says WHICH of Definitions
        # def:pmc and def:pmcex PRODUCED EACH AND AT WHAT DEPTH").
        assert record.definition == "def:pmcex", case.case_id
        assert record.assumption_eig_invoked is True, case.case_id
        # THE SAME DECLARATION WITHOUT A DEPTH emits Eq. eq:pmcdef's value, and
        # forms nothing: this is the opt-in invariant at one setting.
        plain = setting_bound(
            case.case_id,
            data,
            case.photon_cutoff,
            case.predicate_x,
            TOLERANCE,
            case.tail_window,
        )
        assert plain.exact_window is None, case.case_id
        assert plain.definition == "def:pmc", case.case_id
        assert plain.assumption_eig_invoked is False, case.case_id
        assert plain.weight == pytest.approx(
            float(case.p_mc_without_depth), abs=MACHINE_AGREEMENT
        ), case.case_id


@pytest.mark.contract
@pytest.mark.oracle
def test_prop_exactnoworse_holds_at_every_frozen_declaration() -> None:
    """Proposition prop:exactnoworse, with Remark rem:noworsefl's qualification.

    "At every setting carrying a declared depth, the value Eq. ``eq:pmcex`` is at
    least the value Eq. ``eq:pmcdef`` gives at that setting ON THE SAME BOUND
    DATA." Seven of the thirteen are STRICT and six are EQUAL, and the equal
    ones are not failures: they are every receiver whose channel space is one
    dimensional, where Eq. ``eq:mcbound`` holds with equality and the window has
    nothing to find.

    ``NO_WORSE_UNDER_EVALUATION`` records the one step that does NOT survive an
    evaluation term for term -- branch 1's ``beta(m*_t + 1) >= beta(N + 1)``,
    which is Lemma ``lem:collapse``, a statement about EXACT values. So this is
    a statement about the mathematics and NOT a runtime invariant an
    implementation may assert as a check, and nothing in this module asserts it.
    """
    frozen = {row[0]: (row[1], row[2]) for row in NO_WORSE_CASES}
    strict = 0
    for case in EXACT_WINDOW_CASES:
        without, with_depth = frozen[case.case_id]
        assert float(case.p_mc_without_depth) == float(without), case.case_id
        assert float(case.p_mc) == float(with_depth), case.case_id
        record = _record(case)
        plain = setting_bound(
            case.case_id,
            bound_data_of(case),
            case.photon_cutoff,
            case.predicate_x,
            TOLERANCE,
            case.tail_window,
        )
        assert record.weight >= plain.weight - MACHINE_AGREEMENT, case.case_id
        if record.weight > plain.weight + MACHINE_AGREEMENT:
            strict += 1
    assert strict == 7
    assert len(EXACT_WINDOW_CASES) - strict == 6
    # The three steps of the proof, and which survives an evaluation.
    survives = {row[0]: row[1] for row in NO_WORSE_UNDER_EVALUATION}
    assert survives["branch 1's beta(m*_t + 1) >= beta(N + 1)"] is False
    assert survives["ell(n) >= beta(n) on the exact window"] is True


@pytest.mark.contract
@pytest.mark.oracle
def test_the_opt_in_invariant_leaves_every_earlier_bound_case_standing() -> None:
    """Def. def:pmc: a declaration with no depth is governed by Eq. eq:pmcdef ALONE.

    Every frozen bound-data case declares NO depth, so the module emits for it
    what Eq. ``eq:pmcdef`` defines -- expression for expression -- and NOT ONE
    of them is superseded. The four the registry names are re-derived from
    their own bound data rather than asserted.
    """
    invariant = {row[0]: row for row in OPT_IN_INVARIANT}
    assert len(invariant) == len(BOUND_DATA_CASES)
    for case in BOUND_DATA_CASES:
        row = invariant[case.case_id]
        # (declares a depth, beta* formed, ass:eig invoked, r_6 emitted) all
        # False; p_mc unchanged True.
        assert row[1:5] == (False, False, False, False), case.case_id
        assert row[5] is True, case.case_id
    named = {row[0]: (row[1], row[2]) for row in BOUND_DATA_CASES_NOT_SUPERSEDED_0_3_0}
    assert set(named) == {
        "BD-BB84-N1-ZERO",
        "BD-BB84-N2",
        "BD-BB84-N3",
        "BD-BB84-PZ-QUARTER-N2",
    }
    for case_id, (cutoff, expected) in named.items():
        case = next(c for c in BOUND_DATA_CASES if c.case_id == case_id)
        assert case.photon_cutoff == cutoff, case_id
        record = setting_bound(
            case_id,
            bound_data_of(case),
            cutoff,
            case.predicate == "X",
            TOLERANCE,
            case.window,
        )
        assert record.exact_window is None, case_id
        assert record.definition == "def:pmc", case_id
        assert record.weight == pytest.approx(float(expected), abs=MACHINE_AGREEMENT), (
            case_id
        )
        assert record.weight == pytest.approx(float(case.p_mc), abs=MACHINE_AGREEMENT)


@pytest.mark.contract
@pytest.mark.oracle
@requires_probe
def test_the_two_kinds_of_setting_mix_in_one_declaration() -> None:
    """Def. def:pmc: the two kinds of setting MAY BE MIXED in one declaration.

    And Def. def:pmcex's per-setting paragraph: a declaration that carries a
    depth at some settings and not at others has its uniform weight BOUNDED BY
    THE SETTINGS WITHOUT ONE. At ``MIX-DEPTH-AT-THERMAL-ONLY`` the cost is paid
    at one setting and the answer is decided at the other.

    This runs the WHOLE inputs-to-artifact pass on the frozen
    ``I-PROBE`` receiver, so the conditioned families, the two branches, the
    minimum over ``T`` and the emitted record are all exercised together.
    """
    depths = {
        "MIX-NO-DEPTH-ANYWHERE": {},
        "MIX-DEPTH-AT-OFF-ONLY": {"off": 2},
        "MIX-DEPTH-AT-THERMAL-ONLY": {"on": 2},
        "MIX-DEPTH-AT-BOTH": {"off": 2, "on": 2},
    }
    # The registry's setting labels are `off` and `thermal`; this receiver
    # declares them `off` and `on`, and the two name the same two settings.
    for case in MIXED_SETTING_CASES:
        emission = construct_receiver(
            probe_receiver_request(exact_window=dict(depths[case.case_id]))
        )
        assert emission.refusal is None, (case.case_id, emission.refusal)
        artifact = emission.artifact
        assert artifact is not None
        weights = dict(artifact.high_photon_bounds.per_setting)
        for label, declared, depth, definition, value in case.per_setting:
            ours = "on" if label == "thermal" else label
            assert weights[ours] == pytest.approx(
                float(value), abs=MACHINE_AGREEMENT
            ), (case.case_id, label)
            record = next(
                row
                for row in artifact.bound_quantifier_domain.per_setting
                if row.setting == ours
            )
            # Derived by hand from receiver/req:eig-ledger-row:
            # a setting invokes A-EIG exactly when its emitted weight is that
            # of def:pmcex evaluated in floating point; every weight here is
            # the enclosed one (req:rigorous-weight), so none does.
            assert record.evaluation == "rigorous"
            assert record.assumption_eig_invoked is False, (case.case_id, label)
            assert (record.exact_window is not None) is declared
            if declared:
                assert record.exact_window is not None
                assert record.exact_window.depth == depth
            assert definition.startswith("Eq. eq:pmcex") is declared
            assert record.definition == ("def:pmcex" if declared else "def:pmc")
        # The entry's UNIFORM weight p_mc is the MINIMUM over T of the
        # per-setting weights above, which are the slot's guaranteed content
        # (thm:emitted-bound eq:pmcsetting); the exact window
        # does not change which setting binds at this receiver.
        assert artifact.high_photon_bounds.entries[0].weight == pytest.approx(
            float(case.p_mc), abs=MACHINE_AGREEMENT
        ), case.case_id
        # Ass. ass:eig is invoked exactly where a depth is declared AND the
        # weight is evaluated in floating point (derived by hand
        # from receiver/req:eig-ledger-row; the frozen eig_invoked reads the
        # depth alone). Every weight here is the enclosed one, so the ledger
        # records no setting.
        ledger = {row.assumption_id: row for row in artifact.assumption_ledger}
        invoked = dict(ledger["A-EIG"].constrains)["invoked_at"]
        assert invoked == [], case.case_id
