"""The STRUCTURAL fail-closed properties of ``proof-reductions``.

Section 2.5, ``fail_closed``, states four of them in one sentence -- "NO DEFAULT
IS SUBSTITUTED FOR A MISSING DATUM, NO WEIGHT IS CLIPPED INTO RANGE, NO FIBRE
CONDITION IS WAIVED, AND NO LICENCE IS EMITTED WITHOUT ITS CERTIFICATE" -- and
adds a fifth: "every failed validation produces a refusal with a machine-readable
reason and NO ARTIFACT", which is the statement that a refusal is a RECORD and
never an exception.

The sixth property is architectural rather than mathematical: importing this
module imports no consumer, no array library and no shared wire format
(PRINCIPLES.md section 4). It is checked on the IMPORT GRAPH
in a fresh interpreter, not on the text.
"""

from __future__ import annotations

import ast
import inspect
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

import pytest

from certiqs_key.foundations.exact import (
    Cx,
    diagonal,
    direct_sum,
    equal,
    identity,
    is_positive_semidefinite,
    matrix,
    scale,
    subtract,
)
from certiqs_key.reductions import Refusal, RefusalReason
from certiqs_key.reductions.constraints import (
    ConstraintEntry,
    certificate_holds,
    issue_licence,
)
from certiqs_key.reductions.errors import HypothesisError, MalformedInputError
from certiqs_key.reductions.inputs import (
    BoundQuantifierDomain,
    ChannelGrading,
    CoarseGraining,
    DarkCountChannel,
    HighPhotonBound,
    InheritedAssumption,
    ProbeDeclaration,
    ReceiverArtifactRows,
    canonical_coarse_graining,
    patterns,
    product_form_dark_counts,
)
from certiqs_key.reductions.reasons import (
    ASSUMED_FROM_THE_TRANSMITTER,
    CORE_FAIL_CLOSED_ROWS,
    LINK_KINDS_DEFERRED,
    LINK_KINDS_IMPLEMENTED,
    LINK_STATUS_EMITTED,
    NEVER_VERIFIED,
    AssumptionId,
    CertificateKind,
    FailClosedRule,
    LinkKind,
    LinkStatus,
    Relation,
    Route,
    SourceMode,
)
from certiqs_key.reductions.reasons import (
    CORE_REFUSAL_REASONS as REFUSAL_REASONS,
)
from certiqs_key.reductions.validation import (
    RULE_ORDER,
    RuleOutcome,
    rule_licence_presence,
    rule_probe_weights,
)
from certiqs_key.reductions.wpfss.construction import (
    fss_target,
    mprime_family,
    transported_cutoff_projectors,
    wp_adjoint,
    wpfss_target,
)
from certiqs_key.reductions.wpfss.validation import (
    WPFSS_ROWS,
    rule_absorbing,
    rule_column_stochastic,
    rule_fibre,
    rule_total_weight,
)
from certiqs_key.reductions.wpfss.validation import (
    FailClosedRule as WpfssRule,
)
from certiqs_key.reductions.wpfss.weights import (
    bounded_letters,
    declared_column_sums,
    descend,
    is_column_stochastic,
    is_monotone,
    smallest_declared_entry,
    weight_route,
)

F = Fraction
PACKAGE = Path(__file__).resolve().parents[2] / "src" / "certiqs_key" / "reductions"


# ---------------------------------------------------------------------------
#  1. No default is substituted for a missing datum
# ---------------------------------------------------------------------------


def test_no_default_is_substituted_for_a_missing_datum() -> None:
    """A missing declaration is a refusal or an error, never a filled-in value."""
    # A probe declaration whose weights do not cover the declared settings.
    incomplete = ProbeDeclaration(settings=("t0", "t1"), weights={"t0": F(1)})
    refusal = rule_probe_weights(incomplete)
    assert refusal is not None
    assert refusal.reason is RefusalReason.PROBE_WEIGHTS_ILL_FORMED
    # A coarse-graining that is not total: the pattern is not silently dropped.
    partial = CoarseGraining(
        ports=2,
        letters=("y",),
        assignment={frozenset(): "y"},
    )
    with pytest.raises(MalformedInputError):
        partial.image(frozenset({1}))
    # A carried operator with no computed pull-back gets no default certificate.
    from certiqs_key.reductions.validation import (
        rule_constraint_certificate,
    )

    entry = ConstraintEntry(
        label="unbacked",
        operator=identity(3),
        relation=Relation.GE,
        constant=F(0),
        certificate_kind=CertificateKind.POSITIVITY,
        certified_against="Lambda",
        theta_typing="Theta = c = 0",
    )
    missing = rule_constraint_certificate([entry], {})
    assert missing is not None
    assert missing.reason is RefusalReason.CONSTRAINT_WITHOUT_CERTIFICATE


def _receiver_ledger_keys() -> tuple[str, ...]:
    """Return the receiver's own machine keys, in the receiver's order.

    Read from the SUPPLIER'S vocabulary, as the code under test reads it; the
    oracle ``RECEIVER_LEDGER_KEYS`` (tests/support) pins the same ten independently in
    the golden emission tests.
    """
    from certiqs_key.receiver.reasons import ASSUMPTION_MACHINE_KEYS

    return tuple(ASSUMPTION_MACHINE_KEYS.values())


