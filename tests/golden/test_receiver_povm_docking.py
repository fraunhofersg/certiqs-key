"""The emitted artifact, docked onto ``reductions``' own input rows.

The adapter under test is :mod:`certiqs_key.receiver.docking`, and what is on trial
is the FIELD-TO-ROW MAP: that every receiver row of the consumer's inputs table
(:class:`certiqs_key.reductions.inputs.ReceiverArtifactRows`) is filled from the
artifact and from nothing else, that the conversion to the consumer's exact
substrate is lossless, and that the things the consumer's types cannot carry
do not cross.

THE ROUND TRIP IS RUN THROUGH THE CONSUMER'S OWN ENTRY POINT,
``certiqs_key.reductions.emit.reduce``, on the two receivers the request
builders declare, and it ends at a DECLARED BOUNDARY rather than in a gap: the
consumer decides exact admissibility on entry and refuses both docked receivers,
on that one row alone, as
:func:`test_both_docked_receivers_are_refused_as_not_exactly_admissible`
asserts; on the supplier side this module's ``r_5`` watches the block defect.

WHAT THIS FILE DOES NOT DO. It does not re-check any rule of either contract.
The consumer's fail-closed rows -- descent, the fibre condition, the absorbing
condition, the cutoff agreement, block structure -- are decided by
``reduce`` and by nothing here; the adapter converts and the consumer judges.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import fields
from fractions import Fraction

import numpy as np
import pytest
from probe_presence import requires_probe, with_probe
from receiver_povm_support import bb84_channel_only_request, probe_receiver_request
from reductions_support import RECEIVER_LEDGER_KEYS
from reductions_support import reduce_flat_call as reduce

from certiqs_key.foundations.assurance import Assurance
from certiqs_key.receiver import ReceiverRequest, construct_receiver
from certiqs_key.receiver.artifact import (
    MATHEMATICAL_SPEC_VERSION,
    ReceiverMeasurementArtifact,
)
from certiqs_key.receiver.docking import (
    DockingRefusal,
    DockingRefusalReason,
    receiver_artifact_rows,
)
from certiqs_key.reductions.artifact import assumption_ledger
from certiqs_key.reductions.inputs import (
    BoundQuantifierDomain,
    DarkCountChannel,
    HighPhotonBound,
    LinkDeclaration,
    ProbeDeclaration,
    ProtocolDeclaration,
    ReceiverArtifactRows,
    ReductionRequest,
)
from certiqs_key.reductions.reasons import (
    LinkKind,
    LinkStage,
    RefusalReason,
    SourceMode,
)
from certiqs_key.reductions.validation import rule_receiver_spec

#: THE FIXTURE LATTICE EXPONENT. The consumer's `lattice_exponent` input row
#: (spec/modules/reductions/interface.yaml) is REQUIRED, with NO DEFAULT AND NO
#: FALLBACK, so every request below declares one -- which is the point of the
#: row, and a test helper that supplied one silently would be the default the
#: contract forbids. The value is a fixture choice: the contract fixes none,
#: and spec/architecture.md section 2.9 records the platform's k = 40.
KAPPA_FIXTURE: int = 12

#: THE FILE-LEVEL XFAIL IS GONE, AND THIS FILE IS NOT A DEVICE-PARAMETER
#: PROBLEM. Six of its eight cases exercise the ADAPTER ALONE -- the field-to-row
#: map, the conversion, the four things the consumer's types cannot carry, the
#: docking refusal -- and never call :func:`reduce`, so nothing about
#: ``eq:latinv`` reaches them; they passed under the mark and pass without it.
#: The two that do call :func:`reduce` are re-aimed below at what 1.0.1 makes
#: of this boundary, which is a REFUSAL, and they assert it.
#:
#: WHY NO FROZEN DEVICE PARAMETER REPAIRS THEM, and it is proved rather than
#: assumed (band 5, ``OBSTRUCTIONS_RP_X``). ``bb84_channel_only_request``
#: compiles a ``Beamsplitter(1/2)`` and a ``HWP(pi/8)``, so its instrument
#: matrix carries ``1/sqrt2`` and binary64 squaring returns ``1 + 2.2e-16`` for
#: ``A_Sigma`` -- which fails ``|x| <= 1`` of Eq. ``eq:latinv`` outright, before
#: any lattice question arises -- and THERE IS NO NON-TRIVIAL DYADIC
#: BEAMSPLITTER: ``sqrt(x)`` and ``sqrt(1-x)`` are both dyadic only if a
#: Pythagorean triple has a power-of-two hypotenuse, and every hypotenuse is
#: divisible by an odd primitive hypotenuse above one. ``probe_receiver_request``
#: fails exactly rather than numerically: ``thm:gaussian-schur``'s prefactors are
#: reciprocals ``1/(1 + nbar (A)_ss)``, dyadic only when ``1 + u`` is a power of
#: two, which under this fixture's SYMMETRIC coupling never happens.
#:
#: THE 1.0.0 ANSWER TO BOTH IS THE INSTANCE'S SNAP, NOT NEW PARAMETERS. The
#: ``photon_blocks`` row says it in terms: "the perturbation between these
#: numbers and the receiver's own complex128 output was absorbed AT THE
#: INSTANCE, by the instance's snap ... THAT RECORD IS THE INSTANCE'S AND IS NOT
#: AN INPUT OF THIS MODULE". These tests contain no instance -- they feed
#: ``receiver_artifact_rows`` straight into ``reduce`` -- and
#: :mod:`certiqs_key.foundations.snap` records in its own header that nothing calls it
#: yet. So the full round trip is NOT reopened here; what is asserted is the
#: boundary as it now stands, which needs no frozen number.

# WHAT THE RECEIVER EMITS HERE, READ OFF THE MODULE RATHER THAN SPELLED. The
# module is `receiver` and its pin is an accepted version of
# spec/modules/receiver/module.yaml, so the version is the module's own pin:
# a version pin is the one value that MUST move when the module it names is
# accepted under a new version.
ACCEPTED = (MATHEMATICAL_SPEC_VERSION,)


def _artifact(request: ReceiverRequest) -> ReceiverMeasurementArtifact:
    """Return the emitted artifact, asserting the emission did not refuse."""
    emission = construct_receiver(request)
    assert emission.refusal is None, emission.refusal
    assert emission.artifact is not None
    return emission.artifact


def _rows(request: ReceiverRequest) -> ReceiverArtifactRows:
    """Return the docked rows, asserting the adapter did not refuse."""
    rows = receiver_artifact_rows(_artifact(request))
    assert not isinstance(rows, DockingRefusal), rows
    return rows


def _declaration(rows: ReceiverArtifactRows) -> ProtocolDeclaration:
    """Return the minimal consuming declaration the consumer's request reads.

    THE ALPHABETS COME FROM THE ARTIFACT AND THE WEIGHTS DO NOT. ``T`` and the
    detection alphabet are the receiver's declared data, echoed here because the
    consumer's ``alphabet_or_order_mismatch`` rule compares them ORDER INCLUDED.
    The probe WEIGHTS ``q_t`` are the declaration's own -- Requirement
    ``req:conditional-family-only``: "nothing in this contract multiplies by a
    ``q_t``", and no key of the emitted
    artifact carries one -- so a uniform choice is made HERE, in the test, and is
    not read off the artifact.

    THE REGISTER MODEL IS NOT A SLOT OF THE CONSUMER'S DECLARATION: the
    extended-register construction is a SUBMODULE of that module and is
    removable, so the degenerate one-mode declaration -- which every statement
    of the contract specialises to -- is what an absent slot MEANS rather than
    something a declaration has to spell. This file names no file of the
    submodule, which is what makes the submodule removable.
    """
    settings = rows.bound_quantifier_domain.settings
    weight = Fraction(1, len(settings))
    return ProtocolDeclaration(
        probe_declaration=ProbeDeclaration(
            settings=settings, weights=dict.fromkeys(settings, weight)
        ),
        detection_alphabet=rows.detection_alphabet,
        photon_cutoff=rows.bound_quantifier_domain.cutoff,
        source_mode=SourceMode.UNTRUSTED,
        joint_alphabet=tuple(
            (letter, setting)
            for setting in settings
            for letter in rows.detection_alphabet
        ),
    )


def _request() -> ReductionRequest:
    """Return the minimal reduction request: encoded route, one wpfss link.

    ``requested_assurance`` is REQUIRED by the consumer and carries no default,
    so it is stated here -- and it is spelled from the PLATFORM enum
    :class:`certiqs_key.foundations.assurance.Assurance`, not from a bare string of this
    band's own. One tier vocabulary, one home for it: the same rule that makes
    :mod:`certiqs_key.receiver.request` the single importer of the platform's
    tier vocabulary.
    Asking for ``estimate`` is also the only honest request from this supplier,
    since Theorem ``thm:exact-and-evaluated`` (iii) has already answered every
    ``certified`` one down before the artifact was emitted.

    ``operator_tolerance`` WAS A PARAMETER HERE AND IS GONE. The consumer's
    ``eps_op`` left its contract at 1.0.0 with the whole tolerance apparatus,
    and ``kappa`` is not its successor: the ``lattice_exponent`` row says in
    terms that "IT IS NOT A TOLERANCE, NOTHING IS ADMITTED OR REFUSED WITHIN
    ``kappa``". Nothing on this side chooses either number; ``kappa`` is the
    caller's declaration and no declared tolerance of ``receiver-povm`` is
    reused as one.
    """
    return ReductionRequest(
        lattice_exponent=KAPPA_FIXTURE,
        link_declarations=(
            LinkDeclaration(stage=LinkStage.RECEIVER, kind=LinkKind.WPFSS),
        ),
        route="encoded",
        requested_assurance=Assurance.ESTIMATE,
        accepted_receiver_versions=ACCEPTED,
    )


@pytest.mark.contract
def test_the_conversion_is_exact_and_lossless() -> None:
    """The one conversion site: ``Fraction(x)`` NAMES the dyadic rational ``x``.

    Not a rounding and not an approximation: converting back reproduces the
    double bit for bit, so nothing the receiver decided is changed by crossing.
    """
    for build in (bb84_channel_only_request, *with_probe(probe_receiver_request)):
        artifact = _artifact(build())
        rows = _rows(build())
        # The weights: exact on the way over, and the same double on the way
        # back -- EVERY PER-SETTING WEIGHT (thm:emitted-bound eq:pmcsetting), in
        # the declared order of T, and the uniform weight read off them is the
        # entry's own.
        emitted_entry = artifact.high_photon_bounds.entries[0]
        crossed_entry = rows.high_photon_bounds[0]
        assert crossed_entry.settings == tuple(
            setting for setting, _ in emitted_entry.per_setting
        )
        for (setting, emitted), crossed in zip(
            emitted_entry.per_setting, crossed_entry.weights, strict=True
        ):
            assert isinstance(crossed, Fraction), setting
            assert float(crossed) == emitted
            assert crossed == Fraction(emitted)
        assert crossed_entry.uniform_weight == Fraction(emitted_entry.weight)
        # Every matrix entry, likewise, real and imaginary part separately.
        for outcome, blocks in rows.photon_blocks.items():
            letter, setting = outcome
            family = next(f for f in artifact.photon_blocks if f.setting == setting)
            source = {photons: dict(rows_) for photons, rows_ in family.blocks}
            for photons, block in enumerate(blocks):
                original = np.asarray(source[photons][letter], dtype=np.complex128)
                assert len(block) == original.shape[0]
                for i, row in enumerate(block):
                    for j, entry in enumerate(row):
                        assert float(entry.re) == original[i, j].real
                        assert float(entry.im) == original[i, j].imag


@pytest.mark.contract
def test_the_field_to_row_map_is_honoured() -> None:
    """Every row of the consumer's group 1, filled from the artifact alone."""
    for build in (bb84_channel_only_request, *with_probe(probe_receiver_request)):
        artifact = _artifact(build())
        rows = _rows(build())

        # mathematical_spec_version: the artifact's, verbatim.
        assert rows.mathematical_spec_version == artifact.mathematical_spec_version
        # As ``ACCEPTED`` above: the module is `receiver` and its accepted
        # version is its own module.yaml's.
        assert rows.mathematical_spec_version == MATHEMATICAL_SPEC_VERSION

        # detection_alphabet: the emitted Y, IN ITS DECLARED ORDER.
        assert rows.detection_alphabet == tuple(
            letter for _, letter in artifact.outcome_alphabet.letters
        )

        # bound_quantifier_domain: N and T carried.
        assert rows.bound_quantifier_domain.cutoff == (
            artifact.bound_quantifier_domain.photon_cutoff
        )
        assert rows.bound_quantifier_domain.settings == (
            artifact.bound_quantifier_domain.probe_alphabet
        )

        # bound_evaluation: propagated UNCHANGED, never upgraded (rigorous on
        # the exact route, receiver/req:evaluation-label).
        assert rows.bound_evaluation == artifact.bound_evaluation == "rigorous"

        # channel_grading: from block_dimensions, and no above-cutoff dimension.
        assert rows.channel_grading.block_dimensions == tuple(
            row.dimension for row in artifact.block_dimensions
        )
        assert rows.channel_grading.above_cutoff_finite is False
        assert rows.channel_grading.cutoff == rows.bound_quantifier_domain.cutoff

        # validation_results_present: from the artifact's validation_results.
        assert rows.validation_results_present is bool(
            artifact.validation_results.residuals
        )

        # declared_device_family: EMPTY, derived from calibration_coverage.
        assert rows.declared_device_family == ()

        # occupation_basis_order: every emitted block's basis, in increasing m.
        expected = tuple(
            tuple(str(count) for count in vector)
            for row in artifact.block_dimensions
            for vector in row.occupation_vectors
        )
        assert rows.occupation_basis_order == expected


