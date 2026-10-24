"""The three declarations, the three reduction arms, and Eq. ``eq:two-sector-entry``.

The subjects are the template's (``instances/optical_bb84/protocol.yaml``) lowering (its
device requests, its public part, its specification provider:
``tests/support/lowered_templates.py``). What it is about is the ONE claim that makes a
route sweep a comparison at all:

    ``optics.py``, ``honest.py`` and ``rationalize.py`` are shared unchanged and
    the source part is identical, so a difference between two arms is a
    difference between two REDUCTIONS and cannot be a difference in the physics.

That claim is asserted directly -- the three arms are run over one
``ReceiverParameters`` and their receiver artifacts are compared -- rather than
left as a comment, because every comparison between the arms rests on it.

WHAT THE CONTRACT PREDICTS, AND WHAT IS THEREFORE TESTABLE HERE
===============================================================
Proposition ``prop:chain`` (ii) with Corollary ``cor:monotone`` makes ``F^FSS``
strictly cleaner than ``F^WP``; Remark ``rem:tworoutes`` says the encoded route
"is preferable wherever it is available"; and Remark ``rem:published`` proves the
``a > 0`` entry "cuts the strictly smaller set and is the stronger constraint,
UNCONDITIONALLY". The KEY LENGTHS those predict are measured in
``tests/integration/test_optical_bb84_slice.py``, which is where a solver may
run. What is here is the structure the prediction is about: which link kind, how
many entries, whether a licence is present, and -- for the ``a > 0`` entry --
that ``reductions`` CERTIFIED it rather than merely accepted the label.

``a`` IS RE-DERIVED HERE, NOT READ OFF THE ENTRY. ``_two_sector_certificate`` recovers
``a`` and ``b`` from the declared operator and re-verifies them; this file does
the same thing independently, from the emitted ``target_povm``, so that a bug
which built the entry and the check from one wrong number would not pass both.
"""

from __future__ import annotations

from fractions import Fraction as F

import pytest
from instances.bb84.specification import BB84_ACCEPTANCE_ALPHABET
from instances.common.optics import RAW_LETTERS, ReceiverParameters
from instances.common.passive_device import (
    ACCEPTED_RECEIVER_VERSIONS,
    PROBE_SETTING,
    two_sector_provider,
)
from optical_bb84_prologue import run_prologue
from tests.support.lowered_templates import (
    ACCEPTANCE_MAPS,
    ANNOUNCEMENT_RESOLVED,
    ENCODED,
    LICENSED,
    LICENSED_TWO_SECTOR,
    MERGED_DISCARD,
    PAIR_RESOLVED,
    ROUTES,
    lowered,
    optical_config,
    optical_lowered,
)

from certiqs_key.foundations.blocks import Label
from certiqs_key.foundations.exact import (
    Matrix,
    direct_sum,
    identity,
    loewner_ge,
    scale,
    subtract,
)
from certiqs_key.protocol_compiler.spec import PublicPart
from certiqs_key.reductions.artifact import ProofReductionArtifact
from certiqs_key.reductions.constraints import CertificateKind, Relation
from certiqs_key.reductions.inputs import LinkKind, SourceMode
from certiqs_key.reductions.wpfss.construction import (
    transported_cutoff_projectors,
)
from certiqs_key.runs.errors import RunInputReason, RunInputValueError

#: The instance's own spellings of the discarded rounds' letters.
DISCARD = "disc"
NO_CLICK = "nc"
MULTI_CLICK = "mc"

#: The device the route comparison is run over. A dark-count rate large enough
#: that a sub-cutoff multi-click has real probability, which is the ONLY regime
#: where the ``a > 0`` entry has anything to add -- see :func:`two_sector_provider`.
NOISY = ReceiverParameters(photon_cutoff=1, exact_window=2, dark_count=(F(1, 16),) * 4)

#: The ideal device, where ``a = 0`` exactly and the entry is correctly omitted.
IDEAL = ReceiverParameters(photon_cutoff=1, exact_window=2)

#: ``tau``, the ceiling the instance's snap may spend. The sweep's own value,
#: so that what these tests exercise is what a run does. REQUIRED at every
#: ``device_requests`` call:
#: spec/architecture.md 2.8 gives it no default and this file may not
#: invent one either.
TAU = 1e-12

