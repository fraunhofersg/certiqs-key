"""Hand-built declarations of the GENERAL FORMAT, and points of their feasible sets.

Toys for the engine-level targets of the two frozen instance registries --
``tests/oracles/registry_instances_decoy_bb84.py`` OT1 to OT4 and
``registry_instances_bbm92.py`` B-6 -- which are stated of the mathematics and
not of an instance, so they are testable on a toy the way the registries'
``observable`` fields ask.

EVERY DECLARED NUMBER HERE IS DYADIC, so every declaration is exactly
admissible in the sense of ``def:declaration``'s exact-admissibility paragraph
and passes
:func:`~certiqs_key.meat_core.declaration.general_validation.validate_general_declaration`
without a repair. That is not decoration: an inexactly admissible toy would be
refused, and a test that needed one would be testing a path no run has.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from itertools import product

import numpy as np

from certiqs_key.domain.manifest import ConstraintRelation, KeyHolder, PartyLabel
from certiqs_key.meat_core.declaration.declaration import (
    AcceptanceSet,
    KeyLengthParameters,
)
from certiqs_key.meat_core.declaration.general import (
    AliceFactor,
    AliceForm,
    GeneralConstraintEntry,
    GeneralDeclaration,
    GeneralRhsTag,
    MeasuredFactor,
    Message,
    Transcript,
    sector_axis,
)
from certiqs_key.meat_core.objective.joint import (
    JointChoiParametrization,
    JointMaps,
    JointSector,
    build_joint_maps,
    joint_choi_parametrization,
    joint_statistics,
)
from certiqs_key.meat_core.objective.linalg import Matrix

#: The Renyi orders the tests sweep. The registries' own grid is wider; these
#: three span it and keep the property tests quick.
ALPHA_GRID = (1.05, 1.5, 2.0)

_PARAMETERS = KeyLengthParameters(alpha=1.5, eps_pa=1e-10, eps_ev=1e-10, lambda_ec=0)


def projector(vector: Sequence[complex]) -> Matrix:
    """Return ``|v><v|`` of a unit vector, as binary64 data."""
    column = np.asarray(vector, dtype=np.complex128).reshape(-1, 1)
    return np.asarray(column @ column.conj().T, dtype=np.complex128)


#: The four BB84 projectors, halved so that the four-element family is a POVM
#: with DYADIC entries: ``sum_x M_x = (|0><0| + |1><1| + |+><+| + |-><-|)/2 = 1``.
_ROOT_HALF = 0.5
BB84_LETTERS = ("z0", "z1", "x0", "x1")
BB84_BASIS = {"z0": "Z", "z1": "Z", "x0": "X", "x1": "X"}
BB84_BIT = {"z0": 0, "z1": 1, "x0": 0, "x1": 1}
BB84_ELEMENTS: Mapping[str, Matrix] = {
    "z0": 0.5 * projector((1.0, 0.0)),
    "z1": 0.5 * projector((0.0, 1.0)),
    "x0": np.asarray(
        [[_ROOT_HALF * 0.5, _ROOT_HALF * 0.5], [_ROOT_HALF * 0.5, _ROOT_HALF * 0.5]],
        dtype=np.complex128,
    ),
    "x1": np.asarray(
        [[_ROOT_HALF * 0.5, -_ROOT_HALF * 0.5], [-_ROOT_HALF * 0.5, _ROOT_HALF * 0.5]],
        dtype=np.complex128,
    ),
}


def _bb84_transcript() -> Transcript:
    """Return the ``L = 2`` transcript: Alice's basis, then Bob's basis.

    The degenerate case of ``def:declaration`` (DX5): two messages neither of
    which reads the other.
    """
    return Transcript(
        messages=(
            Message(
                sender=KeyHolder.ALICE,
                alphabet=("Z", "X"),
                table={(x, ()): BB84_BASIS[x] for x in BB84_LETTERS},
            ),
            Message(
                sender=KeyHolder.BOB,
                alphabet=("Z", "X"),
                table={
                    (v, (first,)): BB84_BASIS[v]
                    for v in BB84_LETTERS
                    for first in ("Z", "X")
                },
            ),
        )
    )


def _three_message_transcript() -> Transcript:
    """Return an ``L = 3`` transcript whose third message READS the first two.

    ``def:declaration`` (DX5) admits any ordered list of messages, each a
    function of its sender's readout and of the earlier messages; this is the
    smallest one the accepted format's two maps cannot express, and it is what a
    test of the transcript reading needs.
    """
    return Transcript(
        messages=(
            Message(
                sender=KeyHolder.ALICE,
                alphabet=("Z", "X"),
                table={(x, ()): BB84_BASIS[x] for x in BB84_LETTERS},
            ),
            Message(
                sender=KeyHolder.BOB,
                alphabet=("Z", "X"),
                table={
                    (v, (first,)): BB84_BASIS[v]
                    for v in BB84_LETTERS
                    for first in ("Z", "X")
                },
            ),
            Message(
                sender=KeyHolder.ALICE,
                alphabet=("keep", "drop"),
                table={
                    (x, (first, second)): ("keep" if first == second else "drop")
                    for x in BB84_LETTERS
                    for first in ("Z", "X")
                    for second in ("Z", "X")
                },
            ),
        )
    )


def _bb84_maps(
    transcript: Transcript,
) -> tuple[dict[tuple[str, ...], str], dict[tuple[str, str], int | None]]:
    """Return ``phi`` and ``r`` for a BB84 transcript, sifting on matched bases."""
    # DX5 defines K as the full message product, including unreachable tuples.
    statistic = {
        letters: "match" if letters[0] == letters[1] else "mismatch"
        for letters in product(*(m.alphabet for m in transcript.messages))
    }
    key: dict[tuple[str, str], int | None] = {}
    for x in BB84_LETTERS:
        for v in BB84_LETTERS:
            letters: tuple[str, ...] = ()
            for message in transcript.messages:
                readout = x if message.sender is KeyHolder.ALICE else v
                letters = (*letters, message.table[(readout, letters)])
            matched = BB84_BASIS[x] == BB84_BASIS[v]
            statistic[letters] = "match" if matched else "mismatch"
            key[(x, v)] = BB84_BIT[x] if matched else None
    return statistic, key


def _qubit_factor(label: str = "f0") -> MeasuredFactor:
    """Return one measured factor: a qubit with the four BB84 elements."""
    return MeasuredFactor(
        label=label,
        party=PartyLabel.BOB,
        sectors=sector_axis([("q", 2)]),
        alphabet=BB84_LETTERS,
        blocks={v: {"q": BB84_ELEMENTS[v]} for v in BB84_LETTERS},
    )


def qubit_bb84_general(
    *, ensemble: bool = False, messages: int = 2
) -> GeneralDeclaration:
    """Return the qubit BB84 declaration, in POVM or ENSEMBLE form.

    ``tau_A = 1/2`` is a MULTIPLE OF THE IDENTITY, which is what the
    ensemble-form equality test needs: ``N_x = tau^{1/2} M_x tau^{1/2} = M_x/2``
    is then exactly representable, so the two declarations denote each other on
    the binary64 lattice and any difference between their objectives is the
    code's and not the data's.

    At ``messages = 2`` this declaration is DEGENERATE -- it is the accepted
    format entry for entry -- and at ``messages = 3`` it is not, the third
    message reading the first two.
    """
    transcript = _bb84_transcript() if messages == 2 else _three_message_transcript()
    statistic, key = _bb84_maps(transcript)
    tau = 0.5 * np.eye(2, dtype=np.complex128)
    operators = {
        x: {"t0": (0.5 * BB84_ELEMENTS[x] if ensemble else BB84_ELEMENTS[x])}
        for x in BB84_LETTERS
    }
    return GeneralDeclaration(
        alice=AliceFactor(party=PartyLabel.ALICE, sectors=sector_axis([("t0", 2)])),
        alice_marginal={"t0": tau},
        alice_alphabet=BB84_LETTERS,
        alice_operators=operators,
        alice_form=AliceForm.ENSEMBLE if ensemble else AliceForm.POVM,
        factors=(_qubit_factor(),),
        transcript=transcript,
        accept_statistic=statistic,
        key_map=key,
        key_holder=KeyHolder.ALICE,
        acceptance_values=("match", "mismatch"),
        key_value_count=2,
        acceptance_set=AcceptanceSet(geometry="singleton", frequencies=(0.5, 0.5)),
        rounds=1000,
        parameters=_PARAMETERS,
        sector_block_kind="photon_number",
    )


def decoy_like_general(*, ensemble: bool = False) -> GeneralDeclaration:
    """Return a declaration with FOUR ALICE SECTORS of the decoy shape.

    The shapes OT1 to OT4 are stated on, on the smallest space that carries
    them:

    * ``vacuum`` -- ``d_{A_t} = 1``, so ``tau_A^{(t)}`` is rank one, with
      Alice's letters carrying equal weight inside each basis class: the key is
      a UNIFORM BIT there, which is OT1's one bit per sifted round;
    * ``flag`` -- ``d_{A_t} = 1`` with all the weight on one letter, so the key
      is CONSTANT where ``mu_x > 0``: OT2's identically zero deficit;
    * ``rank1`` -- ``d_{A_t} = 2`` with a RANK-ONE marginal, which is OT3's
      "rank-one Alice sectors factorise at every feasible point" on a sector
      where factorisation is a statement and not a triviality;
    * ``one`` -- ``d_{A_t} = 2`` with ``tau_A^{(t)} = p 1/2``, the single-photon
      sector OT4's Bell-diagonal closed form is stated on.

    The weights are dyadic and sum to one exactly, in the declared order.
    """
    transcript = _bb84_transcript()
    statistic, key = _bb84_maps(transcript)
    weights = {"vacuum": 0.25, "one": 0.25, "flag": 0.25, "rank1": 0.25}
    marginal = {
        "vacuum": np.asarray([[weights["vacuum"]]], dtype=np.complex128),
        "one": weights["one"] * np.eye(2, dtype=np.complex128) / 2.0,
        "flag": np.asarray([[weights["flag"]]], dtype=np.complex128),
        "rank1": weights["rank1"] * projector((1.0, 0.0)),
    }
    povm: dict[str, dict[str, Matrix]] = {}
    for x in BB84_LETTERS:
        povm[x] = {
            "vacuum": np.asarray([[0.25]], dtype=np.complex128),
            "one": BB84_ELEMENTS[x],
            "flag": np.asarray(
                [[1.0 if x == "z0" else 0.0]], dtype=np.complex128
            ),
            "rank1": BB84_ELEMENTS[x],
        }
    if ensemble:
        # N_x^(t) = tau^{1/2} M_x^(t) tau^{1/2}, WRITTEN OUT ON THE LATTICE
        # rather than computed from a numerical square root: on these sectors
        # tau is c 1 or c |0><0|, so the product is c M_x, respectively
        # c (M_x)_{00} |0><0|, and every entry stays dyadic. A numerical root
        # would put the declared sum off the lattice and the declaration would
        # be REFUSED for rounding -- which is the admission rule working, not a
        # defect, and is why the toy declares the exact numbers.
        operators: dict[str, dict[str, Matrix]] = {}
        for x in BB84_LETTERS:
            block = povm[x]
            operators[x] = {
                "vacuum": weights["vacuum"] * block["vacuum"],
                "one": (weights["one"] / 2.0) * block["one"],
                "flag": weights["flag"] * block["flag"],
                "rank1": weights["rank1"]
                * float(np.real(block["rank1"][0, 0]))
                * projector((1.0, 0.0)),
            }
    else:
        operators = povm
    return GeneralDeclaration(
        alice=AliceFactor(
            party=PartyLabel.ALICE,
            sectors=sector_axis(
                [("vacuum", 1), ("one", 2), ("flag", 1), ("rank1", 2)]
            ),
        ),
        alice_marginal=marginal,
        alice_alphabet=BB84_LETTERS,
        alice_operators=operators,
        alice_form=AliceForm.ENSEMBLE if ensemble else AliceForm.POVM,
        factors=(_qubit_factor(),),
        transcript=transcript,
        accept_statistic=statistic,
        key_map=key,
        key_holder=KeyHolder.ALICE,
        acceptance_values=("match", "mismatch"),
        key_value_count=2,
        acceptance_set=AcceptanceSet(geometry="singleton", frequencies=(0.5, 0.5)),
        rounds=1000,
        parameters=_PARAMETERS,
        sector_block_kind="photon_number",
    )


def _psd_root(matrix: Matrix) -> Matrix:
    """Return the positive semidefinite square root of a small block."""
    values, vectors = np.linalg.eigh(np.asarray(matrix, dtype=np.complex128))
    kept = np.clip(values, 0.0, None) ** 0.5
    return np.asarray((vectors * kept) @ vectors.conj().T, dtype=np.complex128)


def two_factor_general(*, party_local: bool) -> GeneralDeclaration:
    """Return an untrusted-source declaration with TWO measured factors.

    The BBM92 shape of ``05-validation.md`` B-6 on the smallest space: ``d_A =
    1``, a one-letter ``X``, two qubit factors with their own alphabets, and one
    constraint entry scoped to the SECOND factor -- declared ``party_local`` or
    scalar, which is the only difference between the two declarations B-6
    compares.
    """
    alice_letter = "*"
    first = MeasuredFactor(
        label="fA",
        party=PartyLabel.ALICE,
        sectors=sector_axis([("qA", 2)]),
        alphabet=BB84_LETTERS,
        blocks={v: {"qA": BB84_ELEMENTS[v]} for v in BB84_LETTERS},
    )
    second = MeasuredFactor(
        label="fB",
        party=PartyLabel.BOB,
        sectors=sector_axis([("qB", 2)]),
        alphabet=BB84_LETTERS,
        blocks={v: {"qB": BB84_ELEMENTS[v]} for v in BB84_LETTERS},
    )
    transcript = Transcript(
        messages=(
            Message(
                sender=KeyHolder.ALICE,
                alphabet=("*",),
                table={(alice_letter, ()): "*"},
            ),
            Message(
                sender=KeyHolder.BOB,
                alphabet=("ZZ", "XX", "no"),
                table={
                    (f"{a}__{b}", ("*",)): (
                        "ZZ"
                        if BB84_BASIS[a] == BB84_BASIS[b] == "Z"
                        else ("XX" if BB84_BASIS[a] == BB84_BASIS[b] == "X" else "no")
                    )
                    for a in BB84_LETTERS
                    for b in BB84_LETTERS
                },
            ),
        )
    )
    statistic: dict[tuple[str, ...], str] = {}
    key: dict[tuple[str, str], int | None] = {}
    for a in BB84_LETTERS:
        for b in BB84_LETTERS:
            letter = f"{a}__{b}"
            kappa = ("*", transcript.messages[1].table[(letter, ("*",))])
            statistic[kappa] = "sifted" if kappa[1] != "no" else "discarded"
            key[(alice_letter, letter)] = BB84_BIT[a] if kappa[1] != "no" else None
    # THE ENTRY B-6 COMPARES, and its constant is chosen so that the two
    # readings SEPARATE: with ``O_k = F_z0`` on the second factor and
    # ``c_k = 1/4``, a point whose first factor correlates the two stations
    # satisfies the scalar reading with equality while the operator reading of
    # eq:partylocal-entry fails on one of its rows. A constant at which both
    # readings are vacuous would test nothing.
    entry = GeneralConstraintEntry(
        scope="fB",
        operator_blocks={"qB": BB84_ELEMENTS["z0"]},
        relation=ConstraintRelation.PRECEQ,
        bound=0.25,
        rhs_tag=(
            GeneralRhsTag.PARTY_LOCAL if party_local else GeneralRhsTag.HOMOGENEOUS
        ),
    )
    return GeneralDeclaration(
        alice=AliceFactor(party=PartyLabel.ALICE, sectors=sector_axis([("t0", 1)])),
        alice_marginal=None,
        alice_alphabet=(alice_letter,),
        alice_operators={alice_letter: {"t0": np.eye(1, dtype=np.complex128)}},
        alice_form=AliceForm.POVM,
        factors=(first, second),
        transcript=transcript,
        accept_statistic=statistic,
        key_map=key,
        key_holder=KeyHolder.BOB,
        acceptance_values=("sifted", "discarded"),
        key_value_count=2,
        acceptance_set=AcceptanceSet(geometry="singleton", frequencies=(0.5, 0.5)),
        rounds=1000,
        parameters=_PARAMETERS,
        sector_block_kind="photon_number",
        constraint_list=(entry,),
    )


def maps_of(declaration: GeneralDeclaration) -> JointMaps:
    """Return the generated maps of a toy, with its frames."""
    return build_joint_maps(joint_choi_parametrization(declaration))


def random_choi_point(
    parametrization: JointChoiParametrization, seed: int
) -> dict[JointSector, Matrix]:
    """Return a random point satisfying the coupling condition of its mode.

    Trusted: one coupling constraint per Alice sector, imposed by conjugating a
    random positive list with the inverse square root of its own summed partial
    trace. Untrusted: the single normalisation. The declared constraint rows are
    NOT imposed -- a caller that needs them supplies its own point -- and every
    property stated "at every feasible point" is tested on points of the
    coupling set, which contains the feasible set.
    """
    rng = np.random.default_rng(seed)
    declaration = parametrization.declaration
    blocks: dict[JointSector, Matrix] = {}
    for pair in parametrization.joint_sectors:
        dim = parametrization.block_dim(pair)
        sample = rng.normal(size=(dim, dim)) + 1j * rng.normal(size=(dim, dim))
        blocks[pair] = np.asarray(sample @ sample.conj().T, dtype=np.complex128)
    if not declaration.is_trusted_source:
        total = sum(float(np.real(np.trace(blocks[p]))) for p in blocks)
        return {pair: block / total for pair, block in blocks.items()}
    out: dict[JointSector, Matrix] = {}
    for alice_sector in declaration.alice_sectors:
        input_dim = parametrization.input_dim(alice_sector)
        accumulated = np.zeros((input_dim, input_dim), dtype=np.complex128)
        for sector in declaration.sector_index_set:
            width = declaration.sector_dims[sector]
            block = blocks[(alice_sector, sector)].reshape(
                input_dim, width, input_dim, width
            )
            accumulated = accumulated + np.einsum("aqbq->ab", block)
        values, vectors = np.linalg.eigh(accumulated)
        inverse_root = np.asarray(
            (vectors * (values ** -0.5)) @ vectors.conj().T, dtype=np.complex128
        )
        for sector in declaration.sector_index_set:
            width = declaration.sector_dims[sector]
            lift = np.kron(inverse_root, np.eye(width, dtype=np.complex128))
            out[(alice_sector, sector)] = np.asarray(
                lift @ blocks[(alice_sector, sector)] @ lift.conj().T,
                dtype=np.complex128,
            )
    return out


def honest_q(maps: JointMaps, choi: Mapping[JointSector, Matrix]) -> dict[str, float]:
    """Return ``q = Phi[chi(J)]``, at which every divergence term vanishes.

    The registries' own convention for a closed form: at ``q = Phi[omega]`` the
    objective of ``eq:objective`` is the single key term, so a test compares the
    entropy and not a divergence.
    """
    return joint_statistics(maps, choi)


def bits_from_objective(objective: float, p_gen: float, alpha: float) -> float:
    """Return the conditional entropy an objective at ``q = Phi`` carries.

    Inverting ``O = (P/(alpha-1)) log2(P/K)`` and ``K/P = 2^{(1-alpha)h}``:
    ``h = O / P``. The registries state their targets as bits per SIFTED round,
    so a caller divides by the pass weight, which is what this does.
    """
    del alpha
    return objective / p_gen if p_gen > 0.0 else math.nan
