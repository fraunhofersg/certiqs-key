"""The BB84 instance and the Y-basis conjugation example, as named constructors.

Both are Band-A specifications (protocol-compiler Definition ``def:banda``,
Theorem ``thm:band-a``) whose source is presented by source replacement; that
Alice's declared conditional POVMs carry the complex conjugate of her signal
states is the transposition of transmitter Lemma ``lem:ensemble-presentation``
(``N_x = (sigma_x)^T``).

WHY THE Y-BASIS EXAMPLE IS A FIRST-CLASS CONSTRUCTOR AND NOT A TEST FIXTURE
===========================================================================
One fact about the BB84 signal set is the reason this module has two
constructors instead of one:

    ALL FOUR BB84 SIGNAL STATES HAVE REAL COEFFICIENTS in the declared
    computational basis, so ``conj(a^b) = a^b`` and THE CONJUGATION IS THE
    IDENTITY ON THIS SIGNAL SET: emitting ``M = p^A_b |a^b><a^b|`` in place of
    ``p^A_b |conj(a^b)><conj(a^b)|`` CHANGES ``P_D[omega]`` AT NO STATE, IN NO
    BASIS. A reversed convention is exactly as silent here as anywhere else,
    and A REGRESSION TEST BUILT ON THIS INSTANCE TO CATCH IT CANNOT FAIL. The
    case that does exercise ``conjugation_basis`` needs a signal with a
    genuinely complex amplitude in the declared basis; the Y-basis example
    computes one and IS THE CASE AN IMPLEMENTER SHOULD ENCODE.

So :func:`bb84_specification` cannot defend the ``conjugation_basis``
convention -- no test built on it can -- and
:func:`conjugation_example_specification` is the only thing that can. It
belongs in the package for the same reason the convention does: it is where the
correctness of the emitted ``{M_x}`` is observable, and a defence that lives
only in a test fixture is a defence that moves when the fixture does.

THE WRONG BRANCH IS NAMED, NOT HIDDEN
=====================================
:class:`ConjugationConvention` has two members and the second one,
``OMITTED``, builds the DEFECT the Y-basis example exhibits: the emitted
element without the bar, which "describes a source that SENDS ``|1^Y>``
WHENEVER THE SPECIFICATION SAYS ``|0^Y>``". It exists so that the regression
test can discriminate, and it is not a conforming emission: compiled at
``d_A = 2`` it FAILS (SR2), so gate (G2) refuses it under Table
``tab:gateoutcome`` row 3. That refusal is the end-to-end demonstration, and it
is why the defect is safe to name here -- the pipeline rejects it rather than
emitting it.

WHERE THE CONJUGATION HAPPENS
=============================
In the SPECIFICATION, not in the compilation map. Definition ``def:spec`` (a)
types Alice's family as a declared POVM "itself possibly presented as a
choice-weighted family", and the BB84 instance's emitted family is Lemma
``lem:weighted`` (i) applied with choice alphabet ``{Z, X}``, weights
``p^A_b`` and the conditional projective measurements
``{|conj(a^b)><conj(a^b)|}_a``. So the conditional POVMs a Band-A instance
DECLARES already carry the bar, and Definition ``def:compile`` only multiplies
the weight in. :func:`conjugate_projector` (in
:mod:`instances.common.conjugation`, re-exported here) is the one place the
bar is applied.
"""

from __future__ import annotations

from enum import StrEnum
from fractions import Fraction
from functools import cache
from typing import TYPE_CHECKING

from certiqs_key.foundations.blocks import BlockOperator
from certiqs_key.foundations.errors import MalformedInputError
from certiqs_key.foundations.exact import Cx, Matrix, matrix, round_to_binary64, scale
from certiqs_key.protocol_compiler.chain import (
    ChainLink,
    LinkStage,
    LinkStatus,
    ReductionChain,
    Side,
    SystemDescriptor,
    identity_channel,
)

if TYPE_CHECKING:  # pragma: no cover - NumPy stays off this import path
    from certiqs_key.foundations.blocks import BlockKind
