"""Declared-data parts of premises, decided: the Band-A route and d_A = 1.

``protocol-compiler/req:band-a-ideal-receiver``: a specification the record
puts on the Band-A route is refused with ``band_a_outside_ideal_receiver``
unless it declares one measured factor, a two-dimensional receiver system
(and, in trusted-source mode, a two-dimensional transmitted system) and a
projective family as presented. The route is recognised on the record:
empty source segment, emitted (joint) sector set a singleton, and for some
measured factor one exact identity link whose channel, where supplied, is
exactly the identity map.

``protocol-compiler/req:band-a-identity-link``: on the route, the one link
must supply its channel as data and its outcome correspondence must be the
identity on ``V = V^ph``, or the specification is refused with
``band_a_link_not_identity``; (C4) then decides that the link delivers the
declared family, and a target POVM that is not it is refused by (C4).

``protocol-compiler/req:da1-source-identity``: in trusted-source mode at
``d_A = 1`` the identity ``sigma_x = m_x sum_y sigma_y`` is decided for every
letter, exactly, and a failure is ``da1_source_identity_failed``; in
untrusted-source mode nothing is compared.

Each refusal below is one that would not happen were the decision absent, and
each has a control on which the same specification shape passes.
"""

from __future__ import annotations

from dataclasses import replace
from fractions import Fraction as F

import pytest
from protocol_blocks import source_part

from certiqs_key.domain.chain import (
    ChainLink,
    LinkStage,
    LinkStatus,
    ReductionChain,
    Side,
    SystemDescriptor,
)
from certiqs_key.foundations.blocks import (
    PRODUCT_LABEL_SEPARATOR,
    BlockKind,
    BlockOperator,
    Label,
    SectorStructure,
)
from certiqs_key.foundations.exact import Cx, Matrix, identity, matrix
from certiqs_key.protocol_compiler import (
    ConditionOutcome,
    DirectPovm,
    Party,
    PartyPartition,
    PovmPresentation,
    ProtocolSpecification,
    PublicChoices,
    PublicPart,
    ReceiverPart,
    RefusalReason,
    Sifting,
    SourcePart,
    SpecConstraints,
    band_a_chain,
    band_a_route,
    compile_specification,
    decide_band_a_ideal_receiver,
    decide_band_a_identity_link,
    decide_da1_source_identity,
    default_party_partition,
    weighted_family,
)
from certiqs_key.protocol_compiler.declared_premises import (
    channel_is_exactly_identity,
    is_band_a,
)
from certiqs_key.transmitter.artifact import (
    SourceSpecification,
    TransmitterArtifact,
    emit_artifact,
)
from certiqs_key.transmitter.presentation import EnsemblePresentation
from certiqs_key.transmitter.reasons import SourceMode

pytestmark = pytest.mark.contract

HALF = F(1, 2)
QUARTER = F(1, 4)
Z0 = matrix(((1, 0), (0, 0)))
Z1 = matrix(((0, 0), (0, 1)))
MIXED = matrix(((HALF, 0), (0, HALF)))
X_PAIR: tuple[Label, ...] = ("x0", "x1")
V_PAIR: tuple[Label, ...] = ("v0", "v1")
PROJECTIVE = DirectPovm(alphabet=V_PAIR, elements={"v0": Z0, "v1": Z1})
#: An admissible qubit POVM that is not projective: two half Z effects and an
#: unresolved one. Every entry is binary64 and the declared-order sum is exact.
THREE_OUTCOME = DirectPovm(
    alphabet=("0", "1", "n"),
    elements={
        "0": matrix(((HALF, 0), (0, 0))),
        "1": matrix(((0, 0), (0, HALF))),
        "n": matrix(((HALF, 0), (0, HALF))),
    },
)


def _sectors(dim: int) -> SectorStructure:
    return SectorStructure(
        labels=("s0",), dims=(dim,), block_kind=BlockKind.PROOF_SECTOR
    )


def _target(name: str, dim: int) -> SystemDescriptor:
    return SystemDescriptor(
        name=name,
        dim=dim,
        side=Side.RECEIVER,
        sectors=(("s0", dim),),
        sector_block_kind=BlockKind.PROOF_SECTOR,
    )


def _resolved(
    physical: PovmPresentation,
) -> tuple[tuple[Label, ...], dict[Label, Matrix]]:
    if isinstance(physical, DirectPovm):
        return physical.alphabet, dict(physical.elements)
    weighted = weighted_family(physical)
    return weighted.alphabet, dict(weighted.elements)


def _band_a(
    physical: PovmPresentation,
    dim: int = 2,
    *,
    name: str = "Q",
    channel: tuple[Matrix, ...] | None = None,
    supply_channel: bool = True,
) -> ReductionChain:
    """Return the Band-A chain of def:banda (b) carrying ``physical`` as its target."""
    alphabet, elements = _resolved(physical)
    chain = band_a_chain(_target(name, dim))
    link = replace(
        chain.receiver_segment[0],
        target_alphabet=alphabet,
        target_povm={
            label: BlockOperator.of(_sectors(dim), (elements[label],))
            for label in alphabet
        },
    )
    if channel is not None:
        link = replace(link, channel=channel)
    elif not supply_channel:
        link = replace(link, channel=None)
    return replace(
        chain,
        receiver_segment=(link,),
        outcome_correspondence={label: label for label in alphabet},
    )


