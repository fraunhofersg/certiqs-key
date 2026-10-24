"""Route C: the setting-dependent weighting, its refusals and what it asserts.

``def:weighted`` has a second construction -- ``N_(v,f) = P(f | t(v)) F_v``
over the support of ``P``, on Bob's side and AFTER the reduction chain -- with
``lem:weighted`` (i), (ii) and (iv), ``thm:choice-encoding`` (v)-(viii) and
``rem:relabel``.

WHAT IS EXERCISED HERE AND WHY EACH ONE IS A CLAIM AND NOT A DETAIL.

* THE FAMILY IS A POVM AND PRESERVES BLOCK DIAGONALITY (``lem:weighted`` (i),
  (ii); ``thm:choice-encoding`` (v)). Every element is a scalar multiple of an element
  the chain delivered, so the encoding cannot break D(iii).
* FORGETTING THE CHOICE RETURNS THE CHAIN'S FAMILY, exactly
  (``lem:weighted`` (iv), Eq. ``eq:forgetf``). This is the identity the second
  form has INSTEAD of ``eq:choicemass``, and it is an operator identity rather
  than a statement about probabilities.
* THE MARGINAL OF THE CHOICE IS A FUNCTION OF THE STATE IN GENERAL
  (Eq. ``eq:fmarginal``), equal to a state-independent ``q_f`` exactly in the
  setting-independent case. THE POINT IS THE NEGATIVE HALF: no identity of the
  form ``eq:choicemass`` holds for this form, and a test that only showed the
  easy case would hide that.
* THE SUPPORT IS WHAT ZERO ENTRIES ARE FOR (Eq. ``eq:support``). A pair with
  weight zero is not an outcome, is not emitted and indexes nothing, so every
  emitted element carries a strictly positive weight.
* THE TWO REFUSALS ARE DATA AND THE FIRST IS A TYPE
  (``thm:choice-encoding`` (viii)). ``choice_weight_not_stochastic`` is returned as a
  :class:`Refusal` from the construction; ``choice_weight_depends_on_outcome``
  has no field to arrive through at all, which is the stronger statement, and
  the function that spells it exists for a caller that presents such a
  weighting out of band.
* THE PRODUCTS ARE DECIDED BEFORE ANYTHING IS EMITTED
  (``def:weighted``, "the two things this module constructs").
  ``emitted_value_not_representable`` covers ``P(f | t(v)) F_v`` exactly as it
  covers ``q_t N_{u|t}``, and the string is unchanged.

EVERY NUMBER BELOW IS A FIXTURE AND NO FROZEN ORACLE VALUE IS READ: there is
none to read, the registry having been frozen against a contract that had no
setting-dependent form. What these tests pin is the claims, exercised on data
small enough to check by eye.
"""

from __future__ import annotations

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
from certiqs_key.foundations.blocks import BlockKind, BlockOperator, SectorStructure
from certiqs_key.foundations.errors import HypothesisError, MalformedInputError
from certiqs_key.foundations.exact import equal, identity, matrix, scale
from certiqs_key.protocol_compiler.chain import identity_channel
from certiqs_key.protocol_compiler.compile import compile_specification
from certiqs_key.protocol_compiler.reasons import Refusal, RefusalReason
from certiqs_key.protocol_compiler.spec import (
    DirectPovm,
    Party,
    ProtocolSpecification,
    PublicPart,
    ReceiverPart,
    Sifting,
    SpecConstraints,
    default_party_partition,
)
from certiqs_key.protocol_compiler.weights import (
    ChoiceWeighting,
    SettingWeightedFamily,
    choice_marginal,
    decide_setting_emission,
    forget_choice,
    is_povm,
    refuse_outcome_dependent_weighting,
    setting_weighted_family,
)

pytestmark = pytest.mark.contract

#: One sector of dimension two: the Band-A map, which is where the compiler's
#: only live instance lives.
QUBIT = SectorStructure(labels=("s0",), dims=(2,), block_kind=BlockKind.PROOF_SECTOR)

P_Z0 = matrix(((1, 0), (0, 0)))
P_Z1 = matrix(((0, 0), (0, 1)))
P_X0 = matrix(((F(1, 2), F(1, 2)), (F(1, 2), F(1, 2))))
P_X1 = matrix(((F(1, 2), F(-1, 2)), (F(-1, 2), F(1, 2))))

#: The chain's family: the joint alphabet of a Z/X basis choice, ALREADY
#: weighted by the supplier, which is what the last link of the receiver
#: segment delivers. ``t`` is its class map -- the basis -- exactly as
#: ``reductions/def:joint-family`` (a) declares one.
V_ORDER = ("(Z,0)", "(Z,1)", "(X,0)", "(X,1)")
FAMILY = {
    "(Z,0)": BlockOperator.of(QUBIT, (scale(F(1, 2), P_Z0),)),
    "(Z,1)": BlockOperator.of(QUBIT, (scale(F(1, 2), P_Z1),)),
    "(X,0)": BlockOperator.of(QUBIT, (scale(F(1, 2), P_X0),)),
    "(X,1)": BlockOperator.of(QUBIT, (scale(F(1, 2), P_X1),)),
}
SETTING_OF = {"(Z,0)": "Z", "(Z,1)": "Z", "(X,0)": "X", "(X,1)": "X"}

