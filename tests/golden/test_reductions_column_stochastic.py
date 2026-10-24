"""Group PR-P: the column-stochasticity row of contract 0.3.0, RUN BY THE CODE.

``tests/oracles/registry_reductions.py`` freezes FIVE declarations and,
for each, what every row that looks at them decides. Those frozen decisions were
derived by hand from the accepted ``contract.tex`` before any code changed, and
``tests/oracles/test_reductions_registry.py`` checks them against each
other WITHOUT IMPORTING THE IMPLEMENTATION. This file closes the loop: it builds
each frozen declaration as a real ``DarkCountChannel``, runs the rules on it, and
runs the whole of :func:`~certiqs_key.reductions.emit.reduce` where the declaration
carries enough data to reach an emission.

WHAT THE FIVE CASES ARE FOR, IN THE FREEZE'S OWN GROUPING
=========================================================
Two ANCHORS -- ``CS-canonical-admit``, which is the band-1 ``RC2`` declaration
read one level lower, and ``CS-coarse-admit``, whose ``cg`` merges two patterns
so that a descended entry is a genuine SUM. Both are admitted at 0.3.0 exactly as
at 0.2.0, which is the regression half: THE AMENDMENT REFUSES STRICTLY MORE AND
NEVER LESS, and no conforming declaration changes hands.

One DEFECT EXAMPLE -- ``CS-colsum-refuse``, which is the contract's own: "A
DARK-COUNT MATRIX WHOSE COLUMNS SUM TO 1 ONLY TO WITHIN A ROUNDING ERROR, say --
IS STILL REFUSED, NOW BY THE COLUMN-STOCHASTICITY ROW AND UNDER ITS OWN REASON
STRING" (Remark ``rem:tolboundary``). It is ``CS-canonical-admit`` with ONE entry
moved by exactly ``1/100``.

And the BOUNDARY PAIR, which is why the row is not redundant with the descent row
beside it. Remark ``rem:darkcompose``: "a STRICTLY POSITIVE entry in a
(D2)-forbidden position fails monotonicity while leaving column-stochasticity
untouched, and A NEGATIVE ENTRY IN SUCH A POSITION DOES THE REVERSE -- IT
SATISFIES THE MONOTONICITY IMPLICATION VACUOUSLY AND FAILS NON-NEGATIVITY."
``CS-negative-vacuous-refuse`` is the first half and ``CS-positive-forbidden-
refuse`` the second: each is refused by exactly ONE of the two rows and admitted
by the other, and the two carry DIFFERENT reason strings.

THE ONE FIXTURE DECISION MADE HERE, AND IT IS NOT A CONTRACT DECISION
=====================================================================
The frozen cases declare ``R``, ``cg``, the slot weight and the probe weights and
NOTHING ELSE -- deliberately, because the registry records that whether
Proposition ``prop:tolrows`` (iv) fires "depends on data this case does not
declare", and "NOTHING IS FROZEN HERE ABOUT THAT BUDGET". Reaching
:func:`~certiqs_key.reductions.emit.reduce` needs declared photon blocks, so this
file supplies them: one ``1 x 1`` block per letter and setting, summing EXACTLY
to one at every setting, so that parts (i)-(iii) hold at every ``eps_op >= 0``
and the only thing varying between cases is ``R``. Those blocks are test data.
They decide nothing the contract states, and the assertions below say which row
they let a case reach rather than assuming it.

WHY ONE CASE IS RUN AT A POSITIVE TOLERANCE, AND WHAT THAT PROVES
==================================================================
This is the subtlety the whole group exists for and it must not be glossed.
Remark ``rem:colstoch`` records TWO indirect paths by which a column-sum defect
was already refused at 0.2.0: through ``total_weight_not_below_one`` where the
defect lifts some ``r_min,i`` to one, and through Proposition ``prop:tolrows``
(iv) under ``declaration_outside_tolerance`` where it exceeds that part's
completeness budget -- "at ``eps_op = 0`` the threshold ``q_t |Y| dcf eps_op`` is
zero, so ANY excess at all refuses". And then: "A DEFECT OUTSIDE THOSE TWO -- one
that at ``eps_op > 0`` NEITHER LIFTS SOME ``r_min,i`` TO 1 NOR EXCEEDS THAT
PART'S TOLERANCE BUDGET -- MET NO ROW AT ALL."

THAT RESIDUE IS THE CLASS THE ROW EXISTS FOR, and it is the one class that
changes hands. So ``CS-colsum-refuse`` is run twice: at ``eps_op = 0``, where the
tolerance row also refuses and -- IT COMING FIRST IN THE CONTRACT'S ROW ORDER --
carries the reason a caller receives; and at ``eps_op = 1/100``, where the
tolerance row PASSES and the new row is the only thing standing between the
declaration and an emitted artifact. The second run is the one that would have
emitted at 0.2.0. Both runs are asserted, because a test that only ran the first
would pass against an implementation in which the new row was never reachable.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Any

import pytest
from reductions_support import RECEIVER_LEDGER_KEYS
from reductions_support import reduce_flat_call as reduce
from registry_reductions import (
    COLSTOCH_CANONICAL_ADMIT,
    COLSTOCH_CASES,
    COLSTOCH_COARSE_ADMIT,
    COLSTOCH_COLSUM_REFUSE,
    COLSTOCH_NEGATIVE_VACUOUS_REFUSE,
    COLSTOCH_POSITIVE_FORBIDDEN_REFUSE,
    COLSTOCH_PROBE_WEIGHTS,
    COLSTOCH_SLOT_WEIGHT,
    COLSTOCH_TOLERANCE_PROBE,
    CS_CASES_PR_R,
    CS_PROBE_WEIGHTS_PR_R,
    CS_SLOT_WEIGHT_PR_R,
    FAIL_CLOSED_ROW_COUNT_0_3_0,
    FAIL_CLOSED_ROW_COUNT_1_0_0,
    FAIL_CLOSED_ROWS_ADDED_0_3_0,
    KAPPA_FIXTURE_PR_R,
    PR_R1,
    REFUSAL_REASONS_0_3_0,
    REFUSAL_REASONS_1_0_0,
    REFUSAL_REASONS_1_0_0_ORDER_NOTE,
    REFUSAL_REASONS_ADDED_0_3_0,
    SCOPE_MARKS_1_0_0,
)

from certiqs_key.foundations.exact import matrix
from certiqs_key.reductions import MATHEMATICAL_SPEC_VERSION
from certiqs_key.reductions.artifact import ReductionOutcome
from certiqs_key.reductions.inputs import (
    BoundQuantifierDomain,
    ChannelGrading,
    ClickPattern,
    CoarseGraining,
    DarkCountChannel,
    HighPhotonBound,
    InheritedAssumption,
    LinkDeclaration,
    ProbeDeclaration,
    ProtocolDeclaration,
    ReceiverArtifactRows,
    ReductionRequest,
)
from certiqs_key.reductions.reasons import (
    FailClosedRule,
    LinkKind,
    LinkStage,
    RefusalReason,
    SourceMode,
)
from certiqs_key.reductions.validation import (
    RULE_ORDER,
)
from certiqs_key.reductions.wpfss.validation import (
    WPFSS_ROWS,
    rule_absorbing,
    rule_column_stochastic,
    rule_descent,
    rule_fibre,
    rule_high_photon_slot,
    rule_total_weight,
)
from certiqs_key.reductions.wpfss.validation import (
    FailClosedRule as WpfssRule,
)
from certiqs_key.reductions.wpfss.weights import (
    declared_column_sums,
    descend,
    is_column_stochastic,
    is_monotone,
    minimum_off_letter_rate,
    smallest_declared_entry,
)

#: THE FIXTURE LATTICE EXPONENT. Section 2.1's `lattice_exponent` row is
#: REQUIRED and has "NO DEFAULT AND NO FALLBACK", so every request below
#: declares one -- which is the point of the row, and a test helper that
#: supplied one silently would be the default the contract forbids. The value
#: is a fixture choice: the contract "fixes no value".
KAPPA_FIXTURE: int = 12

F = Fraction

#: THE COVERAGE IS SPLIT IN TWO. The 0.3.0 declarations are over fifths and
#: 1.0.1 refuses them under ``declaration_not_exactly_admissible``
#: (``def:exactadm`` (b), Eq. ``eq:latinv``), so a non-strict ``xfail`` would
#: let a regression in any of them leave the suite green.
#:
#: THE 0.3.0 CASES ARE VALID, for the contract's own reason:
#: the column-stochasticity row is "A SIGN-AND-EQUALITY COMPARISON ON THE
#: DECLARED ENTRIES OF ``R``" and tests neither ``eq:latinv`` nor any tolerance,
#: so a matrix over fifths is still a CORRECT DECISION about those two subrules
#: even though the declaration as a whole would be refused elsewhere. Every test
#: that decides a subrule WITHOUT calling :func:`reduce` therefore uses its
#: 0.3.0 parametrization.
#:
#: EVERY TEST THAT REACHES :func:`reduce` decides ``eq:latinv`` too, so it
#: reads band 5's ``CS_CASES_PR_R`` (PRR-7a...7e), the dyadic twins of the same
#: five declarations, derived by hand from the accepted 1.0.1 by an agent that
#: wrote no source file. There is no test of the declared operator tolerance,
#: which is not in the contract (see the note at its place below).

#: FIXTURE DATA AND NOT A PIN. Section ``sec:failclosed``'s receiver-spec row
#: tests SET MEMBERSHIP of the artifact's declared version in a caller-supplied
#: tuple; ``accepted_receiver_versions`` "is a caller-supplied tuple defaulting
#: to empty, which is fail-closed by construction and is not a pin". The
#: fixture's receiver version is the receiver's accepted one, which STATES the
#: per-setting weights; the wpfss slot row refuses an artifact of a version
#: that does not (req:supplier-version).
ACCEPTED = ("receiver@0.9.0",)


def pattern_of(spelling: str) -> ClickPattern:
    """Return the frozen registry's click-pattern spelling as a set.

    ``"e"`` is the empty pattern and ``"12"`` is ``{1, 2}``; the registry's
    ``ColumnStochasticCase.patterns`` field states the convention.
    """
    return frozenset() if spelling == "e" else frozenset(int(c) for c in spelling)


def channel_of(case: Any) -> DarkCountChannel:
    """Return the frozen RAW matrix as a declared :class:`DarkCountChannel`.

    THE RAW MATRIX IS THE ROW'S SUBJECT. "DECIDED ON ``R``, WHICH SUFFICES."
    A zero entry is dropped from the mapping rather than stored, which is the
    record's declared convention -- an absent pair IS a declared zero -- so this
    also exercises the fact that both halves of the row quantify over the whole
    of ``2^[K]`` and not over the keys that happen to be present.
    """
    entries = {
        (pattern_of(row), pattern_of(column)): value
        for column, rows in case.raw_matrix
        for row, value in rows
        if value != 0
    }
    return DarkCountChannel(ports=case.ports, entries=entries)


def coarse_of(case: Any) -> CoarseGraining:
    """Return the frozen coarse-graining, in the declared letter order."""
    letters = tuple(dict.fromkeys(letter for _, letter in case.coarse_graining))
    return CoarseGraining(
        ports=case.ports,
        letters=letters,
        assignment={
            pattern_of(spelling): letter for spelling, letter in case.coarse_graining
        },
    )


def declaration_of(
    case: Any, *, operator_tolerance: object = None
) -> tuple[ReceiverArtifactRows, ProtocolDeclaration, ReductionRequest]:
    """Return a full reduction request built around the frozen case's ``R``.

    Everything but ``R`` and ``cg`` is the same across the five cases -- the slot
    weight ``COLSTOCH_SLOT_WEIGHT``, the probe weights ``COLSTOCH_PROBE_WEIGHTS``,
    the cutoff and the blocks -- which is what makes a difference in outcome
    attributable to the declared matrix and to nothing else.

    THE BLOCKS ARE AN EXACT POVM AT EVERY SETTING: the first letter carries
    ``1 - (|Y| - 1)/6`` and the rest ``1/6``, so ``sum_y blk M^{=0}_{y|t} = 1``
    exactly and Proposition ``prop:tolrows`` (i)-(iii) hold at every
    ``eps_op >= 0``. Part (iv), on the POST-PROCESSED family, is the one that
    can still fire, and it is the whole point of the ``eps_op`` argument.
    """
    coarse = coarse_of(case)
    settings = tuple(setting for setting, _ in COLSTOCH_PROBE_WEIGHTS)
    letters = coarse.letters
    share = F(1, 6)
    values = {letters[0]: 1 - share * (len(letters) - 1)}
    values.update(dict.fromkeys(letters[1:], share))
    artifact = ReceiverArtifactRows(
        mathematical_spec_version=ACCEPTED[0],
        detection_alphabet=letters,
        photon_blocks={
            (letter, setting): (matrix([[values[letter]]]),)
            for letter in letters
            for setting in settings
        },
        high_photon_bounds=(
            HighPhotonBound.uniform(
                coarse.fibre(case.bounded_letter), COLSTOCH_SLOT_WEIGHT, settings
            ),
        ),
        bound_quantifier_domain=BoundQuantifierDomain(cutoff=0, settings=settings),
        dark_count_channel=channel_of(case),
        outcome_coarse_graining=coarse,
        bound_evaluation="floating_point",
        channel_grading=ChannelGrading(block_dimensions=(1,)),
        validation_results_present=True,
        declared_device_family=(),
        occupation_basis_order=(),
    )
    declaration = ProtocolDeclaration(
        probe_declaration=ProbeDeclaration(
            settings=settings, weights=dict(COLSTOCH_PROBE_WEIGHTS)
        ),
        detection_alphabet=letters,
        photon_cutoff=0,
        source_mode=SourceMode.UNTRUSTED,
        joint_alphabet=tuple(
            (letter, setting) for setting in settings for letter in letters
        ),
    )
    request = ReductionRequest(
        lattice_exponent=KAPPA_FIXTURE,
        link_declarations=(
            LinkDeclaration(stage=LinkStage.RECEIVER, kind=LinkKind.WPFSS),
            LinkDeclaration(stage=LinkStage.RECEIVER, kind=LinkKind.PINCHING),
        ),
        route="encoded",
        accepted_receiver_versions=ACCEPTED,
        requested_assurance="estimate",
        operator_tolerance=operator_tolerance,
    )
    return artifact, declaration, request


def outcome_of(case: Any, *, operator_tolerance: object = None) -> ReductionOutcome:
    """Run the whole emission path on the frozen case."""
    return reduce(*declaration_of(case, operator_tolerance=operator_tolerance))


def declaration_of_pr_r(
    case: Any,
) -> tuple[ReceiverArtifactRows, ProtocolDeclaration, ReductionRequest]:
    """Return a full 1.0.1-conforming request built around a band-5 case.

    THE SAME SHAPE AS :func:`declaration_of` AND DIFFERENT NUMBERS, and every
    number is the freeze's: the declared blocks are ``case.declared_blocks``
    (dyadic, summing to one exactly at every setting), the probe weights are
    ``CS_PROBE_WEIGHTS_PR_R`` and the slot weight ``CS_SLOT_WEIGHT_PR_R``.
    Nothing here is derived from the code it tests.

    ``operator_tolerance`` HAS NO COUNTERPART AND TAKES NO ARGUMENT. The field
    left ``ReductionRequest`` at 1.0.0 with the apparatus behind it, and
    ``kappa`` is not a successor: the ``lattice_exponent`` row says so in terms
    -- "it is not a tolerance, nothing is admitted or refused WITHIN kappa".
    """
    coarse = coarse_of(case)
    settings = tuple(setting for setting, _ in CS_PROBE_WEIGHTS_PR_R)
    letters = coarse.letters
    values = dict(case.declared_blocks)
    artifact = ReceiverArtifactRows(
        mathematical_spec_version=ACCEPTED[0],
        detection_alphabet=letters,
        photon_blocks={
            (letter, setting): (matrix([[values[letter]]]),)
            for letter in letters
            for setting in settings
        },
        high_photon_bounds=(
            HighPhotonBound.uniform(
                coarse.fibre(case.bounded_letter), CS_SLOT_WEIGHT_PR_R, settings
            ),
        ),
        bound_quantifier_domain=BoundQuantifierDomain(cutoff=0, settings=settings),
        dark_count_channel=channel_of(case),
        outcome_coarse_graining=coarse,
        bound_evaluation="floating_point",
        channel_grading=ChannelGrading(block_dimensions=(1,)),
        validation_results_present=True,
        declared_device_family=(),
        occupation_basis_order=(),
        inherited_assumption_ledger=tuple(
            InheritedAssumption(machine_key=key)
            for key in RECEIVER_LEDGER_KEYS
        ),
    )
    declaration = ProtocolDeclaration(
        probe_declaration=ProbeDeclaration(
            settings=settings, weights=dict(CS_PROBE_WEIGHTS_PR_R)
        ),
        detection_alphabet=letters,
        photon_cutoff=0,
        source_mode=SourceMode.UNTRUSTED,
        joint_alphabet=tuple(
            (letter, setting) for setting in settings for letter in letters
        ),
    )
    request = ReductionRequest(
        lattice_exponent=KAPPA_FIXTURE_PR_R,
        link_declarations=(
            LinkDeclaration(stage=LinkStage.RECEIVER, kind=LinkKind.WPFSS),
            LinkDeclaration(stage=LinkStage.RECEIVER, kind=LinkKind.PINCHING),
        ),
        route="encoded",
        accepted_receiver_versions=ACCEPTED,
        requested_assurance="estimate",
    )
    return artifact, declaration, request


def outcome_of_pr_r(case: Any) -> ReductionOutcome:
    """Run the whole emission path on a band-5 dyadic case."""
    return reduce(*declaration_of_pr_r(case))


def _pr_r(case_id: str) -> Any:
    """Return the band-5 case with this id, or fail loudly."""
    return next(case for case in CS_CASES_PR_R if case.case_id == case_id)


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("case", CS_CASES_PR_R, ids=lambda c: c.case_id)
def test_the_code_decides_every_dyadic_case_as_the_freeze_does(case: Any) -> None:
    """The same two subrules on the LATTICE-ADMISSIBLE twin of each declaration.

    The 0.3.0 parametrization above is kept and this one is added beside it:
    the row's decision must not depend on whether the declared entries happen to
    be dyadic, and asserting it on both families is the only way to see that.
    Band 5 additionally freezes ``all_entries_on_lattice`` per case, which is
    the property the 0.3.0 twins fail and the row does NOT read.
    """
    channel = channel_of(case)
    coarse = coarse_of(case)

    assert smallest_declared_entry(channel) == case.min_entry
    assert (smallest_declared_entry(channel) >= 0) is case.non_negative
    sums = declared_column_sums(channel)
    assert {
        "".join(sorted(str(k) for k in sorted(column))) or "e": total
        for column, total in sums.items()
    } == dict(case.column_sums)
    assert all(total == 1 for total in sums.values()) is case.unit_columns

    assert is_column_stochastic(channel) is case.column_stochastic_row_admits
    refusal = rule_column_stochastic(channel)
    assert (refusal is None) is case.column_stochastic_row_admits

    assert is_monotone(channel) is case.monotone
    assert (descend(channel, coarse) is not None) is case.descends
    assert (rule_descent(channel, coarse) is None) is case.descent_row_admits

    # THE FROZEN DESCENDED MATRIX, ENTRY FOR ENTRY.
    descended = descend(channel, coarse)
    if descended is not None:
        for column, rows in case.descended_matrix:
            for letter, value in rows:
                assert descended.value(letter, column) == value, (column, letter)

    if case.reason:
        emitted = refusal or rule_descent(channel, coarse)
        assert emitted is not None
        assert str(emitted.reason) == case.reason
    else:
        assert refusal is None
        assert rule_descent(channel, coarse) is None


def row(outcome: ReductionOutcome, rule: FailClosedRule) -> Any:
    """Return one row's outcome out of the verification report."""
    return next(
        entry for entry in outcome.verification_report.outcomes if entry.rule is rule
    )