_CACHE: dict[tuple[str, int], object] = {}


# NO TEST BELOW IS MARKED xfail. Contract Section 2.6's `acceptance_data_exact`
# row decides the declared acceptance data at EXACTLY 0, so the instance
# declares its receiver family through `certiqs_key.foundations.snap`, which
# produces exact admissibility (spec/architecture.md 2.9) rather than reducing
# a defect.


def _prologue(parameters: ReceiverParameters, route: str):  # noqa: ANN202
    """One prologue per (device, route), built once and shared."""
    key = (route, id(parameters))
    if key not in _CACHE:
        _CACHE[key] = run_prologue(parameters, route=route)
    return _CACHE[key]


def _public(acceptance_map: str = MERGED_DISCARD) -> PublicPart:
    """Return the template's lowered public part under one acceptance map.

    This part carries Bob's announcement alphabet, the acceptance alphabet,
    the acceptance statistic and Bob's readout alphabet (the keys of
    ``announce_bob``).
    """
    public = optical_lowered(IDEAL, acceptance_map=acceptance_map).public
    assert public is not None
    return public


def _refused_choice(name: str, value: str) -> RunInputValueError:
    """Return the run tier's refusal of a choice outside the template's domain."""
    from instances.optical_bb84.surface import preparation

    config = optical_config(IDEAL)
    with pytest.raises(RunInputValueError) as refused:
        preparation(config.with_(device={**config.device, name: value}))
    assert refused.value.reason is RunInputReason.OUTSIDE_DOMAIN
    return refused.value


# ===========================================================================
#  The alphabets, which two modules have to agree about.
# ===========================================================================


def test_the_emitted_alphabet_is_the_raw_letters_at_the_one_probe_setting() -> None:
    """``V = Y x T`` with ``T = {off}``: this receiver is probe-free.

    A probe-free receiver's labels omit the probe
    component (reductions.inputs.outcome_label), so the emitted alphabet IS
    the raw letters, with no ``,off`` in any label.
    """
    alphabet = tuple(_public().announce_bob)
    assert alphabet == tuple(RAW_LETTERS)
    assert all(PROBE_SETTING not in label.split(",") for label in alphabet)


def test_bobs_announcements_extend_slice_ones_by_exactly_one_class() -> None:
    """The first three are Slice 1's, so the two instances' statistics coincide.

    A fourth is unavoidable: an optical receiver can fail to click and can click
    twice, and both are rounds Slice 1's qubit receiver does not have. Under
    ``merged-discard`` the two share that fourth class, which is the
    declaration this instance carried before it carried another.
    """
    announcements = _public(MERGED_DISCARD).bob_announcement_alphabet
    assert announcements[:3] == ("Z", "(X,0)", "(X,1)")
    assert announcements[3] == DISCARD
    assert len(announcements) == 4


@pytest.mark.parametrize("acceptance_map", [ANNOUNCEMENT_RESOLVED, PAIR_RESOLVED])
def test_a_resolved_map_announces_the_two_discard_reasons_apart(
    acceptance_map: str,
) -> None:
    """Slice 1's three come first; the fourth class becomes two.

    The two resolved arms differ in the ACCEPTANCE alphabet and not in what Bob
    announces, so they share this alphabet exactly.
    """
    announcements = _public(acceptance_map).bob_announcement_alphabet
    assert announcements[:3] == ("Z", "(X,0)", "(X,1)")
    assert announcements[3:] == (NO_CLICK, MULTI_CLICK)
    assert DISCARD not in announcements


def test_the_merged_arm_declares_the_qubit_slices_own_four_letters() -> None:
    """The lateral import and this instance's own spelling, held together.

    The Python instance's ``_public_part`` passed ``instances.bb84.
    specification``'s tuple straight through on this arm so that the exit
    condition compares two sides that declare ONE alphabet; the template writes
    the same four letters, and a drift between the two would make that
    comparison compare two things.
    """
    assert _public(MERGED_DISCARD).acceptance_alphabet == BB84_ACCEPTANCE_ALPHABET


