"""``protocol-compiler`` against its FROZEN registry -- the candidate-side pass.

``tests/oracles/registry_protocol_compiler.py`` is the authority here and this
implementation is what is on trial. Every value in it was derived BY HAND from
the accepted ``contract.tex`` 0.1.3 and committed by a DIFFERENT implementer
instance before ``src/certiqs_key/protocol_compiler/`` existed at all (the
freeze rule). A disagreement is a finding against
this code, never against the registry, and no expected value may be edited to
make a test green.

WHAT THIS FILE REPLAYS, AND WHAT IT DEFERS
==========================================
This pass implements the CANDIDATE-SIDE predicates only -- the contract's own
seam, at which Definition ``def:validator`` is stated "given a candidate
declaration", Theorem ``thm:feasibility`` says "nothing below uses that ``D`` was
emitted", and Theorem ``thm:validator-soundness`` applies to candidates. Nothing under
``src/src/certiqs_key/protocol_compiler/`` depends on a compilation map existing, so
every
frozen entry whose subject is an EMISSION is deferred to the emission pass.

REPLAYED HERE:

    PC-A   INDEX_MAP_CASES -- the nine label-to-index bijections and their
           inverses, built by ``build_label_index_map``
    PC-B   WEIGHTED_FAMILY_CASES, JOINT_DISTRIBUTION_CASES, the partial-phi
           deficit of O-PC-PARTIAL-PHI, and the verbatim
           ``fixed_fraction_requested`` string
    PC-C   KEY_MAP_CASES -- Eq. eq:rdef, BOTH r_h extensions, the realized
           set, and the V5/V8 verdicts including the rem:vacuous split
    PC-D   WITNESS_CASES and WITNESS_LEG_FAILURES -- the default witness in
           both modes, the supplied witness that rescues, the thm:validator-soundness
           (iii) counterexample, and one failure per verification leg; plus
           O-PC-WELLPOSED's two exact witnesses
    PC-E   VALIDATOR_CASES (all nine), RECONSTRUCTION_CASES (all three) and
           DECIDABILITY_COUNTS (both)
    PC-F   CHAIN_CASES (all nine) condition by condition, with the A-LINK
           naming and Eq. eq:pullbackstats at two named states
    PC-G   FEASIBLE_SET_COMPARISONS and DIMENSION_ONE_EQUALITIES -- pure
           membership predicates of Definition def:feasible, so they are on
           the candidate side even though O-PC-CONSERVATIVE sits in the gate
           group
    PC-H   CERTIFICATE_CASES, CONSISTENCY_CRITERION_CASES, SR3_RECORD, and
           the outcome distribution O-PC-SR-BOUNDARY is stated on
    PC-I   the BB84 instance's (SR1)/(SR2) values, key map, D-verdicts,
           statistics and Phi -- read off the FROZEN emitted matrices
    PC-J   both conjugation branches' (SR2) verdicts and matched-basis
           distributions -- likewise from the frozen emitted element
    PC-K   the machine-key vocabulary as frozen tuples
    PC-L   the assumption identifiers, their machine keys and the
           never-verified set

DEFERRED TO THE EMISSION PASS, with the reason for each:

    O-PC-TYPING's slot-by-slot emitted declaration -- it is Definition
        ``def:compile`` filling Eq. ``eq:declaration``, which is an EMISSION.
        The machine-readable part of PC-A is INDEX_MAP_CASES and is replayed.
    O-PC-GATES in full -- GATE_AXES, GATE_CONSISTENCY_RULES and GATE_CASES are
        Definition ``def:eligible`` and Table ``tab:gateoutcome``, which decide
        what is emitted and under which flag. No gate is evaluated in this
        pass.
    O-PC-BB84's emitted matrices, tau_A and gate verdicts -- Eq. eq:bb84data
        is what Definition ``def:compile`` produces from Definition
        ``def:bb84spec``, and BB84_GATE_VERDICTS is a gate report. The frozen
        matrices are used here as INPUT DATA to the candidate-side predicates,
        never re-derived.
    O-PC-CONJUGATION's emitted element -- likewise: applying the conjugation
        of ``conjugation_basis`` to a declared signal set is an emission step.
        Both branches' CONSEQUENCES are replayed from the frozen element.
    The docking cross-check against the consuming engine's own validator --
        it needs a declaration to hand across, so it belongs where one is
        emitted.

TWO TRANSLATIONS THIS FILE PERFORMS, AND NEITHER IS A DERIVATION
================================================================
The registry freezes announcement classes as strings like ``"(alpha0,beta0)"``
and chain descriptors as prose labels like ``"(Q, (s0), (2))"``. The
implementation types the first as the pair ``("alpha0", "beta0")`` of
Eq. ``eq:jointann`` and the second as a
:class:`~certiqs_key.protocol_compiler.chain.SystemDescriptor`. :func:`_class` and
:data:`DESCRIPTORS` are those two translations, and they touch LABELS ONLY --
no expected value passes through either.
"""

from __future__ import annotations

from fractions import Fraction as F

import pytest
from protocol_blocks import (
    NotBlockDiagonalError,
    as_blocks,
    family_as_blocks,
    joint_as_blocks,
    split,
)
from registry_instances_bb84 import (
    BB84_ALPHABETS,
    BB84_CASES,
    BB84_D_VERDICTS,
    BB84_KEY_MAP,
    BB84_PHI,
    CONJUGATION_BRANCHES,
    BB84Case,
    ConjugationBranch,
)
from registry_protocol_compiler import (
    CHAIN_CASES,
    COMPILER_ONLY_KEYS,
    DECIDABILITY_COUNTS,
    DECLARATION_SLOT_KEYS,
    DIMENSION_ONE_EQUALITIES,
    FEASIBLE_SET_COMPARISONS,
    GATE_VERDICT_VOCABULARY,
    INDEX_MAP_CASES,
    INDEXED_ALPHABETS,
    INPUT_KEYS,
    JOINT_DISTRIBUTION_CASES,
    KEY_MAP_CASES,
    LEDGER_ROWS,
    LINK_STATUS_VOCABULARY,
    NEVER_VERIFIED,
    NOT_OUTPUTS,
    OUTPUT_KEYS,
    PERP,
    RECONSTRUCTION_CASES,
    REFUSAL_REASONS_VERBATIM,
    VALIDATOR_CASES,
    WEIGHTED_FAMILY_CASES,
    WITNESS_CASES,
    WITNESS_LEG_FAILURES,
    ChainCase,
    DecidabilityCount,
    DimensionOneEquality,
    FeasibleSetComparison,
    IndexMapCase,
    JointDistributionCase,
    KeyMapCase,
    LedgerRow,
    ReconstructionCase,
    ValidatorCase,
    WeightedFamilyCase,
    WitnessCase,
)
from registry_transmitter import (
    CERTIFICATE_CASES,
    CONSISTENCY_CRITERION_CASES,
    SR3_RECORD,
    CertificateCase,
    ConsistencyCriterionCase,
)

from certiqs_key.domain.constraints import ConstraintEntry, Relation
from certiqs_key.foundations.blocks import BlockKind, SectorStructure
from certiqs_key.foundations.exact import (
    ONE,
    Cx,
    Matrix,
    equal,
    identity,
    kron,
    matmul,
    matrix,
    outer_projector,
    scale,
    trace,
    vector,
)
from certiqs_key.protocol_compiler import (
    ASSUMPTION_MACHINE_KEYS,
    AssumptionId,
    CandidateDeclaration,
    ChainContext,
    ChainLink,
    ConditionOutcome,
    GateVerdict,
    LinkStage,
    LinkStatus,
    Party,
    PublicChoices,
    PublicPart,
    ReductionChain,
    RefusalReason,
    Side,
    Sifting,
    SystemDescriptor,
    build_label_index_map,
    check_chain,
    choice_mass,
    decidability_counts,
    default_party_partition,
    default_witness,
    derived_holder_key_rule,
    identity_channel,
    in_feasible_set,
    joint_distribution,
    phi_distribution,
    raw_key_map,
    realized_readout_classes,
    reconstruct_holder_key_rule,
    reconstruct_sifting_predicate,
    validate,
    verify_witness,
)
from certiqs_key.protocol_compiler.statistics import announcement_class_mass
from certiqs_key.transmitter import (
    SourceReplacementCertificate,
    SourceReplacementLicense,
    check_sr1,
    check_sr2,
    consistency_criterion,
)

pytestmark = [pytest.mark.contract, pytest.mark.oracle]


# ---------------------------------------------------------------------------
#  Translations and shared fixtures. Labels only; no expected value here.
# ---------------------------------------------------------------------------


def reg(frozen: object) -> Matrix:
    """Return a frozen registry matrix in the implementation's substrate.

    Both are exact Gaussian rationals -- the registry as ``(re, im)`` pairs and
    the implementation as :class:`~certiqs_key.foundations.exact.Cx`. NO TOLERANCE IS
    INTRODUCED AND NONE IS NEEDED: this is a change of representation, and
    every comparison in this file is an exact equality of rationals.
    """
    assert isinstance(frozen, tuple)
    return tuple(
        tuple(Cx(entry[0], entry[1]) for entry in row)  # type: ignore[index]
        for row in frozen
    )


def _class(label: str) -> tuple[str, str]:
    """Return the announcement class a frozen ``"(c_A,c_B)"`` label denotes."""
    left, right = label[1:-1].split(",")
    return (left, right)


P_Z0 = matrix(((1, 0), (0, 0)))
P_Z1 = matrix(((0, 0), (0, 1)))
P_X0 = matrix(((F(1, 2), F(1, 2)), (F(1, 2), F(1, 2))))
P_X1 = matrix(((F(1, 2), F(-1, 2)), (F(-1, 2), F(1, 2))))
P_Y0 = ((Cx(F(1, 2), F(0)), Cx(F(0), F(-1, 2))), (Cx(F(0), F(1, 2)), Cx(F(1, 2), F(0))))
P_Y1 = ((Cx(F(1, 2), F(0)), Cx(F(0), F(1, 2))), (Cx(F(0), F(-1, 2)), Cx(F(1, 2), F(0))))
ID2 = identity(2)
PHI_PLUS_PROJECTOR = matrix(
    (
        (F(1, 2), 0, 0, F(1, 2)),
        (0, 0, 0, 0),
        (0, 0, 0, 0),
        (F(1, 2), 0, 0, F(1, 2)),
    )
)

#: The block kind every fixture below declares: the shared format's
#: ``proof_sector`` (:class:`~certiqs_key.foundations.blocks.BlockKind`,
#: spec/architecture.md 2.9, a frozen type of the shared format). The contract
#: NAMES the datum and the format FIXES the values, so open choice
#: ``OC-sector-block-kind`` is narrowed within that alphabet and still not
#: decided. ``proof_sector`` is the member these fixtures ARE: their
#: decomposition is "justified by dephasing or SOURCE REPLACEMENT", not photon
#: number (``physical_sector``) and not solver sparsity (``numerical_block``).
#: See :func:`instances.bb84.specification.band_a_block_kind` for the reading.
FIXTURE_BLOCK_KIND = BlockKind.PROOF_SECTOR

ONE_SECTOR_QUBIT = SectorStructure(
    labels=("s0",), dims=(2,), block_kind=FIXTURE_BLOCK_KIND
)
TWO_SECTOR_QUTRIT = SectorStructure(
    labels=("s0", "s1"), dims=(2, 1), block_kind=FIXTURE_BLOCK_KIND
)


def _mini(
    *,
    constraint_list: tuple[ConstraintEntry, ...] = (),
    alice_marginal: Matrix | None = None,
    key_map_override: dict[tuple[str, str], object] | None = None,
    bob_announcement_alphabet: tuple[str, ...] = ("beta0", "beta1"),
    accept_statistic: dict[tuple[str, str], str] | None = None,
) -> CandidateDeclaration:
    """Return the MINI candidate of the registry's Group PC-A header comment."""
    x_alphabet = ("x0", "x1")
    v_alphabet = ("v0", "v1")
    key_map: dict[tuple[str, str], object] = {
        ("x0", "v0"): 0,
        ("x0", "v1"): PERP,
        ("x1", "v0"): PERP,
        ("x1", "v1"): 1,
    }
    if key_map_override is not None:
        key_map = dict(key_map_override)
    statistic = accept_statistic or {
        ("alpha0", "beta0"): "g",
        ("alpha0", "beta1"): "d",
        ("alpha1", "beta0"): "d",
        ("alpha1", "beta1"): "g",
    }
    return CandidateDeclaration(
        alice_dim=2,
        alice_marginal=alice_marginal,
        sectors=ONE_SECTOR_QUBIT,
        alice_alphabet=x_alphabet,
        alice_povm={"x0": P_Z0, "x1": P_Z1},
        bob_alphabet=v_alphabet,
        bob_povm=family_as_blocks(ONE_SECTOR_QUBIT, {"v0": P_Z0, "v1": P_Z1}),
        partition=default_party_partition(x_alphabet, v_alphabet),
        announce_alice={"x0": "alpha0", "x1": "alpha1"},
        announce_bob={"v0": "beta0", "v1": "beta1"},
        alice_announcement_alphabet=("alpha0", "alpha1"),
        bob_announcement_alphabet=bob_announcement_alphabet,
        acceptance_alphabet=("g", "d"),
        accept_statistic=statistic,
        key_map=key_map,  # type: ignore[arg-type]
        key_alphabet=(0, 1),
        key_holder=Party.ALICE,
        constraint_list=constraint_list,
    )


