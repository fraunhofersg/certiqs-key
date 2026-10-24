"""PC5 -- D(vii), by exhibition at an empty list and by WITNESS otherwise.

protocol-compiler 0.3.0 Definition ``def:feasible`` (Eq. ``eq:feas``,
Eq. ``eq:feas-modes``), Theorem ``thm:feasibility`` (i)-(ii) with
Eq. ``eq:witness-empty``, and Remark ``rem:nosearch``.

NO SEARCH. NOT NOW, NOT EVER, NOT ANYWHERE IN THIS PACKAGE
==========================================================
Remark ``rem:nosearch`` is the whole design of this module and is worth having
in front of a reader who is about to add a solver:

    "Deciding ``W != empty`` for a general list is a SEMIDEFINITE FEASIBILITY
    PROBLEM, and solving it is neither this module's scope nor necessary: the
    supplier that produced the entries produced them from a reachable-state
    argument and CAN EXHIBIT A REACHABLE STATE. Requiring the witness moves a
    numerical search out of the compiler and turns D(vii) into a check."

So: nothing in this package imports a solver, formulates an SDP, iterates
towards a feasible point, or perturbs a supplied witness to make it pass.
:func:`check_feasibility` tries the default candidate of
Eq. ``eq:witness-empty`` and then the supplied one, VERIFIES each condition by
condition, and refuses. Adding a search here would not merely exceed the
contract; it would make check V7 mean something other than what Theorem
``thm:validator-soundness`` (iii) proves about it.

THE ONE-SIDEDNESS IS DELIBERATE AND ITS REFUSAL HAS A READING
=============================================================
V7 is the one check of the eight that refuses a WELL-FORMED declaration
(Theorem ``thm:validator-soundness`` (iii)). Remark ``rem:completeness`` fixes how the
refusal must be read: ``no_feasibility_witness`` means "I WAS NOT SHOWN A FEASIBLE
STATE", never "there is none", and "it must not be reported to a user as a
defect in the protocol". The supplier has a remedy inside the interface --
supply ``omega^*`` -- and no other check has that character. The refusal detail
this module writes says so in words, so that the reading travels with the
record.

THE FIVE VERIFICATION LEGS ARE THE CONTRACT'S OWN
=================================================
Theorem ``thm:feasibility`` (ii) names them: positivity "by a Hermitian eigenvalue or
Cholesky-type test on a ``d_A d_Q``-dimensional matrix"; the trace; the
off-diagonal block conditions; the marginal condition "by comparing ``d_A^2``
entries" -- TRUSTED MODE ONLY; and each constraint entry evaluated against
``Theta_k`` in the ordering ``bowtie_k``, as a ``d_A x d_A`` Loewner
comparison in trusted mode and as a scalar comparison in untrusted mode,
ACCORDING TO THE EMITTED SOURCE MODE (D(vi)).
:class:`WitnessVerification` carries one verdict per leg, so a refusal names
the leg that decided it and a passing witness is passing for a stated reason.

AND WHAT THE VERIFICATION MUST NOT DO. It must not normalize a subnormalized
witness before testing it, and it must not repair one: the conventions
(``fail_closed``) -- "no default value is ever substituted for a missing
datum". Definition ``def:feasible``'s set is a set of NORMALIZED states and the
consuming engine minimizes over it.

AND THE LEGS ARE RECORDED WHERE THEY ARE DECIDED
================================================
The ``gate_report`` output row asks for "the decisions check V7 takes on the
candidate it verified -- Hermiticity and positive semidefiniteness PER BLOCK
and the trace ... together with the marginal equality ``omega_A = tau_A`` in
trusted mode and ONE LOEWNER OR SCALAR LEG PER CONSTRAINT ENTRY", each keyed
by ``(source, element, block)``
(:mod:`certiqs_key.protocol_compiler.transcript`).
:attr:`WitnessVerification.predicates` is that record and
:func:`verify_witness` fills it, which is the only place it can be filled
honestly: the four verdict fields beside it are AGGREGATES -- ``positive`` is
one boolean over every block and ``constraints`` one over every entry -- so a
consumer holding only those cannot key a leg by the block or the entry that
decided it, and re-deciding the predicates one module up would pay for a
second exact positivity test per block and put a second decision site on the
same data.

``element`` IS THE CANDIDATE, AND THE CALLER SAYS WHICH, because the row asks
for the decisions on "the candidate it VERIFIED" and this function verifies
whichever it is handed: :data:`DEFAULT_CANDIDATE` for the one
Eq. ``eq:witness-empty`` exhibits and :data:`SUPPLIED_WITNESS` for a supplied
``omega^*``. :func:`check_feasibility` always says which; a caller that does
not -- :func:`in_feasible_set`, which discards the record -- gets the
UNQUALIFIED name rather than a claim about which candidate it was.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from fractions import Fraction
from typing import Final

from certiqs_key.domain.constraints import ConstraintEntry, Relation
from certiqs_key.foundations.blocks import BlockOperator, JointBlockOperator
from certiqs_key.foundations.errors import HypothesisError
from certiqs_key.foundations.exact import (
    Cx,
    Matrix,
    add,
    equal,
    identity,
    is_hermitian,
    is_positive_semidefinite,
    kron,
    loewner_ge,
    matmul,
    partial_trace_second,
    real_part,
    scale,
    trace,
    zeros,
)
from certiqs_key.protocol_compiler.declaration import CandidateDeclaration
from certiqs_key.protocol_compiler.reasons import Refusal, RefusalReason
from certiqs_key.protocol_compiler.transcript import (
    PredicateOutcome,
    PredicateSource,
)

__all__ = [
    "DEFAULT_CANDIDATE",
    "SUPPLIED_WITNESS",
    "WITNESS_UNQUALIFIED",
    "FeasibilityCheck",
    "WitnessVerification",
    "check_feasibility",
    "constraint_value",
    "default_witness",
    "factor_sector_indices",
    "general_constraint_value",
    "in_feasible_set",
    "party_local_rows",
    "scoped_contraction",
    "trusted_rhs",
    "verify_witness",
]

#: HOW THE TRANSCRIPT NAMES THE CANDIDATE A LEG WAS DECIDED ON. The row asks
#: for the decisions "on the candidate it VERIFIED", and check V7 may verify
#: two: the default one of Eq. ``eq:witness-empty``, always tried first, and a
#: supplied ``omega^*``. WHICH ONE IS PART OF THE KEY -- Theorem ``thm:feasibility``
#: (ii)'s legs are decided on a STATE, and two states give two answers -- so
#: the element names it rather than leaving a reader to infer it from the
#: verdict.
DEFAULT_CANDIDATE: Final[str] = "omega* (default candidate)"
SUPPLIED_WITNESS: Final[str] = "omega* (supplied witness)"

#: What a caller that does not say gets. It is NOT one of the two above: a
#: record labelled "default candidate" for a state that was supplied would be
#: a false datum, and the honest answer where nobody said is the unqualified
#: name (:func:`in_feasible_set` is the one such caller, and it discards the
#: record entirely).
WITNESS_UNQUALIFIED: Final[str] = "omega*"


def default_witness(declaration: CandidateDeclaration) -> JointBlockOperator:
    """Return ``omega^*`` of Eq. ``eq:witness-empty``, AS A BLOCK LIST.

    ``omega^{*(s)} = tau_A (x) 1_{Q_s}/d_Q`` in trusted-source mode and
    ``(1_A/d_A) (x) 1_{Q_s}/d_Q`` in untrusted-source mode, one array per
    sector, with the factors in the order the ``subsystem_order`` convention
    declares. Theorem ``thm:feasibility`` (i) proves this state lies in ``W`` whenever
    the constraint list is empty, and its hypothesis is D(i)-D(iii) alone --
    nothing about emission -- which is what lets Theorem ``thm:validator-soundness`` (i)
    use it on a candidate.

    THIS IS NOT A SUBSTITUTED DEFAULT. It is a state the compiler EXHIBITS to
    discharge a proof obligation, not a datum it supplies in place of a missing
    one; contrast Remark ``rem:notfallback``, where ``tau_A = 1_A / d_A`` is
    never substituted for ``nomarg`` because it is a strictly stronger claim.

    ITS ENTRIES NEED NOT BE BINARY64 AND NOTHING REQUIRES THEM TO BE: "``1/d_Q``
    is a rational, DYADIC ONLY WHEN ``d_Q`` IS A POWER OF TWO, and ``omega^*``
    is NEVER EMITTED. It is formed and decided in exact rational arithmetic on
    the declared dyadic entries -- which is exactly what the platform's exact
    island is for -- so every predicate above is DECIDED, NOT APPROXIMATED, and
    NO REPRESENTABILITY QUESTION ARISES for an object no consumer ever sees."
    """
    sectors = declaration.sectors
    q_dim = sectors.total_dim
    if declaration.is_general_format:
        # eq:witness-general: tau_A^(t) (x) 1_{Q_s}/d_Q in trusted-source mode and
        # 1_{A_t}/d_A (x) 1_{Q_s}/d_Q in untrusted mode, ONE ARRAY PER JOINT
        # SECTOR. At |T| = 1 and one measured factor it is eq:witness-empty, block
        # for block, which is what thm:feasibility's general paragraph says.
        alice_sectors = declaration.alice_sectors
        marginal_blocks = declaration.marginal_blocks
        alice_side: list[Matrix] = []
        for position, alice_dim in enumerate(alice_sectors.dims):
            if marginal_blocks is None:
                alice_side.append(
                    scale(Fraction(1, declaration.alice_dim), identity(alice_dim))
                )
            else:
                alice_side.append(marginal_blocks.blocks[position])
        return JointBlockOperator.of(
            sectors,
            alice_sectors,
            [
                kron(block, scale(Fraction(1, q_dim), identity(dim)))
                for block in alice_side
                for dim in sectors.dims
            ],
        )
    marginal = declaration.alice_marginal
    if marginal is None:
        alice_dim = declaration.alice_dim
        alice = scale(Fraction(1, alice_dim), identity(alice_dim))
    else:
        alice = marginal
    return JointBlockOperator.of(
        sectors,
        declaration.alice_dim,
        [kron(alice, scale(Fraction(1, q_dim), identity(dim))) for dim in sectors.dims],
    )


def factor_sector_indices(counts: Sequence[int], flat: int) -> tuple[int, ...]:
    """Return the per-factor sector positions behind one PRODUCT sector position.

    (DX1): ``S = prod_f S^f`` "ordered with the LAST FACTOR FASTEST", so the
    product position is the mixed-radix numeral over the factors' sector counts in
    that order and this is its digits. With one factor it is that factor's own
    position, which is the accepted format.

    IT IS ARITHMETIC ON THE DERIVED ORDER AND NOT A DECLARED DATUM: "the product
    sector map, its order, the product alphabet and the joint sectors are DERIVED
    from that list ... and are declared, formed and emitted by no one".
    """
    digits: list[int] = []
    remaining = flat
    for stride in reversed(counts):
        digits.append(remaining % stride)
        remaining //= stride
    return tuple(reversed(digits))


def _offset(
    strides: Sequence[int], indices: Sequence[int], values: Sequence[int]
) -> int:
    """Return the flat ``Q`` offset of an assignment to some of the factors.

    The mixed-radix contribution of the factors ``indices`` at the values
    ``values``, which is what makes the two halves of one index -- the traced
    factors' and the free ones' -- addable rather than re-derived twice.
    """
    return sum(
        strides[index] * value
        for index, value in zip(indices, values, strict=True)
    )


def scoped_contraction(
    block: Matrix,
    alice_dim: int,
    factor_dims: Sequence[int],
    scope: int,
    operator: Matrix,
    *,
    traced: Sequence[int],
) -> Matrix:
    """Contract one joint block against ``O_k`` ON ITS OWN TENSOR FACTOR.

    ``tr_{traced}[(1 (x) O_k (x) 1) omega^{(t,s)}]``, computed INDEX BY INDEX and
    WITHOUT FORMING THE LIFTED OPERATOR. The interface's
    ``constraint_entries.scope_and_tag`` row is explicit: "IT NEVER FORMS THE
    LIFTED OPERATOR ``1 (x) O_k (x) 1`` as a datum, AT ANY STEP, V7'S LEGS
    INCLUDED: a constraint value is computed by contracting a joint block against
    ``O_k``'s block on its own tensor factor" (``thm:feasibility`` (ii), the general
    format). So no Kronecker product is formed here and none may be.

    THE TWO LINES OF ``eq:feas-general`` THAT NEED IT ARE ONE CONTRACTION, and
    ``traced`` is the whole difference: ALL measured factors for an untagged
    entry's value, which leaves an operator on ``A_t``, and THE SCOPED FACTOR
    ALONE for a ``party_local`` entry, which leaves one on
    ``A_t (x) Q_{f^c,s_{f^c}}``. Deriving the index arithmetic once is what keeps
    the two readings one statement.

    THE ARITHMETIC. With ``Z`` on ``A (x) B``, ``(tr_B[(1 (x) N) rho])[a][a'] =
    sum_q sum_{q''} N[q][q''] rho[(a, q'')][(a', q)]``; ``N`` is ``O_k`` on the
    scoped factor and the identity on the other traced ones, so ``q''`` agrees with
    ``q`` off the scope and the coefficient is ``O_k[q_k][q''_k]``. The block index
    is ``a * D + q`` with ``q`` the mixed-radix numeral over ``factor_dims``, the
    last factor fastest, which is the ``A``-first, ``Q``-fastest order
    :meth:`~certiqs_key.foundations.blocks.JointBlockOperator.dense` places a block by.
    """
    traced_set = frozenset(traced)
    if scope not in traced_set:
        raise HypothesisError(
            "the scoped factor is traced out by both lines of eq:feas-general; "
            f"factor {scope} is not in the traced list {list(traced)}"
        )
    strides: list[int] = []
    running = 1
    for dim in reversed(factor_dims):
        strides.append(running)
        running *= dim
    strides.reverse()
    total_q = running
    free = [index for index in range(len(factor_dims)) if index not in traced_set]
    free_dims = [factor_dims[index] for index in free]
    free_total = 1
    for dim in free_dims:
        free_total *= dim
    size = alice_dim * free_total
    rows = [list(row) for row in zeros(size, size)]
    traced_order = sorted(traced_set)
    traced_dims = [factor_dims[index] for index in traced_order]

    def assignments(dims: Sequence[int]) -> list[tuple[int, ...]]:
        """Return every index tuple over ``dims``, the last entry fastest."""
        out: list[tuple[int, ...]] = [()]
        for dim in dims:
            out = [(*prefix, value) for prefix in out for value in range(dim)]
        return out

    free_assignments = assignments(free_dims)
    traced_assignments = assignments(traced_dims)
    scope_position = traced_order.index(scope)
    zero = Cx(Fraction(0), Fraction(0))
    for alice in range(alice_dim):
        for left_index, left_free in enumerate(free_assignments):
            for alice_prime in range(alice_dim):
                for right_index, right_free in enumerate(free_assignments):
                    total = zero
                    left_free_offset = _offset(strides, free, left_free)
                    right_free_offset = _offset(strides, free, right_free)
                    for right_traced in traced_assignments:
                        # THE RIGHT INDEX carries the traced assignment as it is;
                        # THE LEFT ONE carries it with the scoped factor replaced
                        # by j, which is the only index O_k's entry couples.
                        right_q = (
                            _offset(strides, traced_order, right_traced)
                            + right_free_offset
                        )
                        scope_value = right_traced[scope_position]
                        for j in range(factor_dims[scope]):
                            coefficient = operator[scope_value][j]
                            if coefficient == zero:
                                continue
                            left_traced = list(right_traced)
                            left_traced[scope_position] = j
                            left_q = (
                                _offset(strides, traced_order, left_traced)
                                + left_free_offset
                            )
                            total = total + coefficient * block[
                                alice * total_q + left_q
                            ][alice_prime * total_q + right_q]
                    rows[alice * free_total + left_index][
                        alice_prime * free_total + right_index
                    ] = total
    return tuple(tuple(row) for row in rows)


def trusted_rhs(declaration: CandidateDeclaration, entry: ConstraintEntry) -> Matrix:
    """Return the trusted-mode right-hand side of one entry, PER ITS TAG.

    Definition ``def:homog`` (a): for a ``homogeneous`` entry "the right-hand
    side it denotes is then CONSTRUCTED as ``Theta_k := c_k tau_A`` from the
    declared ``c_k`` and the declared ``tau_A``"; for a ``general`` entry it is
    the declared ``Theta_k``. Theorem ``thm:feasibility`` (ii): "the compiler forms
    ``c_k tau_A`` HERE IN ORDER TO TEST the candidate, and DOES NOT EMIT IT --
    the consumer constructs its own from the same declared ``c_k`` and
    ``tau_A``, SO THE TWO FORM THE SAME MATRIX."
    """
    marginal = declaration.alice_marginal
    if marginal is None:
        raise HypothesisError(
            "a trusted-mode right-hand side is constructed from the declared "
            "tau_A; the marginal slot holds nomarg"
        )
    rhs = entry.rhs
    if isinstance(rhs, Fraction):
        return scale(rhs, marginal)
    return rhs.dense() if isinstance(rhs, BlockOperator) else rhs


def constraint_value(
    declaration: CandidateDeclaration,
    entry: ConstraintEntry,
    state: JointBlockOperator,
) -> Matrix | Fraction:
    """Return the left-hand side of one entry of Eq. ``eq:feas-modes``, PER BLOCK.

    Theorem ``thm:feasibility`` (ii): in trusted mode
    ``sum_s tr_{Q_s}[(1_A (x) O^_k^(s)) omega^(s)]``, "A MATRIX OF SIZE ``d_A``
    ASSEMBLED FROM ``|S|`` BLOCK TERMS"; in untrusted mode the scalar
    ``sum_s tr[(1_A (x) O^_k^(s)) omega^(s)]``. WHICH ONE IS DECIDED BY THE
    EMITTED SOURCE MODE and not by the type of the right-hand side, which is
    what D(vi) types and check V6 tests. NO ARRAY OF DIMENSION ``d_A d_Q`` IS
    FORMED.

    Remark ``rem:wellposed`` is why Hermiticity of ``O^_k`` must already have
    been checked: without it the trusted left-hand side need not be Hermitian
    and the Loewner comparison has no truth value, while the untrusted one need
    not be real. Reaching this function with a non-Hermitian operator raises.
    """
    if not entry.operator.is_hermitian():
        raise HypothesisError(
            "Eq. eq:feas-modes is well posed only for a Hermitian O^_k (Remark "
            "rem:wellposed); check V3 refuses a non-Hermitian one, and it must "
            "run before this evaluation"
        )
    alice_dim = declaration.alice_dim
    if declaration.is_trusted_mode:
        assembled: Matrix = zeros(alice_dim, alice_dim)
        for position, block in enumerate(state.blocks):
            dim = state.sector_map.dims[position]
            joint = kron(identity(alice_dim), entry.operator.blocks[position])
            assembled = add(
                assembled, partial_trace_second(matmul(joint, block), alice_dim, dim)
            )
        return assembled
    total = Cx(Fraction(0), Fraction(0))
    for position, block in enumerate(state.blocks):
        joint = kron(identity(alice_dim), entry.operator.blocks[position])
        total = total + trace(matmul(joint, block))
    return real_part(total, "the untrusted constraint value tr[(1 (x) O) omega]")


def _entry_holds(
    declaration: CandidateDeclaration,
    entry: ConstraintEntry,
    value: Matrix | Fraction,
) -> bool:
    """Whether one entry of Eq. ``eq:feas-modes`` holds at a computed value.

    The two lines of Eq. ``eq:feas-modes`` are told apart by the EMITTED SOURCE
    MODE, which :func:`constraint_value` read; a right-hand side of a type the
    mode does not admit is what check V6 refuses, and reaching it here is a
    hypothesis violation rather than a false entry.

    IN TRUSTED MODE THE RIGHT-HAND SIDE IS CONSTRUCTED FROM THE TAG, by
    :func:`trusted_rhs`: ``c_k tau_A`` for a ``homogeneous`` entry and the
    declared ``Theta_k`` for a ``general`` one (Definition ``def:homog`` (a)).
    That construction is 0.3.0's, and it is the whole reason a scalar
    right-hand side is admissible in trusted mode at all.
    """
    rhs = entry.rhs
    if isinstance(value, Fraction):
        if not isinstance(rhs, Fraction):
            raise HypothesisError(
                "the untrusted line of Eq. eq:feas-modes compares reals; this "
                "entry carries an operator right-hand side, which V6 refuses"
            )
        if entry.relation is Relation.GE:
            return value >= rhs
        if entry.relation is Relation.LE:
            return value <= rhs
        return value == rhs
    constructed = trusted_rhs(declaration, entry)
    if entry.relation is Relation.GE:
        return loewner_ge(value, constructed)
    if entry.relation is Relation.LE:
        return loewner_ge(constructed, value)
    return equal(value, constructed)


@dataclass(frozen=True)
class WitnessVerification:
    """The five legs of Theorem ``thm:feasibility`` (ii), one verdict each.

    THE SECTOR LEG OF 0.1.4 IS ABSENT: with ``omega`` presented as a block
    list "the off-block conjunct HOLDS BY THE PRESENTATION and there is nothing
    to verify" (Theorem ``thm:feasibility`` (i)), so there are FOUR legs and not five.

    ``marginal`` is ``True`` in untrusted-source mode in the sense "no
    condition to violate": Definition ``def:feasible`` imposes no marginal
    condition there beyond ``tr omega = 1``, which the trace leg already
    decided.
    """

    positive: bool
    trace_one: bool
    marginal: bool
    constraints: bool
    constraint_values: tuple[Matrix | Fraction, ...]
    #: THE FOUR LEGS AS THE ``gate_report`` ROW KEYS THEM: (H) and (P) PER
    #: BLOCK, the trace, the marginal equality where it is decided at all, and
    #: one leg per constraint entry -- each with the candidate as its element
    #: and, for a per-block leg, the block. The fields above are the
    #: aggregates a refusal reads; this is the record the row asks for, and the
    #: module docstring says why it is filled here. A DEFAULTED FIELD, so that
    #: every existing construction site stays valid and an unfilled record is a
    #: visible ``()``.
    predicates: tuple[PredicateOutcome, ...] = ()

    @property
    def passes(self) -> bool:
        """Whether every leg passed, i.e. the witness lies in ``W``."""
        return self.positive and self.trace_one and self.marginal and self.constraints

    def failing_legs(self) -> tuple[str, ...]:
        """Return the names of the legs that failed, in the theorem's order."""
        verdicts = (
            ("positivity", self.positive),
            ("trace", self.trace_one),
            ("marginal", self.marginal),
            ("constraints", self.constraints),
        )
        return tuple(name for name, passed in verdicts if not passed)


def _entry_leg(declaration: CandidateDeclaration, entry: ConstraintEntry) -> str:
    """Return the name of the leg Eq. ``eq:feas-modes`` takes for one entry.

    FOUR SPELLINGS, and the two axes are the two the contract names: WHICH LINE
    of Eq. ``eq:feas-modes`` is read is decided by the EMITTED SOURCE MODE -- a
    ``d_A x d_A`` Loewner comparison in trusted mode, a scalar comparison in
    untrusted mode -- and whether the comparison is an ordering or an equality
    is decided by ``bowtie_k``. The row keys by that distinction itself ("ONE
    Loewner or scalar leg per constraint entry, TWO for an entry whose relation
    is ``=``"), so naming the leg per relation kind records which predicate was
    decided and not a datum about the entry.

    AN ``=`` ENTRY RECORDS ONE OUTCOME AND NOT TWO. Theorem ``thm:feasibility`` (ii)
    counts two legs there and Eq. ``eq:predcount`` counts them that way; the
    code decides ONE exact entrywise equality, which for Hermitian operands is
    equivalent to the conjunction of the two Loewner legs. Recording two
    outcomes would report two decisions where one was taken, and deciding two
    ``loewner_ge`` comparisons to make the count come out would add an exact
    elimination per entry for nothing.
    """
    kind = "Loewner" if declaration.is_trusted_mode else "scalar"
    if entry.relation is Relation.EQ:
        return f"the {kind} equality leg of Eq. eq:feas-modes"
    return f"the {kind} leg of Eq. eq:feas-modes"


def verify_witness(
    declaration: CandidateDeclaration,
    state: JointBlockOperator,
    *,
    element: str = WITNESS_UNQUALIFIED,
) -> WitnessVerification:
    """Verify a candidate witness against every condition of ``def:feasible``.

    Finitely many arithmetic operations on the declared data, exactly as
    Theorem ``thm:feasibility`` (ii) enumerates them, AND PER BLOCK -- "no array of
    dimension ``d_A d_Q`` is formed at any point". Every leg is evaluated even
    when an earlier one failed, so that a refusal can name the leg that decided
    it without an implementation-defined short circuit deciding which.

    THERE IS NO SECTOR LEG. Theorem ``thm:feasibility`` (i):
    "``omega^*`` is presented AS A LIST, one array on ``A Q_s`` per ``s``, so
    THE OFF-BLOCK CONJUNCT HOLDS BY THE PRESENTATION AND THERE IS NOTHING TO
    VERIFY". Where a SUPPLIED witness's map is compared is V7 branch (c), and
    it is compared there before this function is reached.

    EVERY LEG IS ALSO RECORDED, keyed as the ``gate_report`` row keys it (the
    module docstring says why here and not one module up). The two conjunctions
    are unrolled into the per-block loops they are -- SAME DECISIONS, SAME
    ORDER, SAME SHORT CIRCUIT, so the aggregate verdicts and the refusal they
    feed are unchanged -- because an aggregate cannot be keyed by the block that
    decided it. ``element`` is the candidate; see :data:`DEFAULT_CANDIDATE`.
    """
    if declaration.is_general_format:
        return _verify_witness_general(declaration, state, element=element)
    alice_dim = declaration.alice_dim
    if state.alice_dim != alice_dim:
        raise HypothesisError(
            "Definition def:feasible is stated on Pos(A Q); the supplied block "
            f"list is on an A of dimension {state.alice_dim}, not {alice_dim}"
        )
    predicates: list[PredicateOutcome] = []

    def record(
        predicate: str,
        outcome: bool,
        *,
        on: str | None = None,
        block: str | None = None,
        index: int | None = None,
    ) -> None:
        """Record one leg of Theorem ``thm:feasibility`` (ii)."""
        predicates.append(
            PredicateOutcome(
                source=PredicateSource.V7,
                predicate=predicate,
                element=element if on is None else on,
                block=block,
                outcome=outcome,
                first_failure_index=None if outcome else index,
            )
        )

    blocks = state.sector_map.labels
    # (H) AND (P) PER BLOCK, short-circuiting exactly as ``all()`` did: a block
    # after the first failure is NOT decided and carries no entry, and the
    # positivity loop is not entered at all on a non-Hermitian state -- which
    # is the ``hermitian and ...`` the aggregate spelled.
    hermitian = True
    for position, block in enumerate(state.blocks):
        hermitian = is_hermitian(block)
        record("(H)", hermitian, block=blocks[position], index=position + 1)
        if not hermitian:
            break
    positive = hermitian
    if hermitian:
        for position, block in enumerate(state.blocks):
            positive = is_positive_semidefinite(block)
            record("(P)", positive, block=blocks[position], index=position + 1)
            if not positive:
                break

    # "One trace decision, tr omega = 1 on the scalar sum_s tr omega^(s), a sum
    # of |S| block traces ACCUMULATED IN THE DECLARED ORDER."
    running = Cx(Fraction(0), Fraction(0))
    for block in state.blocks:
        running = running + trace(block)
    trace_one = running == Cx(Fraction(1), Fraction(0))
    record("tr omega = 1", trace_one)

    marginal = True
    declared = declaration.alice_marginal
    if declared is not None:
        # "Form omega_A = sum_s tr_{Q_s} omega^(s), which is |S| partial traces
        # onto A and |S| - 1 additions of d_A^2 entries, then omega_A = tau_A."
        assembled: Matrix = zeros(alice_dim, alice_dim)
        for position, block in enumerate(state.blocks):
            assembled = add(
                assembled,
                partial_trace_second(block, alice_dim, state.sector_map.dims[position]),
            )
        marginal = equal(assembled, declared)
        # THE ELEMENT IS tau_A AND NOT THE CANDIDATE: the row names "the
        # marginal equality omega_A = tau_A", and the declared marginal is the
        # side of it a supplier can act on. IN UNTRUSTED MODE THERE IS NO SUCH
        # DECISION AND NONE IS RECORDED -- Definition def:feasible imposes no
        # marginal condition there, and ``marginal`` stays ``True`` in the sense
        # "no condition to violate".
        record("omega_A = tau_A", marginal, on="tau_A")

    values: list[Matrix | Fraction] = []
    constraints = True
    if hermitian:
        for index, entry in enumerate(declaration.constraint_list, start=1):
            value = constraint_value(declaration, entry, state)
            values.append(value)
            holds = _entry_holds(declaration, entry, value)
            # EVERY ENTRY IS DECIDED AND EVERY ENTRY IS RECORDED: this loop
            # does not stop at the first failure, so each failing entry carries
            # its own entry index and the FIRST of them is the first failure.
            record(
                _entry_leg(declaration, entry),
                holds,
                on=f"CList[{index}]",
                index=index,
            )
            if not holds:
                constraints = False
    else:
        # A non-Hermitian omega makes every comparison of Eq. eq:feas-modes
        # ill-posed for the same reason Remark rem:wellposed gives; the
        # positivity leg has already refused it, and no constraint value is
        # invented for a state the set does not contain. NOTHING IS RECORDED
        # FOR THE ENTRIES EITHER: an outcome here would report a comparison
        # that was never made.
        constraints = False

    return WitnessVerification(
        positive=positive,
        trace_one=trace_one,
        marginal=marginal,
        constraints=constraints,
        constraint_values=tuple(values),
        predicates=tuple(predicates),
    )


def _verify_witness_general(
    declaration: CandidateDeclaration,
    state: JointBlockOperator,
    *,
    element: str,
) -> WitnessVerification:
    """Verify a candidate against ``eq:feas-general``, PER JOINT BLOCK.

    ``thm:feasibility`` (ii) in the general format: "the verification is the
    per-JOINT-block one listed in the proof, which forms no array larger than one joint
    block". The four legs are the four the accepted reading has, read over the joint
    sectors: (H) and (P) per joint block; ``sum_{(t,s)} tr omega^{(t,s)} = 1``;
    the marginal equality PER ALICE SECTOR in trusted mode; and per entry either
    ``|T|`` Loewner comparisons, one comparison of real numbers in untrusted mode,
    or, for a ``party_local`` entry, one Loewner comparison per pair of an Alice
    sector and a block of the unscoped factors.

    AT ``|T| = 1``, ONE MEASURED FACTOR AND NO SCOPED ENTRY THIS IS THE ACCEPTED
    VERIFICATION, leg for leg: the joint list is the per-``Q``-sector list, the
    marginal loop runs once, and the entry legs are ``eq:feas-modes``'s two lines.
    """
    alice_sectors = declaration.alice_sectors
    predicates: list[PredicateOutcome] = []

    def record(
        predicate: str,
        outcome: bool,
        *,
        on: str | None = None,
        block: str | None = None,
        index: int | None = None,
    ) -> None:
        """Record one leg of ``thm:feasibility`` (ii) in its general-format reading."""
        predicates.append(
            PredicateOutcome(
                source=PredicateSource.V7,
                predicate=predicate,
                element=element if on is None else on,
                block=block,
                outcome=outcome,
                first_failure_index=None if outcome else index,
            )
        )

    joint = state.joint_sectors().labels
    hermitian = True
    for position, block in enumerate(state.blocks):
        hermitian = is_hermitian(block)
        record("(H)", hermitian, block=joint[position], index=position + 1)
        if not hermitian:
            break
    positive = hermitian
    if hermitian:
        for position, block in enumerate(state.blocks):
            positive = is_positive_semidefinite(block)
            record("(P)", positive, block=joint[position], index=position + 1)
            if not positive:
                break

    running = Cx(Fraction(0), Fraction(0))
    for block in state.blocks:
        running = running + trace(block)
    trace_one = running == Cx(Fraction(1), Fraction(0))
    record("tr omega = 1", trace_one)

    marginal = True
    declared = declaration.marginal_blocks
    if declared is not None:
        for alice_position in range(alice_sectors.count):
            alice_dim = alice_sectors.dims[alice_position]
            assembled: Matrix = zeros(alice_dim, alice_dim)
            for sector_position, sector_dim in enumerate(declaration.sectors.dims):
                assembled = add(
                    assembled,
                    partial_trace_second(
                        state.block(alice_position, sector_position),
                        alice_dim,
                        sector_dim,
                    ),
                )
            holds = equal(assembled, declared.blocks[alice_position])
            record(
                "omega_A^(t) = tau_A^(t)",
                holds,
                on="tau_A",
                block=alice_sectors.labels[alice_position],
                index=alice_position + 1,
            )
            marginal = marginal and holds

    values: list[Matrix | Fraction] = []
    constraints = True
    if hermitian:
        for index, entry in enumerate(declaration.constraint_list, start=1):
            if not entry.operator.is_hermitian():
                raise HypothesisError(
                    "Eq. eq:feas-general is well posed only for a Hermitian O^_k "
                    "(Remark rem:wellposed); check V3 refuses a non-Hermitian one"
                )
            holds = True
            if entry.is_party_local:
                for alice_position in range(alice_sectors.count):
                    for row_label, row in party_local_rows(
                        declaration, entry, state, alice_position
                    ):
                        leg = _general_entry_holds(entry, row, None)
                        record(
                            "the party_local line of eq:feas-general",
                            leg,
                            on=f"CList[{index}]",
                            block=(
                                f"{alice_sectors.labels[alice_position]}"
                                f"{'|' + row_label if row_label else ''}"
                            ),
                            index=index,
                        )
                        holds = holds and leg
            elif declaration.is_trusted_mode:
                assert declared is not None
                for alice_position in range(alice_sectors.count):
                    operator = general_constraint_value(
                        declaration, entry, state, alice_position
                    )
                    assert not isinstance(operator, Fraction)
                    values.append(operator)
                    rhs = _general_trusted_rhs(
                        entry, declared.blocks[alice_position], alice_position
                    )
                    leg = _general_entry_holds(entry, operator, rhs)
                    record(
                        "the Loewner leg of eq:feas-general",
                        leg,
                        on=f"CList[{index}]",
                        block=alice_sectors.labels[alice_position],
                        index=index,
                    )
                    holds = holds and leg
            else:
                total = Fraction(0)
                for alice_position in range(alice_sectors.count):
                    scalar_value = general_constraint_value(
                        declaration, entry, state, alice_position
                    )
                    assert isinstance(scalar_value, Fraction)
                    total += scalar_value
                values.append(total)
                holds = _general_entry_holds(entry, total, None)
                record(
                    "the scalar leg of eq:feas-general",
                    holds,
                    on=f"CList[{index}]",
                    index=index,
                )
            if not holds:
                constraints = False
    else:
        constraints = False
    return WitnessVerification(
        positive=positive,
        trace_one=trace_one,
        marginal=marginal,
        constraints=constraints,
        constraint_values=tuple(values),
        predicates=tuple(predicates),
    )


def _general_trusted_rhs(
    entry: ConstraintEntry, marginal_block: Matrix, alice_position: int
) -> Matrix:
    """Return ``Theta^(t)_k`` of ``eq:feas-general``'s third line at one sector.

    ``c_k tau_A^(t)`` for a ``homogeneous`` entry, CONSTRUCTED here in order to
    test the candidate and emitted by nobody, and the declared block of a
    ``general`` one -- which (DX2) types as a block list along ``T``.
    """
    rhs = entry.rhs
    if isinstance(rhs, Fraction):
        return scale(rhs, marginal_block)
    if isinstance(rhs, BlockOperator):
        return rhs.blocks[alice_position]
    return rhs


def _general_entry_holds(
    entry: ConstraintEntry, value: Matrix | Fraction, rhs: Matrix | None
) -> bool:
    """Whether one row of ``eq:feas-general`` holds at a computed value.

    ``rhs`` is the right-hand side where the line has an operator one, and ``None``
    where the line compares against a datum -- the scalar ``c_k`` of the fourth
    line, read off the entry, and the ``0`` of the party-local line, which is why
    the comparison there is with the zero matrix of the row's own size.
    """
    if isinstance(value, Fraction):
        constant = entry.rhs
        if not isinstance(constant, Fraction):  # pragma: no cover - V6 refuses it
            raise HypothesisError(
                "the scalar line of eq:feas-general compares reals; this entry "
                "carries an operator right-hand side, which V6 refuses"
            )
        if entry.relation is Relation.GE:
            return value >= constant
        if entry.relation is Relation.LE:
            return value <= constant
        return value == constant
    against = zeros(len(value), len(value)) if rhs is None else rhs
    if entry.relation is Relation.GE:
        return loewner_ge(value, against)
    if entry.relation is Relation.LE:
        return loewner_ge(against, value)
    return equal(value, against)


def general_constraint_value(
    declaration: CandidateDeclaration,
    entry: ConstraintEntry,
    state: JointBlockOperator,
    alice_position: int,
) -> Matrix | Fraction:
    """Return one entry's value at one Alice sector, the general format's reading.

    The third and fourth lines of ``eq:feas-general``: the operator on ``A_t``
    obtained by tracing out all of ``Q_s`` and summing over ``s``, in trusted-source
    mode, and the real number obtained by tracing everything, in untrusted mode.

    THE LIFTED OPERATOR IS NOT FORMED. Each ``s``-block is contracted against
    ``hat O_k``'s block on the scoped factor by :func:`scoped_contraction`, whose
    docstring carries the rule and the arithmetic. Which ``s_f`` the entry's
    operator is read at is (DX1)'s digit decomposition of the product sector
    position, so the operator's own sector order is the one its map declares.
    """
    factors = declaration.measured_factors
    counts = [factor.sectors.count for factor in factors]
    scope = declaration.measured_factor_position(entry.scope)
    alice_dim = declaration.alice_sectors.dims[alice_position]
    assembled: Matrix = zeros(alice_dim, alice_dim)
    for sector_position in range(declaration.sectors.count):
        digits = factor_sector_indices(counts, sector_position)
        operator = entry.operator.blocks[digits[scope]]
        assembled = add(
            assembled,
            scoped_contraction(
                state.block(alice_position, sector_position),
                alice_dim,
                [factor.sectors.dims[digit] for factor, digit in zip(
                    factors, digits, strict=True
                )],
                scope,
                operator,
                traced=tuple(range(len(factors))),
            ),
        )
    if declaration.is_trusted_mode:
        return assembled
    return real_part(
        trace(assembled), "the untrusted constraint value tr[(1 (x) O) omega]"
    )


def party_local_rows(
    declaration: CandidateDeclaration,
    entry: ConstraintEntry,
    state: JointBlockOperator,
    alice_position: int,
) -> tuple[tuple[str, Matrix], ...]:
    """Return one ROW per block of the unscoped factors, the party-local line.

    The last line of ``eq:feas-general``: for each ``(t, s_{f^c})`` the operator
    ``sum_{s_f} tr_{Q_{f,s_f}}[(1 (x) (hat O^{(s_f)}_k - c_k 1)) omega^{(t,(s_{f^c},
    s_f))}]`` on ``H(A_t) (x) H(Q_{f^c,s_{f^c}})``, compared with ``0``. Each row
    carries the label of the unscoped blocks it belongs to, so a refusal says which.

    WITH ONE MEASURED FACTOR THERE IS ONE ROW per Alice sector and it is
    ``tr_Q[(1_A (x) hat O_k) omega] bowtie_k c_k omega_A`` read on ``A_t``, which is
    what ``def:homog``'s one-factor case states.

    ``c_k 1`` IS SUBTRACTED FROM THE SCOPED BLOCK AND NOT FROM THE VALUE, which is
    how the line is written: the subtraction happens on an array of one factor
    block's size, and the right-hand side is then the datum ``0``.
    """
    factors = declaration.measured_factors
    counts = [factor.sectors.count for factor in factors]
    scope = declaration.measured_factor_position(entry.scope)
    constant = entry.rhs
    if not isinstance(constant, Fraction):
        raise HypothesisError(
            "a party_local entry declares a REAL SCALAR c_k (def:homog, the "
            "party-local form); check V6 refuses any other datum beside that tag"
        )
    alice_dim = declaration.alice_sectors.dims[alice_position]
    rows: dict[str, Matrix] = {}
    for sector_position in range(declaration.sectors.count):
        digits = factor_sector_indices(counts, sector_position)
        dims = [
            factor.sectors.dims[digit]
            for factor, digit in zip(factors, digits, strict=True)
        ]
        scoped = entry.operator.blocks[digits[scope]]
        shifted = add(scoped, scale(-constant, identity(dims[scope])))
        row_label = "|".join(
            factor.sectors.labels[digit]
            for index, (factor, digit) in enumerate(zip(factors, digits, strict=True))
            if index != scope
        )
        contribution = scoped_contraction(
            state.block(alice_position, sector_position),
            alice_dim,
            dims,
            scope,
            shifted,
            traced=(scope,),
        )
        existing = rows.get(row_label)
        rows[row_label] = (
            contribution if existing is None else add(existing, contribution)
        )
    return tuple(rows.items())


def in_feasible_set(
    declaration: CandidateDeclaration, state: JointBlockOperator
) -> bool:
    """Whether ``state`` lies in ``W`` of Eq. ``eq:feas``.

    The membership predicate itself, used where a derivation compares two
    feasible sets rather than checking one witness -- Proposition
    ``prop:conservative``'s inclusion and its equality at ``d_A = 1`` are
    both statements about this predicate at two declarations.
    """
    return verify_witness(declaration, state).passes


@dataclass(frozen=True)
class FeasibilityCheck:
    """The outcome of check V7 on a candidate declaration."""

    passes: bool
    #: The witness that passed, or ``None`` where none did.
    witness: JointBlockOperator | None
    #: Whether the passing witness is the default of Eq. ``eq:witness-empty``.
    used_default: bool
    #: The verification of the default candidate, always attempted first.
    default_verification: WitnessVerification | None
    #: The verification of the supplied witness, where one was supplied.
    supplied_verification: WitnessVerification | None
    refusal: Refusal | None
    #: Whether the constraint list was empty, i.e. whether V7 passed by its
    #: FIRST branch -- which Theorem ``thm:feasibility`` (i) PROVES rather than checks.
    first_branch: bool


def check_feasibility(
    declaration: CandidateDeclaration,
    supplied: JointBlockOperator | None = None,
) -> FeasibilityCheck:
    """Return check V7's verdict: the one-sided, fail-closed feasibility check.

    Theorem ``thm:feasibility``: at an empty constraint list D(vii) is PROVED and the
    default witness Eq. ``eq:witness-empty`` is exhibited; at a non-empty list
    "Eq. eq:witness-empty is CHECKED FIRST, and a list it satisfies needs no
    further witness", and otherwise a supplied witness is verified. Where
    neither passes the refusal carries the verbatim reason
    ``no_feasibility_witness`` -- for BOTH branches of the second case, "when no
    witness is supplied OR THE SUPPLIED ONE FAILS".
    """
    first_branch = not declaration.constraint_list
    candidate = default_witness(declaration)
    # EACH VERIFICATION SAYS WHICH CANDIDATE IT IS ABOUT, so that the legs it
    # records are keyed by the state they were decided on (:data:
    # `DEFAULT_CANDIDATE`); this function is the one caller that knows.
    default_verification = verify_witness(
        declaration, candidate, element=DEFAULT_CANDIDATE
    )
    if default_verification.passes:
        return FeasibilityCheck(
            passes=True,
            witness=candidate,
            used_default=True,
            default_verification=default_verification,
            supplied_verification=None,
            refusal=None,
            first_branch=first_branch,
        )

    supplied_verification = (
        None
        if supplied is None
        else verify_witness(declaration, supplied, element=SUPPLIED_WITNESS)
    )
    if supplied_verification is not None and supplied_verification.passes:
        return FeasibilityCheck(
            passes=True,
            witness=supplied,
            used_default=False,
            default_verification=default_verification,
            supplied_verification=supplied_verification,
            refusal=None,
            first_branch=first_branch,
        )

    if supplied is None:
        default_legs = ", ".join(default_verification.failing_legs())
        detail = (
            "no feasibility witness was supplied and the default candidate of "
            f"Eq. eq:witness-empty fails its {default_legs} "
            "leg. THIS MEANS 'I WAS NOT SHOWN A FEASIBLE STATE', NEVER 'THERE "
            "IS NONE' (Remark rem:completeness): the remedy is to supply "
            "omega^*, and no search is performed here (Remark rem:nosearch)"
        )
    else:
        assert supplied_verification is not None
        detail = (
            "the supplied feasibility witness fails its "
            f"{', '.join(supplied_verification.failing_legs())} leg. THIS MEANS "
            "'I WAS NOT SHOWN A FEASIBLE STATE', NEVER 'THERE IS NONE' (Remark "
            "rem:completeness); the witness is verified as supplied and is "
            "never normalized or repaired"
        )
    return FeasibilityCheck(
        passes=False,
        witness=None,
        used_default=False,
        default_verification=default_verification,
        supplied_verification=supplied_verification,
        refusal=Refusal(reason=RefusalReason.NO_FEASIBILITY_WITNESS, detail=detail),
        first_branch=first_branch,
    )
