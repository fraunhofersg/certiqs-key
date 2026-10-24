"""The factorised operator family: one family per measured factor, no product.

Motivation: the target POVM of several measuring parties is NEVER formed as a
declared product datum -- what is declared is one exactly admissible family per measured
factor plus the rule ``F_v = (x)_f F^f_{v_f}``, and the product's admissibility is a
theorem (``reductions/thm:emitted-product``). ``domain/`` carries that shape, and the
shape is only worth carrying if the two things it promises are executed.

WHAT IS ASSERTED HERE. That ONE factor is today's family entry for entry --
alphabet, sector map and every block -- which is the design rule of the stage.
That the product order is the declared one for the alphabet exactly as for the
sectors, the last factor fastest, with the one separator. That a two-factor
product of complete families is complete PER PRODUCT SECTOR, checked by forming
the Kronecker blocks HERE, in exact arithmetic, and summing them -- the
arithmetic the type itself refuses to do inside a predicate. And the refusals:
a family list that is not the map's measured factors in count, party or order,
a member against another map, and the ``A`` factor being handed a family.
"""

from __future__ import annotations

from fractions import Fraction as F

import pytest

from certiqs_key.domain.families import FactorFamily, FactorisedFamily
from certiqs_key.foundations.blocks import (
    PRODUCT_LABEL_SEPARATOR,
    BlockKind,
    BlockOperator,
    FactorisedSectorMap,
    SectorFactor,
    SectorStructure,
    SystemTag,
)
from certiqs_key.foundations.errors import MalformedInputError
from certiqs_key.foundations.exact import (
    Matrix,
    add,
    equal,
    identity,
    kron,
    matrix,
    zeros,
)

K = BlockKind.PROOF_SECTOR

#: Alice's station: two sectors, so that a product sector is not trivial.
ALICE_Q = SectorStructure(labels=("qa0", "qa1"), dims=(1, 2), block_kind=K)
#: Bob's station: the shape the minimal fixture declares.
BOB_Q = SectorStructure(labels=("s0", "s1"), dims=(2, 1), block_kind=K)

BBM92_MAP = FactorisedSectorMap(
    factors=(
        SectorFactor(party="alice", sectors=ALICE_Q, system=SystemTag.Q),
        SectorFactor(party="bob", sectors=BOB_Q, system=SystemTag.Q),
    )
)


def _projector_family(sectors: SectorStructure) -> list[BlockOperator]:
    """Return a complete two-letter family on ``sectors``: a diagonal split.

    ``d0`` takes the first basis vector of each sector and ``d1`` the rest, so
    the two are Hermitian, positive semidefinite and sum to the identity block
    by block -- everything the admission of a declared family decides, and all
    of it exact.
    """
    first = [
        matrix(
            [
                [F(1) if i == j == 0 else F(0) for j in range(dim)]
                for i in range(dim)
            ]
        )
        for dim in sectors.dims
    ]
    second = [
        matrix(
            [
                [F(1) if i == j and i > 0 else F(0) for j in range(dim)]
                for i in range(dim)
            ]
        )
        for dim in sectors.dims
    ]
    return [BlockOperator.of(sectors, first), BlockOperator.of(sectors, second)]


def alice_family() -> FactorFamily:
    """Return Alice's station's declared family."""
    return FactorFamily.of("alice", ("a0", "a1"), _projector_family(ALICE_Q))


def bob_family() -> FactorFamily:
    """Return Bob's station's declared family."""
    return FactorFamily.of("bob", ("b0", "b1"), _projector_family(BOB_Q))


def bbm92_family() -> FactorisedFamily:
    """Return the two-station family against :data:`BBM92_MAP`."""
    return FactorisedFamily.of(BBM92_MAP, [alice_family(), bob_family()])


# ---------------------------------------------------------------------------
#  One factor is today's family, entry for entry
# ---------------------------------------------------------------------------


def test_one_factor_is_todays_family_entry_for_entry() -> None:
    """THE DESIGN RULE: nothing about a single declared family changes.

    The product alphabet of one factor is that factor's alphabet, the flattened
    map is that factor's map, and the product block is that factor's block --
    the join of a single letter is that letter and the Kronecker product of one
    operand is that operand.
    """
    plain = bob_family()
    family = FactorisedFamily.single_factor("bob", BOB_Q, plain)
    assert family.count == 1
    assert family.alphabet() == plain.alphabet == ("b0", "b1")
    assert family.flattened() == BOB_Q
    assert family.product_letters() == (("b0",), ("b1",))
    for outcome, letter in enumerate(plain.alphabet):
        for sector in range(BOB_Q.count):
            assert equal(
                family.product_block(outcome, sector),
                plain.member(letter).blocks[sector],
            )
    assert family.is_hermitian()
    assert family.is_positive_semidefinite()
    (verdicts,) = family.completeness_per_factor()
    assert len(verdicts) == BOB_Q.count
    for verdict, dim in zip(verdicts, BOB_Q.dims, strict=True):
        assert equal(verdict.total, identity(dim))


# ---------------------------------------------------------------------------
#  Two factors: the product order, and completeness per product sector
# ---------------------------------------------------------------------------