@pytest.mark.parametrize("acceptance_map", list(ACCEPTANCE_MAPS))
def test_the_acceptance_statistic_is_total_and_onto_its_alphabet(
    acceptance_map: str,
) -> None:
    """``phi`` is defined at every announcement pair and uses every letter.

    Totality is what ``protocol-compiler`` asks of it. Surjectivity is this
    instance's own check: a declared letter no pair reaches is a coordinate the
    acceptance box would constrain to the honest zero for no reason, and it
    would make ``|Chat_con|`` -- which divides the completeness budget -- larger
    than the statistic it describes.
    """
    public = _public(acceptance_map)
    announcements = public.bob_announcement_alphabet
    alphabet = public.acceptance_alphabet
    statistic = public.accept_statistic
    # Alice's side is read off the statistic itself rather than imported: it is
    # the same on every arm, and naming it here would be a second copy of it.
    alice = {c_a for c_a, _ in statistic}
    assert alice == {"Z", "(X,0)", "(X,1)"}
    assert set(statistic) == {(c_a, c_b) for c_a in alice for c_b in announcements}
    assert set(statistic.values()) == set(alphabet)
    assert len(alphabet) == len(set(alphabet))


def test_the_announcement_map_is_exactly_a_coarsening_of_the_pair_map() -> None:
    """Every pair letter lands in ONE six-letter class, and every class is hit.

    This is what makes the two resolved arms a pair rather than two separately
    written partitions: the finer one refines the coarser, so a difference
    between the two key rates is the value of the refinement and not the value
    of a different declaration. The witness is built from the two statistics
    and never from a table written beside them.
    """
    fine = _public(PAIR_RESOLVED).accept_statistic
    coarse = _public(ANNOUNCEMENT_RESOLVED).accept_statistic
    assert set(fine) == set(coarse)
    fibres: dict[Label, set[Label]] = {}
    for pair, letter in fine.items():
        fibres.setdefault(letter, set()).add(coarse[pair])
    assert all(len(images) == 1 for images in fibres.values())
    assert {next(iter(images)) for images in fibres.values()} == set(
        _public(ANNOUNCEMENT_RESOLVED).acceptance_alphabet
    )


def test_no_arm_is_coarser_than_the_merged_one_where_a_round_is_kept() -> None:
    """Every arm REFINES ``gen``/``ok``/``err``, and one of them equals it.

    The arms differ in how finely a round is reported and never in what the
    protocol does with it, so no arm may identify two kept pairs that another
    separates: an arm that did would be a different protocol rather than a
    finer statistic over the same one. ``announcement-resolved`` agrees with
    the merged arm exactly here -- it refines only the discarded rounds --
    while ``pair-resolved`` splits ``ok`` and ``err`` by which X outcome was
    announced, which is a refinement and is the point of it.

    Compared as PARTITIONS of the kept pairs, because the three arms name their
    letters differently on purpose and comparing the names would compare the
    spellings.
    """
    merged = _public(MERGED_DISCARD).accept_statistic
    keep = {pair for pair, letter in merged.items() if letter != DISCARD}
    assert keep, "the merged arm keeps some pair"

    def partition(name: str) -> set[frozenset[tuple[Label, Label]]]:
        statistic = _public(name).accept_statistic
        fibres: dict[Label, set[tuple[Label, Label]]] = {}
        for pair in keep:
            fibres.setdefault(statistic[pair], set()).add(pair)
        return {frozenset(pairs) for pairs in fibres.values()}

    reference = partition(MERGED_DISCARD)
    assert len(reference) == 3, "gen, ok and err"
    for name in ACCEPTANCE_MAPS:
        for fibre in partition(name):
            containing = [block for block in reference if fibre <= block]
            assert len(containing) == 1, (name, sorted(fibre))
    assert partition(ANNOUNCEMENT_RESOLVED) == reference


def test_an_unknown_acceptance_map_is_this_instances_error() -> None:
    """The names are this instance's; no module ever sees one from elsewhere.

    The names are the template's ``acceptance_map`` domain, and a
    name outside it is the run tier's coded refusal of the instance's table,
    before any lowering or module runs.
    """
    refused = _refused_choice("acceptance_map", "resolved")
    assert "acceptance_map is 'resolved'" in str(refused)