#: A SECOND family, whose class sums are NOT multiples of the identity. It is
#: needed for exactly one thing and the need is itself a claim: on the family
#: above -- a basis choice with projective conditional families -- every
#: ``Pi_t`` IS a multiple of the identity, so ``lem:weighted`` (iv)'s marginal
#: is state-independent there and a test written on it would show the
#: dependence nowhere. This one is a which-detector partition: ``Pi_a = P_Z0``,
#: which is not a multiple of ``1``.
WHICH_ORDER = ("v0", "v1")
WHICH_FAMILY = {
    "v0": BlockOperator.of(QUBIT, (P_Z0,)),
    "v1": BlockOperator.of(QUBIT, (P_Z1,)),
}


def _weighting(
    matrix_entries: dict[tuple[str, str], F],
    choices: tuple[str, ...] = ("test", "gen"),
) -> ChoiceWeighting:
    return ChoiceWeighting(
        choice_alphabet=choices,
        setting_alphabet=("Z", "X"),
        setting_of=dict(SETTING_OF),
        matrix=matrix_entries,
    )


#: A genuinely SETTING-DEPENDENT matrix: the Z rounds are mostly generation and
#: the X rounds are all test, which is the round-type choice route C exists
#: for. Every entry is dyadic, so every product is exactly representable.
SETTING_DEPENDENT = _weighting(
    {
        ("Z", "test"): F(1, 4),
        ("Z", "gen"): F(3, 4),
        ("X", "test"): F(1),
        ("X", "gen"): F(0),
    }
)

#: The SETTING-INDEPENDENT case of the same construction, ``P(f | t) = q_f``.
SETTING_INDEPENDENT = _weighting(
    {
        ("Z", "test"): F(1, 4),
        ("Z", "gen"): F(3, 4),
        ("X", "test"): F(1, 4),
        ("X", "gen"): F(3, 4),
    }
)

#: The which-detector weighting: ``test`` on detector a, ``gen`` on b.
WHICH_WEIGHTING = ChoiceWeighting(
    choice_alphabet=("test", "gen"),
    setting_alphabet=("a", "b"),
    setting_of={"v0": "a", "v1": "b"},
    matrix={
        ("a", "test"): F(1),
        ("a", "gen"): F(0),
        ("b", "test"): F(0),
        ("b", "gen"): F(1),
    },
)


def _emitted(weighting: ChoiceWeighting) -> object:
    result = setting_weighted_family(V_ORDER, FAMILY, weighting)
    assert not isinstance(result, Refusal), result
    return result


# ---------------------------------------------------------------------------
#  lem:weighted (i), (ii) and thm:choice-encoding (v): a POVM, blockwise
# ---------------------------------------------------------------------------


def test_the_emitted_family_is_a_povm_over_the_support() -> None:
    """``sum_{(v,f) in V_P} N_(v,f) = 1_S``, exactly and per block."""
    family = _emitted(SETTING_DEPENDENT)
    blocks = tuple(operator.blocks[0] for operator in family.ordered())
    assert is_povm(blocks, 2)
    # And the identity is exact rather than approximate: the omitted terms of
    # each inner sum are exactly the zero entries of a row of P, so the inner
    # sum IS the row sum, which is one.
    total = matrix(((0, 0), (0, 0)))
    for block in blocks:
        total = matrix(
            tuple(
                tuple(total[i][j] + block[i][j] for j in range(2)) for i in range(2)
            )
        )
    assert equal(total, identity(2))


def test_every_element_is_a_scalar_multiple_of_the_one_the_chain_delivered() -> None:
    """``lem:weighted`` (ii): the weighting acts BLOCKWISE and preserves the map."""
    family = _emitted(SETTING_DEPENDENT)
    for label in family.alphabet:
        outcome, choice = family.pairs[label]
        weight = SETTING_DEPENDENT.weight(SETTING_OF[outcome], choice)
        expected = scale(weight, FAMILY[outcome].blocks[0])
        assert equal(family.elements[label].blocks[0], expected), label
        # The sector map is the SAME map, which is what "a block list against
        # the same sector map" means.
        assert family.elements[label].sector_map is QUBIT


# ---------------------------------------------------------------------------
#  eq:support: a zero-weight pair is not an outcome
# ---------------------------------------------------------------------------


def test_a_zero_weight_pair_is_not_emitted_and_indexes_nothing() -> None:
    """``P(gen | X) = 0``, so ``(X,*),gen`` is not in the support."""
    family = _emitted(SETTING_DEPENDENT)
    assert ("(X,0)", "gen") not in family.pairs.values()
    assert ("(X,1)", "gen") not in family.pairs.values()
    # Six emitted elements, not eight: two of the eight pairs are off the
    # support.
    assert len(family.alphabet) == 6
    # AND EVERY EMITTED ELEMENT CARRIES A STRICTLY POSITIVE WEIGHT, which is
    # what q_t > 0 requires of the first form and what the support buys here.
    for label in family.alphabet:
        outcome, choice = family.pairs[label]
        assert SETTING_DEPENDENT.weight(SETTING_OF[outcome], choice) > 0


