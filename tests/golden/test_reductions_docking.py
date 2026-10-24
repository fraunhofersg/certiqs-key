"""Docking: the emitted artifact, in the consumer's records, and OFF the surface.

Two things are checked here and they pull in opposite directions, which is the
point. The conversion must WORK -- the docked chain is accepted by
``protocol-compiler``'s OWN chain checker, wherever that checker's conditions are
decidable -- and it must stay OFF THE PACKAGE SURFACE, so that importing
:mod:`certiqs_key.reductions` still imports no consumer.

The round trip runs the consumer's :func:`certiqs_key.domain.chain.check_chain`
rather than a re-implementation of it. (C4) is the one condition it cannot
decide, and the reason is the contract's rather than the conversion's: the
supplier emits no above-cutoff block, so no link can supply its channel as data
and the consumer's own Assumption A-LINK is named instead.
"""

from __future__ import annotations

import ast
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

import pytest
from reductions_support import RECEIVER_LEDGER_KEYS
from reductions_support import reduce_flat_call as reduce
from registry_reductions import (
    PR_R3,
)

from certiqs_key.domain.chain import Side, SystemDescriptor
from certiqs_key.domain.constraints import Relation as ConsumerRelation
from certiqs_key.domain.constraints import RhsTag
from certiqs_key.foundations.blocks import BlockKind
from certiqs_key.foundations.exact import Cx as ConsumerCx
from certiqs_key.foundations.exact import dimension as consumer_dimension
from certiqs_key.foundations.exact import direct_sum, equal, identity, matrix, zeros
from certiqs_key.foundations.exact import is_hermitian as consumer_is_hermitian
from certiqs_key.foundations.exact import scale as consumer_scale
from certiqs_key.protocol_compiler.docking_reductions import (
    chain_report,
)
from certiqs_key.protocol_compiler.reasons import (
    AssumptionId as ConsumerAssumptionIdEnum,
)
from certiqs_key.protocol_compiler.reasons import (
    ConditionOutcome as ConsumerConditionOutcome,
)
from certiqs_key.reductions import MATHEMATICAL_SPEC_VERSION, docking
from certiqs_key.reductions.artifact import ProofReductionArtifact
from certiqs_key.reductions.inputs import (
    BoundQuantifierDomain,
    ChannelGrading,
    CoarseGraining,
    HighPhotonBound,
    InheritedAssumption,
    LinkDeclaration,
    ProbeDeclaration,
    ProtocolDeclaration,
    ReceiverArtifactRows,
    ReductionRequest,
    patterns,
    product_form_dark_counts,
)
from certiqs_key.reductions.links import source_stage_is_empty
from certiqs_key.reductions.reasons import LinkKind, LinkStage, SourceMode

#: ``ChainContext``, ``ChainReport``, ``ConditionOutcome`` and ``check_chain``
#: are the PROTOCOL COMPILER'S OWN EVALUATION of its chain conditions -- a
#: consumer's behaviour, not a shared wire record -- so they are not in
#: :mod:`certiqs_key.domain.chain`; the two docking functions that build them
#: live in :mod:`certiqs_key.protocol_compiler.docking_reductions`, in the
#: CONSUMER's package rather than this one's, which is the direction imports
#: run in (PRINCIPLES.md section 4). ``ConditionOutcome`` and the consumer's
#: ``AssumptionId`` are the real enums. The file's own docstring says the round
#: trip "runs the consumer's checker rather than a re-implementation of it".

ConditionOutcome = ConsumerConditionOutcome
ConsumerAssumptionId = ConsumerAssumptionIdEnum

#: THE FIXTURE LATTICE EXPONENT. Section 2.1's `lattice_exponent` row is
#: REQUIRED and has "NO DEFAULT AND NO FALLBACK", so every request below
#: declares one -- which is the point of the row, and a test helper that
#: supplied one silently would be the default the contract forbids. The value
#: is a fixture choice: the contract "fixes no value".
KAPPA_FIXTURE: int = PR_R3.kappa

F = Fraction

#: THE FIXTURES BELOW ARE THE DYADIC ONES: data on a dyadic lattice, because
#: data off it (blocks of 3/5 and 2/5, slot weights of 1/5 and 1/10) are
#: refused under ``declaration_not_exactly_admissible`` (``def:exactadm`` (b),
#: Eq. ``eq:latinv``).
#:
#: The declaration is ``PR_R3``, a two-instance freeze derived by
#: hand from the accepted 1.0.1 by an agent that wrote no source file. The
#: assertions are structural -- sectors,
#: labels, dimensions, the licence fragments, the ``tau_A`` typing -- and none
#: of them is about particular fifths.
#: ``TAU_A = diag(1/2, 1/2)`` is already dyadic and is the CALLER'S, not this
#: module's: no row of this contract decides it.