# ---------------------------------------------------------------------------
#  1. The row's two predicates, on the declared matrix, case by case
# ---------------------------------------------------------------------------


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("case", COLSTOCH_CASES, ids=lambda c: c.case_id)
def test_the_code_decides_every_frozen_case_as_the_freeze_does(case: Any) -> None:
    """Both subrules, both dark-count rows, and every frozen scalar beside them.

    The freeze carries ``min_entry``, ``column_sums``, ``non_negative``,
    ``unit_columns``, ``monotone``, ``descends`` and the two ``*_row_admits``
    flags per case. Every one is recomputed here from the declared matrix, so a
    single wrong comparison in the rule cannot be masked by a compensating one.
    """
    channel = channel_of(case)
    coarse = coarse_of(case)

    # The two subrules, separately, so a conjunction cannot hide a half.
    assert smallest_declared_entry(channel) == case.min_entry
    assert (smallest_declared_entry(channel) >= 0) is case.non_negative
    sums = declared_column_sums(channel)
    assert {
        "".join(sorted(str(k) for k in sorted(column))) or "e": total
        for column, total in sums.items()
    } == dict(case.column_sums)
    assert all(total == 1 for total in sums.values()) is case.unit_columns

    # The row is the CONJUNCTION of the two, and nothing else.
    assert is_column_stochastic(channel) is case.column_stochastic_row_admits
    refusal = rule_column_stochastic(channel)
    assert (refusal is None) is case.column_stochastic_row_admits

    # The row beside it, on the SAME declaration.
    assert is_monotone(channel) is case.monotone
    assert (descend(channel, coarse) is not None) is case.descends
    assert (rule_descent(channel, coarse) is None) is case.descent_row_admits

    # And the reason string, when one of the two refuses.
    if case.reason:
        emitted = refusal or rule_descent(channel, coarse)
        assert emitted is not None
        assert str(emitted.reason) == case.reason
        assert emitted.detail
        assert emitted.as_machine_record()["reason"] == case.reason
    else:
        assert refusal is None
        assert rule_descent(channel, coarse) is None


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize("case", COLSTOCH_CASES, ids=lambda c: c.case_id)
def test_deciding_on_r_discharges_the_descended_matrix(case: Any) -> None:
    """Remark ``rem:colstoch``: no second row is stated on ``R^cg``, and none is.

    The implication is checked rather than asserted: where the declared matrix is
    column-stochastic the descended one is too, and where the declared one has a
    column defect the defect TRAVELS. ``CS-coarse-admit`` makes the first
    direction non-trivial -- its ``cg`` has a fibre of size two, so a descended
    entry is a genuine sum rather than a relabelling.
    """
    channel = channel_of(case)
    descended = descend(channel, coarse_of(case))
    if descended is None:
        # Only a descent failure can produce this, and no frozen case has one.
        assert not case.descends
        return
    assert descended.is_column_stochastic() is case.descended_is_column_stochastic
    if is_column_stochastic(channel):
        assert descended.is_column_stochastic(), (
            "the fibres of cg partition 2^[K], so column-stochasticity of the "
            "declared R implies it of R^cg (rem:colstoch)"
        )
    # THE FROZEN DESCENDED MATRIX, ENTRY FOR ENTRY.
    for column, rows in case.descended_matrix:
        for letter, value in rows:
            assert descended.value(letter, column) == value, (column, letter)