def _squashing(physical: PovmPresentation, *, name: str = "Q") -> ReductionChain:
    """Return one exact link B -> Q with different descriptors: not Band A."""
    alphabet, elements = _resolved(physical)
    return ReductionChain(
        source_segment=(),
        receiver_segment=(
            ChainLink(
                link_id="L1",
                segment=LinkStage.RECEIVER,
                link_type="wpfss",
                source_descriptor=SystemDescriptor(name="B", dim=2, side=Side.RECEIVER),
                target_descriptor=_target(name, 2),
                status=LinkStatus.EXACT,
                target_alphabet=alphabet,
                target_povm={
                    label: BlockOperator.of(_sectors(2), (elements[label],))
                    for label in alphabet
                },
            ),
        ),
        outcome_correspondence=dict(zip(alphabet, alphabet, strict=True)),
    )


def _public(x_alphabet: tuple[Label, ...], v_alphabet: tuple[Label, ...]) -> PublicPart:
    announcements = tuple(f"b_{label}" for label in v_alphabet)
    alice_announcements = tuple(f"a_{label}" for label in x_alphabet)
    classes = [(c_a, c_b) for c_a in alice_announcements for c_b in announcements]
    return PublicPart(
        partition=default_party_partition(x_alphabet, v_alphabet),
        announce_alice=dict(zip(x_alphabet, alice_announcements, strict=True)),
        announce_bob=dict(zip(v_alphabet, announcements, strict=True)),
        alice_announcement_alphabet=alice_announcements,
        bob_announcement_alphabet=announcements,
        sifting=dict.fromkeys(classes, Sifting.PASS),
        key_rule={
            (readout, kappa): index % 2
            for index, readout in enumerate(x_alphabet)
            for kappa in classes
        },
        holder=Party.ALICE,
        key_alphabet=(0, 1) if len(x_alphabet) > 1 else (0,),
        acceptance_alphabet=("g",),
        accept_statistic=dict.fromkeys(classes, "g"),
    )


def _untrusted_source(transmitted_dim: int = 2) -> SourcePart:
    """Return an untrusted d_A = 2 source with two letters (no certificate needed)."""
    return source_part(
        alphabet=X_PAIR,
        alice_dim=2,
        alice_povm=DirectPovm(alphabet=X_PAIR, elements={"x0": Z0, "x1": Z1}),
        transmitted_dim=transmitted_dim,
        signal_weights=dict.fromkeys(X_PAIR, HALF),
        signal_states=dict.fromkeys(
            X_PAIR,
            identity(transmitted_dim)
            if transmitted_dim == 1
            else _mixed(transmitted_dim),
        ),
    )


def _mixed(dim: int) -> Matrix:
    return matrix(
        tuple(
            tuple(F(1, dim) if row == column else 0 for column in range(dim))
            for row in range(dim)
        )
    )


def _specification(
    physical: PovmPresentation,
    *,
    dim: int = 2,
    chain: ReductionChain | None = None,
    source: SourcePart | None = None,
) -> ProtocolSpecification:
    """Return a one-factor Band-A specification presenting ``physical``."""
    used_source = source if source is not None else _untrusted_source()
    alphabet, _ = _resolved(physical)
    return ProtocolSpecification(
        source=used_source,
        receiver=ReceiverPart(physical_dim=dim, physical_povm=physical),
        public=_public(used_source.alphabet, alphabet),
        sectors=_sectors(dim),
        chain=chain if chain is not None else _band_a(physical, dim),
        constraints=SpecConstraints(),
    )


def _refusal(specification: ProtocolSpecification) -> tuple[RefusalReason, str]:
    result = compile_specification(specification)
    assert result.refusal is not None
    return result.refusal.reason, result.refusal.detail


# ===========================================================================
#  req:band-a-ideal-receiver
# ===========================================================================


def test_a_projective_qubit_family_on_band_a_compiles_and_names_a_ideal() -> None:
    """The control: one factor, qubits, projectors -- the route is taken."""
    specification = _specification(PROJECTIVE)
    assert band_a_route(specification)
    result = compile_specification(specification)
    assert result.refusal is None, result.refusal
    assert "ideal_qubit_receiver" in result.assumption_ledger


def test_a_non_projective_direct_family_on_band_a_is_refused_at_iii() -> None:
    """Admissible but not projective: element 1 of the declared order fails."""
    specification = _specification(THREE_OUTCOME)
    assert band_a_route(specification)
    reason, detail = _refusal(specification)
    assert reason is RefusalReason.BAND_A_OUTSIDE_IDEAL_RECEIVER
    assert "clause (iii)" in detail and "element 1" in detail
    assert "F^ph_0" in detail


def test_the_same_family_off_band_a_is_not_refused_by_the_requirement() -> None:
    """Through a squashing link (not Band A) the same family is not this rule's."""
    specification = _specification(THREE_OUTCOME, chain=_squashing(THREE_OUTCOME))
    assert not band_a_route(specification)
    assert decide_band_a_ideal_receiver(specification) is None
    result = compile_specification(specification)
    assert (
        result.refusal is None
        or result.refusal.reason is not RefusalReason.BAND_A_OUTSIDE_IDEAL_RECEIVER
    )


def _choices(x_family: dict[Label, Matrix]) -> PublicChoices:
    return PublicChoices(
        party=Party.BOB,
        choices=("Z", "X"),
        weights={"Z": HALF, "X": HALF},
        conditional_alphabets={"Z": ("0", "1"), "X": tuple(x_family)},
        conditional_elements={"Z": {"0": Z0, "1": Z1}, "X": x_family},
    )