def test_the_product_alphabet_and_map_run_the_last_factor_fastest() -> None:
    """One convention and one separator for a product letter and a product sector."""
    family = bbm92_family()
    join = PRODUCT_LABEL_SEPARATOR.join
    assert family.alphabet() == (
        join(("a0", "b0")),
        join(("a0", "b1")),
        join(("a1", "b0")),
        join(("a1", "b1")),
    )
    assert family.product_letters() == (
        ("a0", "b0"),
        ("a0", "b1"),
        ("a1", "b0"),
        ("a1", "b1"),
    )
    flattened = family.flattened()
    assert flattened.labels == (
        join(("qa0", "s0")),
        join(("qa0", "s1")),
        join(("qa1", "s0")),
        join(("qa1", "s1")),
    )
    assert flattened.dims == (2, 1, 4, 2)
    assert flattened.block_kind is K
    # The flattening is the MAP's, not a second one computed here.
    assert flattened == BBM92_MAP.flattened_of(SystemTag.Q)


def test_the_product_is_complete_per_product_sector() -> None:
    """``sum_v F_v = 1`` on every product block, formed HERE and not by the type.

    The type decides completeness per factor
    (:meth:`FactorisedFamily.completeness_per_factor`) and leaves the product to
    ``thm:emitted-product`` (i). This test is the other side of that division of
    labour: it forms every Kronecker block itself, in the module's exact
    arithmetic, and checks the theorem's conclusion on the numbers.
    """
    family = bbm92_family()
    flattened = family.flattened()
    for sector, dim in enumerate(flattened.dims):
        total: Matrix = zeros(dim, dim)
        for outcome in range(len(family.alphabet())):
            total = add(total, family.product_block(outcome, sector))
        assert equal(total, identity(dim))
    # ... and the per-factor decision the type DOES make agrees, per factor.
    for verdicts, declared in zip(
        family.completeness_per_factor(), (ALICE_Q, BOB_Q), strict=True
    ):
        for verdict, factor_dim in zip(verdicts, declared.dims, strict=True):
            assert equal(verdict.total, identity(factor_dim))
            assert verdict.rounds_nowhere


def test_completeness_sums_the_members_in_the_declared_order() -> None:
    """The sum is the DECLARED order, which is not a set and is not sorted.

    ``Sigma_1`` of ``eq:declorder`` is the FIRST declared member's block, per
    factor and per sector: the accumulation starts where the alphabet starts.
    """
    family = bbm92_family()
    for verdicts, declared in zip(
        family.completeness_per_factor(), (alice_family(), bob_family()), strict=True
    ):
        first = declared.member(declared.alphabet[0])
        for sector, verdict in enumerate(verdicts):
            assert equal(verdict.partial_sums[0], first.blocks[sector])
            assert len(verdict.partial_sums) == len(declared.alphabet)