PACKAGE = Path(__file__).resolve().parents[2] / "src" / "certiqs_key" / "reductions"

#: The sector block kind every call below declares: the shared format's
#: ``proof_sector`` (:class:`~certiqs_key.foundations.blocks.BlockKind`,
#: spec/architecture.md, a frozen type of the shared format). THE
#: DECLARATION IS THE CALLER'S AND NOT THIS MODULE'S, and ``proof_sector`` is
#: the member the emitted map IS: its identifiers are named by the REDUCTION (one
#: preserved summand and
#: the flag sectors of the weight-preserving flag-state squasher), not by a
#: photon number of the physical receiver, which is a different map with kind
#: ``physical_sector``.
FIXTURE_BLOCK_KIND = BlockKind.PROOF_SECTOR
#: The declaration's ``tau_A``: a state on Alice's system, supplied by the
#: CALLER because Remark ``rem:notlicensed`` (a) forbids this module to declare
#: one. A rank-one qubit state is enough for the typing clauses V6 decides.
TAU_A = matrix([[F(1, 2), F(0)], [F(0), F(1, 2)]])


def _consumer(operator: object) -> object:
    """Return one of this module's matrices in the consumer's representation."""
    return tuple(
        tuple(ConsumerCx(entry.re, entry.im) for entry in row)
        for row in operator  # type: ignore[attr-defined]
    )


LETTERS = ("a", "b")
JOINT = (("a", "t"), ("b", "t"))


def _emitted(
    route: str = "encoded", mode: SourceMode = SourceMode.UNTRUSTED
) -> ProofReductionArtifact:
    """Emit a two-mode artifact on the requested route."""
    assignment = {
        pattern: ("a" if pattern in (frozenset(), frozenset({1})) else "b")
        for pattern in patterns(2)
    }
    coarse = CoarseGraining(ports=2, letters=LETTERS, assignment=assignment)
    blocks = dict(PR_R3.declared_blocks)
    weights = dict(PR_R3.slot_weights)
    rows = ReceiverArtifactRows(
        mathematical_spec_version="receiver@0.9.0",
        detection_alphabet=LETTERS,
        photon_blocks={
            ("a", "t"): (matrix([[blocks["a"]]]),),
            ("b", "t"): (matrix([[blocks["b"]]]),),
        },
        high_photon_bounds=(
            HighPhotonBound.uniform(coarse.fibre("a"), weights["a"], ("t",)),
            HighPhotonBound.uniform(coarse.fibre("b"), weights["b"], ("t",)),
        ),
        bound_quantifier_domain=BoundQuantifierDomain(cutoff=0, settings=("t",)),
        dark_count_channel=product_form_dark_counts(2, {1: F(0), 2: F(0)}),
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
            settings=PR_R3.settings, weights=dict(PR_R3.probe_weights)
        ),
        detection_alphabet=LETTERS,
        photon_cutoff=0,
        source_mode=mode,
        joint_alphabet=JOINT,
    )
    request = ReductionRequest(
        lattice_exponent=KAPPA_FIXTURE,
        link_declarations=(
            LinkDeclaration(
                stage=LinkStage.RECEIVER,
                kind=LinkKind.FSS if route == "licensed" else LinkKind.WPFSS,
            ),
            LinkDeclaration(stage=LinkStage.RECEIVER, kind=LinkKind.PINCHING),
        ),
        route=route,
        accepted_receiver_versions=("receiver@0.9.0",),
        requested_assurance="estimate",
    )
    outcome = reduce(rows, declaration, request)
    assert outcome.artifact is not None, outcome.refusal
    return outcome.artifact


PHYSICAL = SystemDescriptor(
    name=(
        "B = C Bl, described by the consuming declaration: H(C) is a Fock space "
        "(def:system-setting) and SystemDescriptor.dim cannot express it "
        "(docking limitation 1)"
    ),
    dim=2,
    side=Side.RECEIVER,
)