def test_a_choice_weighted_family_is_read_per_conditional_family() -> None:
    """The weighted family is not projective; each conditional family is.

    The control: Z and X projectors behind a public choice of weight one half.
    The weighted elements ``Z0 / 2`` are not projectors, and the route is
    taken anyway, because clause (iii) reads every conditional family.
    """
    plus = matrix(((HALF, HALF), (HALF, HALF)))
    minus = matrix(((HALF, -HALF), (-HALF, HALF)))
    specification = _specification(_choices({"+": plus, "-": minus}))
    assert band_a_route(specification)
    assert decide_band_a_ideal_receiver(specification) is None
    result = compile_specification(specification)
    assert result.refusal is None, result.refusal


def test_a_non_projective_conditional_family_is_refused_naming_choice_and_index() -> (
    None
):
    """An X family of two half identities: a POVM, and not a projective one."""
    specification = _specification(_choices({"+": MIXED, "-": MIXED}))
    reason, detail = _refusal(specification)
    assert reason is RefusalReason.BAND_A_OUTSIDE_IDEAL_RECEIVER
    assert "clause (iii)" in detail
    assert "choice value 'X'" in detail and "element 1" in detail


def test_a_three_dimensional_receiver_on_band_a_is_refused_at_ii() -> None:
    family = DirectPovm(
        alphabet=V_PAIR,
        elements={
            "v0": matrix(((1, 0, 0), (0, 0, 0), (0, 0, 0))),
            "v1": matrix(((0, 0, 0), (0, 1, 0), (0, 0, 1))),
        },
    )
    specification = _specification(family, dim=3)
    assert band_a_route(specification)
    reason, detail = _refusal(specification)
    assert reason is RefusalReason.BAND_A_OUTSIDE_IDEAL_RECEIVER
    assert "clause (ii)" in detail and "dimension 3" in detail


def test_a_one_dimensional_receiver_on_band_a_is_refused_at_ii() -> None:
    """Clause (ii)'s first half below two: a one-outcome family on dimension one."""
    family = DirectPovm(alphabet=("v0",), elements={"v0": identity(1)})
    specification = _specification(family, dim=1)
    assert band_a_route(specification)
    refusal = decide_band_a_ideal_receiver(specification)
    assert refusal is not None
    assert refusal.reason is RefusalReason.BAND_A_OUTSIDE_IDEAL_RECEIVER
    assert "clause (ii)" in refusal.detail and "dimension 1" in refusal.detail
    reason, _ = _refusal(specification)
    assert reason is RefusalReason.BAND_A_OUTSIDE_IDEAL_RECEIVER


def _trusted_d1_source(
    states: dict[Label, Matrix],
    weights: dict[Label, F],
    alice: dict[Label, Matrix],
    *,
    transmitted_dim: int = 2,
    mode: SourceMode = SourceMode.TRUSTED,
    choices: PublicChoices | None = None,
) -> SourcePart:
    """Return a ``d_A = 1`` source part emitted by the transmitter itself."""
    alphabet = tuple(states)
    artifact = emit_artifact(
        SourceSpecification(
            signal_alphabet=alphabet,
            transmitted_dim=transmitted_dim,
            signal_weights=weights,
            signal_states=states,
            alice_dim=1,
            alice_povm=alice,
            source_mode_request=mode,
        )
    ).require()
    assert artifact.alice_dim == 1
    assert artifact.source_mode is mode
    return SourcePart(artifact=artifact, alice_choices=choices)


def test_a_trusted_transmitted_system_of_dimension_three_is_refused_at_ii() -> None:
    """Clause (ii)'s second half binds in trusted-source mode only."""
    one = matrix(((1, 0, 0), (0, 0, 0), (0, 0, 0)))
    trusted = _trusted_d1_source(
        {"x0": one}, {"x0": F(1)}, {"x0": identity(1)}, transmitted_dim=3
    )
    reason, detail = _refusal(_specification(PROJECTIVE, source=trusted))
    assert reason is RefusalReason.BAND_A_OUTSIDE_IDEAL_RECEIVER
    assert "clause (ii)" in detail and "transmitted system" in detail
    untrusted = _trusted_d1_source(
        {"x0": one},
        {"x0": F(1)},
        {"x0": identity(1)},
        transmitted_dim=3,
        mode=SourceMode.UNTRUSTED,
    )
    assert (
        decide_band_a_ideal_receiver(_specification(PROJECTIVE, source=untrusted))
        is None
    )


def _factor_public(x_alphabet: tuple[Label, ...]) -> PublicPart:
    """Return the factor projection on ``V_PAIR x V_PAIR``: each party reads one.

    A two-factor specification's emitted alphabet is the product one,
    ``v0__v0`` and so on, so its party partition tabulates the readouts there;
    :func:`_public`'s default partition tabulates the one-factor alphabet and
    would be malformed past the decisions this file tests.
    """
    sep = PRODUCT_LABEL_SEPARATOR
    v = tuple(f"{a}{sep}{b}" for a in V_PAIR for b in V_PAIR)
    partition = PartyPartition(
        alice_readout={(x, w): w.split(sep)[0] for x in x_alphabet for w in v},
        bob_readout={(x, w): w.split(sep)[1] for x in x_alphabet for w in v},
        alice_readout_alphabet=V_PAIR,
        bob_readout_alphabet=V_PAIR,
        sector_factor_parties=((Party.ALICE,), (Party.BOB,)),
    )
    ca = tuple(f"a_{label}" for label in V_PAIR)
    cb = tuple(f"b_{label}" for label in V_PAIR)
    classes = [(p, q) for p in ca for q in cb]
    return PublicPart(
        partition=partition,
        announce_alice=dict(zip(V_PAIR, ca, strict=True)),
        announce_bob=dict(zip(V_PAIR, cb, strict=True)),
        alice_announcement_alphabet=ca,
        bob_announcement_alphabet=cb,
        sifting=dict.fromkeys(classes, Sifting.PASS),
        key_rule={(r, k): i % 2 for i, r in enumerate(V_PAIR) for k in classes},
        holder=Party.ALICE,
        key_alphabet=(0, 1),
        acceptance_alphabet=("g",),
        accept_statistic=dict.fromkeys(classes, "g"),
    )