from certiqs_key.foundations.blocks import Label, SectorStructure
from certiqs_key.protocol_compiler.spec import (
    Party,
    ProtocolSpecification,
    PublicChoices,
    PublicPart,
    ReceiverPart,
    Sifting,
    SourcePart,
    SpecConstraints,
    default_party_partition,
)
from certiqs_key.protocol_compiler.weights import weighted_family
from certiqs_key.transmitter.artifact import TransmitterArtifact
from certiqs_key.transmitter.certificate import (
    SourceReplacementCertificate,
    SourceReplacementLicense,
    verify_certificate,
)
from instances.common.conjugation import conjugate_projector

__all__ = [
    "BB84_ACCEPTANCE_ALPHABET",
    "P_X0",
    "P_X1",
    "P_Y0",
    "P_Y1",
    "P_Z0",
    "P_Z1",
    "ConjugationConvention",
    "bb84_specification",
    "conjugate_projector",
    "conjugation_example_specification",
]

#: The four BB84 signal projectors in the declared computational basis. Every
#: one is REAL, so conjugation is the identity on them (module docstring).
P_Z0: Matrix = matrix(((1, 0), (0, 0)))
P_Z1: Matrix = matrix(((0, 0), (0, 1)))
P_X0: Matrix = matrix(
    ((Fraction(1, 2), Fraction(1, 2)), (Fraction(1, 2), Fraction(1, 2)))
)
P_X1: Matrix = matrix(
    ((Fraction(1, 2), Fraction(-1, 2)), (Fraction(-1, 2), Fraction(1, 2)))
)

#: The two Y-basis projectors. THE ONLY GENUINELY COMPLEX OBJECTS IN THIS
#: PACKAGE'S INSTANCES, and the reason the Y-basis example exists:
#: ``|0^Y> = (|0> + i|1>)/sqrt2`` and ``|1^Y> = (|0> - i|1>)/sqrt2``.
P_Y0: Matrix = (
    (Cx(Fraction(1, 2), Fraction(0)), Cx(Fraction(0), Fraction(-1, 2))),
    (Cx(Fraction(0), Fraction(1, 2)), Cx(Fraction(1, 2), Fraction(0))),
)
P_Y1: Matrix = (
    (Cx(Fraction(1, 2), Fraction(0)), Cx(Fraction(0), Fraction(1, 2))),
    (Cx(Fraction(0), Fraction(-1, 2)), Cx(Fraction(1, 2), Fraction(0))),
)

#: ``Psi = |Phi+><Phi+|`` on ``A A''`` in the declared computational basis with
#: ``A`` first: the 4x4 matrix with ``1/2`` at (0,0), (0,3), (3,0), (3,3) and
#: ``0`` elsewhere: the source-replacement certificate of both constructors.
_HALF = Cx(Fraction(1, 2), Fraction(0))
_PHI_PLUS: Matrix = matrix(
    (
        (Fraction(1, 2), 0, 0, Fraction(1, 2)),
        (0, 0, 0, 0),
        (0, 0, 0, 0),
        (Fraction(1, 2), 0, 0, Fraction(1, 2)),
    )
)

#: The four acceptance values of the Band-A instance (Eq. ``eq:bb84phi``).
BB84_ACCEPTANCE_ALPHABET: tuple[Label, ...] = ("gen", "ok", "err", "disc")