def test_the_support_is_ordered_by_the_product_order_def_weighted_fixes() -> None:
    """``v`` in the supplier's order, ``f`` in the choice alphabet's, gaps omitted."""
    family = _emitted(SETTING_DEPENDENT)
    assert family.alphabet == (
        "((Z,0),test)",
        "((Z,0),gen)",
        "((Z,1),test)",
        "((Z,1),gen)",
        "((X,0),test)",
        "((X,1),test)",
    )
    # The order is the SUPPLIER'S on V -- def:compile takes it rather than
    # choosing one -- and this test would fail if the family were iterated in
    # dictionary order or sorted.
    assert family.source_alphabet == V_ORDER


# ---------------------------------------------------------------------------
#  lem:weighted (iv): eq:forgetf and eq:fmarginal
# ---------------------------------------------------------------------------


def test_forgetting_the_choice_returns_the_family_the_chain_delivered() -> None:
    """Eq. ``eq:forgetf``, an EXACT operator identity, at every ``v``."""
    family = _emitted(SETTING_DEPENDENT)
    for outcome in V_ORDER:
        assert equal(
            forget_choice(family, outcome).blocks[0], FAMILY[outcome].blocks[0]
        ), outcome


def test_forgetting_a_choice_no_outcome_carries_is_a_hypothesis_error() -> None:
    """``eq:forgetf`` is stated for every ``v``; an absent one has no subject."""
    family = _emitted(SETTING_DEPENDENT)
    with pytest.raises(HypothesisError):
        forget_choice(family, "(Y,0)")


def test_the_choice_marginal_depends_on_the_state_for_the_dependent_form() -> None:
    """Eq. ``eq:fmarginal``: A FUNCTION OF THE STATE, and that is the point.

    On the which-detector family ``Pi_a = P_Z0``, so the setting marginal
    ``m_a(omega) = tr[P_Z0 omega]`` is 1 at ``|0><0|`` and 1/2 at ``|+><+|``,
    and the marginal of ``test`` follows it. NO IDENTITY OF THE FORM
    ``eq:choicemass`` HOLDS, and ``lem:weighted`` (iv) says so in as many
    words.
    """
    result = setting_weighted_family(WHICH_ORDER, WHICH_FAMILY, WHICH_WEIGHTING)
    assert not isinstance(result, Refusal)
    on_zero = choice_marginal(result, "test", P_Z0)
    on_plus = choice_marginal(result, "test", P_X0)
    assert on_zero == F(1)
    assert on_plus == F(1, 2)
    assert on_zero != on_plus
    # And the two choices still partition the mass at every unit-trace state.
    assert on_zero + choice_marginal(result, "gen", P_Z0) == 1
    assert on_plus + choice_marginal(result, "gen", P_X0) == 1


def test_the_marginal_is_state_independent_at_a_multiple_of_the_identity() -> None:
    """``lem:weighted`` (iv)'s middle case, which is why no "iff" is claimed.

    On a basis choice every ``Pi_t`` is ``(1/2) 1``, so the marginal of ``f``
    is ``sum_t P(f | t) lambda_t`` -- state-independent although ``P`` is
    genuinely setting-dependent. It is asserted here rather than left as prose.
    """
    family = _emitted(SETTING_DEPENDENT)
    expected = F(1, 4) * F(1, 2) + F(1) * F(1, 2)
    for state in (P_Z0, P_Z1, P_X0, P_X1):
        assert choice_marginal(family, "test", state) == expected


def test_the_choice_marginal_is_the_declared_weight_in_the_independent_case() -> None:
    """``P(f | t) = q_f`` gives ``q_f`` at every state -- ``eq:choicemass``'s value.

    THE POSITIVE HALF OF ``lem:weighted`` (iv), and the reason the two forms
    overlap: the setting-independent form IS this construction at a constant
    matrix, and there the state drops out.
    """
    family = _emitted(SETTING_INDEPENDENT)
    for state in (P_Z0, P_Z1, P_X0, P_X1):
        assert choice_marginal(family, "test", state) == F(1, 4)
        assert choice_marginal(family, "gen", state) == F(3, 4)


def test_the_choice_marginal_refuses_a_state_on_the_wrong_space() -> None:
    """``eq:fmarginal`` is stated on ``omega`` in ``L(S)`` and on nothing else."""
    family = _emitted(SETTING_DEPENDENT)
    with pytest.raises(HypothesisError):
        choice_marginal(family, "test", identity(3))


# ---------------------------------------------------------------------------
#  thm:choice-encoding (viii): the refusals, fail-closed
# ---------------------------------------------------------------------------