def _two_factors(
    first_chain: ReductionChain, second_chain: ReductionChain
) -> ProtocolSpecification:
    """Return a two-factor specification (the general format) on the two chains.

    Its public part is :func:`_factor_public`, so the specification is well
    formed past the route and identity decisions, and a test that expects
    one of them to refuse would see compilation proceed were it absent.
    """
    base = replace(
        _specification(PROJECTIVE, chain=first_chain), public=_factor_public(X_PAIR)
    )
    second = ReceiverPart(
        physical_dim=2,
        physical_povm=PROJECTIVE,
        party=Party.BOB,
        factor_label="f1",
        chain=second_chain,
    )
    return replace(
        base,
        receiver=replace(base.receiver, party=Party.ALICE, factor_label="f0"),
        further_receiver_factors=(second,),
    )


def test_two_band_a_shaped_factors_are_refused_at_i() -> None:
    specification = _two_factors(
        _band_a(PROJECTIVE, name="Q_a"), _band_a(PROJECTIVE, name="Q_b")
    )
    assert specification.is_general_format
    assert band_a_route(specification)
    reason, detail = _refusal(specification)
    assert reason is RefusalReason.BAND_A_OUTSIDE_IDEAL_RECEIVER
    assert "clause (i)" in detail and "2 measured factors" in detail


def test_an_identity_shaped_factor_other_than_the_first_puts_it_on_the_route() -> None:
    """The link test reads every factor, not only the first (the F-4 case)."""
    specification = _two_factors(
        _squashing(PROJECTIVE, name="Q_a"), _band_a(PROJECTIVE, name="Q_b")
    )
    assert not is_band_a(_squashing(PROJECTIVE, name="Q_a"), _sectors(2))
    assert band_a_route(specification)
    reason, detail = _refusal(specification)
    assert reason is RefusalReason.BAND_A_OUTSIDE_IDEAL_RECEIVER
    assert "clause (i)" in detail


def test_a_joint_sector_set_that_is_not_one_keeps_two_factors_off_the_route() -> None:
    """Two sectors at one factor: the joint set is not a singleton."""
    two = SectorStructure(
        labels=("s0", "s1"), dims=(1, 1), block_kind=BlockKind.PROOF_SECTOR
    )
    split = DirectPovm(
        alphabet=V_PAIR,
        elements={"v0": Z0, "v1": Z1},
    )
    chain = _band_a(split, name="Q_a")
    (link,) = chain.receiver_segment
    target = SystemDescriptor(
        name="Q_a",
        dim=2,
        side=Side.RECEIVER,
        sectors=(("s0", 1), ("s1", 1)),
        sector_block_kind=BlockKind.PROOF_SECTOR,
    )
    two_sector = replace(
        chain,
        receiver_segment=(
            replace(
                link,
                source_descriptor=target,
                target_descriptor=target,
                target_povm={
                    "v0": BlockOperator.of(two, (matrix(((1,),)), matrix(((0,),)))),
                    "v1": BlockOperator.of(two, (matrix(((0,),)), matrix(((1,),)))),
                },
            ),
        ),
    )
    specification = _two_factors(two_sector, _band_a(PROJECTIVE, name="Q_b"))
    assert not band_a_route(specification)
    assert decide_band_a_ideal_receiver(specification) is None


def _ensemble_source(sectors: int) -> SourcePart:
    """Return a trusted ensemble-presentation source on a qubit ``A^v``.

    With ``sectors = 2`` the virtual sector structure is ``{t0, t1}`` of
    dimensions ``(1, 1)``, so Alice's sector set ``T``, a copy of it, has two
    sectors; with ``sectors = 1`` it is one sector of dimension two. Either
    way the specification is in the general format and the ensemble is
    ``{1/2, |0><0|}, {1/2, |1><1|}``.
    """
    zero = matrix(((0,),))
    if sectors == 2:
        structure = SectorStructure(
            labels=("t0", "t1"), dims=(1, 1), block_kind=BlockKind.PROOF_SECTOR
        )
        blocks = {"x0": (ONE_BY_ONE_HALF, zero), "x1": (zero, ONE_BY_ONE_HALF)}
    else:
        structure = SectorStructure(
            labels=("t0",), dims=(2,), block_kind=BlockKind.PROOF_SECTOR
        )
        blocks = {
            "x0": (matrix(((HALF, 0), (0, 0))),),
            "x1": (matrix(((0, 0), (0, HALF))),),
        }
    artifact = emit_artifact(
        SourceSpecification(
            signal_alphabet=X_PAIR,
            transmitted_dim=2,
            signal_weights=dict.fromkeys(X_PAIR, HALF),
            signal_states={"x0": Z0, "x1": Z1},
            source_mode_request=SourceMode.TRUSTED,
            ensemble_presentation=EnsemblePresentation(
                virtual_sectors=structure, weighted_blocks=blocks
            ),
        )
    ).require()
    return SourcePart(artifact=artifact)