#: The block kind the Band-A sector map carries: ``proof_sector``.
#:
#: OPEN CHOICE ``OC-sector-block-kind``, NARROWED AND NOT DECIDED --
#: narrowed WITHIN the shared format's frozen alphabet
#: (:class:`~certiqs_key.foundations.blocks.BlockKind`, spec/architecture.md 2.9, a
#: frozen type of the shared format). The claims name the datum; the
#: format fixes the values; neither fixes WHICH value a given map is, and this
#: line records the reading rather than deciding the question.
#:
#: WHY ``proof_sector`` AND NOT THE OTHER TWO, in that section's own words:
#:   * ``physical_sector`` is "for example photon number or a classical device
#:     mode", and Definition ``def:banda`` (a) declares the receiver POVM
#:     "directly on a finite-dimensional system, WITH NO CHARACTERIZATION STEP
#:     AND NO PHOTON-NUMBER STRUCTURE" -- so there is no physical structure
#:     here for an identifier to name;
#:   * ``numerical_block`` is "sparsity exploited BY A SOLVER INSIDE ONE
#:     OPERATOR", which is a solver's business and not a declared component of
#:     an emitted declaration at all;
#:   * ``proof_sector`` is "a direct-sum decomposition JUSTIFIED BY DEPHASING
#:     OR SOURCE REPLACEMENT", and this instance's declaration is the
#:     source-replacement one -- its certificate is ``Psi`` above. Band A's
#:     singleton ``S = {s_0}`` with ``Pi_{s_0} = 1_Q`` is the trivial such
#:     decomposition, and a trivial proof sector is still a proof sector.
#:
#: IT ALSO AGREES WITH WHAT THE WIRE ALREADY WRITES: the operator-bundle writer
#: stamps ``block_kind: proof_sector`` on exactly these operators -- the
#: declaration's ``bob_povm`` elements and its constraint operators
#: (the run-tier wire record) --
#: so the module and the format name the same
#: decomposition the same way, which is the point of taking the alphabet from
#: the format instead of inventing one here.
#: THE ACCESSOR IS A FUNCTION AND THE VALUE IS CACHED, WHICH IS AN IMPORT-PATH
#: DECISION AND NOT A MATHEMATICAL ONE. ``BlockKind`` is frozen in
#: :mod:`certiqs_key.foundations.blocks`, which imports NumPy at module scope, and this
#: package "must run without NumPy ... on its import path"
#: (:mod:`certiqs_key.foundations.exact`, reason 2) -- an invariant
#: ``tests/unit/test_protocol_emission.py`` pins. A module-scope constant here
#: would pull NumPy into every ``import protocol_compiler``; a cached function
#: pulls it on first use instead, and the value is the same object either way.
@cache
def band_a_block_kind() -> BlockKind:
    """Return the block kind the Band-A sector map carries: ``proof_sector``.

    OPEN CHOICE ``OC-sector-block-kind``, NARROWED AND NOT DECIDED -- and the
    distinction is the whole reason this docstring is longer than one line
    (the implementer role file: a narrowed open choice is NAMED AS SUCH at
    the site). ``interface.yaml`` records the choice with ``decided: false``
    and states its scope exactly: what the contract FIXES is that a sector map
    has a block kind, that the kind is one of the map's three components, that
    it is emitted as a machine key of this module, and that check V1 compares
    it for equality -- a disagreement being ``sector_map_mismatch``. What the
    contract does NOT fix is "which kinds exist, what any of them is called, or
    how one is encoded". It never enumerates them and no claim quantifies over
    them.

    WHAT NARROWED IT. The
    vocabulary is the SHARED FORMAT'S -- ``certiqs_key.foundations.blocks.BlockKind``,
    a frozen type of spec/architecture.md 2.9 -- and THE
    INSTANCE DECLARES WHICH MEMBER. That is what makes the return type a
    ``BlockKind`` rather than a free string, and a free string here was itself
    the defect it corrected. So the OPEN part of the choice is not resolved by
    this function: the contract still enumerates no kinds, and this function
    exercises the instance's half rather than deciding the
    module's.

    WHY ``proof_sector`` AND NOT THE OTHER TWO is argued in full at the module
    constant above; the short form is that Band A's declaration is the
    source-replacement one and its singleton ``S = {s_0}`` with
    ``Pi_{s_0} = 1_Q`` is the trivial such decomposition.
    """
    from certiqs_key.foundations.blocks import BlockKind

    return BlockKind.PROOF_SECTOR


@cache
def _qubit() -> SectorStructure:
    """Return the Band-A sector map: one proof sector of dimension two."""
    return SectorStructure(labels=("s0",), dims=(2,), block_kind=band_a_block_kind())