MINI_ENTRY = ConstraintEntry(
    operator=as_blocks(ONE_SECTOR_QUBIT, P_Z0), relation=Relation.GE, rhs=F(1, 4)
)


def _mini_public() -> PublicPart:
    """Return MINI's public part ``S_pub``, from which Eq. eq:rdef is built."""
    x_alphabet = ("x0", "x1")
    v_alphabet = ("v0", "v1")
    classes = [(c_a, c_b) for c_a in ("alpha0", "alpha1") for c_b in ("beta0", "beta1")]
    return PublicPart(
        partition=default_party_partition(x_alphabet, v_alphabet),
        announce_alice={"x0": "alpha0", "x1": "alpha1"},
        announce_bob={"v0": "beta0", "v1": "beta1"},
        alice_announcement_alphabet=("alpha0", "alpha1"),
        bob_announcement_alphabet=("beta0", "beta1"),
        sifting={
            kappa: (
                Sifting.PASS
                if kappa in {("alpha0", "beta0"), ("alpha1", "beta1")}
                else Sifting.FAIL
            )
            for kappa in classes
        },
        key_rule={
            (readout, kappa): index
            for index, readout in enumerate(x_alphabet)
            for kappa in classes
        },
        holder=Party.ALICE,
        key_alphabet=(0, 1),
        acceptance_alphabet=("g", "d"),
        accept_statistic={
            kappa: ("g" if kappa in {("alpha0", "beta0"), ("alpha1", "beta1")} else "d")
            for kappa in classes
        },
    )


# ---------------------------------------------------------------------------
#  Group PC-A -- the label-to-index map (PC1)
# ---------------------------------------------------------------------------


def test_the_nine_indexed_alphabets_are_the_contracts_own() -> None:
    from certiqs_key.protocol_compiler import INDEXED_ALPHABETS as implemented

    assert implemented == INDEXED_ALPHABETS
    assert len(implemented) == 9


def test_label_index_map_reproduces_every_frozen_bijection() -> None:
    alphabets = {case.alphabet: case.labels for case in INDEX_MAP_CASES}
    built = build_label_index_map(alphabets)
    for case in INDEX_MAP_CASES:
        forward = {label: built.index_of(case.alphabet, label) for label in case.labels}
        assert tuple(forward.items()) == case.forward
        inverse = tuple(
            (index, built.label_of(case.alphabet, index))
            for index in range(len(case.labels))
        )
        assert inverse == case.inverse
        # Onto an INITIAL SEGMENT: indices 0..N-1 with no gaps (thm:typing).
        assert sorted(forward.values()) == list(range(len(case.labels)))


@pytest.mark.parametrize("case", INDEX_MAP_CASES, ids=lambda c: c.alphabet)
def test_a_repeated_label_admits_no_bijection(case: IndexMapCase) -> None:
    from certiqs_key.foundations.errors import MalformedInputError

    alphabets = {other.alphabet: other.labels for other in INDEX_MAP_CASES}
    alphabets[case.alphabet] = (*case.labels, case.labels[0])
    with pytest.raises(MalformedInputError):
        build_label_index_map(alphabets)


# ---------------------------------------------------------------------------
#  Group PC-B -- weights, not fractions; the statistics functional (PC2, PC3)
# ---------------------------------------------------------------------------

_CONDITIONALS: dict[str, tuple[Matrix, ...]] = {
    "z": (P_Z0, P_Z1),
    "x": (P_X0, P_X1),
}


def _weight_choices(case: WeightedFamilyCase) -> PublicChoices:
    """Return the ``public_choices`` record one frozen family is presented as."""
    if case.case_id in {"WEIGHT-alice", "WEIGHT-bob"}:
        conditionals = {
            case.choices[0]: _CONDITIONALS["z"],
            case.choices[1]: _CONDITIONALS["x"],
        }
        alphabets = dict.fromkeys(case.choices, ("0", "1"))
    elif case.case_id == "SECTOR-holds":
        conditionals = {
            case.choices[0]: (
                matrix(
                    (
                        (F(1, 2), F(1, 2), 0),
                        (F(1, 2), F(1, 2), 0),
                        (0, 0, 0),
                    )
                ),
                matrix(
                    (
                        (F(1, 2), F(-1, 2), 0),
                        (F(-1, 2), F(1, 2), 0),
                        (0, 0, 0),
                    )
                ),
                matrix(((0, 0, 0), (0, 0, 0), (0, 0, 1))),
            )
        }
        alphabets = {case.choices[0]: ("0", "1", "2")}
    else:
        conditionals = {
            case.choices[0]: (
                matrix(
                    (
                        (F(1, 2), 0, F(1, 2)),
                        (0, 0, 0),
                        (F(1, 2), 0, F(1, 2)),
                    )
                ),
                matrix(
                    (
                        (F(1, 2), 0, F(-1, 2)),
                        (0, 0, 0),
                        (F(-1, 2), 0, F(1, 2)),
                    )
                ),
                matrix(((0, 0, 0), (0, 1, 0), (0, 0, 0))),
            )
        }
        alphabets = {case.choices[0]: ("0", "1", "2")}
    return PublicChoices(
        party=Party.ALICE if case.party == "A" else Party.BOB,
        choices=case.choices,
        weights=dict(zip(case.choices, case.weights, strict=True)),
        conditional_alphabets=alphabets,
        conditional_elements={
            choice: dict(zip(alphabets[choice], conditionals[choice], strict=True))
            for choice in case.choices
        },
    )


@pytest.mark.parametrize("case", WEIGHTED_FAMILY_CASES, ids=lambda c: c.case_id)
def test_weighted_family_reproduces_the_frozen_emission(
    case: WeightedFamilyCase,
) -> None:
    from certiqs_key.protocol_compiler import is_povm, weighted_family

    family = weighted_family(_weight_choices(case))
    assert family.alphabet == case.joint_alphabet
    assert tuple(family.choice_of[label] for label in family.alphabet) == case.choice_of
    for label, expected in zip(case.joint_alphabet, case.emitted, strict=True):
        assert equal(family.elements[label], reg(expected))
    dim = len(case.emitted[0])
    assert is_povm(family.ordered(), dim)

    # BLOCK-DIAGONALITY IS NOW TYPING AND THERE IS NO PREDICATE TO CALL.
    # `is_sector_block_diagonal` is deleted at 0.3.0: Section 2.5
    # (`operator_form`), "Sector-block-diagonality HOLDS BY CONSTRUCTION;
    # nothing verifies that the off-sector entries are zero, BECAUSE NOTHING
    # CAN WRITE THEM." The frozen `block_diagonal` field is asserted here in
    # the only way that survives -- whether the emitted family HAS a block list
    # against the case's map at all. A family that does not is inexpressible,
    # which is `SUPERSEDED_BY_SCOPE_0_3_0`'s WEIGHTED_FAMILY_CASES/SECTOR-fails
    # entry: "A FAMILY THAT IS NOT SECTOR-BLOCK-DIAGONAL IS NOW INEXPRESSIBLE."
    dims = tuple(_projector_dim(reg(p)) for p in case.sector_projectors)
    if dims:
        expressible = True
        try:
            for element in family.ordered():
                split(element, dims)
        except NotBlockDiagonalError:
            expressible = False
        assert expressible is case.block_diagonal


def _projector_dim(projector: Matrix) -> int:
    """Return the rank of a frozen sector projector, i.e. its block dimension.

    The registry freezes the sector decomposition as its PROJECTORS; a block
    list is indexed by the block DIMENSIONS, so the fixture reads each d_s off
    the projector it was frozen as. Diagonal 0/1 by Section 2.5
    (subsystem_order), so the rank is the count of ones on the diagonal.
    """
    return sum(1 for i in range(len(projector)) if projector[i][i] == ONE)


def _weight_declaration() -> CandidateDeclaration:
    """Return the two-sided WEIGHT declaration of Group PC-B."""
    from certiqs_key.protocol_compiler import weighted_family

    alice = weighted_family(_weight_choices(WEIGHTED_FAMILY_CASES[0]))
    bob = weighted_family(_weight_choices(WEIGHTED_FAMILY_CASES[1]))
    classes = [(c_a, c_b) for c_a in ("t0", "t1") for c_b in ("r0", "r1")]
    return CandidateDeclaration(
        alice_dim=2,
        alice_marginal=None,
        sectors=ONE_SECTOR_QUBIT,
        alice_alphabet=alice.alphabet,
        alice_povm=alice.elements,
        bob_alphabet=bob.alphabet,
        bob_povm=family_as_blocks(ONE_SECTOR_QUBIT, bob.elements),
        partition=default_party_partition(alice.alphabet, bob.alphabet),
        announce_alice={label: alice.choice_of[label] for label in alice.alphabet},
        announce_bob={label: bob.choice_of[label] for label in bob.alphabet},
        alice_announcement_alphabet=("t0", "t1"),
        bob_announcement_alphabet=("r0", "r1"),
        acceptance_alphabet=("match", "cross"),
        accept_statistic={
            kappa: ("match" if kappa in {("t0", "r0"), ("t1", "r1")} else "cross")
            for kappa in classes
        },
        key_map=dict.fromkeys(_all_pairs(alice.alphabet, bob.alphabet), 0),
        key_alphabet=(0,),
        key_holder=Party.ALICE,
    )


def _all_pairs(
    left: tuple[str, ...], right: tuple[str, ...]
) -> tuple[tuple[str, str], ...]:
    return tuple((a, b) for a in left for b in right)


@pytest.mark.parametrize("case", JOINT_DISTRIBUTION_CASES, ids=lambda c: c.case_id)
def test_joint_distribution_and_phi_reproduce_the_frozen_tables(
    case: JointDistributionCase,
) -> None:
    from certiqs_key.protocol_compiler import weighted_family

    declaration = _weight_declaration()
    state = reg(case.state)
    joint = joint_distribution(declaration, state)
    assert case.alice_alphabet == declaration.alice_alphabet
    assert case.bob_alphabet == declaration.bob_alphabet
    for x, row in zip(case.alice_alphabet, case.joint, strict=True):
        for v, expected in zip(case.bob_alphabet, row, strict=True):
            assert joint[(x, v)] == expected

    statistics = phi_distribution(declaration, state)
    assert case.acceptance_alphabet == declaration.acceptance_alphabet
    for value, expected in zip(case.acceptance_alphabet, case.phi_vector, strict=True):
        assert statistics.values[value] == expected
    assert statistics.total == 1

    # The fibres, as index pairs into the two emitted alphabets.
    for value, fibre in zip(case.acceptance_alphabet, case.phi_fibres, strict=True):
        indices = tuple(
            (case.alice_alphabet.index(x), case.bob_alphabet.index(v))
            for x, v in statistics.fibres[value]
        )
        assert sorted(indices) == sorted(fibre)

    # Eq. eq:choicemass: the SAME four numbers at both states.
    alice = weighted_family(_weight_choices(WEIGHTED_FAMILY_CASES[0]))
    bob = weighted_family(_weight_choices(WEIGHTED_FAMILY_CASES[1]))
    for choice, declared, expected in case.choice_mass:
        family = alice if choice in alice.weights else bob
        assert family.weights[choice] == declared
        assert choice_mass(family, choice, state, 2) == expected


def test_a_partial_phi_loses_exactly_the_dropped_class_mass() -> None:
    """O-PC-PARTIAL-PHI: V1 refuses, and the deficit is the class's own mass."""
    declaration = _weight_declaration()
    partial = dict(declaration.accept_statistic)
    del partial[("t1", "r0")]
    crippled = CandidateDeclaration(
        **{**declaration.__dict__, "accept_statistic": partial}
    )
    result = validate(crippled)
    assert "V1" in result.refusing_checks
    assert result.first_refusal is not None
    assert result.first_refusal.reason is RefusalReason.CHECK_V1_FAILED

    for case in JOINT_DISTRIBUTION_CASES:
        state = reg(case.state)
        joint = joint_distribution(declaration, state)
        surviving = sum(
            (
                joint[pair]
                for pair in declaration.outcome_pairs()
                if declaration.announcement(*pair) in partial
            ),
            F(0),
        )
        assert surviving == F(7, 8)
        assert announcement_class_mass(declaration, state, ("t1", "r0")) == F(1, 8)


def test_the_fixed_fraction_refusal_carries_the_contracts_own_string() -> None:
    from certiqs_key.protocol_compiler import refuse_fixed_fraction

    refusal = refuse_fixed_fraction("a caller selected fixed_fraction out of band")
    assert refusal.reason == "fixed_fraction_requested"
    assert str(refusal.reason) in {str(reason) for reason in REFUSAL_REASONS_VERBATIM}
    # AND NO INPUT KEY CARRIES A MODEL SELECTOR: the twelve are the twelve.
    assert tuple(INPUT_KEYS) == INPUT_KEYS
    assert not any("model" in key or "fraction" in key for key in INPUT_KEYS)