@pytest.mark.contract
def test_the_photon_blocks_are_re_keyed_and_never_recomputed() -> None:
    """(t, m, y) -> (y, t) -> tuple over m, with the blocks themselves untouched."""
    for build in (bb84_channel_only_request, *with_probe(probe_receiver_request)):
        artifact = _artifact(build())
        rows = _rows(build())
        cutoff = artifact.bound_quantifier_domain.photon_cutoff
        settings = artifact.bound_quantifier_domain.probe_alphabet
        letters = rows.detection_alphabet
        # The mapping covers exactly the product Y x T, and nothing else.
        assert set(rows.photon_blocks) == {
            (letter, setting) for letter in letters for setting in settings
        }
        for blocks in rows.photon_blocks.values():
            assert len(blocks) == cutoff + 1
            for photons, block in enumerate(blocks):
                dimension = rows.channel_grading.block_dimensions[photons]
                assert len(block) == dimension
                assert all(len(row) == dimension for row in block)


@pytest.mark.contract
def test_the_outcome_sets_and_the_raw_channel_are_indexed_by_port_position() -> None:
    """Port LABELS become the consumer's 1-based indices, via ``port_grams``."""
    for build in (bb84_channel_only_request, *with_probe(probe_receiver_request)):
        artifact = _artifact(build())
        rows = _rows(build())
        order = [label for label, _ in artifact.port_grams]
        ports = len(order)
        assert rows.outcome_coarse_graining.ports == ports
        assert rows.dark_count_channel.ports == ports

        # The slot's outcome set is MC_K, in the consumer's index typing.
        entry = rows.high_photon_bounds[0]
        assert all(
            set(pattern) <= set(range(1, ports + 1)) for pattern in entry.outcome_set
        )
        assert all(len(pattern) >= 2 for pattern in entry.outcome_set)
        assert len(entry.outcome_set) == 2**ports - ports - 1

        # cg is total on 2^[K] and its fibres agree with the emitted ones.
        assert len(rows.outcome_coarse_graining.assignment) == 2**ports
        for letter, fibre in artifact.outcome_alphabet.fibres:
            crossed = rows.outcome_coarse_graining.fibre(letter)
            assert len(crossed) == len(fibre)
            for pattern_labels in fibre:
                indexed = frozenset(order.index(label) + 1 for label in pattern_labels)
                assert indexed in crossed

        # The RAW R, entry for entry, with only the non-zero ones carried.
        for column_labels, column_entries in artifact.dark_count_channel.columns:
            column = frozenset(order.index(label) + 1 for label in column_labels)
            for row_labels, value in column_entries:
                row = frozenset(order.index(label) + 1 for label in row_labels)
                assert rows.dark_count_channel.value(row, column) == Fraction(value)
        assert all(value != 0 for value in rows.dark_count_channel.entries.values())


