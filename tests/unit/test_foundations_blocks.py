"""The frozen shared operator type of ``spec/architecture.md`` 2.9.

Motivation: the section makes the sector-map comparison THE consumer's
structural check -- "a disagreement is a refusal with a machine-readable
reason" -- and the whole comparison is executed here. ``domain/`` is the one
tier every module depends on.

WHAT IS ASSERTED HERE. The four disagreement components in the order the type
reports them, the refusals :class:`BlockOperator` makes on a list that is not a
block list against its own map, the per-block admission decisions, and the
ONE-WAY dense rendering: "the identity ``F_v = bigoplus_s F_v^(s)`` is what the
list MEANS, not a condition on it", so ``dense()`` goes from the list to the
array and there is no route back.

AND 2.9's FACTORISED map: that the single-factor default flattens to exactly
the map it was given -- the assertion that the single-factor consumers do not
change behaviour -- that the product
order is the factor order with the last factor fastest, that the comparison
names the first disagreeing FACTOR, and the three refusals the product makes
rather than deciding something that is not its to decide.

AND THE SYSTEM TAG AND THE ``A`` SIDE. The design rule is one sentence -- the
one-Alice-sector, one-``Q``-factor format is the special case of the general
one, ENTRY FOR ENTRY -- so what is executed here is that sentence: the default
system is ``Q``, an integer ``d_A`` builds the joint operator with the block
list of the one-sector case, the dense rendering of a one-Alice-sector
operator is the one-sector array, and a one-sector ``A`` family is the dense
``M_x``. Beside it, the
generalisation: a two-Alice-sector joint operator, the refusals that keep the
``A`` factor single and first, and ``system`` as a ground of the comparison.
"""

from __future__ import annotations

from fractions import Fraction as F

import pytest

from certiqs_key.foundations.blocks import (
    DEFAULT_FACTOR_SYSTEM,
    FACTORISED_MAP_COMPONENTS,
    IMPLICIT_ALICE_SECTOR_LABEL,
    PRODUCT_LABEL_SEPARATOR,
    SECTOR_MAP_COMPONENTS,
    BlockKind,
    BlockOperator,
    FactorisedSectorMap,
    JointBlockOperator,
    SectorFactor,
    SectorStructure,
    SystemTag,
    block_sum_in_declared_order,
    single_alice_sector,
)
from certiqs_key.foundations.errors import MalformedInputError
from certiqs_key.foundations.exact import (
    Cx,
    Matrix,
    equal,
    identity,
    matrix,
    sum_in_declared_order,
    zeros,
)

K = BlockKind.PROOF_SECTOR
MAP = SectorStructure(labels=("s0", "s1"), dims=(1, 2), block_kind=K)


@pytest.mark.parametrize(
    ("other", "component"),
    [
        (SectorStructure(labels=("s1", "s0"), dims=(2, 1), block_kind=K), "order"),
        (SectorStructure(labels=("s0", "s2"), dims=(1, 2), block_kind=K), "identifier"),
        (SectorStructure(labels=("s0", "s1"), dims=(1, 3), block_kind=K), "dimension"),
        (
            SectorStructure(
                labels=("s0", "s1"), dims=(1, 2), block_kind=BlockKind.NUMERICAL_BLOCK
            ),
            "block_kind",
        ),
    ],
)
def test_every_component_of_the_sector_map_comparison_is_reported(
    other: SectorStructure, component: str
) -> None:
    """Each of the four grounds is produced, and exactly one is."""
    found = MAP.disagreement(other)
    assert found is not None
    assert found.component == component
    assert found.component in SECTOR_MAP_COMPONENTS
    assert found.detail
    # The block kind is not a position in a list; every other ground is.
    assert (found.position is None) is (component == "block_kind")
    assert not MAP.agrees_with(other)


def test_an_equal_map_agrees_and_reports_nothing() -> None:
    """A comparison with itself is the one case that returns ``None``."""
    assert MAP.disagreement(MAP) is None
    assert MAP.agrees_with(MAP)
    assert MAP.total_dim == 3
    assert MAP.count == 2
    assert MAP.entries == (("s0", 1), ("s1", 2))


