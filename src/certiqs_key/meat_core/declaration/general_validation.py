"""Admissibility, general format: every refusal of ``def:declaration`` (DX1)-(DX6).

The conditions are ``def:admissible-declaration``'s, decided as
``req:declaration-admission`` requires.

``def:admissible-declaration``'s general-format paragraph reads the eight conditions for
a declaration of the general format, and this module decides them. It adds NO
refusal string to the closed vocabulary of ``interface.yaml``
(``refusal_reasons``): an exact-admissibility failure carries
``declaration_not_exactly_admissible``, exactly as on the accepted path, and a
well-formedness failure raises
:class:`~certiqs_key.meat_core.errors.DeclarationError` naming the
def:admissible-declaration clause, as the accepted path's ``validate_declaration`` does.
The general format widened what may be declared; it did not widen how a defect is
reported.

WHERE THE EXACT PREDICATES RUN
==============================
**Per factor, never on a product** (``def:declaration``, "Exact admissibility
in the general format"): the conditions on ``{F_v}`` are decided on each
measured factor's own family, its own blocks and its own declared order, by the
very function the accepted path calls
(:func:`~certiqs_key.meat_core.declaration.admission.admit_bob_povm_exact`), so
there is one admission rule and not two. **Per Alice sector**: the conditions
on ``tau_A``, on ``{M_x}`` and on a ``general`` ``Theta_k`` are decided block
by block along ``T``, and the trace of ``tau_A`` is accumulated over the blocks
in their declared order and verified to round nowhere.

**In ensemble form the conditions on ``{M_x}`` are replaced by those of (DX4)
on ``{N_x}``** -- ``sum_x N_x^{(t)} = tau_A^{(t)}`` exactly, the sum in the
declared order of ``X`` rounding nowhere, every block exactly Hermitian and
exactly positive semidefinite, and ``tau_A^{(t)} != 0`` -- and the denoted
``{M_x}`` of ``eq:ensemblepovm`` "is a POVM by ``lem:ensemble-form`` and
decided by nothing". It is not formed here or anywhere.

THE REFUSING READINGS THIS MODULE TAKES, each named at its function
==================================================================
* **The ensemble form is refused in untrusted-source mode** (``def:declaration``
  (DX4): it "exists in trusted-source mode only"), in
  :func:`_check_alice_slot`.
* The party readouts are declared total maps; absent, they take the default
  ``pi_A(x,v)=x``, ``pi_B(x,v)=v``. Every message reads its sender's declared
  readout and the key must be computable from the holder's readout and transcript.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
from itertools import product

import numpy as np

from certiqs_key.domain.manifest import ConstraintRelation, KeyHolder
from certiqs_key.foundations import exact
from certiqs_key.foundations.exact_admission import (
    admit_family_exact,
    is_hermitian_exact,
    is_psd_exact,
    sum_rounds_nowhere,
    to_exact,
)
from certiqs_key.meat_core.declaration.admission import (
    AdmissionError,
    BobPovmAdmission,
    admit_bob_povm_exact,
)
from certiqs_key.meat_core.declaration.general import (
    SEPARATOR,
    GeneralDeclaration,
    GeneralRhsTag,
)
from certiqs_key.meat_core.errors import DeclarationError
from certiqs_key.meat_core.objective.linalg import Matrix, as_matrix
from certiqs_key.meat_core.reasons import GroupAPredicate
from certiqs_key.meat_core.reasons import RefusalReason as AdmissionRefusal

#: The order in which Alice's blocks are summed, recorded with the verdict, as
#: the accepted path records its own: ``eq:declorder`` fixes that a declared
#: family's sum is the sequential sum in the DECLARED order of its alphabet.
ALICE_SUMMATION_ORDER = "the declared order of X, then the declared order of T"


@dataclass(frozen=True)
class GeneralAdmission:
    """What the general-format admission decided, for the record.

    ``per_factor`` is one verdict per measured factor, in the factor order:
    the evidence that every exact predicate on ``{F_v}`` ran on a factor and on
    no product.
    """

    per_factor: tuple[BobPovmAdmission, ...]
    alice_rounds_nowhere_per_sector: Mapping[str, bool]


def validate_general_declaration(
    declaration: GeneralDeclaration,
) -> GeneralAdmission:
    """Decide def:admissible-declaration for a declaration of the general format.

    ``req:declaration-admission``: conditions (i)-(vi) and (viii) are decided
    exactly on the declared data, and nothing is computed from a declaration
    that fails one; (vii), the non-empty feasible set, is left to the compiler
    where constraints are declared (``req:compiled-declaration-only``).

    ``def:admissible-declaration``, the general-format paragraph, together with the
    exact-admissibility paragraph of ``def:declaration``. The order is the
    order of ``interface.yaml``'s ``fail_closed`` rows: structure first, then
    the declared numbers, then the typed constraint list.

    Raises:
        DeclarationError: naming the def:admissible-declaration clause it
            violates, or (as
            :class:`~certiqs_key.meat_core.declaration.admission.AdmissionError`)
            carrying ``declaration_not_exactly_admissible``.
    """
    _check_structure(declaration)
    _check_alphabets(declaration)
    per_factor = _check_measured_factors(declaration)
    alice_rounds = _check_alice_slot(declaration)
    _check_transcript(declaration)
    _check_party_computability(declaration)
    _check_constraints(declaration)
    return GeneralAdmission(
        per_factor=per_factor, alice_rounds_nowhere_per_sector=alice_rounds
    )


# ---------------------------------------------------------------------------
#  (DX1): the factor list
# ---------------------------------------------------------------------------


def _check_structure(declaration: GeneralDeclaration) -> None:
    """Decide the structural conditions of ``def:declaration`` (DX1).

    THREE OF THEM HOLD BY THE TYPE AND ARE NOT CHECKED HERE, which is the
    reason the type is shaped as it is: at most one factor is tagged ``A``
    because :attr:`GeneralDeclaration.alice` is one factor and not a list;
    where there is one it is first because the joint order is built ``t``
    slowest from that one field; and all factors carry one block kind because
    the declaration carries one :attr:`sector_block_kind`. What is left is
    decided.
    """
    if not declaration.factors:
        raise DeclarationError(
            "def:declaration (DX1): at least one factor is tagged Q, and this "
            "declaration has no measured factor. There is nothing to measure "
            "and no product sector map to form"
        )
    labels = [factor.label for factor in declaration.factors]
    for axis in (declaration.alice.sectors, *(f.sectors for f in declaration.factors)):
        if (
            not axis.labels
            or len(set(axis.labels)) != len(axis.labels)
            or set(axis.dims) != set(axis.labels)
            or any(
                not isinstance(axis.dims[s], int) or axis.dims[s] < 1
                for s in axis.labels
            )
        ):
            raise DeclarationError(
                "sector axes require distinct labels and positive dimensions"
            )
    if len(set(labels)) != len(labels):
        raise DeclarationError(
            f"def:declaration (DX1): the measured factors {labels} do not have "
            "distinct labels, so an entry's declared scope would not say which "
            "factor it is scoped to"
        )
    for factor in declaration.factors:
        if not factor.sectors.labels:
            raise DeclarationError(
                f"def:declaration (DX1): the measured factor {factor.label!r} "
                "declares no sector, so the product sector map is empty"
            )
        for sector in factor.sectors.labels:
            if SEPARATOR in sector:
                raise DeclarationError(
                    f"def:declaration (DX1): the sector identifier {sector!r} "
                    f"of factor {factor.label!r} contains the declared product "
                    f"separator {SEPARATOR!r}, so the product identifier would "
                    "not say which factor supplied which part"
                )
        for letter in factor.alphabet:
            if SEPARATOR in letter:
                raise DeclarationError(
                    f"def:declaration (DX3): the outcome letter {letter!r} of "
                    f"factor {factor.label!r} contains the declared product "
                    f"separator {SEPARATOR!r}, 'which is why a factor letter "
                    "may not contain it'"
                )
    for alice_sector in declaration.alice_sectors:
        if declaration.alice_dim_of(alice_sector) < 1:
            raise DeclarationError(
                "def:declaration (DX1): the Alice sector "
                f"{alice_sector!r} has dimension "
                f"{declaration.alice_dim_of(alice_sector)}; a declared "
                "subspace is spanned by at least one basis vector"
            )


def _check_alphabets(declaration: GeneralDeclaration) -> None:
    """Decide def:admissible-declaration (i) on the declared alphabets and tables.

    "All alphabets finite, all maps total." Finiteness is the type; totality of
    ``r`` and ``phi`` over the DERIVED product alphabet is what is decided.
    """
    if not declaration.alice_alphabet:
        raise DeclarationError("def:admissible-declaration (i): X is empty")
    for alphabet in (
        declaration.alice_alphabet,
        declaration.acceptance_values,
        *(f.alphabet for f in declaration.factors),
    ):
        if not alphabet or len(set(alphabet)) != len(alphabet):
            raise DeclarationError(
                "def:admissible-declaration (i): alphabets are nonempty without "
                "repetitions"
            )
    for factor in declaration.factors:
        if not factor.alphabet:
            raise DeclarationError(
                "def:admissible-declaration (i): the alphabet of factor "
                f"{factor.label!r} is empty"
            )
    for x in declaration.alice_alphabet:
        if x not in declaration.alice_operators:
            raise DeclarationError(
                "def:admissible-declaration (i): Alice's slot declares no operator "
                f"for {x!r}"
            )
        for alice_sector in declaration.alice_sectors:
            if alice_sector not in declaration.alice_operators[x]:
                raise DeclarationError(
                    f"def:declaration (DX2): Alice's operator at {x!r} declares "
                    f"no block on the Alice sector {alice_sector!r}; the list "
                    "is one array per t and the list IS the operator"
                )
    for x in declaration.alice_alphabet:
        for v in declaration.bob_outcomes:
            if (x, v) not in declaration.key_map:
                raise DeclarationError(
                    "def:admissible-declaration (i), (iv): r is not total -- the "
                    "outcome pair "
                    f"{(x, v)} has no declared raw-key value"
                )
            value = declaration.raw_key(x, v)
            if value is not None and not 0 <= value < declaration.key_value_count:
                raise DeclarationError(
                    "def:admissible-declaration (iv): raw key outside the declared "
                    "alphabet"
                )
            if declaration.party_partition is not None:
                partition = declaration.party_partition
                for table, alphabet in (
                    (partition.readout_alice, partition.alphabet_alice),
                    (partition.readout_bob, partition.alphabet_bob),
                ):
                    if (x, v) not in table or table[(x, v)] not in alphabet:
                        raise DeclarationError(
                            "def:admissible-declaration (viii): party readout is not "
                            "total"
                        )


# ---------------------------------------------------------------------------
#  (DX3): the factorised family, decided per factor
# ---------------------------------------------------------------------------


def _check_measured_factors(
    declaration: GeneralDeclaration,
) -> tuple[BobPovmAdmission, ...]:
    """Admit each measured factor's family EXACTLY, and no product.

    ``def:declaration`` (DX3) and its exact-admissibility reading: "Every exact
    predicate is decided PER FACTOR, on that factor's blocks and in that
    factor's declared order." This calls the accepted path's own admission
    function once per factor, so the rule that decides a single family decides
    each factor of a product and there is no second implementation of it.
    """
    verdicts: list[BobPovmAdmission] = []
    for factor in declaration.factors:
        for letter in factor.alphabet:
            if letter not in factor.blocks:
                raise DeclarationError(
                    f"def:declaration (DX3): factor {factor.label!r} declares no "
                    f"family member for its letter {letter!r}"
                )
            for sector in factor.sectors.labels:
                block = factor.blocks[letter].get(sector)
                if block is None:
                    raise DeclarationError(
                        f"def:declaration (DX3): factor {factor.label!r}, letter "
                        f"{letter!r} declares no block on its sector {sector!r}"
                    )
                width = factor.sectors.dims[sector]
                if as_matrix(block).shape != (width, width):
                    raise DeclarationError(
                        f"def:declaration (DX3): factor {factor.label!r}, letter "
                        f"{letter!r}, sector {sector!r}: the block has shape "
                        f"{as_matrix(block).shape}, expected ({width}, {width})"
                    )
        try:
            verdicts.append(admit_bob_povm_exact(factor.blocks, factor.sectors.labels))
        except AdmissionError as refusal:
            raise AdmissionError(
                f"the measured factor {factor.label!r}: {refusal}",
                reason=refusal.reason,
                predicate=refusal.predicate,
            ) from refusal
    return tuple(verdicts)


# ---------------------------------------------------------------------------
#  (DX4): Alice's slot, per Alice sector
# ---------------------------------------------------------------------------


def _check_alice_slot(declaration: GeneralDeclaration) -> Mapping[str, bool]:
    """Admit ``tau_A`` and Alice's slot, block by block along ``T``.

    THE REFUSING READING, NAMED HERE: the ensemble form exists in
    trusted-source mode only (``def:declaration`` (DX4)), so an ensemble-form
    declaration whose marginal slot holds ``none`` is REFUSED rather than read
    as a POVM form or completed by some ``tau_A`` this module chose. Nothing
    may stand in for an undeclared marginal.
    """
    if declaration.is_ensemble_form and not declaration.is_trusted_source:
        raise DeclarationError(
            "def:declaration (DX4): the ensemble form exists in TRUSTED-source "
            "mode only -- eq:ensembleform reads sum_x N_x^(t) = tau_A^(t), and "
            "in untrusted-source mode there is no tau_A for it to sum to. The "
            "declaration is refused; no marginal is supplied for it here"
        )
    if declaration.is_trusted_source:
        _check_marginal(declaration)
    rounds: dict[str, bool] = {}
    for alice_sector in declaration.alice_sectors:
        width = declaration.alice_dim_of(alice_sector)
        blocks: list[Matrix] = []
        for x in declaration.alice_alphabet:
            block = declaration.alice_block(x, alice_sector)
            if block.shape != (width, width):
                raise DeclarationError(
                    f"def:declaration (DX2): Alice's operator at {x!r} has "
                    f"shape {block.shape} on the Alice sector "
                    f"{alice_sector!r}, expected ({width}, {width})"
                )
            blocks.append(block)
        if declaration.is_ensemble_form:
            rounds[alice_sector] = _admit_ensemble_blocks(
                declaration, alice_sector, blocks
            )
        else:
            admission = admit_family_exact(blocks)
            if not admission.admissible:
                raise AdmissionError(
                    "def:declaration, the exact-admissibility paragraph in the "
                    f"general format (the alice_povm_exact row) on the Alice "
                    f"sector {alice_sector!r}: the declared blocks are refused "
                    f"at EXACTLY 0, failing {list(admission.failures)}. The "
                    f"summation order is {ALICE_SUMMATION_ORDER}; nothing is "
                    "repaired here",
                    reason=AdmissionRefusal.DECLARATION_NOT_EXACTLY_ADMISSIBLE,
                    predicate=GroupAPredicate.ALICE_POVM_EXACT,
                )
            rounds[alice_sector] = admission.rounds_nowhere.ok
    return rounds


def _admit_ensemble_blocks(
    declaration: GeneralDeclaration, alice_sector: str, blocks: Sequence[Matrix]
) -> bool:
    """Decide ``eq:ensembleform`` on one Alice sector, exactly.

    ``sum_x N_x^{(t)} = tau_A^{(t)}`` with the sum "formed entrywise in the
    declared order of ``X`` and rounding nowhere", every block exactly
    Hermitian and exactly positive semidefinite, "and the second condition a
    comparison of declared entries with the datum ``0``". The denoted
    ``{M_x}`` of ``eq:ensemblepovm`` is NOT formed: it is a POVM by
    ``lem:ensemble-form`` (i) and decided by nothing.
    """
    tau = declaration.marginal_block(alice_sector)
    if not np.any(tau != 0.0):
        raise AdmissionError(
            "def:declaration (DX4), eq:ensembleform: the side condition "
            f"tau_A^(t) != 0 fails on the Alice sector {alice_sector!r}. "
            "lem:ensemble-form needs a non-zero marginal block -- the weights "
            "tr N_x / tr tau_A of eq:ensemblepovm are undefined without one -- "
            "and this is a comparison of declared entries with the datum 0",
            reason=AdmissionRefusal.DECLARATION_NOT_EXACTLY_ADMISSIBLE,
            predicate=GroupAPredicate.ALICE_MARGINAL_EXACT,
        )
    for x, block in zip(declaration.alice_alphabet, blocks, strict=True):
        if not is_hermitian_exact(block) or not is_psd_exact(block):
            raise AdmissionError(
                "def:declaration (DX4): the declared N_x is exactly Hermitian "
                f"and exactly positive semidefinite per block; at {x!r} on the "
                f"Alice sector {alice_sector!r} it is not (decided by a "
                "rational LDL^*, never by a floating-point eigenvalue)",
                reason=AdmissionRefusal.DECLARATION_NOT_EXACTLY_ADMISSIBLE,
                predicate=GroupAPredicate.ALICE_POVM_EXACT,
            )
    verdict = sum_rounds_nowhere(list(blocks))
    if not verdict.ok:
        raise AdmissionError(
            "def:declaration (DX4), eq:ensembleform: the sum sum_x N_x^(t) is "
            "formed in the declared order of X and must round nowhere; the "
            f"first inexact addition on the Alice sector {alice_sector!r} is at "
            f"index {verdict.first_inexact_index!r} of "
            f"{list(declaration.alice_alphabet)}. A computed sum that rounded "
            "would not say the identity holds of the declared numbers",
            reason=AdmissionRefusal.DECLARATION_NOT_EXACTLY_ADMISSIBLE,
            predicate=GroupAPredicate.ALICE_POVM_EXACT,
        )
    width = int(tau.shape[0])
    total = exact.zeros(width, width)
    for block in blocks:
        total = exact.add(total, to_exact(block))
    if not exact.equal(total, to_exact(tau)):
        raise AdmissionError(
            "def:declaration (DX4), eq:ensembleform: sum_x N_x^(t) is not "
            f"tau_A^(t) on the Alice sector {alice_sector!r}, decided EXACTLY "
            "on the declared dyadic numbers. Nothing is repaired: an instance "
            "declares blocks whose sum closes exactly, or the declaration is "
            "refused",
            reason=AdmissionRefusal.DECLARATION_NOT_EXACTLY_ADMISSIBLE,
            predicate=GroupAPredicate.ALICE_POVM_EXACT,
        )
    return True


def _check_marginal(declaration: GeneralDeclaration) -> None:
    """Decide def:admissible-declaration (ii) on ``tau_A`` as the block list of (DX2).

    Every block exactly Hermitian and exactly positive semidefinite, and
    ``tr tau_A = 1`` with "the trace of ``tau_A`` accumulated over the blocks in
    their declared order and rounding nowhere" -- so that ``tau_A = 0`` is
    inadmissible for the reason ``rem:modes-da1`` (c) gives, and the identity
    the proofs read is an identity of the declared numbers.
    """
    traces: list[float] = []
    exact_total = Fraction(0)
    for alice_sector in declaration.alice_sectors:
        block = declaration.marginal_block(alice_sector)
        width = declaration.alice_dim_of(alice_sector)
        if block.shape != (width, width):
            raise DeclarationError(
                f"def:declaration (DX2): tau_A^(t) on {alice_sector!r} has "
                f"shape {block.shape}, expected ({width}, {width})"
            )
        if not is_hermitian_exact(block) or not is_psd_exact(block):
            raise AdmissionError(
                "the alice_marginal_exact row, per Alice sector: "
                f"tau_A^(t) on {alice_sector!r} is not exactly Hermitian and "
                "exactly positive semidefinite",
                reason=AdmissionRefusal.DECLARATION_NOT_EXACTLY_ADMISSIBLE,
                predicate=GroupAPredicate.ALICE_MARGINAL_EXACT,
            )
        exact_block = to_exact(block)
        exact_total += exact.real_part(
            exact.trace(exact_block), f"tr tau_A^({alice_sector})"
        )
        traces.append(float(np.real(np.trace(block))))
    if exact_total != 1:
        raise AdmissionError(
            "def:admissible-declaration (ii): tr tau_A = 1 whenever a marginal is "
            "declared, and "
            f"the EXACT sum over the Alice sectors is {exact_total}. Decided at "
            "exactly 0 on the declared dyadic numbers",
            reason=AdmissionRefusal.DECLARATION_NOT_EXACTLY_ADMISSIBLE,
            predicate=GroupAPredicate.ALICE_MARGINAL_EXACT,
        )
    running = 0.0
    for alice_sector, value in zip(declaration.alice_sectors, traces, strict=True):
        candidate = running + value
        if Fraction(candidate) != Fraction(running) + Fraction(value):
            raise AdmissionError(
                "def:admissible-declaration (ii) in the general format: the trace of "
                "tau_A is "
                "accumulated OVER THE BLOCKS IN THEIR DECLARED ORDER and must "
                f"round nowhere; the addition at the Alice sector "
                f"{alice_sector!r} rounds",
                reason=AdmissionRefusal.DECLARATION_NOT_EXACTLY_ADMISSIBLE,
                predicate=GroupAPredicate.ALICE_MARGINAL_EXACT,
            )
        running = candidate


# ---------------------------------------------------------------------------
#  (DX5), def:admissible-declaration (v), (viii)
# ---------------------------------------------------------------------------


def validate_general_transcript_tables(declaration: GeneralDeclaration) -> None:
    """Check DX5 total tables on the full declared message products.

    Unreachable prefixes and transcript tuples still belong to the declared
    domains. This shared check also guards serialization before table lookup.
    Mapping insertion order is not mathematical data.
    """
    messages = declaration.transcript.messages
    if not messages:
        raise DeclarationError("def:declaration (DX5): L >= 1 messages required")
    partition = declaration.party_partition
    readouts = {
        KeyHolder.ALICE: declaration.alice_alphabet
        if partition is None
        else partition.alphabet_alice,
        KeyHolder.BOB: declaration.bob_outcomes
        if partition is None
        else partition.alphabet_bob,
    }
    prefixes: tuple[tuple[str, ...], ...] = ((),)
    for index, message in enumerate(messages):
        if message.sender not in readouts:
            raise DeclarationError("def:declaration (DX5): unknown message sender")
        if not message.alphabet or len(set(message.alphabet)) != len(message.alphabet):
            raise DeclarationError("def:declaration (DX5): invalid message alphabet")
        expected = set(product(readouts[message.sender], prefixes))
        if set(message.table) != expected:
            raise DeclarationError(
                f"def:declaration (DX5): message {index} table is not total "
                "on its declared readout and prefix product domain"
            )
        if any(value not in message.alphabet for value in message.table.values()):
            raise DeclarationError(
                f"def:declaration (DX5): message {index} value outside its alphabet"
            )
        prefixes = tuple(
            (*prefix, value) for prefix in prefixes for value in message.alphabet
        )
    if set(declaration.accept_statistic) != set(prefixes):
        raise DeclarationError(
            "def:admissible-declaration (i), (DX5): phi is not total on the declared "
            "transcript product"
        )
    if any(
        value not in declaration.acceptance_values
        for value in declaration.accept_statistic.values()
    ):
        raise DeclarationError(
            "def:admissible-declaration (i): phi value outside its declared codomain"
        )


def _check_transcript(declaration: GeneralDeclaration) -> None:
    """Decide def:admissible-declaration (i), (v) for the transcript protocol of (DX5).

    Every message table is total on the full declared readout/prefix product.
    A ``KeyError`` from
    :meth:`Transcript.announcement` is that failure and is raised as the
    def:admissible-declaration violation it is -- ``phi`` is total on the derived ``K``,
    and sifting is announcement-determined: ``r(x, v) = perp`` exactly when the class
    fails.
    """
    validate_general_transcript_tables(declaration)
    verdict: dict[tuple[str, ...], bool] = {}
    witness: dict[tuple[str, ...], tuple[str, str]] = {}
    for x in declaration.alice_alphabet:
        for v in declaration.bob_outcomes:
            try:
                kappa = declaration.announcement(x, v)
            except KeyError as missing:
                raise DeclarationError(
                    "def:admissible-declaration (i), (viii) for the transcript of "
                    "(DX5): a "
                    "message table is not total -- no letter is declared for "
                    f"{missing} at the outcome pair {(x, v)}"
                ) from missing
            if kappa not in declaration.accept_statistic:
                raise DeclarationError(
                    "def:admissible-declaration (i): phi is not total -- the derived "
                    "transcript "
                    f"{kappa} has no acceptance value"
                )
            if declaration.accept_statistic[kappa] not in declaration.acceptance_values:
                raise DeclarationError(
                    f"def:admissible-declaration (i): phi maps the transcript {kappa} "
                    "to "
                    f"{declaration.accept_statistic[kappa]!r}, which is not a "
                    "declared acceptance value"
                )
            passes = declaration.raw_key(x, v) is not None
            if kappa in verdict and verdict[kappa] != passes:
                raise DeclarationError(
                    "def:admissible-declaration (v): sifting is not "
                    "announcement-determined. The "
                    f"transcript {kappa} contains both a sifted and an unsifted "
                    f"outcome pair: {witness[kappa]} and {(x, v)}"
                )
            verdict[kappa] = passes
            witness[kappa] = (x, v)


def _check_party_computability(declaration: GeneralDeclaration) -> None:
    """Decide def:admissible-declaration (viii) for the transcript protocol.

    ``eq:partycomp``: the declared holder computes ``r`` from ITS OWN readout
    and the announcements. With the default readouts this is
    ``r(x, v) = r_A(x, a(x, v))`` for ``h = A`` and
    ``r(x, v) = r_B(v, a(x, v))`` for ``h = B``, and it is decided by testing
    that no two outcome pairs agreeing on (holder's readout, transcript)
    disagree on ``r``.

    The same predicate applies to an explicitly declared non-default readout.
    """
    seen: dict[tuple[str, tuple[str, ...]], int | None] = {}
    for x in declaration.alice_alphabet:
        for v in declaration.bob_outcomes:
            kappa = declaration.announcement(x, v)
            readout = declaration.readouts(x, v)[declaration.key_holder]
            key = (readout, kappa)
            value = declaration.raw_key(x, v)
            if key in seen and seen[key] != value:
                raise DeclarationError(
                    "def:admissible-declaration (viii), eq:partycomp: the raw key is "
                    "not "
                    "computable by the declared holder "
                    f"{declaration.key_holder.value}. "
                    f"Two outcome pairs share the holder's readout {readout!r} "
                    f"and the transcript {kappa} but disagree on r "
                    f"({seen[key]!r} and {value!r}), so no total r_h exists"
                )
            seen[key] = value


# ---------------------------------------------------------------------------
#  (DX6): the typed constraint list
# ---------------------------------------------------------------------------


def _check_constraints(declaration: GeneralDeclaration) -> None:
    """Decide def:admissible-declaration (vi) and (DX6) on the declared list.

    The tag typing is the accepted rule widened by exactly one form: a
    ``general`` right-hand side exists in trusted-source mode only, and a
    ``party_local`` entry is admissible IN EITHER MODE with the OPERATOR
    relation symbols (``def:homog``, the relation-symbol clause). Licensing
    stays a type check on the tag and compares no numbers; every constraint
    operator is exactly Hermitian per block, and positivity is asked of no
    constraint operator anywhere in this module.
    """
    scopes = {factor.label for factor in declaration.factors}
    for index, entry in enumerate(declaration.constraint_list):
        if entry.scope not in scopes:
            raise DeclarationError(
                f"def:declaration (DX6): entry {index} declares the scope "
                f"{entry.scope!r}, which is no declared measured factor "
                f"{sorted(scopes)}"
            )
        factor = next(f for f in declaration.factors if f.label == entry.scope)
        for sector in factor.sectors.labels:
            block = entry.operator_blocks.get(sector)
            if block is None:
                raise DeclarationError(
                    f"def:declaration (DX6): entry {index} declares no block on "
                    f"the sector {sector!r} of its scope {entry.scope!r}; the "
                    "operator is a block list against that factor's own map"
                )
            width = factor.sectors.dims[sector]
            if as_matrix(block).shape != (width, width):
                raise DeclarationError(
                    f"def:declaration (DX6): entry {index}, sector {sector!r}: "
                    f"the block has shape {as_matrix(block).shape}, expected "
                    f"({width}, {width})"
                )
            if not is_hermitian_exact(as_matrix(block)):
                raise AdmissionError(
                    "def:declaration, the exact-admissibility paragraph: every "
                    f"O_k is exactly Hermitian per block; entry {index} on "
                    f"sector {sector!r} is not",
                    reason=AdmissionRefusal.DECLARATION_NOT_EXACTLY_ADMISSIBLE,
                    predicate=GroupAPredicate.CONSTRAINT_OPERATOR_EXACT,
                )
        if entry.relation not in tuple(ConstraintRelation):
            raise DeclarationError(
                f"def:admissible-declaration (vi): entry {index} declares the relation "
                f"{entry.relation!r}, which is none of the three"
            )
        if entry.rhs_tag is GeneralRhsTag.GENERAL:
            if not declaration.is_trusted_source:
                raise DeclarationError(
                    f"def:admissible-declaration (vi): entry {index} is tagged "
                    "`general`, and in "
                    "untrusted-source mode the right-hand side is a real "
                    "number. A general operator Theta_k does not exist there"
                )
            for alice_sector in declaration.alice_sectors:
                block = entry.operator_bound(alice_sector)
                width = declaration.alice_dim_of(alice_sector)
                if block.shape != (width, width):
                    raise DeclarationError(
                        f"def:declaration (DX2): entry {index}: Theta_k^(t) on "
                        f"{alice_sector!r} has shape {block.shape}, expected "
                        f"({width}, {width})"
                    )
                if not is_hermitian_exact(block):
                    raise AdmissionError(
                        "def:declaration, the exact-admissibility paragraph: a "
                        "`general` Theta_k is exactly Hermitian block by block "
                        f"along T; entry {index} on {alice_sector!r} is not",
                        reason=AdmissionRefusal.DECLARATION_NOT_EXACTLY_ADMISSIBLE,
                        predicate=GroupAPredicate.CONSTRAINT_OPERATOR_EXACT,
                    )
        else:
            # `homogeneous` and `party_local` carry the real c_k, and reading
            # it is how a declaration that carries an operator under one of
            # those tags is refused: the property raises rather than guessing.
            _ = entry.scalar_bound