def test_a_negative_entry_is_refused_as_data_and_not_raised() -> None:
    """``choice_weight_not_stochastic``, decided BY SIGN."""
    refusal = setting_weighted_family(
        V_ORDER,
        FAMILY,
        _weighting(
            {
                ("Z", "test"): F(-1, 4),
                ("Z", "gen"): F(5, 4),
                ("X", "test"): F(1, 2),
                ("X", "gen"): F(1, 2),
            }
        ),
    )
    assert isinstance(refusal, Refusal)
    assert refusal.reason is RefusalReason.CHOICE_WEIGHT_NOT_STOCHASTIC
    assert "negative" in refusal.detail
    assert not isinstance(refusal, BaseException)


def test_a_row_that_does_not_sum_to_one_is_refused() -> None:
    """``sum_f P(f | t) = 1`` for EVERY ``t``, decided exactly."""
    refusal = setting_weighted_family(
        V_ORDER,
        FAMILY,
        _weighting(
            {
                ("Z", "test"): F(1, 4),
                ("Z", "gen"): F(1, 4),
                ("X", "test"): F(1, 2),
                ("X", "gen"): F(1, 2),
            }
        ),
    )
    assert isinstance(refusal, Refusal)
    assert refusal.reason is RefusalReason.CHOICE_WEIGHT_NOT_STOCHASTIC
    assert "not\nexactly 1" in refusal.detail or "not " in refusal.detail


def test_the_row_sums_are_decided_for_a_setting_no_outcome_realizes() -> None:
    """``P`` is declared on ``T x F``, and an unreached row is still a row.

    THE DELIBERATE READING, recorded at the deciding function: a row that is
    not a distribution is not a declared datum this module accepts, whether or
    not some ``v`` reaches it. The alternative -- checking only the rows the
    setting map hits -- would let a malformed declaration through and would
    make the refusal depend on the outcome alphabet.
    """
    weighting = ChoiceWeighting(
        choice_alphabet=("test", "gen"),
        setting_alphabet=("Z", "X", "Y"),
        setting_of=dict(SETTING_OF),
        matrix={
            ("Z", "test"): F(1, 2),
            ("Z", "gen"): F(1, 2),
            ("X", "test"): F(1, 2),
            ("X", "gen"): F(1, 2),
            ("Y", "test"): F(1, 2),
            ("Y", "gen"): F(1, 4),
        },
    )
    refusal = setting_weighted_family(V_ORDER, FAMILY, weighting)
    assert isinstance(refusal, Refusal)
    assert refusal.reason is RefusalReason.CHOICE_WEIGHT_NOT_STOCHASTIC
    assert "'Y'" in refusal.detail


def test_a_row_sum_that_rounds_is_refused_by_the_same_reason() -> None:
    """The round-nowhere leg of a row sum refuses, as the first form's weight list does.

    ``fl(0.9) + fl(0.1)`` is exactly one on the computed binary64 total and is
    ``1 + 2^-55`` exactly, so the accumulation ROUNDS. ``def:weighted``
    requires the row sums to round nowhere and this batch's
    ``choice_weight_not_stochastic`` covers it, as
    ``choice_weights_not_normalized`` covers the same leg of the first form's
    weight list (``req:weight-list``).
    """
    nine_tenths = F(0.9)
    one_tenth = F(0.1)
    assert nine_tenths + one_tenth != 1
    refusal = setting_weighted_family(
        V_ORDER,
        FAMILY,
        _weighting(
            {
                ("Z", "test"): nine_tenths,
                ("Z", "gen"): one_tenth,
                ("X", "test"): F(1, 2),
                ("X", "gen"): F(1, 2),
            }
        ),
    )
    assert isinstance(refusal, Refusal)
    assert refusal.reason is RefusalReason.CHOICE_WEIGHT_NOT_STOCHASTIC


def test_an_outcome_dependent_weighting_is_inexpressible_and_has_a_reason() -> None:
    """``choice_weight_depends_on_outcome``: REFUSED BY TYPE, nothing measured.

    The record keys ``P`` by ``(t, f)`` with ``t`` in the SETTING alphabet, so
    a weighting indexed by ``V`` or by a device outcome has no field to arrive
    through. That is the stronger statement and it is asserted structurally;
    the function exists for a caller that presents one out of band, exactly as
    ``refuse_fixed_fraction`` does for the fixed-fraction request.
    """
    fields = set(ChoiceWeighting.__dataclass_fields__)
    assert fields == {
        "choice_alphabet",
        "setting_alphabet",
        "setting_of",
        "matrix",
    }
    refusal = refuse_outcome_dependent_weighting("a caller-level weighting on V")
    assert refusal.reason is RefusalReason.CHOICE_WEIGHT_DEPENDS_ON_OUTCOME
    assert not isinstance(refusal, BaseException)


def test_a_setting_map_that_is_not_total_is_malformed_and_not_refused() -> None:
    """A map that is not a map: no clause of ``def:weighted`` reads against it."""
    partial = ChoiceWeighting(
        choice_alphabet=("test", "gen"),
        setting_alphabet=("Z", "X"),
        setting_of={"(Z,0)": "Z"},
        matrix={
            ("Z", "test"): F(1, 2),
            ("Z", "gen"): F(1, 2),
            ("X", "test"): F(1, 2),
            ("X", "gen"): F(1, 2),
        },
    )
    with pytest.raises(MalformedInputError, match="TOTAL map"):
        setting_weighted_family(V_ORDER, FAMILY, partial)