# ---------------------------------------------------------------------------
#  Group PC-C -- sifting and party computability (PC4)
# ---------------------------------------------------------------------------


def _key_map_declaration(case: KeyMapCase) -> CandidateDeclaration:
    """Return the candidate one frozen key-map case describes."""
    announcement = {
        (case.alice_alphabet[x], case.bob_alphabet[v]): _class(label)
        for x, v, label in case.announcement
    }
    key_map = {
        (case.alice_alphabet[x], case.bob_alphabet[v]): value
        for x, v, value in case.key_map
    }
    alice_classes = tuple(dict.fromkeys(k[0] for k in announcement.values()))
    bob_classes = tuple(dict.fromkeys(k[1] for k in announcement.values()))
    announce_alice = {
        x: next(k[0] for (px, _), k in announcement.items() if px == x)
        for x in case.alice_alphabet
    }
    announce_bob = {
        v: next(k[1] for (_, pv), k in announcement.items() if pv == v)
        for v in case.bob_alphabet
    }
    alice_povm = (
        {"x0": ID2} if len(case.alice_alphabet) == 1 else {"x0": P_Z0, "x1": P_Z1}
    )
    alice_dim = 2 if len(case.alice_alphabet) > 1 else 1
    if alice_dim == 1:
        alice_povm = {"x0": matrix(((1,),))}
    return CandidateDeclaration(
        alice_dim=alice_dim,
        alice_marginal=None,
        sectors=ONE_SECTOR_QUBIT,
        alice_alphabet=case.alice_alphabet,
        alice_povm=alice_povm,
        bob_alphabet=case.bob_alphabet,
        bob_povm=family_as_blocks(ONE_SECTOR_QUBIT, {"v0": P_Z0, "v1": P_Z1}),
        partition=default_party_partition(case.alice_alphabet, case.bob_alphabet),
        announce_alice=announce_alice,
        announce_bob=announce_bob,
        alice_announcement_alphabet=alice_classes,
        bob_announcement_alphabet=bob_classes,
        acceptance_alphabet=("c",),
        accept_statistic={(a, b): "c" for a in alice_classes for b in bob_classes},
        key_map=key_map,  # type: ignore[arg-type]
        key_alphabet=(0, 1),
        key_holder=Party.ALICE,
    )


@pytest.mark.parametrize("case", KEY_MAP_CASES, ids=lambda c: c.case_id)
def test_v5_and_v8_verdicts_match_the_frozen_ones(case: KeyMapCase) -> None:
    from certiqs_key.protocol_compiler import check_v5, check_v8

    declaration = _key_map_declaration(case)
    assert check_v5(declaration).passed is case.v5_passes
    assert check_v8(declaration).passed is case.v8_passes


@pytest.mark.parametrize("case", KEY_MAP_CASES, ids=lambda c: c.case_id)
def test_the_joint_pair_reading_of_partycomp_always_passes(case: KeyMapCase) -> None:
    """Remark rem:vacuous: read against ``(x, v)`` the condition is vacuous."""
    declaration = _key_map_declaration(case)
    joint_pair_rule: dict[tuple[str, str], object] = {}
    satisfied = True
    for pair in declaration.outcome_pairs():
        value = declaration.key_map[pair]
        if pair in joint_pair_rule and joint_pair_rule[pair] != value:
            satisfied = False
        joint_pair_rule[pair] = value
    assert satisfied is case.joint_pair_reading_passes is True


def test_the_mini_key_map_and_both_r_hold_extensions() -> None:
    case = next(c for c in KEY_MAP_CASES if c.case_id == "KEY-MINI")
    public = _mini_public()
    built = raw_key_map(public, case.alice_alphabet, case.bob_alphabet)
    for x, v, expected in case.key_map:
        assert built[(case.alice_alphabet[x], case.bob_alphabet[v])] == expected

    declared = derived_holder_key_rule(public)
    for readout, label, expected in case.r_hold_eq_rhold:
        assert declared[(readout, _class(label))] == expected

    rebuilt = reconstruct_holder_key_rule(_mini(constraint_list=(MINI_ENTRY,)))
    for readout, label, expected in case.r_hold_reconstructed:
        assert rebuilt[(readout, _class(label))] == expected

    realized = realized_readout_classes(_mini(constraint_list=(MINI_ENTRY,)))
    assert sorted(realized) == sorted(
        (readout, _class(label)) for readout, label in case.realized_pairs
    )
    # THE TWO TABLES AGREE ON THE REALIZED SET AND DIFFER OFF IT.
    assert all(declared[pair] == rebuilt[pair] for pair in realized)
    assert declared != rebuilt


def test_the_side_condition_of_rem_sidecond_is_decided_on_the_specification() -> None:
    from certiqs_key.protocol_compiler import key_rule_side_condition

    public = _mini_public()
    assert key_rule_side_condition(public) is True
    violated = PublicPart(
        **{
            **public.__dict__,
            "key_rule": {**public.key_rule, (("x0"), ("alpha0", "beta0")): PERP},
        }
    )
    assert key_rule_side_condition(violated) is False


# ---------------------------------------------------------------------------
#  Group PC-D -- the feasible set (PC5, thm:validator-soundness (iii))
# ---------------------------------------------------------------------------


def _witness_declaration(case: WitnessCase) -> CandidateDeclaration:
    """Return the candidate one frozen witness case describes."""
    sectors = SectorStructure(
        labels=tuple(f"s{i}" for i in range(len(case.sector_dims))),
        dims=case.sector_dims,
        block_kind=FIXTURE_BLOCK_KIND,
    )
    entries = tuple(
        ConstraintEntry(
            operator=as_blocks(sectors, reg(operator)),
            relation={"<=": Relation.LE, "=": Relation.EQ, ">=": Relation.GE}[relation],
            rhs=rhs if isinstance(rhs, F) else reg(rhs),
        )
        for operator, relation, rhs in case.constraints
    )
    x_alphabet = tuple(f"x{i}" for i in range(case.alice_dim))
    v_alphabet = tuple(f"v{i}" for i in range(case.q_dim))
    alice_povm = {
        label: _basis_projector(case.alice_dim, i) for i, label in enumerate(x_alphabet)
    }
    bob_povm = family_as_blocks(
        sectors,
        {label: _basis_projector(case.q_dim, i) for i, label in enumerate(v_alphabet)},
    )
    return CandidateDeclaration(
        alice_dim=case.alice_dim,
        alice_marginal=None if case.tau_a is None else reg(case.tau_a),
        sectors=sectors,
        alice_alphabet=x_alphabet,
        alice_povm=alice_povm,
        bob_alphabet=v_alphabet,
        bob_povm=bob_povm,
        partition=default_party_partition(x_alphabet, v_alphabet),
        announce_alice=dict.fromkeys(x_alphabet, "a"),
        announce_bob=dict.fromkeys(v_alphabet, "b"),
        alice_announcement_alphabet=("a",),
        bob_announcement_alphabet=("b",),
        acceptance_alphabet=("c",),
        accept_statistic={("a", "b"): "c"},
        key_map=dict.fromkeys(_all_pairs(x_alphabet, v_alphabet), 0),
        key_alphabet=(0,),
        key_holder=Party.ALICE,
        constraint_list=entries,
    )


def _basis_projector(dim: int, index: int) -> Matrix:
    """Return ``|index><index|`` on a ``dim``-dimensional space."""
    return tuple(
        tuple(
            Cx(F(1), F(0)) if (i == index and j == index) else Cx(F(0), F(0))
            for j in range(dim)
        )
        for i in range(dim)
    )


@pytest.mark.parametrize("case", WITNESS_CASES, ids=lambda c: c.case_id)
def test_the_default_witness_and_every_verification_leg(case: WitnessCase) -> None:
    from certiqs_key.protocol_compiler import check_feasibility

    declaration = _witness_declaration(case)
    assert case.witness is not None
    witness = joint_as_blocks(
        declaration.sectors, declaration.alice_dim, reg(case.witness)
    )
    if case.is_default_witness:
        assert equal(default_witness(declaration).dense(), witness.dense())

    verification = verify_witness(declaration, witness)
    assert verification.positive is case.leg_positive
    assert verification.trace_one is case.leg_trace_one
    # THE SECTOR LEG IS SUPERSEDED BY SCOPE at 0.3.0: with omega presented as a
    # block list "the off-block conjunct HOLDS BY THE PRESENTATION and there is
    # nothing to verify" (Theorem thm:feasibility (i)), so the frozen
    # `leg_sector_blocks` value has no predicate left to compare against. The
    # fixture adaptor asserts the same content in a stronger place: a dense
    # witness with off-block mass has NO IMAGE as a block list at all.
    assert case.leg_sector_blocks is True
    assert verification.marginal is case.leg_marginal
    assert verification.constraints is case.leg_constraints
    assert tuple(verification.constraint_values) == tuple(case.constraint_values)

    supplied = None if case.is_default_witness else witness
    outcome = check_feasibility(declaration, supplied)
    assert outcome.passes is case.v7_passes
    if case.refusal_reason is None:
        assert outcome.refusal is None or not case.v7_passes
    else:
        assert outcome.refusal is not None
        assert str(outcome.refusal.reason) == case.refusal_reason


@pytest.mark.parametrize("case", WITNESS_LEG_FAILURES, ids=lambda c: c.case_id)
def test_one_supplied_witness_fails_each_leg_and_no_other(case: WitnessCase) -> None:
    """Each frozen leg case fails its own leg of Theorem thm:feasibility (ii) and no other.

    ``v7_passes`` IS READ HERE AS A STATEMENT ABOUT THE WITNESS, which is what
    ``WitnessCase`` documents itself as ("one feasibility witness, verified
    condition by condition") and what these five rows exercise. Four of them
    carry an EMPTY constraint list, so V7 as a whole nevertheless passes on
    those declarations -- by its FIRST branch, which Theorem ``thm:feasibility`` (i)
    PROVES rather than checks, and which never looks at a supplied witness.
    That is a fact about the declaration and not about the witness, and the
    fifth row, ``LEG-constraint``, is the one at ``m >= 1`` where the two
    coincide: there the default candidate fails too and V7 refuses with the
    verbatim reason the row carries.
    """  # noqa: E501
    from certiqs_key.protocol_compiler import check_feasibility

    declaration = _witness_declaration(case)
    assert case.witness is not None
    if not case.leg_sector_blocks:
        # THE SECTOR LEG IS SUPERSEDED BY SCOPE and this row's subject is gone
        # with it: a witness with off-block mass is INEXPRESSIBLE, not
        # merely refused. Theorem ``thm:feasibility`` (i): "omega^* is presented AS A
        # LIST ... so the off-block conjunct HOLDS BY THE PRESENTATION and
        # there is NOTHING TO VERIFY -- structural, not an argument". The frozen witness
        # is asserted to have
        # NO image as a block list, which is a STRONGER statement than a
        # refusal: the module cannot be handed this object at all.
        with pytest.raises(NotBlockDiagonalError):
            joint_as_blocks(
                declaration.sectors, declaration.alice_dim, reg(case.witness)
            )
        assert case.v7_passes is False
        return
    verification = verify_witness(
        declaration,
        joint_as_blocks(declaration.sectors, declaration.alice_dim, reg(case.witness)),
    )
    assert verification.positive is case.leg_positive
    assert verification.trace_one is case.leg_trace_one
    assert verification.marginal is case.leg_marginal
    assert verification.constraints is case.leg_constraints
    assert tuple(verification.constraint_values) == tuple(case.constraint_values)
    assert verification.passes is case.v7_passes is False
    assert len(verification.failing_legs()) == 1

    outcome = check_feasibility(
        declaration,
        joint_as_blocks(declaration.sectors, declaration.alice_dim, reg(case.witness)),
    )
    if case.refusal_reason is not None:
        assert outcome.passes is False
        assert outcome.refusal is not None
        assert str(outcome.refusal.reason) == case.refusal_reason
        assert outcome.first_branch is False
    else:
        # The empty-list rows: V7 passes by Theorem thm:feasibility (i), on the
        # DEFAULT candidate and not on the supplied one.
        assert outcome.first_branch is True
        assert outcome.passes is True
        assert outcome.used_default is True
        assert outcome.witness is not None
        assert equal(outcome.witness.dense(), default_witness(declaration).dense())