@pytest.mark.contract
@requires_probe
def test_the_four_things_the_consumer_s_types_cannot_carry() -> None:
    """The adapter's limitations 1-3, asserted against the consumer's types."""
    rows = _rows(probe_receiver_request())
    artifact = _artifact(probe_receiver_request())

    # 1. The quantifier SENTENCE: the consumer's record has no field for it, and
    #    the two contracts letter the photon number differently.
    domain_fields = {field.name for field in fields(BoundQuantifierDomain)}
    assert domain_fields == {"cutoff", "settings"}
    assert "statement" not in domain_fields
    assert artifact.bound_quantifier_domain.statement == "for all n > N and all t in T"

    # 2. r_min: this module emits ONE, over the raw non-multiclick columns; the
    #    consumer's channel record has no field for it or for its per-letter
    #    successors, which it derives itself under Lemma lem:descent.
    channel_fields = {field.name for field in fields(DarkCountChannel)}
    assert channel_fields == {"ports", "entries"}
    assert artifact.dark_count_channel.r_min == pytest.approx(0.02)
    assert not any("min" in name for name in channel_fields)

    # NOT A LIMITATION: the per-setting weights are the slot's
    #    guaranteed content (thm:emitted-bound eq:pmcsetting) and the consumer's
    #    record carries one per setting, so they CROSS, each exactly; the
    #    uniform weight is the consumer's to read off them.
    bound_fields = {field.name for field in fields(HighPhotonBound)}
    assert bound_fields == {"outcome_set", "per_setting"}
    assert len(artifact.high_photon_bounds.per_setting) == 2
    assert len(rows.high_photon_bounds) == 1
    assert rows.high_photon_bounds[0].per_setting == tuple(
        (setting, Fraction(weight))
        for setting, weight in artifact.high_photon_bounds.per_setting
    )
    assert rows.high_photon_bounds[0].uniform_weight == Fraction(
        min(weight for _, weight in artifact.high_photon_bounds.per_setting)
    )

    # 3. Keys with no row under their own name: six are limitation 3's (its
    #    seventh item, the alphabet's stable IDs, is not a key), and
    #    assumption_ledger crosses as inherited_assumption_ledger.
    row_names = {field.name for field in fields(ReceiverArtifactRows)}
    for absent in (
        "input_mode_space",
        "port_grams",
        "receiver_construction",
        "efficiency_record",
        "assumption_ledger",
        "calibration_coverage",
        "validation_results",
    ):
        assert absent not in row_names