# ---------------------------------------------------------------------------
#  The round trip through the consumer's OWN chain checker
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_the_docked_chain_is_accepted_by_the_consumer_s_own_checker() -> None:
    """``check_chain`` decides (C1), (C2), (C3), (C5); none of them fails."""
    artifact = _emitted()
    report = chain_report(
        artifact,
        PHYSICAL,
        sector_block_kind=FIXTURE_BLOCK_KIND,
    )
    assert report.failing_condition is None
    assert report.refusal is None
    assert report.verdicts["C1"] is ConditionOutcome.HOLDS
    assert report.verdicts["C2"] is ConditionOutcome.HOLDS
    assert report.verdicts["C3"] is ConditionOutcome.HOLDS
    assert report.verdicts["C5"] is ConditionOutcome.HOLDS


@pytest.mark.contract
def test_the_one_undecidable_condition_names_the_consumer_s_own_assumption() -> None:
    """(C4) needs the channel AS DATA, and Section 2.3 says there is none.

    "The supplier emits no above-cutoff block at all, so neither map can be
    materialised from the artifact -- and neither need be, SINCE THE CONSUMER
    NEVER APPLIES IT." The consumer's answer to that is ``not checked`` with its
    Assumption A-LINK named, which is the correct outcome rather than a gap.
    """
    artifact = _emitted()
    report = chain_report(
        artifact,
        PHYSICAL,
        sector_block_kind=FIXTURE_BLOCK_KIND,
    )
    assert report.verdicts["C4"] is ConditionOutcome.NOT_CHECKED
    assert report.named_assumption is ConsumerAssumptionId.A_LINK
    chain = docking.reduction_chain(
        artifact,
        PHYSICAL,
        sector_block_kind=FIXTURE_BLOCK_KIND,
    )
    assert all(link.channel is None for link in chain.receiver_segment)
    assert all(not link.channel_supplied for link in chain.receiver_segment)


@pytest.mark.contract
def test_the_source_segment_is_empty() -> None:
    """The ``source`` stage of every emitted chain is EMPTY, AND IT IS DATA.

    The (S1)-(S4) verdicts are the consumer's own evaluation; that the
    segment IS empty is decidable on the docked chain AND on the
    module's own predicate.

    WHOSE STATEMENT IT IS: no module's assumption at all. The emitted
    ``reduction_chain`` CARRIES the
    segment, so a consumer reads whether it is empty.
    """
    artifact = _emitted()
    chain = docking.reduction_chain(
        artifact,
        PHYSICAL,
        sector_block_kind=FIXTURE_BLOCK_KIND,
    )
    assert chain.source_segment == ()
    assert chain.source_length == 0
    assert chain.receiver_length == len(artifact.reduction_chain.links)
    assert source_stage_is_empty(artifact.reduction_chain.links)


@pytest.mark.contract
def test_the_source_segment_s_conditions_are_vacuous_to_the_consumer() -> None:
    """(S1)-(S4) as the consumer's own checker reports them."""
    report = chain_report(
        _emitted(), PHYSICAL, sector_block_kind=FIXTURE_BLOCK_KIND
    )
    for condition in ("S1", "S2", "S3", "S4"):
        assert report.verdicts[condition] is ConditionOutcome.VACUOUS


@pytest.mark.contract
def test_the_docked_target_carries_the_sectors_and_the_povm_exactly() -> None:
    """(C3) is decided "on the emitted matrices themselves", and they are exact."""
    artifact = _emitted()
    descriptor = docking.target_descriptor(
        artifact,
        sector_block_kind=FIXTURE_BLOCK_KIND,
    )
    assert descriptor.side is Side.RECEIVER
    assert descriptor.dim == artifact.target_descriptor.dimension
    assert descriptor.sectors is not None
    assert len(descriptor.sectors) == len(artifact.target_descriptor.sectors.labels)
    assert [dim for _, dim in descriptor.sectors] == list(
        artifact.target_descriptor.sectors.dimensions
    )
    # The label join is the representational change, and it is injective.
    joined = [label for label, _ in descriptor.sectors]
    assert len(set(joined)) == len(joined)
    assert all(":" in label for label in joined)
    # The POVM crosses exactly: both sides are exact Gaussian rationals. AT
    # 1.0.0 IT CROSSES AS SECTOR BLOCKS AND NOT AS A FULL-SPACE ARRAY -- "there
    # is no full-space array, no off-block entry to declare and none to verify"
    # (sec:inputs, `photon_blocks`; ADR-0008) -- AND THE ARTIFACT CARRIES THE
    # SAME LIST, so the
    # comparison is block against block and nothing is split on either side.
    chain = docking.reduction_chain(
        artifact,
        PHYSICAL,
        sector_block_kind=FIXTURE_BLOCK_KIND,
    )
    last = chain.receiver_segment[-1]
    assert last.target_povm is not None
    dims = list(artifact.target_descriptor.sectors.dimensions)
    settings = docking.probe_settings_of(artifact.wpfss_data.flag_basis)
    for outcome, element in artifact.target_povm.items():
        docked = last.target_povm[docking.outcome_label(outcome, settings)]
        assert len(docked.blocks) == len(dims) == len(element)
        for block, emitted_block, dim in zip(docked.blocks, element, dims, strict=True):
            assert len(block) == dim
            for i in range(dim):
                for j in range(dim):
                    assert block[i][j].re == emitted_block[i][j].re
                    assert block[i][j].im == emitted_block[i][j].im
        # The blocks ACCOUNT FOR THE WHOLE TARGET: their dimensions sum to
        # dim H(Q), which is the only thing a dense rendering would have added.
        assert sum(len(block) for block in docked.blocks) == (
            artifact.target_descriptor.dimension
        )


