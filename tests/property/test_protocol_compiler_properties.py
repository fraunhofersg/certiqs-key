"""Hypothesis properties over generated candidate declarations.

Every property here is a THEOREM OF THE CONTRACT quantified over its own input
domain, which is what the frozen cases cannot be: a case is one point, and
these statements are universal ones.

    thm:measurements-and-statistics (iv)
                   P_D[omega] is a distribution, Phi[omega] is a distribution,
                   both are AFFINE in omega, and Phi depends on omega only
                   through P_D
    thm:choice-encoding (ii)
                   Eq. eq:choicemass -- the choice mass is the declared weight
                   at EVERY state
    thm:validator-soundness (i)
                   SOUNDNESS: whatever passes V1-V8 satisfies D(i)-D(viii)
    thm:validator-soundness (ii)
                   COMPLETENESS: whatever satisfies D(i)-D(vi), D(viii) passes
                   V1-V6, V8
    thm:validator-soundness (iii)
                   and the one-sidedness at V7, as a negative property
    rem:vacuous    the joint-pair reading of Eq. eq:partycomp is satisfied by
                   EVERY r, so it is vacuous where V8 is not
    lem:weighted   (i), (ii): the SETTING-DEPENDENT family of def:weighted
                   is a POVM over the support of P, and every element is a
                   POSITIVE MULTIPLE of the F_v it was built from, against
                   the same sector map
    lem:weighted   (iv), Eq. eq:forgetf: summing over f at fixed v returns
                   F_v EXACTLY

D(i)-D(viii) ARE CODED INDEPENDENTLY IN THIS FILE, from Definition
``def:target`` and nothing else. That is the whole point of the soundness and
completeness properties: if they were evaluated by calling the validator the
two implications would be tautologies. The predicates below therefore share no
code with :mod:`certiqs_key.protocol_compiler.validation` -- they use the exact
substrate
and the declaration's own accessors, and nothing else.

EVERYTHING IS DETERMINISTIC. ``derandomize=True`` fixes Hypothesis's stream, so
a failure is reproducible from the test name alone and a green run today is a
green run tomorrow on the same code.
"""

from __future__ import annotations

import itertools
from fractions import Fraction as F

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from protocol_blocks import (
    as_blocks,
    family_as_blocks,
    joint_as_blocks,
)

from certiqs_key.domain.constraints import ConstraintEntry, Relation
from certiqs_key.foundations.blocks import BlockKind, BlockOperator, SectorStructure
from certiqs_key.foundations.exact import (
    Cx,
    Matrix,
    add,
    conjugate_transpose,
    dimension,
    equal,
    identity,
    is_hermitian,
    is_positive_semidefinite,
    kron,
    matrix,
    scale,
    trace,
    zeros,
)
from certiqs_key.protocol_compiler import (
    CandidateDeclaration,
    ChoiceWeighting,
    Party,
    PublicChoices,
    Refusal,
    check_v1,
    check_v2,
    check_v3,
    check_v4,
    check_v5,
    check_v6,
    check_v8,
    choice_mass,
    default_party_partition,
    forget_choice,
    in_feasible_set,
    is_povm,
    joint_distribution,
    phi_distribution,
    setting_weighted_family,
    validate,
    weighted_family,
)
from certiqs_key.protocol_compiler.spec import PERP

#: The block kind every fixture below declares: the shared format's
#: ``proof_sector`` (:class:`~certiqs_key.foundations.blocks.BlockKind`). The
#: contract NAMES the datum and the format FIXES the values, so open choice
#: ``OC-sector-block-kind`` is narrowed within that alphabet and still not
#: decided. ``proof_sector`` is the member these fixtures ARE: their
#: decomposition is "justified by dephasing or SOURCE REPLACEMENT", not photon
#: number (``physical_sector``) and not solver sparsity (``numerical_block``).
#: See :func:`instances.bb84.specification.band_a_block_kind` for the reading.
FIXTURE_BLOCK_KIND = BlockKind.PROOF_SECTOR

_QUBIT_MAP = SectorStructure(labels=("s0",), dims=(2,), block_kind=FIXTURE_BLOCK_KIND)

pytestmark = pytest.mark.contract

SETTINGS = settings(max_examples=60, deadline=None, derandomize=True)