def test_no_predicate_forms_the_kronecker_product(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """With the product block unavailable, every decision still decides.

    The claim "no predicate forms a product" is made executable by taking the
    product away: :meth:`FactorisedFamily.product_block` raises, and the
    admission decisions, the alphabet and the flattened map all still work --
    because each of them reads a factor and never the product.
    """

    def refuse(*args: object, **kwargs: object) -> Matrix:
        raise AssertionError("a predicate formed the Kronecker product")

    monkeypatch.setattr(FactorisedFamily, "product_block", refuse)
    family = bbm92_family()
    assert family.is_hermitian()
    assert family.is_positive_semidefinite()
    for verdicts in family.completeness_per_factor():
        assert all(verdict.rounds_nowhere for verdict in verdicts)
    assert len(family.alphabet()) == 4
    assert family.flattened().count == 4
    assert family.product_letters()[0] == ("a0", "b0")
    with pytest.raises(AssertionError, match="formed the Kronecker product"):
        family.product_block(0, 0)


def test_a_product_block_is_the_kronecker_product_of_the_factors_blocks() -> None:
    """The block at ``(v, s)``, in the factors' order, checked term by term."""
    family = bbm92_family()
    alice, bob = alice_family(), bob_family()
    for outcome, (alice_letter, bob_letter) in enumerate(family.product_letters()):
        for sector, (alice_sector, bob_sector) in enumerate(
            (i, j) for i in range(ALICE_Q.count) for j in range(BOB_Q.count)
        ):
            assert equal(
                family.product_block(outcome, sector),
                kron(
                    alice.member(alice_letter).blocks[alice_sector],
                    bob.member(bob_letter).blocks[bob_sector],
                ),
            )


def test_every_exact_decision_is_taken_per_factor() -> None:
    """A member that is not PSD is seen without any product being formed."""
    indefinite = BlockOperator.of(
        BOB_Q,
        [matrix([[F(-1, 4), F(0)], [F(0), F(1)]]), matrix([[F(0)]])],
    )
    broken = FactorFamily.of("bob", ("b0", "b1"), [indefinite, bob_family().members[1]])
    family = FactorisedFamily.of(BBM92_MAP, [alice_family(), broken])
    assert family.is_hermitian()
    assert not family.is_positive_semidefinite()


# ---------------------------------------------------------------------------
#  The refusals
# ---------------------------------------------------------------------------


def test_the_a_factor_is_handed_no_family() -> None:
    """``{F_v}`` is a measurement on the measured systems; ``A`` carries ``{M_x}``."""
    alice_sectors = SectorStructure(labels=("t0", "t1"), dims=(1, 2), block_kind=K)
    decoy = FactorisedSectorMap(
        factors=(
            SectorFactor(party="alice", sectors=alice_sectors, system=SystemTag.A),
            SectorFactor(party="bob", sectors=BOB_Q, system=SystemTag.Q),
        )
    )
    retained = FactorFamily.of(
        "alice", ("m0", "m1"), _projector_family(alice_sectors)
    )
    with pytest.raises(MalformedInputError, match="handed no family"):
        FactorisedFamily.of(decoy, [retained, bob_family()])
    # One family, matched to the ONE measured factor, is the decoy shape and is
    # accepted: the A factor simply takes no family.
    accepted = FactorisedFamily.of(decoy, [bob_family()])
    assert accepted.count == 1
    assert accepted.flattened() == BOB_Q


@pytest.mark.parametrize(
    ("families", "because"),
    [
        ([], "ONE family per measured factor"),
        ([alice_family()], "ONE family per measured factor"),
        ([bob_family(), alice_family()], "IN THE PRODUCT ORDER"),
    ],
)
def test_a_family_list_that_is_not_the_measured_factors_is_refused(
    families: list[FactorFamily], because: str
) -> None:
    """Count, party and order: matched to the map, never reordered to fit."""
    with pytest.raises(MalformedInputError, match=because):
        FactorisedFamily.of(BBM92_MAP, families)


def test_a_member_against_another_map_is_refused_naming_the_ground() -> None:
    """The sector-map comparison decides it, inside the factor it belongs to."""
    wrong = SectorStructure(labels=("s0", "s1"), dims=(2, 2), block_kind=K)
    mismatched = FactorFamily.of("bob", ("b0", "b1"), _projector_family(wrong))
    with pytest.raises(MalformedInputError, match="dimension"):
        FactorisedFamily.of(BBM92_MAP, [alice_family(), mismatched])


def test_a_map_with_no_measured_factor_carries_no_family() -> None:
    """An ``A``-only map declares no measurement."""
    alice_sectors = SectorStructure(labels=("t0",), dims=(2,), block_kind=K)
    retained_only = FactorisedSectorMap(
        factors=(
            SectorFactor(party="alice", sectors=alice_sectors, system=SystemTag.A),
        )
    )
    with pytest.raises(MalformedInputError, match="AT LEAST ONE measured factor"):
        FactorisedFamily.of(retained_only, [])


@pytest.mark.parametrize(
    ("party", "alphabet", "count", "because"),
    [
        ("", ("b0", "b1"), 2, "non-empty party label"),
        ("bob", (), 0, "NON-EMPTY alphabet"),
        ("bob", ("b0", "b0"), 2, "repeats a letter"),
        ("bob", (f"b0{PRODUCT_LABEL_SEPARATOR}x", "b1"), 2, "product separator"),
        ("bob", ("b0", "b1", "b2"), 3, "that many block lists"),
    ],
)
def test_a_factor_family_is_refused_against_its_own_alphabet(
    party: str, alphabet: tuple[str, ...], count: int, because: str
) -> None:
    """The letters are a set in a declared order, and every one has a block list."""
    members = _projector_family(BOB_Q)
    with pytest.raises(MalformedInputError, match=because):
        FactorFamily.of(party, alphabet, members[: min(count, len(members))])


def test_a_letter_outside_the_alphabet_is_refused_rather_than_guessed() -> None:
    """``member`` names the declared alphabet rather than raising a KeyError."""
    with pytest.raises(MalformedInputError, match="not a letter"):
        bob_family().member("b9")


def test_a_product_letter_says_which_factor_supplied_which_part() -> None:
    """On the alphabet: the product letter is joined by the same separator.

    So the same injectivity rule binds it: ``("a", "a_")`` against
    ``("b", "_b")`` would give two different outcomes the same product letter.
    """
    trailing = FactorFamily.of("alice", ("a", "a_"), _projector_family(ALICE_Q))
    leading = FactorFamily.of("bob", ("b", "_b"), _projector_family(BOB_Q))
    with pytest.raises(MalformedInputError, match="product separator"):
        FactorisedFamily.of(BBM92_MAP, [trailing, leading])
    # In the unambiguous positions the same letters are accepted, and one factor
    # is unconstrained: today's alphabets are untouched.
    accepted = FactorisedFamily.of(
        BBM92_MAP,
        [
            FactorFamily.of("alice", ("_a", "a"), _projector_family(ALICE_Q)),
            FactorFamily.of("bob", ("b", "b_"), _projector_family(BOB_Q)),
        ],
    )
    assert accepted.alphabet() == ("_a__b", "_a__b_", "a__b", "a__b_")
    assert FactorisedFamily.single_factor("bob", BOB_Q, leading).alphabet() == (
        "b",
        "_b",
    )