@pytest.mark.parametrize(("sectors", "on_route"), [(1, True), (2, False)])
def test_several_alice_sectors_keep_an_identity_link_factor_off_the_route(
    sectors: int, on_route: bool
) -> None:
    """The joint set ``T x S`` is not a singleton where ``T`` has two sectors.

    One measured factor with the identity link over one sector: with one Alice
    sector the specification is on the route (the control), and with two it
    is not, so A-IDEAL is not emitted and the inherited receiver rows are.
    """
    specification = replace(
        _specification(PROJECTIVE), source=_ensemble_source(sectors)
    )
    assert specification.is_general_format
    assert specification.source.alice_sectors.count == sectors
    assert band_a_route(specification) is on_route
    assert decide_band_a_ideal_receiver(specification) is None
    result = compile_specification(specification)
    assert result.refusal is None, result.refusal
    assert ("ideal_qubit_receiver" in result.assumption_ledger) is on_route


def test_the_channel_test_is_exact_identity_where_supplied() -> None:
    """A Kraus set is the identity iff each K_k = c_k 1 and sum |c_k|^2 = 1."""
    link = _band_a(PROJECTIVE).receiver_segment[0]
    three_fifths = matrix(((F(3, 5), 0), (0, F(3, 5))))
    four_fifths_i = matrix(((Cx(F(0), F(4, 5)), 0), (0, Cx(F(0), F(4, 5)))))
    assert channel_is_exactly_identity(replace(link, channel=None))
    assert channel_is_exactly_identity(replace(link, channel=(identity(2),)))
    assert channel_is_exactly_identity(
        replace(link, channel=(three_fifths, four_fifths_i))
    )
    pauli_z = matrix(((1, 0), (0, -1)))
    assert not channel_is_exactly_identity(replace(link, channel=(pauli_z,)))
    assert not channel_is_exactly_identity(replace(link, channel=(three_fifths,)))
    flip = matrix(((0, 1), (1, 0)))
    assert not channel_is_exactly_identity(replace(link, channel=(flip,)))
    assert not channel_is_exactly_identity(replace(link, channel=(identity(3),)))


def test_a_non_identity_channel_takes_a_link_off_the_route() -> None:
    """Equal descriptors are not enough where the link supplies a channel."""
    pauli_z = matrix(((1, 0), (0, -1)))
    chain = _band_a(THREE_OUTCOME, channel=(pauli_z,))
    assert not is_band_a(chain, _sectors(2))
    specification = _specification(THREE_OUTCOME, chain=chain)
    assert not band_a_route(specification)
    assert decide_band_a_ideal_receiver(specification) is None
    # With no channel supplied the link is identity-shaped and on the route.
    unsupplied = _specification(
        THREE_OUTCOME, chain=_band_a(THREE_OUTCOME, supply_channel=False)
    )
    assert band_a_route(unsupplied)
    assert decide_band_a_ideal_receiver(unsupplied) is not None


def test_the_shipped_band_a_specifications_are_admitted() -> None:
    """Trusted, d_A = 2, a choice-weighted projective receiver: on the route.

    Every shipped Band-A specification: the BB84 instance (which a lowered
    protocol document with a declared POVM equals, tests/unit/
    test_declared_lowering.py) and the Y-basis conjugation example. Each
    supplies the identity channel as data with the identity outcome
    correspondence, so req:band-a-identity-link passes and (C4) is decided.
    """
    from instances.bb84.specification import (
        bb84_specification,
        conjugation_example_specification,
    )

    for specification in (
        bb84_specification(HALF, HALF, HALF, HALF),
        conjugation_example_specification(),
    ):
        assert band_a_route(specification)
        assert decide_band_a_ideal_receiver(specification) is None
        physical, _ = _resolved(specification.receiver.physical_povm)
        assert decide_band_a_identity_link(specification, physical) is None
        result = compile_specification(specification)
        assert result.refusal is None, result.refusal
        assert result.chain is not None
        assert result.chain.verdict("C4") is ConditionOutcome.HOLDS
        assert "reduction_chain_sound" not in result.assumption_ledger
        assert "ideal_qubit_receiver" in result.assumption_ledger


# ===========================================================================
#  req:band-a-identity-link
# ===========================================================================


def test_a_link_without_channel_data_is_refused_at_i() -> None:
    """The identity-shaped link that only names its channel: (C4) undecidable.

    The recognition admits it (a link without channel data passes the link
    test), the ideal receiver passes, and without this requirement the chain
    stage would leave (C4) ``not checked`` while the Band-A ledger omits
    A-LINK.
    """
    specification = _specification(
        PROJECTIVE, chain=_band_a(PROJECTIVE, supply_channel=False)
    )
    assert band_a_route(specification)
    assert decide_band_a_ideal_receiver(specification) is None
    refusal = decide_band_a_identity_link(specification, V_PAIR)
    assert refusal is not None
    assert refusal.reason is RefusalReason.BAND_A_LINK_NOT_IDENTITY
    assert "clause (i)" in refusal.detail
    reason, detail = _refusal(specification)
    assert reason is RefusalReason.BAND_A_LINK_NOT_IDENTITY
    assert "clause (i)" in detail and "Lambda_1" in detail