@pytest.mark.contract
@pytest.mark.oracle
def test_the_emitted_target_is_the_frozen_one_of_prr_3() -> None:
    """The fixture, checked against the freeze rather than itself.

    A fixture proves nothing on its own:
    every assertion in this file would still pass against a family the code
    invented. So the emission is asserted against band 5's ``PR_R3``, derived
    by hand from the accepted 1.0.1 by an agent that wrote no source file --
    the emitted target ``F_a = diag(19/32, 29/32, 3/16)`` and
    ``F_b = diag(13/32, 3/32, 13/16)`` on the UNPADDED ``dim H(Q) = 1 + 1*2 =
    3``, the sector labels, and ``Delta_s = 0`` because the declaration is
    already on the lattice and ``def:emitnorm``'s first property then makes the
    normalizer the identity.
    """
    artifact = _emitted()
    assert PR_R3.emitted_target is not None
    assert PR_R3.sector_labels is not None
    assert artifact.target_descriptor.dimension == PR_R3.unpadded_dim

    # THE SECTOR LABELS, PINNED EXACTLY AS THE CODE EMITS THEM TODAY.
    #
    # NO SENTENCE OF THIS CONTRACT FIXES HOW A SECTOR LABEL IS SPELLED. The
    # freeze writes the same identity as ((nb,0),(nb,a),(nb,b)) -- the branch,
    # the preserved block, and one flag per letter, in that order -- while the
    # code writes the flag sectors with the joint outcome `(y,t)` that indexes
    # the flag basis, which at |T| = 1 is in bijection with the letter. The two
    # denote the same three sectors and differ only in the rendering.
    #
    # THE GAP IS FILED AS DF-37 on main and is not decided here. Until it is,
    # this test PINS THE CURRENT SPELLING rather than accepting any rendering
    # that happens to contain the frozen one: a containment test ('b' in 'ab')
    # admits strictly more than the identity this block claims, and would let
    # the emitted spelling drift without a failure. Asserting the tuple
    # verbatim makes ANY change to it visible, which is what a pin is for --
    # and a deliberate change is then a one-line edit here with DF-37 closed
    # beside it.
    #
    # THE GROUP IS THE INSTANCE'S. The freeze
    # writes ``nb``, reaching the case without branches by
    # declaring a DEGENERATE branching model, so even a reduction with no
    # branching carries the flat branch's name. This artifact is the FLAT
    # instance's: its physical system is the channel space itself, with no
    # register, so the group is ``C``. The three sectors, their ORDER and their
    # DIMENSIONS are the frozen ones; what differs is the register bookkeeping,
    # which is the whole of what the flat instance removes.
    assert artifact.target_descriptor.sectors.labels == (
        ("C", "0"),
        ("C", "a,t"),
        ("C", "b,t"),
    )
    # AND THE IDENTITY THE FREEZE FIXES, which survives any spelling: three
    # sectors, all on ONE branch, in the frozen order, the first the preserved
    # block and the other two the flags of the declared letters.
    labels = artifact.target_descriptor.sectors.labels
    assert len(labels) == len(PR_R3.sector_labels) == 3
    assert len({branch for branch, _ in labels}) == len(
        {branch for branch, _ in PR_R3.sector_labels}
    ) == 1
    assert labels[0][1] == "0" and PR_R3.sector_labels[0][1] == 0
    assert [part.split(",")[0] for _, part in labels[1:]] == [
        str(part) for _, part in PR_R3.sector_labels[1:]
    ]
    for letter, diagonal in PR_R3.emitted_target:
        # THE FROZEN VALUE IS THE DENSE DIAGONAL; the direct sum
        # is formed here from the emitted blocks.
        element = direct_sum(list(artifact.target_povm[(letter, "t")]))
        assert len(element) == len(diagonal)
        for index, expected in enumerate(diagonal):
            assert element[index][index].re == expected
            assert element[index][index].im == 0
            for other in range(len(diagonal)):
                if other != index:
                    assert element[index][other].re == 0
                    assert element[index][other].im == 0
    # def:emitnorm is the IDENTITY here: no rounding moved anything, no residue
    # was absorbed, no lift fired, and the displacement is exactly zero.
    (setting, _constructed, _rounded, residue, designated, delta) = PR_R3.emission[0]
    assert residue == 0 and designated is None and delta == 0
    assert PR_R3.lift_weight is None
    record = artifact.emission_record.blocks[0]
    assert record.already_on_lattice is True
    # Read off the per-class record; with the fidelity-first normalizer a
    # kept class has no step at all.
    assert str(record.classes[setting].status) == "kept"
    assert record.classes[setting].step is None
    assert record.displacement_squared == 0
    # eq:weightroute with eq:latdown moves nothing either: both routed weights
    # are already lattice numbers at kappa = 12.
    assert dict(PR_R3.routed_weights_hat) == dict(PR_R3.emitted_weights)
    emitted = dict(
        zip(
            artifact.wpfss_data.flag_basis,
            artifact.wpfss_data.weights,
            strict=True,
        )
    )
    assert emitted == dict(PR_R3.emitted_weights)
    assert artifact.wpfss_data.total == PR_R3.total_weight