@pytest.mark.contract
@pytest.mark.oracle
def test_a_fibre_of_size_two_makes_the_descended_entry_a_genuine_sum() -> None:
    """``CS-coarse-admit``: the descended entry ADDS two entries of ``R``.

    Under the canonical coarse-graining ``cg`` is a bijection and the "sum over
    the fibre" has one term. Here ``cg^{-1}(y_d) = {{1}, {2}}``, so
    ``R^cg_{y_d|e} = R_{1|e} + R_{2|e}`` -- and the unit column of ``R^cg`` is
    formed BY THAT ADDITION, which is what makes the implication of Remark
    ``rem:colstoch`` non-trivial rather than a relabelling.
    """
    case = COLSTOCH_COARSE_ADMIT
    channel = channel_of(case)
    coarse = coarse_of(case)
    fibre = coarse.fibre("y_d")
    assert len(fibre) == 2
    descended = descend(channel, coarse)
    assert descended is not None
    empty = frozenset()
    assert (
        descended.value("y_d", "y_0")
        == sum((channel.value(target, empty) for target in fibre), start=F(0))
        == F(8, 25)
    )
    # And that column of R^cg sums to one WITH the added term in it.
    assert (
        descended.value("y_0", "y_0")
        + descended.value("y_d", "y_0")
        + descended.value("y_mc", "y_0")
        == 1
    )