def test_a_link_without_channel_data_is_refused_in_the_general_format() -> None:
    """The general-format call site: one factor, an ensemble-form source."""
    specification = replace(
        _specification(PROJECTIVE, chain=_band_a(PROJECTIVE, supply_channel=False)),
        source=_ensemble_source(1),
    )
    assert specification.is_general_format
    assert band_a_route(specification)
    reason, detail = _refusal(specification)
    assert reason is RefusalReason.BAND_A_LINK_NOT_IDENTITY
    assert "clause (i)" in detail


def _swapped(physical: DirectPovm) -> ReductionChain:
    """Return the identity link with gamma swapping the outcomes, target to match.

    ``gamma(v0) = v1``, ``gamma(v1) = v0`` and ``F_v1 = F^ph_v0``,
    ``F_v0 = F^ph_v1``: a bijection, so (C2) holds, and the pullback identity
    ``F_v = F^ph_{gamma^{-1}(v)}`` holds too, so (C4) passes. Only
    req:band-a-identity-link (ii) refuses it.
    """
    chain = _band_a(physical)
    (link,) = chain.receiver_segment
    elements = dict(physical.elements)
    return replace(
        chain,
        receiver_segment=(
            replace(
                link,
                target_povm={
                    "v0": BlockOperator.of(_sectors(2), (elements["v1"],)),
                    "v1": BlockOperator.of(_sectors(2), (elements["v0"],)),
                },
            ),
        ),
        outcome_correspondence={"v0": "v1", "v1": "v0"},
    )


def test_a_non_identity_outcome_correspondence_is_refused_at_ii() -> None:
    specification = _specification(PROJECTIVE, chain=_swapped(PROJECTIVE))
    assert band_a_route(specification)
    assert decide_band_a_ideal_receiver(specification) is None
    reason, detail = _refusal(specification)
    assert reason is RefusalReason.BAND_A_LINK_NOT_IDENTITY
    assert "clause (ii)" in detail and "'v0' to 'v1'" in detail


def test_the_swapped_correspondence_off_the_route_passes_the_chain() -> None:
    """The control: through a squashing link the same gamma is (C2)-(C4)-sound."""
    swapped = _swapped(PROJECTIVE)
    (link,) = swapped.receiver_segment
    chain = replace(
        _squashing(PROJECTIVE),
        outcome_correspondence=dict(swapped.outcome_correspondence),
    )
    (squashing,) = chain.receiver_segment
    chain = replace(
        chain,
        receiver_segment=(
            replace(
                squashing,
                target_povm=link.target_povm,
                channel=(identity(2),),
            ),
        ),
    )
    specification = _specification(PROJECTIVE, chain=chain)
    assert not band_a_route(specification)
    assert decide_band_a_identity_link(specification, V_PAIR) is None
    result = compile_specification(specification)
    assert result.chain is not None
    assert result.chain.verdict("C4") is ConditionOutcome.HOLDS


def test_a_relabelled_target_alphabet_is_refused_at_ii() -> None:
    """V and V^ph not one set: a bijection onto other labels, (C4) satisfied."""
    chain = _band_a(PROJECTIVE)
    (link,) = chain.receiver_segment
    relabelled = replace(
        chain,
        receiver_segment=(
            replace(
                link,
                target_alphabet=("a", "b"),
                target_povm={
                    "a": BlockOperator.of(_sectors(2), (Z0,)),
                    "b": BlockOperator.of(_sectors(2), (Z1,)),
                },
            ),
        ),
        outcome_correspondence={"v0": "a", "v1": "b"},
    )
    specification = _specification(PROJECTIVE, chain=relabelled)
    assert band_a_route(specification)
    refusal = decide_band_a_identity_link(specification, V_PAIR)
    assert refusal is not None
    assert refusal.reason is RefusalReason.BAND_A_LINK_NOT_IDENTITY
    assert "clause (ii)" in refusal.detail and "not one set" in refusal.detail


#: The audit's counter-scenario: the declared receiver measures Z, the link's
#: target POVM is X.
PLUS = matrix(((HALF, HALF), (HALF, HALF)))
MINUS = matrix(((HALF, -HALF), (-HALF, HALF)))


def _target_x(*, supply_channel: bool) -> ReductionChain:
    chain = _band_a(PROJECTIVE, supply_channel=supply_channel)
    (link,) = chain.receiver_segment
    return replace(
        chain,
        receiver_segment=(
            replace(
                link,
                target_povm={
                    "v0": BlockOperator.of(_sectors(2), (PLUS,)),
                    "v1": BlockOperator.of(_sectors(2), (MINUS,)),
                },
            ),
        ),
    )


def test_a_target_povm_other_than_the_declared_family_is_refused_by_c4() -> None:
    """Identity channel as data, gamma the identity, target X, declared Z.

    req:band-a-identity-link passes, so (C4) is decided and reads
    ``F_v = F^ph_v``: it fails, and the refusal is (C4)'s own,
    ``chain_interface_condition_failed`` naming (C4).
    """
    specification = _specification(PROJECTIVE, chain=_target_x(supply_channel=True))
    assert band_a_route(specification)
    assert decide_band_a_ideal_receiver(specification) is None
    assert decide_band_a_identity_link(specification, V_PAIR) is None
    result = compile_specification(specification)
    assert result.refusal is not None
    assert result.refusal.reason is RefusalReason.CHAIN_INTERFACE_CONDITION_FAILED
    assert result.chain is not None
    assert result.chain.failing_condition == "C4"
    assert "(C4)" in result.refusal.detail