def test_a_map_that_is_not_a_map_is_refused_rather_than_completed() -> None:
    """``__post_init__``: the three malformed presentations, each refused."""
    with pytest.raises(MalformedInputError):
        SectorStructure(labels=("s0", "s1"), dims=(1,), block_kind=K)
    with pytest.raises(MalformedInputError):
        SectorStructure(labels=("s0", "s0"), dims=(1, 2), block_kind=K)
    with pytest.raises(MalformedInputError):
        # "A value outside the enum is a malformed declaration and is refused
        # as one -- never mapped to a nearest member, never defaulted."
        SectorStructure(labels=("s0",), dims=(1,), block_kind="proof")  # type: ignore[arg-type]


def test_a_block_list_is_refused_against_its_own_map() -> None:
    """``BlockOperator`` takes BLOCKS and decides that they are its map's."""
    one = matrix([[F(1)]])
    two = identity(2)
    operator = BlockOperator.of(MAP, [one, two])
    assert operator.is_positive_semidefinite()
    assert operator.is_hermitian()
    with pytest.raises(MalformedInputError):
        BlockOperator.of(MAP, [one])
    with pytest.raises(MalformedInputError):
        BlockOperator.of(MAP, [one, one])
    with pytest.raises(MalformedInputError):
        BlockOperator.of(MAP, [one, matrix([[F(1), F(0)]])])


def test_the_per_block_decisions_are_per_block_and_decided_at_zero() -> None:
    """2.9: "positivity and completeness are per block", at zero and no window."""
    indefinite = matrix([[F(-1, 4), F(0)], [F(0), F(1)]])
    negative = BlockOperator.of(MAP, [matrix([[F(1)]]), indefinite])
    assert negative.is_hermitian()
    assert not negative.is_positive_semidefinite()
    skew = BlockOperator.of(
        MAP,
        [matrix([[Cx(F(0), F(1))]]), identity(2)],
    )
    assert not skew.is_hermitian()


def test_the_dense_rendering_is_one_way_and_decides_nothing() -> None:
    """``dense()`` builds the direct sum; nothing reads a dense array back in."""
    one = matrix([[F(1, 2)]])
    two = matrix([[F(1, 4), F(0)], [F(0), F(3, 4)]])
    dense = BlockOperator.of(MAP, [one, two]).dense()
    assert len(dense) == MAP.total_dim
    assert dense[0][0].re == F(1, 2)
    assert dense[1][1].re == F(1, 4)
    assert dense[2][2].re == F(3, 4)
    # The off-sector entries are zero BY CONSTRUCTION -- there is no route by
    # which a caller hands over a d_Q x d_Q array with one and has it
    # truncated, which is why nothing verifies them.
    assert dense[0][1].is_zero and dense[1][0].is_zero
    assert dense[0][2].is_zero and dense[2][0].is_zero
    assert not hasattr(BlockOperator, "of_dense")


def test_a_sector_projector_is_a_block_list_and_not_a_full_space_array() -> None:
    """2.9's operator type, on the projectors the map itself supplies.

    ``Pi_s`` is ``1_{d_s}`` on its own block and the zero block on every other,
    carried as the list; the dense
    rendering is formed by the caller that wants it, and the projectors then
    sum to the identity and are mutually orthogonal there.
    """
    projectors = MAP.projectors()
    assert len(projectors) == MAP.count
    for index, projector in enumerate(projectors):
        assert isinstance(projector, BlockOperator)
        assert projector.sector_map is MAP
        for position, block in enumerate(projector.blocks):
            dim = MAP.dims[position]
            expected = identity(dim) if position == index else zeros(dim, dim)
            assert equal(block, expected)
        assert projector.is_positive_semidefinite()
    assert equal(
        MAP.projector(0).dense(),
        matrix([[F(1), F(0), F(0)], [F(0), F(0), F(0)], [F(0), F(0), F(0)]]),
    )


ALICE = SectorStructure(labels=("a0", "a1"), dims=(1, 2), block_kind=K)
BOB = SectorStructure(labels=("b0", "b1", "b2"), dims=(1, 2, 3), block_kind=K)
PRODUCT_MAP = FactorisedSectorMap(
    factors=(
        SectorFactor(party="A", sectors=ALICE),
        SectorFactor(party="B", sectors=BOB),
    )
)