@cache
def _q_descriptor() -> SystemDescriptor:
    """Return the Band-A target descriptor, which IS that sector map ((C1))."""
    return SystemDescriptor("Q", 2, Side.RECEIVER, (("s0", 2),), band_a_block_kind())


#: The BB84 instance's own spelling of the joint alphabet: the CHOICE
#: first, where Definition ``def:weighted``'s default writes the outcome first.
#: A bijection over the same disjoint union; labels are metadata and the index
#: is binding (the outputs table).
_BB84_LABELS: dict[tuple[Label, Label], Label] = {
    (outcome, choice): f"({choice},{outcome})"
    for choice in ("Z", "X")
    for outcome in ("0", "1")
}

#: The same, for the Z+Y signal set of the Y-basis example.
_CONJ_LABELS: dict[tuple[Label, Label], Label] = {
    (outcome, choice): f"({choice},{outcome})"
    for choice in ("Z", "Y")
    for outcome in ("0", "1")
}


def _emitted_family(
    choices: PublicChoices, sector_map: SectorStructure | None = None
) -> dict[Label, BlockOperator]:
    """Return the emitted BLOCK LISTS of one declared choice-weighted family.

    Definition ``def:weighted`` applied by the same function the compilation
    map uses, so an instance's receiver family and the family
    ``compile.compile_specification`` emits are produced
    by ONE code path and cannot drift.

    BAND A HAS ONE SECTOR with ``Pi_{s_0} = 1_Q`` (Definition ``def:banda``),
    so each emitted element is the one-block list carrying the whole matrix --
    which is the identity ``F_v = bigoplus_s F_v^(s)`` at ``|S| = 1``, not a
    truncation of anything.
    """
    from certiqs_key.protocol_compiler.weights import weighted_family

    if sector_map is None:
        sector_map = _qubit()

    return {
        label: BlockOperator.of(sector_map, [element])
        for label, element in weighted_family(choices).elements.items()
    }


def _basis_weights(first: Fraction, second: Fraction, party: str) -> None:
    """Refuse basis weights the BB84 specification does not admit.

    ``p_Z, p_X > 0`` is decided BY SIGN, which is what Definition
    ``def:weighted`` says of a strict inequality on a declared scalar.

    ``p_Z + p_X = 1`` IS CHECKED HERE ON THE COMPUTED BINARY64 TOTAL ONLY, so
    that the exact decision is taken where its refusal is a record. At the
    decimal literals ``fl(0.9)`` and ``fl(0.1)`` -- whose EXACT sum is
    ``1 + 2**-55`` and whose COMPUTED sum is exactly ``1`` -- this constructor
    admits the specification, and the compiler refuses it:
    ``protocol-compiler/req:weight-list`` decides the weight list exactly on
    the declared numbers and refuses it with ``choice_weights_not_normalized``,
    naming addition 2 of the declared order ``(Z, X)`` as the first that
    rounds (the frozen case ``S-ALICE-DECIMAL-LITERALS``). Deciding the
    equality exactly here would refuse the same specification as a raised
    exception instead of the refusal record the ``fail_closed`` convention
    requires.

    An ordinary run never meets this case: the instance surface prepares the
    four weights through the shared snapping rule onto lists that sum to
    exactly 1, and records the displacement (``req:weight-preparation``).
    """
    if first <= 0 or second <= 0:
        raise MalformedInputError(
            f"{party}'s basis weights must be strictly positive"
        )
    # Eq. eq:declorder on two scalar terms: Sigma_1 = 0 + first, which is exact
    # for any binary64 operand, and Sigma_2 = fl(Sigma_1 + second).
    computed = round_to_binary64(round_to_binary64(first) + second)
    if computed != 1:
        raise MalformedInputError(
            f"{party}'s basis weights sum to {computed} on the computed "
            f"binary64 total (exactly {first + second}), not 1"
        )