def test_rem_wellposed_two_exact_witnesses() -> None:
    """O-PC-WELLPOSED: both lines lose their MEANING, and V3 is what refuses."""
    from certiqs_key.foundations.errors import HypothesisError
    from certiqs_key.protocol_compiler import check_v3

    non_hermitian = matrix(((0, 1), (0, 0)))
    # Witness 1: the trusted partial trace is (1/2) O^T, which is NOT Hermitian.
    joint = kron(ID2, non_hermitian)
    from certiqs_key.foundations.exact import partial_trace_second

    value = partial_trace_second(matmul(joint, PHI_PLUS_PROJECTOR), 2, 2)
    assert equal(value, scale(F(1, 2), matrix(((0, 0), (1, 0)))))
    from certiqs_key.foundations.exact import is_hermitian

    assert is_hermitian(value) is False

    # Witness 2: the untrusted scalar is i/2, which is not real.
    imaginary = ((Cx(F(0), F(1)), Cx(F(0), F(0))), (Cx(F(0), F(0)), Cx(F(0), F(0))))
    maximally_mixed = scale(F(1, 4), identity(4))
    scalar = trace(matmul(kron(ID2, imaginary), maximally_mixed))
    assert scalar == Cx(F(0), F(1, 2))

    # AND V3 REFUSES BOTH BEFORE Eq. eq:feas-modes IS EVALUATED.
    for operator in (non_hermitian, imaginary):
        declaration = _mini(
            constraint_list=(
                ConstraintEntry(
                    operator=as_blocks(ONE_SECTOR_QUBIT, operator),
                    relation=Relation.GE,
                    rhs=F(0),
                ),
            )
        )
        outcome = check_v3(declaration)
        assert outcome.passed is False
        assert outcome.refusal is not None
        assert outcome.refusal.reason is RefusalReason.CHECK_V3_FAILED
        with pytest.raises(HypothesisError):
            verify_witness(declaration, default_witness(declaration))


# ---------------------------------------------------------------------------
#  Group PC-E -- the validator (PC6)
# ---------------------------------------------------------------------------


def _sector_declaration(entries: int) -> CandidateDeclaration:
    """Return the two-sector receiver of Group PC-B as a candidate."""
    bob_povm = family_as_blocks(
        TWO_SECTOR_QUTRIT,
        {
            "v0": matrix(((F(1, 2), F(1, 2), 0), (F(1, 2), F(1, 2), 0), (0, 0, 0))),
            "v1": matrix(((F(1, 2), F(-1, 2), 0), (F(-1, 2), F(1, 2), 0), (0, 0, 0))),
            "v2": matrix(((0, 0, 0), (0, 0, 0), (0, 0, 1))),
        },
    )
    x_alphabet = ("x0", "x1")
    v_alphabet = ("v0", "v1", "v2")
    entry = ConstraintEntry(
        operator=as_blocks(
            TWO_SECTOR_QUTRIT, matrix(((1, 0, 0), (0, 0, 0), (0, 0, 0)))
        ),
        relation=Relation.GE,
        rhs=F(0),
    )
    return CandidateDeclaration(
        alice_dim=2,
        alice_marginal=None,
        sectors=TWO_SECTOR_QUTRIT,
        alice_alphabet=x_alphabet,
        alice_povm={"x0": P_Z0, "x1": P_Z1},
        bob_alphabet=v_alphabet,
        bob_povm=bob_povm,
        partition=default_party_partition(x_alphabet, v_alphabet),
        announce_alice={"x0": "a0", "x1": "a1"},
        announce_bob=dict.fromkeys(v_alphabet, "b0"),
        alice_announcement_alphabet=("a0", "a1"),
        bob_announcement_alphabet=("b0",),
        acceptance_alphabet=("c",),
        accept_statistic={("a0", "b0"): "c", ("a1", "b0"): "c"},
        # A function of the holder readout alone, so that V8 passes and the
        # case isolates V3 (Remark rem:vacuous is what V8 is FOR).
        key_map={
            (x, v): x_alphabet.index(x) for x, v in _all_pairs(x_alphabet, v_alphabet)
        },
        key_alphabet=(0, 1),
        key_holder=Party.ALICE,
        constraint_list=(entry,) * entries,
    )


def _validator_candidate(case: ValidatorCase) -> CandidateDeclaration:
    """Return the candidate one frozen validator case describes."""
    if case.case_id == "ALLPASS-MINI":
        return _mini(constraint_list=(MINI_ENTRY,))
    if case.case_id == "V1-partial-phi":
        declaration = _weight_declaration()
        partial = dict(declaration.accept_statistic)
        del partial[("t1", "r0")]
        return CandidateDeclaration(
            **{**declaration.__dict__, "accept_statistic": partial}
        )
    if case.case_id == "V2-zero-marginal":
        return _mini(alice_marginal=matrix(((0, 0), (0, 0))))
    if case.case_id == "V3-block-diagonality":
        raise AssertionError(
            "V3-block-diagonality has no candidate at 0.3.0 -- see "
            "`_v3_block_diagonality_is_inexpressible`"
        )
    if case.case_id == "V4-key-value-outside-alphabet":
        return _mini(
            constraint_list=(MINI_ENTRY,),
            key_map_override={
                ("x0", "v0"): 2,
                ("x0", "v1"): PERP,
                ("x1", "v0"): PERP,
                ("x1", "v1"): 1,
            },
        )
    if case.case_id == "V5-sifting-consistency":
        return _key_map_declaration(
            next(c for c in KEY_MAP_CASES if c.case_id == "KEY-SIDECOND")
        )
    if case.case_id == "V6-constraint-typing":
        # 0.3.0: this fixture holds nomarg in the marginal slot, "where ONLY
        # THE SCALAR FORM EXISTS" (Definition def:homog), so a MATRIX
        # right-hand side is what V6 refuses here. Through 0.2.0 the refusal
        # ran the other way -- V6 "REQUIRED A MATRIX WHENEVER THE MARGINAL SLOT
        # WAS FILLED", which is the defect this version repairs.
        return _mini(
            constraint_list=(
                ConstraintEntry(
                    operator=as_blocks(ONE_SECTOR_QUBIT, P_Z0),
                    relation=Relation.GE,
                    rhs=scale(F(1, 2), P_Z0),
                ),
            )
        )
    if case.case_id == "V7-well-formed-but-refused":
        return _mini(
            constraint_list=(
                ConstraintEntry(
                    operator=as_blocks(ONE_SECTOR_QUBIT, P_Z0),
                    relation=Relation.GE,
                    rhs=F(1),
                ),
            )
        )
    return _key_map_declaration(next(c for c in KEY_MAP_CASES if c.case_id == "KEY-V8"))


@pytest.mark.parametrize("case", VALIDATOR_CASES, ids=lambda c: c.case_id)
def test_every_validator_case_refuses_at_the_check_it_names(
    case: ValidatorCase,
) -> None:
    if case.case_id == "V3-block-diagonality":
        _v3_block_diagonality_is_inexpressible()
        return
    candidate = _validator_candidate(case)
    result = validate(candidate)
    assert result.passed is not case.refuses
    if case.check is None:
        assert result.refusing_checks == ()
        assert result.unevaluated_checks == ()
    else:
        assert result.refusing_checks == (case.check,)
        assert result.outcome_of(case.check).passed is False


def _v3_block_diagonality_is_inexpressible() -> None:
    """Assert that the frozen V3 counterexample has no candidate at 0.3.0.

    ``SUPERSEDED_BY_SCOPE_0_3_0``, ``VALIDATOR_CASES/V3-block-diagonality``:
    "V3's OFF-BLOCK CONDITIONS ARE DELETED ... an emitted Q-operator is a block
    list, so there is NO ``Pi_s F_v Pi_{s'}`` or ``Pi_s O^_k Pi_{s'}`` TO
    EVALUATE and NOTHING THAT COULD BE NON-ZERO. What replaced them is V1'S
    SECTOR-MAP COMPARISON, AND NOTHING ELSE DID."

    So the frozen family cannot be presented to a 0.3.0 compiler at all --
    Definition ``def:exact`` (T) calls an off-block entry "NOT SMALL BUT
    INEXPRESSIBLE" -- and this asserts exactly that, in the place where the
    0.1.4 test asserted a refusal. THE CASE'S D(iii) TARGET SURVIVES AND ITS
    MECHANISM DOES NOT; its replacement is exercised by the V1 sector-map
    cases.
    """
    family = {
        "v0": matrix(((F(1, 2), 0, F(1, 2)), (0, 0, 0), (F(1, 2), 0, F(1, 2)))),
        "v1": matrix(((F(1, 2), 0, F(-1, 2)), (0, 0, 0), (F(-1, 2), 0, F(1, 2)))),
        "v2": matrix(((0, 0, 0), (0, 1, 0), (0, 0, 0))),
    }
    inexpressible = []
    for label, element in family.items():
        try:
            split(element, TWO_SECTOR_QUTRIT.dims)
        except NotBlockDiagonalError:
            inexpressible.append(label)
    # The frozen family's defect is carried by v0 and v1, whose coherence
    # between sector s0 and sector s1 is exactly the `Pi_s F_v Pi_{s'} != 0`
    # the deleted conditions caught. v2 is block-diagonal and is expressible;
    # what has no image is the FAMILY, which is what D(iii) quantifies over.
    assert inexpressible == ["v0", "v1"]


def test_v1_refuses_a_family_whose_sector_map_disagrees() -> None:
    """V1 exercised on the structural error a block list can still carry.

    A family whose OWN sector map disagrees with the emitted one -- which is
    the one structural error a block list can still carry -- is refused by V1
    with the contract's own ``sector_map_mismatch``, "NAMING THE FIRST POSITION
    AT WHICH THE LISTS DIFFER".
    """
    from certiqs_key.foundations.blocks import BlockOperator
    from certiqs_key.protocol_compiler import check_v1

    declaration = _sector_declaration(0)
    permuted = SectorStructure(
        labels=("s1", "s0"), dims=(1, 2), block_kind=FIXTURE_BLOCK_KIND
    )
    element = declaration.bob_povm["v2"]
    broken = CandidateDeclaration(
        **{
            **declaration.__dict__,
            "bob_povm": {
                **declaration.bob_povm,
                "v2": BlockOperator.of(
                    permuted, (element.blocks[1], element.blocks[0])
                ),
            },
        }
    )
    outcome = check_v1(broken)
    assert outcome.passed is False
    assert outcome.refusal is not None
    assert str(outcome.refusal.reason) == "sector_map_mismatch"
    assert "order" in outcome.refusal.detail
    assert "position 0" in outcome.refusal.detail


def test_v7_is_the_only_check_that_refuses_a_well_formed_declaration() -> None:
    case = next(c for c in VALIDATOR_CASES if c.case_id == "V7-well-formed-but-refused")
    assert case.well_formed is True
    assert case.genuine_violation is False
    candidate = _validator_candidate(case)
    result = validate(candidate)
    assert result.refusing_checks == ("V7",)
    assert result.feasibility.refusal is not None
    assert str(result.feasibility.refusal.reason) == "no_feasibility_witness"
    # D(vii) NEVERTHELESS HOLDS: omega = tau (x) |0><0| is feasible for any tau.
    for tau in (scale(F(1, 2), ID2), P_Z0):
        assert (
            in_feasible_set(
                candidate,
                joint_as_blocks(
                    candidate.sectors, candidate.alice_dim, kron(tau, P_Z0)
                ),
            )
            is True
        )
    # And exactly one frozen case has genuine_violation False.
    assert sum(1 for c in VALIDATOR_CASES if not c.genuine_violation and c.refuses) == 1


@pytest.mark.parametrize("case", RECONSTRUCTION_CASES, ids=lambda c: c.case_id)
def test_the_two_reconstructions_of_thm_pc6(case: ReconstructionCase) -> None:
    if case.case_id == "RECON-varsigma-MINI":
        declaration = _mini(constraint_list=(MINI_ENTRY,))
        rebuilt = reconstruct_sifting_predicate(declaration)
        for label, _declared, expected in case.rows:
            assert str(rebuilt[_class(label)]) == expected
        assert case.agree_everywhere is True
    elif case.case_id == "RECON-varsigma-unrealized":
        statistic = {
            (a, b): (
                "g" if (a, b) in {("alpha0", "beta0"), ("alpha1", "beta1")} else "d"
            )
            for a in ("alpha0", "alpha1")
            for b in ("beta0", "beta1", "beta2")
        }
        declaration = _mini(
            constraint_list=(MINI_ENTRY,),
            bob_announcement_alphabet=("beta0", "beta1", "beta2"),
            accept_statistic=statistic,
        )
        rebuilt = reconstruct_sifting_predicate(declaration)
        for label, declared, expected in case.rows:
            kappa = _class(label)
            assert str(rebuilt[kappa]) == expected
            if declared != expected:
                assert kappa not in {
                    declaration.announcement(*pair)
                    for pair in declaration.outcome_pairs()
                }
        assert case.agree_everywhere is False
    else:
        declaration = _mini(constraint_list=(MINI_ENTRY,))
        declared = derived_holder_key_rule(_mini_public())
        rebuilt_rule = reconstruct_holder_key_rule(declaration)
        for argument, declared_value, rebuilt_value in case.rows:
            readout, label = argument[1:-1].split(", ", 1)
            key = (readout, _class(label))
            assert str(declared[key]) == declared_value
            assert str(rebuilt_rule[key]) == rebuilt_value
        assert case.agree_everywhere is False