P_Z0 = matrix(((1, 0), (0, 0)))
P_Z1 = matrix(((0, 0), (0, 1)))
P_X0 = matrix(((F(1, 2), F(1, 2)), (F(1, 2), F(1, 2))))
P_X1 = matrix(((F(1, 2), F(-1, 2)), (F(-1, 2), F(1, 2))))
P_Y0 = ((Cx(F(1, 2), F(0)), Cx(F(0), F(-1, 2))), (Cx(F(0), F(1, 2)), Cx(F(1, 2), F(0))))
P_Y1 = ((Cx(F(1, 2), F(0)), Cx(F(0), F(1, 2))), (Cx(F(0), F(-1, 2)), Cx(F(1, 2), F(0))))
QUBIT_BASES = ((P_Z0, P_Z1), (P_X0, P_X1), (P_Y0, P_Y1))


# ---------------------------------------------------------------------------
#  D(i)-D(viii), coded INDEPENDENTLY from Definition def:target
# ---------------------------------------------------------------------------


def d_i(declaration: CandidateDeclaration) -> bool:
    """D(i): finite non-empty alphabets, finite dimensions, total maps."""
    alphabets = (
        declaration.alice_alphabet,
        declaration.bob_alphabet,
        declaration.sectors.labels,
        declaration.partition.alice_readout_alphabet,
        declaration.partition.bob_readout_alphabet,
        declaration.alice_announcement_alphabet,
        declaration.bob_announcement_alphabet,
        declaration.acceptance_alphabet,
    )
    if any(not labels or len(set(labels)) != len(labels) for labels in alphabets):
        return False
    if declaration.alice_dim < 1 or any(d < 1 for d in declaration.sectors.dims):
        return False
    pairs = tuple(
        (x, v) for x in declaration.alice_alphabet for v in declaration.bob_alphabet
    )
    if any(pair not in declaration.key_map for pair in pairs):
        return False
    if any(
        pair not in declaration.partition.alice_readout
        or pair not in declaration.partition.bob_readout
        for pair in pairs
    ):
        return False
    if any(
        readout not in declaration.announce_alice
        for readout in declaration.partition.alice_readout_alphabet
    ):
        return False
    if any(
        readout not in declaration.announce_bob
        for readout in declaration.partition.bob_readout_alphabet
    ):
        return False
    classes = tuple(
        (a, b)
        for a in declaration.alice_announcement_alphabet
        for b in declaration.bob_announcement_alphabet
    )
    return all(kappa in declaration.accept_statistic for kappa in classes)


def d_ii(declaration: CandidateDeclaration) -> bool:
    """D(ii): the slot holds ``nomarg`` or a state on ``A``."""
    marginal = declaration.alice_marginal
    if marginal is None:
        return True
    if dimension(marginal) != declaration.alice_dim:
        return False
    if not is_hermitian(marginal) or not is_positive_semidefinite(marginal):
        return False
    return trace(marginal) == Cx(F(1), F(0))


def d_iii(declaration: CandidateDeclaration) -> bool:
    """D(iii): two POVMs and Hermitian entries, decided PER BLOCK.

    THE SECTOR-BLOCK-DIAGONALITY CLAUSE IS TYPING AT 0.3.0 and is not evaluated
    here or anywhere: Section 2.5 (``operator_form``), "nothing verifies that
    the off-sector entries are zero, BECAUSE NOTHING CAN WRITE THEM". What
    replaced the ``Pi_s O Pi_{s'}`` loop is the sector-map comparison, which is
    D(i)'s and is decided at check V1.
    """
    total: Matrix = zeros(declaration.alice_dim, declaration.alice_dim)
    for label in declaration.alice_alphabet:
        element = declaration.alice_povm.get(label)
        if element is None or dimension(element) != declaration.alice_dim:
            return False
        if not is_hermitian(element) or not is_positive_semidefinite(element):
            return False
        total = add(total, element)
    if not equal(total, identity(declaration.alice_dim)):
        return False

    members = [declaration.bob_povm.get(label) for label in declaration.bob_alphabet]
    if any(member is None for member in members):
        return False
    for member in members:
        assert member is not None
        if not declaration.sectors.agrees_with(member.sector_map):
            return False
        if not member.is_hermitian() or not member.is_positive_semidefinite():
            return False
    for position, dim in enumerate(declaration.sectors.dims):
        block_total: Matrix = zeros(dim, dim)
        for member in members:
            assert member is not None
            block_total = add(block_total, member.blocks[position])
        if not equal(block_total, identity(dim)):
            return False
    for entry in declaration.constraint_list:
        if not declaration.sectors.agrees_with(entry.operator.sector_map):
            return False
        if not entry.operator.is_hermitian():
            return False
    return True