def _band_a_chain(
    alphabet: tuple[Label, ...], povm: dict[Label, BlockOperator]
) -> ReductionChain:
    """Return the Band-A chain of Definition ``def:banda`` carrying its target.

    ``L_s = 0`` and ``L = 1`` with ``Lambda_1 = id_Q``, status ``exact``, empty
    constraint slot and empty licence slot -- and, per Definition ``def:spec``
    (c), the last link's target descriptor ``(Q, S, (d_s))`` together with its
    target POVM ``{F_v}``. The outcome correspondence is the identity bijection
    on ``V = V^ph``, which is the special case of (C2)'s total surjection.
    """
    link = ChainLink(
        link_id="Lambda_1",
        segment=LinkStage.RECEIVER,
        link_type="squashing (identity)",
        source_descriptor=_q_descriptor(),
        target_descriptor=_q_descriptor(),
        status=LinkStatus.EXACT,
        channel=identity_channel(2),
        transported_constraints=(),
        license_slot=None,
        target_alphabet=alphabet,
        target_povm=povm,
    )
    return ReductionChain(
        source_segment=(),
        receiver_segment=(link,),
        # (C2) at its special case: the identity bijection on V = V^ph.
        outcome_correspondence={label: label for label in alphabet},
    )


def _announcement(label: Label) -> Label:
    """Return ``a_A`` / ``a_B`` of the BB84 specification at one outcome.

    ``a_A(b, a) = Z`` if ``b = Z`` and ``(X, a)`` if ``b = X``; ``C_B`` and
    ``a_B`` likewise on ``(b', y)``. The BASIS is announced always and the
    OUTCOME only in the ``X`` basis, which is what makes the ``Z`` class the
    single passing one.
    """
    basis, outcome = label[1:-1].split(",")
    return "Z" if basis == "Z" else f"(X,{outcome})"


def _bb84_public(alphabet: tuple[Label, ...]) -> PublicPart:
    """Return the public structure of the BB84 specification."""
    announcements = ("Z", "(X,0)", "(X,1)")
    classes = [(c_a, c_b) for c_a in announcements for c_b in announcements]
    accept: dict[tuple[Label, Label], Label] = {}
    for c_a, c_b in classes:
        if c_a == "Z" and c_b == "Z":
            accept[(c_a, c_b)] = "gen"
        elif c_a.startswith("(X") and c_b.startswith("(X"):
            accept[(c_a, c_b)] = "ok" if c_a == c_b else "err"
        else:
            accept[(c_a, c_b)] = "disc"
    return PublicPart(
        partition=default_party_partition(alphabet, alphabet),
        announce_alice={label: _announcement(label) for label in alphabet},
        announce_bob={label: _announcement(label) for label in alphabet},
        alice_announcement_alphabet=announcements,
        bob_announcement_alphabet=announcements,
        sifting={
            kappa: (Sifting.PASS if kappa == ("Z", "Z") else Sifting.FAIL)
            for kappa in classes
        },
        # r^0_A((b, a), kappa) = a, which lands in Z = {0, 1} as Definition
        # def:spec (d) requires -- the side condition of Remark rem:sidecond.
        key_rule={
            (label, kappa): int(label[1:-1].split(",")[1])
            for label in alphabet
            for kappa in classes
        },
        holder=Party.ALICE,
        key_alphabet=(0, 1),
        acceptance_alphabet=BB84_ACCEPTANCE_ALPHABET,
        accept_statistic=accept,
    )