@pytest.mark.parametrize("case", DECIDABILITY_COUNTS, ids=lambda c: c.case_id)
def test_the_decidability_counts_of_thm_pc6_iv(case: DecidabilityCount) -> None:
    declaration = (
        _mini(constraint_list=(MINI_ENTRY,))
        if case.case_id == "COUNT-MINI"
        else _sector_declaration(case.constraint_count)
    )
    counts = decidability_counts(declaration)
    assert len(declaration.alice_alphabet) == case.x_size
    assert len(declaration.bob_alphabet) == case.v_size
    assert declaration.sectors.count == case.sector_count
    assert len(declaration.constraint_list) == case.constraint_count
    assert counts.block_conditions == case.block_conditions
    assert counts.v4_pairs == case.v4_pairs
    assert counts.ordered_pairs == case.ordered_pairs


# ---------------------------------------------------------------------------
#  Group PC-F -- the reduction chain (PC7, PC8)
# ---------------------------------------------------------------------------

# THE LAST LINK'S TARGET DESCRIPTOR *IS* THE SECTOR MAP (Definition
# ``def:chaincond`` (C1)), and since 0.3.0 the map carries its block kind --
# (C1) is decided "BY THE SAME FOUR-COMPONENT COMPARISON V1 MAKES".
Q_DESCRIPTOR = SystemDescriptor("Q", 2, Side.RECEIVER, (("s0", 2),), FIXTURE_BLOCK_KIND)
DESCRIPTORS: dict[str, SystemDescriptor] = {
    "(Q, (s0), (2))": Q_DESCRIPTOR,
    "C^2 (physical receiver space)": SystemDescriptor("C^2", 2, Side.RECEIVER),
    "C^3 (physical receiver space)": SystemDescriptor("C^3", 3, Side.RECEIVER),
    "C^4 (physical receiver space)": SystemDescriptor("C^4", 4, Side.RECEIVER),
    "C^2": SystemDescriptor("C^2", 2, Side.RECEIVER),
    "C^3": SystemDescriptor("C^3", 3, Side.RECEIVER),
    "A'' (virtual transmitted system, a qubit)": SystemDescriptor("A''", 2, Side.ALICE),
    "A' (transmitted system, a qubit)": SystemDescriptor("A'", 2, Side.ALICE),
    "A'' (a qubit)": SystemDescriptor("A''", 2, Side.ALICE),
    "A' (a qubit)": SystemDescriptor("A'", 2, Side.ALICE),
    "A_mid (a qubit)": SystemDescriptor("A_mid", 2, Side.ALICE),
    "A_mid' (a QUTRIT)": SystemDescriptor("A_mid'", 3, Side.ALICE),
}

_COARSE_KRAUS = (
    matrix(((1, 0, 0), (0, 1, 0))),
    matrix(((0, 0, 0), (0, 0, 1))),
)
_DEPHASING_KRAUS = (P_Z0, P_Z1)
_BITFLIP_KRAUS = (matrix(((0, 1), (1, 0))),)


def _channel_for(case_id: str, link_id: str, dim: int) -> tuple[Matrix, ...] | None:
    """Return the channel a frozen link supplies as data, or ``None``."""
    if case_id == "CHAIN-not-decided-C4-S3":
        return None
    if case_id == "CHAIN-coarse-proper" or (
        case_id == "CHAIN-receiver-descriptor-mismatch" and link_id == "Lambda_1"
    ):
        return (
            _COARSE_KRAUS if case_id == "CHAIN-coarse-proper" else identity_channel(dim)
        )
    if case_id == "CHAIN-srcmap-failure" and link_id == "Xi_1":
        return _DEPHASING_KRAUS
    return identity_channel(dim)


def _build_chain(case: ChainCase) -> ReductionChain:
    """Return the typed chain one frozen case presents."""
    source = tuple(
        ChainLink(
            link_id=link.link_id,
            segment=LinkStage.SOURCE,
            link_type=link.link_type,
            source_descriptor=DESCRIPTORS[link.source_descriptor],
            target_descriptor=DESCRIPTORS[link.target_descriptor],
            status=LinkStatus(link.status),
            channel=(
                _channel_for(
                    case.case_id,
                    link.link_id,
                    DESCRIPTORS[link.source_descriptor].dim,
                )
                if link.channel_supplied
                else None
            ),
            transported_constraints=(
                (
                    ConstraintEntry(
                        operator=as_blocks(ONE_SECTOR_QUBIT, P_Z0),
                        relation=Relation.GE,
                        rhs=F(0),
                    ),
                )
                if link.transported_constraints
                else ()
            ),
            license_slot=None if link.license_slot_empty else "supplied",
        )
        for link in case.source_segment
    )
    receiver = tuple(
        ChainLink(
            link_id=link.link_id,
            segment=LinkStage.RECEIVER,
            link_type=link.link_type,
            source_descriptor=DESCRIPTORS[link.source_descriptor],
            target_descriptor=DESCRIPTORS[link.target_descriptor],
            status=LinkStatus(link.status),
            channel=(
                _channel_for(
                    case.case_id,
                    link.link_id,
                    DESCRIPTORS[link.source_descriptor].dim,
                )
                if link.channel_supplied
                else None
            ),
            transported_constraints=(),
            license_slot=None if link.license_slot_empty else "supplied",
        )
        for link in case.receiver_segment
    )
    return ReductionChain(source_segment=source, receiver_segment=receiver)


def _chain_context(case: ChainCase) -> ChainContext:
    """Return the data the interface conditions are read against."""
    first_receiver = case.receiver_segment[0]
    physical = DESCRIPTORS[first_receiver.source_descriptor]
    if case.case_id == "CHAIN-squashing-link-in-source-segment":
        physical = Q_DESCRIPTOR
    if case.case_id == "CHAIN-source-link-in-receiver-segment":
        physical = DESCRIPTORS["C^2 (physical receiver space)"]
    if case.case_id == "CHAIN-not-decided-C4-S3":
        physical = DESCRIPTORS["C^3 (physical receiver space)"]

    physical_povm = {
        label: _basis_projector(physical.dim, index)
        for index, label in enumerate(case.physical_alphabet)
    }
    if len(case.emitted_alphabet) == 3:
        emitted_povm = family_as_blocks(
            ONE_SECTOR_QUBIT,
            {
                "v0": P_Z0,
                "v1": scale(F(1, 2), P_Z1),
                "v2": scale(F(1, 2), P_Z1),
            },
        )
    else:
        emitted_povm = family_as_blocks(
            ONE_SECTOR_QUBIT,
            {
                label: _basis_projector(2, index)
                for index, label in enumerate(case.emitted_alphabet)
            },
        )
    # The wrong-direction case's frozen `gamma` column is written EMITTED ->
    # PHYSICAL, which is the direction (C2) forbids; it is passed through
    # unchanged so that (C2) sees exactly what the registry froze.
    gamma = dict(case.gamma)

    virtual_weights = {"x0": F(1, 2), "x1": F(1, 2)}
    specified_weights = (
        {"x0": F(3, 4), "x1": F(1, 4)}
        if case.case_id == "CHAIN-index-failure"
        else dict(virtual_weights)
    )
    virtual_states = {"x0": P_Z0, "x1": P_Z1}
    specified_states = (
        {"x0": P_X0, "x1": P_Z1}
        if case.case_id == "CHAIN-srcmap-failure"
        else {"x0": P_Z0, "x1": P_Z1}
    )
    return ChainContext(
        physical_descriptor=physical,
        physical_alphabet=case.physical_alphabet,
        physical_povm=physical_povm,
        target_descriptor=Q_DESCRIPTOR,
        emitted_alphabet=case.emitted_alphabet,
        emitted_povm=emitted_povm,
        gamma=gamma,
        # THERE IS NO `sector_projectors` in the context: (C3) reads the block
        # lists themselves and projectors would have no
        # subject (Definition ``def:chaincond`` (C3), "TYPING, HELD BY THE
        # EMITTED FORM AND NOT CHECKED").
        virtual_descriptor=DESCRIPTORS["A'' (a qubit)"],
        transmitted_descriptor=DESCRIPTORS["A' (a qubit)"],
        signal_alphabet=("x0", "x1"),
        virtual_weights=virtual_weights,
        specified_weights=specified_weights,
        virtual_states=virtual_states,
        specified_states=specified_states,
        link_index_sets={link.link_id: ("x0", "x1") for link in case.source_segment},
    )


@pytest.mark.parametrize("case", CHAIN_CASES, ids=lambda c: c.case_id)
def test_every_chain_condition_matches_the_frozen_verdict(case: ChainCase) -> None:
    report = check_chain(_build_chain(case), _chain_context(case))
    for condition, expected in case.verdicts:
        assert str(report.verdict(condition)) == expected, condition
    assert report.refuses is case.refuses
    assert report.failing_condition == case.failing_condition
    if case.named_assumption is None:
        assert report.named_assumption is None
    else:
        assert report.named_assumption is not None
        assert str(report.named_assumption) == case.named_assumption
    if case.refuses:
        assert report.refusal is not None
        assert case.failing_condition is not None
        # The reason is not `chain_condition_c1_failed` ...
        # `chain_condition_s4_failed`: spec/modules/protocol-compiler/interface.yaml
        # fixes ONE spelling of its own for this row,
        # `chain_interface_condition_failed`, and the machine keys of that file
        # are binding on the implementation. NO FROZEN VALUE MOVES -- `ChainCase`
        # carries no refusal-reason field and `failing_condition` is the frozen
        # datum, asserted above and again here -- and what the claims require is
        # asserted in both places it lives: the condition is
        # NAMED in the detail and carried as a datum on the report
        # (def:chaincond, "refused, naming the condition"; thm:chain-consumption (i)).
        assert str(report.refusal.reason) == "chain_interface_condition_failed"
        assert f"({case.failing_condition})" in report.refusal.detail
        assert report.failing_condition == case.failing_condition


def test_x1_is_never_the_failing_condition() -> None:
    """Theorem thm:chain-consumption (i): (X1) is not decided and no refusal may name it."""  # noqa: E501
    from certiqs_key.protocol_compiler import CHAIN_REFUSAL_REASONS

    assert "X1" not in CHAIN_REFUSAL_REASONS
    for case in CHAIN_CASES:
        report = check_chain(_build_chain(case), _chain_context(case))
        assert report.verdict("X1") is ConditionOutcome.HOLDS
        assert report.failing_condition != "X1"


def test_the_pullback_statistics_identity_at_two_named_states() -> None:
    """Eq. eq:pullbackstats of Theorem thm:chain-consumption (iii), on CHAIN-coarse-proper."""  # noqa: E501
    from certiqs_key.foundations.exact import add, conjugate_transpose

    physical_povm = {
        "w0": _basis_projector(3, 0),
        "w1": _basis_projector(3, 1),
        "w2": _basis_projector(3, 2),
    }
    emitted_povm = {"v0": P_Z0, "v1": P_Z1}
    fibres = {"v0": ("w0",), "v1": ("w1", "w2")}
    coherent = matrix(((0, 0, 0), (0, F(1, 2), F(1, 2)), (0, F(1, 2), F(1, 2))))
    states = {
        "diag(1/2, 1/4, 1/4)": (
            matrix(((F(1, 2), 0, 0), (0, F(1, 4), 0), (0, 0, F(1, 4)))),
            {"v0": F(1, 2), "v1": F(1, 2)},
        ),
        "projector onto (|1> + |2>)/sqrt2": (coherent, {"v0": F(0), "v1": F(1)}),
    }
    for state, expected in states.values():
        pushed = add(
            matmul(
                matmul(_COARSE_KRAUS[0], state), conjugate_transpose(_COARSE_KRAUS[0])
            ),
            matmul(
                matmul(_COARSE_KRAUS[1], state), conjugate_transpose(_COARSE_KRAUS[1])
            ),
        )
        for emitted, want in expected.items():
            left = trace(matmul(emitted_povm[emitted], pushed))
            right = sum(
                (trace(matmul(physical_povm[w], state)) for w in fibres[emitted]),
                Cx(F(0), F(0)),
            )
            assert left == right == Cx(want, F(0))


def test_the_srcmap_check_is_two_sided_on_data() -> None:
    """(S3) holds for the bit-flip companion of the frozen failing case."""
    case = next(c for c in CHAIN_CASES if c.case_id == "CHAIN-srcmap-failure")
    chain = _build_chain(case)
    link = chain.source_segment[0]
    passing = ReductionChain(
        source_segment=(ChainLink(**{**link.__dict__, "channel": _BITFLIP_KRAUS}),),
        receiver_segment=chain.receiver_segment,
    )
    context = _chain_context(case)
    passing_context = ChainContext(
        **{**context.__dict__, "specified_states": {"x0": P_Z1, "x1": P_Z0}}
    )
    report = check_chain(passing, passing_context)
    assert report.verdict("S3") is ConditionOutcome.HOLDS
    assert report.refuses is False