def test_a_setting_outside_the_declared_alphabet_is_malformed() -> None:
    weighting = ChoiceWeighting(
        choice_alphabet=("test",),
        setting_alphabet=("Z",),
        setting_of=dict(SETTING_OF),
        matrix={("Z", "test"): F(1)},
    )
    with pytest.raises(MalformedInputError, match="declared setting alphabet"):
        setting_weighted_family(V_ORDER, FAMILY, weighting)


def test_an_empty_alphabet_tabulates_no_family_at_all() -> None:
    """``def:weighted`` asks for finite NON-EMPTY alphabets on both sides."""
    with pytest.raises(MalformedInputError, match="NON-EMPTY"):
        ChoiceWeighting(
            choice_alphabet=(),
            setting_alphabet=("Z",),
            setting_of={},
            matrix={},
        )
    with pytest.raises(MalformedInputError, match="NON-EMPTY"):
        ChoiceWeighting(
            choice_alphabet=("test",),
            setting_alphabet=(),
            setting_of={},
            matrix={},
        )


def test_an_untabulated_cell_of_p_is_malformed() -> None:
    """A stochastic matrix on ``T x F`` is tabulated at every cell."""
    weighting = _weighting({("Z", "test"): F(1)})
    with pytest.raises(MalformedInputError, match="not tabulated"):
        setting_weighted_family(V_ORDER, FAMILY, weighting)


# ---------------------------------------------------------------------------
#  def:weighted: the products are decided BEFORE anything is emitted
# ---------------------------------------------------------------------------


def test_the_products_are_binary64_on_a_dyadic_weighting() -> None:
    """The decision passes where it should, and records that it did."""
    decision = decide_setting_emission(_emitted(SETTING_DEPENDENT))
    assert decision.every_product_is_binary64 is True
    assert decision.first_unrepresentable is None
    assert decision.refusal is None
    # The weight-sum leg says nothing for this form: the row sums are decided
    # -- and refused on -- before any product is formed.
    assert decision.weights_sum_rounds_nowhere is True


def test_a_product_that_leaves_the_lattice_refuses_with_the_unchanged_string() -> None:
    """``emitted_value_not_representable``, now of ``P(f | t(v)) F_v`` too.

    BOTH FACTORS ARE BINARY64 AND THE PRODUCT IS NOT, which is the only way
    this refusal can be reached and is exactly what ``def:weighted``'s closing
    paragraph describes: the declared entries lie on lattices of exponent
    ``k`` and ``k_P``, the product lies on one of exponent ``k + k_P``, and
    ``k + k_P > 53`` leaves binary64 altogether. Here both factors are
    ``(2^30 + 1) / 2^31`` -- 31 significand bits each -- so the product needs
    61 and is not a binary64 number. THE STRING'S SUBJECT IS WIDE: it covers
    this product as well as the first form's entries.

    THE CONSTRUCTOR ITSELF REFUSES, AND THAT IS THE POINT. ``def:weighted``
    decides "BEFORE EMITTING ANYTHING", and :func:`setting_weighted_family` is
    the only route from a weighting record to emitted matrices, so a decision
    taken BESIDE it would leave the obligation undischarged on every real
    compilation.
    """
    result = setting_weighted_family(*_off_lattice_fixture())
    assert isinstance(result, Refusal)
    assert result.reason is RefusalReason.EMITTED_VALUE_NOT_REPRESENTABLE
    assert "declares no k" in result.detail
    assert "(v0,test)" in result.detail


def test_the_emission_decision_is_available_beside_the_path_as_well() -> None:
    """The record :func:`decide_setting_emission` returns, on the same data.

    The function stays public because a caller that wants the RECORD -- which
    entry, at which flat index -- rather than the refusal needs it, and because
    the first form's :func:`decide_emission` is public for the same reason.
    Nothing DEPENDS on a caller invoking it.
    """
    alphabet, family, weighting = _off_lattice_fixture()
    unchecked = SettingWeightedFamily(
        alphabet=("(v0,test)", "(v0,gen)"),
        elements={
            "(v0,test)": BlockOperator.of(
                family["v0"].sector_map,
                [
                    scale(weighting.weight("a", "test"), block)
                    for block in family["v0"].blocks
                ],
            ),
            "(v0,gen)": BlockOperator.of(
                family["v0"].sector_map,
                [
                    scale(weighting.weight("a", "gen"), block)
                    for block in family["v0"].blocks
                ],
            ),
        },
        pairs={"(v0,test)": ("v0", "test"), "(v0,gen)": ("v0", "gen")},
        source_alphabet=tuple(alphabet),
        weighting=weighting,
    )
    decision = decide_setting_emission(unchecked)
    assert decision.every_product_is_binary64 is False
    assert decision.first_unrepresentable == ("(v0,test)", 0)
    assert decision.refusal is not None
    assert decision.refusal.reason is RefusalReason.EMITTED_VALUE_NOT_REPRESENTABLE