def _trusted_artifact(
    alphabet: tuple[Label, ...],
    alice: PublicChoices,
    signal_weights: dict[Label, Fraction],
    signal_states: dict[Label, Matrix],
    certificate: SourceReplacementCertificate,
) -> TransmitterArtifact:
    """Return the transmitter artefact this instance declares, as a frozen record.

    WHY THE RECORD IS BUILT AND NOT EMITTED BY
    :func:`certiqs_key.transmitter.artifact.emit_artifact`. An instance is
    DATA (PRINCIPLES.md section 5), and the datum a consumer of this instance
    needs is the artefact itself. Going through the transmitter's decision
    would ALSO make this constructor refuse -- and one branch of
    :func:`conjugation_example_specification` exists precisely to be refused
    FURTHER DOWN, at the compiler's gate (G2), which re-decides the five
    certificate conditions on the emitted data. Routing it through the
    transmitter first would move that refusal one module upstream and delete
    the example. The transmitter's own decision path is exercised by the
    transmitter's own tests.

    ALICE'S FAMILY IS CONSTRUCTED HERE AND DECIDED IN THE COMPILER. The
    artefact carries the weighted ``{M_x}`` over the joint alphabet, which is
    what ``def:spec`` (a) reads; the CHOICE RECORD travels beside it in
    ``SourcePart.alice_choices``, so that ``def:compile``'s "weighted by
    ``def:weighted`` where a choice family is presented" is what the compiler
    does and ``def:weighted``'s emission decision is taken where its refusal is
    DATA. The numbers are the same numbers either way.
    """
    # THE CONSTRUCTION AND NOT THE DECISION. `weighted_family` applies
    # def:weighted's eq:weighted; `resolve_povm` would ALSO take the emission
    # decision and refuse a non-dyadic presentation here. That decision is the
    # COMPILER's -- def:weighted names it as "the one object this module
    # constructs" -- and it is taken on the compilation path, where its refusal
    # is DATA rather than an exception (the BB84-w3 case of the frozen
    # registry). So this constructor builds the numbers and decides nothing.
    emitted = weighted_family(alice)
    verification = verify_certificate(
        certificate, emitted.alphabet, dict(emitted.elements)
    )
    return TransmitterArtifact(
        signal_alphabet=alphabet,
        alice_dim=2,
        alice_marginal=certificate.alice_marginal,
        alice_povm=dict(emitted.elements),
        virtual_transmitted_system=certificate.virtual_dim,
        virtual_ensemble_weights=dict(signal_weights),
        virtual_ensemble_states=dict(signal_states),
        source_segment=(),
        source_replacement_license=SourceReplacementLicense.pass_through(
            verification, certificate.retention_attestation, certificate
        ),
        marginal_slot_filled=False,
        assumption_ledger=(
            "source_ensemble",
            "sequential_round_model",
            "source_replacement_license",
        ),
    )