# ---------------------------------------------------------------------------
#  2. The boundary: the two rows do not cover each other, IN THE CODE
# ---------------------------------------------------------------------------


@pytest.mark.contract
@pytest.mark.oracle
def test_the_two_dark_count_rows_do_not_cover_each_other() -> None:
    """Remark ``rem:darkcompose``, both halves, decided by the rules themselves.

    THE PAIR IS THE POINT. Both declarations put an entry at the SAME
    (D2)-forbidden position ``(e | {1})`` and differ only in its SIGN, and each
    is refused by exactly one of the two rows under its own reason string. An
    implementation that folded them into one test would emit the wrong string
    for one of these two, and one that tested monotonicity with ``!= 0`` instead
    of the contract's ``> 0`` would refuse the first under BOTH.
    """
    negative = channel_of(COLSTOCH_NEGATIVE_VACUOUS_REFUSE)
    positive = channel_of(COLSTOCH_POSITIVE_FORBIDDEN_REFUSE)
    negative_cg = coarse_of(COLSTOCH_NEGATIVE_VACUOUS_REFUSE)
    positive_cg = coarse_of(COLSTOCH_POSITIVE_FORBIDDEN_REFUSE)
    forbidden = (frozenset(), frozenset({1}))
    assert negative.entries[forbidden] == F(-1, 20)
    assert positive.entries[forbidden] == F(1, 20)

    # HALF ONE: a NEGATIVE entry there satisfies monotonicity VACUOUSLY.
    assert is_monotone(negative) is True
    assert rule_descent(negative, negative_cg) is None
    refusal = rule_column_stochastic(negative)
    assert refusal is not None
    assert refusal.reason is RefusalReason.DARK_COUNTS_NOT_COLUMN_STOCHASTIC
    # And it fails ONLY on non-negativity: every column still sums to one.
    assert all(total == 1 for total in declared_column_sums(negative).values())

    # HALF TWO: a STRICTLY POSITIVE entry there leaves the new row untouched.
    assert rule_column_stochastic(positive) is None
    assert is_monotone(positive) is False
    descent = rule_descent(positive, positive_cg)
    assert descent is not None
    assert descent.reason is RefusalReason.DARK_COUNTS_DO_NOT_DESCEND
    # ...and it is the MONOTONICITY half that failed, not the descent half.
    assert descend(positive, positive_cg) is not None

    # The two reasons are DIFFERENT STRINGS and both are in the vocabulary.
    assert refusal.reason != descent.reason
    assert {str(refusal.reason), str(descent.reason)} <= set(REFUSAL_REASONS_0_3_0)