@pytest.mark.contract
def test_the_outcome_correspondence_docks_as_the_identity_total_surjection() -> None:
    """(C2) needs ``gamma : V^ph -> V`` total and surjective; ``id`` is both."""
    artifact = _emitted()
    chain = docking.reduction_chain(
        artifact,
        PHYSICAL,
        sector_block_kind=FIXTURE_BLOCK_KIND,
    )
    flags = artifact.wpfss_data.flag_basis
    settings = docking.probe_settings_of(flags)
    labels = [docking.outcome_label(v, settings) for v in flags]
    assert dict(chain.outcome_correspondence) == dict(zip(labels, labels, strict=True))


# ---------------------------------------------------------------------------
#  The constraint list and the licence
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_the_encoded_route_docks_an_empty_list_and_no_licence() -> None:
    artifact = _emitted(route="encoded")
    assert (
        docking.constraint_entries(
            artifact,
            sector_block_kind=FIXTURE_BLOCK_KIND,
        )
        == ()
    )
    assert docking.attack_set_license(artifact) is None
    chain = docking.reduction_chain(
        artifact,
        PHYSICAL,
        sector_block_kind=FIXTURE_BLOCK_KIND,
    )
    last = chain.receiver_segment[-1]
    assert last.transported_constraints == ()
    assert last.license_slot_present is True
    assert last.license_slot_empty is True


@pytest.mark.contract
def test_the_licensed_route_docks_the_entries_and_the_licence() -> None:
    """The scalar right-hand spelling, which ``def:attset`` admits under either."""
    artifact = _emitted(route="licensed")
    entries = docking.constraint_entries(
        artifact,
        sector_block_kind=FIXTURE_BLOCK_KIND,
    )
    assert len(entries) == len(artifact.constraint_list) == 2
    for docked, original in zip(entries, artifact.constraint_list, strict=True):
        assert docked.relation is ConsumerRelation.GE
        assert docked.rhs == original.constant == 0
        assert docked.rhs_is_scalar
        # AT 1.0.0 THE OPERATOR CROSSES AS SECTOR BLOCKS (ADR-0008), and the
        # artifact carries it as one too,
        # so the conversion pairs the list it was handed with the sector map
        # and moves no number: the block dimensions on both sides ARE the
        # declared sector dimensions, and the blocks are equal one by one.
        dims = list(artifact.target_descriptor.sectors.dimensions)
        assert [len(block) for block in docked.operator.blocks] == dims
        assert [len(block) for block in original.operator] == dims
        assert len(docked.operator.blocks) == docked.operator.sector_map.count
        for left, right in zip(
            docked.operator.blocks, original.operator, strict=True
        ):
            assert equal(left, right)
    licence = docking.attack_set_license(artifact)
    assert licence is not None
    # The accepted contract version
    # (sec:conventions, bullet 13, written as
    # `proof-reductions@<contract_version>` OF THE ACCEPTED CONTRACT); the
    # docking adapter passes the string through unchanged.
    assert MATHEMATICAL_SPEC_VERSION in licence.supplier
    # The five things the record NAMES survive into the statement string.
    for fragment in (
        "thm:licence",
        "eq:certificate",
        "A-RECV",
        "receiver@0.9.0",
        "untrusted",
        "A_CList",
    ):
        assert fragment in licence.statement, fragment
    chain = docking.reduction_chain(
        artifact,
        PHYSICAL,
        sector_block_kind=FIXTURE_BLOCK_KIND,
    )
    last = chain.receiver_segment[-1]
    assert len(last.transported_constraints) == 2
    assert last.license_slot_empty is False


