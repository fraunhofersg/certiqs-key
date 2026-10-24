"""The channel witness, the generic adjoints, and the POVM predicates.

WHAT THIS FILE COMPUTES, AND WHAT IT DELIBERATELY DOES NOT
==========================================================
Every statement of this module is written with ``Lambda^dagger``. Definition
``def:squashing`` reads ``Lambda^dagger(F_v) = M_v``; Corollary
``cor:pullback`` transports operator bounds through ``Lambda^dagger``; Theorem
``thm:licence``'s hypothesis Eq. ``eq:certificate`` is a statement about
``Lambda^dagger(O^_k)``. So the adjoints are what this module computes, in the
closed forms the claims prove -- Eq. ``eq:masteradjoint``, Lemma ``lem:top``'s
``Lmp^dagger``, Corollary ``cor:flagsenough``'s, Theorem ``thm:mixture``'s
``I_b^dagger`` -- and never by materialising a channel.

That is not an optimization. It is a fact about the data: the receiver supplier
emits NO ABOVE-CUTOFF BLOCK AT ALL, "so neither map can be materialised from
the artifact -- and neither need be, SINCE THE CONSUMER NEVER APPLIES IT". The
emitted ``squashing_channel`` is therefore "A SYMBOLIC CONSTRUCTOR RECORD, NOT
EVALUABLE DATA, ON EITHER ROUTE", which is :class:`ChannelWitness` below.

The adjoint functions here nonetheless take the above-cutoff data as an
argument, because a TOY INSTANCE has it and the claims' identities are
checkable on one. An artifact path never supplies it and never needs to.

WHAT LIVES WHERE, AND WHY THIS FILE IS THE CORE'S HALF
======================================================
This is the generic half of the reductions constructions; the device-specific
constructions are the submodules':

* HERE, the core: the constructor record and its composition, the flag
  projector, the block split, and the four adjoints that belong to no device --
  ``lem:top``'s measure-and-prepare, ``cor:flagsenough``'s,
  ``thm:mixture``'s instrument adjoint and ``eq:masteradjoint``'s mixture,
  ``prop:pinching``'s pinching -- together with the predicates that decide
  whether a declared family is a POVM.
* :mod:`certiqs_key.reductions.wpfss.construction`: the weight-preserving and
  flag-state targets, ``M'``, their adjoints and the transported cutoff pair.
  One squasher is a submodule.
* a branching submodule's construction: its target, sectors, transport and
  adjoint. Deleting that submodule's directory leaves this one whole.

THE SQUASHING-CHANNEL CONSTRUCTOR RECORD IS DECIDED HERE. The interface "names
WHAT the record identifies (the constructor and its parameters) and states WHY
it cannot be materialised ... It states no schema for the record."
:class:`ChannelWitness` is a frozen record carrying the constructor's equation,
its declared parameters as strings, and the ordered list of witnesses it is
composed of, plus a stable ``identity`` string. Two properties are what the
record is for. First, "LATER LINKS ACT LATER" and "THE ORDER IS EMITTED AS DATA
AND IS NEVER INFERRED FROM ARTIFACT CREATION TIME", so ``composed_of`` is an
ordered list and :func:`compose_witnesses` writes the composite in that order.
Second, an entry is refused unless it is "certified against THE CHANNEL WITNESS
OF ITS OWN LINK", which needs witnesses to be COMPARABLE -- so ``identity``
exists and is what a constraint entry names. NOTHING IN THE RECORD IS
EVALUABLE, and no function here turns one into a matrix.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from fractions import Fraction

from certiqs_key.foundations.exact import (
    Cx,
    Matrix,
    add,
    basis_projector,
    conjugate_transpose,
    dimension,
    equal,
    identity,
    is_hermitian,
    is_positive_semidefinite,
    kron,
    matmul,
    real_part,
    scale,
    zeros,
)
from certiqs_key.reductions.errors import MalformedInputError
from certiqs_key.reductions.reasons import CertificateKind, Relation

__all__ = [
    "ChannelWitness",
    "TransportedOperator",
    "adjoint_is_unital",
    "compose_witnesses",
    "conjugated",
    "flag_diagonal",
    "flag_projector",
    "flags_enough_adjoint",
    "instrument_adjoint",
    "is_povm",
    "mixture_adjoint",
    "mp_adjoint",
    "pinching_adjoint",
    "split_blocks",
]


@dataclass(frozen=True)
class ChannelWitness:
    """The symbolic constructor record of the emitted ``squashing_channel``.

    ``identity`` is a stable name a constraint entry can be certified against;
    ``equation`` is the claim's equation the constructor is; ``parameters``
    names the declared data it is built from, as strings, because the record is
    "NOT EVALUABLE DATA"; ``composed_of`` is the ORDERED list of witnesses the
    composite is made of, later acting later.

    ``precomposed_with`` is the record of a channel ``Phi`` ACTING FIRST, in
    front of this witness's channel: the precomposed instance of
    Lemma ``lem:precomposed-instance`` has the channel ``Lambda o Phi``, and
    by its item (i) every spectral certificate of the instance holds of the
    composite at the same constant, so the composite keeps the identity the
    entries are certified against. ``None`` where nothing is precomposed, and
    then the record carries no such key.
    """

    identity: str
    equation: str
    parameters: tuple[str, ...] = ()
    composed_of: tuple[str, ...] = ()
    precomposed_with: ChannelWitness | None = None

    def as_machine_record(self) -> dict[str, object]:
        """Return the witness as a machine record, for the emitted artifact."""
        record: dict[str, object] = {
            "identity": self.identity,
            "equation": self.equation,
            "parameters": list(self.parameters),
            "composed_of": list(self.composed_of),
        }
        if self.precomposed_with is not None:
            record["precomposed_with"] = self.precomposed_with.as_machine_record()
        return record


def compose_witnesses(
    identity_name: str, witnesses: Sequence[ChannelWitness]
) -> ChannelWitness:
    """Return the composite witness ``Lambda_k o ... o Lambda_1``.

    "LATER LINKS ACT LATER, so ``Lambda = Lambda_k o ... o Lambda_1`` and
    ``Lambda^dagger = Lambda_1^dagger o ... o Lambda_k^dagger``."
    ``composed_of`` is written in the order the LINKS were declared -- the order
    the channels ACT in -- so that reading the record never requires knowing
    which convention was used.
    """
    if not witnesses:
        raise MalformedInputError("a composite witness composes at least one witness")
    return ChannelWitness(
        identity=identity_name,
        equation="Lambda_Chain = Lambda_{l_k} o ... o Lambda_{l_1} (def:chain)",
        parameters=(),
        composed_of=tuple(witness.identity for witness in witnesses),
    )


@dataclass(frozen=True)
class TransportedOperator:
    """One entry of the carried tuple: ``(O^_k, O_k)`` with its certificate case.

    "The carried tuple with ``Lambda^dagger(O^_k) = O_k`` and, PER ENTRY, the
    certificate (identity / positivity / spectral bound) that makes it usable
    (Cor. ``cor:transported``)."

    ``target_operator`` IS THE SECTOR-BLOCK LIST of ``hat O_k``: one square
    block per sector, in the sector map's order, "exactly as ``target_povm``
    is" (the outputs table, ``transported_operators``; spec/architecture.md
    2.8-2.9). The ``dim H(Q) x dim H(Q)`` direct sum is what the list MEANS and
    is never an object this record carries. The PULL-BACK is not of that kind: it is an
    operator on ``B``, whose sectors are not ``Q``'s and which on an artifact path is
    not a matrix at all.

    ``pullback`` is ``None`` EXACTLY WHEN the pull-back is an operator on the
    channel Fock space and no finite channel dimension was declared. That is the
    ordinary case on an artifact path: the pull-back of a cutoff projector is an
    operator on a system with an infinite-dimensional factor, which Definition
    ``def:system-setting`` permits exactly here. ``pullback_expression`` carries
    the claim's own form in that case, and it is what the artifact records --
    the emitted key asks for the carried tuple and its certificate, not for a
    matrix that does not exist. A toy instance with a finite channel supplies
    the dimension and gets the matrix.
    """

    label: str
    target_operator: tuple[Matrix, ...]
    pullback: Matrix | None
    pullback_expression: str
    certificate_kind: CertificateKind
    relation: Relation
    constant: Fraction
    certified_against: str


def flag_projector(alphabet_size: int, index: int) -> Matrix:
    """Return ``|v><v|_Flag`` on ``H(Flag) = C^{|V|}``."""
    return basis_projector(alphabet_size, index)


def split_blocks(x: Matrix, dims: Sequence[int]) -> list[Matrix]:
    """Return the diagonal blocks of ``x`` for the given ordered dimensions."""
    if sum(dims) != len(x):
        raise MalformedInputError("the declared block dimensions do not sum to dim X")
    out: list[Matrix] = []
    offset = 0
    for dim in dims:
        out.append(
            tuple(
                tuple(x[offset + i][offset + j] for j in range(dim)) for i in range(dim)
            )
        )
        offset += dim
    return out


def flag_diagonal(flag_block: Matrix) -> list[Cx]:
    """Return the diagonal of a flag block, entry by entry."""
    return [flag_block[i][i] for i in range(len(flag_block))]


def mp_adjoint(x: Matrix, povm: Sequence[Matrix]) -> Matrix:
    """Lemma ``lem:top``: ``Lmp+(X) = sum_v <v|X|v> M_v`` for the flag PVM target.

    Eq. ``eq:mpsquasher``'s measure-and-prepare channel. Its content is that
    EVERY POVM squashes to a flag PVM, so "existence is never the difficulty ...
    A squashing relation on its own is therefore WORTH NOTHING: the target
    ``P^flag`` lets the adversary prepare a flag state and FIX BOB'S OUTCOME
    OUTRIGHT." It is the adjoint of the instance an UNCHARACTERISED BRANCH
    gets -- a detector-response mode, a device label or a decoy tag.
    """
    size = len(povm)
    if len(x) != size:
        raise MalformedInputError("the flag observable has one dimension per outcome")
    accumulated = zeros(dimension(povm[0]))
    for index in range(size):
        weight = real_part(x[index][index], "a flag diagonal entry")
        if weight == 0:
            continue
        accumulated = add(accumulated, scale(weight, povm[index]))
    return accumulated


def flags_enough_adjoint(
    x: Matrix, source_povm: Sequence[Matrix], base_dim: int
) -> Matrix:
    """Corollary ``cor:flagsenough``, Eq. ``eq:flagsenough``.

    ``Lambda+(X_{B_0} (+) X_Flag) = sum_v <v|X_Flag|v> (G_v (+) |v><v|)``: the
    output is supported in the flag block, so "THE ``B_0``-PART OF THE
    OBSERVABLE CONTRIBUTES NOTHING". The squashing channel depends on ``G``
    while the target does not, "so ONE TARGET COVERS EVERY DEVICE WITH THE SAME
    FLAG STRUCTURE".

    ``source_povm`` is the family ``{G_v (+) |v><v|}`` on ``B_0 (+) Flag``.
    """
    size = len(source_povm)
    _, flag = split_blocks(x, [base_dim, size])
    accumulated = zeros(base_dim + size)
    for index, entry in enumerate(flag_diagonal(flag)):
        weight = real_part(entry, "a flag diagonal entry")
        if weight == 0:
            continue
        accumulated = add(accumulated, scale(weight, source_povm[index]))
    return accumulated


def instrument_adjoint(x: Matrix, register_element: Matrix) -> Matrix:
    """Theorem ``thm:mixture``: ``I_b+(X) = X (x) N_b``.

    Computed once in that theorem's proof: for ``K = 1 (x) N_b^{1/2}``,
    cyclicity gives ``tr[X tr_D(K rho K)] = tr[K (X (x) 1_D) K rho]``, so
    ``I_b+(X) = X (x) N_b``, "the two factors commuting because they act on
    different tensor factors". NO SQUARE ROOT IS TAKEN HERE: the adjoint is
    stated in terms of ``N_b`` itself, which is what the declaration carries.
    """
    return kron(x, register_element)


def mixture_adjoint(
    x: Matrix,
    block_dims: Sequence[int],
    branch_adjoints: Sequence[Matrix],
    register_povm: Sequence[Matrix],
) -> Matrix:
    """Eq. ``eq:masteradjoint``: ``Lambda+((+)_j X_j) = sum_j I_j+(Lambda_j+(X_j))``.

    With ``I_j+(Y) = Y (x) N_j`` (Theorem ``thm:mixture``) this reads
    ``sum_j Lambda_j+(X_j) (x) N_j``. ``branch_adjoints`` are the per-branch
    pull-backs ``Lambda_j+(X_j)``, already computed by the branch's own closed
    form; ``block_dims`` is only used to check the caller split ``X``
    consistently.
    """
    if len(branch_adjoints) != len(register_povm):
        raise MalformedInputError("one register element per branch is required")
    if sum(block_dims) != len(x):
        raise MalformedInputError("the branch block dimensions do not sum to dim X")
    accumulated: Matrix | None = None
    for pullback, element in zip(branch_adjoints, register_povm, strict=True):
        term = instrument_adjoint(pullback, element)
        accumulated = term if accumulated is None else add(accumulated, term)
    if accumulated is None:
        raise MalformedInputError("a mixture has at least one branch")
    return accumulated


def pinching_adjoint(x: Matrix, projectors: Sequence[Matrix]) -> Matrix:
    """Proposition ``prop:pinching``: ``P_S+ = P_S``, i.e. ``sum_s Pi_s X Pi_s``.

    Self-adjoint because ``tr[X sum_s Pi_s sigma Pi_s]`` equals
    ``tr[(sum_s Pi_s X Pi_s) sigma]``. Corollary ``cor:blockdiag`` (i) is why
    the emitted channel composes it LAST: it fixes every sector-block-diagonal
    operator, so the relation is unchanged, while (ii) makes "``sigma`` is block
    diagonal in every round's sector decomposition" a SOUND constraint for that
    channel -- which is what lets the squashed analysis be restricted to
    block-diagonal states without excluding a reachable one.
    """
    accumulated: Matrix | None = None
    for projector in projectors:
        term = matmul(matmul(projector, x), projector)
        accumulated = term if accumulated is None else add(accumulated, term)
    if accumulated is None:
        raise MalformedInputError("a pinching has at least one sector")
    return accumulated


def is_povm(elements: Sequence[Matrix]) -> bool:
    """Whether ``{elements}`` is a POVM: each Hermitian PSD, summing to ``1``.

    Used where a claim states a POVM hypothesis -- Theorem ``thm:mixture``'s
    ``{N_j}``, a branch family, a declared register. Positivity is decided
    exactly by :func:`certiqs_key.foundations.exact.is_positive_semidefinite`.
    """
    if not elements:
        return False
    size = dimension(elements[0])
    accumulated = zeros(size)
    for element in elements:
        if not is_hermitian(element) or dimension(element) != size:
            return False
        if not is_positive_semidefinite(element):
            return False
        accumulated = add(accumulated, element)
    return equal(accumulated, identity(size))


def adjoint_is_unital(adjoint_of_identity: Matrix, source_dim: int) -> bool:
    """Whether ``Lambda^dagger(1_Q) = 1_B``, the unitality of Eq. ``eq:pairing``.

    "Unitality is trace preservation read through Eq. ``eq:pairing``". It is the
    property every transported-operator statement rests on -- Lemma
    ``lem:obstructions`` (ii)'s last clause is unitality, and Theorem
    ``thm:licence``'s proof uses "ONLY POSITIVITY AND UNITALITY OF AN ATTACK
    CHANNEL'S ADJOINT".
    """
    return equal(adjoint_of_identity, identity(source_dim))


def conjugated(operator: Matrix, isometry: Matrix) -> Matrix:
    """Return ``V^dagger operator V``: the adjoint action of one Kraus operator."""
    return matmul(matmul(conjugate_transpose(isometry), operator), isometry)