def test_the_receiver_versions_this_declaration_is_written_against() -> None:
    """The one version this repository has accepted, and the emitted string.

    The one entry is the receiver's pin (an accepted version of its
    module.yaml), written by hand when the pin moves. The
    list is checked against the string the receiver's own docking emits, so
    that an upstream bump reaches a run as ``receiver_spec_not_accepted``
    rather than as a silent reinterpretation -- and so that the list can only
    be widened by hand, which is the fail-closed direction.
    """
    assert ACCEPTED_RECEIVER_VERSIONS == ("receiver@0.9.0",)
    emitted = _prologue(IDEAL, ENCODED).reduction
    assert emitted.verification_report.receiver_spec_version in (
        ACCEPTED_RECEIVER_VERSIONS
    )


# ===========================================================================
#  The three arms are three declarations over ONE device.
# ===========================================================================


def test_an_unknown_route_is_this_instances_error_and_not_a_modules() -> None:
    """``reductions`` only ever sees a string this instance declares."""
    refused = _refused_choice("route", "wpfss")
    assert "route is 'wpfss'" in str(refused)
    assert ROUTES == (ENCODED, LICENSED, LICENSED_TWO_SECTOR)


def test_the_three_arms_run_identical_optics_and_an_identical_source() -> None:
    """The claim the whole route comparison rests on, asserted rather than said.

    If the arms differed in the receiver, a difference in key length would be a
    difference in the physics and the comparison would measure nothing.
    """
    # Compared through the artifact's OWN payload form. Its ``port_grams`` and
    # ``photon_blocks`` carry numpy arrays, and ``==`` on two of those is an
    # array rather than a verdict; ``as_payload`` is the module's own JSON-ready
    # rendering of every field and compares as data.
    payloads = [_prologue(NOISY, route).receiver.as_payload() for route in ROUTES]
    for other in payloads[1:]:
        assert other == payloads[0]
    declarations = [_prologue(NOISY, route).declaration for route in ROUTES]
    for declaration in declarations[1:]:
        assert declaration.alice_marginal == declarations[0].alice_marginal
        assert declaration.alice_dim == declarations[0].alice_dim


@pytest.mark.parametrize(
    ("route", "kind", "emitted_route"),
    [
        (ENCODED, LinkKind.WPFSS, "encoded"),
        (LICENSED, LinkKind.FSS, "licensed"),
        (LICENSED_TWO_SECTOR, LinkKind.FSS, "licensed"),
    ],
)
def test_each_arm_declares_the_link_kind_and_route_it_names(
    route: str, kind: LinkKind, emitted_route: str
) -> None:
    """The two licensed arms are ONE ``reductions`` route, with two lists.

    ``licensed+two-sector`` is this instance's name for a second reduction pass, not a
    third route of that module: the module declares two and would refuse a third.
    """
    reduction = _prologue(NOISY, route).reduction
    assert str(reduction.route) == emitted_route
    links = reduction.reduction_chain.links
    assert len(links) == 1
    assert links[0].kind is kind


def test_the_encoded_route_carries_no_constraint_list_and_no_licence() -> None:
    """The contract's own rule gives an encoded-route declaration none of either.

    Not an omission this instance chose: an encoded-route declaration has no
    attack-set licence to carry, so an entry here would be a claim nothing
    supports.
    """
    reduction = _prologue(NOISY, ENCODED).reduction
    assert reduction.constraint_list == ()
    assert reduction.attack_set_license is None


def test_both_licensed_arms_carry_a_licence_and_the_default_entry() -> None:
    """Corollary ``cor:fssinstance``'s entry, on both, at ``a = 0``."""
    for route in (LICENSED, LICENSED_TWO_SECTOR):
        reduction = _prologue(NOISY, route).reduction
        assert reduction.attack_set_license is not None
        assert len(reduction.constraint_list) >= 1
        baseline = reduction.constraint_list[0]
        assert baseline.relation is Relation.GE
        assert baseline.constant == 0
        assert baseline.certificate_kind is CertificateKind.POSITIVITY
        assert "Pi_flag" in baseline.label