def _off_lattice_fixture() -> tuple[
    tuple[str, ...], dict[str, BlockOperator], ChoiceWeighting
]:
    """Two binary64 factors of 31 significand bits each: the product needs 61."""
    fine = F(2**30 + 1, 2**31)
    unit_map = SectorStructure(
        labels=("s0",), dims=(1,), block_kind=BlockKind.PROOF_SECTOR
    )
    return (
        ("v0",),
        {"v0": BlockOperator.of(unit_map, (matrix(((fine,),)),))},
        ChoiceWeighting(
            choice_alphabet=("test", "gen"),
            setting_alphabet=("a",),
            setting_of={"v0": "a"},
            matrix={("a", "test"): fine, ("a", "gen"): 1 - fine},
        ),
    )


def test_a_declared_entry_that_is_not_binary64_is_malformed_and_not_refused() -> None:
    """``2/3`` is not a binary64 number at all, so no clause reads against it.

    The ``choice_weighting`` row's domain is "a stochastic matrix P(f | t)
    on T x F of BINARY64 ENTRIES", and the three conditions this module
    DECIDES -- the sign, the row sum, the rounding -- are decided on declared
    numbers. A value off the lattice altogether is the malformed case, exactly
    as a declared weight that is not an exact rational is for the first form.
    """
    with pytest.raises(MalformedInputError, match="not a binary64 number"):
        setting_weighted_family(
            V_ORDER,
            FAMILY,
            _weighting(
                {
                    ("Z", "test"): F(2, 3),
                    ("Z", "gen"): F(1, 3),
                    ("X", "test"): F(1, 2),
                    ("X", "gen"): F(1, 2),
                }
            ),
        )


# ---------------------------------------------------------------------------
#  def:compile and rem:relabel: the weighting reaches the emitted declaration
#
#  Route C is reachable from a compilation, not only a library: `weights.py`
#  implements both forms of `def:weighted`, and a compilation reaches the
#  second because `ReceiverPart` carries the weighting and
#  `compile_specification` fills `bob_povm` from it. `def:spec` (b) makes the
#  weighting a PART of `S_rec` and `rem:relabel`'s fifth statement says
#  version 1 emits BOTH forms.
#
#  THE FIXTURE DECLARES ITS PUBLIC PART OVER THE SUPPORT, which is not an
#  accommodation but what `def:compile` requires: "the emitted alphabet is V_P
#  ... the public part is declared on the emitted alphabets". A specification
#  that declared it over V would fail V1's totality clause on X x V_P, which is
#  the fail-closed direction and is asserted below.
# ---------------------------------------------------------------------------

#: The two-outcome receiver family the route-C specification declares, and the
#: weighting over it. `Pi_a = P_Z0` is not a multiple of the identity, so the
#: emitted declaration is one on which `eq:fmarginal` genuinely depends on the
#: state -- the case route C exists for.
RC_V = ("v0", "v1")
RC_POVM = {"v0": P_Z0, "v1": P_Z1}
RC_WEIGHTING = ChoiceWeighting(
    choice_alphabet=("test", "gen"),
    setting_alphabet=("a", "b"),
    setting_of={"v0": "a", "v1": "b"},
    matrix={
        ("a", "test"): F(1, 4),
        ("a", "gen"): F(3, 4),
        ("b", "test"): F(1, 2),
        ("b", "gen"): F(1, 2),
    },
)
#: V_P in `def:weighted`'s product order: v in the supplier's order, f in the
#: choice alphabet's, the pairs off the support omitted (there are none here).
RC_SUPPORT = ("(v0,test)", "(v0,gen)", "(v1,test)", "(v1,gen)")


def _rc_chain() -> ReductionChain:
    """Return a Band-A chain carrying the two-outcome target family."""
    descriptor = SystemDescriptor(
        "Q", 2, Side.RECEIVER, (("s0", 2),), BlockKind.PROOF_SECTOR
    )
    blocks = {
        label: BlockOperator.of(QUBIT, (element,))
        for label, element in RC_POVM.items()
    }
    return ReductionChain(
        source_segment=(),
        receiver_segment=(
            ChainLink(
                link_id="Lambda_1",
                segment=LinkStage.RECEIVER,
                link_type="squashing (identity)",
                source_descriptor=descriptor,
                target_descriptor=descriptor,
                status=LinkStatus.EXACT,
                channel=identity_channel(2),
                target_alphabet=RC_V,
                target_povm=blocks,
            ),
        ),
        outcome_correspondence=dict(zip(RC_V, RC_V, strict=True)),
    )