def test_an_inherited_key_the_artifact_does_not_carry_is_a_refusal() -> None:
    """``ass:recv``: a shortened list is refused.

    "A key the artifact does not carry is a REFUSAL
    (``receiver_spec_not_accepted``) RATHER THAN A SILENTLY SHORTENED LIST." The
    row that decides it is the receiver-spec row, which is where the contract
    puts the reason string; no twenty-ninth row and no thirty-first string is
    invented for it, exactly as the same row already carries the consistency
    re-check of Section 4.14's closing paragraph.

    EVERY REQUIRED KEY, ONE AT A TIME. The refusal is asserted for every key
    the receiver's own presence rules make present, rather than for one,
    because a check written against a hardcoded list would pass for the key it
    names and admit the others.
    """
    from certiqs_key.reductions.validation import (
        required_receiver_keys,
        rule_receiver_spec,
    )

    # The receiver's rules make every one of its keys present, in its own
    # order, on every artifact.
    assert required_receiver_keys() == _receiver_ledger_keys()

    # The accepted supplier version this fixture declares is the receiver's
    # accepted one, which states the per-setting weights the wpfss slot row
    # requires of every artifact (req:supplier-version). Fixture data.
    accepted = ("receiver@0.9.0",)
    full = tuple(
        InheritedAssumption(machine_key=key) for key in _receiver_ledger_keys()
    )
    complete = _receiver_rows(inherited_assumption_ledger=full)
    assert rule_receiver_spec(complete, accepted) is None

    for dropped in required_receiver_keys():
        rows = _receiver_rows(
            inherited_assumption_ledger=tuple(
                row for row in full if row.machine_key != dropped
            )
        )
        refusal = rule_receiver_spec(rows, accepted)
        assert refusal is not None, dropped
        assert refusal.reason is RefusalReason.RECEIVER_SPEC_NOT_ACCEPTED
        # The refusal NAMES the missing key: a caller must be able to tell which
        # of the receiver's keys its supplier did not emit.
        assert dropped in refusal.detail

    # An EMPTY ledger is refused too, and is not read as "nothing to check".
    empty = _receiver_rows(inherited_assumption_ledger=())
    refusal = rule_receiver_spec(empty, accepted)
    assert refusal is not None
    assert refusal.reason is RefusalReason.RECEIVER_SPEC_NOT_ACCEPTED


def test_every_key_is_required_whether_or_not_the_supplier_declares_a_probe() -> (
    None
):
    """The receiver's presence rule: every row on every artifact.

    There is no conditional receiver row (the probe-diagonal condition is
    ``receiver/def:probe``, decided by ``req:probe-diagonal-admission``), so a
    probe-free supplier's ledger is required to carry every key exactly as a
    probe-declaring supplier's is (``wpfss/rem:receiver-imports``: "the
    supplier's rules omit no key").
    """
    from certiqs_key.reductions.artifact import assumption_ledger
    from certiqs_key.reductions.validation import (
        required_receiver_keys,
        rule_receiver_spec,
    )

    accepted = ("receiver@0.9.0",)
    full = tuple(
        InheritedAssumption(machine_key=key) for key in required_receiver_keys()
    )
    letters = _receiver_rows().detection_alphabet

    def probe_free(ledger: tuple[InheritedAssumption, ...]) -> ReceiverArtifactRows:
        return _receiver_rows(
            photon_blocks={
                (letter, "off"): (matrix([[F(1, 4)]]),) for letter in letters
            },
            bound_quantifier_domain=BoundQuantifierDomain(cutoff=0, settings=("off",)),
            inherited_assumption_ledger=ledger,
        )

    assert rule_receiver_spec(probe_free(full), accepted) is None
    ledger = assumption_ledger({}, "receiver@0.9.0", full)
    recv = next(entry for entry in ledger if entry.assumption_id == "A-RECV")
    assert recv.inherited == required_receiver_keys()

    for dropped in required_receiver_keys():
        shortened = tuple(row for row in full if row.machine_key != dropped)
        refusal = rule_receiver_spec(probe_free(shortened), accepted)
        assert refusal is not None, dropped
        assert refusal.reason is RefusalReason.RECEIVER_SPEC_NOT_ACCEPTED
        assert dropped in refusal.detail


def test_a_supplier_key_this_module_never_named_is_passed_through() -> None:
    """The supplier's ledger is passed through.

    The A-RECV entry carries the supplied ledger AS IT STANDS AND IN ITS
    ORDER. Filtering the supplier's rows through a list held here would DROP
    SILENTLY a key the receiver gained and nobody re-transcribed -- the unsafe
    direction, an emitted ledger that understates what the artifact rests on. A
    key this module has never heard of is carried, at the place the supplier put it, and
    admitted: the receiver-spec row refuses a MISSING key, never an extra one.
    """
    from certiqs_key.reductions.artifact import assumption_ledger
    from certiqs_key.reductions.validation import rule_receiver_spec

    new_key = "a_key_the_receiver_gained_later"
    keys = _receiver_ledger_keys()
    supplied_keys = (*keys[:3], new_key, *keys[3:])
    supplied = tuple(InheritedAssumption(machine_key=key) for key in supplied_keys)

    rows = _receiver_rows(inherited_assumption_ledger=supplied)
    assert rule_receiver_spec(rows, ("receiver@0.9.0",)) is None

    ledger = assumption_ledger({}, "receiver@0.9.0", supplied)
    recv = next(entry for entry in ledger if entry.assumption_id == "A-RECV")
    assert recv.inherited == supplied_keys
    assert recv.inherited_from == "receiver@0.9.0"
    # And on no other entry.
    assert all(entry.inherited == () for entry in ledger if entry is not recv)


def test_a_supplied_ledger_that_repeats_a_key_is_refused() -> None:
    """A repeated machine key is refused, and the refusal names it.

    The ledger is passed through as supplied, so a repeated key would ride the
    A-RECV entry twice, and of two differing A-EIG records one would be kept
    and the other dropped silently. The receiver-spec row refuses the ledger
    instead, as a well-formedness check under its EXISTING reason string.
    """
    from certiqs_key.reductions.validation import rule_receiver_spec

    eig = "exact_window_eigenvalue_slack"
    supplied = (
        *(InheritedAssumption(machine_key=key) for key in _receiver_ledger_keys()),
        InheritedAssumption(machine_key=eig, constrains=(("eps_eig", "1e-12"),)),
    )
    # The base ledger already carries the key once; give that row a record too,
    # so the two records differ.
    supplied = tuple(
        InheritedAssumption(machine_key=eig, constrains=(("eps_eig", "1e-9"),))
        if index < len(supplied) - 1 and row.machine_key == eig
        else row
        for index, row in enumerate(supplied)
    )
    assert [row.machine_key for row in supplied].count(eig) == 2

    refusal = rule_receiver_spec(
        _receiver_rows(inherited_assumption_ledger=supplied), ("receiver@0.9.0",)
    )
    assert refusal is not None
    assert refusal.reason is RefusalReason.RECEIVER_SPEC_NOT_ACCEPTED
    assert eig in refusal.detail
    assert "repeat" in refusal.detail