def test_the_licensed_route_emits_rather_than_refusing_for_want_of_a_witness() -> None:
    """The licensed arm is not a two-line diff.

    Theorem ``thm:feasibility`` (i) proves the compiler's DEFAULT witness
    ``tau_A (x) 1_Q/d_Q`` feasible only for an EMPTY constraint list, and
    ``cor:fssinstance``'s entry is not empty -- so the licensed route genuinely
    fails it and the compilation refuses with ``no_feasibility_witness``. This
    instance therefore supplies the below-cutoff corner
    ``tau_A (x) 1_{<=N}/d_{<=N}``, which discharges every entry by the SAME
    inequality that certifies it. A regression there would show up here as a
    refusal, not as a wrong number.
    """
    for route in (LICENSED, LICENSED_TWO_SECTOR):
        compilation = _prologue(NOISY, route).compilation
        assert compilation.refusal is None, compilation.refusal
        assert compilation.declaration is not None


def test_the_source_is_trusted_on_every_arm() -> None:
    """The licensed+trusted docking REQUIRES a declared ``tau_A``, and has one."""
    for route in ROUTES:
        request = optical_lowered(NOISY, declared_tolerance=TAU, route=route).device
        assert request.reduction_declaration.source_mode is SourceMode.TRUSTED
        assert _prologue(NOISY, route).declaration.alice_marginal is not None


# ===========================================================================
#  Eq. eq:two-sector-entry: asked for where it helps, omitted where it cannot.
# ===========================================================================


def test_at_the_ideal_device_the_published_entry_asks_for_nothing() -> None:
    """``a = 0`` exactly, and the entry is OMITTED rather than weakened.

    With unit efficiency and no dark counts no state of at most ``N`` photons
    can produce a multi-click at all, so ``blk M^{<=N}_mc = 0`` and the published
    entry has nothing to add over the default. Asking for it at ``a = 0`` would
    add a duplicate of the baseline under a second label, not a constraint.
    """
    baseline = _prologue(IDEAL, LICENSED).reduction
    assert two_sector_provider()(baseline) == ()
    with_arm = _prologue(IDEAL, LICENSED_TWO_SECTOR).reduction
    assert len(with_arm.constraint_list) == len(baseline.constraint_list)


def test_at_a_noisy_device_the_published_entry_is_asked_for_and_certified() -> None:
    """The first time Eq. ``eq:two-sector-entry`` has been driven through ``reduce()``.

    Its BUILDER was tested before this band; the entry itself had never crossed
    the module boundary. What is asserted is that the module EMITTED it -- an
    entry the module declined would be absent from ``constraint_list``, not
    present with a warning.
    """
    baseline = _prologue(NOISY, LICENSED).reduction
    requested = two_sector_provider()(baseline)
    assert len(requested) == 1

    emitted = _prologue(NOISY, LICENSED_TWO_SECTOR).reduction
    assert len(emitted.constraint_list) == len(baseline.constraint_list) + 1
    published = emitted.constraint_list[-1]
    assert published.label == requested[0].label
    assert "Pi_leq" in published.label


def test_the_published_entry_has_the_shape_the_certificate_requires() -> None:
    """Five requirements ``_two_sector_certificate`` enforces, asserted on the emission.

    ``relation = GE``, ``constant = 0`` EXACTLY, ``certificate_kind =
    POSITIVITY``, ``certified_against`` the link's own witness, and a declared
    constant -- Assumption A-CONST, where a ``False`` would be
    ``data_dependent_constant`` and nothing would infer the value.
    """
    reduction = _prologue(NOISY, LICENSED_TWO_SECTOR).reduction
    published = reduction.constraint_list[-1]
    assert published.relation is Relation.GE
    assert published.constant == F(0)
    assert published.certificate_kind is CertificateKind.POSITIVITY
    assert published.certified_against == reduction.squashing_channel.identity
    assert published.constant_is_declared is True