@pytest.mark.contract
@requires_probe
def test_the_adapter_refuses_rather_than_defaulting_an_unreadable_row() -> None:
    """A docking limitation is a RECORD with a named reason, never a default."""
    from dataclasses import replace

    artifact = _artifact(probe_receiver_request())
    # calibration_coverage the adapter cannot interpret: it must not read an
    # empty device family off prose it does not recognise.
    altered = replace(artifact, calibration_coverage="a different statement")
    outcome = receiver_artifact_rows(altered)
    assert isinstance(outcome, DockingRefusal)
    assert outcome.reason is DockingRefusalReason.CALIBRATION_COVERAGE_NOT_RECOGNISED
    assert outcome.as_machine_record()["reason"] == (
        "calibration_coverage_not_recognised"
    )
    assert not isinstance(outcome, BaseException)
    # And the artifact this module actually emits is recognised.
    assert not isinstance(receiver_artifact_rows(artifact), DockingRefusal)


@pytest.mark.contract
def test_both_docked_receivers_are_refused_as_not_exactly_admissible() -> None:
    """The boundary as 1.0.1 draws it: a REFUSAL, on both receivers, named.

    There is no ``operator_tolerance`` input key, no
    ``declaration_outside_tolerance`` reason string and no tolerance row, so
    there is no tolerance value to run at.

    WHAT IS ASSERTED IS THE BOUNDARY ITSELF. At 1.0.1 the consumer decides
    ``def:exactadm`` on entry -- exactly Hermitian, exactly positive
    semidefinite, exactly complete, and every entry an integer multiple of
    ``2^-kappa`` of modulus at most 1, DECIDED EXACTLY, PER BLOCK, ON ENTRY
    (``reductions/wpfss/interface.yaml``) -- and BOTH of these receivers'
    emitted blocks fail it, for reasons band 5 proves are not repairable by any
    choice of device parameter (see the module header). So both are refused
    under ``declaration_not_exactly_admissible``, and that is asserted here
    rather than left as a blanket xfail.

    THE REFUSAL IS ISOLATED TO THAT ONE ROW: every other row still decides and passes,
    so the
    field-to-row map itself is still under test.

    WHAT WOULD REOPEN THE FULL ROUND TRIP is an instance snap sitting between
    ``receiver_artifact_rows`` and ``reduce`` -- the consumer's interface has
    the perturbation absorbed AT THE INSTANCE, before the module is reached --
    and :mod:`certiqs_key.foundations.snap` exists but, by its own header,
    nothing calls it yet. That is an architectural gap and not a numerical one.
    """
    for build in (bb84_channel_only_request, *with_probe(probe_receiver_request)):
        rows = _rows(build())
        outcome = reduce(rows, _declaration(rows), _request())
        assert outcome.emitted is False, build.__name__
        assert outcome.artifact is None
        assert outcome.refusal is not None
        assert outcome.refusal.reason is (
            RefusalReason.DECLARATION_NOT_EXACTLY_ADMISSIBLE
        ), build.__name__
        # ONE ROW REFUSES AND ONLY ONE.
        assert [
            str(entry.rule)
            for entry in outcome.verification_report.outcomes
            if entry.refusal is not None
        ] == ["exact_admissibility"], build.__name__
        # EVERY OTHER ROW STILL DECIDES, which is the evidence the field-to-row
        # map is right: the version and validation-results row, the cutoff echo,
        # the fibre condition, the descent of R through cg, the absorbing
        # condition, the device family and the alphabet order -- ORDER INCLUDED.
        decided = {str(entry.rule) for entry in outcome.verification_report.outcomes}
        for row in (
            "receiver_spec",
            "cutoff",
            "fibre",
            "descent",
            "absorbing",
            "device_family",
            "alphabet_order",
        ):
            assert row in decided, (build.__name__, row)
        # The receiver's own label crosses unchanged and is never upgraded
        # (`rigorous` on the exact route).
        assert rows.bound_evaluation == "rigorous"