def _rc_public(v_alphabet: tuple[str, ...]) -> PublicPart:
    """Return the public part, declared on whichever Bob alphabet is emitted."""
    x_alphabet = ("x0", "x1")
    bob_announcements = tuple(f"b_{label}" for label in v_alphabet)
    classes = [
        (c_a, c_b) for c_a in ("a0", "a1") for c_b in bob_announcements
    ]
    return PublicPart(
        partition=default_party_partition(x_alphabet, v_alphabet),
        announce_alice={"x0": "a0", "x1": "a1"},
        announce_bob=dict(zip(v_alphabet, bob_announcements, strict=True)),
        alice_announcement_alphabet=("a0", "a1"),
        bob_announcement_alphabet=bob_announcements,
        sifting=dict.fromkeys(classes, Sifting.PASS),
        key_rule={
            (readout, kappa): index
            for index, readout in enumerate(x_alphabet)
            for kappa in classes
        },
        holder=Party.ALICE,
        key_alphabet=(0, 1),
        acceptance_alphabet=("g",),
        accept_statistic=dict.fromkeys(classes, "g"),
    )


def _rc_specification(
    weighting: ChoiceWeighting | None,
    public_over: tuple[str, ...] | None = None,
) -> ProtocolSpecification:
    """Return the route-C specification, with or without the weighting."""
    x_alphabet = ("x0", "x1")
    if public_over is None:
        public_over = RC_SUPPORT if weighting is not None else RC_V
    return ProtocolSpecification(
        source=source_part(
            alphabet=x_alphabet,
            alice_dim=2,
            alice_povm=DirectPovm(
                alphabet=x_alphabet, elements={"x0": P_Z0, "x1": P_Z1}
            ),
            transmitted_dim=2,
            signal_weights={"x0": F(1, 2), "x1": F(1, 2)},
            signal_states={"x0": P_Z0, "x1": P_Z1},
        ),
        receiver=ReceiverPart(
            physical_dim=2,
            physical_povm=DirectPovm(alphabet=RC_V, elements=dict(RC_POVM)),
            choice_weighting=weighting,
        ),
        public=_rc_public(public_over),
        sectors=QUBIT,
        chain=_rc_chain(),
        constraints=SpecConstraints(),
    )


def test_a_declared_bob_weighting_reaches_the_emitted_declaration() -> None:
    """``def:spec`` (b) and ``def:compile``: the support IS the emitted alphabet.

    On a specification of this file's own rather than on
    the BB84 instance, which declares no weighting and whose frozen expectations
    must stay byte-identical.
    """
    result = compile_specification(_rc_specification(RC_WEIGHTING))
    assert result.refusal is None
    declaration = result.declaration
    assert declaration is not None

    # THE EMITTED ALPHABET IS V_P IN ITS PRODUCT ORDER, and the emitted family
    # is N_(v,f) = P(f | t(v)) F_v.
    assert declaration.bob_alphabet == RC_SUPPORT
    expected = setting_weighted_family(
        RC_V,
        {
            label: BlockOperator.of(QUBIT, (element,))
            for label, element in RC_POVM.items()
        },
        RC_WEIGHTING,
    )
    assert not isinstance(expected, Refusal)
    for label in RC_SUPPORT:
        assert equal(
            declaration.bob_povm[label].blocks[0],
            expected.elements[label].blocks[0],
        ), label

    # idxm's V COMPONENT FOLLOWS: def:compile indexes the EMITTED alphabet.
    index_map = declaration.label_index_map
    assert index_map is not None
    assert tuple(index_map.forward["V"]) == RC_SUPPORT
    for position, label in enumerate(RC_SUPPORT):
        assert index_map.index_of("V", label) == position, label
        assert index_map.label_of("V", position) == label, label

    # AND THE WEIGHTING IS RECORDED BESIDE THE CHAIN RECORD (rem:relabel).
    record = result.as_machine_record()
    # One entry per weighted factor, naming the factor (spec/pm-eb-roles R1).
    (weighting_record,) = record["choice_weighting_record"]
    assert weighting_record["factor"] == "f0"
    assert "party" not in weighting_record
    assert weighting_record["choice_alphabet"] == ["test", "gen"]
    assert weighting_record["setting_alphabet"] == ["a", "b"]
    assert weighting_record["setting_map"] == {"v0": "a", "v1": "b"}
    assert [entry[0] for entry in weighting_record["support"]] == list(RC_SUPPORT)
    assert weighting_record["matrix"]["a|test"] == "1/4"


def test_no_weighting_declared_emits_the_chains_family_unchanged() -> None:
    """``rem:relabel``, "what version 1 emits": absent is the ordinary case."""
    result = compile_specification(_rc_specification(None))
    assert result.refusal is None
    assert result.declaration is not None
    assert result.declaration.bob_alphabet == RC_V
    assert result.as_machine_record()["choice_weighting_record"] is None


def test_a_public_part_declared_over_v_and_not_over_the_support_is_refused() -> None:
    """``def:compile``: the public part is declared ON THE EMITTED ALPHABETS.

    A specification that weights the family and leaves its announcement tables
    over ``V`` describes a protocol whose public part does not cover its own
    outcomes. It is MALFORMED and not refused: the readout of an untabulated
    cell is not a false clause of ``def:validator`` but a table that cannot be
    read at all, which is exactly what
    :class:`~certiqs_key.foundations.errors.MalformedInputError` is for.
    """
    with pytest.raises(MalformedInputError):
        compile_specification(_rc_specification(RC_WEIGHTING, public_over=RC_V))