def test_the_published_entry_is_the_baseline_minus_a_positive_multiple_of_pi() -> None:
    """``O^ = O^|_{a=0} - a Pi_{<=N}`` with ``a > 0``, re-derived independently.

    ``a`` is recovered here from the EMITTED ``target_povm``, not read off the
    entry's label and not taken from the builder, so a single wrong number could
    not satisfy both this file and ``_two_sector_certificate``.
    """
    reduction = _prologue(NOISY, LICENSED_TWO_SECTOR).reduction
    baseline, published = reduction.constraint_list
    preserved = reduction.source_descriptor.channel_grading.preserved_dimension
    pi_leq, _pi_flag = transported_cutoff_projectors(
        preserved, len(reduction.target_povm)
    )

    difference = subtract(
        _whole_space(baseline.operator), _whole_space(published.operator)
    )
    # The difference must be exactly ``a Pi_{<=N}`` for ONE positive rational a:
    # the same quotient at every entry the projector supports, and exactly zero
    # everywhere else. A ``Cx`` never equals the int 0, so the support test is
    # on the parts.
    recovered = None
    for row in range(len(difference)):
        for column in range(len(difference)):
            entry, projector = difference[row][column], pi_leq[row][column]
            if projector.re != 0 or projector.im != 0:
                assert projector.im == 0, "Pi_{<=N} is real"
                candidate = entry.over(projector.re)
                recovered = candidate if recovered is None else recovered
                assert candidate == recovered, "not a scalar multiple of Pi_{<=N}"
            else:
                assert entry.re == 0
                assert entry.im == 0
    assert recovered is not None
    assert recovered.im == 0
    assert recovered.re > 0


def test_the_declared_a_satisfies_the_loewner_inequality_that_certifies_it() -> None:
    """Eq. ``eq:certificate``: ``blk M^{<=N}_e >= a 1`` on the preserved block.

    Decided with the module's OWN exact :func:`loewner_ge`, on the emitted POVM
    element, at the ``a`` this instance declared. The contract's own posture is
    what makes a conservative ``a`` legitimate: "a caller declaring smaller
    values gets a weaker but equally certified entry; one declaring larger values
    gets ``constraint_without_certificate``."
    """
    reduction = _prologue(NOISY, LICENSED_TWO_SECTOR).reduction
    baseline, published = reduction.constraint_list
    preserved = reduction.source_descriptor.channel_grading.preserved_dimension
    pi_leq, _pi_flag = transported_cutoff_projectors(
        preserved, len(reduction.target_povm)
    )
    difference = subtract(
        _whole_space(baseline.operator), _whole_space(published.operator)
    )
    declared = next(
        difference[row][column].over(pi_leq[row][column].re).re
        for row in range(len(difference))
        for column in range(len(difference))
        if pi_leq[row][column].re != 0
    )

    outcome = _multiclick_outcome(reduction)
    block = _preserved_block(reduction.target_povm[outcome], preserved)
    assert loewner_ge(block, scale(declared, identity(preserved)))


def _multiclick_outcome(reduction: ProofReductionArtifact) -> str:
    """Return the emitted label of the multi-click outcome, from the alphabet."""
    for label in reduction.target_povm:
        if "mc" in label:
            return label
    raise AssertionError("this receiver's alphabet carries a multi-click letter")


def _preserved_block(element: tuple[Matrix, ...], preserved: int) -> Matrix:
    """Return ``blk M^{<=N}`` from the element's LEADING SECTOR BLOCKS.

    The emitted element is a sector-block list (spec/architecture.md 2.9) and
    the preserved summand is one sector per photon number since the reductions
    restructure, so the corner of the dense element is
    the direct sum of the leading blocks.
    """
    blocks: list[Matrix] = []
    total = 0
    for block in element:
        if total >= preserved:
            break
        blocks.append(block)
        total += len(block)
    assert total == preserved, (total, preserved)
    return direct_sum(blocks)


def _whole_space(element: tuple[Matrix, ...]) -> Matrix:
    """Return the ``d_Q x d_Q`` rendering a whole-space comparison needs."""
    return direct_sum(list(element))


# ===========================================================================
#  The helper this file shares with three others is the path a run takes.
# ===========================================================================