def test_the_band_a_chain_constructor_matches_the_frozen_record() -> None:
    from certiqs_key.protocol_compiler import band_a_chain

    case = next(c for c in CHAIN_CASES if c.case_id == "CHAIN-bandA")
    chain = band_a_chain(Q_DESCRIPTOR)
    assert chain.source_length == case.l_s == 0
    assert chain.receiver_length == case.l_r == 1
    link = chain.receiver_segment[0]
    frozen = case.receiver_segment[0]
    assert link.link_id == frozen.link_id
    assert str(link.status) == frozen.status
    assert link.channel_supplied is frozen.channel_supplied
    assert link.transported_constraints == ()
    assert link.license_slot_present is frozen.license_slot_present
    assert link.license_slot_empty is frozen.license_slot_empty
    report = check_chain(chain, _chain_context(case))
    for condition, expected in case.verdicts:
        assert str(report.verdict(condition)) == expected


def test_the_link_status_vocabulary_is_the_contracts_three() -> None:
    from certiqs_key.protocol_compiler import LINK_STATUS_VOCABULARY as implemented

    assert tuple(str(status) for status in implemented) == LINK_STATUS_VOCABULARY


# ---------------------------------------------------------------------------
#  Group PC-G -- the parts of PC9 that are predicates on data
# ---------------------------------------------------------------------------


def _comparison_declarations(
    case: FeasibleSetComparison,
) -> tuple[CandidateDeclaration, CandidateDeclaration]:
    """Return the trusted and untrusted declarations prop:conservative compares."""
    sectors = SectorStructure(
        labels=("s0",), dims=(case.q_dim,), block_kind=FIXTURE_BLOCK_KIND
    )
    trusted_entries = tuple(
        ConstraintEntry(
            operator=as_blocks(sectors, reg(operator)),
            relation={"succeq": Relation.GE, "preceq": Relation.LE, "=": Relation.EQ}[
                relation
            ],
            rhs=reg(trusted_rhs),
        )
        for operator, relation, trusted_rhs, _ in case.licensed_entries
    )
    untrusted_entries = tuple(
        ConstraintEntry(
            operator=as_blocks(sectors, reg(operator)),
            relation={"succeq": Relation.GE, "preceq": Relation.LE, "=": Relation.EQ}[
                relation
            ],
            rhs=untrusted_rhs,
        )
        for operator, relation, _, untrusted_rhs in case.licensed_entries
    )
    x_alphabet = tuple(f"x{i}" for i in range(case.alice_dim))
    v_alphabet = tuple(f"v{i}" for i in range(case.q_dim))
    common = {
        "alice_dim": case.alice_dim,
        "sectors": sectors,
        "alice_alphabet": x_alphabet,
        "alice_povm": {
            label: _basis_projector(case.alice_dim, i)
            for i, label in enumerate(x_alphabet)
        },
        "bob_alphabet": v_alphabet,
        "bob_povm": family_as_blocks(
            sectors,
            {
                label: _basis_projector(case.q_dim, i)
                for i, label in enumerate(v_alphabet)
            },
        ),
        "partition": default_party_partition(x_alphabet, v_alphabet),
        "announce_alice": dict.fromkeys(x_alphabet, "a"),
        "announce_bob": dict.fromkeys(v_alphabet, "b"),
        "alice_announcement_alphabet": ("a",),
        "bob_announcement_alphabet": ("b",),
        "acceptance_alphabet": ("c",),
        "accept_statistic": {("a", "b"): "c"},
        "key_map": dict.fromkeys(_all_pairs(x_alphabet, v_alphabet), 0),
        "key_alphabet": (0,),
        "key_holder": Party.ALICE,
    }
    assert case.tau_a is not None
    trusted = CandidateDeclaration(
        alice_marginal=reg(case.tau_a), constraint_list=trusted_entries, **common
    )
    untrusted = CandidateDeclaration(
        alice_marginal=None, constraint_list=untrusted_entries, **common
    )
    return trusted, untrusted


@pytest.mark.parametrize("case", FEASIBLE_SET_COMPARISONS, ids=lambda c: c.case_id)
def test_prop_conservative_pointwise(case: FeasibleSetComparison) -> None:
    from certiqs_key.foundations.exact import partial_trace_second
    from certiqs_key.protocol_compiler import constraint_value

    trusted, untrusted = _comparison_declarations(case)
    dense = reg(case.state)
    state = joint_as_blocks(trusted.sectors, case.alice_dim, dense)
    assert in_feasible_set(trusted, state) is case.in_trusted_set
    assert in_feasible_set(untrusted, state) is case.in_untrusted_set
    assert equal(
        partial_trace_second(dense, case.alice_dim, case.q_dim),
        reg(case.state_marginal),
    )
    for entry, expected in zip(
        trusted.constraint_list, case.trusted_values, strict=True
    ):
        assert equal(constraint_value(trusted, entry, state), reg(expected))  # type: ignore[arg-type]
    for entry, scalar in zip(
        untrusted.constraint_list, case.untrusted_values, strict=True
    ):
        assert constraint_value(untrusted, entry, state) == scalar


@pytest.mark.parametrize("case", DIMENSION_ONE_EQUALITIES, ids=lambda c: c.case_id)
def test_rem_da1_the_two_feasible_sets_coincide(case: DimensionOneEquality) -> None:
    from certiqs_key.foundations.exact import partial_trace_second

    sectors = SectorStructure(
        labels=("s0",), dims=(case.q_dim,), block_kind=FIXTURE_BLOCK_KIND
    )
    v_alphabet = tuple(f"v{i}" for i in range(case.q_dim))
    common = {
        "alice_dim": 1,
        "sectors": sectors,
        "alice_alphabet": ("x0",),
        "alice_povm": {"x0": matrix(((1,),))},
        "bob_alphabet": v_alphabet,
        "bob_povm": family_as_blocks(
            sectors,
            {
                label: _basis_projector(case.q_dim, i)
                for i, label in enumerate(v_alphabet)
            },
        ),
        "partition": default_party_partition(("x0",), v_alphabet),
        "announce_alice": {"x0": "a"},
        "announce_bob": dict.fromkeys(v_alphabet, "b"),
        "alice_announcement_alphabet": ("a",),
        "bob_announcement_alphabet": ("b",),
        "acceptance_alphabet": ("c",),
        "accept_statistic": {("a", "b"): "c"},
        "key_map": dict.fromkeys(_all_pairs(("x0",), v_alphabet), 0),
        "key_alphabet": (0,),
        "key_holder": Party.ALICE,
    }
    trusted = CandidateDeclaration(alice_marginal=reg(case.tau_a), **common)
    untrusted = CandidateDeclaration(alice_marginal=None, **common)
    dense = reg(case.state)
    state = joint_as_blocks(sectors, 1, dense)
    marginal = partial_trace_second(dense, 1, case.q_dim)
    assert equal(marginal, reg(case.marginal))
    assert (marginal == reg(case.tau_a)) is case.marginal_equals_tau
    assert (trace(dense) == Cx(F(1), F(0))) is case.trace_is_one
    assert trace(dense) == Cx(case.trace, F(0))
    assert in_feasible_set(trusted, state) is case.in_trusted_set
    assert in_feasible_set(untrusted, state) is case.in_untrusted_set
    # THE EQUALITY: the two verdicts coincide at d_A = 1.
    assert case.in_trusted_set == case.in_untrusted_set


# ---------------------------------------------------------------------------
#  Group PC-H -- the source-replacement certificate (PC10, PC11)
# ---------------------------------------------------------------------------


def _certificate(case: CertificateCase) -> SourceReplacementCertificate:
    """Return the certificate one frozen case presents."""
    dim = case.alice_dim * case.virtual_dim
    amplitudes = [0] * dim
    for label, amplitude in case.psi_integer_amplitudes:
        index = int(label[1:-1], 2)
        amplitudes[index] = amplitude
    labels = tuple(label for label, _ in case.povm)
    return SourceReplacementCertificate(
        alice_marginal=reg(case.tau_a),
        # THE FROZEN CASE PRESENTS AN UNNORMALIZED INTEGER AMPLITUDE VECTOR
        # WITH ITS SQUARED NORM, which is exactly the presentation 0.3.0's type
        # change removed (SUPERSEDED_BY_SCOPE_0_3_0, CERTIFICATE_CASES). The
        # OPERATOR it denotes is |psi><psi| / N, and the case's (SR1)/(SR2)
        # verdicts are RESTORED_AT_0_3_0 -- "functions of Psi and UNCHANGED" --
        # so they are read against the operator here and NOT re-derived.
        psi=outer_projector(vector(amplitudes), F(case.psi_squared_norm)),
        virtual_dim=case.virtual_dim,
        virtual_weights=dict(zip(labels, case.virtual_weights, strict=True)),
        virtual_states=dict(
            zip(labels, (reg(state) for state in case.virtual_states), strict=True)
        ),
    )


@pytest.mark.parametrize("case", CERTIFICATE_CASES, ids=lambda c: c.case_id)
def test_sr1_and_sr2_reproduce_the_frozen_values(case: CertificateCase) -> None:
    certificate = _certificate(case)
    labels = tuple(label for label, _ in case.povm)
    povm = {label: reg(element) for label, element in case.povm}

    holds, computed = check_sr1(certificate)
    assert holds is case.sr1_holds
    assert equal(computed, reg(case.sr1_computed))

    sr2_holds, values, expected = check_sr2(certificate, labels, povm)
    assert sr2_holds is case.sr2_holds
    for label, want in zip(labels, case.sr2_computed, strict=True):
        assert equal(values[label], reg(want))
    for label in labels:
        assert equal(
            expected[label],
            scale(
                certificate.virtual_weights[label], certificate.virtual_states[label]
            ),
        )


def test_the_checker_accepts_the_canonical_and_the_non_canonical_shape() -> None:
    """Corollary cor:noncanonical: no code path tests canonicity."""
    from certiqs_key.transmitter import verify_certificate

    for case in CERTIFICATE_CASES:
        if not (case.sr1_holds and case.sr2_holds):
            continue
        certificate = _certificate(case)
        labels = tuple(label for label, _ in case.povm)
        povm = {label: reg(element) for label, element in case.povm}
        verification = verify_certificate(certificate, labels, povm)
        # THE FROZEN (SR1)/(SR2) VERDICTS STAND AND ARE ASSERTED AS FROZEN --
        # `RESTORED_AT_0_3_0`: they "are read at 0.3.0 EXACTLY AS AT 0.1.4 --
        # as EXACT MATRIX IDENTITIES on declared data, decided entry by entry",
        # and only their PRESENTATION is superseded.
        assert verification.sr1_holds is True
        assert verification.sr2_holds is True
        # THE THREE PURITY CONDITIONS ON Psi ARE NEW AT 0.3.0 and are decided
        # INDEPENDENTLY (Definition def:eligible (G2)). The rank-one projector
        # conditions hold of every frozen Psi; `tr Psi = 1 ROUNDING NOWHERE` is
        # the condition with no 0.1.4 counterpart, and a fixture whose entries
        # are not binary64 numbers fails it -- which is fail-closed and is the
        # number model doing its work, not a defect in the frozen value.
        assert verification.purity.hermitian is True
        assert verification.purity.idempotent is True
        assert verification.purity.trace_is_one is True
        assert verification.purity.trace_rounds_nowhere is _psi_is_binary64(
            certificate.psi
        )
        assert verification.passes is verification.purity.trace_rounds_nowhere
    shapes = {case.canonical_form for case in CERTIFICATE_CASES if case.sr2_holds}
    assert shapes == {True, False}


def _psi_is_binary64(psi: Matrix) -> bool:
    """Whether every entry of a frozen Psi is a binary64 number.

    Section 2.5 (``number_model``): "a declared value IS its binary64 datum, a
    dyadic rational, and there is NO EXACT OBJECT BEHIND IT of which the float
    is an approximation." Two of the four frozen certificates carry entries on
    a denominator of 625, which no binary64 number equals; those fixtures are
    correct evidence written against the 0.1.3 text, and the number model
    0.3.0 states is what puts them out of the declarable range rather than any
    change to their (SR1)/(SR2) content.
    """
    from certiqs_key.foundations.exact import matrix_is_binary64

    return matrix_is_binary64(psi)


@pytest.mark.parametrize("case", CONSISTENCY_CRITERION_CASES, ids=lambda c: c.case_id)
def test_the_thm_pc11_ii_criterion_and_its_identity(
    case: ConsistencyCriterionCase,
) -> None:
    tau = reg(case.tau_a)
    alice_dim = len(tau)
    labels = tuple(f"x{i}" for i in range(len(case.family)))
    povm = dict(zip(labels, (reg(element) for element in case.family), strict=True))
    if case.case_id == "CONS-nonpovm-holds":
        amplitudes = vector([1, 0, 0, 0])
        norm = F(1)
        weights = {"x0": F(1), "x1": F(0)}
        states = {"x0": P_Z0, "x1": P_Z0}
    else:
        amplitudes = vector([1, 0, 0, 1])
        norm = F(2)
        weights = {label: F(1, 2) for label in labels}
        states = {"x0": P_Z0, "x1": P_Z1}
    certificate = SourceReplacementCertificate(
        alice_marginal=tau,
        psi=outer_projector(amplitudes, norm),
        virtual_dim=2,
        virtual_weights={label: weights[label] for label in labels},
        virtual_states={label: states[label] for label in labels},
    )
    criterion = consistency_criterion(certificate, labels, povm)
    assert equal(criterion.support_projector, reg(case.pi_s))
    assert equal(criterion.family_sum, reg(case.family_sum))
    assert equal(criterion.projected_sum, reg(case.projected_sum))
    assert criterion.criterion_holds is case.criterion_holds
    assert equal(criterion.average_virtual_state, reg(case.average_virtual_state))
    assert equal(criterion.psi_signal_marginal, reg(case.psi_signal_marginal))
    assert criterion.identity_holds is case.identity_holds
    # The criterion IS the identity: thm:certificate-sufficiency (ii) is an equivalence.
    assert criterion.criterion_holds is criterion.identity_holds
    assert alice_dim == 2