def test_the_counter_scenario_without_channel_data_is_refused_before_c4() -> None:
    """The same X target with the channel only named: refused, not emitted.

    Were it emitted, (C4) would be ``not checked`` and the Band-A ledger would
    omit A-LINK for a key length computed on X while Z is declared.
    """
    specification = _specification(PROJECTIVE, chain=_target_x(supply_channel=False))
    reason, detail = _refusal(specification)
    assert reason is RefusalReason.BAND_A_LINK_NOT_IDENTITY
    assert "clause (i)" in detail


# ===========================================================================
#  req:da1-source-identity
# ===========================================================================

ONE_BY_ONE_HALF = matrix(((HALF,),))


def test_letter_independent_emission_with_matching_weights_compiles() -> None:
    """The control: one common state, Alice's weights equal to the source's."""
    source = _trusted_d1_source(
        {"x0": MIXED, "x1": MIXED},
        {"x0": HALF, "x1": HALF},
        {"x0": ONE_BY_ONE_HALF, "x1": ONE_BY_ONE_HALF},
    )
    specification = _specification(PROJECTIVE, source=source)
    assert decide_da1_source_identity(specification, source.artifact.alice_povm) is None
    result = compile_specification(specification)
    assert result.refusal is None, result.refusal


def test_a_letter_dependent_state_is_refused_naming_letter_and_entry() -> None:
    """``rho_x0 = |0><0|``, ``rho_x1 = |1><1|``: (SR2) at d_A = 1 fails at x0."""
    source = _trusted_d1_source(
        {"x0": Z0, "x1": Z1},
        {"x0": HALF, "x1": HALF},
        {"x0": ONE_BY_ONE_HALF, "x1": ONE_BY_ONE_HALF},
    )
    reason, detail = _refusal(_specification(PROJECTIVE, source=source))
    assert reason is RefusalReason.DA1_SOURCE_IDENTITY_FAILED
    assert "letter 'x0'" in detail and "entry (1, 1)" in detail


def test_letter_weights_that_differ_from_the_source_are_refused() -> None:
    """One common state, and ``m_x = (1/4, 3/4)`` against ``p_x = (1/2, 1/2)``."""
    source = _trusted_d1_source(
        {"x0": MIXED, "x1": MIXED},
        {"x0": HALF, "x1": HALF},
        {"x0": matrix(((QUARTER,),)), "x1": matrix(((F(3, 4),),))},
    )
    reason, detail = _refusal(_specification(PROJECTIVE, source=source))
    assert reason is RefusalReason.DA1_SOURCE_IDENTITY_FAILED
    assert "letter 'x0'" in detail and "m_x = 1/4" in detail


def test_one_letter_is_decided_and_passes() -> None:
    source = _trusted_d1_source({"x0": Z0}, {"x0": F(1)}, {"x0": identity(1)})
    specification = _specification(PROJECTIVE, source=source)
    assert decide_da1_source_identity(specification, source.artifact.alice_povm) is None
    result = compile_specification(specification)
    assert result.refusal is None, result.refusal


def test_untrusted_mode_has_no_comparison() -> None:
    """No source premise is emitted in untrusted-source mode: nothing to compare."""
    source = _trusted_d1_source(
        {"x0": Z0, "x1": Z1},
        {"x0": HALF, "x1": HALF},
        {"x0": matrix(((QUARTER,),)), "x1": matrix(((F(3, 4),),))},
        mode=SourceMode.UNTRUSTED,
    )
    specification = _specification(PROJECTIVE, source=source)
    assert decide_da1_source_identity(specification, source.artifact.alice_povm) is None
    result = compile_specification(specification)
    assert (
        result.refusal is None
        or result.refusal.reason is not RefusalReason.DA1_SOURCE_IDENTITY_FAILED
    )


def _alice_choices(weights: tuple[F, F]) -> PublicChoices:
    """Return Alice's public choice: one letter per choice value, ``M_x = [q_t]``."""
    return PublicChoices(
        party=Party.ALICE,
        choices=("t0", "t1"),
        weights={"t0": weights[0], "t1": weights[1]},
        conditional_alphabets={"t0": ("x0",), "t1": ("x1",)},
        conditional_elements={"t0": {"x0": identity(1)}, "t1": {"x1": identity(1)}},
        joint_labels={("x0", "t0"): "x0", ("x1", "t1"): "x1"},
    )


@pytest.mark.parametrize(
    ("weights", "states", "refused"),
    [
        ((HALF, HALF), (MIXED, MIXED), False),
        ((HALF, HALF), (Z0, Z1), True),
        ((QUARTER, F(3, 4)), (MIXED, MIXED), True),
    ],
)
def test_a_choice_weighted_alice_reads_the_weighted_element(
    weights: tuple[F, F], states: tuple[Matrix, Matrix], refused: bool
) -> None:
    """``m_x`` is the weighted element the engine forms, ``q_t N_{u|t}``."""
    choices = _alice_choices(weights)
    weighted = weighted_family(choices)
    source = _trusted_d1_source(
        {"x0": states[0], "x1": states[1]},
        {"x0": HALF, "x1": HALF},
        dict(weighted.elements),
        choices=choices,
    )
    result = compile_specification(_specification(PROJECTIVE, source=source))
    if refused:
        assert result.refusal is not None
        assert result.refusal.reason is RefusalReason.DA1_SOURCE_IDENTITY_FAILED
    else:
        assert result.refusal is None, result.refusal