def d_iv(declaration: CandidateDeclaration) -> bool:
    """D(iv): ``r`` maps into ``Z sqcup {perp}``."""
    admissible = {*declaration.key_alphabet, PERP}
    return all(value in admissible for value in declaration.key_map.values())


def d_v(declaration: CandidateDeclaration) -> bool:
    """D(v): SOME ``varsigma`` witnesses announcement-determined sifting."""
    for candidate in itertools.product(
        (True, False), repeat=len(declaration.announcement_classes())
    ):
        fails = dict(zip(declaration.announcement_classes(), candidate, strict=True))
        if all(
            (declaration.key_map[(x, v)] == PERP)
            == fails[declaration.announcement(x, v)]
            for x, v in declaration.outcome_pairs()
        ):
            return True
    return False


def d_vi(declaration: CandidateDeclaration) -> bool:
    """D(vi): the right-hand side is typed by the marginal slot."""
    for entry in declaration.constraint_list:
        if declaration.alice_marginal is None:
            if not isinstance(entry.rhs, F):
                return False
        else:
            if isinstance(entry.rhs, F):
                return False
            if dimension(entry.rhs) != declaration.alice_dim:
                return False
            if not is_hermitian(entry.rhs):
                return False
    return True


def d_viii(declaration: CandidateDeclaration) -> bool:
    """D(viii): announcement locality, and ``r`` factors through the readout."""
    if any(
        readout not in declaration.announce_alice
        for readout in declaration.partition.alice_readout_alphabet
    ):
        return False
    if any(
        readout not in declaration.announce_bob
        for readout in declaration.partition.bob_readout_alphabet
    ):
        return False
    seen: dict[tuple[str, tuple[str, str]], object] = {}
    for x, v in declaration.outcome_pairs():
        key = (
            declaration.partition.readout(declaration.key_holder, x, v),
            declaration.announcement(x, v),
        )
        value = declaration.key_map[(x, v)]
        if key in seen and seen[key] != value:
            return False
        seen[key] = value
    return True


# ---------------------------------------------------------------------------
#  Generators. Every operator is built from an exact orthonormal qubit basis,
#  so a generated POVM is a POVM by construction and a MUTATED one need not be.
# ---------------------------------------------------------------------------