def bb84_specification(
    alice_z: Fraction,
    alice_x: Fraction,
    bob_z: Fraction,
    bob_x: Fraction,
) -> ProtocolSpecification:
    """Return the source-replacement BB84 specification.

    Parameterized by the four declared basis weights, which the contract fixes
    only up to "``p^A_Z, p^A_X > 0`` with ``p^A_Z + p^A_X = 1``" on Alice's side
    and likewise on Bob's. NOTHING IN THE CONTRACT PREFERS A DYADIC WEIGHT, and
    this constructor accepts any exact rationals meeting those conditions --
    which is what makes the non-dyadic frozen instance a real test of the
    arithmetic rather than of the fixtures.

    The emitted declaration is ``tau_A = 1_A / 2``,
    ``M_{(b,a)} = p^A_b |conj(a^b)><conj(a^b)|``,
    ``F_{(b',y)} = p^B_{b'} |y^{b'}><y^{b'}|`` and ``CList`` empty -- but this
    function returns the SPECIFICATION, and it is
    ``compile.compile_specification`` that produces those
    matrices, by weighting the declared conditional families.
    """
    _basis_weights(alice_z, alice_x, "Alice")
    _basis_weights(bob_z, bob_x, "Bob")
    alphabet: tuple[Label, ...] = ("(Z,0)", "(Z,1)", "(X,0)", "(X,1)")
    signal_states = {
        "(Z,0)": P_Z0,
        "(Z,1)": P_Z1,
        "(X,0)": P_X0,
        "(X,1)": P_X1,
    }
    signal_weights = {
        "(Z,0)": alice_z / 2,
        "(Z,1)": alice_z / 2,
        "(X,0)": alice_x / 2,
        "(X,1)": alice_x / 2,
    }
    # THE BAR IS APPLIED HERE, in the DECLARED conditional families.
    alice_choices = PublicChoices(
        party=Party.ALICE,
        choices=("Z", "X"),
        weights={"Z": alice_z, "X": alice_x},
        conditional_alphabets={"Z": ("0", "1"), "X": ("0", "1")},
        conditional_elements={
            "Z": {
                "0": conjugate_projector(P_Z0),
                "1": conjugate_projector(P_Z1),
            },
            "X": {
                "0": conjugate_projector(P_X0),
                "1": conjugate_projector(P_X1),
            },
        },
        joint_labels=_BB84_LABELS,
    )
    bob_choices = PublicChoices(
        party=Party.BOB,
        choices=("Z", "X"),
        weights={"Z": bob_z, "X": bob_x},
        conditional_alphabets={"Z": ("0", "1"), "X": ("0", "1")},
        conditional_elements={
            "Z": {"0": P_Z0, "1": P_Z1},
            "X": {"0": P_X0, "1": P_X1},
        },
        joint_labels=_BB84_LABELS,
    )
    certificate = SourceReplacementCertificate(
        alice_marginal=scale(Fraction(1, 2), matrix(((1, 0), (0, 1)))),
        # Psi = |Phi+><Phi+| ON A A'', DECLARED AS THE OPERATOR. Every entry
        # is 0 or 1/2, both binary64, where the VECTOR |Phi+> has
        # amplitudes 1/sqrt2 THAT NO BINARY64 NUMBER SQUARES TO 1/2.
        psi=_PHI_PLUS,
        virtual_dim=2,
        virtual_weights=signal_weights,
        virtual_states=signal_states,
    )
    return ProtocolSpecification(
        source=SourcePart(
            artifact=_trusted_artifact(
                alphabet, alice_choices, signal_weights, signal_states, certificate
            ),
            alice_choices=alice_choices,
        ),
        receiver=ReceiverPart(physical_dim=2, physical_povm=bob_choices),
        public=_bb84_public(alphabet),
        sectors=_qubit(),
        chain=_band_a_chain(alphabet, _emitted_family(bob_choices)),
        constraints=SpecConstraints(),
    )


class ConjugationConvention(StrEnum):
    """Which of the Y-basis example's two branches a specification declares.

    ``CONTRACT`` is the ``conjugation_basis`` convention as the contract states
    it. ``OMITTED`` is THE DEFECT the example exists to exhibit -- the emitted
    element without the bar -- and is never a conforming emission: compiled at
    ``d_A = 2`` it fails (SR2) and gate (G2) refuses it (Table
    ``tab:gateoutcome``, row 3). It is named rather than hidden because no
    test built on the BB84 instance, whose signal states are all real, can
    catch a reversed convention, so the branch pair IS the defence.
    """

    CONTRACT = "contract"
    OMITTED = "omitted"