def test_the_single_factor_default_flattens_to_the_map_it_was_given() -> None:
    """Today's map is one factor, and flattening it changes nothing.

    This is the assertion that carries "nothing that consumes a single-factor
    map changes behaviour" (spec/architecture.md 2.9): the flattened structure
    is the handed-in one entry for entry and kind for kind, so every consumer
    that compares sector maps sees the map it saw before.
    """
    single = FactorisedSectorMap.single_factor("B", MAP)
    assert single.factors == (SectorFactor(party="B", sectors=MAP),)
    assert single.parties == ("B",)
    assert single.block_kind is MAP.block_kind
    assert single.flattened() == MAP
    assert single.agrees_with(FactorisedSectorMap.single_factor("B", MAP))


def test_the_product_order_is_the_factor_order_with_the_last_factor_fastest() -> None:
    """The declared convention, which is what keeps two producers agreeing."""
    flattened = PRODUCT_MAP.flattened()
    joined = PRODUCT_LABEL_SEPARATOR.join
    assert flattened.labels == (
        joined(("a0", "b0")),
        joined(("a0", "b1")),
        joined(("a0", "b2")),
        joined(("a1", "b0")),
        joined(("a1", "b1")),
        joined(("a1", "b2")),
    )
    assert flattened.dims == (1, 2, 3, 2, 4, 6)
    assert flattened.total_dim == ALICE.total_dim * BOB.total_dim
    assert flattened.block_kind is K
    # Swapping the factors is a DIFFERENT product, not the same one written
    # differently: that is the point of fixing the order.
    swapped = FactorisedSectorMap(factors=tuple(reversed(PRODUCT_MAP.factors)))
    assert swapped.flattened().labels != flattened.labels


@pytest.mark.parametrize(
    ("other", "component", "position"),
    [
        (
            FactorisedSectorMap.single_factor("A", ALICE),
            "factor_count",
            None,
        ),
        (
            FactorisedSectorMap(
                factors=(
                    SectorFactor(party="A", sectors=ALICE),
                    SectorFactor(party="Bob", sectors=BOB),
                )
            ),
            "party",
            1,
        ),
        (
            FactorisedSectorMap(
                factors=(
                    SectorFactor(
                        party="A",
                        sectors=SectorStructure(
                            labels=("a0", "a1"), dims=(1, 5), block_kind=K
                        ),
                    ),
                    SectorFactor(party="B", sectors=BOB),
                )
            ),
            "dimension",
            0,
        ),
        (
            FactorisedSectorMap(
                factors=(
                    SectorFactor(party="A", sectors=ALICE),
                    SectorFactor(
                        party="B",
                        sectors=SectorStructure(
                            labels=("b1", "b0", "b2"), dims=(2, 1, 3), block_kind=K
                        ),
                    ),
                )
            ),
            "order",
            1,
        ),
    ],
)
def test_the_comparison_names_the_first_disagreeing_factor(
    other: FactorisedSectorMap, component: str, position: int | None
) -> None:
    """Factor by factor in the product order, with the ground it failed on."""
    found = PRODUCT_MAP.disagreement(other)
    assert found is not None
    assert found.component == component
    assert found.component in FACTORISED_MAP_COMPONENTS
    assert found.factor_position == position
    assert found.detail
    if component in SECTOR_MAP_COMPONENTS:
        # The single-map comparison is reached UNCHANGED inside the factor, and
        # its own report is carried whole rather than flattened away.
        assert found.within is not None
        assert found.within.component == component
        assert position is not None
        assert found.party == PRODUCT_MAP.factors[position].party
    else:
        assert found.within is None
    assert PRODUCT_MAP.agrees_with(PRODUCT_MAP)


@pytest.mark.parametrize(
    ("factors", "because"),
    [
        ((), "AT LEAST ONE factor"),
        (
            (
                SectorFactor(party="A", sectors=ALICE),
                SectorFactor(
                    party="B",
                    sectors=SectorStructure(
                        labels=("b0",), dims=(2,), block_kind=BlockKind.PHYSICAL_SECTOR
                    ),
                ),
            ),
            "ONE block kind",
        ),
    ],
)
def test_a_product_refuses_rather_than_deciding_what_is_not_its_to_decide(
    factors: tuple[SectorFactor, ...], because: str
) -> None:
    """An empty product and a product of differently-licensed factors.

    The second is 2.3's rule in code: the kind records WHY the decomposition is
    licensed, so a product of factors licensed differently has no kind this
    type may supply -- and supplying one would be the same mistake
    ``SectorStructure`` refuses by having no default.
    """
    with pytest.raises(MalformedInputError, match=because):
        FactorisedSectorMap(factors=factors)


