"""PC6 -- the emitted validator V1-V8, stated on a CANDIDATE declaration.

protocol-compiler 0.3.0 Definition ``def:validator`` and Theorem
``thm:validator-soundness``.

WHY THIS IS NOT THE CONSUMING ENGINE'S OWN ``validate_declaration`` (meat-core)
==============================================================================
The consuming engine has its own fail-closed validator over its own
well-formedness assumption, and this module neither calls it, imports it, nor
shares code with it. That separation is deliberate and it is the right one on the
mathematics:

* **The proofs are about THESE checks.** Theorem ``thm:validator-soundness`` (i)-(iv) is
  a statement about V1-V8 as Definition ``def:validator`` writes them --
  soundness on all of D(i)-D(viii), completeness on seven of the eight, V7
  one-sided, and each decided by a stated finite enumeration. Delegating to
  another module's checks would leave those four claims about nothing: what
  would be verified is that module's predicate, whose contract is a different
  contract's def:admissible-declaration.
* **The two are stated on different objects.** These checks are stated on a
  CANDIDATE -- "given a candidate declaration" -- and the discriminating cases
  of Theorem ``thm:validator-soundness`` (ii)-(iii) are candidates Definition
  ``def:compile`` could not have emitted. The consumer validates a bundle it is about to
  solve.
* **Two independent implementations of a fail-closed path are worth more than
  one.** The consumer's validator is an INDEPENDENT check of the same
  mathematics at the other end of the pipe. Sharing code would collapse two
  chances to catch an error into one, which is exactly what a fail-closed
  boundary must not do. A golden docking cross-check belongs to the emission
  pass, where a declaration exists to hand across; it is a TEST that the two
  agree, never an import that makes them agree by construction.

THE SHAPE OF THE CLAIM IS NOT SYMMETRIC
=======================================
SOUNDNESS holds for all eight: if V1-V8 all pass then D(i)-D(viii) all hold.
COMPLETENESS holds for seven: if D(i)-D(vi) and D(viii) hold then V1-V6 and V8
all pass. The missing direction is exactly ``D(vii) => V7``, and Theorem
``thm:validator-soundness`` (iii) exhibits the counterexample. Remark
``rem:completeness`` says what each direction buys: soundness is the safety direction,
"without it the compiler could emit a declaration that passes every check and is
nonetheless ill-formed, which is the failure this module exists to prevent";
completeness is what makes a REFUSAL informative, "so a refusal names a real defect and
not a limitation of the checker".

Five pairs are literal restatements in both directions -- V1/D(i), V2/D(ii),
V3/D(iii), V4/D(iv), V6/D(vi) -- and two are equivalences that need an
argument, V5/D(v) and V8/D(viii). The arguments are CONSTRUCTIONS, of
``varsigma`` from ``r`` and ``a`` and of ``r_h`` from ``r``, and both are here
(:func:`reconstruct_sifting_predicate`, :func:`reconstruct_holder_key_rule`)
because a reader checking soundness needs to run them. Both are non-unique off
the realized set and the contract says the value there "is immaterial", so
neither may be asserted to agree with a declared table off that set.

EVERY CHECK RETURNS A VERDICT; NONE RAISES
==========================================
the ``fail_closed`` convention: "every failed check produces a REFUSAL with a
machine-readable reason and NO declaration". A check is therefore a function to
a :class:`CheckOutcome` carrying the reason, and the exceptions of
:mod:`certiqs_key.foundations.errors` are reserved for data no clause can be read
against. And no check drops anything: the constraint list a candidate carries
is the list the checks are run over, entry for entry, because Theorem
``thm:gates`` (ii) says the compiler "never drops a constraint entry silently".

AND EVERY CHECK NOW CARRIES WHAT IT DECIDED
===========================================
:attr:`CheckOutcome.predicates` is the ``gate_report`` row's per-predicate
transcript for this check (:mod:`certiqs_key.protocol_compiler.transcript`).
Two rules follow from the fact that a check RETURNS EARLY on its first
failure, and both are properties a reader can check:

* what is recorded is what was DECIDED. A check that returns at its first
  failure carries the outcomes it reached up to and including that one, and
  nothing about the elements it never looked at -- so the transcript of a
  refusal is shorter than that of a pass, which is the honest shape.
* the ``recorded_predicates`` enumeration of the ``gate_report`` row scopes
  WHICH decisions are keyed per element, and its scope note excludes the rest
  explicitly: V1's finiteness, non-emptiness, totality and ``d_Q = sum_s d_s``
  clauses, the whole of checks V4, V5 and V8, and V7's emptiness test on
  ``CList``. Those are recorded through the outcome of gate (G1) that carries
  them and, where one fails, through ``refusal``. So :func:`check_v4`,
  :func:`check_v5` and :func:`check_v8` record NOTHING, and that is the row's
  decision and not an omission of this file.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from fractions import Fraction

from certiqs_key.domain.constraints import ConstraintEntry, RhsTag
from certiqs_key.domain.families import AliceForm
from certiqs_key.foundations.blocks import (
    BlockOperator,
    JointBlockOperator,
    Label,
    SectorMapDisagreement,
    SectorStructure,
    block_sum_in_declared_order,
)
from certiqs_key.foundations.exact import (
    Cx,
    Matrix,
    SummationVerdict,
    addition_rounds_nowhere,
    dimension,
    identity,
    is_hermitian,
    is_positive_semidefinite,
    sum_in_declared_order,
    trace_in_row_order,
)
from certiqs_key.protocol_compiler.declaration import CandidateDeclaration
from certiqs_key.protocol_compiler.feasibility import (
    SUPPLIED_WITNESS,
    FeasibilityCheck,
    check_feasibility,
)
from certiqs_key.protocol_compiler.reasons import (
    CHECK_REFUSAL_REASONS,
    Refusal,
    RefusalReason,
)
from certiqs_key.protocol_compiler.spec import (
    PERP,
    AnnouncementClass,
    KeyValue,
    Party,
    Sifting,
)
from certiqs_key.protocol_compiler.transcript import (
    SUMMATION_PREDICATE,
    PredicateOutcome,
    PredicateSource,
    sector_map_predicates,
)

__all__ = [
    "CHECK_IDS",
    "CHECK_TARGET_CONDITIONS",
    "CheckOutcome",
    "DecidabilityCounts",
    "ValidationResult",
    "check_v1",
    "check_v2",
    "check_v3",
    "check_v4",
    "check_v5",
    "check_v6",
    "check_v7",
    "check_v8",
    "decidability_counts",
    "reconstruct_holder_key_rule",
    "reconstruct_sifting_predicate",
    "validate",
]

#: The eight checks of Definition ``def:validator``, in its order.
CHECK_IDS: tuple[str, ...] = ("V1", "V2", "V3", "V4", "V5", "V6", "V7", "V8")

#: The target condition each check pairs with. V7 is the one pairing that is
#: not an equivalence (Theorem ``thm:validator-soundness`` (iii)).
CHECK_TARGET_CONDITIONS: dict[str, str] = {
    "V1": "D(i)",
    "V2": "D(ii)",
    "V3": "D(iii)",
    "V4": "D(iv)",
    "V5": "D(v)",
    "V6": "D(vi)",
    "V7": "D(vii)",
    "V8": "D(viii)",
}


@dataclass(frozen=True)
class CheckOutcome:
    """The verdict of one check, with the refusal it produces when it fails.

    ``evaluated`` is ``False`` for a check that could not be READ against the
    candidate at all, because an earlier check found the data it quantifies
    over untabulated or ill-posed. Such a check is reported as FAILING and
    NEVER as passing -- the ``fail_closed`` convention -- and the flag is what
    keeps "this check refused" distinguishable from "this check never ran".
    """

    check: str
    passed: bool
    refusal: Refusal | None
    evaluated: bool = True
    #: THE PER-PREDICATE TRANSCRIPT OF THIS CHECK, in the order the check
    #: decided its elements: the ``gate_report`` row's second half, for the
    #: decisions its ``recorded_predicates`` enumeration keys to this check. A
    #: DEFAULTED FIELD, so that every existing construction site stays valid
    #: and an unfilled transcript is a visible ``()`` rather than an absence.
    predicates: tuple[PredicateOutcome, ...] = ()

    @classmethod
    def passing(
        cls, check: str, predicates: tuple[PredicateOutcome, ...] = ()
    ) -> CheckOutcome:
        """Return a passing verdict for ``check``, carrying what it decided."""
        return cls(check=check, passed=True, refusal=None, predicates=predicates)

    @classmethod
    def failing(
        cls,
        check: str,
        detail: str,
        predicates: tuple[PredicateOutcome, ...] = (),
    ) -> CheckOutcome:
        """Return a failing verdict, carrying the reason that names ``check``.

        ``predicates`` is what the check had decided when it returned -- up to
        and including the failing decision where that decision is one the
        ``gate_report`` row keys, and empty where the failure is one of the
        clauses its scope note excludes.
        """
        return cls(
            check=check,
            passed=False,
            refusal=Refusal(reason=CHECK_REFUSAL_REASONS[check], detail=detail),
            predicates=predicates,
        )

    @classmethod
    def not_evaluated(cls, check: str, blocked_by: str, why: str) -> CheckOutcome:
        """Return a failing, unevaluated verdict naming what blocked it."""
        return cls(
            check=check,
            passed=False,
            refusal=Refusal(
                reason=CHECK_REFUSAL_REASONS[check],
                detail=(
                    f"not evaluated: {blocked_by} failed, and {why}. REPORTED AS "
                    "FAILING AND NEVER AS PASSING"
                ),
            ),
            evaluated=False,
        )


def _map_refusal(
    check: str,
    what: str,
    disagreement: SectorMapDisagreement,
    predicates: tuple[PredicateOutcome, ...] = (),
) -> CheckOutcome:
    """Return the ``sector_map_mismatch`` refusal, naming the first position.

    Check V1: "A disagreement on any of the four is a refusal with reason
    ``sector_map_mismatch``, NAMING THE FIRST POSITION AT WHICH THE LISTS
    DIFFER." The position travels with the refusal, which is what lets a
    supplier find the entry it wrote against the wrong map.
    """
    where = (
        "the block kind"
        if disagreement.position is None
        else f"position {disagreement.position}"
    )
    return CheckOutcome(
        check=check,
        passed=False,
        refusal=Refusal(
            reason=RefusalReason.SECTOR_MAP_MISMATCH,
            detail=(
                f"{what} carries a sector map disagreeing with the emitted map "
                f"in {disagreement.component}, first at {where}: "
                f"{disagreement.detail}"
            ),
        ),
        predicates=predicates,
    )


def _first_difference(
    declared: tuple[Label, ...], fixed: tuple[Label, ...]
) -> int | None:
    """Return the first position at which two orders differ, 0-based.

    The index a failed order comparison is recorded with. ``None`` where the
    two agree elementwise and differ only in LENGTH, which is not a position in
    either list; nothing is invented for it.
    """
    for position, (left, right) in enumerate(zip(declared, fixed, strict=False)):
        if left != right:
            return position
    return None


@dataclass(frozen=True)
class _ComparedFamily:
    """One Q-operator family V1 compares, under both of its names.

    ``machine_key`` is the name the refusal detail carries -- V1 names the
    families "BY MACHINE KEY, because at a non-trivial chain TWO DIFFERENT
    FAMILIES COULD ANSWER TO 'THE RECEIVER POVM'" -- and ``element`` is the
    transcript's spelling of the same object
    (:mod:`certiqs_key.protocol_compiler.transcript`, the element table). A
    RECORD AND NOT A TRIPLE: three positional fields at one call site are
    exactly the misreading :class:`
    ~certiqs_key.protocol_compiler.gates.GateEntry` argues against.
    """

    machine_key: str
    element: str
    operator: BlockOperator


def _compared_families(
    declaration: CandidateDeclaration,
) -> tuple[_ComparedFamily, ...]:
    """Return EXACTLY the Q-operator families V1 compares, named by machine key.

    Check V1: "The families compared are EXACTLY THE Q-OPERATOR FAMILIES of
    Eq. eq:declaration -- which is the list D(i) quantifies over, AND NO WIDER
    ONE -- named by machine key, because at a non-trivial chain TWO DIFFERENT
    FAMILIES COULD ANSWER TO 'THE RECEIVER POVM': the emitted Bob family
    ``bob_povm``, {F_v} ...; AND EACH CONSTRAINT ENTRY of CList ... Those two
    slots are THE WHOLE of Eq. eq:declaration that carries a Q-operator, so THE
    LIST IS EXHAUSTIVE BY CONSTRUCTION RATHER THAN BY ENUMERATION."

    THREE OBJECTS ARE DELIBERATELY ABSENT AND AN IMPLEMENTATION MUST NOT ADD
    THEM: ``receiver_povm`` (not a Q-operator family at a non-trivial receiver
    segment, and "INCLUDING IT AT A NON-TRIVIAL CHAIN WOULD NOT BE FAIL-CLOSED
    IN THE USEFUL SENSE: IT WOULD REFUSE EVERY SUCH CHAIN"); the chain's last
    target descriptor, decided at (C1) "AND NOWHERE ELSE"; and a supplied
    feasibility witness, compared at V7 branch (c). Carrying any of them here
    "would make V1 REFUSE A CANDIDATE THAT D(i)-D(viii) ADMIT and so FALSIFY
    Theorem thm:validator-soundness (ii)".
    """
    families: list[_ComparedFamily] = [
        _ComparedFamily(
            machine_key=f"bob_povm[{label!r}]",
            element=f"F_{label}",
            operator=declaration.bob_povm[label],
        )
        for label in declaration.bob_alphabet
        if label in declaration.bob_povm
    ]
    families.extend(
        _ComparedFamily(
            machine_key=f"constraint_list[{index}].operator",
            element=f"O^_{index + 1}",
            operator=entry.operator,
        )
        for index, entry in enumerate(declaration.constraint_list)
    )
    return tuple(families)


def _alice_compared_data(
    declaration: CandidateDeclaration,
) -> tuple[_ComparedFamily, ...]:
    """Return ALICE'S DECLARED DATA, whose maps V1 compares in the general format.

    V1 in the general format: "the map carried by ``tau_A``, the map carried by
    each operator of Alice's measurement slot -- ``M_x`` in POVM form, ``N_x`` in
    ensemble form -- and the map carried by each ``general`` ``Theta_k`` are each
    compared against that factor's map in the same four components". That
    comparison "is what makes condition (T) of Definition ``def:exact`` decided
    for Alice's data, which its general-format paragraph calls non-empty for them;
    IT IS DECIDED HERE AND NOWHERE ELSE, and without it a candidate whose Alice
    block list carried a different block kind, a different identifier list or a
    different order would pass every check and violate D(i)."

    THE LIST IS EMPTY WHERE NO FACTOR IS TAGGED ``A``: "there is one Alice block
    and no map to compare, which is the accepted reading". A ``general``
    ``Theta_k`` is included only where it arrives AS A BLOCK LIST, which is the
    only shape (DX2) gives it; a matrix right-hand side carries no map and is
    typed at V6 instead.
    """
    if declaration.alice_factor is None:
        return ()
    compared: list[_ComparedFamily] = []
    marginal = declaration.alice_marginal_blocks
    if marginal is not None:
        compared.append(
            _ComparedFamily(
                machine_key="alice_marginal_blocks",
                element="tau_A",
                operator=marginal,
            )
        )
    if declaration.alice_slot is not None:
        slot = declaration.alice_slot
        key = "alice_ensemble" if slot.is_ensemble else "alice_povm_blocks"
        symbol = "N" if slot.is_ensemble else "M"
        compared.extend(
            _ComparedFamily(
                machine_key=f"{key}[{label!r}]",
                element=f"{symbol}_{label}",
                operator=slot.member(label),
            )
            for label in slot.alphabet
        )
    compared.extend(
        _ComparedFamily(
            machine_key=f"constraint_list[{index}].rhs",
            element=f"Theta_{index + 1}",
            operator=entry.rhs,
        )
        for index, entry in enumerate(declaration.constraint_list)
        if isinstance(entry.rhs, BlockOperator)
    )
    return tuple(compared)


def _factor_prefixes(declaration: CandidateDeclaration) -> tuple[str, ...]:
    """Return the transcript prefix of each measured factor, in factor order.

    ``"<factor>:"`` where more than one factor is measured and ``""`` at one,
    the transcript module's factor rule: the keys of the accepted format do not
    move, and two factors of one party do not share a key.
    """
    labels = declaration.measured_factor_labels
    if len(labels) <= 1:
        return ("",) * len(labels)
    return tuple(f"{label}:" for label in labels)


def _general_compared_families(
    declaration: CandidateDeclaration,
) -> tuple[tuple[_ComparedFamily, SectorStructure], ...]:
    """Return every declared operator V1 compares IN THE GENERAL FORMAT, with its map.

    V1: "the map carried by each declared family ``{F^f_{v_f}}`` is compared
    against the map of factor ``f``, and the map carried by each entry's operator
    ``hat O_k`` against the map of that entry's scope, in the same four
    components". Beside them :func:`_alice_compared_data`, against the map of the
    factor tagged ``A``.

    THE LIST IS AGAIN EXHAUSTIVE BY CONSTRUCTION: "the objects D(i) quantifies
    over are the per-factor families, the entries' operators and Alice's declared
    data -- the product family being no datum, the lifted operator of a scoped
    entry being no datum", and the two objects deliberately outside it, a chain's
    target descriptors and a supplied witness, stay outside it for the reasons the
    accepted check gives.

    AN ENTRY WHOSE SCOPE NAMES NO FACTOR IS NOT COMPARED HERE. Its refusal is
    V6's ``constraint_scope_not_a_factor``, and comparing its operator against a
    map this function would have to choose would refuse it for the wrong reason.

    A FAMILY MEMBER'S ELEMENT NAMES ITS FACTOR where more than one is measured
    (``<factor>:F^<party>_<v>``, the transcript module's factor rule): a party
    may hold two factors, and their members would otherwise share a key.
    """
    compared: list[tuple[_ComparedFamily, SectorStructure]] = []
    factors = declaration.measured_factors
    factor_prefixes = _factor_prefixes(declaration)
    if declaration.bob_factors is not None:
        for position, family in enumerate(declaration.bob_factors.factors):
            for label in family.alphabet:
                compared.append(
                    (
                        _ComparedFamily(
                            machine_key=f"bob_povm_factors[{position}][{label!r}]",
                            element=(
                                f"{factor_prefixes[position]}"
                                f"F^{family.party}_{label}"
                            ),
                            operator=family.member(label),
                        ),
                        factors[position].sectors,
                    )
                )
    else:
        compared.extend(
            (family, declaration.sectors)
            for family in _compared_families(declaration)
            if family.machine_key.startswith("bob_povm[")
        )
    for index, entry in enumerate(declaration.constraint_list):
        scope = entry.scope
        factor = declaration.measured_factors[0] if scope is None else (
            declaration.measured_factor(scope)
        )
        if factor is None:
            continue
        compared.append(
            (
                _ComparedFamily(
                    machine_key=f"constraint_list[{index}].operator",
                    element=f"O^_{index + 1}",
                    operator=entry.operator,
                ),
                factor.sectors,
            )
        )
    compared.extend(
        (family, declaration.alice_sectors)
        for family in _alice_compared_data(declaration)
    )
    return tuple(compared)


def _check_v1_general(declaration: CandidateDeclaration) -> CheckOutcome:
    """V1's GENERAL-FORMAT reading (``def:validator``, V1 in the general format).

    What the accepted reading does not reach, conjunct for conjunct: the
    transcript's tables and their SIGNATURE clause; the factorised map's dimension
    identities per factor, over the product and on Alice's side; the restriction
    of ``idxm`` to each factor's sector set and to ``T``; and the four-component
    comparison run FACTOR BY FACTOR together with Alice's declared data.

    WHAT IS NOT COMPARED, and the absence is the claim's: "the product orders on
    ``S`` and ``V`` and the order on the joint sectors are DERIVED by (DX1) and
    (DX3) and are not compared, there being no second datum to compare them with".

    ONE BLOCK KIND ACROSS THE FACTORS is refused by
    :class:`~certiqs_key.foundations.blocks.FactorisedSectorMap` at construction, so a
    candidate that reaches this function carries one; where the factor list is
    ASSEMBLED, in the compilation map, that refusal is
    ``sector_map_mismatch`` naming the first factor at which the kind differs, and
    the map is built there for exactly that reason.
    """
    predicates: list[PredicateOutcome] = []
    transcript = declaration.transcript
    if transcript is not None:
        readouts = {
            str(Party.ALICE): declaration.partition.alice_readout_alphabet,
            str(Party.BOB): declaration.partition.bob_readout_alphabet,
        }
        for index, message in enumerate(transcript.messages, start=1):
            if not message.alphabet:  # pragma: no cover - Message refuses it
                return CheckOutcome.failing(
                    "V1", f"the alphabet C_{index} of message {index} is empty"
                )
        missing = transcript.missing_cell(readouts)
        if missing is not None:
            position, readout, prefix = missing
            return CheckOutcome.failing(
                "V1",
                f"the table of message {position + 1} is not tabulated at "
                f"readout {readout!r} with the earlier messages {list(prefix)}; "
                "every a_m is total on O_pi_m x C_1 x ... x C_{m-1} (D(viii)), "
                "which is also the SIGNATURE clause",
            )
    for factor in declaration.sector_factorisation.factors if (
        declaration.sector_factorisation is not None
    ) else ():
        if any(dim < 1 for dim in factor.sectors.dims):  # pragma: no cover - typed
            return CheckOutcome.failing(
                "V1",
                f"a sector dimension of the factor scoped to {factor.party!r} is "
                "below 1",
            )
    measured = declaration.measured_factors
    if not measured:
        return CheckOutcome.failing(
            "V1",
            "the factorised sector map carries no factor tagged Q; (DX1) asks "
            "for at least one measured factor",
        )
    product = 1
    for factor in measured:
        product *= factor.sectors.total_dim
    if product != declaration.q_dim:
        return CheckOutcome.failing(
            "V1",
            f"d_Q = {declaration.q_dim} differs from prod_f sum_{{s_f}} "
            f"d_{{f,s_f}} = {product} (D(i) in the general format)",
        )
    alice_sectors = declaration.alice_sectors
    if alice_sectors.total_dim != declaration.alice_dim:
        return CheckOutcome.failing(
            "V1",
            f"d_A = {declaration.alice_dim} differs from sum_t d_{{A_t}} = "
            f"{alice_sectors.total_dim} (D(i) in the general format)",
        )
    index_map = declaration.label_index_map
    if index_map is not None:
        order = index_map.forward.get("S")
        if order is None:
            return CheckOutcome.failing(
                "V1", "the emitted index map does not index the sector set S"
            )
        declared_order = tuple(
            label for label, _ in sorted(order.items(), key=lambda item: item[1])
        )
        ordered = declared_order == declaration.sectors.labels
        predicates.append(
            PredicateOutcome(
                source=PredicateSource.V1,
                predicate="idx|_S is the total order Smap fixes",
                element="idxm|_S",
                block=None,
                outcome=ordered,
                first_failure_index=(
                    None
                    if ordered
                    else _first_difference(declared_order, declaration.sectors.labels)
                ),
            )
        )
        if not ordered:
            return CheckOutcome.failing(
                "V1",
                f"idx|_S orders the sectors {declared_order} while the product "
                f"map fixes {declaration.sectors.labels}; the product order is "
                "DERIVED by (DX1) and is not a second choice",
                tuple(predicates),
            )
    for compared, against in _general_compared_families(declaration):
        disagreement = against.disagreement(compared.operator.sector_map)
        predicates.extend(
            sector_map_predicates(PredicateSource.V1, compared.element, disagreement)
        )
        if disagreement is not None:
            return _map_refusal(
                "V1", compared.machine_key, disagreement, tuple(predicates)
            )
    return CheckOutcome.passing("V1", tuple(predicates))


def check_v1(declaration: CandidateDeclaration) -> CheckOutcome:
    """V1 -- finiteness and totality, and ``d_Q = sum_s d_s``.

    "Every declared alphabet is finite and non-empty and every declared map is
    tabulated on all of its stated domain; every declared system carries a
    finite dimension; and ``d_Q = sum_s d_s``."

    TWO OF V1'S CLAUSES ARE IN THE TRANSCRIPT AND THE REST ARE NOT, and the
    ``gate_report`` row decides which. Its ``recorded_predicates`` keys "V1's
    sector-map comparison, reported per DECLARED Q-OPERATOR family ... and per
    component (block kind, identifiers, order, dimensions), together with its
    comparison of ``idxm``'s sector order against ``Smap``'s, which is the last
    clause of D(i)"; and its scope note excludes "V1's finiteness,
    non-emptiness, totality and ``d_Q = sum_s d_s`` clauses" by name, those
    being recorded through gate (G1)'s outcome and, on a failure, through
    ``refusal``. Every early return below therefore carries an EMPTY
    transcript, and the two recorded clauses are the last two the check runs.
    """
    predicates: list[PredicateOutcome] = []
    alphabets: tuple[tuple[str, tuple[Label, ...]], ...] = (
        ("X", declaration.alice_alphabet),
        ("V", declaration.bob_alphabet),
        ("S", declaration.sectors.labels),
        ("O_A", declaration.partition.alice_readout_alphabet),
        ("O_B", declaration.partition.bob_readout_alphabet),
        ("C_A", declaration.alice_announcement_alphabet),
        ("C_B", declaration.bob_announcement_alphabet),
        ("Chat", declaration.acceptance_alphabet),
    )
    for name, labels in alphabets:
        if not labels:
            return CheckOutcome.failing("V1", f"the declared alphabet {name} is empty")
        if len(set(labels)) != len(labels):
            return CheckOutcome.failing(
                "V1", f"the declared alphabet {name} repeats a label"
            )
    if not declaration.key_alphabet:
        return CheckOutcome.failing("V1", "the declared key alphabet Z is empty")
    if declaration.alice_dim < 1:
        return CheckOutcome.failing(
            "V1", f"d_A = {declaration.alice_dim} is not a finite dimension >= 1"
        )
    if any(dim < 1 for dim in declaration.sectors.dims):
        return CheckOutcome.failing("V1", "a declared sector dimension is below 1")

    pairs = declaration.outcome_pairs()
    for x, v in pairs:
        for table_name, table in (
            ("pi_A", declaration.partition.alice_readout),
            ("pi_B", declaration.partition.bob_readout),
        ):
            if (x, v) not in table:
                return CheckOutcome.failing(
                    "V1", f"the readout {table_name} is not tabulated at ({x!r}, {v!r})"
                )
        if (x, v) not in declaration.key_map:
            return CheckOutcome.failing(
                "V1", f"the key map r is not tabulated at ({x!r}, {v!r})"
            )
    # THE ANNOUNCEMENT SLOT'S TOTALITY, IN WHICHEVER FORM IT IS DECLARED. With a
    # transcript the two maps are no slot at all and the clause is on the
    # transcript's tables, which `_check_v1_general` decides; (DX5) makes the
    # accepted pair the case L = 2, so the two readings are one clause read on the
    # slot that is filled.
    if declaration.transcript is None:
        for readout in declaration.partition.alice_readout_alphabet:
            if readout not in declaration.announce_alice:
                return CheckOutcome.failing(
                    "V1", f"a_A is not tabulated at the readout {readout!r}"
                )
        for readout in declaration.partition.bob_readout_alphabet:
            if readout not in declaration.announce_bob:
                return CheckOutcome.failing(
                    "V1", f"a_B is not tabulated at the readout {readout!r}"
                )
    for kappa in declaration.announcement_classes():
        if kappa not in declaration.tabulated_classes():
            return CheckOutcome.failing(
                "V1",
                f"phi is not tabulated on the announcement class {kappa}; a "
                "partial phi loses probability mass (Remark rem:phitotal) and "
                "is refused rather than completed with a default value",
            )
    # ALICE'S AND BOB'S OPERATORS ARE LOOKED UP IN THE SPELLING THAT CARRIES THEM
    # (DX2), (DX3), (DX4): the block list of the declared slot where one is
    # declared, and the accepted mapping otherwise. A letter with no operator is
    # refused either way; what moves is where the operator is read from.
    if declaration.alice_slot is None:
        for label in declaration.alice_alphabet:
            if label not in declaration.alice_povm:
                return CheckOutcome.failing(
                    "V1", f"no matrix for Alice's outcome {label!r}"
                )
    elif set(declaration.alice_slot.alphabet) != set(declaration.alice_alphabet):
        return CheckOutcome.failing(
            "V1",
            "Alice's measurement slot is declared over an alphabet other than "
            f"the emitted X: {list(declaration.alice_slot.alphabet)} against "
            f"{list(declaration.alice_alphabet)}",
        )
    if declaration.bob_factors is None:
        for label in declaration.bob_alphabet:
            if label not in declaration.bob_povm:
                return CheckOutcome.failing(
                    "V1", f"no matrix for Bob's outcome {label!r}"
                )
    elif declaration.bob_factors.alphabet() != declaration.bob_alphabet:
        return CheckOutcome.failing(
            "V1",
            "the emitted outcome alphabet V is not the product alphabet the "
            f"factor list derives: {list(declaration.bob_alphabet)} against "
            f"{list(declaration.bob_factors.alphabet())}; the product order is "
            "DERIVED by (DX3) and is not a second choice",
        )

    declared_q = declaration.q_dim
    if declared_q != sum(declaration.sectors.dims):  # pragma: no cover - invariant
        return CheckOutcome.failing("V1", f"d_Q = {declared_q} differs from sum_s d_s")

    if declaration.is_general_format:
        general = _check_v1_general(declaration)
        if not general.passed:
            return general
        predicates.extend(general.predicates)
        for label in declaration.alice_alphabet:
            if (
                declaration.alice_slot is None
                and dimension(declaration.alice_povm[label]) != declaration.alice_dim
            ):  # pragma: no cover - the dense spelling is the accepted branch
                return CheckOutcome.failing(
                    "V1",
                    f"M_{label!r} does not have the declared dimension d_A",
                    tuple(predicates),
                )
        return CheckOutcome.passing("V1", tuple(predicates))

    # THE LAST CLAUSE OF D(i): "the restriction of idx to S IS THE TOTAL ORDER
    # THE SECTOR MAP FIXES". Definition def:target states it as a target
    # condition and not only as a check, because "THE SECTOR ORDER A CONSUMER
    # COMPARES AGAINST ITS OWN MAP AND THE SUMMATION ORDER IT READS OFF THE
    # EMITTED `label_index_map` MUST BE THE SAME ORDER".
    index_map = declaration.label_index_map
    if index_map is not None:
        sector_order = index_map.forward.get("S")
        if sector_order is None:
            return CheckOutcome.failing(
                "V1", "the emitted index map does not index the sector set S"
            )
        declared_order = tuple(
            label for label, _ in sorted(sector_order.items(), key=lambda item: item[1])
        )
        fixed_order = declaration.sectors.labels
        ordered = declared_order == fixed_order
        predicates.append(
            PredicateOutcome(
                source=PredicateSource.V1,
                predicate="idx|_S is the total order Smap fixes",
                element="idxm|_S",
                block=None,
                outcome=ordered,
                first_failure_index=(
                    None if ordered else _first_difference(declared_order, fixed_order)
                ),
            )
        )
        if not ordered:
            return CheckOutcome.failing(
                "V1",
                f"idx|_S orders the sectors {declared_order} while the sector "
                f"map fixes {declaration.sectors.labels}; the order on S is "
                "NOT A SECOND CHOICE (Definition def:compile)",
                tuple(predicates),
            )

    # THE FOUR-COMPONENT SECTOR-MAP COMPARISON, over exactly the Q-operator
    # families of Eq. eq:declaration.
    for family in _compared_families(declaration):
        disagreement = declaration.sectors.disagreement(family.operator.sector_map)
        predicates.extend(
            sector_map_predicates(PredicateSource.V1, family.element, disagreement)
        )
        if disagreement is not None:
            return _map_refusal(
                "V1", family.machine_key, disagreement, tuple(predicates)
            )
    for label in declaration.alice_alphabet:
        if dimension(declaration.alice_povm[label]) != declaration.alice_dim:
            return CheckOutcome.failing(
                "V1",
                f"M_{label!r} does not have the declared dimension d_A",
                tuple(predicates),
            )
    return CheckOutcome.passing("V1", tuple(predicates))


def _check_v2_general(declaration: CandidateDeclaration) -> CheckOutcome:
    """V2's GENERAL-FORMAT reading (``def:validator``, V2 in the general format).

    "The slot holds ``nomarg``, or a block list ``(tau_A^(t))_t`` against the
    ``A`` factor's map with ``tau_A^(t)`` Hermitian and positive semidefinite for
    every ``t`` and ``sum_t tr tau_A^(t) = 1``, each trace accumulated over the row
    index and the block traces then added in the declared order of ``T``, with
    EVERY one of those additions verified to round nowhere; a failure of the last
    is ``alice_marginal_trace_rounds``. And where Alice's measurement slot is in
    ensemble form, additionally ``tau_A^(t) != 0`` for every ``t``, a comparison of
    declared entries with the datum ``0``, refused with
    ``alice_sector_marginal_zero`` naming the sector."

    AT ``|T| = 1`` THIS IS V2 ABOVE, "the one block being the whole of ``A``": the
    per-block loop runs once, the outer sum has one term, and the non-zero clause
    is the one the accepted check already covers by the trace being one.

    A SINGULAR BLOCK IS ADMISSIBLE AND NO RANK IS READ (``lem:choi-factor`` (iv)):
    what is decided is Hermiticity, positivity, the total trace and, in ensemble
    form, a comparison with zero.
    """
    marginal = declaration.marginal_blocks
    if marginal is None:
        return CheckOutcome.passing("V2")
    sectors = declaration.alice_sectors
    predicates: list[PredicateOutcome] = []

    def record(
        predicate: str, block: str | None, outcome: bool, index: int | None = None
    ) -> None:
        """Record one of V2's decisions, PER ALICE SECTOR where it is per block."""
        predicates.append(
            PredicateOutcome(
                source=PredicateSource.V2,
                predicate=predicate,
                element="tau_A",
                block=block,
                outcome=outcome,
                first_failure_index=None if outcome else index,
                first_inexact_index=(
                    None
                    if outcome or predicate != SUMMATION_PREDICATE
                    else index
                ),
            )
        )

    for position, block in enumerate(marginal.blocks):
        sector = sectors.labels[position]
        hermitian = is_hermitian(block)
        record("(H)", sector, hermitian, position + 1)
        if not hermitian:
            return CheckOutcome.failing(
                "V2",
                f"the declared tau_A block at Alice sector {sector!r} is not "
                "Hermitian",
                tuple(predicates),
            )
        positive = is_positive_semidefinite(block)
        record("(P)", sector, positive, position + 1)
        if not positive:
            return CheckOutcome.failing(
                "V2",
                f"the declared tau_A block at Alice sector {sector!r} is not "
                "positive semidefinite",
                tuple(predicates),
            )

    # sum_t tr tau_A^(t) = 1, the row traces first and the block traces then, EVERY
    # addition of both stages required to round nowhere.
    running = Cx(Fraction(0), Fraction(0))
    rounds_nowhere = True
    first_inexact: int | None = None
    for position, block in enumerate(marginal.blocks, start=1):
        accumulated = trace_in_row_order(block)
        if not accumulated.rounds_nowhere and rounds_nowhere:
            rounds_nowhere = False
            first_inexact = position
        if rounds_nowhere and not addition_rounds_nowhere(running, accumulated.value):
            rounds_nowhere = False
            first_inexact = position
        running = running + accumulated.value
    trace_is_one = running == Cx(Fraction(1), Fraction(0))
    record("(C)", None, trace_is_one, None)
    if not trace_is_one:
        return CheckOutcome.failing(
            "V2",
            "the declared tau_A does not have total trace one, sum_t tr "
            "tau_A^(t) = 1; in particular a slot whose blocks are all zero is "
            "inadmissible, while a SINGULAR block is admissible",
            tuple(predicates),
        )
    record(SUMMATION_PREDICATE, None, rounds_nowhere, first_inexact)
    if not rounds_nowhere:
        return CheckOutcome(
            check="V2",
            passed=False,
            refusal=Refusal(
                reason=RefusalReason.ALICE_MARGINAL_TRACE_ROUNDS,
                detail=(
                    "sum_t tr tau_A^(t) = 1 holds of the declared numbers, but "
                    "one of the additions forming it ROUNDS: the first is at "
                    f"Alice sector {first_inexact}. The trace is read as an "
                    "IDENTITY OF REAL NUMBERS exactly as a completeness sum is "
                    "(Definition def:exact, the general format)"
                ),
            ),
            predicates=tuple(predicates),
        )

    # THE ENSEMBLE FORM'S ONE EXTRA SIDE CONDITION: tau_A^(t) != 0 per sector, a
    # comparison of declared entries with the datum 0 (eq:ensembleform). It is
    # decided only where that form is declared, because in POVM form the
    # denominator eq:ensemblepovm divides by does not arise.
    if declaration.alice_form is AliceForm.ENSEMBLE:
        for position, block in enumerate(marginal.blocks, start=1):
            sector = sectors.labels[position - 1]
            zero = Cx(Fraction(0), Fraction(0))
            non_zero = any(entry != zero for row in block for entry in row)
            record("tau_A^(t) != 0", sector, non_zero, position)
            if not non_zero:
                return CheckOutcome(
                    check="V2",
                    passed=False,
                    refusal=Refusal(
                        reason=RefusalReason.ALICE_SECTOR_MARGINAL_ZERO,
                        detail=(
                            f"the declared tau_A block at Alice sector "
                            f"{sector!r} is ZERO, and the ensemble form requires "
                            "tau_A^(t) != 0 for every t (eq:ensembleform). It is "
                            "a comparison of declared entries with the datum 0; a "
                            "SINGULAR block is admissible and no rank is read"
                        ),
                    ),
                    predicates=tuple(predicates),
                )
    return CheckOutcome.passing("V2", tuple(predicates))


def check_v2(declaration: CandidateDeclaration) -> CheckOutcome:
    """V2 -- the marginal slot holds ``nomarg``, or a state.

    "The slot holds ``nomarg``, or a matrix ``tau_A`` on ``A`` -- ONE BLOCK,
    ``A`` carrying no sector decomposition -- satisfying ``tau_A =
    tau_A^dag``, ``tau_A >= 0`` and ``tr tau_A = 1``, EACH DECIDED EXACTLY, and
    with the trace accumulated over the row index VERIFIED TO ROUND NOWHERE; a
    failure of the last is refused with reason
    ``alice_marginal_trace_rounds``." A SINGULAR ``tau_A`` IS ADMISSIBLE and
    ``tau_A = 0`` is NOT, and both clauses are needed: ``diag(2, -1)`` is
    Hermitian with trace one and is not positive semidefinite, and the zero
    matrix is positive semidefinite with trace zero.
    """
    if declaration.is_general_format:
        return _check_v2_general(declaration)
    marginal = declaration.alice_marginal
    if marginal is None:
        # ``nomarg``: there is no tau_A, so none of the four predicates is
        # decided and none is recorded. The slot's own contents are the
        # marginal-slot presence test, which the row's scope note does not key.
        return CheckOutcome.passing("V2")
    if dimension(marginal) != declaration.alice_dim:
        return CheckOutcome.failing(
            "V2", "the declared tau_A does not have the declared dimension d_A"
        )
    predicates: list[PredicateOutcome] = []

    def record(predicate: str, outcome: bool, inexact: int | None = None) -> None:
        """Record one of V2's four decisions on ``tau_A``."""
        predicates.append(
            PredicateOutcome(
                source=PredicateSource.V2,
                predicate=predicate,
                element="tau_A",
                block=None,
                outcome=outcome,
                first_failure_index=None if outcome else inexact,
                first_inexact_index=None if outcome else inexact,
            )
        )

    hermitian = is_hermitian(marginal)
    record("(H)", hermitian)
    if not hermitian:
        return CheckOutcome.failing(
            "V2", "the declared tau_A is not Hermitian", tuple(predicates)
        )
    positive = is_positive_semidefinite(marginal)
    record("(P)", positive)
    if not positive:
        return CheckOutcome.failing(
            "V2",
            "the declared tau_A is not positive semidefinite",
            tuple(predicates),
        )
    accumulated = trace_in_row_order(marginal)
    trace_is_one = accumulated.value == Cx(Fraction(1), Fraction(0))
    # (C) ON tau_A IS THE TRACE IDENTITY, and it is spelled (C) because
    # Definition def:exact reads it as one: the trace is "read below as an
    # IDENTITY OF REAL NUMBERS exactly as a completeness sum is", in the
    # paragraph that states tau_A's own three conditions.
    record("(C)", trace_is_one)
    if not trace_is_one:
        return CheckOutcome.failing(
            "V2",
            "the declared tau_A does not have trace one; in particular the zero "
            "matrix is inadmissible, while a SINGULAR tau_A is admissible",
            tuple(predicates),
        )
    record(
        SUMMATION_PREDICATE,
        accumulated.rounds_nowhere,
        accumulated.first_inexact_row,
    )
    if not accumulated.rounds_nowhere:
        return CheckOutcome(
            check="V2",
            passed=False,
            refusal=Refusal(
                reason=RefusalReason.ALICE_MARGINAL_TRACE_ROUNDS,
                detail=(
                    "tr tau_A = 1 holds of the declared numbers, but the trace "
                    "accumulated over the row index ROUNDS: the first inexact "
                    f"addition is at row {accumulated.first_inexact_row}. The "
                    "trace is read as an IDENTITY OF REAL NUMBERS exactly as a "
                    "completeness sum is (Definition def:exact)"
                ),
            ),
            predicates=tuple(predicates),
        )
    return CheckOutcome.passing("V2", tuple(predicates))


def _check_v3_general(declaration: CandidateDeclaration) -> CheckOutcome:
    """V3's GENERAL-FORMAT reading (``def:validator``, V3 in the general format).

    PER MEASURED FACTOR: for every ``f``, every ``v_f`` and every ``s_f``,
    ``F^{f,(s_f)}_{v_f}`` Hermitian and positive semidefinite, and for each
    ``s_f`` the sum ``sum_{v_f} F^{f,(s_f)}_{v_f} = 1_{Q_{f,s_f}}`` with its
    declared-order sum verified to round nowhere -- reason
    ``bob_povm_summation_rounds``, "carrying the FACTOR, the sector and the outcome
    index at which the first inexact addition occurred".

    ON ALICE'S DATA, BLOCK BY BLOCK ALONG ``T``: in POVM form ``M^(t)_x``
    Hermitian and positive semidefinite and ``sum_x M^(t)_x = 1_{A_t}`` per sector
    (``alice_povm_summation_rounds``, carrying the Alice sector); in ensemble form
    ``N^(t)_x`` Hermitian and positive semidefinite and, IN PLACE OF THE
    COMPLETENESS IDENTITY, the identity ``sum_x N^(t)_x = tau^(t)_A`` decided entry
    by entry (``alice_ensemble_marginal_mismatch``) with that sum verified to round
    nowhere (``alice_ensemble_sum_rounds``).

    AN ENSEMBLE-FORM SLOT BESIDE A MARGINAL SLOT HOLDING ``nomarg`` IS REFUSED
    with ``ensemble_form_in_untrusted_mode``, "which is D(iii)'s general-format
    clause and is a decision on which of two slots is filled, NOT ON A NUMBER".

    AND ``hat O_k^(s_{f_k})`` HERMITIAN for every entry and every block of its
    scope.

    NOTHING IS DECIDED ON A PRODUCT BLOCK, ON A LIFTED OPERATOR OR ON THE DENOTED
    FAMILY: "none of the three is a datum, and that the first is a POVM on ``Q``
    and the third a POVM on ``A`` are theorems" ((DX3); ``thm:sifting-and-key`` (v)).
    """
    predicates: list[PredicateOutcome] = []

    def record(
        predicate: str,
        element: str | None,
        block: str | None,
        outcome: bool,
        index: int | None = None,
    ) -> None:
        """Record one of V3's decisions, per element and per block."""
        predicates.append(
            PredicateOutcome(
                source=PredicateSource.V3,
                predicate=predicate,
                element=element,
                block=block,
                outcome=outcome,
                first_failure_index=None if outcome else index,
                first_inexact_index=(
                    None
                    if outcome or predicate != SUMMATION_PREDICATE
                    else index
                ),
            )
        )

    # THE MODE-FORM DECISION FIRST, because it is a decision on WHICH SLOT IS
    # FILLED and every numerical clause below reads the slot it names.
    slot = declaration.alice_slot
    if slot is not None and slot.is_ensemble and not declaration.is_trusted_mode:
        return CheckOutcome(
            check="V3",
            passed=False,
            refusal=Refusal(
                reason=RefusalReason.ENSEMBLE_FORM_IN_UNTRUSTED_MODE,
                detail=(
                    "Alice's measurement slot is declared in ENSEMBLE form beside "
                    "a marginal slot holding nomarg; that form exists in "
                    "TRUSTED-SOURCE MODE ONLY (def:declaration (DX4)), its "
                    "condition sum_x N_x^(t) = tau_A^(t) having no right-hand side "
                    "without a declared tau_A. It is a decision on which of two "
                    "slots is filled and not on a number (D(iii), the general "
                    "format)"
                ),
            ),
        )

    # ALICE'S DATA, BLOCK BY BLOCK ALONG T, IN THE FORM THAT IS DECLARED.
    alice_sectors = declaration.alice_sectors
    for signal, label in enumerate(declaration.alice_alphabet, start=1):
        operator = declaration.alice_operator(label)
        symbol = "N" if declaration.alice_form is AliceForm.ENSEMBLE else "M"
        for position, block in enumerate(operator.blocks):
            sector = alice_sectors.labels[position]
            hermitian = is_hermitian(block)
            record("(H)", f"{symbol}_{label}", sector, hermitian, signal)
            if not hermitian:
                return CheckOutcome.failing(
                    "V3",
                    f"the block of {symbol}_{label!r} at Alice sector {sector!r} "
                    "is not Hermitian",
                    tuple(predicates),
                )
            positive = is_positive_semidefinite(block)
            record("(P)", f"{symbol}_{label}", sector, positive, signal)
            if not positive:
                return CheckOutcome.failing(
                    "V3",
                    f"the block of {symbol}_{label!r} at Alice sector {sector!r} "
                    "is not positive semidefinite",
                    tuple(predicates),
                )

    alice_sums = block_sum_in_declared_order(
        [declaration.alice_operator(label) for label in declaration.alice_alphabet]
    )
    ensemble = declaration.alice_form is AliceForm.ENSEMBLE
    marginal = declaration.marginal_blocks
    family_name = "{N_x}" if ensemble else "{M_x}"
    for position, verdict in enumerate(alice_sums):
        sector = alice_sectors.labels[position]
        if ensemble:
            assert marginal is not None  # the mode decision above guarantees it
            expected = marginal.blocks[position]
            where = _first_entry_difference
            holds = verdict.computed_total_equals(expected)
            record(
                "sum_x N_x^(t) = tau_A^(t)",
                family_name,
                sector,
                holds,
                position + 1,
            )
            if not holds:
                return CheckOutcome(
                    check="V3",
                    passed=False,
                    predicates=tuple(predicates),
                    refusal=Refusal(
                        reason=RefusalReason.ALICE_ENSEMBLE_MARGINAL_MISMATCH,
                        detail=(
                            "the declared-order sum sum_x N_x^(t) differs from "
                            "the declared tau_A block at Alice sector "
                            f"{sector!r}, first at entry "
                            f"{_computed_difference(verdict, expected, where)}. "
                            "The identity of eq:ensembleform stands IN PLACE OF the "
                            "completeness identity and is decided entry by entry"
                        ),
                    ),
                )
        else:
            complete = verdict.computed_total_equals(
                identity(alice_sectors.dims[position])
            )
            record("(C)", family_name, sector, complete, position + 1)
            if not complete:
                return CheckOutcome.failing(
                    "V3",
                    f"the computed sum_x M_x^({sector!r}) is not 1_{{A_t}} -- "
                    "condition (C) fails on that Alice block",
                    tuple(predicates),
                )
        record(
            SUMMATION_PREDICATE,
            family_name,
            sector,
            verdict.rounds_nowhere,
            verdict.first_inexact_index,
        )
        if not verdict.rounds_nowhere:
            reason = (
                RefusalReason.ALICE_ENSEMBLE_SUM_ROUNDS
                if ensemble
                else RefusalReason.ALICE_POVM_SUMMATION_ROUNDS
            )
            return CheckOutcome(
                check="V3",
                passed=False,
                predicates=tuple(predicates),
                refusal=Refusal(
                    reason=reason,
                    detail=(
                        f"the declared-order sum {family_name} rounds at Alice "
                        f"sector {sector!r}, at element "
                        f"{verdict.first_inexact_index} of the emitted index "
                        "order. Condition (S) is on the ADDITIONS, not on the "
                        "operands"
                    ),
                ),
            )

    # PER MEASURED FACTOR: nothing is decided on a product block. Each element
    # names its factor where more than one is measured (the transcript
    # module's factor rule).
    factor_prefixes = _factor_prefixes(declaration)
    for factor_index, factor in enumerate(declaration.measured_factors):
        prefix = factor_prefixes[factor_index]
        if declaration.bob_factors is not None:
            family = declaration.bob_factors.factors[factor_index]
            alphabet = family.alphabet
            members = family.members
            party = family.party
        else:
            alphabet = declaration.bob_alphabet
            members = tuple(declaration.bob_povm[label] for label in alphabet)
            party = factor.party
        for outcome_index, (label, member) in enumerate(
            zip(alphabet, members, strict=True), start=1
        ):
            element = f"{prefix}F^{party}_{label}"
            for position, block in enumerate(member.blocks):
                sector = factor.sectors.labels[position]
                hermitian = is_hermitian(block)
                record("(H)", element, sector, hermitian, outcome_index)
                if not hermitian:
                    return CheckOutcome.failing(
                        "V3",
                        f"a block of {element!r} is not Hermitian",
                        tuple(predicates),
                    )
                positive = is_positive_semidefinite(block)
                record("(P)", element, sector, positive, outcome_index)
                if not positive:
                    return CheckOutcome.failing(
                        "V3",
                        f"a block of {element!r} is not positive semidefinite",
                        tuple(predicates),
                    )
        family_key = f"{prefix}{{F^{party}_v}}"
        for position, verdict in enumerate(block_sum_in_declared_order(members)):
            sector = factor.sectors.labels[position]
            complete = verdict.computed_total_equals(
                identity(factor.sectors.dims[position])
            )
            record("(C)", family_key, sector, complete, position + 1)
            if not complete:
                return CheckOutcome.failing(
                    "V3",
                    f"the computed sum_{{v_f}} F^{party}_v at sector {sector!r} is "
                    "not 1_{Q_{f,s_f}} -- condition (C) fails on that block",
                    tuple(predicates),
                )
            record(
                SUMMATION_PREDICATE,
                family_key,
                sector,
                verdict.rounds_nowhere,
                verdict.first_inexact_index,
            )
            if not verdict.rounds_nowhere:
                return CheckOutcome(
                    check="V3",
                    passed=False,
                    predicates=tuple(predicates),
                    refusal=Refusal(
                        reason=RefusalReason.BOB_POVM_SUMMATION_ROUNDS,
                        detail=(
                            "the declared-order sum sum_{v_f} F^{f,(s_f)}_{v_f} "
                            "rounds at the measured factor "
                            f"{declaration.measured_factor_labels[factor_index]!r} "
                            f"(party {party!r}), sector "
                            f"{sector!r}, at outcome index "
                            f"{verdict.first_inexact_index} of that factor's "
                            "declared order"
                        ),
                    ),
                )

    for index, entry in enumerate(declaration.constraint_list):
        blocks = entry.operator.sector_map.labels
        for position, block in enumerate(entry.operator.blocks):
            hermitian = is_hermitian(block)
            record("(H)", f"O^_{index + 1}", blocks[position], hermitian, index + 1)
            if not hermitian:
                return CheckOutcome.failing(
                    "V3",
                    f"a block of the constraint operator O^_{index + 1} is not "
                    "Hermitian; Eq. eq:feas-general would lose its meaning, not "
                    "merely its soundness (Remark rem:wellposed)",
                    tuple(predicates),
                )
    return CheckOutcome.passing("V3", tuple(predicates))


def _computed_difference(
    verdict: SummationVerdict,
    expected: Matrix,
    where: Callable[[Matrix, Matrix], tuple[int, int] | None],
) -> str:
    """Name where a computed total first differs from ``expected``.

    A computed total that overflowed to an infinity (``None``) differs from
    every declared block, and the refusal says so instead of naming an entry.
    """
    if verdict.computed_total is None:
        return "an entry whose computed sum overflowed to an infinity"
    return str(where(verdict.computed_total, expected))


def _first_entry_difference(left: Matrix, right: Matrix) -> tuple[int, int] | None:
    """Return the first ``(row, column)`` at which two matrices differ, 0-based.

    The index the ``alice_ensemble_marginal_mismatch`` refusal names -- the
    identity of ``eq:ensembleform`` is "decided ENTRY BY ENTRY against the declared
    block of ``tau_A``", so the refusal says which entry. ``None`` where the two
    agree, which is the branch that does not refuse.
    """
    for row, (a, b) in enumerate(zip(left, right, strict=False)):
        for column, (x, y) in enumerate(zip(a, b, strict=False)):
            if x != y:
                return (row, column)
    return None


def check_v3(declaration: CandidateDeclaration) -> CheckOutcome:
    """V3 -- the operator predicates, PER BLOCK AND AT ZERO, plus condition (S).

    "``M_x = M_x^dag`` and ``M_x >= 0`` for each ``x``, and ``sum_x M_x = 1_A``
    with the sum, IN THE EMITTED INDEX ORDER, VERIFIED TO ROUND NOWHERE
    (refusal reason ``alice_povm_summation_rounds``); ``F_v^(s) = F_v^(s)dag``
    and ``F_v^(s) >= 0`` for each ``(v, s)``, and, FOR EACH ``s``,
    ``sum_v F_v^(s) = 1_{Q_s}`` with that sum verified to round nowhere (reason
    ``bob_povm_summation_rounds``, CARRYING THE SECTOR AND THE OUTCOME INDEX at
    which the first inexact addition occurred); and ``O^_k^(s) = O^_k^(s)dag``
    for each ``(k, s)``. EVERY ONE OF THESE IS DECIDED AT ZERO AND AT NO
    WINDOW."

    THERE ARE NO OFF-BLOCK CONDITIONS in this validator: "an emitted Q-operator IS A
    BLOCK LIST, so there is NO ``Pi_s F_v Pi_{s'}`` or ``Pi_s O^_k Pi_{s'}`` TO EVALUATE
    and NOTHING THAT COULD BE NON-ZERO. What decides the structure is V1'S SECTOR-MAP
    COMPARISON, AND NOTHING ELSE." Omitting them is safe because
    :class:`~certiqs_key.foundations.blocks.BlockOperator` cannot carry an off-block
    entry: Definition ``def:exact`` (T) calls one "NOT SMALL BUT
    INEXPRESSIBLE".

    (C) AND (S) ARE READ ON DIFFERENT OBJECTS AND CAN DISAGREE. (C) is read on
    the COMPUTED binary64 total and (S) on the additions that formed it. At Alice's
    basis weights ``fl(0.9)``, ``fl(0.1)``, whose computed sum is exactly ``1``
    and whose exact sum is ``1 + 2**-55``, the first passes and the second
    fails, which is why such a presentation WOULD PASS A TEST WRITTEN ON THE
    COMPUTED TOTAL ALONE.

    Hermiticity of every ``O^_k`` is tested HERE, before any evaluation of
    Eq. ``eq:feas-modes``, because after that point there is no well-defined
    comparison to report a failure of (Remark ``rem:wellposed``).

    THE TRANSCRIPT IS PER BLOCK WHEREVER THE CONDITION IS, which is what the
    ``gate_report`` row asks of "the (H), (P), (C) and (S) decisions of checks
    V2 and V3 on ``tau_A``, on ``{M_x}``, on each emitted Bob block family and
    on each ``hat O_k^(s)``". So the two aggregate calls
    :meth:`~certiqs_key.foundations.blocks.BlockOperator.is_hermitian` and
    :meth:`~certiqs_key.foundations.blocks.BlockOperator.is_positive_semidefinite`
    are unrolled below into the per-block conjunction they are -- SAME
    DECISIONS, SAME ORDER, SAME SHORT CIRCUIT, and therefore the same refusal
    at the same first failure -- because an aggregate verdict cannot be keyed
    by the block that decided it. ``{M_x}`` and ``tau_A`` live on ``A``, which
    carries no sector decomposition, so their ``block`` is ``None``: the
    one-block case of Definition ``def:exact``, for which (T) is empty.
    """
    if declaration.is_general_format:
        return _check_v3_general(declaration)
    predicates: list[PredicateOutcome] = []

    def record(
        predicate: str,
        element: str | None,
        block: str | None,
        outcome: bool,
        index: int | None = None,
    ) -> None:
        """Record one of V3's decisions, per element and per block.

        ``index`` is what the row asks a FAILED predicate for -- "the block,
        outcome, signal or entry index at which it FIRST failed" -- in the
        convention :mod:`certiqs_key.protocol_compiler.transcript` states: an
        index this file computes is 1-based in the declared order, and one it
        carries through is the deciding record's own. It is dropped on a pass,
        where there is no first failure to index.
        """
        predicates.append(
            PredicateOutcome(
                source=PredicateSource.V3,
                predicate=predicate,
                element=element,
                block=block,
                outcome=outcome,
                first_failure_index=None if outcome else index,
                first_inexact_index=(
                    None
                    if outcome or predicate != SUMMATION_PREDICATE
                    else index
                ),
            )
        )

    # V3 evaluates matrix identities, so it guards its own table access rather
    # than relying on V1 having passed. Overlapping checks are not a defect --
    # what matters is that no datum is refused by NO check.
    for signal, label in enumerate(declaration.alice_alphabet, start=1):
        element = declaration.alice_povm.get(label)
        if element is None:
            return CheckOutcome.failing(
                "V3", f"no matrix M_{label!r} to test", tuple(predicates)
            )
        if dimension(element) != declaration.alice_dim:
            return CheckOutcome.failing(
                "V3", f"M_{label!r} is not an operator on A", tuple(predicates)
            )
        hermitian = is_hermitian(element)
        record("(H)", f"M_{label}", None, hermitian, signal)
        if not hermitian:
            return CheckOutcome.failing(
                "V3", f"M_{label!r} is not Hermitian", tuple(predicates)
            )
        positive = is_positive_semidefinite(element)
        record("(P)", f"M_{label}", None, positive, signal)
        if not positive:
            return CheckOutcome.failing(
                "V3",
                f"M_{label!r} is not positive semidefinite",
                tuple(predicates),
            )
    for outcome_index, label in enumerate(declaration.bob_alphabet, start=1):
        family_member = declaration.bob_povm.get(label)
        if family_member is None:
            return CheckOutcome.failing(
                "V3", f"no block list F_{label!r} to test", tuple(predicates)
            )
        blocks = family_member.sector_map.labels
        member_hermitian = True
        for position, block in enumerate(family_member.blocks):
            member_hermitian = is_hermitian(block)
            record(
                "(H)",
                f"F_{label}",
                blocks[position],
                member_hermitian,
                outcome_index,
            )
            if not member_hermitian:
                break
        if not member_hermitian:
            return CheckOutcome.failing(
                "V3", f"a block of F_{label!r} is not Hermitian", tuple(predicates)
            )
        member_positive = True
        for position, block in enumerate(family_member.blocks):
            member_positive = is_positive_semidefinite(block)
            record(
                "(P)",
                f"F_{label}",
                blocks[position],
                member_positive,
                outcome_index,
            )
            if not member_positive:
                break
        if not member_positive:
            return CheckOutcome.failing(
                "V3",
                f"a block of F_{label!r} is not positive semidefinite",
                tuple(predicates),
            )

    # (C) and (S) on {M_x}: A carries no sector decomposition, so this is the
    # ONE-BLOCK case of Definition def:exact and (T) is empty for it.
    alice_sum = sum_in_declared_order(
        [declaration.alice_povm[label] for label in declaration.alice_alphabet]
    )
    alice_complete = alice_sum.computed_total_equals(identity(declaration.alice_dim))
    # THE ELEMENT OF A COMPLETENESS SUM IS THE FAMILY, which is one of the
    # elements the row names ("the entry id, the link index, THE FAMILY NAME,
    # tau_A"): the sum is not per element of the family, and a key carrying
    # ``None`` there could not be told from another family's.
    record("(C)", "{M_x}", None, alice_complete)
    if not alice_complete:
        return CheckOutcome.failing(
            "V3",
            "the computed sum_x M_x is not 1_A -- condition (C) fails",
            tuple(predicates),
        )
    record(
        SUMMATION_PREDICATE,
        "{M_x}",
        None,
        alice_sum.rounds_nowhere,
        alice_sum.first_inexact_index,
    )
    if not alice_sum.rounds_nowhere:
        return CheckOutcome(
            check="V3",
            passed=False,
            predicates=tuple(predicates),
            refusal=Refusal(
                reason=RefusalReason.ALICE_POVM_SUMMATION_ROUNDS,
                detail=(
                    "the declared-order sum sum_x M_x rounds: the first inexact "
                    f"addition is at element {alice_sum.first_inexact_index} of "
                    f"the emitted index order, at {len(alice_sum.inexact_sites)} "
                    "entrywise site(s) in all. Condition (S) is on the "
                    "ADDITIONS, not on the operands, so a family every one of "
                    "whose entries is a binary64 number may still be refused -- "
                    "and the remedy is at the instance, this module never "
                    "repairing what it was handed"
                ),
            ),
        )

    # (C) and (S) on {F_v}, PER BLOCK, in Smap's declared order.
    sectors = declaration.sectors
    if declaration.bob_alphabet:
        per_sector = block_sum_in_declared_order(
            [declaration.bob_povm[label] for label in declaration.bob_alphabet]
        )
        for position, verdict in enumerate(per_sector):
            sector = sectors.labels[position]
            complete = verdict.computed_total_equals(identity(sectors.dims[position]))
            record("(C)", "{F_v}", sector, complete)
            if not complete:
                return CheckOutcome.failing(
                    "V3",
                    f"the computed sum_v F_v^({sector!r}) is not 1_{{Q_s}} -- "
                    "condition (C) fails on that block",
                    tuple(predicates),
                )
            record(
                SUMMATION_PREDICATE,
                "{F_v}",
                sector,
                verdict.rounds_nowhere,
                verdict.first_inexact_index,
            )
            if not verdict.rounds_nowhere:
                assert verdict.first_inexact_index is not None
                outcome_index = verdict.first_inexact_index
                return CheckOutcome(
                    check="V3",
                    passed=False,
                    predicates=tuple(predicates),
                    refusal=Refusal(
                        reason=RefusalReason.BOB_POVM_SUMMATION_ROUNDS,
                        detail=(
                            "the declared-order sum sum_v F_v^(s) rounds at "
                            f"sector {sector!r} (position {position}), at "
                            f"outcome index {outcome_index} of the emitted "
                            f"order -- {declaration.bob_alphabet[outcome_index - 1]!r}"
                        ),
                    ),
                )

    for index, entry in enumerate(declaration.constraint_list):
        operator_hermitian = True
        operator_blocks = entry.operator.sector_map.labels
        for position, block in enumerate(entry.operator.blocks):
            operator_hermitian = is_hermitian(block)
            record(
                "(H)",
                f"O^_{index + 1}",
                operator_blocks[position],
                operator_hermitian,
                index + 1,
            )
            if not operator_hermitian:
                break
        if not operator_hermitian:
            return CheckOutcome.failing(
                "V3",
                f"a block of the constraint operator O^_{index + 1} is not "
                "Hermitian; Eq. eq:feas-modes would lose its meaning, not "
                "merely its soundness (Remark rem:wellposed)",
                tuple(predicates),
            )
    return CheckOutcome.passing("V3", tuple(predicates))


def check_v4(declaration: CandidateDeclaration) -> CheckOutcome:
    """V4 -- every tabulated value of ``r`` lies in ``Z sqcup {perp}``."""
    admissible: set[KeyValue] = {*declaration.key_alphabet, PERP}
    for pair, value in declaration.key_map.items():
        if value not in admissible:
            return CheckOutcome.failing(
                "V4",
                f"r{pair} = {value!r} lies outside Z sqcup {{perp}} = "
                f"{tuple(declaration.raw_key_alphabet)}",
            )
    return CheckOutcome.passing("V4")


def check_v5(declaration: CandidateDeclaration) -> CheckOutcome:
    """V5 -- sifting consistency.

    "For all ``(x, v)`` and ``(x', v')`` with ``a(x, v) = a(x', v')``:
    ``r(x, v) = perp`` iff ``r(x', v') = perp``." Its failure is a GENUINE D(v)
    violation and not a limitation of the checker: within one announcement
    class the right-hand side of D(v)'s biconditional has one truth value while
    the left-hand side has two, so NO ``varsigma`` whatsoever witnesses D(v).
    """
    by_class: dict[AnnouncementClass, list[tuple[tuple[Label, Label], KeyValue]]] = {}
    for x, v in declaration.outcome_pairs():
        by_class.setdefault(declaration.announcement(x, v), []).append(
            ((x, v), declaration.key_map[(x, v)])
        )
    for kappa, members in by_class.items():
        sifted = {pair: value == PERP for pair, value in members}
        if len(set(sifted.values())) > 1:
            witnesses = sorted(str(pair) for pair in sifted)
            return CheckOutcome.failing(
                "V5",
                f"the announcement class {kappa} is realized by {witnesses} with "
                "r = perp at some and not at others, so sifting is not "
                "announcement-determined",
            )
    return CheckOutcome.passing("V5")


def _rows_are_one_by_one(
    declaration: CandidateDeclaration, entry: ConstraintEntry
) -> bool:
    """Whether every row of a ``party_local`` entry is a ``1 x 1`` comparison.

    ``def:homog``, the relation-symbol clause: the degenerate case is
    ``d_{A_t} prod_{f != f_k} d_{f,s_f} = 1`` FOR EVERY ROW -- "one measured factor
    and every Alice block of dimension one, ``d_A = 1`` included, and ``d_A > 1``
    with ``|T|`` Alice blocks of dimension one among them". The apposition is the
    gloss and the displayed condition is the normative one, so this decides the
    displayed condition: every Alice block of dimension one AND every other
    measured factor's every block of dimension one.

    ``d_A = 1`` IS NOT THE TEST: several Alice blocks of dimension one give
    ``1 x 1`` rows at ``d_A > 1``, and the narrower test would refuse a
    ``party_local`` entry declared at a scalar symbol there.
    """
    if any(dim != 1 for dim in declaration.alice_sectors.dims):
        return False
    scoped = declaration.measured_factor_position(entry.scope)
    return all(
        dim == 1
        for position, factor in enumerate(declaration.measured_factors)
        if position != scoped
        for dim in factor.sectors.dims
    )


def _check_v6_general(declaration: CandidateDeclaration) -> CheckOutcome:
    """V6's GENERAL-FORMAT reading (``def:validator``, V6 in the general format).

    THREE ADMITTED FORMS, "which with the arriving tag field is what fixes its
    tag": ``homogeneous`` with a real scalar, ``general`` with a block list
    ``(Theta_k^(t))_t`` along ``T`` decided Hermitian block by block, or
    ``party_local`` with a real scalar. "When the slot holds ``nomarg``: the
    right-hand side is of real scalar type, EITHER UNTAGGED OR TAGGED
    ``party_local``."

    THE RELATION SYMBOL IS DECIDED BY FORM AND NOT BY MODE ALONE: an UNTAGGED entry
    carries the symbols its mode admits, exactly as the accepted check has it, and an
    entry declared ``party_local`` carries the OPERATOR symbols IN EITHER MODE, "with
    the scalar symbols admitted as well where every row of that entry is ``1 x 1``".
    Without this ``ex:two-party-shape`` -- untrusted-source, with a ``party_local``
    entry declared at ``preceq`` -- would be refused here.

    THE THREE SYMBOLS ARE ONE ENUM IN THIS IMPLEMENTATION and the two readings
    are the two ORDERS they are read in, which is the modelling decision
    ``spec.py``'s docstring records. So "the relation symbol is admitted" is a
    decision about WHICH READING an entry's symbol carries, and the one thing it
    can refuse is a symbol outside the three -- which the type makes
    inexpressible. What this check therefore decides, and records, is the READING:
    the operator order for a tagged entry in either mode, the mode's order for an
    untagged one.

    AND EVERY ENTRY'S SCOPE NAMES A MEASURED FACTOR of the emitted sector map, "a
    comparison of a label against the factor list", refused with
    ``constraint_scope_not_a_factor`` naming the entry -- "which is the
    general-format half of D(vi) and is decided and never measured, as the relation
    symbol is".
    """
    trusted = declaration.is_trusted_mode
    predicates: list[PredicateOutcome] = []

    def record(
        predicate: str,
        entry_id: str,
        outcome: bool,
        index: int,
        *,
        block: Label | None = None,
    ) -> None:
        """Record one of V6's decisions on one entry, WITH ITS ENTRY INDEX."""
        predicates.append(
            PredicateOutcome(
                source=PredicateSource.V6,
                predicate=predicate,
                element=entry_id,
                block=block,
                outcome=outcome,
                first_failure_index=None if outcome else index,
            )
        )

    for index, entry in enumerate(declaration.constraint_list):
        entry_id = f"CList[{index + 1}]"
        tag = entry.tag
        record(
            "the right-hand side is of one of the three admitted forms, and its "
            "tag is that form",
            entry_id,
            tag is not None,
            index + 1,
        )
        if tag is None:
            return CheckOutcome.failing(
                "V6",
                f"the right-hand-side slot of entry {index + 1} holds NEITHER "
                "admitted object -- neither a real scalar nor a Hermitian "
                "right-hand side on A -- so it is REFUSED BY TYPE AND NOT MEASURED",
                tuple(predicates),
            )
        # THE SCOPE, decided before the numerical clauses: a scope naming no
        # measured factor leaves the entry's operator with no map to be a block
        # list against, and V1 deliberately compares nothing for it.
        scope = entry.scope
        if scope is not None:
            names_a_factor = declaration.measured_factor(scope) is not None
            record(
                "the scope names a measured factor of the emitted map",
                entry_id,
                names_a_factor,
                index + 1,
            )
            if not names_a_factor:
                return CheckOutcome(
                    check="V6",
                    passed=False,
                    predicates=tuple(predicates),
                    refusal=Refusal(
                        reason=RefusalReason.CONSTRAINT_SCOPE_NOT_A_FACTOR,
                        detail=(
                            f"entry {index + 1} is scoped to {scope!r}, which names "
                            "no measured factor of the emitted sector map "
                            f"{list(declaration.measured_factor_labels)}. "
                            "It is a comparison of a label against the factor list "
                            "and is decided, never measured (D(vi), the general "
                            "format)"
                        ),
                    ),
                )
        if tag is RhsTag.PARTY_LOCAL:
            # THE THIRD FORM'S TYPE CHECK: the datum that tag admits is a real
            # scalar, and the tag arrives rather than being read off it. A
            # party_local tag beside a matrix reads `general` off the datum, so the
            # disagreement below is what refuses it.
            scalar_rows = _rows_are_one_by_one(declaration, entry)
            record(
                "a party_local entry carries the OPERATOR relation symbols in "
                "either source mode; the reading here is "
                + ("the degenerate 1 x 1 one" if scalar_rows else "the operator one"),
                entry_id,
                True,
                index + 1,
            )
            continue
        if not trusted:
            scalar_only = tag is RhsTag.HOMOGENEOUS
            record(
                "the type the emitted mode admits (nomarg: scalar only, untagged)",
                entry_id,
                scalar_only,
                index + 1,
            )
            if not scalar_only:
                return CheckOutcome.failing(
                    "V6",
                    "the marginal slot holds nomarg, where ONLY THE SCALAR FORM "
                    f"EXISTS for an untagged entry (Definition def:homog); entry "
                    f"{index + 1} declares a matrix right-hand side",
                    tuple(predicates),
                )
        if tag is RhsTag.GENERAL:
            blocks = entry.rhs
            if not isinstance(blocks, BlockOperator):
                return CheckOutcome.failing(
                    "V6",
                    f"Theta_{index + 1} is declared `general` and is not a block "
                    "list along T; (DX2) types a general right-hand side as one",
                    tuple(predicates),
                )
            for alice_label, block in zip(
                blocks.sector_map.labels, blocks.blocks, strict=True
            ):
                hermitian = is_hermitian(block)
                record(
                    "(H)",
                    entry_id,
                    hermitian,
                    index + 1,
                    block=alice_label,
                )
                if not hermitian:
                    return CheckOutcome.failing(
                        "V6",
                        f"the {alice_label!r} block of Theta_{index + 1} is not "
                        "Hermitian on its Alice sector",
                        tuple(predicates),
                    )
        if entry.arriving_tag is not None:
            agrees = entry.arriving_tag is tag
            record(
                "the arriving tag agrees with the type of the datum",
                entry_id,
                agrees,
                index + 1,
            )
            if not agrees:
                return CheckOutcome.failing(
                    "V6",
                    f"entry {index + 1} arrived carrying the explicit tag "
                    f"{entry.arriving_tag.value!r} against a right-hand side of "
                    f"type {tag.value!r}; the tag is NEVER TAKEN ON A SUPPLIER'S "
                    "WORD AGAINST THE OBJECT THE ENTRY HOLDS",
                    tuple(predicates),
                )
    return CheckOutcome.passing("V6", tuple(predicates))


def check_v6(declaration: CandidateDeclaration) -> CheckOutcome:
    """V6 -- constraint typing against the marginal SLOT, INCLUDING THE TAG.

    "When the marginal slot is filled: ``bowtie_k`` in ``{<=, =, >=}``, and the
    entry's right-hand side is OF ONE OF THE TWO ADMITTED TYPES, WHICH IS WHAT
    FIXES ITS TAG (Definition def:homog) -- ``homogeneous``, whose datum is of
    REAL SCALAR type, or ``general``, whose datum is a matrix on ``A`` with
    ``Theta_k = Theta_k^dag`` DECIDED EXACTLY. When the slot holds ``nomarg``:
    ``bowtie_k`` in ``{<=, =, >=}`` and the right-hand side is of real scalar
    type."

    A REAL SCALAR IS ACCEPTED IN TRUSTED MODE AT EVERY ``d_A``, and is the
    LICENSED form there. "Through 0.2.0 this check REQUIRED A MATRIX WHENEVER
    THE MARGINAL SLOT WAS FILLED, WHICH REFUSED THE CONSUMING ENGINE'S OWN
    LICENSED FORM BY TYPE BEFORE ANY GATE RAN" -- that is the defect 0.3.0
    repairs, and it is why the trusted branch below admits both types.

    AN ENTRY CARRYING NO TAG FIELD IS NOT REFUSED: "the tag IS the type and is
    read off it, WHICH IS WHAT LETS AN ENTRY DECLARED AS A REAL CONSTANT AND
    CARRYING NO TAG FIELD DOCK HERE." Where an ARRIVING entry does carry one,
    "V6 compares that field with the type of the datum it names and A
    DISAGREEMENT IS A REFUSAL; the tag is NEVER TAKEN ON A SUPPLIER'S WORD
    AGAINST THE OBJECT THE ENTRY HOLDS."

    DECIDING HERMITICITY DOES NOT MAKE THE TAG A MEASURED PROPERTY. It is "the
    one decision of that check that is on DATA rather than on a type", required
    by D(vi) and counted in Eq. ``eq:predcount``; the tag is still the type.
    LICENSING IS DECIDED NOWHERE HERE -- it is gate (G3)(a)'s, and a ``general``
    entry passes V6 and is refused a key-length claim there.

    WHAT THE TRANSCRIPT CARRIES, in the ``gate_report`` row's words: "the type
    decisions of V6, including each entry's right-hand-side tag and the type it
    was read off, together with the one decision of that check that is on DATA
    rather than on a type -- the exact Hermiticity ``Theta_k =
    Theta_k^dagger`` of a ``general`` entry's matrix right-hand side". The
    decisions are recorded PER ENTRY, each under the name of the type question
    it answers, and the one on data under the same ``(H)`` this module spells
    everywhere else. A decision that a given entry does not reach -- the
    licensed-type question in trusted mode, the two ``general`` questions on a
    scalar right-hand side, the arriving-tag comparison where none arrived --
    is not recorded for it, because it was not taken.
    """
    if declaration.is_general_format:
        return _check_v6_general(declaration)
    trusted = declaration.is_trusted_mode
    predicates: list[PredicateOutcome] = []

    def record(predicate: str, entry_id: str, outcome: bool, index: int) -> None:
        """Record one of V6's decisions on one entry, WITH ITS ENTRY INDEX."""
        predicates.append(
            PredicateOutcome(
                source=PredicateSource.V6,
                predicate=predicate,
                element=entry_id,
                block=None,
                outcome=outcome,
                first_failure_index=None if outcome else index,
            )
        )

    for index, entry in enumerate(declaration.constraint_list):
        rhs = entry.rhs
        tag = entry.tag
        entry_id = f"CList[{index + 1}]"
        # THE TAG IS THE TYPE AND IS READ OFF IT, so ONE decision answers both
        # halves of the row's "each entry's right-hand-side tag and the type it
        # was read off": whether the slot holds one of the two admitted objects.
        # THE TAG'S VALUE IS NOT PUT IN THIS RECORD, and that is deliberate: a
        # transcript entry is an OUTCOME and not a datum ("THERE ARE NO
        # MEASURED DEFECTS TO REPORT AND NONE IS REPORTED: every entry of this
        # record is an OUTCOME"), and the value is already on the wire as the
        # emitted declaration's own ``constraint_rhs_tag`` key, per entry. A
        # second copy here would put one datum on the wire twice.
        record(
            "the right-hand side is of one of the two admitted types, and its "
            "tag is the type read off it",
            entry_id,
            tag is not None,
            index + 1,
        )
        if tag is None:
            return CheckOutcome.failing(
                "V6",
                f"the right-hand-side slot of entry {index + 1} holds NEITHER "
                "admitted object -- neither a real scalar nor a matrix on A -- "
                "so it is REFUSED BY TYPE AND NOT MEASURED",
                tuple(predicates),
            )
        if not trusted:
            scalar_only = tag is RhsTag.HOMOGENEOUS
            record(
                "the type the emitted mode admits (nomarg: scalar only)",
                entry_id,
                scalar_only,
                index + 1,
            )
            if not scalar_only:
                return CheckOutcome.failing(
                    "V6",
                    f"the marginal slot holds nomarg, where ONLY THE SCALAR FORM "
                    f"EXISTS (Definition def:homog); entry {index + 1} declares a "
                    "matrix right-hand side",
                    tuple(predicates),
                )
        if tag is RhsTag.GENERAL:
            assert not isinstance(rhs, Fraction)
            dense_rhs = rhs.dense() if isinstance(rhs, BlockOperator) else rhs
            on_alice = dimension(dense_rhs) == declaration.alice_dim
            record("Theta_k is an operator on A", entry_id, on_alice, index + 1)
            if not on_alice:
                return CheckOutcome.failing(
                    "V6",
                    f"Theta_{index + 1} is not an operator on A",
                    tuple(predicates),
                )
            hermitian = is_hermitian(dense_rhs)
            record("(H)", entry_id, hermitian, index + 1)
            if not hermitian:
                return CheckOutcome.failing(
                    "V6",
                    f"Theta_{index + 1} is not Hermitian on A",
                    tuple(predicates),
                )
        if entry.arriving_tag is not None:
            agrees = entry.arriving_tag is tag
            record(
                "the arriving tag agrees with the type of the datum",
                entry_id,
                agrees,
                index + 1,
            )
            if not agrees:
                return CheckOutcome.failing(
                    "V6",
                    f"entry {index + 1} arrived carrying the explicit tag "
                    f"{entry.arriving_tag.value!r} against a right-hand side of "
                    f"type {tag.value!r}; the tag is NEVER TAKEN ON A SUPPLIER'S "
                    "WORD AGAINST THE OBJECT THE ENTRY HOLDS",
                    tuple(predicates),
                )
    return CheckOutcome.passing("V6", tuple(predicates))


def _verified_candidate_predicates(
    outcome: FeasibilityCheck,
) -> tuple[PredicateOutcome, ...]:
    """Return V7's decisions on THE CANDIDATE ITS VERDICT RESTS ON.

    NOTHING IS DECIDED OR REBUILT HERE: the legs are recorded where they are
    decided, in
    :func:`~certiqs_key.protocol_compiler.feasibility.verify_witness`, and this
    function SELECTS which candidate's record the verdict rests on. Which one
    that is follows
    :func:`~certiqs_key.protocol_compiler.feasibility.check_feasibility`'s own
    attribution rather than a second rule: the passing candidate where one
    passed, and otherwise the SUPPLIED one where a witness was supplied --
    which is the candidate whose failing legs the refusal detail names -- and
    the default where none was.

    WHY ONE AND NOT BOTH. Where the default candidate fails and a supplied
    witness passes, both were verified; the row asks for the decisions on "the
    candidate it VERIFIED", singular, and the two records would share every
    key but the element. Recording both would put two answers to one question
    in the record and leave a consumer to work out which one the verdict came
    from. Where the check could not be read against the candidate at all --
    V6, V2 or V3 having failed first, so Eq. ``eq:feas-modes`` is not well
    posed (Remark ``rem:wellposed``) -- both verifications are absent and
    nothing is recorded.
    """
    if outcome.passes:
        verification = (
            outcome.default_verification
            if outcome.used_default
            else outcome.supplied_verification
        )
    elif outcome.supplied_verification is not None:
        verification = outcome.supplied_verification
    else:
        verification = outcome.default_verification
    return () if verification is None else verification.predicates


def check_v7(
    declaration: CandidateDeclaration, witness: JointBlockOperator | None = None
) -> tuple[CheckOutcome, FeasibilityCheck]:
    """V7 -- feasibility: ONE-SIDED, fail-closed, and THREE BRANCHES.

    "V7 passes in exactly three cases: (a) ``CList = empty``; or (b)
    ``CList != empty`` and THE DEFAULT CANDIDATE Eq. eq:witness-empty, WHICH
    THE COMPILER FORMS AND DOES NOT EMIT, passes the per-block verification of
    Theorem thm:feasibility (ii); or (c) ``CList != empty``, THE DEFAULT CANDIDATE
    FAILS, and a witness ``omega^*`` is supplied AS A BLOCK LIST AGAINST
    ``Smap`` -- the map it carries compared with ``Smap`` IN BLOCK KIND, IN
    IDENTIFIERS, IN THEIR ORDER AND IN THEIR DIMENSIONS, EXACTLY AS V1 COMPARES
    the map of a declared Q-operator family -- and passes that same
    verification."

    THE WITNESS'S MAP IS COMPARED HERE AND NOWHERE ELSE, and the refusal is
    V7's: "THIS IS THE ONE PLACE A WITNESS'S SECTOR MAP IS COMPARED, and it is
    HERE RATHER THAN AT V1 because ``omega^*`` is a block list on ``A Q``, IS
    NO SLOT of Eq. eq:declaration, and is QUANTIFIED OVER BY NO TARGET
    CONDITION." A permuted witness map therefore refuses with
    ``no_feasibility_witness`` and NOT with ``sector_map_mismatch`` -- same four
    components, different check, different reason -- and the reason "NAMES,
    WHERE A WITNESS WAS SUPPLIED AND REJECTED ON ITS MAP, THE FIRST POSITION AT
    WHICH THE TWO LISTS DIFFER", so the position travels with it.

    AND THE READING RULE SURVIVES (Remark ``rem:completeness``): the reason
    means "I WAS NOT SHOWN A FEASIBLE STATE", never "there is none". A witness
    rejected on its map is a fortiori not a demonstration that ``W`` is empty.

    "This is the one check of the list that is NOT equivalent to its target
    condition: it implies D(vii) and is implied by nothing weaker than a
    candidate that verifies." The verdict and the verification are returned
    together, so that a caller can report which leg decided a refusal without
    re-running it.

    WHAT THE TRANSCRIPT CARRIES OF V7, AND WHERE EACH PART IS FILLED
    ----------------------------------------------------------------
    Recorded HERE: condition (T) on a SUPPLIED witness's sector map, in the
    same four components V1 compares (the row: "the sector-map comparison check
    V7 makes where it passes on branch (c) ... recorded under V7 as its
    source"), which is decided in this function and nowhere else.

    Recorded in
    :func:`~certiqs_key.protocol_compiler.feasibility.verify_witness`, which is
    where they are DECIDED: Theorem ``thm:feasibility`` (ii)'s four legs -- (H) and (P)
    PER BLOCK, the trace, the marginal equality ``omega_A = tau_A`` where
    trusted mode takes it, and one Loewner-or-scalar leg PER CONSTRAINT ENTRY.
    :func:`_verified_candidate_predicates` selects the candidate whose record
    the verdict rests on and DECIDES NOTHING; the two conjunctions that would
    hide the per-block legs are unrolled there, not re-run here.
    """
    if witness is not None:
        # THE MAP COMPARED IS THE ONE THE WITNESS IS A BLOCK LIST AGAINST, and in
        # the general format that is the JOINT map: V7 "keeps its three branches
        # ... and a supplied omega^* is required to be A BLOCK LIST OVER THE JOINT
        # SECTORS, its map compared in the same four components at branch (c) and
        # there alone". At one Alice sector the joint map IS the Q map, identifier
        # for identifier, so the accepted comparison is this one at the degenerate
        # value and no candidate of today's format sees a different decision.
        if declaration.is_general_format:
            disagreement = declaration.joint_sectors.disagreement(
                witness.joint_sectors()
            )
        else:
            disagreement = declaration.sectors.disagreement(witness.sector_map)
        witness_map = sector_map_predicates(
            PredicateSource.V7, SUPPLIED_WITNESS, disagreement
        )
        if disagreement is not None:
            where = (
                "the block kind"
                if disagreement.position is None
                else f"position {disagreement.position}"
            )
            refusal = Refusal(
                reason=RefusalReason.NO_FEASIBILITY_WITNESS,
                detail=(
                    "the supplied feasibility witness carries a sector map "
                    f"disagreeing with Smap in {disagreement.component}, first "
                    f"at {where}: {disagreement.detail}. THE REASON IS V7's AND "
                    "NOT V1's -- omega^* is no slot of Eq. eq:declaration -- and "
                    "it means 'I WAS NOT SHOWN A FEASIBLE STATE', never 'THERE "
                    "IS NONE' (Remark rem:completeness)"
                ),
            )
            # THE SAME ONE PRINCIPLE AS EVERYWHERE ELSE IN THIS CHECK, and
            # not a second one: the record carries the legs of THE CANDIDATE
            # THE VERDICT RESTS ON, the row's "the candidate it verified",
            # singular. Here the supplied witness is rejected BY ITS MAP and
            # is never verified -- the call below passes `None` -- so the
            # candidate verified is the default one, and its legs are recorded
            # for that reason and not because the check did work that would
            # otherwise go unreported.
            rejected = check_feasibility(declaration, None)
            return (
                CheckOutcome(
                    check="V7",
                    passed=False,
                    refusal=refusal,
                    predicates=witness_map
                    + _verified_candidate_predicates(rejected),
                ),
                rejected,
            )
    else:
        witness_map = ()
    outcome = check_feasibility(declaration, witness)
    predicates = witness_map + _verified_candidate_predicates(outcome)
    if outcome.passes:
        return CheckOutcome.passing("V7", predicates), outcome
    assert outcome.refusal is not None
    return (
        CheckOutcome(
            check="V7", passed=False, refusal=outcome.refusal, predicates=predicates
        ),
        outcome,
    )


def check_v8(declaration: CandidateDeclaration) -> CheckOutcome:
    """V8 -- party computability, read against the READOUTS.

    "``a_A`` and ``a_B`` are tabulated on ``O_A``, ``O_B``; and for all
    ``(x, v)``, ``(x', v')`` with ``pi_h(x, v) = pi_h(x', v')`` and
    ``a(x, v) = a(x', v')``: ``r(x, v) = r(x', v')``."

    Remark ``rem:vacuous`` is why the second clause is read against
    ``pi_h`` and not against the joint pair: read against ``(x, v)``,
    Eq. ``eq:partycomp`` "would be satisfied by EVERY ``r`` whatsoever", and it
    would be vacuous exactly for the declaration shapes that need it most --
    those which place both parties' data in one outcome symbol, as the
    ``d_A = 1`` embedding does.
    """
    # THE TABULATION CLAUSE IS ON WHICHEVER TABLES THE FORMAT DECLARES, and
    # under a transcript the two maps are no slot at all: (DX5) replaces them,
    # "the two maps a_A, a_B above are the transcript with L = 2", and V1's
    # totality clause -- which is also its signature clause -- is what decides
    # every message's table there (def:validator, the general format).
    # def:validator's general paragraph says V5 and V8 "pair verbatim, their
    # proofs reading only that a is a total map into the derived announcement
    # alphabet"; so the clause below is the accepted spelling of exactly that,
    # and the transcript's spelling of it is V1's. The SECOND clause, which is
    # eq:partycomp itself, reads `declaration.announcement` and is therefore
    # unchanged in either format -- it is one function for both.
    if declaration.transcript is None:
        for readout in declaration.partition.alice_readout_alphabet:
            if readout not in declaration.announce_alice:
                return CheckOutcome.failing(
                    "V8", f"a_A is not tabulated at the readout {readout!r}"
                )
        for readout in declaration.partition.bob_readout_alphabet:
            if readout not in declaration.announce_bob:
                return CheckOutcome.failing(
                    "V8", f"a_B is not tabulated at the readout {readout!r}"
                )
    else:
        senders = {
            str(Party.ALICE): declaration.partition.alice_readout_alphabet,
            str(Party.BOB): declaration.partition.bob_readout_alphabet,
        }
        missing = declaration.transcript.missing_cell(senders)
        if missing is not None:
            position, readout, prefix = missing
            return CheckOutcome.failing(
                "V8",
                f"message {position + 1} of the declared transcript is not "
                f"tabulated at the readout {readout!r} after the earlier "
                f"messages {list(prefix)}, so the joint announcement function "
                "eq:transcript derives no value there",
            )
    seen: dict[tuple[Label, AnnouncementClass], KeyValue] = {}
    for x, v in declaration.outcome_pairs():
        key = (
            declaration.partition.readout(declaration.key_holder, x, v),
            declaration.announcement(x, v),
        )
        value = declaration.key_map[(x, v)]
        if key in seen and seen[key] != value:
            return CheckOutcome.failing(
                "V8",
                f"two pairs with holder readout {key[0]!r} and announcements "
                f"{key[1]} carry different key values, {seen[key]!r} and "
                f"{value!r}, so the holder cannot compute its own key",
            )
        seen[key] = value
    return CheckOutcome.passing("V8")


def reconstruct_sifting_predicate(
    declaration: CandidateDeclaration,
) -> dict[AnnouncementClass, Sifting]:
    """Rebuild ``varsigma`` from ``r`` and ``a`` -- the ``V5 => D(v)`` construction.

    ``varsigma(kappa) := fail`` if there EXISTS ``(x, v)`` in ``a^{-1}(kappa)``
    with ``r(x, v) = perp``, and ``pass`` otherwise -- "in particular on
    ``kappa not in ran a``, WHERE THE CHOICE IS IMMATERIAL because the
    condition of D(v) quantifies over pairs ``(x, v)``". So this table assigns
    ``pass`` on an unrealized class and may DIFFER from a declared
    ``varsigma`` there; both witness D(v) for the same ``r``, and an
    implementation that asserted agreement off ``ran a`` would assert something
    the contract calls immaterial.
    """
    rebuilt: dict[AnnouncementClass, Sifting] = dict.fromkeys(
        declaration.announcement_classes(), Sifting.PASS
    )
    for x, v in declaration.outcome_pairs():
        if declaration.key_map[(x, v)] == PERP:
            rebuilt[declaration.announcement(x, v)] = Sifting.FAIL
    return rebuilt


def reconstruct_holder_key_rule(
    declaration: CandidateDeclaration,
) -> dict[tuple[Label, AnnouncementClass], KeyValue]:
    """Rebuild ``r_h`` from ``r`` -- the ``V8 => D(viii)`` construction.

    ``r_h(o, kappa) := r(x, v)`` for any realizing pair -- well defined
    "precisely by V8's implication" -- and ``perp`` on pairs that are NOT
    REALIZED. Total on ``O_h x K``, and DIFFERENT from Eq. ``eq:rhold`` exactly
    on the unrealized pairs where the declared key rule returns a key value.
    """
    rebuilt: dict[tuple[Label, AnnouncementClass], KeyValue] = {
        (readout, kappa): PERP
        for readout in declaration.partition.readout_alphabet(declaration.key_holder)
        for kappa in declaration.announcement_classes()
    }
    for x, v in declaration.outcome_pairs():
        key = (
            declaration.partition.readout(declaration.key_holder, x, v),
            declaration.announcement(x, v),
        )
        rebuilt[key] = declaration.key_map[(x, v)]
    return rebuilt


@dataclass(frozen=True)
class DecidabilityCounts:
    """The current finite arithmetic inventories of Theorem ``thm:validator-soundness`` (iv).

    The last three fields retain the 0.1.4 query surface for old callers. They
    describe historical presentation loops and are not part of
    :attr:`exact_decisions`.
    """  # noqa: E501

    v2: int
    v3_alice: int
    v3_measured: int
    v3_constraints: int
    v6_general: int
    summations: int
    v7_state: int
    v7_marginal: int
    v7_constraints: int

    block_conditions: int
    v4_pairs: int
    ordered_pairs: int

    @property
    def v2_v3_v6(self) -> int:
        """Return the displayed V2/V3/V6 inventory."""
        return (
            self.v2
            + self.v3_alice
            + self.v3_measured
            + self.v3_constraints
            + self.v6_general
        )

    @property
    def v7(self) -> int:
        """Return all decisions made on the candidate checked by V7."""
        return self.v7_state + self.v7_marginal + self.v7_constraints

    @property
    def exact_decisions(self) -> int:
        """Return all arithmetic decisions enumerated by PC6(iv)."""
        return self.v2_v3_v6 + self.summations + self.v7


def decidability_counts(declaration: CandidateDeclaration) -> DecidabilityCounts:
    """Return the counts of Theorem ``thm:validator-soundness`` (iv) for one declaration."""  # noqa: E501
    x_size = len(declaration.alice_alphabet)
    v_size = len(declaration.bob_alphabet)
    sectors = declaration.sectors.count
    entries = len(declaration.constraint_list)
    trusted = declaration.is_trusted_mode
    general_entries = sum(
        entry.tag is RhsTag.GENERAL for entry in declaration.constraint_list
    )
    if declaration.is_general_format:
        alice_sectors = declaration.alice_sectors.count
        factor_sector_counts = tuple(
            factor.sectors.count for factor in declaration.measured_factors
        )
        factor_alphabet_counts = (
            tuple(
                len(family.alphabet) for family in declaration.bob_factors.factors
            )
            if declaration.bob_factors is not None
            else (v_size,)
        )
        v2 = (
            2 * alice_sectors
            + 1
            + alice_sectors * (declaration.alice_form is AliceForm.ENSEMBLE)
            if trusted
            else 0
        )
        v3_alice = alice_sectors * (2 * x_size + 1)
        v3_measured = sum(
            sector_count * (2 * alphabet_count + 1)
            for sector_count, alphabet_count in zip(
                factor_sector_counts, factor_alphabet_counts, strict=True
            )
        )
        def scoped_sector_count(entry: ConstraintEntry) -> int:
            """Return ``|S^{f_k}|``, or zero before V6 validates the scope."""
            factor = (
                declaration.measured_factors[0]
                if entry.scope is None
                else declaration.measured_factor(entry.scope)
            )
            return 0 if factor is None else factor.sectors.count

        v3_constraints = sum(
            scoped_sector_count(entry) for entry in declaration.constraint_list
        )
        v6_general = general_entries * alice_sectors
        summations = alice_sectors + sum(factor_sector_counts) + int(trusted)
        v7_state = 2 * alice_sectors * sectors + 1
        v7_marginal = alice_sectors if trusted else 0
        v7_constraints = 0
        for entry in declaration.constraint_list:
            if entry.is_party_local:
                scoped_sectors = scoped_sector_count(entry)
                if scoped_sectors:
                    v7_constraints += alice_sectors * sectors // scoped_sectors
            elif trusted:
                v7_constraints += alice_sectors
            else:
                v7_constraints += 1
    else:
        v2 = 3 if trusted else 0
        v3_alice = 2 * x_size + 1
        v3_measured = sectors * (2 * v_size + 1)
        v3_constraints = entries * sectors
        v6_general = general_entries
        summations = sectors + 1 + int(trusted)
        v7_state = 2 * sectors + 1
        v7_marginal = int(trusted)
        v7_constraints = entries
    ordered_sector_pairs = sectors * (sectors - 1)
    return DecidabilityCounts(
        v2=v2,
        v3_alice=v3_alice,
        v3_measured=v3_measured,
        v3_constraints=v3_constraints,
        v6_general=v6_general,
        summations=summations,
        v7_state=v7_state,
        v7_marginal=v7_marginal,
        v7_constraints=v7_constraints,
        block_conditions=v_size * ordered_sector_pairs + entries * ordered_sector_pairs,
        v4_pairs=x_size * v_size,
        ordered_pairs=(x_size * v_size) ** 2,
    )


@dataclass(frozen=True)
class ValidationResult:
    """The verdict of V1-V8 on one candidate declaration."""

    outcomes: tuple[CheckOutcome, ...]
    feasibility: FeasibilityCheck

    @property
    def passed(self) -> bool:
        """Whether every check passed, i.e. whether gate (G1) would pass."""
        return all(outcome.passed for outcome in self.outcomes)

    @property
    def failing_checks(self) -> tuple[str, ...]:
        """Return the identifiers of the failing checks, in the list's order."""
        return tuple(outcome.check for outcome in self.outcomes if not outcome.passed)

    @property
    def refusing_checks(self) -> tuple[str, ...]:
        """Return the checks that were EVALUATED and refused.

        Distinct from :attr:`failing_checks`, which also carries the checks
        that could not be read against the candidate at all.
        """
        return tuple(
            outcome.check
            for outcome in self.outcomes
            if not outcome.passed and outcome.evaluated
        )

    @property
    def unevaluated_checks(self) -> tuple[str, ...]:
        """Return the checks that were blocked by an earlier failure."""
        return tuple(
            outcome.check for outcome in self.outcomes if not outcome.evaluated
        )

    @property
    def predicates(self) -> tuple[PredicateOutcome, ...]:
        """Return every decision V1-V8 recorded, IN THE CHECKS' OWN ORDER.

        The concatenation of :attr:`CheckOutcome.predicates` over
        :attr:`outcomes`, which :func:`validate` builds in Definition
        ``def:validator``'s order -- so the transcript reads in the order the
        contract lists the checks and not in the order
        :func:`validate` happens to evaluate them (V6 before V5 and V8, V7
        last). What each check records and what it does not is that check's own
        docstring; the row's ``recorded_predicates`` scope note is why V4, V5
        and V8 record nothing.
        """
        return tuple(
            predicate
            for outcome in self.outcomes
            for predicate in outcome.predicates
        )

    @property
    def refusals(self) -> tuple[Refusal, ...]:
        """Return the refusals the failing checks produced, in order."""
        return tuple(
            outcome.refusal for outcome in self.outcomes if outcome.refusal is not None
        )

    def outcome_of(self, check: str) -> CheckOutcome:
        """Return the verdict of one named check."""
        for outcome in self.outcomes:
            if outcome.check == check:
                return outcome
        raise KeyError(f"no check {check!r} in Definition def:validator")

    @property
    def first_refusal(self) -> Refusal | None:
        """Return the refusal of the first failing check, or ``None``."""
        refusals = self.refusals
        return refusals[0] if refusals else None


def validate(
    declaration: CandidateDeclaration, witness: JointBlockOperator | None = None
) -> ValidationResult:
    """Run V1-V8 and return every verdict, in Definition ``def:validator``'s order.

    EVERY CHECK IS RUN, even after one has failed, so that the result names all
    the checks a candidate fails rather than the first. That is not a weakening
    of the fail-closed rule -- a candidate failing any check is refused and no
    declaration is emitted -- and it is what lets a supplier see the whole
    defect rather than one symptom at a time.

    TWO DEPENDENCIES ARE NOT OPTIMIZATIONS AND ARE REPORTED AS SUCH.

    V5 and V8 quantify over ``X x V`` through ``a`` and ``pi_h``; if V1 has
    found a readout or an announcement map untabulated, there is no ``a(x, v)``
    to compare and the clause cannot be READ against the candidate rather than
    being false of it. V7 needs Eq. ``eq:feas-modes`` to be well posed, which
    takes V2's marginal, V3's Hermiticity and V6's typing (Remark
    ``rem:wellposed``): evaluating it first would be a computation on an
    ill-formed input. In both cases the blocked check is reported FAILING with
    ``evaluated = False`` and the blocking check named -- never as passing.
    """
    v1 = check_v1(declaration)
    v2 = check_v2(declaration)
    v3 = check_v3(declaration)
    v4 = check_v4(declaration)
    v6 = check_v6(declaration)

    if v1.passed:
        v5 = check_v5(declaration)
        v8 = check_v8(declaration)
    else:
        tabulation = (
            "V5 and V8 quantify over X x V through a and pi_h, which V1 is what "
            "tabulates"
        )
        v5 = CheckOutcome.not_evaluated("V5", "V1", tabulation)
        v8 = CheckOutcome.not_evaluated("V8", "V1", tabulation)

    blocking = [outcome for outcome in (v1, v2, v3, v6) if not outcome.passed]
    if blocking:
        names = ", ".join(outcome.check for outcome in blocking)
        v7 = CheckOutcome.not_evaluated(
            "V7",
            names,
            "Eq. eq:feas-modes is then not well posed on this candidate "
            "(Remark rem:wellposed)",
        )
        feasibility = FeasibilityCheck(
            passes=False,
            witness=None,
            used_default=False,
            default_verification=None,
            supplied_verification=None,
            refusal=v7.refusal,
            first_branch=not declaration.constraint_list,
        )
    else:
        v7, feasibility = check_v7(declaration, witness)

    return ValidationResult(
        outcomes=(v1, v2, v3, v4, v5, v6, v7, v8), feasibility=feasibility
    )