@pytest.mark.contract
def test_trusted_mode_docks_c_k_tau_a_from_the_declaration_s_own_marginal() -> None:
    """``sec:outputs`` at 1.0.0: THE SCALAR CROSSES AND THE CONSUMER BUILDS THE REST.

    THE ``constraint_list`` ROW at 1.0.0: every entry "carries A REAL SCALAR ``c_k`` as
    its third
    component, IN BOTH SOURCE MODES", and in trusted-source mode "the entry
    declares the real ``c_k`` and THE RIGHT-HAND SIDE ``Theta_k := c_k tau_A``
    IS CONSTRUCTED BY THE CONSUMER from it and from THE CONSUMER'S OWN
    ``tau_A``". "**THIS MODULE EMITS NO OPERATOR ``Theta_k`` IN EITHER MODE**":
    an entry carrying a Hermitian ``Theta_k`` is a ``general`` entry at the
    consumer, "admissible input but NEVER LICENSED", so the 0.3.0 adapter --
    which multiplied ``c_k`` by a caller-supplied marginal and produced exactly
    that -- converted a licensed list into an unlicensed one at the boundary.
    The ``alice_marginal`` parameter is therefore gone, and with it the two
    refusals built around it. Theorem ``thm:licence`` (iv) is unchanged and is
    why: "the identification of the right-hand side is THE DECLARATION'S AND
    NOT THIS CONTRACT'S".
    """
    untrusted = _emitted(route="licensed", mode=SourceMode.UNTRUSTED)
    trusted = _emitted(route="licensed", mode=SourceMode.TRUSTED)
    for artifact in (trusted, untrusted):
        entries = docking.constraint_entries(
            artifact, sector_block_kind=FIXTURE_BLOCK_KIND
        )
        assert len(entries) == len(artifact.constraint_list)
        for docked, original in zip(entries, artifact.constraint_list, strict=True):
            # A REAL SCALAR IN BOTH MODES, and it is the artifact's own c_k.
            assert docked.rhs_is_scalar
            assert docked.rhs == Fraction(original.constant)
    # TAU_A stays the CALLER'S: nothing here reads it, and Remark
    # rem:notlicensed (a) is why -- "nothing here licenses declaring tau_A".
    assert len(TAU_A) == 2
    assert consumer_is_hermitian(_consumer(TAU_A))
    assert consumer_scale is not None
    assert ConsumerCx is not None