def test_the_prologue_here_agrees_with_the_one_a_run_takes() -> None:
    """Pins ``tests/support/optical_bb84_prologue.py`` against the pipeline.

    That helper composes the PUBLIC entry points in the order
    :func:`certiqs_key.runs.pipeline._run_device_prologue` runs them, and
    ``reductions`` Section 2.2 says of its own three steps that "THE ORDER
    IS PART OF THE INTERFACE, NOT AN IMPLEMENTATION DETAIL". This asserts the
    two agree on their observable output, so that a change to the pipeline's
    order fails here rather than leaving three unit modules testing a path no
    run takes.
    """
    from certiqs_key.runs.flow import FlowRecorder
    from certiqs_key.runs.pipeline import DeviceEmission, _run_device_prologue

    device = optical_lowered(
        NOISY, declared_tolerance=TAU, route=LICENSED_TWO_SECTOR
    ).device
    outcome = _run_device_prologue(device, FlowRecorder(device_prologue=True))
    # Composition follows all station emissions in the multi-station path.
    # The prologue still carries its own artifact edges and final prepared call.
    assert isinstance(outcome, DeviceEmission)
    receiver, reduction, adaptation = (
        outcome.receiver,
        outcome.reduction,
        outcome.rows_adaptation,
    )
    assert [identifier.split(":")[0] for identifier in outcome.upstream] == [
        "receiver_artifact",
        "reduction_chain",
    ]

    mine = _prologue(NOISY, LICENSED_TWO_SECTOR)
    assert receiver.as_payload() == mine.receiver.as_payload()
    assert reduction.constraint_list == mine.reduction.constraint_list
    assert reduction.target_povm == mine.reduction.target_povm
    assert str(reduction.route) == str(mine.reduction.route)
    assert adaptation == mine.adaptation


def test_the_alice_weights_the_specification_provider_is_given_reach_the_run() -> None:
    """They are Alice's and cannot be the receiver's.

    Bob's basis weight IS the beamsplitter's splitting ratio, a DEVICE
    parameter; Alice's is a declaration the specification provider carries. A
    provider that ignored its arguments would make the two indistinguishable in
    the record, so the asymmetric pair is run and its effect asserted.
    """
    symmetric = run_prologue(IDEAL, route=ENCODED).declaration
    asymmetric = run_prologue(
        IDEAL, route=ENCODED, alice_z=F(7, 8), alice_x=F(1, 8)
    ).declaration
    assert symmetric.alice_dim == asymmetric.alice_dim == 2
    assert symmetric.acceptance_alphabet == asymmetric.acceptance_alphabet
    assert symmetric.alice_povm != asymmetric.alice_povm


def test_the_default_configuration_declares_the_exact_window_at_n_plus_one() -> None:
    """The instance's own default must be a MEANINGFUL point, not merely a legal one.

    Without a declared window the analytic high-photon bound of ``receiver`` Definition
    ``def:pmc`` stays in force where ``def:pmcex`` would sharpen it, and this device
    then yields no key at all -- which
    ``tests/integration/test_optical_bb84_slice.py::test_without_the_exact_window_the_cutoff_one_device_yields_no_key``
    pins as the CORRECT value of that bound. Both facts stand together: the analytic
    zero is right, and a default configuration that walks into it is a trap for the
    first caller.

    THE RELATION IS ASSERTED, NOT THE NUMBER. ``m*`` is filled from the cutoff
    in the same mapping, so a caller who raises ``N`` through ``overrides`` is
    never left with a window that no longer exceeds it -- which
    ``ReceiverParameters`` would refuse outright. A literal ``2`` here would
    pass at the shipped cutoff and hide exactly that failure.
    """
    from instances.optical_bb84.surface import default_config

    for cutoff in (1, 2, 3):
        device = dict(default_config().device)
        device["photon_cutoff"] = F(cutoff)
        config = default_config(device=device | {"exact_window": F(cutoff + 1)})
        assert config.device["exact_window"] == config.device["photon_cutoff"] + 1

    shipped = default_config()
    assert shipped.device["exact_window"] == shipped.device["photon_cutoff"] + 1
    # And the value the declaration surface carries stays ABSENT: the row
    # describes what a declaration MAY carry, and absent is a legal declaration
    # rather than a number standing in for one.
    from instances.optical_bb84.surface import PARAMETERS

    row = next(spec for spec in PARAMETERS if spec.name == "exact_window")
    assert row.default is None


def test_the_default_configuration_reaches_the_instance_reader_as_a_window() -> None:
    """And the filled key survives this instance's own reader, not just the mapping.

    The reader is the template's lowering: an ABSENT
    ``exact_window`` lowers to a receiver request that declares no depth, so a
    default that never reached the reader would be indistinguishable from no
    default at all.
    """
    request = lowered("optical_bb84")[1].device.receiver_request
    assert request.exact_window == {PROBE_SETTING: request.photon_cutoff + 1}