def conjugation_example_specification(
    convention: ConjugationConvention = ConjugationConvention.CONTRACT,
) -> ProtocolSpecification:
    """Return the Y-basis conjugation example as a specification.

    It is the smallest specification on which the conjugation convention is
    OBSERVABLE, so that the regression test built from it discriminates.

    The signal set is ``{|0^Y>, |1^Y>}`` (:data:`P_Y0`, :data:`P_Y1`), on which
    conjugation in the declared basis SWAPS THE TWO LABELS -- so the defect is a
    label permutation and not a phase, and it shows at three points of the
    pipeline: the emitted element, the (SR2) verdict, and the matched-basis
    statistics.

    THE Y BASIS IS EMBEDDED IN THE SMALLEST COMPLETE FAMILY, and that is a
    consequence of turning an auxiliary computation into a SPECIFICATION.
    The example needs a signal set CONTAINING the Y-basis states; a
    specification must declare a COMPLETE POVM
    (Definition ``def:spec`` (a), Assumption ``ass:spec``), and a lone Y basis
    at weight ``p^A_Y = 1/2`` sums to ``1_A / 2``. The Z basis is therefore
    declared alongside it at the same weight, so that ``sum_x M_x = 1_A``. THE
    Y ROWS ARE UNCHANGED BY THE EMBEDDING: ``M_{(Y,a)}`` and ``F_{(Y,y)}``
    depend on ``p^A_Y = p^B_Y = 1/2`` and on the Y projectors alone, and the
    added Z rows are additional rows of the same table.
    """
    alphabet: tuple[Label, ...] = ("(Z,0)", "(Z,1)", "(Y,0)", "(Y,1)")
    signal_states = {
        "(Z,0)": P_Z0,
        "(Z,1)": P_Z1,
        "(Y,0)": P_Y0,
        "(Y,1)": P_Y1,
    }
    half = Fraction(1, 2)
    signal_weights = dict.fromkeys(alphabet, half / 2)
    y_conditionals = (
        {"0": conjugate_projector(P_Y0), "1": conjugate_projector(P_Y1)}
        if convention is ConjugationConvention.CONTRACT
        else {"0": P_Y0, "1": P_Y1}
    )
    alice_choices = PublicChoices(
        party=Party.ALICE,
        choices=("Z", "Y"),
        weights={"Z": half, "Y": half},
        conditional_alphabets={"Z": ("0", "1"), "Y": ("0", "1")},
        conditional_elements={
            "Z": {
                "0": conjugate_projector(P_Z0),
                "1": conjugate_projector(P_Z1),
            },
            "Y": y_conditionals,
        },
        joint_labels=_CONJ_LABELS,
    )
    bob_choices = PublicChoices(
        party=Party.BOB,
        choices=("Z", "Y"),
        weights={"Z": half, "Y": half},
        conditional_alphabets={"Z": ("0", "1"), "Y": ("0", "1")},
        conditional_elements={
            "Z": {"0": P_Z0, "1": P_Z1},
            "Y": {"0": P_Y0, "1": P_Y1},
        },
        joint_labels=_CONJ_LABELS,
    )
    announcements = ("Z", "Y")
    classes = [(c_a, c_b) for c_a in announcements for c_b in announcements]
    public = PublicPart(
        partition=default_party_partition(alphabet, alphabet),
        announce_alice={label: label[1] for label in alphabet},
        announce_bob={label: label[1] for label in alphabet},
        alice_announcement_alphabet=announcements,
        bob_announcement_alphabet=announcements,
        # Sifting on the MATCHED basis, which keeps D(v) true and leaves the
        # matched-basis Y rows -- the ones the convention is observable on --
        # inside the key-live class.
        sifting={
            kappa: (Sifting.PASS if kappa[0] == kappa[1] else Sifting.FAIL)
            for kappa in classes
        },
        key_rule={
            (label, kappa): int(label[1:-1].split(",")[1])
            for label in alphabet
            for kappa in classes
        },
        holder=Party.ALICE,
        key_alphabet=(0, 1),
        acceptance_alphabet=("matched", "mismatched"),
        accept_statistic={
            kappa: ("matched" if kappa[0] == kappa[1] else "mismatched")
            for kappa in classes
        },
    )
    certificate = SourceReplacementCertificate(
        alice_marginal=scale(half, matrix(((1, 0), (0, 1)))),
        # Psi = |Phi+><Phi+| ON A A'', DECLARED AS THE OPERATOR. Every entry
        # is 0 or 1/2, both binary64, where the VECTOR |Phi+> has
        # amplitudes 1/sqrt2 THAT NO BINARY64 NUMBER SQUARES TO 1/2.
        psi=_PHI_PLUS,
        virtual_dim=2,
        virtual_weights=signal_weights,
        virtual_states=signal_states,
    )
    return ProtocolSpecification(
        source=SourcePart(
            artifact=_trusted_artifact(
                alphabet, alice_choices, signal_weights, signal_states, certificate
            ),
            alice_choices=alice_choices,
        ),
        receiver=ReceiverPart(physical_dim=2, physical_povm=bob_choices),
        public=public,
        sectors=_qubit(),
        chain=_band_a_chain(alphabet, _emitted_family(bob_choices)),
        constraints=SpecConstraints(),
    )