def test_sr3_is_presence_only_and_is_never_asserted() -> None:
    from certiqs_key.foundations.errors import HypothesisError
    from certiqs_key.transmitter import RetentionAttestation

    supplied = RetentionAttestation(attested_by="the supplier", statement="A retained")
    with_attestation = SourceReplacementLicense(
        sr1_holds=True, sr2_holds=True, retention_attestation=supplied
    )
    without = SourceReplacementLicense(
        sr1_holds=True, sr2_holds=True, retention_attestation=None
    )
    for description, is_supplied, _emitted, asserted, _note in SR3_RECORD:
        assert asserted is False
        record = with_attestation if is_supplied else without
        assert record.attestation_supplied is is_supplied, description
        assert record.asserted_by_this_module is False
        assert record.as_machine_record()["sr3_asserted_by_this_module"] is False
    with pytest.raises(HypothesisError):
        SourceReplacementLicense(
            sr1_holds=True,
            sr2_holds=True,
            retention_attestation=supplied,
            asserted_by_this_module=True,
        )


def test_the_outcome_distribution_rem_xreg_is_stated_on() -> None:
    """O-PC-SR-BOUNDARY: the measured distribution, and the refutation."""
    from certiqs_key.transmitter import alice_outcome_distribution

    case = next(
        c for c in CERTIFICATE_CASES if c.case_id == "CERT-canonical-with-shield"
    )
    certificate = _certificate(case)
    labels = tuple(label for label, _ in case.povm)
    povm = {label: reg(element) for label, element in case.povm}
    distribution = alice_outcome_distribution(certificate, labels, povm)
    assert tuple(distribution[label] for label in labels) == (F(9, 25), F(16, 25))
    assert sum(distribution.values()) == 1

    # Remark rem:xreg: one OVERWRITING channel gives the point distribution,
    # and the two differ -- which refutes a commutation asserted for EVERY
    # channel. The symmetric instance of the remark is p = (1/2, 1/2).
    symmetric = next(c for c in CERTIFICATE_CASES if c.case_id == "CERT-sr1-fails")
    symmetric_certificate = _certificate(symmetric)
    symmetric_labels = tuple(label for label, _ in symmetric.povm)
    measured = alice_outcome_distribution(
        symmetric_certificate,
        symmetric_labels,
        {label: reg(element) for label, element in symmetric.povm},
    )
    assert tuple(measured[label] for label in symmetric_labels) == (F(1, 2), F(1, 2))
    overwritten = (F(1), F(0))
    assert tuple(measured[label] for label in symmetric_labels) != overwritten


# ---------------------------------------------------------------------------
#  Group PC-I -- the BB84 instance's candidate-side consequences (PC12)
# ---------------------------------------------------------------------------

BB84_X = dict(BB84_ALPHABETS)["X"]
BB84_V = dict(BB84_ALPHABETS)["V"]
BB84_CA = dict(BB84_ALPHABETS)["C_A"]
BB84_CHAT = dict(BB84_ALPHABETS)["Chat"]


def _bb84_announce(label: str) -> str:
    basis, outcome = label[1:-1].split(",")
    return "Z" if basis == "Z" else f"(X,{outcome})"


def _bb84_declaration(case: BB84Case) -> CandidateDeclaration:
    """Return the BB84 candidate, built from the FROZEN emitted matrices."""
    alice_povm = dict(zip(BB84_X, (reg(m) for m in case.alice_povm), strict=True))
    bob_povm = family_as_blocks(
        ONE_SECTOR_QUBIT,
        dict(zip(BB84_V, (reg(m) for m in case.bob_povm), strict=True)),
    )
    return CandidateDeclaration(
        alice_dim=2,
        alice_marginal=reg(case.tau_a),
        sectors=ONE_SECTOR_QUBIT,
        alice_alphabet=BB84_X,
        alice_povm=alice_povm,
        bob_alphabet=BB84_V,
        bob_povm=bob_povm,
        partition=default_party_partition(BB84_X, BB84_V),
        announce_alice={label: _bb84_announce(label) for label in BB84_X},
        announce_bob={label: _bb84_announce(label) for label in BB84_V},
        alice_announcement_alphabet=BB84_CA,
        bob_announcement_alphabet=BB84_CA,
        acceptance_alphabet=BB84_CHAT,
        accept_statistic={(c_a, c_b): value for c_a, c_b, value in BB84_PHI},
        key_map={(x, v): value for x, v, value in BB84_KEY_MAP},  # type: ignore[misc]
        key_alphabet=(0, 1),
        key_holder=Party.ALICE,
    )


@pytest.mark.parametrize("case", BB84_CASES, ids=lambda c: c.case_id)
def test_the_bb84_statistics_and_certificate_at_every_weight_pair(
    case: BB84Case,
) -> None:
    declaration = _bb84_declaration(case)

    # D(i)-D(viii), through the soundness half of thm:validator-soundness (i).
    result = validate(declaration)
    if case.dyadic:
        assert result.passed is True
        assert all(holds for _, holds, _ in BB84_D_VERDICTS)
    else:
        # THE NON-DYADIC PRESENTATION IS NOT DECLARABLE AT 0.3.0, and the
        # module refuses it rather than admitting it within a margin. The
        # frozen matrices are the correct closed forms of Theorem thm:pc12 at
        # these weights and are NOT withdrawn -- every value below is still
        # asserted -- but Section 2.5 (`number_model`) has a declared value BE
        # its binary64 datum, and 2/3 is no binary64 number, so the emitted
        # completeness sum cannot be the identity. Remark ``rem:bb84checks``:
        # "The instance is then REFUSED RATHER THAN ADMITTED WITHIN A MARGIN,
        # and the remedy is to declare weights that satisfy it ... it is A
        # PROPERTY OF THE PRESENTATION AND NOT OF THE MATHEMATICS."
        assert result.passed is False
        assert result.refusing_checks[0] == "V3"

    # (SR1) and (SR2) on the frozen emitted family.
    weights = {
        label: (
            case.alice_weights[0] if label.startswith("(Z") else case.alice_weights[1]
        )
        / 2
        for label in BB84_X
    }
    states = dict(zip(BB84_X, (P_Z0, P_Z1, P_X0, P_X1), strict=True))
    certificate = SourceReplacementCertificate(
        alice_marginal=reg(case.tau_a),
        psi=outer_projector(vector([1, 0, 0, 1]), F(2)),
        virtual_dim=2,
        virtual_weights=weights,
        virtual_states=states,
    )
    holds, computed = check_sr1(certificate)
    assert holds is True
    assert equal(computed, reg(case.tau_a))
    sr2_holds, values, expected = check_sr2(certificate, BB84_X, declaration.alice_povm)
    assert sr2_holds is True
    for label, want, wanted_expected in zip(
        BB84_X, case.sr2_values, case.sr2_expected, strict=True
    ):
        assert equal(values[label], reg(want))
        assert equal(expected[label], reg(wanted_expected))

    # Eq. eq:bb84stats and the four-entry Phi vector.
    joint = joint_distribution(declaration, PHI_PLUS_PROJECTOR)
    for x, row in zip(BB84_X, case.joint, strict=True):
        for v, want_value in zip(BB84_V, row, strict=True):
            assert joint[(x, v)] == want_value
    statistics = phi_distribution(declaration, PHI_PLUS_PROJECTOR)
    assert tuple(statistics.values[value] for value in BB84_CHAT) == case.phi_vector
    assert statistics.total == case.phi_total == 1
    assert statistics.values["err"] == 0

    # Remark rem:bb84checks: the exactness check on BOTH sides.
    for index, basis in enumerate(("Z", "X")):
        bob_mass = sum(
            (joint[(x, v)] for x in BB84_X for v in BB84_V if v[1] == basis), F(0)
        )
        assert bob_mass == case.bob_basis_marginals[index]
        alice_mass = sum(
            (joint[(x, v)] for x in BB84_X for v in BB84_V if x[1] == basis), F(0)
        )
        assert alice_mass == case.alice_basis_marginals[index]


def test_the_bb84_key_map_is_eq_rdef_and_chat_key_is_a_singleton() -> None:
    classes = [(c_a, c_b) for c_a in BB84_CA for c_b in BB84_CA]
    public = PublicPart(
        partition=default_party_partition(BB84_X, BB84_V),
        announce_alice={label: _bb84_announce(label) for label in BB84_X},
        announce_bob={label: _bb84_announce(label) for label in BB84_V},
        alice_announcement_alphabet=BB84_CA,
        bob_announcement_alphabet=BB84_CA,
        sifting={
            kappa: (Sifting.PASS if kappa == ("Z", "Z") else Sifting.FAIL)
            for kappa in classes
        },
        key_rule={
            (label, kappa): int(label[1:-1].split(",")[1])
            for label in BB84_X
            for kappa in classes
        },
        holder=Party.ALICE,
        key_alphabet=(0, 1),
        acceptance_alphabet=BB84_CHAT,
        accept_statistic={(c_a, c_b): value for c_a, c_b, value in BB84_PHI},
    )
    built = raw_key_map(public, BB84_X, BB84_V)
    for x, v, expected in BB84_KEY_MAP:
        assert built[(x, v)] == expected
    key_live = {
        public.accept_statistic[kappa]
        for kappa in classes
        if public.sifting[kappa] is Sifting.PASS
    }
    assert key_live == {"gen"}


# ---------------------------------------------------------------------------
#  Group PC-J -- the conjugation branch pair (ex:conj)
# ---------------------------------------------------------------------------


def _conjugation_declaration(branch: ConjugationBranch) -> CandidateDeclaration:
    """Return the one-signal Y-basis candidate one branch emits."""
    emitted_zero = reg(branch.emitted_element)
    emitted_one = scale(F(1, 2), P_Y1 if branch.convention == "omitted" else P_Y0)
    alphabet = ("(Y,0)", "(Y,1)")
    bob_povm = family_as_blocks(
        ONE_SECTOR_QUBIT,
        {"(Y,0)": scale(F(1, 2), P_Y0), "(Y,1)": scale(F(1, 2), P_Y1)},
    )
    return CandidateDeclaration(
        alice_dim=2,
        alice_marginal=scale(F(1, 2), ID2),
        sectors=ONE_SECTOR_QUBIT,
        alice_alphabet=alphabet,
        alice_povm={"(Y,0)": emitted_zero, "(Y,1)": emitted_one},
        bob_alphabet=alphabet,
        bob_povm=bob_povm,
        partition=default_party_partition(alphabet, alphabet),
        announce_alice=dict.fromkeys(alphabet, "Y"),
        announce_bob=dict.fromkeys(alphabet, "Y"),
        alice_announcement_alphabet=("Y",),
        bob_announcement_alphabet=("Y",),
        acceptance_alphabet=("c",),
        accept_statistic={("Y", "Y"): "c"},
        key_map=dict.fromkeys(_all_pairs(alphabet, alphabet), 0),
        key_alphabet=(0,),
        key_holder=Party.ALICE,
    )


@pytest.mark.parametrize("branch", CONJUGATION_BRANCHES, ids=lambda b: b.branch_id)
def test_both_conjugation_branches(branch: ConjugationBranch) -> None:
    declaration = _conjugation_declaration(branch)
    certificate = SourceReplacementCertificate(
        alice_marginal=scale(F(1, 2), ID2),
        psi=outer_projector(vector([1, 0, 0, 1]), F(2)),
        virtual_dim=2,
        virtual_weights={"(Y,0)": F(1, 4)},
        virtual_states={"(Y,0)": P_Y0},
    )
    holds, computed, expected = check_sr2(
        certificate, ("(Y,0)",), {"(Y,0)": reg(branch.emitted_element)}
    )
    assert holds is branch.sr2_holds
    assert equal(computed["(Y,0)"], reg(branch.sr2_computed))
    assert equal(expected["(Y,0)"], reg(branch.sr2_expected))

    joint = joint_distribution(declaration, PHI_PLUS_PROJECTOR)
    for a, row in enumerate(branch.matched_basis_joint):
        for y, want in enumerate(row):
            assert joint[(f"(Y,{a})", f"(Y,{y})")] == want