@pytest.mark.contract
@pytest.mark.oracle
def test_the_boundary_pair_is_refused_end_to_end_under_its_own_reason() -> None:
    """The same pair through :func:`reduce`, which is what a caller sees.

    The report's refusal is the FIRST in the contract's row order, and the
    column-stochasticity row precedes the descent row there, so a declaration
    failing both would report the former. Neither of these fails both -- that is
    what the case above establishes -- so each reports its own row's string, and
    NO ARTIFACT is emitted in either case.

    THE CASES ARE BAND 5'S DYADIC TWINS, PRR-7d AND PRR-7e, because this test
    reaches :func:`reduce` and that path decides ``eq:latinv`` on every declared
    scalar. The pair is the same pair -- one entry at the SAME (D2)-forbidden
    position, differing only in its SIGN -- and the two reasons are the same two.
    The 0.3.0 twins keep their coverage in the subrule tests above, which do not
    call :func:`reduce`.
    """
    negative = outcome_of_pr_r(_pr_r("PRR-7d-cs-negative-vacuous-refuse"))
    assert negative.artifact is None
    assert negative.refusal is not None
    assert str(negative.refusal.reason) == "dark_counts_not_column_stochastic"
    assert negative.refusal.rule == str(WpfssRule.COLUMN_STOCHASTIC)
    assert row(negative, WpfssRule.COLUMN_STOCHASTIC).passed is False
    assert row(negative, WpfssRule.DESCENT).passed is True

    positive = outcome_of_pr_r(_pr_r("PRR-7e-cs-positive-forbidden-refuse"))
    assert positive.artifact is None
    assert positive.refusal is not None
    assert str(positive.refusal.reason) == "dark_counts_do_not_descend"
    assert positive.refusal.rule == str(WpfssRule.DESCENT)
    assert row(positive, WpfssRule.COLUMN_STOCHASTIC).passed is True
    assert row(positive, WpfssRule.DESCENT).passed is False


# ---------------------------------------------------------------------------
#  3. Reachability: the residue the row exists for, refused end to end
# ---------------------------------------------------------------------------