def test_the_required_keys_are_the_receiver_s_own_rule_not_a_copy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The receiver-spec row reads the RECEIVER'S presence rules at call time.

    No transcription of them lives in this module (the ledger is passed
    through), so a key the receiver's own vocabulary gains is
    required at once: an artifact lacking it is refused and the refusal names
    it. The receiver's mapping is extended here in place of a new receiver
    claim file, which is the only way this can happen for real. Had the rule
    been a copy held in this module, the ledger below would have been admitted.
    """
    import certiqs_key.receiver.reasons as receiver_reasons
    from certiqs_key.reductions.validation import (
        required_receiver_keys,
        rule_receiver_spec,
    )

    new_key = "a_key_the_receiver_gained_later"
    extended = {**receiver_reasons.ASSUMPTION_MACHINE_KEYS, "A-LATER": new_key}
    monkeypatch.setattr(receiver_reasons, "ASSUMPTION_MACHINE_KEYS", extended)
    assert new_key in required_receiver_keys()

    old_ledger = tuple(
        InheritedAssumption(machine_key=key)
        for key in extended.values()
        if key != new_key
    )
    refusal = rule_receiver_spec(
        _receiver_rows(inherited_assumption_ledger=old_ledger), ("receiver@0.9.0",)
    )
    assert refusal is not None
    assert refusal.reason is RefusalReason.RECEIVER_SPEC_NOT_ACCEPTED
    assert new_key in refusal.detail


def _receiver_rows(**overrides: object) -> ReceiverArtifactRows:
    """Return a well-formed receiver-artifact declaration, mutated per case."""
    coarse = canonical_coarse_graining(
        2,
        empty_letter="y_empty",
        single_letters={1: "y_1", 2: "y_2"},
        multiclick_letter="y_mc",
    )
    settings = ("t_off", "t_on")
    defaults: dict[str, object] = {
        # The supplier version the declared receiver rows carry: the
        # receiver's accepted one, stating the per-setting weights the wpfss
        # slot row requires.
        "mathematical_spec_version": "receiver@0.9.0",
        "detection_alphabet": coarse.letters,
        "photon_blocks": {
            (letter, setting): (matrix([[F(1, 4)]]),)
            for letter in coarse.letters
            for setting in settings
        },
        "high_photon_bounds": (
            HighPhotonBound.uniform(coarse.fibre("y_mc"), F(1, 10), settings),
        ),
        "bound_quantifier_domain": BoundQuantifierDomain(cutoff=0, settings=settings),
        "dark_count_channel": product_form_dark_counts(2, {1: F(3, 16), 2: F(1, 4)}),
        "outcome_coarse_graining": coarse,
        "bound_evaluation": "floating_point",
        "channel_grading": ChannelGrading(block_dimensions=(1,)),
        "validation_results_present": True,
        "declared_device_family": (),
        "occupation_basis_order": (),
        "inherited_assumption_ledger": (),
    }
    defaults.update(overrides)
    return ReceiverArtifactRows(**defaults)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
#  2. No weight is clipped into range
# ---------------------------------------------------------------------------


def test_no_weight_is_clipped_into_range() -> None:
    """A declaration with ``p >= 1`` is REFUSED, not repaired (Section 2.4)."""
    for weights in ((F(1), F(0)), (F(3, 4), F(1, 2)), (F(2), F(0))):
        refusal = rule_total_weight(weights)
        assert refusal is not None
        assert refusal.reason is RefusalReason.TOTAL_WEIGHT_NOT_BELOW_ONE
    # A negative weight is likewise refused rather than raised to zero.
    negative = rule_total_weight((F(-1, 8), F(1, 4)))
    assert negative is not None
    assert negative.reason is RefusalReason.TOTAL_WEIGHT_NOT_BELOW_ONE
    # And the construction refuses to divide by 1 - p at p = 1.
    with pytest.raises(HypothesisError):
        mprime_family((identity(1), identity(1)), (F(1), F(0)))
    # The admissible neighbour IS admitted: rem:peqone's recovery.
    assert rule_total_weight((F(1, 2), F(0))) is None


# ---------------------------------------------------------------------------
#  3. No fibre condition is waived
# ---------------------------------------------------------------------------


def test_no_fibre_condition_is_waived_in_either_direction() -> None:
    """Remark ``rem:fibre``: a SPLIT and a MERGED fibre both refuse."""
    coarse = canonical_coarse_graining(
        3,
        empty_letter="y_empty",
        single_letters={1: "y_1", 2: "y_2", 3: "y_3"},
        multiclick_letter="y_mc",
    )
    multiclick = frozenset(p for p in patterns(3) if len(p) >= 2)
    exact_fibre = HighPhotonBound.uniform(multiclick, F(1, 10), ("off",))
    assert rule_fibre((exact_fibre,), coarse) is None
    # SPLIT: a strict subset of the multiclick fibre.
    split = HighPhotonBound.uniform(
        frozenset({frozenset({1, 2})}), F(1, 10), ("off",)
    )
    refusal = rule_fibre((split,), coarse)
    assert refusal is not None
    assert refusal.reason is RefusalReason.BOUND_SET_NOT_A_FIBRE
    # MERGED: a strict superset. Sound in principle, refused because version 1
    # requires EQUALITY rather than a validated containment.
    merged = HighPhotonBound.uniform(
        multiclick | {frozenset({1})}, F(1, 10), ("off",)
    )
    merged_refusal = rule_fibre((merged,), coarse)
    assert merged_refusal is not None
    assert merged_refusal.reason is RefusalReason.BOUND_SET_NOT_A_FIBRE
    # Two entries on the same letter are refused: the letters must be DISTINCT.
    duplicate = rule_fibre((exact_fibre, exact_fibre), coarse)
    assert duplicate is not None
    assert duplicate.reason is RefusalReason.BOUND_SET_NOT_A_FIBRE


# ---------------------------------------------------------------------------
#  4. No licence is emitted without its certificate
# ---------------------------------------------------------------------------


def test_no_licence_is_emitted_without_its_certificate() -> None:
    """A licence is built only from a non-empty list, and never for an empty one."""
    assert (
        issue_licence(
            [], SourceMode.TRUSTED, "receiver-povm@0.1.3", discharged_by={}
        )
        is None
    )
    preserved = (matrix([[F(2, 3)]]), matrix([[F(1, 3)]]))
    fss = fss_target(preserved)
    _, pi_flag = transported_cutoff_projectors(1, 2)
    # An entry whose declared weight EXCEEDS the certified one has no
    # certificate, so its pull-back is not positive and no licence follows.
    above = (
        matrix(
            [
                [F(19, 40), Cx(F(0), F(-3, 10))],
                [Cx(F(0), F(3, 10)), F(13, 20)],
            ]
        ),
        matrix(
            [
                [F(21, 40), Cx(F(0), F(3, 10))],
                [Cx(F(0), F(-3, 10)), F(7, 20)],
            ]
        ),
    )
    overclaimed = subtract(fss[0], scale(F(1, 2), pi_flag))
    pullback = wp_adjoint(overclaimed, 1, above)
    assert not is_positive_semidefinite(pullback)
    assert not certificate_holds(pullback, Relation.GE, F(0))
    # The presence rule is an IFF, and both directions carry their own reason.
    entry = ConstraintEntry(
        label="entry",
        operator=overclaimed,
        relation=Relation.GE,
        constant=F(0),
        certificate_kind=CertificateKind.POSITIVITY,
        certified_against="Lambda-FSS",
        theta_typing="Theta = c = 0",
    )
    assert rule_licence_presence([entry], licence_present=False) is not None
    assert rule_licence_presence([], licence_present=True) is not None


# ---------------------------------------------------------------------------
#  5. A refusal is a record and never an exception
# ---------------------------------------------------------------------------


def test_a_refusal_is_a_record_and_never_an_exception() -> None:
    """The two vocabularies are disjoint and neither converts into the other."""
    refusal = rule_total_weight((F(1), F(0)))
    assert isinstance(refusal, Refusal)
    assert not isinstance(refusal, BaseException)
    record = refusal.as_machine_record()
    assert set(record) == {"reason", "rule", "detail"}
    assert record["reason"] in {str(reason) for reason in RefusalReason}
    # An exception carries NO reason code, and no reason code is an exception.
    error = MalformedInputError("ragged matrix")
    assert not hasattr(error, "reason")
    assert not any(str(reason) in str(error) for reason in RefusalReason)
    assert issubclass(MalformedInputError, Exception)
    assert issubclass(HypothesisError, Exception)


def test_no_rule_emits_a_reason_that_is_not_its_row_s() -> None:
    """Every emitted reason belongs to the ``sec:failclosed`` row that emitted it.

    THE TWO COUNTS CAME APART AT 0.2.0 and have not come back together, which is
    the point of asserting both. TWENTY-FIVE ROWS carry TWENTY-SEVEN strings:
    three rows name two reasons each, AND ONE REASON
    (``constraint_without_certificate``) IS NAMED BY TWO DIFFERENT ROWS -- the
    constraint-certificate row and the licensed-route Hermiticity row 0.2.0
    adds. So summing the row lengths gives 28 mentions of 27 distinct strings,
    and neither number determines the other. THAT 0.3.0 MOVED BOTH COUNTS BY ONE
    IS A COINCIDENCE OF THAT AMENDMENT: its single row carries a single string.
    """
    # TWENTY-ONE CORE ROWS AND TWENTY-SEVEN ON THE FLAT PATH; the
    # twenty-eighth is a removable submodule's and is asserted in ITS OWN
    # test file, because this one must stay green when that directory is
    # deleted. THE ROWS ARE READ FROM WHAT THE TWO HALVES DECLARE, not from the
    # ambient registry, so the count does not depend on which submodules a
    # caller happened to import.
    rows = {
        str(row.rule): row.reasons for row in CORE_FAIL_CLOSED_ROWS + WPFSS_ROWS
    }
    assert len(RULE_ORDER) == 21
    assert set(RULE_ORDER) < set(rows)
    assert len(rows) == 27
    spanned = {reason for row in rows.values() for reason in row}
    # THE ONE STRING ADDED SINCE THE FREEZE is carried by a row of wpfss that
    # the flat path does not declare: the branch refusal of a normalized
    # receiver (wpfss/req:normalized-branch-refusal), which a branching
    # builder declares.
    from certiqs_key.reductions.wpfss.validation import NORMALIZED_BRANCH_ROWS

    (branch,) = NORMALIZED_BRANCH_ROWS
    assert branch.reasons == (RefusalReason.NORMALIZED_RECEIVER_IN_BRANCH,)
    assert spanned | set(branch.reasons) == set(REFUSAL_REASONS)
    assert len(spanned) == 29
    # The row total exceeds the string count by exactly one at every version,
    # because `constraint_without_certificate` is carried by TWO rows: 28 over
    # 27 at 0.3.0, 31 over 30 at 1.0.0.
    # THIRTY MENTIONS OF TWENTY-NINE STRINGS ON THE FLAT PATH; the
    # thirty-first mention and the thirtieth string are the removable row's.
    assert sum(len(row) for row in rows.values()) == 30
    assert sum(1 for row in rows.values() if len(row) == 2) == 3
    # THE FOUR ROWS 1.0.0 ADDS OR REPLACES CARRY EXACTLY ONE STRING EACH.
    for rule in (
        FailClosedRule.LATTICE_EXPONENT,
        FailClosedRule.REQUESTED_ASSURANCE,
        FailClosedRule.EXACT_ADMISSIBILITY,
        FailClosedRule.EMITTED_FAMILY,
    ):
        assert len(rows[rule]) == 1
    # AND THE ROW THAT RUNS FIRST IS FIRST, which is what decides the reason a
    # caller receives when two rows would refuse.
    assert RULE_ORDER[0] is FailClosedRule.LATTICE_EXPONENT
    assert next(iter(rows)) == FailClosedRule.LATTICE_EXPONENT
    # The row 0.3.0 adds carries exactly one, and is the only carrier of it.
    assert rows[WpfssRule.COLUMN_STOCHASTIC] == (
        RefusalReason.DARK_COUNTS_NOT_COLUMN_STOCHASTIC,
    )
    assert (
        sum(
            1
            for row in rows.values()
            if RefusalReason.DARK_COUNTS_NOT_COLUMN_STOCHASTIC in row
        )
        == 1
    )
    carriers = [
        rule
        for rule, reasons in rows.items()
        if RefusalReason.CONSTRAINT_WITHOUT_CERTIFICATE in reasons
    ]
    assert len(carriers) == 2


def test_a_rule_outcome_records_undecided_separately_from_passed() -> None:
    """Being decided from declared data is not the same as having passed."""
    undecided = RuleOutcome(
        rule=FailClosedRule.OBSTRUCTIONS,
        decided=False,
        refusal=None,
        detail="the physical family is declared symbolically",
    )
    assert undecided.passed is False
    passed = RuleOutcome(rule=FailClosedRule.OBSTRUCTIONS, decided=True, refusal=None)
    assert passed.passed is True
    record = passed.as_machine_record()
    assert record["decided"] is True
    assert record["refusal"] is None


# ---------------------------------------------------------------------------
#  6. Docking is off the package surface
# ---------------------------------------------------------------------------


#: ``certiqs_key.domain`` IS NOT IN THIS LIST. A bundle format is something a
#: module may not reach; ``certiqs_key.domain`` (the
#: frozen wire records) and, below it, ``certiqs_key.foundations`` (the exact
#: substrate, the two hard errors, the tier vocabulary) are the FLOOR every
#: module imports (PRINCIPLES.md section 4) -- and the protocol compiler's
#: package is not a dependency at all.
FORBIDDEN_MODULES = (
    "certiqs_key.protocol",
    "certiqs_key.meat",
    "certiqs_key.runs",
    "certiqs_key.instances",
    "certiqs_key.solvers",
    "numpy",
    "scipy",
)


def test_importing_the_package_imports_no_consumer_and_no_array_library() -> None:
    """PRINCIPLES.md section 4: imports point DOWNWARD ONLY.

    Checked in a FRESH interpreter and on the import graph rather than on the
    text: a module docstring naming ``certiqs_key.protocol`` is a statement about
    the repository, not a dependency.
    """
    program = (
        "import sys\n"
        "import certiqs_key.reductions\n"
        "import certiqs_key.reductions.constraints\n"
        "import certiqs_key.reductions.channels\n"
        "import certiqs_key.foundations.exact\n"
        "import certiqs_key.reductions.inputs\n"
        "import certiqs_key.reductions.links\n"
        "import certiqs_key.reductions.emit\n"
        "import certiqs_key.reductions.instance\n"
        "import certiqs_key.reductions.joint\n"
        "import certiqs_key.reductions.normalizer\n"
        "import certiqs_key.reductions.sectors\n"
        "import certiqs_key.reductions.reasons\n"
        "import certiqs_key.reductions.validation\n"
        "print(';'.join(sorted(sys.modules)))\n"
    )
    completed = subprocess.run(
        [sys.executable, "-c", program],
        capture_output=True,
        text=True,
        check=True,
    )
    loaded = set(completed.stdout.strip().split(";"))
    for forbidden in FORBIDDEN_MODULES:
        assert not any(
            name == forbidden or name.startswith(forbidden + ".") for name in loaded
        ), forbidden
    assert "certiqs_key.reductions" in loaded


#: The tier vocabulary is the platform's ONE
#: (``src/certiqs_key/foundations/assurance.py``), and reaching it is sanctioned at
#: exactly one function-local site -- see
#: :func:`certiqs_key.reductions.emit._requested_assurance` for the four reasons.
TIER_VOCABULARY = "certiqs_key.foundations.assurance"
TIER_VOCABULARY_SITE = "emit.py"


def _imports(tree: ast.AST) -> set[str]:
    """Return every module named by an import anywhere in ``tree``."""
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            names.add(node.module)
    return names


def _docstring_constants(tree: ast.AST) -> set[int]:
    """Return the ids of every docstring constant in ``tree``."""
    return {
        id(node.body[0].value)
        for node in ast.walk(tree)
        if isinstance(
            node, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef
        )
        and node.body
        and isinstance(node.body[0], ast.Expr)
        and isinstance(node.body[0].value, ast.Constant)
        and isinstance(node.body[0].value.value, str)
    }


def test_no_module_of_the_package_names_a_forbidden_import() -> None:
    """The same check on the source, so a lazy import cannot hide from it."""
    for path in sorted(PACKAGE.glob("*.py")):
        if path.name == "docking.py":
            # The ONE file allowed to name a consumer's types; it is not
            # imported from the package surface.
            continue
        for name in _imports(ast.parse(path.read_text(encoding="utf-8"))):
            if path.name == TIER_VOCABULARY_SITE and name == TIER_VOCABULARY:
                # The one sanctioned site; the next test pins its shape.
                continue
            assert not any(
                name == forbidden or name.startswith(forbidden + ".")
                for forbidden in FORBIDDEN_MODULES
            ), (path.name, name)


def test_the_tier_vocabulary_is_reached_at_exactly_one_function_local_site() -> None:
    """ONE vocabulary, ONE site, and the site is inside a function body.

    The platform rule is ``src/certiqs_key/foundations/assurance.py``'s: there is
    one assurance vocabulary and no module outside it re-declares the values.
    This package obeys it by REACHING that enum rather than restating it, and
    it keeps PRINCIPLES.md section 4's downward-only import graph by
    doing so INSIDE A FUNCTION -- so the arrow exists only while a request is
    being validated and never on the package surface, which
    :func:`test_importing_the_package_imports_no_consumer_and_no_array_library`
    checks in a fresh interpreter.
    """
    from certiqs_key.foundations.assurance import Assurance

    sites: list[str] = []
    for path in sorted(PACKAGE.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        if TIER_VOCABULARY in _imports(tree):
            sites.append(path.name)
            # DIRECT CHILDREN OF THE MODULE BODY ONLY. `ast.walk` descends
            # into every function body, which is exactly what this clause must
            # not look at, so the statements are matched rather than walked.
            module_level: set[str] = set()
            for statement in tree.body:
                if isinstance(statement, ast.Import):
                    module_level.update(a.name for a in statement.names)
                elif (
                    isinstance(statement, ast.ImportFrom)
                    and statement.module is not None
                ):
                    module_level.add(statement.module)
            assert TIER_VOCABULARY not in module_level, (
                f"{path.name} imports the tier vocabulary at module level; the "
                "import is function-local so that the package surface stays "
                "free of it"
            )
        # And no module of the package RESTATES a tier value as a literal.
        docstrings = _docstring_constants(tree)
        values = {member.value for member in Assurance}
        offenders = [
            node.lineno
            for node in ast.walk(tree)
            if isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and id(node) not in docstrings
            and node.value in values
        ]
        assert offenders == [], (path.name, offenders)
    assert sites == [TIER_VOCABULARY_SITE]


def test_the_corpus_directory_is_never_named_in_the_package() -> None:
    """R11: a working note is never authority, and is never named here."""
    needles = ("".join(("cont", "ext", "/")), "".join(("cont", "ext", "\\")))
    for path in sorted(PACKAGE.glob("*.py")):
        source = path.read_text(encoding="utf-8")
        for needle in needles:
            assert needle not in source, (path.name, needle)


# ---------------------------------------------------------------------------
#  The vocabularies are the contract's, and version 1's scope is enforced
# ---------------------------------------------------------------------------


def test_the_link_vocabularies_are_the_contract_s() -> None:
    """The nine kinds: six implemented, two reserved and refused, one stated.

    No requirement emits ``family-dominating``: the ``domination``
    submodule states the kind (``domination/def:domination-link``) and implements none,
    so it is neither implemented nor reserved here, and a request that declares one is
    refused by the chain row (tests/golden/test_reductions_fail_closed.py).
    """
    assert len(list(LinkKind)) == 9
    assert len(LINK_KINDS_IMPLEMENTED) == 6
    assert len(LINK_KINDS_DEFERRED) == 2
    assert LinkKind.FAMILY_DOMINATING not in LINK_KINDS_IMPLEMENTED
    assert LinkKind.FAMILY_DOMINATING not in LINK_KINDS_DEFERRED
    assert set(LINK_KINDS_IMPLEMENTED).isdisjoint(LINK_KINDS_DEFERRED)
    assert set(LINK_KINDS_IMPLEMENTED) | set(LINK_KINDS_DEFERRED) == set(LinkKind) - {
        LinkKind.FAMILY_DOMINATING
    }
    assert LINK_STATUS_EMITTED == (LinkStatus.EXACT,)
    assert len(list(LinkStatus)) == 3
    assert {route.value for route in Route} == {"encoded", "licensed"}
    assert "both" not in {route.value for route in Route}


def test_the_never_verified_assumptions_are_the_contract_s() -> None:
    """The never-verified assumptions are the contract's, and no code path decides one.

    A-RECV is an assumption of this contract about the physical device that
    the module names and never verifies, as is a removable submodule's row.
    """
    # There is no A-OPTOL: under exact admissibility there is no window of
    # declared-versus-true blocks for it to be about -- what stands there is a
    # ROW THAT DECIDES (def:exactadm), not an assumption that is named.
    # TWO ON THE CORE'S LEDGER. The frozen pair's other row is a removable
    # submodule's, spelled there so that deleting the submodule takes it with
    # it -- which its own test file asserts, because this one must stay green
    # when that directory is deleted.
    #
    # A-MEAS is a statement about the physical devices and A-ROUND-SQ one about
    # how they behave across the rounds of the run, so no declared datum bears
    # on either. NEVER_VERIFIED is read from each member's `verification`
    # field (spec/claim-format.md section 3.2): A-PROBE, A-TSM and A-CONST, and
    # the transmitter's A-SRC and A-SEQ under their owner's field
    # (def:system-setting is a definition, and the adversary's registers are
    # the round model's, no row). The frozen pair is not touched:
    # ``NEVER_VERIFIED_1_0_0`` is an oracle's record and is never regenerated
    # from the code it tests.
    assert set(NEVER_VERIFIED) == {
        AssumptionId.A_RECV,
        AssumptionId.A_MEAS,
        AssumptionId.A_ROUND_SQ,
    } | {
        AssumptionId.A_PROBE,
        AssumptionId.A_TSM,
        AssumptionId.A_CONST,
        AssumptionId.A_SRC,
        AssumptionId.A_SEQ,
    }
    assert not hasattr(AssumptionId, "A_OPTOL")
    # EIGHT MEMBERS, of which SIX are the core's own and TWO are
    # the transmitter's, assumed here and restated nowhere -- A-SEQ, which
    # `def:protocol` declares, and A-SRC, present only where the
    # emitted chain's source segment is non-empty. There is no A-EVE-DIM
    # member: meat-core's ass:eve-dim is superseded and no claim of this
    # module assumes it. There is no A-NOSRC member: no claim
    # of this module rests on the segment being empty, so the key is in the
    # closure of none of them and a row for it would be a hand-maintained
    # mirror of a generated view. The transmitter's keys carry their owner's
    # mark, `never`.
    assert len(list(AssumptionId)) == 8
    assert set(ASSUMED_FROM_THE_TRANSMITTER) == {"A-SEQ", "A-SRC"}
    assert not hasattr(AssumptionId, "A_EVE_DIM")
    assert not hasattr(AssumptionId, "A_NOSRC")


def test_the_absorbing_refusal_covers_the_whole_artifact() -> None:
    """Remark ``rem:absorbneeded``: version 1 refuses rather than zeroing one entry."""
    channel = product_form_dark_counts(2, {1: F(0), 2: F(1, 4)})
    coarse = canonical_coarse_graining(
        2,
        empty_letter="y_empty",
        single_letters={1: "y_1", 2: "y_2"},
        multiclick_letter="y_mc",
    )
    descended = descend(channel, coarse)
    assert descended is not None
    bounds = (
        HighPhotonBound.uniform(coarse.fibre("y_1"), F(1, 5), ("t0",)),
        HighPhotonBound.uniform(coarse.fibre("y_mc"), F(1, 10), ("t0",)),
    )
    letters = bounded_letters(bounds, coarse, descended)
    assert letters is not None
    # ONE letter is non-absorbing; NOTHING is emitted for either.
    assert [letter.absorbing for letter in letters] == [False, True]
    probe = ProbeDeclaration(settings=("t0",), weights={"t0": F(1)})
    joint = tuple((letter, "t0") for letter in coarse.letters)
    assert weight_route(letters, probe, joint, lattice_exponent=12) is None
    refusal = rule_absorbing(letters)
    assert refusal is not None
    assert refusal.reason is RefusalReason.BOUNDED_LETTER_NOT_ABSORBING


def test_the_emitted_target_is_built_without_any_above_cutoff_block() -> None:
    """Section 2.3: the supplier emits none, and the target needs none."""
    preserved = (matrix([[F(2, 3)]]), matrix([[F(1, 3)]]))
    weights = (F(1, 4), F(1, 8))
    encoded = wpfss_target(preserved, weights)
    licensed = fss_target(preserved)
    assert len(encoded) == len(licensed) == 2
    # The two differ exactly in the flag block, which is where the weights go.
    assert encoded[0][0][0] == licensed[0][0][0]
    assert encoded[0][1][1] != licensed[0][1][1]
    # And the flag block of F^FSS is a rank-one projector: p_v == 0.
    assert licensed[0][1][1].re == 1
    assert licensed[0][2][2].re == 0
    assert equal(licensed[0], direct_sum([preserved[0], diagonal([F(1), F(0)])]))


# ---------------------------------------------------------------------------
#  The column-stochasticity row's own structural properties (NEW AT 0.3.0)
# ---------------------------------------------------------------------------
#
#  These are the Section 2.5 ``fail_closed`` properties read against the one
#  rule 0.3.0 adds. What the row DECIDES, on the five frozen declarations, is
#  ``tests/golden/test_reductions_column_stochastic.py``; what is checked
#  here is that it cannot be made to decide anything else -- no default
#  substituted, no entry dropped, no tolerance consulted, no repair.


def test_the_column_stochasticity_row_substitutes_no_default() -> None:
    """No default is substituted for a missing datum, on the declared ``R``.

    A ``DarkCountChannel`` whose ``entries`` mapping is EMPTY declares the zero
    matrix, not the identity and not "nothing to check": an absent pair is a
    declared zero, which is the record's own convention. So every column sums to
    ``0``, and the row REFUSES. An implementation that read an empty declaration
    as vacuously satisfied, or that filled a missing diagonal with ones, would
    admit a matrix the contract's type excludes.
    """
    empty_channel = DarkCountChannel(ports=2, entries={})
    assert declared_column_sums(empty_channel) == dict.fromkeys(
        patterns(2), Fraction(0)
    )
    refusal = rule_column_stochastic(empty_channel)
    assert refusal is not None
    assert refusal.reason is RefusalReason.DARK_COUNTS_NOT_COLUMN_STOCHASTIC
    assert "sum to one" in refusal.detail

    # The same at K = 0, where 2^[K] is the single empty pattern: a declaration
    # that says nothing about the one column it has is still refused.
    assert patterns(0) == (frozenset(),)
    assert rule_column_stochastic(DarkCountChannel(ports=0, entries={})) is not None


def test_the_column_stochasticity_row_drops_no_entry_and_no_column() -> None:
    """Both halves quantify over the WHOLE index set, not over the stored keys.

    Section ``sec:failclosed`` writes them as "``R_{S|S'} >= 0`` FOR EVERY
    ENTRY" and "``sum_{S subset [K]} R_{S|S'} = 1`` FOR EVERY COLUMN ``S'``", so
    the quantifier is ``2^[K]``, fixed by the declared port count. A declaration
    that supplies three of its four columns has a fourth column of zeros and is
    refused for it; summing only the present keys would admit it.
    """
    index_set = patterns(2)
    assert len(index_set) == 4
    # A well-formed identity matrix on 2^[2], entry by entry.
    identity_entries = {(pattern, pattern): Fraction(1) for pattern in index_set}
    assert (
        rule_column_stochastic(DarkCountChannel(ports=2, entries=identity_entries))
        is None
    )

    # DROP ONE COLUMN ENTIRELY. It is not absent from the quantifier.
    missing = dict(identity_entries)
    del missing[(frozenset({1, 2}), frozenset({1, 2}))]
    refusal = rule_column_stochastic(DarkCountChannel(ports=2, entries=missing))
    assert refusal is not None
    assert refusal.reason is RefusalReason.DARK_COUNTS_NOT_COLUMN_STOCHASTIC
    assert "[1, 2]" in refusal.detail

    # AND THE NON-NEGATIVITY HALF SEES EVERY ENTRY, including one that would be
    # invisible to a scan of the diagonal or of a single column.
    negative = dict(identity_entries)
    negative[(frozenset({1}), frozenset({1, 2}))] = Fraction(-1, 3)
    negative[(frozenset({1, 2}), frozenset({1, 2}))] = Fraction(4, 3)
    channel = DarkCountChannel(ports=2, entries=negative)
    assert all(total == 1 for total in declared_column_sums(channel).values())
    assert smallest_declared_entry(channel) == Fraction(-1, 3)
    refused = rule_column_stochastic(channel)
    assert refused is not None
    assert "negative" in refused.detail


def test_the_column_stochasticity_row_consults_no_tolerance() -> None:
    """No channel exists by which a tolerance could reach this row.

    Remark ``rem:tolboundary`` puts the declared scalars outside the tolerance
    and Assumption A-OPTOL's clause (b) says the same from the assumption's
    side. This is checked STRUCTURALLY rather than by probing values: the rule
    takes exactly one argument, the declared matrix, so no ``eps_op`` can be
    passed to it at all, and its body names no tolerance symbol.
    """
    signature = inspect.signature(rule_column_stochastic)
    assert list(signature.parameters) == ["channel"]
    source = inspect.getsource(rule_column_stochastic)
    body = source.split('"""')[-1]
    for forbidden in ("eps_op", "eta", "lem:exactpsd", "is_positive"):
        assert forbidden not in body, forbidden
    # A defect of exactly the size of a plausible tolerance is refused all the
    # same -- the contract's own example, at the value the freeze probes.
    empty: frozenset[int] = frozenset()
    click = frozenset({1})
    channel = DarkCountChannel(
        ports=1,
        entries={
            (click, click): Fraction(1),
            (click, empty): Fraction(1, 5),
            (empty, empty): Fraction(4, 5) - Fraction(1, 100),
        },
    )
    assert rule_column_stochastic(channel) is not None


def test_the_column_stochasticity_row_repairs_nothing() -> None:
    """Never a repair: the declaration that travels on is the declared one.

    Nothing here renormalizes a column, clips a negative entry to zero, or
    projects the matrix onto the stochastic ones. The row returns a refusal
    RECORD and the caller's object is unchanged.
    """
    empty: frozenset[int] = frozenset()
    click = frozenset({1})
    entries = {
        (click, click): Fraction(1),
        (click, empty): Fraction(1, 2),
        (empty, empty): Fraction(1, 3),
    }
    before = dict(entries)
    channel = DarkCountChannel(ports=1, entries=entries)
    refusal = rule_column_stochastic(channel)
    assert refusal is not None
    assert dict(channel.entries) == before
    assert declared_column_sums(channel)[empty] == Fraction(5, 6)
    # A REFUSAL IS A RECORD AND NEVER AN EXCEPTION.
    assert isinstance(refusal, Refusal)
    assert refusal.rule == str(WpfssRule.COLUMN_STOCHASTIC)
    assert refusal.as_machine_record()["reason"] == "dark_counts_not_column_stochastic"


def test_the_row_is_a_conjunction_and_each_half_refuses_alone() -> None:
    """One half failing is enough, and each half is reachable on its own.

    The two subrules are independent: a matrix can fail non-negativity with
    every column summing to one, and can fail the column sums with every entry
    non-negative. Both are exercised, so a rule that had silently dropped one
    half would still fail here.
    """
    index_set = patterns(1)
    empty: frozenset[int] = frozenset()
    click = frozenset({1})

    # Unit columns, one negative entry.
    negative_only = DarkCountChannel(
        ports=1,
        entries={
            (empty, empty): Fraction(3, 2),
            (click, empty): Fraction(-1, 2),
            (click, click): Fraction(1),
        },
    )
    assert all(total == 1 for total in declared_column_sums(negative_only).values())
    assert smallest_declared_entry(negative_only) < 0
    assert rule_column_stochastic(negative_only) is not None

    # Non-negative everywhere, one column short.
    colsum_only = DarkCountChannel(
        ports=1,
        entries={(empty, empty): Fraction(1, 2), (click, click): Fraction(1)},
    )
    assert smallest_declared_entry(colsum_only) == 0
    assert declared_column_sums(colsum_only)[empty] == Fraction(1, 2)
    assert rule_column_stochastic(colsum_only) is not None

    # And the conjunction admits only when BOTH hold.
    good = DarkCountChannel(
        ports=1,
        entries={
            (empty, empty): Fraction(4, 5),
            (click, empty): Fraction(1, 5),
            (click, click): Fraction(1),
        },
    )
    assert rule_column_stochastic(good) is None
    assert is_column_stochastic(good) is True
    assert len(index_set) == 2


def test_the_two_dark_count_predicates_are_logically_independent() -> None:
    """Neither implies the other, on all four combinations of the two properties.

    Remark ``rem:darkcompose`` needs BOTH rows for the statement that "every
    declaration this module admits is exactly admissible in the supplier's
    sense", ``def:darkadm``'s (D1) coming from the column-stochasticity row and
    (D2) from the descent row. A table of all four combinations is the strongest
    form of "neither covers the other": each cell is witnessed.
    """
    empty: frozenset[int] = frozenset()
    click = frozenset({1})

    # (D1) and (D2): the honest product form.
    both = DarkCountChannel(
        ports=1,
        entries={
            (empty, empty): Fraction(4, 5),
            (click, empty): Fraction(1, 5),
            (click, click): Fraction(1),
        },
    )
    # (D1) but not (D2): a STRICTLY POSITIVE entry at the forbidden position.
    stochastic_not_monotone = DarkCountChannel(
        ports=1,
        entries={
            (empty, empty): Fraction(4, 5),
            (click, empty): Fraction(1, 5),
            (empty, click): Fraction(1, 5),
            (click, click): Fraction(4, 5),
        },
    )
    # (D2) but not (D1): a NEGATIVE entry at the forbidden position, which
    # satisfies the monotonicity implication VACUOUSLY.
    monotone_not_stochastic = DarkCountChannel(
        ports=1,
        entries={
            (empty, empty): Fraction(4, 5),
            (click, empty): Fraction(1, 5),
            (empty, click): Fraction(-1, 5),
            (click, click): Fraction(6, 5),
        },
    )
    # NEITHER. The forbidden entry must be STRICTLY POSITIVE to break
    # monotonicity -- a negative one there is the "monotone not stochastic" cell
    # above -- so the column-stochasticity failure has to come from elsewhere,
    # and here it is the column sums: 1/5 + 1/2 = 7/10 and 0, neither one.
    neither = DarkCountChannel(
        ports=1,
        entries={(empty, click): Fraction(1, 5), (click, click): Fraction(1, 2)},
    )

    table = {
        "both": (both, True, True),
        "stochastic not monotone": (stochastic_not_monotone, True, False),
        "monotone not stochastic": (monotone_not_stochastic, False, True),
        "neither": (neither, False, False),
    }
    for name, (declared, stochastic, monotone) in table.items():
        assert is_column_stochastic(declared) is stochastic, name
        assert is_monotone(declared) is monotone, name
        assert (rule_column_stochastic(declared) is None) is stochastic, name
    # All four cells are distinct, so no cell was witnessed twice.
    assert len({(s, m) for _, s, m in table.values()}) == 4