def test_the_two_route_c_refusals_are_reachable_through_a_compilation() -> None:
    """``thm:choice-encoding`` (viii): both refusals emit NO declaration, as data.

    THE POINT OF THE TEST IS THE ROUTE, not the refusal: both are exercised at
    the function level above, and a compilation must reach each.
    """
    not_stochastic = ChoiceWeighting(
        choice_alphabet=("test", "gen"),
        setting_alphabet=("a", "b"),
        setting_of={"v0": "a", "v1": "b"},
        matrix={
            ("a", "test"): F(1, 4),
            ("a", "gen"): F(1, 4),
            ("b", "test"): F(1, 2),
            ("b", "gen"): F(1, 2),
        },
    )
    result = compile_specification(_rc_specification(not_stochastic))
    assert result.declaration is None
    assert result.refusal is not None
    assert result.refusal.reason is RefusalReason.CHOICE_WEIGHT_NOT_STOCHASTIC

    # THE OFF-LATTICE CASE NEEDS A CHAIN FAMILY THAT IS A POVM, because (C3)
    # decides completeness before the weighting is applied: a family whose
    # entries merely LOOK awkward is refused by (C3) and the route-C refusal
    # is never reached. A one-dimensional target with F_v0 = [fine] and
    # F_v1 = [1 - fine] is a POVM whose two entries are binary64 and whose
    # products with P's are not, which is the only shape that reaches it.
    fine = F(2**30 + 1, 2**31)
    unrepresentable = ChoiceWeighting(
        choice_alphabet=("test", "gen"),
        setting_alphabet=("a", "b"),
        setting_of={"v0": "a", "v1": "b"},
        matrix={
            ("a", "test"): fine,
            ("a", "gen"): 1 - fine,
            ("b", "test"): F(1, 2),
            ("b", "gen"): F(1, 2),
        },
    )
    result = compile_specification(
        _unit_specification(unrepresentable, RC_SUPPORT)
    )
    assert result.declaration is None
    assert result.refusal is not None
    assert result.refusal.reason is RefusalReason.EMITTED_VALUE_NOT_REPRESENTABLE
    # AND THE REFUSAL IS TAKEN BEFORE THE DECLARATION IS BUILT, which is what
    # "before emitting anything" means: the chain was checked, nothing else.
    assert result.validation is None
    assert result.gates is None


#: The one-dimensional target map of the off-lattice case.
UNIT_MAP = SectorStructure(
    labels=("s0",), dims=(1,), block_kind=BlockKind.PROOF_SECTOR
)


def _unit_chain(entries: tuple[F, F]) -> ReductionChain:
    """Return one exact link ``B -> Q`` on a ONE-dimensional target, carrying a POVM.

    NOT A BAND-A CHAIN: the source descriptor differs from the target, so the
    specification is off the Band-A route, where a one-dimensional receiver
    would be refused first (protocol-compiler/req:band-a-ideal-receiver (ii))
    and route C never reached. The channel is the identity on the one
    dimension, so (C4) is decided and holds.
    """
    descriptor = SystemDescriptor(
        "Q", 1, Side.RECEIVER, (("s0", 1),), BlockKind.PROOF_SECTOR
    )
    physical = SystemDescriptor("B", 1, Side.RECEIVER)
    blocks = {
        label: BlockOperator.of(UNIT_MAP, (matrix(((entry,),)),))
        for label, entry in zip(RC_V, entries, strict=True)
    }
    return ReductionChain(
        source_segment=(),
        receiver_segment=(
            ChainLink(
                link_id="Lambda_1",
                segment=LinkStage.RECEIVER,
                link_type="squashing (identity)",
                source_descriptor=physical,
                target_descriptor=descriptor,
                status=LinkStatus.EXACT,
                channel=identity_channel(1),
                target_alphabet=RC_V,
                target_povm=blocks,
            ),
        ),
        outcome_correspondence=dict(zip(RC_V, RC_V, strict=True)),
    )


def _unit_specification(
    weighting: ChoiceWeighting, public_over: tuple[str, ...]
) -> ProtocolSpecification:
    """Return the off-lattice route-C specification on a unit target."""
    fine = F(2**30 + 1, 2**31)
    x_alphabet = ("x0", "x1")
    return ProtocolSpecification(
        source=source_part(
            alphabet=x_alphabet,
            alice_dim=2,
            alice_povm=DirectPovm(
                alphabet=x_alphabet, elements={"x0": P_Z0, "x1": P_Z1}
            ),
            transmitted_dim=2,
            signal_weights={"x0": F(1, 2), "x1": F(1, 2)},
            signal_states={"x0": P_Z0, "x1": P_Z1},
        ),
        receiver=ReceiverPart(
            physical_dim=1,
            physical_povm=DirectPovm(
                alphabet=RC_V,
                elements={
                    "v0": matrix(((fine,),)),
                    "v1": matrix(((1 - fine,),)),
                },
            ),
            choice_weighting=weighting,
        ),
        public=_rc_public(public_over),
        sectors=UNIT_MAP,
        chain=_unit_chain((fine, 1 - fine)),
        constraints=SpecConstraints(),
    )