@pytest.mark.parametrize(
    ("states", "refused"), [((MIXED, MIXED), False), ((Z0, Z1), True)]
)
def test_the_general_format_decides_the_identity_too(
    states: tuple[Matrix, Matrix], refused: bool
) -> None:
    """Two measured factors (not on the route), a trusted ``d_A = 1`` source.

    The control is the same specification with one common state: it compiles,
    so the refusal of the letter-dependent source is the identity's and does
    not rest on where in the pipeline the decision sits.
    """
    source = _trusted_d1_source(
        {"x0": states[0], "x1": states[1]},
        {"x0": HALF, "x1": HALF},
        {"x0": ONE_BY_ONE_HALF, "x1": ONE_BY_ONE_HALF},
    )
    specification = replace(
        _two_factors(
            _squashing(PROJECTIVE, name="Q_a"), _squashing(PROJECTIVE, name="Q_b")
        ),
        source=source,
    )
    assert specification.is_general_format
    assert not band_a_route(specification)
    result = compile_specification(specification)
    if refused:
        assert result.refusal is not None
        assert result.refusal.reason is RefusalReason.DA1_SOURCE_IDENTITY_FAILED
        assert "letter 'x0'" in result.refusal.detail
    else:
        assert result.refusal is None, result.refusal


def test_the_ensemble_form_reads_n_x() -> None:
    """In ensemble form ``m_x`` is ``N_x`` and ``sigma_x`` the declared member."""
    one = SectorStructure(labels=("t0",), dims=(1,), block_kind=BlockKind.PROOF_SECTOR)

    def source(n_x0: F, n_x1: F) -> SourcePart:
        artifact = TransmitterArtifact(
            signal_alphabet=X_PAIR,
            alice_dim=1,
            alice_marginal=identity(1),
            alice_povm={},
            virtual_transmitted_system=1,
            virtual_ensemble_weights={"x0": HALF, "x1": HALF},
            virtual_ensemble_states={},
            alice_sector_map=one,
            virtual_sector_map=one,
            alice_ensemble_operators={
                "x0": (matrix(((n_x0,),)),),
                "x1": (matrix(((n_x1,),)),),
            },
            virtual_ensemble_blocks={
                "x0": (ONE_BY_ONE_HALF,),
                "x1": (ONE_BY_ONE_HALF,),
            },
        )
        return SourcePart(artifact=artifact)

    base = _specification(PROJECTIVE)
    holds = replace(base, source=source(HALF, HALF))
    assert holds.source.source_mode is SourceMode.TRUSTED
    assert decide_da1_source_identity(holds, {}) is None
    fails = replace(base, source=source(QUARTER, F(3, 4)))
    refusal = decide_da1_source_identity(fails, {})
    assert refusal is not None
    assert refusal.reason is RefusalReason.DA1_SOURCE_IDENTITY_FAILED
    assert "letter 'x0'" in refusal.detail


def test_the_general_format_refuses_at_ii_and_at_c4() -> None:
    """The general format decides clause (ii), and (C4) refuses a wrong target."""
    swapped = replace(
        _specification(PROJECTIVE, chain=_swapped(PROJECTIVE)),
        source=_ensemble_source(1),
    )
    assert swapped.is_general_format
    reason, detail = _refusal(swapped)
    assert reason is RefusalReason.BAND_A_LINK_NOT_IDENTITY
    assert "clause (ii)" in detail
    x_target = replace(
        _specification(PROJECTIVE, chain=_target_x(supply_channel=True)),
        source=_ensemble_source(1),
    )
    result = compile_specification(x_target)
    assert result.refusal is not None
    assert result.refusal.reason is RefusalReason.CHAIN_INTERFACE_CONDITION_FAILED
    assert "(C4)" in result.refusal.detail


def test_the_ideal_receiver_is_decided_before_the_identity_link() -> None:
    """A specification failing both Band-A decisions is refused by the earlier one."""
    both = _specification(
        THREE_OUTCOME, chain=_band_a(THREE_OUTCOME, supply_channel=False)
    )
    reason, _ = _refusal(both)
    assert reason is RefusalReason.BAND_A_OUTSIDE_IDEAL_RECEIVER


def test_a_choice_weighted_target_other_than_the_products_is_refused_by_c4() -> None:
    """(C4) is decided against the family of products, on both formats."""
    plus = matrix(((HALF, HALF), (HALF, HALF)))
    minus = matrix(((HALF, -HALF), (-HALF, HALF)))
    choices = _choices({"+": plus, "-": minus})
    alphabet, _ = _resolved(choices)
    chain = _band_a(choices)
    (link,) = chain.receiver_segment
    target = dict(link.target_povm)
    target[alphabet[2]], target[alphabet[3]] = target[alphabet[3]], target[alphabet[2]]
    bad = replace(chain, receiver_segment=(replace(link, target_povm=target),))
    for specification in (
        _specification(choices, chain=bad),
        replace(_specification(choices, chain=bad), source=_ensemble_source(1)),
    ):
        result = compile_specification(specification)
        assert result.refusal is not None
        assert result.refusal.reason is RefusalReason.CHAIN_INTERFACE_CONDITION_FAILED
        assert result.chain is not None and result.chain.failing_condition == "C4"


def test_is_band_a_is_the_shape_only() -> None:
    """def:banda (b) is completed by req:band-a-identity-link and (C4)."""
    unsupplied = _band_a(PROJECTIVE, supply_channel=False)
    assert is_band_a(unsupplied, _sectors(2))
    reason, _ = _refusal(_specification(PROJECTIVE, chain=unsupplied))
    assert reason is RefusalReason.BAND_A_LINK_NOT_IDENTITY