def test_the_branch_pair_differs_where_the_bb84_instance_cannot() -> None:
    """Remark rem:bb84checks: the pair is the point, and BB84 collapses it."""
    contract_branch, omitted_branch = CONJUGATION_BRANCHES
    assert contract_branch.sr2_holds is not omitted_branch.sr2_holds
    assert contract_branch.matched_basis_joint != omitted_branch.matched_basis_joint
    # Every BB84 element is its own entrywise conjugate, so the branch pair
    # COLLAPSES there and a test built on it cannot fail.
    for case in BB84_CASES:
        for element in case.alice_povm:
            emitted = reg(element)
            conjugated = tuple(
                tuple(entry.conjugate() for entry in row) for row in emitted
            )
            assert equal(emitted, conjugated)


# ---------------------------------------------------------------------------
#  Group PC-K -- the interface vocabulary
# ---------------------------------------------------------------------------


def test_the_machine_key_vocabulary_is_the_contracts_own() -> None:
    from certiqs_key.protocol_compiler import (
        COMPILER_ONLY_KEYS as implemented_compiler_only,
    )
    from certiqs_key.protocol_compiler import DECLARATION_SLOT_KEYS as implemented_slots
    from certiqs_key.protocol_compiler import INPUT_KEYS as implemented_inputs
    from certiqs_key.protocol_compiler import NOT_OUTPUTS as implemented_not_outputs
    from certiqs_key.protocol_compiler import OUTPUT_KEYS as implemented_outputs

    # TWELVE/TWENTY-ONE AT 0.1.4, THIRTEEN/TWENTY-THREE AT 0.3.0. The frozen
    # tuples are read as SUBSETS IN THEIR FROZEN RELATIVE ORDER, which is what
    # `SUPERSEDED_BY_SCOPE_0_3_0` licenses: "NO EXISTING KEY IS REMOVED OR
    # RENAMED ... what is superseded is THE COUNT AND THE POSITION OF THE
    # INSERTIONS." The three additions are pinned BY NAME, which a count would
    # not catch.
    # FOUR FROZEN INPUT NAMES ARE OTHER MODULES', and the
    # relative-order reading holds of the rest. `alice_system`,
    # `alice_povm_spec` and `source_replacement_certificate` are read off
    # the TRANSMITTER ARTEFACT under the transmitter's own key names
    # (`def:spec` (a)), and `source_mode_request` is an input of THAT
    # module: a request is not an emission. The
    # frozen tuple is not edited, and the two rows that replace them --
    # `transmitter_artifact` and route C's `choice_weighting` -- are
    # pinned BY NAME, which a count would not catch.
    MOVED_TO_THE_TRANSMITTER = (
        "alice_system",
        "alice_povm_spec",
        "source_replacement_certificate",
        "source_mode_request",
    )
    carried = tuple(n for n in INPUT_KEYS if n not in MOVED_TO_THE_TRANSMITTER)
    assert set(carried) <= set(implemented_inputs)
    assert tuple(n for n in implemented_inputs if n in carried) == carried
    assert set(implemented_inputs) - set(carried) == {
        "target_povm",
        "transmitter_artifact",
        "choice_weighting",
    }
    assert len(implemented_inputs) == 11
    assert set(OUTPUT_KEYS) <= set(implemented_outputs)
    assert tuple(n for n in implemented_outputs if n in OUTPUT_KEYS) == OUTPUT_KEYS
    assert set(implemented_outputs) - set(OUTPUT_KEYS) == {
        "sector_block_kind",
        "constraint_rhs_tag",
    }
    assert len(implemented_outputs) == 23
    # THE SIX COMPILER-ONLY KEYS ARE UNCHANGED: both additions are declaration
    # SLOTS, each a component of the emitted declaration the consumer reads.
    assert implemented_compiler_only == COMPILER_ONLY_KEYS
    assert len(implemented_compiler_only) == 6
    assert set(DECLARATION_SLOT_KEYS) <= set(implemented_slots)
    assert len(implemented_slots) == 17
    assert tuple(name for name, _ in implemented_not_outputs) == tuple(
        name for name, _ in NOT_OUTPUTS
    )
    assert implemented_not_outputs[0][1] == NOT_OUTPUTS[0][1]


def test_the_two_verbatim_reasons_and_the_gate_vocabulary() -> None:
    from certiqs_key.protocol_compiler import REFUSAL_REASONS_VERBATIM as implemented

    # TWO STRINGS AT 0.1.4, SEVEN AT 0.3.0. The frozen tuple is not withdrawn
    # and both of its strings remain contract-verbatim -- what is superseded is
    # reading it as a COMPLETE list (`SUPERSEDED_BY_SCOPE_0_3_0`,
    # REFUSAL_REASONS_VERBATIM). Section 2.3 (`refusal`) fixes five more by
    # name, and they are asserted here against the contract's own sentence.
    spellings = tuple(str(reason) for reason in implemented)
    assert spellings[: len(REFUSAL_REASONS_VERBATIM)] == REFUSAL_REASONS_VERBATIM
    assert spellings == (
        "fixed_fraction_requested",
        "no_feasibility_witness",
        "sector_map_mismatch",
        "alice_marginal_trace_rounds",
        "alice_povm_summation_rounds",
        "bob_povm_summation_rounds",
        "emitted_value_not_representable",
    )
    assert tuple(str(verdict) for verdict in GateVerdict) == GATE_VERDICT_VOCABULARY
    assert len(GATE_VERDICT_VOCABULARY) == 3


def test_the_declaration_slots_do_not_include_the_two_not_outputs() -> None:
    from certiqs_key.protocol_compiler import DECLARATION_SLOT_KEYS as implemented_slots

    for name, _owner in NOT_OUTPUTS:
        assert name not in implemented_slots
        assert name not in OUTPUT_KEYS
    record = _mini(constraint_list=(MINI_ENTRY,)).as_machine_record()
    for name, _owner in NOT_OUTPUTS:
        assert name not in record


# ---------------------------------------------------------------------------
#  Group PC-L -- the assumption ledger and the never-verified set
# ---------------------------------------------------------------------------


#: THE FOUR FROZEN LEDGER ROWS THIS MODULE DOES NOT OWN, and the module
#: each belongs to. SHORT IDS AND MACHINE
#: KEYS ARE REPOSITORY-WIDE, so an assumption another module already states
#: is ASSUMED FROM THERE: A-SEQ, A-ENS and A-RET (merged into A-SRC under
#: the same key) are the transmitter's, A-RECV is reductions'. WHAT EACH
#: ROW SAYS IS UNCHANGED and the frozen rows are not edited; what changed
#: is which module's claim file states it, and the run manifest assembles
#: the closure from the supplier artefacts (spec/architecture.md 4.4).
INHERITED_FROM_ANOTHER_MODULE = {
    "A-SEQ": "transmitter",
    "A-ENS": "transmitter",
    "A-RET": "transmitter (as A-SRC)",
    "A-RECV": "reductions",
}

#: THE FROZEN ROWS WHOSE MACHINE KEY DIFFERS, and why each has to. The
#: frozen A-RHOM carries `round_homogeneity`; `receiver` owns that
#: key for its own A-ROUND and keys are repository-wide, so this module's
#: became `round_homogeneity_declaration`, as `reductions` renamed its own
#: to `round_homogeneity_squashing` for the same reason. THE STATEMENT IS
#: UNCHANGED. The conditions the compiler decides are in
#: `def:well-formed-spec`; what A-SPEC asserts is that the
#: declared data describe the apparatus, and its key says so. The frozen row
#: is not edited; this map is the whole difference.
RENAMED_KEYS = {
    "A-RHOM": "round_homogeneity_declaration",
    "A-SPEC": "specification_describes_apparatus",
}
# The licence id: A-LIC in the frozen ledger, A-ATK in the code, where the
# compiler's A-LIC and the engine's A-ATK are one claim file under the
# engine's id; same key.
MERGED_IDS = {"A-LIC": "A-ATK"}


@pytest.mark.parametrize("row", LEDGER_ROWS, ids=lambda r: r.assumption_id)
def test_every_ledger_row_has_its_identifier_and_machine_key(row: LedgerRow) -> None:
    if row.assumption_id in INHERITED_FROM_ANOTHER_MODULE:
        with pytest.raises(ValueError, match="not a valid AssumptionId"):
            AssumptionId(row.assumption_id)
        return
    identifier = AssumptionId(MERGED_IDS.get(row.assumption_id, row.assumption_id))
    expected = RENAMED_KEYS.get(row.assumption_id, row.machine_key)
    assert ASSUMPTION_MACHINE_KEYS[identifier] == expected
    assert (row.assumption_id in NEVER_VERIFIED) is row.never_verified


def test_the_never_verified_set_is_two_own_rows_and_two_inherited() -> None:
    """Two never-verified rows here, two elsewhere, and A-BLOCK in neither.

    THE FROZEN FOUR ARE FOUR AND ARE NEVER VERIFIED; two of them are other
    modules' assumptions -- A-RET is the transmitter's A-SRC and A-RECV is
    reductions' -- so this module names them by MACHINE KEY rather than as
    members of its own enum.

    The registry's own scope mark still applies to the frozen ten-row ledger:
    "what is superseded is reading it as complete".

    The frozen four are never verified, and the code's sets are the frozen
    ones plus the rows whose ``verification`` field is ``never`` (the
    comments below list them): seven own rows and five inherited. A-PRESENT is
    in def:well-formed-spec (iv), which the compiler decides.
    """
    from certiqs_key.protocol_compiler import INHERITED_NEVER_VERIFIED_KEYS
    from certiqs_key.protocol_compiler import NEVER_VERIFIED as implemented

    own = tuple(str(entry) for entry in implemented)
    # The licence id is A-ATK: the compiler's A-LIC and the engine's A-ATK are
    # one claim file under the engine's id; the frozen registry keeps A-LIC,
    # and the mapping below is the whole difference.
    # FROZEN UNION ADDED. The
    # fields of A-SPEC, A-RHOM, A-COIN and A-IDEAL are `never`
    # (spec/claim-format.md section 3.2), so the own set is the frozen pair
    # plus those four, in the ledger's order. The frozen ten rows are not
    # edited.
    # A-SPEC's split part A-ALICE-MEAS is an own row the frozen ledger
    # does not name, `never` like A-SPEC, and follows it in the ledger's
    # order. A-PRESENT is in def:well-formed-spec (iv) and
    # req:physical-family-decision, decided on every route.
    added_own = {"A-SPEC", "A-ALICE-MEAS", "A-RHOM", "A-COIN", "A-IDEAL"}
    assert own == (
        "A-SPEC",
        "A-ALICE-MEAS",
        "A-RHOM",
        "A-COIN",
        "A-LINK",
        "A-ATK",
        "A-IDEAL",
    )
    # EVERY FROZEN NEVER-VERIFIED ROW IS STILL NEVER VERIFIED, here or in the
    # module that owns it.
    frozen_never = {row.assumption_id for row in LEDGER_ROWS if row.never_verified}
    assert frozen_never == set(NEVER_VERIFIED)
    inherited_keys = {
        row.machine_key
        for row in LEDGER_ROWS
        if row.never_verified and row.assumption_id in INHERITED_FROM_ANOTHER_MODULE
    }
    # FROZEN UNION ADDED. The transmitter's A-ENS (ass:ens) and A-SEQ and the
    # decoy submodule's A-WCP (ass:wcp; a key the frozen ledger predates)
    # carry `verification: never`, and an inherited row carries its owner's
    # mark.
    added_inherited = {"source_ensemble", "sequential_round_model", "wcp_source_model"}
    # A-RECV, frozen as an inherited row, is no row of this module's ledger on
    # any route (interface.yaml, assumption_ledger.a_recv_not_emitted_note):
    # the row is the reductions artefact's own, emitted or omitted there
    # (reductions/req:recv-row-provenance), and it stays never verified in
    # reductions, its owner. The frozen row is not edited.
    dropped_inherited = {"receiver_artifact_accepted"}
    assert (inherited_keys - dropped_inherited) | added_inherited == set(
        INHERITED_NEVER_VERIFIED_KEYS
    )
    assert {MERGED_IDS.get(i, i) for i in own} - added_own | {
        MERGED_IDS.get(row.assumption_id, row.assumption_id)
        for row in LEDGER_ROWS
        if row.never_verified and row.assumption_id in INHERITED_FROM_ANOTHER_MODULE
    } == {MERGED_IDS.get(i, i) for i in NEVER_VERIFIED}
    # The frozen tuple still has its ten rows, and every one of them still
    # matches the code -- that pairing is asserted row by row above.
    assert len(LEDGER_ROWS) == 10
    # And the code carries the rows no frozen row names: A-SPEC's split part
    # A-ALICE-MEAS (its other part, A-PRESENT, is in def:well-formed-spec (iv)
    # and has no key). A-BLOCK, the consumer obligation, is the
    # remark rem:block-restriction, which meat-core/thm:reduction, step 1,
    # proves, and has no key.
    assert "block_diagonal_feasible_set" not in ASSUMPTION_MACHINE_KEYS.values()
    assert "presented_receiver_family" not in ASSUMPTION_MACHINE_KEYS.values()
    frozen = {
        MERGED_IDS.get(row.assumption_id, row.assumption_id) for row in LEDGER_ROWS
    }
    assert {str(k) for k in ASSUMPTION_MACHINE_KEYS} - frozen == {
        "A-ALICE-MEAS",
    }