@pytest.mark.contract
def test_the_bb84_refusal_names_the_block_that_fails_it() -> None:
    """The refusal is attributable: it names the block, not just the family.

    The BB84 channel-only receiver's defect is one ulp of one on a single
    block -- ``A_Sigma`` evaluating to ``1 + 2.2e-16`` through a
    ``Beamsplitter(1/2)`` and a ``HWP(pi/8)`` -- and band 5's ``RPX-1`` proves
    no device parameter removes it, the dyadic beamsplitter not existing. The
    contract's ``photon_blocks`` row requires the decision to be "PER BLOCK, ON
    ENTRY", so the refusal names which one, and this test holds the code to that
    rather than to the bare reason string.
    """
    rows = _rows(bb84_channel_only_request())
    outcome = reduce(rows, _declaration(rows), _request())
    assert outcome.refusal is not None
    detail = outcome.refusal.detail
    assert "def:exactadm" in detail
    # The block the receiver-side classification identified, in the contract's
    # own notation: blk M^{=1}_{y|t} at y = 'nc' and t = 'off'.
    assert "blk M^{=1}" in detail
    assert "'nc'" in detail and "'off'" in detail
    # AND WHICH OF THE SIX CONDITIONS FAILED, decided exactly and "NEVER BY AN
    # EIGENVALUE ROUTINE" -- which is the whole reason a defect of one ulp is
    # visible here at all. WHERE THE ULP LANDS IS THE BLAS'S: on the recording
    # machine it is a diagonal entry and positivity (eq:psdtest) refuses it; on
    # macOS arm64 it lands on an off-diagonal pair and Hermiticity refuses it
    # first.
    # Both are def:exactadm on the same block, so either reason is accepted.
    by_positivity = "positive semidefinite" in detail and "eq:psdtest" in detail
    by_hermiticity = "NOT exactly Hermitian" in detail
    assert by_positivity or by_hermiticity