def test_a_factor_identifier_may_not_contain_the_product_separator() -> None:
    """Otherwise the flattened identifier does not say which factor it is."""
    with pytest.raises(MalformedInputError, match="product separator"):
        SectorFactor(
            party="A",
            sectors=SectorStructure(
                labels=(f"a{PRODUCT_LABEL_SEPARATOR}0",), dims=(1,), block_kind=K
            ),
        )
    with pytest.raises(MalformedInputError, match="non-empty party label"):
        SectorFactor(party="", sectors=ALICE)


# ---------------------------------------------------------------------------
#  The system tag
# ---------------------------------------------------------------------------

#: The decoy shape: an ``A`` factor first, a ``Q`` factor after it.
DECOY_MAP = FactorisedSectorMap(
    factors=(
        SectorFactor(party="alice", sectors=ALICE, system=SystemTag.A),
        SectorFactor(party="bob", sectors=BOB, system=SystemTag.Q),
    )
)


def test_a_factor_carries_the_q_system_unless_it_says_otherwise() -> None:
    """The default is what makes every factor written before the tag unchanged."""
    assert DEFAULT_FACTOR_SYSTEM is SystemTag.Q
    assert SectorFactor(party="B", sectors=MAP).system is SystemTag.Q
    assert FactorisedSectorMap.single_factor("B", MAP).systems == (SystemTag.Q,)
    assert PRODUCT_MAP.systems == (SystemTag.Q, SystemTag.Q)
    assert tuple(tag.value for tag in SystemTag) == ("A", "Q")


def test_a_factor_carries_a_system_of_the_closed_vocabulary() -> None:
    """A value outside the enum is malformed, never mapped to a nearest member."""
    with pytest.raises(MalformedInputError, match="SystemTag"):
        SectorFactor(party="A", sectors=ALICE, system="alice")  # type: ignore[arg-type]


def test_the_comparison_reports_the_system_as_a_ground_like_the_party() -> None:
    """``system`` is a ground of its own, and it is reported BEFORE the party."""
    assert "system" in FACTORISED_MAP_COMPONENTS
    # The same two maps, the first factor's system changed -- and its party too,
    # so that the ORDER of the two grounds is what this asserts.
    supplied = FactorisedSectorMap(
        factors=(
            SectorFactor(party="somebody", sectors=ALICE, system=SystemTag.Q),
            SectorFactor(party="bob", sectors=BOB, system=SystemTag.Q),
        )
    )
    found = DECOY_MAP.disagreement(supplied)
    assert found is not None
    assert found.component == "system"
    assert found.factor_position == 0
    # The EMITTED map's system and party, as the refusal says what was expected.
    assert found.system is SystemTag.A
    assert found.party == "alice"
    assert found.within is None
    assert "'Q'" in found.detail and "'A'" in found.detail
    assert not DECOY_MAP.agrees_with(supplied)
    assert DECOY_MAP.agrees_with(DECOY_MAP)


def test_the_product_is_read_by_system() -> None:
    """What a consumer needs: each side's factors in product order, and its map."""
    assert DECOY_MAP.factors_of(SystemTag.A) == (DECOY_MAP.factors[0],)
    assert DECOY_MAP.factors_of(SystemTag.Q) == (DECOY_MAP.factors[1],)
    assert DECOY_MAP.flattened_of(SystemTag.A) == ALICE
    assert DECOY_MAP.flattened_of(SystemTag.Q) == BOB
    # A map with no A factor has no A side, and that is None rather than an
    # empty product -- an empty product is not a sector map.
    single = FactorisedSectorMap.single_factor("B", MAP)
    assert single.flattened_of(SystemTag.A) is None
    assert single.flattened_of(SystemTag.Q) == MAP