@pytest.mark.contract
@pytest.mark.oracle
def test_a_residue_defect_only_the_column_stochasticity_row_refuses() -> None:
    """THE CASE THE ROW WAS WRITTEN FOR: a declaration only this row refuses.

    Remark ``rem:colstoch`` names the two indirect paths by which a column-sum
    defect already refused -- through ``total_weight_not_below_one`` where the
    defect lifts some ``r_min,i`` to one, and through the tolerance row's
    completeness budget -- and then: "A DEFECT OUTSIDE THOSE TWO ... MET NO ROW
    AT ALL, though [``sec:inputs``] had already declared it invalid."

    ONE RUN. A second run would need a declared operator tolerance, and there
    is none (``SCOPE_MARKS_1_0_0``): no row of 1.0.1 is decided at one. What
    the single run establishes is that every other row admits this
    declaration, so the column-stochasticity row is the only thing between it
    and an emitted artifact.

    THE DEFECT IS DYADIC TOO, and deliberately: PRR-7c lowers one entry by
    exactly ``1/128`` where the frozen 0.3.0 case uses ``1/100``. A defect that was
    itself off the lattice would be refused by a DIFFERENT row and the case
    would stop testing what it exists to test.
    """
    case = _pr_r("PRR-7c-cs-colsum-refuse")
    outcome = outcome_of_pr_r(case)

    # NO ARTIFACT, and the reason is the row's own.
    assert outcome.artifact is None
    assert outcome.refusal is not None
    assert str(outcome.refusal.reason) == "dark_counts_not_column_stochastic"
    assert outcome.refusal.reason.value in REFUSAL_REASONS_ADDED_0_3_0

    # EVERY OTHER ROW THAT LOOKS AT THIS DECLARATION ADMITS IT, which is the
    # attributability the freeze's own derivation enumerates.
    for rule in (
        FailClosedRule.LATTICE_EXPONENT,
        WpfssRule.FIBRE,
        WpfssRule.DESCENT,
        WpfssRule.ABSORBING,
        WpfssRule.HIGH_PHOTON_SLOT,
        FailClosedRule.PROBE_WEIGHTS,
        WpfssRule.TOTAL_WEIGHT,
    ):
        assert row(outcome, rule).passed is True, rule
    assert row(outcome, WpfssRule.COLUMN_STOCHASTIC).passed is False

    # The frozen scalars behind the total-weight admission: column `e` sums to
    # 127/128, the matrix is monotone, descends and is absorbing, and the total
    # weight admits.
    assert dict(case.column_sums)["e"] == F(127, 128)
    assert case.monotone and case.descends and case.absorbing
    assert case.total_weight_row_admits is True
    descended = descend(channel_of(case), coarse_of(case))
    assert descended is not None
    assert minimum_off_letter_rate(descended, case.bounded_letter) == case.r_min
    routed = (1 - case.r_min) * CS_SLOT_WEIGHT_PR_R + case.r_min
    assert routed == case.routed_total_hat
    assert rule_total_weight([q * routed for _, q in CS_PROBE_WEIGHTS_PR_R]) is None


# ---------------------------------------------------------------------------
#  3b. RETIRED: the tolerance-invariance test, whose subject left the contract
# ---------------------------------------------------------------------------
#
#  There is no test that the row decides identically at every declared
#  tolerance. Its subject would be ``COLSTOCH_TOLERANCE_PROBE``, the declared
#  operator tolerance, and that datum is not in the contract:
#  ``operator_tolerance`` is not an input key, ``declaration_outside_tolerance``
#  is not a refusal reason, and there is no tolerance row.
#  ``SCOPE_MARKS_1_0_0`` marks the whole apparatus ``superseded-by-scope``.
#
#  NO SUCCESSOR IS INVENTED. ``kappa`` is not a tolerance and
#  the ``lattice_exponent`` row says so in terms -- "IT IS NOT A TOLERANCE,
#  NOTHING IS ADMITTED OR REFUSED WITHIN ``kappa``" -- and at a coarser ``kappa``
#  the declared entries leave the lattice, so a "kappa analogue" of this test
#  would be a DIFFERENT row firing and not this row deciding identically.


# ---------------------------------------------------------------------------
#  4. Regression: the anchors are admitted, with the frozen numbers
# ---------------------------------------------------------------------------


@pytest.mark.contract
@pytest.mark.oracle
@pytest.mark.parametrize(
    "case",
    (
        _pr_r("PRR-7a-cs-canonical-admit"),
        _pr_r("PRR-7b-cs-coarse-admit"),
    ),
    ids=lambda c: c.case_id,
)
def test_an_honest_declaration_is_still_admitted_with_the_same_numbers(
    case: Any,
) -> None:
    """EACH AMENDMENT REFUSES STRICTLY MORE AND NEVER LESS: no conforming case moves.

    "The condition was already required, so a declaration OF THE DECLARED TYPE is
    admitted exactly as before and NONE THAT WAS REFUSED IS NOW ADMITTED."
    Both anchors emit and every row that looks at ``R`` passes.

    THE NUMBERS ARE THE DYADIC ONES, AND THE EMITTED WEIGHT IS THE ROUNDED
    ONE. That is asserted in both forms: the routed ``p^`` of Eq. ``eq:weightroute``
    AND,
    beside it, the emitted ``p = lat(p^)`` of Eq. ``eq:latdown``, which "ONLY
    LOWERS". At PRR-7a the two differ -- ``p^ = 279/2048`` against the emitted
    ``187/2048`` and ``183/4096`` -- and asserting only one of them would let
    the other move unnoticed.
    """
    outcome = outcome_of_pr_r(case)
    assert outcome.refusal is None, outcome.refusal
    artifact = outcome.artifact
    assert artifact is not None
    assert artifact.mathematical_spec_version == MATHEMATICAL_SPEC_VERSION

    for rule in (
        WpfssRule.COLUMN_STOCHASTIC,
        WpfssRule.DESCENT,
        WpfssRule.FIBRE,
        WpfssRule.ABSORBING,
        WpfssRule.TOTAL_WEIGHT,
    ):
        assert row(outcome, rule).passed is True, rule

    descended = descend(channel_of(case), coarse_of(case))
    assert descended is not None
    assert descended.is_absorbing_at(case.bounded_letter) is case.absorbing
    assert minimum_off_letter_rate(descended, case.bounded_letter) == case.r_min
    # Eq. eq:weightroute BEFORE the rounding.
    routed = (1 - case.r_min) * CS_SLOT_WEIGHT_PR_R + case.r_min
    assert routed == case.routed_total_hat
    # Eq. eq:latdown AFTER it: the EMITTED weights, per setting, frozen.
    emitted = dict(
        zip(artifact.wpfss_data.flag_basis, artifact.wpfss_data.weights, strict=True)
    )
    for setting, expected in case.emitted_weights:
        assert emitted[(case.bounded_letter, setting)] == expected
        # lat() ONLY LOWERS, and here it strictly does.
        q_t = dict(CS_PROBE_WEIGHTS_PR_R)[setting]
        assert expected <= q_t * routed
    assert artifact.wpfss_data.total == case.emitted_total
    assert sum(emitted.values(), start=F(0)) == case.emitted_total
    # And no lift fires anywhere in this group: every block is 1 x 1 and real.
    assert case.lift_fires is False
    # The uniform lift is only def:emitnorm's flagged last resort (U3), read
    # off the per-class record.
    for record in artifact.emission_record.blocks:
        assert all(str(snap.step) != "U3" for snap in record.classes.values())


