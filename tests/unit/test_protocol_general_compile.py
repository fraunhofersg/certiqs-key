"""SPECIFICATIONS OF THE GENERAL FORMAT THAT COMPILE, end to end.

WHAT THIS FILE IS FOR, AND WHY IT IS SEPARATE FROM
``test_protocol_general_format.py``. That file builds CANDIDATES by hand, which
is what ``def:validator`` is stated on; this one builds SPECIFICATIONS and runs
:func:`~certiqs_key.protocol_compiler.compile.compile_specification` over them,
which is what ``def:spec`` (a')--(e') and ``def:compile``'s general paragraph are
stated on. The two halves of the design rule are therefore both executed:
a specification of the accepted format compiles to what it compiled to (the whole
accepted suite), and a specification of the general format compiles to a
declaration of the general format or refuses for a reason an accepted claim
states.

THE FOUR SHAPES HERE.

* ``ex:two-party-shape``, the general format's own example, COMPILED: untrusted source,
  ``d_A = 1``, two measured factors with a party label each, a transcript with
  ``L = 2`` and a ``party_local`` entry scoped to the second factor.
* ``ex:transcript``, the general format's other example, COMPILED: three messages, the
  third reading the first two, with Bob's disclosure depending on the round type
  Alice announced -- which is what the accepted format could not say.
* A BBM92-SHAPED specification: the two-party shape with party-local entries on
  both arms, which is the shape ``meat-core``'s design note reads as BBM92.
* A DECOY-SHAPED specification: the merged ``transmitter.decoy`` emission -- a
  tagged ensemble, ensemble presentation, several Alice sectors, trusted source,
  one measured factor. ITS PATH STOPS AT A FENCE THAT IS NOT THIS MODULE'S, and
  the test says exactly where.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from dataclasses import replace
from fractions import Fraction as F

import pytest

from certiqs_key.domain.announcements import AnnouncementTranscript, Message
from certiqs_key.domain.chain import (
    ChainLink,
    LinkStage,
    LinkStatus,
    ReductionChain,
    Side,
    SystemDescriptor,
)
from certiqs_key.domain.constraints import (
    AttackSetLicense,
    ConstraintEntry,
    Relation,
    RhsTag,
)
from certiqs_key.foundations.blocks import (
    PRODUCT_LABEL_SEPARATOR,
    BlockKind,
    BlockOperator,
    JointBlockOperator,
    Label,
    SectorStructure,
)
from certiqs_key.foundations.errors import MalformedInputError
from certiqs_key.foundations.exact import Matrix, identity, matrix, scale
from certiqs_key.protocol_compiler.chain import identity_channel
from certiqs_key.protocol_compiler.compile import (
    compile_specification,
    decide_every_conditional_family,
)
from certiqs_key.protocol_compiler.declaration import CandidateDeclaration
from certiqs_key.protocol_compiler.spec import (
    DirectPovm,
    Party,
    PartyPartition,
    ProtocolSpecification,
    PublicChoices,
    PublicPart,
    ReceiverPart,
    Sifting,
    SourcePart,
    SpecConstraints,
)
from certiqs_key.protocol_compiler.validation import check_v3
from certiqs_key.transmitter.artifact import SourceSpecification, emit_artifact
from certiqs_key.transmitter.reasons import SourceMode

KIND = BlockKind.PROOF_SECTOR

#: ``ex:two-party-shape``: each factor has a data sector of dimension two and a
#: flag sector of dimension one, in this order.
FACTOR_SECTORS = SectorStructure(labels=("d", "fl"), dims=(2, 1), block_kind=KIND)

#: ``V^f = (0, 1, fl)``, in this order.
FACTOR_LETTERS: tuple[Label, ...] = ("0", "1", "fl")

#: The two factor labels of the example, ``f = a`` and ``f = b``. THEY ARE FACTOR
#: LABELS AND NOT PARTY LABELS: the example gives factor ``a`` the party label
#: ``A`` and factor ``b`` the party label ``B``, and the scope of its entry names
#: the FACTOR.
FACTORS: tuple[Label, Label] = ("a", "b")


def _factor_family() -> dict[Label, BlockOperator]:
    """Return one factor's family of ``ex:two-party-shape``, block by block.

    ``F^{f,(d)}_0 = diag(1, 0)``, ``F^{f,(d)}_1 = diag(0, 1)``,
    ``F^{f,(d)}_fl = 0``, and ``F^{f,(fl)}_0 = F^{f,(fl)}_1 = [0]``,
    ``F^{f,(fl)}_fl = [1]``. Exactly admissible for that factor's map, with its
    two completeness sums rounding nowhere.
    """
    zero_two = matrix([[0, 0], [0, 0]])
    zero_one = matrix([[0]])
    one = matrix([[1]])
    return {
        "0": BlockOperator.of(FACTOR_SECTORS, [matrix([[1, 0], [0, 0]]), zero_one]),
        "1": BlockOperator.of(FACTOR_SECTORS, [matrix([[0, 1 - 1], [0, 1]]), zero_one]),
        "fl": BlockOperator.of(FACTOR_SECTORS, [zero_two, one]),
    }


def _factor_chain(name: str, sectors: SectorStructure) -> ReductionChain:
    """Return one measured factor's OWN receiver segment: an identity link.

    ``def:spec`` (c'): "segment ``f``'s links act on factor ``f``'s physical
    receiver system and its last link's target descriptor is
    ``(Q_f, S^f, (d_{f,s_f}))`` with target POVM ``{F^f_{v_f}}``". This is the
    explicit identity pass-through of an already-finite fixture, one per factor,
    and the segments are separate lists because their links act on different
    systems.
    """
    descriptor = SystemDescriptor(
        name,
        sectors.total_dim,
        Side.RECEIVER,
        tuple(zip(sectors.labels, sectors.dims, strict=True)),
        KIND,
    )
    return ReductionChain(
        source_segment=(),
        receiver_segment=(
            ChainLink(
                link_id=f"Lambda_1[{name}]",
                segment=LinkStage.RECEIVER,
                link_type="squashing (identity)",
                source_descriptor=descriptor,
                target_descriptor=descriptor,
                status=LinkStatus.EXACT,
                channel=identity_channel(sectors.total_dim),
                target_alphabet=FACTOR_LETTERS,
                target_povm=_factor_family(),
            ),
        ),
        outcome_correspondence=dict(zip(FACTOR_LETTERS, FACTOR_LETTERS, strict=True)),
    )


def _trivial_source() -> SourcePart:
    """Return ``S_src`` at ``d_A = 1`` in untrusted mode, off the transmitter.

    ``ex:two-party-shape``: "the marginal slot holds nomarg, ``X = {x_0}`` and
    ``M_{x_0} = [1]`` (``transmitter/rem:da1``)". Built by the transmitter's own
    emission, so that the artefact this module reads is one a transmitter emitted.
    """
    result = emit_artifact(
        SourceSpecification(
            signal_alphabet=("x0",),
            transmitted_dim=1,
            signal_weights={"x0": F(1)},
            signal_states={"x0": identity(1)},
            alice_dim=1,
            alice_povm={"x0": identity(1)},
            source_mode_request=SourceMode.UNTRUSTED,
        )
    )
    return SourcePart(artifact=result.require())


def _product_letters() -> tuple[Label, ...]:
    """Return ``V = V^a x V^b`` in the product order, the LAST factor fastest."""
    return tuple(
        f"{left}{PRODUCT_LABEL_SEPARATOR}{right}"
        for left in FACTOR_LETTERS
        for right in FACTOR_LETTERS
    )


def _two_party_partition(v_alphabet: Sequence[Label]) -> PartyPartition:
    """Return the partition of ``ex:two-party-shape``, which is NOT the default.

    "``pi_A(x_0, v) = v_a`` and ``pi_B(x_0, v) = v_b``, which is NOT the default
    partition: under the default one both parties' data would sit in ``pi_B`` and
    party computability would be vacuous."
    """
    return PartyPartition(
        alice_readout={
            ("x0", v): v.split(PRODUCT_LABEL_SEPARATOR)[0] for v in v_alphabet
        },
        bob_readout={
            ("x0", v): v.split(PRODUCT_LABEL_SEPARATOR)[1] for v in v_alphabet
        },
        alice_readout_alphabet=FACTOR_LETTERS,
        bob_readout_alphabet=FACTOR_LETTERS,
        sector_factor_parties=((Party.ALICE,), (Party.BOB,)),
    )


def _flag_transcript() -> AnnouncementTranscript:
    """Return the ``L = 2`` transcript of ``ex:two-party-shape``.

    "``pi = (A, B)``, each party announcing whether its outcome is a flag,
    ``a_1(v_a) = a_2(v_b, kappa_1) = fl`` on the flag letter and ``ok``
    otherwise."
    """
    first = Message(
        sender=str(Party.ALICE),
        alphabet=("ok", "fl"),
        table={
            (readout, ()): ("fl" if readout == "fl" else "ok")
            for readout in FACTOR_LETTERS
        },
    )
    second = Message(
        sender=str(Party.BOB),
        alphabet=("ok", "fl"),
        table={
            (readout, (kappa,)): ("fl" if readout == "fl" else "ok")
            for readout in FACTOR_LETTERS
            for kappa in ("ok", "fl")
        },
    )
    return AnnouncementTranscript(messages=(first, second))


def _public_part(
    transcript: AnnouncementTranscript,
    v_alphabet: Sequence[Label],
) -> PublicPart:
    """Return ``S_pub`` of ``def:spec`` (d'): the transcript and the derived ``K``.

    ``sigma``, ``r^0_h``, ``h``, ``Chat`` and ``phi`` are declared on the DERIVED
    ``K = prod_m C_m``, "which is a set determined by the tables and is declared
    by no one".

    ``C_A`` AND ``C_B`` ARE STILL DECLARED, AND THAT IS V1'S CLAUSE AND NOT A
    SECOND ANNOUNCEMENT MAP. (d') replaces ``a_A`` and ``a_B`` by the transcript
    and keeps the party partition "as in (d)"; V1 still reads every declared
    alphabet for finiteness and non-emptiness, and ``idxm``'s nine components
    still include ``C_A`` and ``C_B``. So each is declared as that sender's FIRST
    message's alphabet, which at ``L = 2`` IS the accepted pair, letter for
    letter; the announcement TABLES are the transcript's and this module derives
    ``a`` from them alone.
    """
    classes = transcript.joint_alphabet()
    passes = tuple(kappa for kappa in classes if all(part == "ok" for part in kappa))
    return PublicPart(
        partition=_two_party_partition(v_alphabet),
        announce_alice={},
        announce_bob={},
        alice_announcement_alphabet=transcript.messages[0].alphabet,
        bob_announcement_alphabet=transcript.messages[1].alphabet,
        sifting={
            kappa: (Sifting.PASS if kappa in passes else Sifting.FAIL)
            for kappa in classes
        },
        # r^0_A(v_a, kappa) = v_a, INTO Z = {0, 1}: the flag letter maps to 0,
        # which rem:sidecond's side condition requires to be a value of Z and
        # never perp, and whose value on a failing class is immaterial.
        key_rule={
            (readout, kappa): (1 if readout == "1" else 0)
            for readout in FACTOR_LETTERS
            for kappa in classes
        },
        holder=Party.ALICE,
        key_alphabet=(0, 1),
        acceptance_alphabet=("c",),
        accept_statistic={},
        transcript=transcript,
        accept_statistic_general=dict.fromkeys(classes, "c"),
    )


def _flag_entry(factor: Label, scope: Label | None = None) -> ConstraintEntry:
    """Return the ``party_local`` entry of ``ex:two-party-shape``, scoped to ``factor``.

    "Let ``O`` be the block list on factor ``b`` with ``O^(d) = 0`` and
    ``O^(fl) = [1]``, the projector onto Bob's flag sector, and declare
    ``(O, preceq, 1/8; b)`` with the tag ``party_local``."
    """
    return ConstraintEntry(
        operator=BlockOperator.of(
            FACTOR_SECTORS, [matrix([[0, 0], [0, 0]]), identity(1)]
        ),
        relation=Relation.LE,
        rhs=F(1, 8),
        arriving_tag=RhsTag.PARTY_LOCAL,
        scope=factor if scope is None else scope,
    )


def _flag_free_witness() -> JointBlockOperator:
    """Return ``omega^*`` putting every unit of weight where no factor flags.

    WHY A WITNESS IS SUPPLIED AT ALL, and it is Theorem ``thm:validator-soundness``
    (iii) rather than a defect. The default candidate of ``eq:witness-general`` is
    ``tau^{(t)}_A (x) 1_{Q_s}/d_Q``, which spreads ``3/9`` of its weight over the
    sectors where some factor flags; the example's entry bounds that weight by
    ``1/8``, so branch (b) fails and branch (c) is where the declaration is
    verified -- "exactly the same happens for every declaration with
    ``CList != empty`` presented without a witness whose feasible set is non-empty
    but does not contain ``eq:witness-empty``". The witness below is the uniform
    state on the one sector where neither factor flags, so every flag row of every
    party-local entry is exactly zero.

    IT IS A BLOCK LIST OVER THE JOINT SECTORS, which at ``|T| = 1`` are the
    product sectors, and NOTHING LARGER THAN ONE JOINT BLOCK IS ASSEMBLED.
    """
    sectors = SectorStructure(
        labels=tuple(
            f"{left}{PRODUCT_LABEL_SEPARATOR}{right}"
            for left in FACTOR_SECTORS.labels
            for right in FACTOR_SECTORS.labels
        ),
        dims=tuple(
            left * right
            for left in FACTOR_SECTORS.dims
            for right in FACTOR_SECTORS.dims
        ),
        block_kind=KIND,
    )
    blocks: list[Matrix] = []
    for label, dim in sectors.entries:
        weight = (
            F(1, dim)
            if "fl" not in label.split(PRODUCT_LABEL_SEPARATOR)
            else F(0)
        )
        blocks.append(scale(weight, identity(dim)))
    return JointBlockOperator.of(sectors, 1, blocks)


def _two_party_specification(
    *,
    entries: tuple[ConstraintEntry, ...] = (),
    transcript: AnnouncementTranscript | None = None,
) -> ProtocolSpecification:
    """Return ``ex:two-party-shape`` as a specification of ``def:spec`` (a')--(e')."""
    v_alphabet = _product_letters()
    chains = [_factor_chain(f"Q_{name}", FACTOR_SECTORS) for name in FACTORS]
    first = ReceiverPart(
        physical_dim=FACTOR_SECTORS.total_dim,
        physical_povm=DirectPovm(
            alphabet=FACTOR_LETTERS,
            elements={
                letter: block.dense() for letter, block in _factor_family().items()
            },
        ),
        party=Party.ALICE,
        factor_label=FACTORS[0],
    )
    second = ReceiverPart(
        physical_dim=FACTOR_SECTORS.total_dim,
        physical_povm=DirectPovm(
            alphabet=FACTOR_LETTERS,
            elements={
                letter: block.dense() for letter, block in _factor_family().items()
            },
        ),
        party=Party.BOB,
        factor_label=FACTORS[1],
        chain=chains[1],
    )
    used = transcript if transcript is not None else _flag_transcript()
    return ProtocolSpecification(
        source=_trivial_source(),
        receiver=first,
        public=_public_part(used, v_alphabet),
        # THE EMITTED SECTOR MAP IS DERIVED AND THIS SLOT IS NOT READ IN THE
        # GENERAL FORMAT: def:compile derives the product map from the factor
        # list. It is filled with the FIRST factor's map so that the record is
        # well typed, and the assembly replaces it.
        sectors=FACTOR_SECTORS,
        chain=chains[0],
        constraints=SpecConstraints(
            entries=entries,
            # (G3)(b) DEMANDS THE ATTACK-SET LICENCE RECORD wherever m >= 1, in
            # either format and for either tag: "each is refused unless its
            # gate admits it" (spec/architecture.md 4.2), and the general
            # format adds no row to
            # the gate outcome table. So a shape with entries declares one.
            attack_set_license=(
                AttackSetLicense(
                    supplier="the two-party fixture of tests/unit",
                    statement=(
                        "the declared entries are transported from each factor's "
                        "own certified channel and are asserted of that factor "
                        "alone (ex:two-party-shape)"
                    ),
                )
                if entries
                else None
            ),
            feasibility_witness=_flag_free_witness() if entries else None,
        ),
        further_receiver_factors=(second,),
    )


# ---------------------------------------------------------------------------
#  ex:two-party-shape, compiled
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_the_two_party_shape_compiles_to_the_general_format() -> None:
    """``ex:two-party-shape``, emitted slot by slot by ``def:compile``.

    The example's own numbers: the product map's four sectors in the declared
    order with dimensions ``4, 2, 2, 1``; nine product letters; and, because
    ``|T| = 1``, the joint sectors ARE the product sectors.
    """
    result = compile_specification(_two_party_specification())
    assert not result.refuses, result.refusal
    declaration = result.declaration
    assert declaration is not None
    # (DX1): the factor list, ASSEMBLED from the ordered receiver part.
    factorisation = declaration.sector_factorisation
    assert factorisation is not None
    assert declaration.measured_factor_labels == FACTORS
    assert [factor.party for factor in declaration.measured_factors] == ["A", "B"]
    # NO A FACTOR IS EMITTED: the artefact declares no Alice sector map, so
    # T = {t_0} and A_{t_0} = A (DX1).
    assert declaration.alice_factor is None
    assert declaration.alice_sectors.count == 1
    # The DERIVED product map, the last factor fastest.
    assert declaration.sectors.labels == (
        f"d{PRODUCT_LABEL_SEPARATOR}d",
        f"d{PRODUCT_LABEL_SEPARATOR}fl",
        f"fl{PRODUCT_LABEL_SEPARATOR}d",
        f"fl{PRODUCT_LABEL_SEPARATOR}fl",
    )
    assert declaration.sectors.dims == (4, 2, 2, 1)
    # At |T| = 1 the joint sectors are the product sectors, identifier for
    # identifier: the join of a single identifier is that identifier.
    assert declaration.joint_sectors.dims == (4, 2, 2, 1)
    # (DX3): the per-factor family is the datum and the product is the RULE.
    assert declaration.bob_factors is not None
    assert declaration.bob_factors.count == 2
    assert declaration.bob_povm == {}
    assert len(declaration.bob_alphabet) == 9
    # (DX5): the transcript is emitted VERBATIM and a is derived from it.
    assert declaration.transcript is not None
    assert declaration.announcement("x0", f"fl{PRODUCT_LABEL_SEPARATOR}0") == (
        "fl",
        "ok",
    )
    # idxm has one component per factor alphabet and per factor sector set.
    index = declaration.label_index_map
    assert index is not None
    for factor in FACTORS:
        assert f"V[{factor}]" in index.forward
        assert f"S[{factor}]" in index.forward
    assert "T" not in index.forward
    chain_record = result.reduction_chain_record
    assert set(chain_record) == {"source_segment", "receiver_factor_segments"}
    factor_records = chain_record["receiver_factor_segments"]
    assert [row["factor_label"] for row in factor_records] == ["a", "b"]
    assert [row["party"] for row in factor_records] == ["A", "B"]
    assert all(row["receiver_segment"] for row in factor_records)
    assert all(row["outcome_correspondence"] for row in factor_records)


def _duplicate_transcript_keys(specification: ProtocolSpecification) -> list[object]:
    """Return every ``(source, predicate, element, block)`` decided twice."""
    result = compile_specification(specification)
    assert not result.refuses, result.refusal
    assert result.gate_report is not None
    keys = Counter(
        (o.source, o.predicate, o.element, o.block)
        for o in result.gate_report.transcript.outcomes
    )
    return [key for key, count in keys.items() if count > 1]


def _elements(specification: ProtocolSpecification) -> set[tuple[str, str | None]]:
    """Return the ``(source, element)`` pairs a compilation recorded."""
    result = compile_specification(specification)
    assert result.gate_report is not None
    return {
        (str(o.source), o.element) for o in result.gate_report.transcript.outcomes
    }


def _same_party_factors(*, weighted: bool) -> ProtocolSpecification:
    """Return ``ex:two-party-shape`` with BOTH measured factors of party ``B``.

    ``weighted`` presents each factor's physical family as a ``public_choices``
    record with one choice of weight one, its joint labels the factor letters,
    so that the weight list and the representability of its products are
    decided per factor and the family the chain reads is unchanged.
    """
    spec = _two_party_specification()
    parts = []
    for part in (spec.receiver, *spec.further_receiver_factors):
        physical = part.physical_povm
        if weighted:
            physical = PublicChoices(
                party=Party.BOB,
                choices=("t",),
                weights={"t": F(1)},
                conditional_alphabets={"t": FACTOR_LETTERS},
                conditional_elements={
                    "t": {
                        letter: block.dense()
                        for letter, block in _factor_family().items()
                    }
                },
                joint_labels={(letter, "t"): letter for letter in FACTOR_LETTERS},
            )
        parts.append(replace(part, party=Party.BOB, physical_povm=physical))
    return replace(
        spec, receiver=parts[0], further_receiver_factors=tuple(parts[1:])
    )


@pytest.mark.contract
def test_two_same_party_factors_keep_distinct_transcript_keys() -> None:
    """A party may hold two measured factors (``def:spec`` (b'), (c')).

    The transcript's factor rule: with more than one factor presented, every
    key of a decision on one factor's own data names that factor, so two
    factors of party ``B`` emitting families over the same letters decide (C4),
    V1 and V3 under distinct keys.
    """
    spec = _same_party_factors(weighted=False)
    assert _duplicate_transcript_keys(spec) == []
    elements = _elements(spec)
    for factor in FACTORS:
        assert ("C4", f"{factor}:F_0") in elements
        assert ("V1", f"{factor}:F^B_0") in elements
        assert ("V3", f"{factor}:F^B_fl") in elements
        assert ("V3", f"{factor}:{{F^B_v}}") in elements
    assert ("C4", "F_0") not in elements
    assert ("V3", "{F^B_v}") not in elements


@pytest.mark.contract
def test_two_same_party_weighted_factors_keep_distinct_weight_list_keys() -> None:
    """``req:weight-list`` and ``def:weighted``'s emission, decided per factor.

    Each factor's weight list ``{q_t}`` and the representability of each of its
    products are keyed by the factor, as the conditional families already are.
    """
    spec = _same_party_factors(weighted=True)
    assert _duplicate_transcript_keys(spec) == []
    elements = _elements(spec)
    for factor in FACTORS:
        assert ("compilation_map", f"{factor}:B:{{q_t}}") in elements
        assert ("compilation_map", f"{factor}:B:fl") in elements
        assert ("compilation_map", f"{factor}:B:{{N_(u|t)}}") in elements
    assert ("compilation_map", "B:{q_t}") not in elements


def _with_rounding_member(
    declaration: CandidateDeclaration, *, factor: Label
) -> CandidateDeclaration:
    """Return ``declaration`` with factor ``factor``'s flag-sector sum rounding.

    The accepted-format V3 golden's construction
    (``tests/golden/test_protocol_compiler_marks_executed.py``, case (2)), on
    one factor's one-dimensional flag sector: ``F_0`` and ``F_fl`` carry
    ``fl(0.9)`` and ``fl(0.1)`` there, ``F_1`` keeps ``[0]``. Every entry is
    binary64, the computed total is exactly ``[1]`` so (C) holds, and the third
    addition, ``fl(0.9) + fl(0.1) = 1 + 2**-55``, rounds, so (S) fails at
    outcome index 3. The other factor and the data sector are untouched.

    It edits the DECLARATION, as the golden does: through the specification
    the chain's own (C3) decides the same family first, so V3's refusal is
    reached on the candidate itself.
    """
    nine, one = F(8106479329266893, 2**53), F(3602879701896397, 2**55)
    families = declaration.bob_factors
    assert families is not None
    index = declaration.measured_factor_labels.index(factor)
    family = families.factors[index]
    flag = {"0": nine, "fl": one}
    members = tuple(
        BlockOperator.of(
            member.sector_map,
            [member.blocks[0], matrix([[flag[label]]])],
        )
        if label in flag
        else member
        for label, member in zip(family.alphabet, family.members, strict=True)
    )
    factors = list(families.factors)
    factors[index] = replace(family, members=members)
    return replace(
        declaration, bob_factors=replace(families, factors=tuple(factors))
    )


@pytest.mark.contract
def test_v3_summation_refusal_names_the_measured_factor() -> None:
    """req:validator-refusals (iii): the general-format detail carries the factor.

    ``bob_povm_summation_rounds`` carries "the sector and the outcome index
    ... and in the general format the factor as well": two factors of the same
    party ``B`` are told apart only by the factor label.
    """
    result = compile_specification(_same_party_factors(weighted=False))
    assert result.declaration is not None
    outcome = check_v3(_with_rounding_member(result.declaration, factor="b"))
    assert outcome.refusal is not None
    assert str(outcome.refusal.reason) == "bob_povm_summation_rounds"
    assert "measured factor 'b'" in outcome.refusal.detail
    assert "(party 'B')" in outcome.refusal.detail
    assert "sector 'fl'" in outcome.refusal.detail
    assert "outcome index 3" in outcome.refusal.detail


@pytest.mark.contract
def test_the_party_local_entry_of_the_example_is_emitted_with_its_scope() -> None:
    """(DX6), (e'): the scope is passed through unchanged and no lift is formed."""
    entry = _flag_entry(FACTORS[1])
    result = compile_specification(_two_party_specification(entries=(entry,)))
    assert not result.refuses, result.refusal
    declaration = result.declaration
    assert declaration is not None
    assert len(declaration.constraint_list) == 1
    emitted = declaration.constraint_list[0]
    assert emitted.scope == FACTORS[1]
    assert emitted.tag is RhsTag.PARTY_LOCAL
    assert emitted.rhs == F(1, 8)
    record = declaration.as_machine_record()
    assert record["constraint_scope"] == [FACTORS[1]]
    assert record["constraint_rhs_tag"] == ["party_local"]
    # (G3)(a): the party-local form is LICENSED, so the flag is true.
    assert result.key_length_eligible


@pytest.mark.contract
def test_a_scope_naming_no_measured_factor_refuses_the_compilation() -> None:
    """``constraint_scope_not_a_factor``, reached through the compilation map.

    The string was reachable on a hand-built candidate at part 1; this is the
    same refusal reached by ``def:compile`` on a specification, which is what
    makes it a refusal of an INPUT and not only of a candidate.
    """
    from certiqs_key.protocol_compiler.reasons import RefusalReason

    entry = _flag_entry(FACTORS[1], scope="B")
    result = compile_specification(_two_party_specification(entries=(entry,)))
    assert result.refuses
    assert result.refusal is not None
    assert result.refusal.reason is RefusalReason.CONSTRAINT_SCOPE_NOT_A_FACTOR


# ---------------------------------------------------------------------------
#  A BBM92-shaped specification: party-local entries on BOTH arms
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_a_bbm92_shaped_specification_compiles() -> None:
    """Two measured factors, ``d_A = 1``, untrusted source, party-local entries.

    The shape ``meat-core``'s design note reads as BBM92 -- "untrusted source, two
    measured factors, party-local entries" -- with one entry per arm, each scoped
    to its own factor. IT COMPILES, and the emitted declaration carries two
    factors, two scoped entries and no product datum.
    """
    entries = (_flag_entry(FACTORS[0]), _flag_entry(FACTORS[1]))
    result = compile_specification(_two_party_specification(entries=entries))
    assert not result.refuses, result.refusal
    declaration = result.declaration
    assert declaration is not None
    assert [entry.scope for entry in declaration.constraint_list] == list(FACTORS)
    # BOTH entries are licensed, in untrusted-source mode, by their tag alone.
    assert result.key_length_eligible
    assert not declaration.is_trusted_mode
    # AND NO PRODUCT OPERATOR IS A DATUM: the emitted record carries the factors
    # and the rule, and `bob_povm` -- the accepted format's one family -- is empty.
    record = declaration.as_machine_record()
    assert record["bob_povm"] == []
    factors = record["bob_povm_factors"]
    assert isinstance(factors, list)
    assert len(factors) == 2
    # The general dock receives these from the emitted declaration itself.  It
    # must not reuse the degenerate declaration embedded by an adapter: X need
    # not be either party's readout alphabet, and both codomains are declared
    # protocol data.
    assert record["alice_alphabet"] == list(declaration.alice_alphabet)
    assert record["acceptance_values"] == list(declaration.acceptance_alphabet)
    assert record["key_value_count"] == len(declaration.key_alphabet)
    assert record["accept_statistic"] == [
        [list(kappa), declaration.acceptance_value(kappa)]
        for kappa in declaration.announcement_classes()
    ]
    assert record["key_map"] == [
        [[x, v], declaration.key_map[(x, v)]]
        for x, v in declaration.outcome_pairs()
    ]


@pytest.mark.contract
def test_a_source_segment_in_untrusted_mode_is_refused_before_link_use() -> None:
    """C4's mode half: non-empty source segment plus ``nomarg`` is refused.

    The fixture deliberately reuses a well-typed receiver link in the source
    position.  The declared source mode is the earlier condition: in untrusted
    mode no source map is licensed, so neither that link's kind nor its channel
    can affect the result.  This also distinguishes the condition from the
    trusted ``d_A = 1`` residual, whose marginal slot is ``[1]`` rather than
    ``nomarg`` and for which no additional refusal is added.
    """
    specification = _two_party_specification()
    assert specification.source.source_mode is SourceMode.UNTRUSTED
    chain = specification.chain
    assert isinstance(chain, ReductionChain)
    with_source = replace(
        specification,
        chain=ReductionChain(
            source_segment=(
                replace(chain.receiver_segment[0], segment=LinkStage.SOURCE),
            ),
            receiver_segment=chain.receiver_segment,
            outcome_correspondence=dict(chain.outcome_correspondence),
        ),
    )
    result = compile_specification(with_source)
    assert result.refuses
    assert result.refusal is not None
    assert str(result.refusal.reason) == "source_segment_in_untrusted_mode"
    assert "length 1" in result.refusal.detail
    assert "untrusted-source mode" in result.refusal.detail


# ---------------------------------------------------------------------------
#  ex:transcript: three messages, the third reading the first two
# ---------------------------------------------------------------------------


def _three_message_transcript() -> AnnouncementTranscript:
    """Return ``ex:transcript``'s three messages, on this file's readouts.

    The example's shape with its own letters: (m1) Alice announces the round
    type, (m2) Bob discloses his letter on test rounds and only the detection on
    generation rounds, (m3) Alice discloses hers on detected test rounds. The
    readouts here are the two factors' letters, so "Alice's round type" is read
    off her own factor's letter -- which is what makes the example's point
    expressible at all: ``a_2`` depends on ``kappa_1`` and on nothing of ``x``.
    """
    first = Message(
        sender=str(Party.ALICE),
        alphabet=("test", "gen"),
        table={
            (readout, ()): ("test" if readout == "0" else "gen")
            for readout in FACTOR_LETTERS
        },
    )
    second = Message(
        sender=str(Party.BOB),
        alphabet=("0", "1", "click", "none"),
        table={
            (readout, (kappa,)): (
                "none"
                if readout == "fl"
                else (readout if kappa == "test" else "click")
            )
            for readout in FACTOR_LETTERS
            for kappa in ("test", "gen")
        },
    )
    third = Message(
        sender=str(Party.ALICE),
        alphabet=("0", "1", "star"),
        table={
            (readout, (first_value, second_value)): (
                readout
                if first_value == "test" and second_value != "none" and readout != "fl"
                else "star"
            )
            for readout in FACTOR_LETTERS
            for first_value in ("test", "gen")
            for second_value in ("0", "1", "click", "none")
        },
    )
    return AnnouncementTranscript(messages=(first, second, third))


@pytest.mark.contract
def test_ex_transcript_compiles_and_bob_reads_alices_earlier_message() -> None:
    """``ex:transcript``: what the accepted format could not say, compiled.

    "With two maps ``a_A`` on ``O_A`` and ``a_B`` on ``O_B``, Bob's announcement
    is a function of ``v`` alone and CANNOT DEPEND ON THE ROUND TYPE, which he
    learns only from (m1)". Here it does, and party computability holds BY THE
    SIGNATURES: ``a_2`` has no argument through which ``x`` could enter except the
    message Alice has made public.
    """
    transcript = _three_message_transcript()
    specification = _two_party_specification(transcript=transcript)
    result = compile_specification(specification)
    assert not result.refuses, result.refusal
    declaration = result.declaration
    assert declaration is not None
    assert declaration.transcript is not None
    assert declaration.transcript.length == 3
    # THE DERIVED K IS THE PRODUCT OF THE THREE ALPHABETS and is declared by no
    # one; the classes that OCCUR are fewer, the tables being total anyway.
    assert len(declaration.announcement_classes()) == 2 * 4 * 3
    occurring = {
        declaration.announcement(x, v) for x, v in declaration.outcome_pairs()
    }
    assert occurring < set(declaration.announcement_classes())
    # (m2) READS (m1): the same Bob readout announces differently under the two
    # round types, which is the example's own point.
    test_round = declaration.announcement("x0", f"0{PRODUCT_LABEL_SEPARATOR}1")
    gen_round = declaration.announcement("x0", f"1{PRODUCT_LABEL_SEPARATOR}1")
    assert test_round[0] == "test" and test_round[1] == "1"
    assert gen_round[0] == "gen" and gen_round[1] == "click"


# ---------------------------------------------------------------------------
#  A decoy-shaped specification, and the fence it stops at
# ---------------------------------------------------------------------------


def _decoy_presentation_specification(
    *, segment_free: bool
) -> SourceSpecification:
    """Return the decoy emission's ``S_src``, with or without its tagging link.

    ``transmitter/decoy/cor:emitted-decoy`` (i): the declaration's data ARE a
    source specification in trusted-source mode with the certificate supplied as
    an ensemble presentation and "a non-empty source segment". ``segment_free``
    is the HAND-BUILT VARIANT of the same tagged ensemble declared directly as
    the virtual source with an empty segment, which is what lets everything up to
    the fence be exercised.
    """
    from decoy_support import tagged_declaration

    emitted = tagged_declaration()
    spec = emitted.as_source_specification()
    if not segment_free:
        return spec
    return SourceSpecification(
        signal_alphabet=spec.signal_alphabet,
        transmitted_dim=spec.transmitted_dim,
        signal_weights=dict(spec.signal_weights),
        signal_states=None,
        source_mode_request=SourceMode.TRUSTED,
        ensemble_presentation=spec.ensemble_presentation,
        source_segment=(),
    )


@pytest.mark.contract
def test_ensemble_source_has_no_conditional_povm_to_decide() -> None:
    """An ensemble artefact's deliberately empty POVM table is never read."""
    source_specification = _decoy_presentation_specification(segment_free=True)
    dim = source_specification.transmitted_dim
    state = scale(F(1, dim), identity(dim))
    artifact = emit_artifact(
        replace(
            source_specification,
            signal_states=dict.fromkeys(source_specification.signal_alphabet, state),
        )
    ).require()
    source = SourcePart(artifact=artifact)
    specification = replace(_two_party_specification(), source=source)
    decision = decide_every_conditional_family(specification)
    assert decision.refusal is None


@pytest.mark.contract
def test_source_links_cannot_be_attached_to_an_unrelated_artifact() -> None:
    """The separate typed copy cannot manufacture provenance (A3)."""
    from decoy_support import tagged_declaration

    links = tagged_declaration().source_segment
    unrelated = _trivial_source().artifact
    with pytest.raises(
        MalformedInputError, match=r"must equal.*own source_segment"
    ):
        SourcePart(artifact=unrelated, source_links=links)

    carrying = replace(unrelated, source_segment=links)
    assert SourcePart(artifact=carrying, source_links=links).source_links == links


@pytest.mark.contract
def test_accepted_format_rejects_injected_decoy_link() -> None:
    """A3 is decided before format dispatch from supplier-owned evidence."""
    from decoy_support import tagged_declaration
    from instances.bb84.specification import bb84_specification

    from certiqs_key.protocol_compiler.docking_reductions import dock_source_segment

    links = tagged_declaration().source_segment
    specification = bb84_specification(F(1, 2), F(1, 2), F(1, 2), F(1, 2))
    generic = replace(specification.source.artifact, source_segment=links)
    injected = replace(
        specification,
        source=SourcePart(artifact=generic, source_links=links),
        chain=dock_source_segment(specification.chain, links),
    )
    assert not injected.is_general_format
    result = compile_specification(injected)
    assert result.refusal is not None
    assert str(result.refusal.reason) == "source_segment_not_from_admitting_module"


@pytest.mark.contract
def test_an_artifact_segment_the_chain_does_not_carry_is_refused() -> None:
    """The typed segment and the chain's must agree even where the chain's is empty.

    bb84 on the Band-A route, its artefact carrying the real decoy link and
    its chain left alone (``L_s = 0`` on the record). Were the comparison
    skipped for an empty chain segment, the specification would compile on
    the Band-A route with A-IDEAL and no (A1)--(A3) decision on the link.
    """
    from decoy_support import tagged_declaration
    from instances.bb84.specification import bb84_specification

    links = tagged_declaration().source_segment
    specification = bb84_specification(F(1, 2), F(1, 2), F(1, 2), F(1, 2))
    generic = replace(specification.source.artifact, source_segment=links)
    injected = replace(
        specification, source=SourcePart(artifact=generic, source_links=links)
    )
    assert not injected.chain.source_segment
    result = compile_specification(injected)
    assert result.refusal is not None
    assert str(result.refusal.reason) == "source_segment_not_from_admitting_module"
    assert "the chain carries 0 link(s)" in result.refusal.detail


@pytest.mark.contract
def test_general_format_rejects_an_untrusted_injected_source_segment() -> None:
    """The C4 mode decision is shared by accepted and general assemblies."""
    from decoy_support import tagged_declaration

    from certiqs_key.protocol_compiler.docking_reductions import dock_source_segment

    links = tagged_declaration().source_segment
    specification = _two_party_specification()
    generic = replace(specification.source.artifact, source_segment=links)
    injected = replace(
        specification,
        source=SourcePart(artifact=generic, source_links=links),
        chain=dock_source_segment(specification.chain, links),
    )
    result = compile_specification(injected)
    assert result.refusal is not None
    assert str(result.refusal.reason) == "source_segment_in_untrusted_mode"


@pytest.mark.contract
def test_ensemble_dense_and_block_marginals_must_agree_exactly() -> None:
    """Neither of the supplier's twin carriers may silently replace the other."""
    from decoy_support import tagged_declaration

    artifact = tagged_declaration().as_transmitter_artifact()
    replacement = scale(F(1, artifact.alice_dim), identity(artifact.alice_dim))
    assert artifact.alice_marginal != replacement
    inconsistent = replace(artifact, alice_marginal=replacement)
    with pytest.raises(
        MalformedInputError, match=r"dense alice_marginal.*direct sum"
    ):
        SourcePart(artifact=inconsistent, source_links=inconsistent.source_segment)


@pytest.mark.contract
def test_admitted_decoy_carrier_still_needs_its_wcp_ledger_row() -> None:
    """Supplier provenance does not bypass A2's exact ledger comparison."""
    from decoy_support import tagged_declaration

    from certiqs_key.protocol_compiler.docking_reductions import dock_source_segment

    artifact = tagged_declaration().as_transmitter_artifact()
    missing = replace(
        artifact,
        assumption_ledger=tuple(
            row for row in artifact.assumption_ledger if row != "wcp_source_model"
        ),
    )
    specification = _two_party_specification()
    injected = replace(
        specification,
        source=SourcePart(artifact=missing, source_links=missing.source_segment),
        chain=dock_source_segment(specification.chain, missing.source_segment),
    )
    result = compile_specification(injected)
    assert result.refusal is not None
    assert str(result.refusal.reason) == "source_link_assumption_not_in_ledger"


@pytest.mark.contract
def test_source_link_admission_reads_the_emitted_machine_ledger() -> None:
    """Compiler A1--A3 consume the ledger spelling the transmitter emits."""
    from decoy_support import tagged_declaration

    from certiqs_key.protocol_compiler.chain import check_source_segment
    from certiqs_key.transmitter.decoy import DECOY_ASSUMPTION_LEDGER

    assert (
        check_source_segment(
            tagged_declaration().source_segment,
            assumption_ledger=DECOY_ASSUMPTION_LEDGER,
            from_admitting_module=True,
        )
        is None
    )


@pytest.mark.contract
def test_receiver_part_rejects_a_povm_on_the_wrong_dimension() -> None:
    """A declared receiver dimension is the dimension of every physical effect."""
    with pytest.raises(MalformedInputError, match=r"physical_dim=3"):
        ReceiverPart(
            physical_dim=3,
            physical_povm=DirectPovm(("only",), {"only": identity(1)}),
        )


# ---------------------------------------------------------------------------
#  NO PRODUCT BLOCK AND NO LIFTED OPERATOR ON THE COMPILE PATH, STATICALLY
# ---------------------------------------------------------------------------

#: Every call in ``src/certiqs_key/protocol_compiler`` that forms a Kronecker
#: product or a product block, BY FILE AND BY THE FUNCTION IT SITS IN, with the
#: reason each is licensed. The binding is ``def:compile``'s and the interface's:
#: the product sector map, the product alphabet, the joint sectors, the product
#: family and the lifted operator ``1 (x) O_k (x) 1`` are formed by NO ONE, "at
#: any step, V7's legs included". The four sites below form none of those.
#:
#: They are listed by file AND function rather than allowed by a blanket
#: exemption, so that a fifth call has to be added here with its reason -- the
#: shape ``tests/unit/test_reductions_factors.py``'s declared-sites test takes for
#: the same binding on the supplier's side.
DECLARED_KRON_SITES: dict[str, set[str]] = {
    # eq:witness-general itself: tau^(t)_A (x) 1_{Q_s}/d_Q, ONE JOINT BLOCK at a
    # time. A candidate the compiler exhibits, licensed to be a product, and not
    # a lifted constraint operator.
    "feasibility.py": {"default_witness", "constraint_value"},
    # The honest joint outcome distribution, on the RUN tier's side of the
    # boundary: kron(M_x, F_v) per sector for a caller computing statistics, and
    # no predicate of the validator calls it.
    "statistics.py": {"joint_distribution", "_joint_distribution_general"},
    # def:weighted's setting-dependent complement, a product on ONE party's own
    # system between its family and its choice register -- not a product of two
    # measured factors.
    "weights.py": {"choice_mass"},
}


@pytest.mark.contract
def test_no_product_block_is_formed_anywhere_on_the_compile_path() -> None:
    """THE BINDING OF ``def:compile``'S GENERAL PARAGRAPH, DECIDED STATICALLY.

    "The product sector map, its order, the product alphabet and the joint
    sectors are DERIVED ... and are declared, formed and emitted by no one"; "no
    product of two factors' families is formed by this map"; "the lifted operator
    ``1 (x) O_k (x) 1`` of (DX6) is never formed as a datum either". A Kronecker
    product is how each of those would be built, so the test reads the package:
    every call naming ``kron`` or ``product_block`` sits at one of
    :data:`DECLARED_KRON_SITES`, and the three files of the general format's
    ASSEMBLY -- ``compile.py``, ``declaration.py`` and ``spec.py`` -- contain
    none.

    WHAT IT WOULD ALLOW AND DELIBERATELY DOES NOT: a helper in ``domain/`` that
    formed a product internally would pass this test, which is why
    ``test_protocol_general_format.py``'s dynamic test stays -- it poisons
    :func:`~certiqs_key.foundations.exact.kron` and runs a scoped entry's verification
    to a verdict anyway. The two catch different mistakes and neither is the
    other's weaker form.
    """
    import ast
    from pathlib import Path

    root = (
        Path(__file__).resolve().parents[2]
        / "src"
        / "certiqs_key"
        / "protocol_compiler"
    )
    found: list[tuple[str, str, str]] = []
    for path in sorted(root.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        # THE INNERMOST ENCLOSING FUNCTION NAMES THE SITE. Keep an explicit
        # lexical stack rather than depending on ``ast.walk``'s traversal order.
        enclosing: dict[ast.AST, str] = {}

        class EnclosingFunctions(ast.NodeVisitor):
            def __init__(self, target: dict[ast.AST, str]) -> None:
                self.stack: list[str] = []
                self.target = target

            def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
                self.stack.append(node.name)
                self.generic_visit(node)
                self.stack.pop()

            visit_AsyncFunctionDef = visit_FunctionDef

            def visit_Call(self, node: ast.Call) -> None:
                if self.stack:
                    self.target[node] = self.stack[-1]
                self.generic_visit(node)

        EnclosingFunctions(enclosing).visit(tree)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            called = node.func
            name = (
                called.id
                if isinstance(called, ast.Name)
                else called.attr
                if isinstance(called, ast.Attribute)
                else ""
            )
            if name in {"kron", "product_block"}:
                found.append((path.name, enclosing.get(node, "<module>"), name))
    by_file: dict[str, set[str]] = {}
    for file, function, _ in found:
        by_file.setdefault(file, set()).add(function)
    assert by_file == DECLARED_KRON_SITES, found
    # AND THE ASSEMBLY ITSELF FORMS NONE, which is the sentence the binding is:
    # the factor list, the derived orders, the per-factor families, the transcript
    # and the scoped entries are assembled without a single product array.
    assert not {"compile.py", "declaration.py", "spec.py"} & set(by_file)
    # The one product block is formed by the honest-statistics NUMERICAL
    # consumer, never by compilation or a predicate.
    assert [
        (file, function)
        for file, function, name in found
        if name == "product_block"
    ] == [("statistics.py", "_joint_distribution_general")]


@pytest.mark.contract
def test_direct_core_source_link_needs_its_admitting_module() -> None:
    """C4 keeps A3: a raw core specification cannot attest its own admission.

    The registered tagging kind reaches the admitting-module condition and not
    an empty-source-segment condition. Actual decoy emission uses its supplier artifact.
    """
    result = emit_artifact(_decoy_presentation_specification(segment_free=False))
    assert result.artifact is None
    assert result.refusal is not None
    assert str(result.refusal.reason) == "source_segment_not_from_admitting_module"