@pytest.mark.contract
def test_the_docked_trusted_entries_pass_the_consumer_s_own_v6_clauses() -> None:
    """The consumer's ``check_v6``, clause for clause, and THE ARRIVING TAG.

    The protocol compiler's own ``check_v6`` reads the tag off
    the datum -- "a real scalar spells ``homogeneous``" -- and, at 1.0.0,
    ALSO compares it with the tag the arriving entry declares: "where an
    ARRIVING entry ... carries an explicit tag field, V6 compares that field
    with the type of the datum it names and A DISAGREEMENT IS A REFUSAL".

    So this test asserts BOTH halves at once: the emitted ``form`` reaches the
    consumer's
    ``arriving_tag`` slot, and it AGREES with the type the consumer reads. An
    adapter that dropped the tag left the slot empty and the cross-check with
    nothing to compare, which is the inference ``sec:outputs`` forbids: "the
    docking is by key and NOTHING ABOUT THE FORM IS INFERRED AT EITHER END."
    """
    trusted = _emitted(route="licensed", mode=SourceMode.TRUSTED)
    for entry in docking.constraint_entries(
        trusted, sector_block_kind=FIXTURE_BLOCK_KIND
    ):
        # 1.0.0: a REAL SCALAR in both modes, so the type spells `homogeneous`.
        assert isinstance(entry.rhs, Fraction)
        assert entry.tag is RhsTag.HOMOGENEOUS
        # The DECLARED tag crossed, and V6's comparison has both sides.
        assert entry.arriving_tag is RhsTag.HOMOGENEOUS
        assert entry.arriving_tag is entry.tag
    # UNTRUSTED MODE: the scalar form is "THE ONLY ONE THAT EXISTS THERE" and
    # this contract fixes NO TAG STRING for it, so the entry crosses untagged
    # and the consumer's own rule applies -- "an entry carrying no tag field is
    # NOT REFUSED: the tag is the type and is read off it".
    untrusted = _emitted(route="licensed", mode=SourceMode.UNTRUSTED)
    for entry in docking.constraint_entries(
        untrusted, sector_block_kind=FIXTURE_BLOCK_KIND
    ):
        assert isinstance(entry.rhs, Fraction)
        assert entry.tag is RhsTag.HOMOGENEOUS
        assert entry.arriving_tag is None
    # And the chain docks end to end, the transported entries carrying scalars.
    chain = docking.reduction_chain(
        trusted, PHYSICAL, sector_block_kind=FIXTURE_BLOCK_KIND
    )
    last = chain.receiver_segment[-1]
    assert len(last.transported_constraints) == len(trusted.constraint_list)
    assert all(entry.rhs_is_scalar for entry in last.transported_constraints)
    report = chain_report(
        trusted, PHYSICAL, sector_block_kind=FIXTURE_BLOCK_KIND
    )
    assert report.failing_condition is None
    assert consumer_dimension is not None


@pytest.mark.contract
def test_the_limitations_are_reported_rather_than_discovered() -> None:
    """Every limitation the module docstring names is machine-readable."""
    encoded = docking.docking_limitations(_emitted())
    assert any("def:system-setting" in item for item in encoded)
    assert any("channel=None" in item for item in encoded)
    assert any("reachable-set statement" in item for item in encoded)
    assert any("licence structure" in item for item in encoded)
    licensed = docking.docking_limitations(_emitted(route="licensed"))
    assert len(licensed) > len(encoded)


# ---------------------------------------------------------------------------
#  Off the package surface
# ---------------------------------------------------------------------------


#: The frozen WIRE RECORDS a consumer reads a docked chain in. They live in
#: :mod:`certiqs_key.domain` and :mod:`certiqs_key.foundations`, not in the
#: protocol compiler's package: NO MODULE IMPORTS THE COMPILER AT ALL, and
#: what is worth a test is that ONE FILE of this package converts into those
#: records.
WIRE_RECORDS = ("certiqs_key.domain.constraints", "certiqs_key.foundations.blocks")

#: THE CONSUMER'S OWN SPELLING, as against the shared operator format. The
#: records in ``certiqs_key.domain.constraints`` -- ``ConstraintEntry`` with its
#: ``RhsTag``, ``AttackSetLicense``, the word-spelled ``Relation`` -- are the
#: CONSUMER'S types, and
#: converting into them is what the one sanctioned exception is about.
CONSUMER_RECORDS = ("certiqs_key.domain.constraints",)