@pytest.mark.contract
@pytest.mark.oracle
def test_the_anchor_is_the_band_one_declaration_read_one_level_lower() -> None:
    """``PRR-7a`` is ``PRR-1``'s ``R``: the regression is a real one.

    The anchor is band 5's end-to-end declaration READ ONE LEVEL LOWER, exactly
    as ``CS-canonical-admit`` was band 1's ``RC2`` read one level lower. The
    raw/descended agreement still holds for the contract's own reason: ``cg`` is
    a BIJECTION off the multiclick letter, so ``R^cg = R`` entry for entry, and
    a defect in one is a defect in the other. If a number moved, this is where
    it would show -- the two frozen cases are derived independently and must
    agree.
    """
    case = _pr_r("PRR-7a-cs-canonical-admit")
    assert dict(PR_R1.slot_weights)["y_mc"] == CS_SLOT_WEIGHT_PR_R
    assert PR_R1.probe_weights == CS_PROBE_WEIGHTS_PR_R
    assert (
        case.r_min
        == {letter: r_min for letter, _, r_min in PR_R1.bounded_letters}["y_mc"]
    )
    # THE TWO FREEZES AGREE ON EVERY ENTRY, under the canonical `cg`. PRR-7a
    # indexes its RAW matrix by click pattern and PRR-1 its DESCENDED one by
    # letter; `cg` is a BIJECTION here, so "read one level lower" is exactly the
    # relabelling below and the numbers must be identical on both sides.
    relabel = dict(case.coarse_graining)
    lowered = tuple(
        (relabel[column], tuple((relabel[target], value) for target, value in rows))
        for column, rows in case.raw_matrix
    )
    assert lowered == PR_R1.descended_matrix
    # And the descended matrix of PRR-7a is that same matrix: `cg` being a
    # bijection off MC, the descent is a relabelling and adds nothing.
    assert case.descended_matrix == PR_R1.descended_matrix
    assert case.declared_blocks == PR_R1.declared_blocks
    # ...and on the emitted weights, which is the number a consumer reads.
    assert case.emitted_weights == tuple(
        (setting, weight) for (_, setting), weight in PR_R1.emitted_weights
    )
    outcome = outcome_of_pr_r(case)
    artifact = outcome.artifact
    assert artifact is not None
    weights = dict(
        zip(artifact.wpfss_data.flag_basis, artifact.wpfss_data.weights, strict=True)
    )
    for setting, expected in case.emitted_weights:
        assert weights[("y_mc", setting)] == expected
    assert artifact.wpfss_data.total == case.emitted_total
    # Away from the bounded letter every weight is zero (Eq. eq:weightroute).
    assert all(value == 0 for (letter, _), value in weights.items() if letter != "y_mc")


# ---------------------------------------------------------------------------
#  5. The counts, and that nothing else moved
# ---------------------------------------------------------------------------


@pytest.mark.contract
@pytest.mark.oracle
def test_the_one_row_and_one_string_the_amendment_adds() -> None:
    """Rows 24 -> 25, reasons 26 -> 27, NONE REMOVED, and the position is fixed.

    The 0.2.0 vocabulary is a prefix-preserving subsequence of the 0.3.0 one --
    the frozen tuple is built BY INSERTION for exactly that reason -- so a
    consumer switching on a refusal reason sees one more case and no renames.
    """
    # THE ROW INVENTORY IS 1.0.0'S AND IS BAND 4'S TO FREEZE, NOT THIS FILE'S:
    # 25 rows and 27 strings at 0.3.0, 28 and 30 at 1.0.0. What this file
    # asserts is the COLUMN-STOCHASTICITY HALF, which 1.0.0 leaves untouched.
    # TWENTY-ONE CORE ROWS; the six weight-route rows are ``wpfss``'s and the
    # branching model's row is a removable submodule's, so the frozen
    # twenty-eight is the union of the three.
    assert len(RULE_ORDER) + len(WPFSS_ROWS) + 1 == FAIL_CLOSED_ROW_COUNT_1_0_0 == 28
    assert FAIL_CLOSED_ROW_COUNT_0_3_0 == 25
    # COMPARED AS A SET AND NOT AS A TUPLE, under the dated note beside the
    # frozen entry: `REFUSAL_REASONS_1_0_0` appends the emitted-family string
    # LAST where sec:failclosed prints that row SEVENTH, so the two agree on all
    # thirty strings and diverge in order. The divergence is RECORDED, not
    # fixed here -- correcting a frozen value is done under a mark of its own
    # -- and the CONTRACT'S order is asserted against the enum below.
    # TWENTY-NINE IN THE CORE ENUM, WITH ONE RENAMED. The thirtieth is the
    # removable submodule's own string; ``requested_assurance_shelved`` is
    # ``requested_assurance_unknown`` here.
    # AND ONE ADDED SINCE THE FREEZE, wpfss's normalized_receiver_in_branch
    # (wpfss/req:normalized-branch-refusal).
    added = {"normalized_receiver_in_branch"}
    emitted = {str(reason) for reason in RefusalReason}
    assert emitted == (
        set(REFUSAL_REASONS_1_0_0)
        - {"blinding_model_ill_formed", "requested_assurance_shelved"}
    ) | {"requested_assurance_unknown"} | added
    assert len(REFUSAL_REASONS_1_0_0) == len(RefusalReason) + 1 - len(added) == 30
    assert "emitted_family_not_admissible" in REFUSAL_REASONS_1_0_0_ORDER_NOTE
    assert REFUSAL_REASONS_ADDED_0_3_0 == ("dark_counts_not_column_stochastic",)
    # The 0.3.0 string survives 1.0.0 unrenamed, which is what makes the
    # position assertions below still meaningful.
    assert "dark_counts_not_column_stochastic" in REFUSAL_REASONS_1_0_0
    assert dict(FAIL_CLOSED_ROWS_ADDED_0_3_0) == {
        "the column-stochasticity row": "dark_counts_not_column_stochastic"
    }
    # THE POSITION: between the fibre row and the descent row, which is what
    # decides the reason on a declaration that fails both.
    order = [row.rule for row in WPFSS_ROWS]
    assert (
        order.index(WpfssRule.FIBRE)
        < order.index(WpfssRule.COLUMN_STOCHASTIC)
        < order.index(WpfssRule.DESCENT)
    )
    # ...IN THE ENUM, which carries the contract's own row order.
    reasons = [str(reason) for reason in RefusalReason]
    assert (
        reasons.index("bound_set_not_a_fibre")
        < reasons.index("dark_counts_not_column_stochastic")
        < reasons.index("dark_counts_do_not_descend")
    )