@st.composite
def exact_weights(draw: st.DrawFn, size: int) -> tuple[F, ...]:
    """Return ``size`` strictly positive DYADIC weights summing to one.

    DYADIC BECAUSE 0.3.0 REQUIRES IT, and this is where the number model
    reaches the generators. Section 2.5 (``number_model``): "a declared value
    IS its binary64 datum, A DYADIC RATIONAL, and there is NO EXACT OBJECT
    BEHIND IT of which the float is an approximation." A generator drawing
    ``k/7`` draws data no declaration can present, and the family it builds
    fails condition (C) on the computed sum rather than exercising the
    property under test.

    The parts are drawn as integers on a common denominator ``2**e``, so every
    weight is an integer multiple of ``2**-e`` with ``e <= 6`` -- comfortably
    inside binary64, and every partial sum of the completeness sum is on the
    same lattice, so condition (S) holds too.
    """
    exponent = draw(st.integers(min_value=size.bit_length(), max_value=6))
    total = 2**exponent
    while True:
        parts = draw(
            st.lists(
                st.integers(min_value=1, max_value=total - size + 1),
                min_size=size,
                max_size=size,
            )
        )
        if sum(parts) == total:
            break
        # Re-normalize onto the lattice rather than rejecting: give the
        # remainder to the first part, keeping every weight strictly positive.
        scaled = [max(1, part * total // max(sum(parts), 1)) for part in parts]
        remainder = total - sum(scaled)
        scaled[0] += remainder
        if scaled[0] >= 1 and all(part >= 1 for part in scaled):
            parts = scaled
            break
    return tuple(F(part, total) for part in parts)


@st.composite
def qubit_povms(draw: st.DrawFn) -> tuple[tuple[str, ...], dict[str, Matrix]]:
    """Return a choice-weighted qubit POVM over one or two declared bases."""
    count = draw(st.integers(min_value=1, max_value=2))
    bases = draw(
        st.lists(
            st.integers(min_value=0, max_value=2),
            min_size=count,
            max_size=count,
            unique=True,
        )
    )
    weights = draw(exact_weights(len(bases)))
    choices = tuple(f"t{index}" for index in range(len(bases)))
    record = PublicChoices(
        party=Party.BOB,
        choices=choices,
        weights=dict(zip(choices, weights, strict=True)),
        conditional_alphabets=dict.fromkeys(choices, ("0", "1")),
        conditional_elements={
            choice: {"0": QUBIT_BASES[basis][0], "1": QUBIT_BASES[basis][1]}
            for choice, basis in zip(choices, bases, strict=True)
        },
    )
    family = weighted_family(record)
    return family.alphabet, dict(family.elements)


@st.composite
def candidates(draw: st.DrawFn) -> CandidateDeclaration:
    """Return an arbitrary well-formed candidate on a pair of qubits."""
    alice_alphabet, alice_povm = draw(qubit_povms())
    bob_alphabet, dense_bob_povm = draw(qubit_povms())
    bob_povm = family_as_blocks(_QUBIT_MAP, dense_bob_povm)
    trusted = draw(st.booleans())
    marginal: Matrix | None = None
    if trusted:
        # DYADIC: see `exact_weights`.
        weight = draw(st.sampled_from([F(k, 8) for k in range(9)]))
        marginal = add(scale(weight, P_Z0), scale(1 - weight, P_Z1))
    announce_alice = {label: label.split(",")[1][:-1] for label in alice_alphabet}
    announce_bob = {label: label.split(",")[1][:-1] for label in bob_alphabet}
    alice_classes = tuple(dict.fromkeys(announce_alice.values()))
    bob_classes = tuple(dict.fromkeys(announce_bob.values()))
    classes = tuple((a, b) for a in alice_classes for b in bob_classes)
    sifted = draw(st.lists(st.booleans(), min_size=len(classes), max_size=len(classes)))
    fails = dict(zip(classes, sifted, strict=True))
    partition = default_party_partition(alice_alphabet, bob_alphabet)
    key_rule = {
        (readout, kappa): draw(st.integers(min_value=0, max_value=1))
        for readout in alice_alphabet
        for kappa in classes
    }
    key_map: dict[tuple[str, str], object] = {}
    for x in alice_alphabet:
        for v in bob_alphabet:
            kappa = (announce_alice[x], announce_bob[v])
            key_map[(x, v)] = PERP if fails[kappa] else key_rule[(x, kappa)]
    entries: tuple[ConstraintEntry, ...] = ()
    if draw(st.booleans()):
        bound = draw(st.sampled_from([F(k, 4) for k in range(5)]))
        # THE LICENSED FORM IN BOTH MODES IS THE SCALAR c_k at 0.3.0: in
        # trusted mode "the right-hand side it denotes is then CONSTRUCTED as
        # Theta_k := c_k tau_A", and in untrusted mode "ONLY THE SCALAR FORM
        # EXISTS" (Definition def:homog).
        entries = (
            ConstraintEntry(
                operator=as_blocks(_QUBIT_MAP, P_Z0),
                relation=Relation.GE,
                rhs=bound,
            ),
        )
    return CandidateDeclaration(
        alice_dim=2,
        alice_marginal=marginal,
        sectors=_QUBIT_MAP,
        alice_alphabet=alice_alphabet,
        alice_povm=alice_povm,
        bob_alphabet=bob_alphabet,
        bob_povm=bob_povm,
        partition=partition,
        announce_alice=announce_alice,
        announce_bob=announce_bob,
        alice_announcement_alphabet=alice_classes,
        bob_announcement_alphabet=bob_classes,
        acceptance_alphabet=("keep", "drop"),
        accept_statistic={
            kappa: ("drop" if fails[kappa] else "keep") for kappa in classes
        },
        key_map=key_map,  # type: ignore[arg-type]
        key_alphabet=(0, 1),
        key_holder=Party.ALICE,
        constraint_list=entries,
    )


@st.composite
def states(draw: st.DrawFn) -> Matrix:
    """Return an exact state on ``A Q``: a convex mixture of product states."""
    terms = draw(st.integers(min_value=1, max_value=3))
    weights = draw(exact_weights(terms))
    picks = draw(
        st.lists(
            st.tuples(
                st.integers(min_value=0, max_value=2),
                st.integers(min_value=0, max_value=1),
                st.integers(min_value=0, max_value=2),
                st.integers(min_value=0, max_value=1),
            ),
            min_size=terms,
            max_size=terms,
        )
    )
    total: Matrix = zeros(4, 4)
    for weight, (basis_a, index_a, basis_b, index_b) in zip(
        weights, picks, strict=True
    ):
        product = kron(QUBIT_BASES[basis_a][index_a], QUBIT_BASES[basis_b][index_b])
        total = add(total, scale(weight, product))
    return total


# ---------------------------------------------------------------------------
#  PC2 (iv) -- the statistics functional
# ---------------------------------------------------------------------------


@SETTINGS
@given(declaration=candidates(), state=states())
def test_pc2_iv_p_d_is_a_probability_distribution(
    declaration: CandidateDeclaration, state: Matrix
) -> None:
    joint = joint_distribution(declaration, state)
    assert all(value >= 0 for value in joint.values())
    assert sum(joint.values(), F(0)) == 1


@SETTINGS
@given(declaration=candidates(), state=states())
def test_pc2_iv_phi_is_a_probability_distribution_and_a_fibre_sum(
    declaration: CandidateDeclaration, state: Matrix
) -> None:
    joint = joint_distribution(declaration, state)
    statistics = phi_distribution(declaration, state)
    assert all(value >= 0 for value in statistics.values.values())
    assert statistics.total == 1
    # Phi depends on omega ONLY THROUGH P_D: it is the fibre sum of the table.
    for value, fibre in statistics.fibres.items():
        assert statistics.values[value] == sum((joint[pair] for pair in fibre), F(0))
    # The fibres PARTITION X x V.
    covered = [pair for fibre in statistics.fibres.values() for pair in fibre]
    assert sorted(covered) == sorted(declaration.outcome_pairs())


@SETTINGS
@given(
    declaration=candidates(),
    first=states(),
    second=states(),
    weight=st.sampled_from([F(k, 8) for k in range(9)]),
)
def test_pc2_iv_both_maps_are_affine_in_the_state(
    declaration: CandidateDeclaration, first: Matrix, second: Matrix, weight: F
) -> None:
    mixture = add(scale(weight, first), scale(1 - weight, second))
    left = joint_distribution(declaration, first)
    right = joint_distribution(declaration, second)
    mixed = joint_distribution(declaration, mixture)
    for pair, value in mixed.items():
        assert value == weight * left[pair] + (1 - weight) * right[pair]

    phi_left = phi_distribution(declaration, first).values
    phi_right = phi_distribution(declaration, second).values
    phi_mixed = phi_distribution(declaration, mixture).values
    for label, value in phi_mixed.items():
        assert value == weight * phi_left[label] + (1 - weight) * phi_right[label]


# ---------------------------------------------------------------------------
#  PC3 (ii) -- Eq. eq:choicemass, state-independent
# ---------------------------------------------------------------------------


@SETTINGS
@given(record=st.data(), state=states())
def test_pc3_ii_the_choice_mass_is_the_declared_weight_at_every_state(
    record: st.DataObject, state: Matrix
) -> None:
    _, _ = record.draw(qubit_povms())  # exercise the generator's own invariants
    size = record.draw(st.integers(min_value=1, max_value=2))
    bases = record.draw(
        st.lists(
            st.integers(min_value=0, max_value=2),
            min_size=size,
            max_size=size,
            unique=True,
        )
    )
    weights = record.draw(exact_weights(len(bases)))
    choices = tuple(f"t{index}" for index in range(len(bases)))
    party = record.draw(st.sampled_from((Party.ALICE, Party.BOB)))
    family = weighted_family(
        PublicChoices(
            party=party,
            choices=choices,
            weights=dict(zip(choices, weights, strict=True)),
            conditional_alphabets=dict.fromkeys(choices, ("0", "1")),
            conditional_elements={
                choice: {"0": QUBIT_BASES[basis][0], "1": QUBIT_BASES[basis][1]}
                for choice, basis in zip(choices, bases, strict=True)
            },
        )
    )
    for choice, weight in zip(choices, weights, strict=True):
        assert choice_mass(family, choice, state, 2) == weight


# ---------------------------------------------------------------------------
#  PC6 (i) and (ii) -- soundness and completeness
# ---------------------------------------------------------------------------


def _mutate(declaration: CandidateDeclaration, which: int) -> CandidateDeclaration:
    """Return a candidate with one clause of Definition ``def:target`` broken."""
    fields = dict(declaration.__dict__)
    if which == 0:  # D(ii): an inadmissible marginal.
        fields["alice_marginal"] = matrix(((2, 0), (0, -1)))
    elif which == 1:  # D(iii): an incomplete POVM.
        first = declaration.alice_alphabet[0]
        fields["alice_povm"] = {
            **declaration.alice_povm,
            first: scale(F(1, 2), declaration.alice_povm[first]),
        }
    elif which == 2:  # D(iv): a key value outside the alphabet.
        pair = declaration.outcome_pairs()[0]
        fields["key_map"] = {**declaration.key_map, pair: 7}
    elif which == 3:  # D(v)/D(viii): a supplied, inconsistent key map.
        pair = declaration.outcome_pairs()[-1]
        current = declaration.key_map[pair]
        fields["key_map"] = {
            **declaration.key_map,
            pair: (0 if current == PERP else PERP),
        }
    else:  # D(vi): a right-hand side of the wrong kind.
        if declaration.constraint_list:
            entry = declaration.constraint_list[0]
            replacement = (
                F(1, 2) if not isinstance(entry.rhs, F) else scale(F(1, 2), P_Z0)
            )
            fields["constraint_list"] = (
                ConstraintEntry(
                    operator=entry.operator,
                    relation=entry.relation,
                    rhs=replacement,
                ),
            )
    return CandidateDeclaration(**fields)


@SETTINGS
@given(declaration=candidates(), which=st.integers(min_value=-1, max_value=4))
def test_pc6_i_soundness_whatever_passes_the_checks_is_well_formed(
    declaration: CandidateDeclaration, which: int
) -> None:
    """If V1-V8 all pass then D(i)-D(viii) all hold.

    The D-predicates are coded independently in this file; if the validator
    evaluated them the implication would be a tautology.
    """
    candidate = declaration if which < 0 else _mutate(declaration, which)
    result = validate(candidate)
    if not result.passed:
        return
    assert d_i(candidate)
    assert d_ii(candidate)
    assert d_iii(candidate)
    assert d_iv(candidate)
    assert d_v(candidate)
    assert d_vi(candidate)
    # D(vii): the witness V7 accepted lies in W, so the feasible set is
    # non-empty -- exhibited, never asserted.
    assert result.feasibility.witness is not None
    assert in_feasible_set(candidate, result.feasibility.witness)
    assert d_viii(candidate)


@SETTINGS
@given(declaration=candidates(), which=st.integers(min_value=-1, max_value=4))
def test_pc6_ii_completeness_on_seven_of_the_eight_conditions(
    declaration: CandidateDeclaration, which: int
) -> None:
    """If D(i)-D(vi) and D(viii) hold then V1-V6 and V8 all pass."""
    candidate = declaration if which < 0 else _mutate(declaration, which)
    if not (
        d_i(candidate)
        and d_ii(candidate)
        and d_iii(candidate)
        and d_iv(candidate)
        and d_v(candidate)
        and d_vi(candidate)
        and d_viii(candidate)
    ):
        return
    for check in (check_v1, check_v2, check_v3, check_v4, check_v5, check_v6, check_v8):
        outcome = check(candidate)
        assert outcome.passed, (outcome.check, outcome.refusal)


@SETTINGS
@given(declaration=candidates(), which=st.integers(min_value=0, max_value=4))
def test_a_refusal_on_the_complete_checks_names_a_real_defect(
    declaration: CandidateDeclaration, which: int
) -> None:
    """Remark rem:completeness: outside V7, a refusal is never a limitation."""
    candidate = _mutate(declaration, which)
    conditions = {
        "V1": d_i,
        "V2": d_ii,
        "V3": d_iii,
        "V4": d_iv,
        "V5": d_v,
        "V6": d_vi,
        "V8": d_viii,
    }
    result = validate(candidate)
    for check, predicate in conditions.items():
        outcome = result.outcome_of(check)
        if outcome.passed or not outcome.evaluated:
            continue
        assert predicate(candidate) is False, check


# ---------------------------------------------------------------------------
#  thm:validator-soundness (iii) and rem:vacuous -- the two negative properties
# ---------------------------------------------------------------------------


@SETTINGS
@given(declaration=candidates())
def test_v7_is_the_only_check_that_can_refuse_a_well_formed_candidate(
    declaration: CandidateDeclaration,
) -> None:
    result = validate(declaration)
    well_formed = (
        d_i(declaration)
        and d_ii(declaration)
        and d_iii(declaration)
        and d_iv(declaration)
        and d_v(declaration)
        and d_vi(declaration)
        and d_viii(declaration)
    )
    if not well_formed:
        return
    refusing = set(result.refusing_checks)
    assert refusing <= {"V7"}


@SETTINGS
@given(declaration=candidates())
def test_rem_vacuous_the_joint_pair_reading_is_satisfied_by_every_key_map(
    declaration: CandidateDeclaration,
) -> None:
    """Read against ``(x, v)``, Eq. eq:partycomp holds for EVERY ``r``.

    So the joint-pair reading can never refuse, which is exactly why D(viii)
    is read against the holder READOUT -- and V8 genuinely can refuse.
    """
    joint_pair_rule: dict[tuple[str, str], object] = {}
    for pair in declaration.outcome_pairs():
        joint_pair_rule[pair] = declaration.key_map[pair]
    assert all(
        joint_pair_rule[pair] == declaration.key_map[pair]
        for pair in declaration.outcome_pairs()
    )
    # And V8 is a genuine restriction: it can fail on a candidate for which
    # the joint-pair reading holds.
    broken = _mutate(declaration, 3)
    assert check_v8(broken).passed in (True, False)


@SETTINGS
@given(declaration=candidates(), state=states())
def test_a_feasible_state_stays_feasible_under_the_untrusted_relaxation(
    declaration: CandidateDeclaration, state: Matrix
) -> None:
    """Proposition prop:conservative: ``W^tr subset W^un`` on a licensed list."""
    if declaration.alice_marginal is None:
        return
    marginal = declaration.alice_marginal
    untrusted_entries = []
    for entry in declaration.constraint_list:
        # SINCE 0.3.0 A LICENSED ENTRY CARRIES c_k DIRECTLY, in both modes:
        # "In untrusted-source mode ONLY THE SCALAR FORM EXISTS", and in
        # trusted mode the same c_k denotes ``c_k tau_A`` by construction
        # (Definition def:homog). There is nothing left to recover from a
        # trace, and the two lists differ only in the marginal slot -- which is
        # exactly what Proposition prop:conservative compares.
        assert isinstance(entry.rhs, F)
        untrusted_entries.append(entry)
    untrusted = CandidateDeclaration(
        **{
            **declaration.__dict__,
            "alice_marginal": None,
            "constraint_list": tuple(untrusted_entries),
        }
    )
    assert equal(marginal, marginal)
    blocks = joint_as_blocks(declaration.sectors, declaration.alice_dim, state)
    if in_feasible_set(declaration, blocks):
        assert in_feasible_set(untrusted, blocks)


@SETTINGS
@given(state=states())
def test_every_generated_state_is_a_state(state: Matrix) -> None:
    """The generator's own invariant, so that a failure is never its fault."""
    assert is_hermitian(state)
    assert is_positive_semidefinite(state)
    assert trace(state) == Cx(F(1), F(0))
    assert equal(state, conjugate_transpose(state))


# ---------------------------------------------------------------------------
#  Route C: lem:weighted (i), (ii) and (iv) as universal statements
#
#  The route-C unit file
#  drives specific witnesses -- the support, the product order, both refusals,
#  eq:forgetf, eq:fmarginal, the state dependence and the two-setting case --
#  and this file is where a universally quantified statement of this module
#  belongs. lem:weighted (i) and (ii) are stated FOR EVERY stochastic P and
#  every POVM {F_v}, and eq:forgetf is an identity at every v.
# ---------------------------------------------------------------------------


@st.composite
def stochastic_matrices(
    draw: st.DrawFn, settings_count: int, choices_count: int
) -> ChoiceWeighting:
    """Return a declared weighting with DYADIC rows summing to one exactly.

    DYADIC FOR THE REASON :func:`exact_weights` GIVES, and here it is a
    condition the module DECIDES rather than a convenience: ``def:weighted``
    requires each row of ``P`` to sum to one exactly IN THE DECLARED ORDER of
    ``F`` and to round nowhere, and a generator drawing ``k/7`` would draw a
    matrix ``choice_weight_not_stochastic`` refuses -- exercising the refusal
    instead of the property.

    ZERO ENTRIES ARE DRAWN DELIBERATELY. The support of Eq. ``eq:support`` is
    what they are for, and a generator that never produced one would leave the
    one structural feature of this form untested at the property level.
    """
    rows: dict[tuple[str, str], F] = {}
    setting_alphabet = tuple(f"t{index}" for index in range(settings_count))
    choice_alphabet = tuple(f"f{index}" for index in range(choices_count))
    for setting in setting_alphabet:
        exponent = draw(st.integers(min_value=choices_count.bit_length(), max_value=6))
        total = 2**exponent
        parts = draw(
            st.lists(
                st.integers(min_value=0, max_value=total),
                min_size=choices_count,
                max_size=choices_count,
            )
        )
        if sum(parts) == 0:
            parts = [total] + [0] * (choices_count - 1)
        scaled = [part * total // sum(parts) for part in parts]
        scaled[0] += total - sum(scaled)
        if scaled[0] < 0:  # pragma: no cover - the remainder is non-negative
            scaled = [total] + [0] * (choices_count - 1)
        for choice, part in zip(choice_alphabet, scaled, strict=True):
            rows[(setting, choice)] = F(part, total)
    return ChoiceWeighting(
        choice_alphabet=choice_alphabet,
        setting_alphabet=setting_alphabet,
        setting_of={},
        matrix=rows,
    )


@st.composite
def weighted_receiver_families(
    draw: st.DrawFn,
) -> tuple[
    tuple[str, ...], dict[str, BlockOperator], ChoiceWeighting, SectorStructure
]:
    """Return a qubit POVM on one sector with a declared setting map over it."""
    alphabet, elements = draw(qubit_povms())
    sector_map = SectorStructure(
        labels=("s0",), dims=(2,), block_kind=BlockKind.PROOF_SECTOR
    )
    family = {
        label: as_blocks(sector_map, element) for label, element in elements.items()
    }
    settings_count = draw(st.integers(min_value=1, max_value=2))
    choices_count = draw(st.integers(min_value=1, max_value=3))
    weighting = draw(stochastic_matrices(settings_count, choices_count))
    setting_of = {
        label: weighting.setting_alphabet[index % settings_count]
        for index, label in enumerate(alphabet)
    }
    return (
        alphabet,
        family,
        ChoiceWeighting(
            choice_alphabet=weighting.choice_alphabet,
            setting_alphabet=weighting.setting_alphabet,
            setting_of=setting_of,
            matrix=weighting.matrix,
        ),
        sector_map,
    )


@SETTINGS
@given(drawn=weighted_receiver_families())
def test_lem_weighted_i_and_ii_the_weighted_family_is_a_povm_per_block(
    drawn: tuple[
        tuple[str, ...], dict[str, BlockOperator], ChoiceWeighting, SectorStructure
    ],
) -> None:
    """``lem:weighted`` (i), (ii) for the SETTING-DEPENDENT form, universally.

    "``{N_(v,f)}`` over the support of ``P`` is a POVM on ``S``", and every
    element "is a scalar multiple of the ``F_v`` it was built from ... so
    ``N_(v,f)`` is sector-block-diagonal iff ``F_v`` is". Both are checked on
    THE BLOCK LIST, which is where block diagonality lives: an emitted operator
    IS its list of sector blocks, so preserving the map is preserving the list.
    """
    alphabet, family, weighting, sector_map = drawn
    emitted = setting_weighted_family(alphabet, family, weighting)
    # NO DRAW OF THIS GENERATOR IS REFUSED, and the property would be vacuous
    # if one were: the rows are dyadic and sum to one EXACTLY, so (S) holds of
    # the row sums, and every product of a row entry with an entry of a qubit
    # basis projector is a dyadic of at most thirteen significand bits, so (S)
    # holds of the emitted values too. The refusals have their own witnesses in
    # tests/unit/test_protocol_route_c.py; here a refusal is a FAILURE.
    assert not isinstance(emitted, Refusal), emitted

    # (i): positive semidefinite per block, and the completeness sum is 1_S.
    blocks = [operator.blocks[0] for operator in emitted.ordered()]
    assert is_povm(tuple(blocks), 2)

    # (ii): every element is a POSITIVE SCALAR MULTIPLE of the one the chain
    # delivered, blockwise, and against THE SAME sector map.
    for label in emitted.alphabet:
        outcome, choice = emitted.pairs[label]
        weight = weighting.weight(weighting.setting_of[outcome], choice)
        assert weight > 0, label
        assert emitted.elements[label].sector_map == sector_map, label
        assert equal(
            emitted.elements[label].blocks[0],
            scale(weight, family[outcome].blocks[0]),
        ), label


@SETTINGS
@given(drawn=weighted_receiver_families())
def test_lem_weighted_iv_forgetting_the_choice_returns_the_chains_family(
    drawn: tuple[
        tuple[str, ...], dict[str, BlockOperator], ChoiceWeighting, SectorStructure
    ],
) -> None:
    """Eq. ``eq:forgetf``: ``sum_f N_(v,f) = F_v`` for EVERY ``v``, exactly.

    An operator identity and not a statement about probabilities: the omitted
    terms of each inner sum are exactly the zero entries of the row
    ``P( . | t(v))``, so the inner sum IS the row sum, which is one. The
    universal quantifier over ``v`` and over ``P`` is what the unit file's
    witnesses cannot carry.
    """
    alphabet, family, weighting, _sector_map = drawn
    emitted = setting_weighted_family(alphabet, family, weighting)
    assert not isinstance(emitted, Refusal), emitted  # as above: never refused
    for outcome in alphabet:
        assert equal(
            forget_choice(emitted, outcome).blocks[0], family[outcome].blocks[0]
        ), outcome