@pytest.mark.contract
def test_docking_is_the_only_file_that_builds_the_consumer_s_records() -> None:
    """One sanctioned exception, one file (PRINCIPLES.md section 4).

    ``factors.py`` joins ``docking.py`` in naming
    ``certiqs_key.foundations.blocks``, AND THE RULE IS NOT WEAKENED -- it is
    split into the two things that module holds.

    ``foundations.blocks`` carries TWO kinds of type. One is the shared OPERATOR
    format of spec/architecture.md 2.9 -- ``SectorStructure``,
    ``BlockOperator``, ``SectorFactor``,
    ``FactorisedSectorMap`` and ``SystemTag`` -- which is the repository's own
    format for a sector-block operator and is what ``thm:emitted-product``'s
    product sector map IS (``domain.families.FactorisedFamily`` likewise). The
    other is the consumer's wire spelling, and that one lives in
    ``domain.constraints``: :data:`CONSUMER_RECORDS`, asserted below to be
    named by ``docking.py`` and by nothing else. The factor emission declares the shared
    format and converts
    into no consumer record.
    """
    naming: list[str] = []
    consumer: list[str] = []
    for path in sorted(PACKAGE.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                imported.add(node.module)
        if any(name in WIRE_RECORDS for name in imported):
            naming.append(path.name)
        if any(name in CONSUMER_RECORDS for name in imported):
            consumer.append(path.name)
    assert naming == ["docking.py", "factors.py"]
    assert consumer == ["docking.py"]


@pytest.mark.contract
def test_importing_the_package_still_imports_no_consumer() -> None:
    """The docking module exists AND is not on the package surface.

    The records a docked chain travels in are frozen shared types
    (``certiqs_key.domain``), which every module may import and which
    ``reasons`` reaches for the link status and the link stage -- so there is
    no consumer package to keep off the graph. What is worth a test is that
    the DOCKING MODULE is not on the package surface and
    that importing the package pulls in no array library; that ONE FILE
    builds the consumer's records is the test above.
    """
    program = (
        "import sys\n"
        "import certiqs_key.reductions\n"
        "import certiqs_key.reductions.artifact\n"
        "import certiqs_key.reductions.emit\n"
        "assert 'certiqs_key.reductions.docking' not in sys.modules\n"
        "assert not any(n == 'numpy' or n.startswith('numpy.') for n in sys.modules)\n"
        "import certiqs_key.reductions.docking\n"
        "print('ok')\n"
    )
    completed = subprocess.run(
        [sys.executable, "-c", program],
        capture_output=True,
        text=True,
        check=True,
    )
    assert completed.stdout.strip() == "ok"


@pytest.mark.contract
def test_the_docking_modifies_nothing_on_either_side() -> None:
    """One direction only: no function here writes to a consumer's record.

    EVERY ENTRY POINT of this module is exercised below, including
    ``target_descriptor`` and ``sector_projectors``.
    """
    artifact = _emitted(route="licensed")
    before = artifact.as_machine_record()
    docking.reduction_chain(
        artifact,
        PHYSICAL,
        sector_block_kind=FIXTURE_BLOCK_KIND,
    )
    docking.constraint_entries(
        artifact,
        sector_block_kind=FIXTURE_BLOCK_KIND,
    )
    docking.attack_set_license(artifact)
    docking.target_descriptor(artifact, sector_block_kind=FIXTURE_BLOCK_KIND)
    projectors = docking.sector_projectors(
        artifact, sector_block_kind=FIXTURE_BLOCK_KIND
    )
    docking.docking_limitations(artifact)
    after = artifact.as_machine_record()
    assert before == after
    # WHAT sector_projectors RETURNS, asserted and not merely reached:
    # one BlockOperator per sector, in
    # the declared order, carrying the declared block kind, and each one
    # `1_{d_s}` on its own block and zero on every other -- written out here
    # rather than read back from the code.
    sectors = artifact.target_descriptor.sectors
    assert len(projectors) == len(sectors.labels)
    for position, projector in enumerate(projectors):
        assert projector.sector_map.block_kind is FIXTURE_BLOCK_KIND
        assert list(projector.sector_map.dims) == list(sectors.dimensions)
        for index, block in enumerate(projector.blocks):
            dim = sectors.dimensions[index]
            assert equal(block, identity(dim) if index == position else zeros(dim))
    # And the emitted matrices are untouched by the conversion, block by block.
    for outcome, element in artifact.target_povm.items():
        for left, right in zip(element, artifact.target_povm[outcome], strict=True):
            assert equal(left, right)


@pytest.mark.contract
def test_an_encoded_artifact_docks_with_the_declaration_s_marginal_supplied() -> None:
    """The encoded route carries NO entry: a supplied tau_A is unused, not refused.

    The empty entry list and the link's empty transported set need no
    consumer verdict; only the consumer's own verdict on the docked chain
    does.
    """
    encoded = _emitted(route="encoded", mode=SourceMode.TRUSTED)
    assert (
        docking.constraint_entries(
            encoded,
            sector_block_kind=FIXTURE_BLOCK_KIND,
        )
        == ()
    )
    chain = docking.reduction_chain(
        encoded,
        PHYSICAL,
        sector_block_kind=FIXTURE_BLOCK_KIND,
    )
    assert chain.receiver_segment[-1].transported_constraints == ()


@pytest.mark.contract
def test_an_encoded_artifact_passes_the_consumer_s_own_chain_check() -> None:
    """The consumer's verdict on an encoded artifact with a trusted marginal."""
    report = chain_report(
        _emitted(route="encoded", mode=SourceMode.TRUSTED),
        PHYSICAL,
        sector_block_kind=FIXTURE_BLOCK_KIND,
    )
    assert report.failing_condition is None