@pytest.mark.contract
@pytest.mark.oracle
def test_no_second_row_is_stated_on_the_descended_matrix() -> None:
    """No second row is stated on the descended matrix, and none exists here.

    The scan is on the row vocabulary rather than on prose: exactly ONE row of
    Section ``sec:failclosed`` carries the new reason, and the predicate on
    ``R^cg`` is not wired to any row at all. An implementation that added one
    would need a twenty-eighth reason string, which the contract does not name.
    """
    from certiqs_key.reductions.reasons import fail_closed_rules

    carriers = [
        rule
        for rule, reasons in fail_closed_rules().items()
        if RefusalReason.DARK_COUNTS_NOT_COLUMN_STOCHASTIC in reasons
    ]
    assert carriers == [WpfssRule.COLUMN_STOCHASTIC]
    assert fail_closed_rules()[WpfssRule.COLUMN_STOCHASTIC] == (
        RefusalReason.DARK_COUNTS_NOT_COLUMN_STOCHASTIC,
    )
    # The declared-matrix predicate is what the rule reads; the descended one is
    # an expression of the implication and is read by no rule.
    case = COLSTOCH_COLSUM_REFUSE
    descended = descend(channel_of(case), coarse_of(case))
    assert descended is not None
    assert descended.is_column_stochastic() is False
    # ...and the refusal is still attributed to the DECLARED matrix.
    refusal = rule_column_stochastic(channel_of(case))
    assert refusal is not None
    assert "column" in refusal.detail


@pytest.mark.contract
@pytest.mark.oracle
def test_the_frozen_cases_are_all_exercised_here() -> None:
    """No frozen case is skipped, and the group is the five the freeze names."""
    assert len(COLSTOCH_CASES) == 5
    ids = {case.case_id for case in COLSTOCH_CASES}
    assert ids == {
        "CS-canonical-admit",
        "CS-coarse-admit",
        "CS-colsum-refuse",
        "CS-negative-vacuous-refuse",
        "CS-positive-forbidden-refuse",
    }
    admitted = [case for case in COLSTOCH_CASES if not case.reason]
    refused = [case for case in COLSTOCH_CASES if case.reason]
    assert len(admitted) == 2
    assert len(refused) == 3
    # Every refused case names a reason IN the 0.3.0 vocabulary, and the two
    # dark-count rows are the only ones the group reaches.
    assert {case.reason for case in refused} == {
        "dark_counts_not_column_stochastic",
        "dark_counts_do_not_descend",
    }
    # And the slot the whole group shares is well formed, so no case is refused
    # for a reason the group is not about.
    assert (
        rule_high_photon_slot(
            (
                HighPhotonBound.uniform(
                    frozenset({frozenset({1, 2})}),
                    COLSTOCH_SLOT_WEIGHT,
                    tuple(setting for setting, _ in COLSTOCH_PROBE_WEIGHTS),
                ),
            ),
            tuple(setting for setting, _ in COLSTOCH_PROBE_WEIGHTS),
            ACCEPTED[0],
        )
        is None
    )
    assert rule_fibre((), coarse_of(COLSTOCH_CANONICAL_ADMIT)) is None
    assert rule_absorbing(()) is None

    # BAND 5'S DYADIC TWINS ARE EXERCISED TOO, and they are the same five
    # declarations: two admitted, three refused, under the same two strings.
    assert len(CS_CASES_PR_R) == 5
    dyadic_admitted = [case for case in CS_CASES_PR_R if not case.reason]
    dyadic_refused = [case for case in CS_CASES_PR_R if case.reason]
    assert len(dyadic_admitted) == 2
    assert len(dyadic_refused) == 3
    assert {case.reason for case in dyadic_refused} == {
        "dark_counts_not_column_stochastic",
        "dark_counts_do_not_descend",
    }
    # And every one of them is on the declared lattice, which is exactly what
    # the 0.3.0 twins are not and what the row itself does not read.
    assert all(case.all_entries_on_lattice for case in CS_CASES_PR_R)
    # The tolerance apparatus is marked as superseded.
    assert any("TOLERANCE" in mark[0].upper() for mark in SCOPE_MARKS_1_0_0)
    assert (F(0), F(1, 100)) == COLSTOCH_TOLERANCE_PROBE