@pytest.mark.parametrize(
    ("factors", "because"),
    [
        (
            (
                SectorFactor(party="alice", sectors=ALICE, system=SystemTag.A),
                SectorFactor(party="alice", sectors=MAP, system=SystemTag.A),
                SectorFactor(party="bob", sectors=BOB, system=SystemTag.Q),
            ),
            "AT MOST ONE",
        ),
        (
            (
                SectorFactor(party="bob", sectors=BOB, system=SystemTag.Q),
                SectorFactor(party="alice", sectors=ALICE, system=SystemTag.A),
            ),
            "FIRST factor",
        ),
    ],
)
def test_the_a_side_is_single_and_first_or_the_product_is_refused(
    factors: tuple[SectorFactor, ...], because: str
) -> None:
    """Neither is silently repaired: not merged, and not permuted."""
    with pytest.raises(MalformedInputError, match=because):
        FactorisedSectorMap(factors=factors)


def test_a_flattened_identifier_says_which_factor_supplied_which_part() -> None:
    """The flattening is injective, or the product is refused.

    ``_`` is itself a label character, so containment of the two-character
    separator is not enough: ``("a", "a_")`` against ``("b", "_b")`` would
    flatten ``a_`` + ``b`` and ``a`` + ``_b`` to the SAME string, and two
    different product sectors would collide under one identifier. A label may
    end where the separator begins only in the last factor, and begin where it
    ends only in the first.
    """
    trailing = SectorStructure(labels=("a", "a_"), dims=(1, 2), block_kind=K)
    leading = SectorStructure(labels=("b", "_b"), dims=(1, 2), block_kind=K)
    with pytest.raises(MalformedInputError, match="product separator"):
        FactorisedSectorMap(
            factors=(
                SectorFactor(party="alice", sectors=trailing),
                SectorFactor(party="bob", sectors=leading),
            )
        )
    # Each half on its own is refused too, in the position that makes it
    # ambiguous -- and accepted in the position that does not.
    plain = SectorStructure(labels=("b",), dims=(2,), block_kind=K)
    with pytest.raises(MalformedInputError, match="LAST factor"):
        FactorisedSectorMap(
            factors=(
                SectorFactor(party="alice", sectors=trailing),
                SectorFactor(party="bob", sectors=plain),
            )
        )
    with pytest.raises(MalformedInputError, match="FIRST factor"):
        FactorisedSectorMap(
            factors=(
                SectorFactor(party="alice", sectors=plain),
                SectorFactor(party="bob", sectors=leading),
            )
        )
    # A trailing separator character in the LAST factor and a leading one in the
    # FIRST are unambiguous, so they are not refused -- and a one-factor map is
    # both, which is why today's labels (``_X_0_`` and friends) are untouched.
    assert FactorisedSectorMap(
        factors=(
            SectorFactor(party="alice", sectors=leading),
            SectorFactor(party="bob", sectors=trailing),
        )
    ).flattened().labels == (
        "b__a",
        "b__a_",
        "_b__a",
        "_b__a_",
    )
    assert FactorisedSectorMap.single_factor(
        "bob", SectorStructure(labels=("_X_0_",), dims=(1,), block_kind=K)
    ).flattened().labels == ("_X_0_",)


# ---------------------------------------------------------------------------
#  The joint operator: the degenerate case, then the general one
# ---------------------------------------------------------------------------

#: A 2x2 ``A``-side operator with four distinguishable entries.
TAU = matrix([[F(1, 2), F(1, 8)], [F(1, 8), F(1, 4)]])


def _q_blocks(sector_map: SectorStructure) -> list[Matrix]:
    """Return one distinguishable Hermitian block per sector of ``sector_map``."""
    return [
        matrix(
            [
                [F(1 + position, 16) if i == j else F(0) for j in range(dim)]
                for i in range(dim)
            ]
        )
        for position, dim in enumerate(sector_map.dims)
    ]