@pytest.mark.contract
@requires_probe
def test_the_docked_rows_are_still_the_receivers_own_data() -> None:
    """The adapter's half of the round trip, which does NOT depend on reduce.

    That the emitted reduction is built from these rows needs an emission and
    there is none, so what is asserted is the half that does not: the rows the adapter
    produces ARE
    the receiver's own data, transported and never re-derived.
    """
    rows = _rows(probe_receiver_request())
    artifact = _artifact(probe_receiver_request())
    # The grading, block for block, with its above-cutoff flag still False.
    assert rows.channel_grading.block_dimensions == tuple(
        block.dimension for block in artifact.block_dimensions
    )
    assert rows.channel_grading.above_cutoff_finite is False
    # The label is not upgraded anywhere on the way (`rigorous` on the exact
    # route, receiver/req:evaluation-label).
    assert rows.bound_evaluation == artifact.bound_evaluation == "rigorous"
    # And the supplier's ledger keys cross with it, which is a row of this
    # boundary: ten, where the frozen 1.0.0 count is thirteen.
    assert len(rows.inherited_assumption_ledger) == len(RECEIVER_LEDGER_KEYS) == 10


@pytest.mark.oracle
@pytest.mark.parametrize(
    ("request_of", "expected"),
    [
        pytest.param(
            probe_receiver_request,
            RECEIVER_LEDGER_KEYS,
            id="probe",
            marks=requires_probe,
        ),
        pytest.param(bb84_channel_only_request, RECEIVER_LEDGER_KEYS, id="probe-free"),
    ],
)
def test_a_real_receiver_s_ledger_rides_the_a_recv_entry_unchanged(
    request_of: Callable[[], ReceiverRequest], expected: tuple[str, ...]
) -> None:
    """The A-RECV entry of a REAL receiver artifact, against the frozen oracle.

    The A-RECV entry carries the supplied ledger as it
    stands instead of filtering it through a list held in ``reductions``; the
    keys a real receiver emits, and their order, are exactly the frozen
    ``INHERITED_RECEIVER_KEYS_1_0_0`` less three keys
    (``RECEIVER_LEDGER_KEYS``), with or without a probe: every row
    is on every artifact. The receiver-spec row admits both, and the A-EIG
    record travels beside its key.

    ``reduce`` is not called: both docked receivers are refused downstream as
    not exactly admissible (see above), so the ledger's two sites -- the
    receiver-spec row and :func:`assumption_ledger` -- are called directly.
    """
    rows = _rows(request_of())
    assert rule_receiver_spec(rows, ACCEPTED) is None
    ledger = assumption_ledger({}, ACCEPTED[0], rows.inherited_assumption_ledger)
    recv = next(entry for entry in ledger if entry.assumption_id == "A-RECV")
    assert recv.inherited == expected
    assert recv.inherited_from == ACCEPTED[0]
    assert [name for name, _ in recv.inherited_declared] == [
        "exact_window_eigenvalue_slack"
    ]