def _kron(a: Matrix, b: Matrix) -> Matrix:
    """Return ``a (x) b`` with ``a`` major, written out here as the oracle.

    The placement :meth:`JointBlockOperator.dense` makes is checked against this
    rather than against a restatement of its own index formula: for blocks of
    the form ``tau_t (x) X_s`` the direct sum over joint sectors IS the ordinary
    Kronecker product of the two direct sums, because an entry of that product
    vanishes unless both indices lie in the same ``A_t`` and the same ``Q_s``.
    """
    rows = len(a)
    inner = len(b)
    return tuple(
        tuple(
            a[i // inner][j // inner] * b[i % inner][j % inner]
            for j in range(rows * inner)
        )
        for i in range(rows * inner)
    )


def test_an_integer_alice_dim_builds_the_joint_operator_it_always_built() -> None:
    """THE DEGENERATE CASE: the same call, the same block list, the same dense array."""
    blocks = [_kron(TAU, block) for block in _q_blocks(MAP)]
    joint = JointBlockOperator.of(MAP, 2, blocks)
    assert joint.alice_sectors == single_alice_sector(2, K)
    assert joint.alice_sectors.labels == (IMPLICIT_ALICE_SECTOR_LABEL,)
    assert joint.alice_dim == 2
    # One block per Q sector, in the Q map's own order: the list is the list.
    assert joint.blocks == tuple(blocks)
    assert joint.block(0, 1) is blocks[1]
    q_dense = BlockOperator.of(MAP, _q_blocks(MAP)).dense()
    assert equal(joint.dense(), _kron(TAU, q_dense))
    assert len(joint.dense()) == 2 * MAP.total_dim


def test_a_joint_operator_over_two_alice_sectors_is_blocked_per_joint_sector() -> None:
    """The generalisation: one block per ``(t, s)``, of size ``d_{A_t} d_s``."""
    alice_blocks = [matrix([[F(1, 4)]]), TAU]
    alice = SectorStructure(labels=("t0", "t1"), dims=(1, 2), block_kind=K)
    blocks = [
        _kron(alice_block, q_block)
        for alice_block in alice_blocks
        for q_block in _q_blocks(MAP)
    ]
    joint = JointBlockOperator.of(MAP, alice, blocks)
    assert joint.alice_sectors is alice
    joint_map = joint.joint_sectors()
    join = PRODUCT_LABEL_SEPARATOR.join
    assert joint_map.labels == (
        join(("t0", "s0")),
        join(("t0", "s1")),
        join(("t1", "s0")),
        join(("t1", "s1")),
    )
    assert joint_map.dims == (1, 2, 2, 4)
    assert joint_map.block_kind is K
    assert joint.block(1, 0) is blocks[2]
    # The A-first placement, against the Kronecker oracle.
    alice_dense = BlockOperator.of(alice, alice_blocks).dense()
    q_dense = BlockOperator.of(MAP, _q_blocks(MAP)).dense()
    assert equal(joint.dense(), _kron(alice_dense, q_dense))
    assert len(joint.dense()) == alice.total_dim * MAP.total_dim


def test_alice_dim_refuses_rather_than_answering_wrongly() -> None:
    """At two ``A`` sectors no one integer is ``d_A``, so the question is refused."""
    alice = SectorStructure(labels=("t0", "t1"), dims=(1, 2), block_kind=K)
    joint = JointBlockOperator.of(
        MAP,
        alice,
        [
            _kron(alice_block, q_block)
            for alice_block in (matrix([[F(1, 4)]]), TAU)
            for q_block in _q_blocks(MAP)
        ],
    )
    with pytest.raises(MalformedInputError, match="undecomposed A"):
        _ = joint.alice_dim


@pytest.mark.parametrize(
    ("alice_side", "blocks", "because"),
    [
        (2, [identity(2)], "joint blocks"),
        (2, [identity(2), identity(2), identity(2)], "joint blocks"),
        (2, [identity(3), identity(4)], "n_j x n_j"),
        (
            SectorStructure(
                labels=("t0",), dims=(2,), block_kind=BlockKind.PHYSICAL_SECTOR
            ),
            [identity(2), identity(4)],
            "ONE block kind",
        ),
    ],
)
def test_a_joint_block_list_is_refused_against_its_own_maps(
    alice_side: int | SectorStructure, blocks: list[Matrix], because: str
) -> None:
    """The count, the block sizes, and the one block kind the two sides carry."""
    with pytest.raises(MalformedInputError, match=because):
        JointBlockOperator.of(MAP, alice_side, blocks)


def test_a_single_alice_sector_is_a_positive_dimension() -> None:
    """``d_A = 0`` decomposes nothing, and no map is invented for it."""
    with pytest.raises(MalformedInputError, match="positive dimension"):
        single_alice_sector(0, K)


def test_the_joint_map_is_a_product_and_is_refused_as_one() -> None:
    """The joint identifier is a join, so both join refusals bind it.

    The two sides of a joint operator are the two factors of its flattened map,
    so a label that contains the separator, and an ``A`` label that ends where
    the separator begins, make the joint identifier ambiguous in exactly the way
    :func:`check_product_join` describes.
    """
    contains = SectorStructure(
        labels=(f"t0{PRODUCT_LABEL_SEPARATOR}x",), dims=(2,), block_kind=K
    )
    with pytest.raises(MalformedInputError, match="product separator"):
        JointBlockOperator.of(MAP, contains, [identity(2), identity(4)])
    trailing = SectorStructure(labels=("t0_",), dims=(2,), block_kind=K)
    with pytest.raises(MalformedInputError, match="LAST factor"):
        JointBlockOperator.of(MAP, trailing, [identity(2), identity(4)])
    # The Q side is the last factor of the joint map, so a trailing separator
    # character there is unambiguous and is not refused.
    q_trailing = SectorStructure(labels=("s0_",), dims=(2,), block_kind=K)
    unambiguous = JointBlockOperator.of(q_trailing, 2, [identity(4)])
    assert unambiguous.joint_sectors().labels == ("A__s0_",)


def test_the_a_side_of_a_joint_operator_is_a_sector_map_or_an_integer() -> None:
    """``of`` takes ``int`` or a map, and the constructor supplies neither."""
    with pytest.raises(MalformedInputError, match="SectorStructure"):
        JointBlockOperator(
            sector_map=MAP,
            alice_sectors="A",  # type: ignore[arg-type]
            blocks=(identity(1), identity(2)),
        )


# ---------------------------------------------------------------------------
#  The A side of BlockOperator: already served, and held by this test
# ---------------------------------------------------------------------------


def test_a_one_sector_a_family_is_todays_dense_family_entry_for_entry() -> None:
    """``{M_x}`` as a block list over a one-sector ``A`` map IS ``{M_x}``.

    Change 3 of the stage: :class:`BlockOperator` and
    :func:`block_sum_in_declared_order` read ``sector_map.dims`` and nothing
    else, so they serve an ``A``-side map with no change. What has to be
    executed is that the degenerate case is an identity: the single block is the
    dense operator, and the completeness sum in the declared order is the sum
    the dense family already made, verdict for verdict.
    """
    alice = single_alice_sector(2, K)
    family = {
        "x0": matrix([[F(3, 4), F(0)], [F(0), F(1, 4)]]),
        "x1": matrix([[F(1, 4), F(0)], [F(0), F(3, 4)]]),
    }
    blocked = [BlockOperator.of(alice, [element]) for element in family.values()]
    for element, operator in zip(family.values(), blocked, strict=True):
        assert equal(operator.dense(), element)
    (verdict,) = block_sum_in_declared_order(blocked)
    dense_verdict = sum_in_declared_order(list(family.values()))
    assert equal(verdict.total, dense_verdict.total)
    assert equal(verdict.total, identity(2))
    assert verdict.rounds_nowhere is dense_verdict.rounds_nowhere


def test_a_two_sector_a_family_sums_per_sector_in_the_declared_order() -> None:
    """The general case: one verdict per ``A`` sector, in the map's order."""
    alice = SectorStructure(labels=("t0", "t1"), dims=(1, 2), block_kind=K)
    first = BlockOperator.of(
        alice, [matrix([[F(1, 4)]]), matrix([[F(1, 2), F(0)], [F(0), F(1, 4)]])]
    )
    second = BlockOperator.of(
        alice, [matrix([[F(3, 4)]]), matrix([[F(1, 2), F(0)], [F(0), F(3, 4)]])]
    )
    verdicts = block_sum_in_declared_order([first, second])
    assert len(verdicts) == alice.count
    assert equal(verdicts[0].total, identity(1))
    assert equal(verdicts[1].total, identity(2))
    assert equal(
        BlockOperator.of(alice, [first.blocks[0], first.blocks[1]]).dense(),
        matrix(
            [
                [F(1, 4), F(0), F(0)],
                [F(0), F(1, 2), F(0)],
                [F(0), F(0), F(1, 4)],
            ]
        ),
    )
