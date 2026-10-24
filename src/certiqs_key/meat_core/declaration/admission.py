"""The exact admission of declared operator data -- ``def:declaration``.

NO DECLARED-TOLERANCE APPARATUS. There is no DECLARED numerical tolerance
``tau_num``, no admission rule that measures three defects against it, no
admitted-with-defect branch and no key-length suppression that follows:

* there is no tolerance argument anywhere in this package, no
  ``tolerance_report``, no assumption for it and no threshold decided at a
  window on declared data;
* a declaration is EXACTLY ADMISSIBLE OR IT IS REFUSED -- the paragraph on
  exact admissibility inside ``def:declaration``, which is the decision the
  compiler has already taken on the numbers it emits
  (``protocol-compiler/def:exact``, mentioned and not used);
* the reason a tolerance could never have licensed a key-length claim is
  ``prop:optol-nobound``, with ``rem:optol-direction`` on how to read it.

WHAT THE ADMISSION DECIDES
==========================
THE DECLARED SUMMATION ORDER (``eq:declorder``). It is part of the
DECLARATION, because the datum it governs is declared, and it lives inside
``def:declaration``: the completeness sum of each sector is formed left to
right, entrywise, with no re-ordering and no re-association, and EVERY ONE OF
THOSE ADDITIONS MUST BE EXACT. Without that clause a vanishing completeness
defect says only that the COMPUTED sum is the identity; the witness is
``(1, 2^-60, 2^-60)`` on a one-dimensional sector, whose three defects all
vanish while the real sum is ``1 + 2^-59``.

THE SECTOR-MAP COMPARISON. A declared operator arrives as a list of sector
blocks plus the sector map, so an off-block entry is ABSENT FROM THE DATUM
rather than small in it (spec/architecture.md 2.9): sector-block diagonality
holds BY CONSTRUCTION, nothing verifies that off-sector entries vanish because
nothing can write them, and the whole structural check is the comparison of
this module's sector map -- the block kind, the block identifiers and their
ordering -- with the producer's. Its failure is ``sector_map_disagreement``.

HOW THE EXACT DECISIONS ARE MADE
================================
Through :mod:`certiqs_key.foundations.exact_admission`: Hermiticity by an exact
entrywise comparison, positivity by a rational ``LDL^*`` with the zero-pivot
rule (no eigenvalue, no threshold), completeness by the exact rational sum, and
the round-nowhere condition by carrying the partial sums as Gaussian rationals
and testing each against the binary64 lattice. NONE OF THOSE DECISIONS IS A
FLOATING-POINT PROXY for the question it answers, which is what the interface's
``fail_closed.how_a_rule_is_decided`` requires: "positivity by an exact
decision and not by a floating-point eigenvalue".

That distinction is not academic. ``numpy.linalg.eigvalsh`` returns a NEGATIVE
smallest eigenvalue on a block that is exactly positive semidefinite and
exactly SINGULAR -- measured at ``-8.53e-18`` on the optical instance's two 4x4
``nb_3`` blocks at photon cutoff 3, and at ``1e-17`` scale on every
rank-deficient block -- so an eigensolver floor compared against zero would
refuse declared families this contract admits, and a window around the
comparison would be the undeclared default the exact rule exists to forbid.

NOTHING IS REPAIRED
===================
No projection, clamp, symmetrization or renormalization of a DECLARED operator
is performed, licensed or recommended anywhere below (the interface's
``no_row_repairs_declared_data``; ``conventions.no_snapping``). The matrices
the predicates are applied to are the matrices the objective is evaluated on.
The two positivity repairs this contract licenses are of objects the module
COMPUTED and live in the solver submodule.

OPEN IMPLEMENTATION CHOICE SETTLED HERE
=======================================
The order in which the ``{M_x}`` completeness sum and the ``tau_A`` trace are
formed -- :data:`ALICE_SUMMATION_ORDER`. The declared order of the receiver
family is read off the declaration and is not this module's to choose.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

import numpy as np

from certiqs_key.foundations.exact_admission import (
    RoundsNowhereResult,
    admit_family_exact,
    is_hermitian_exact,
    is_psd_exact,
    sum_rounds_nowhere,
    trace_residue_exact,
)
from certiqs_key.meat_core.declaration.declaration import ProtocolDeclaration
from certiqs_key.meat_core.errors import DeclarationError
from certiqs_key.meat_core.objective.linalg import Matrix, as_matrix
from certiqs_key.meat_core.reasons import GroupAPredicate
from certiqs_key.meat_core.reasons import RefusalReason as AdmissionRefusal

#: THE ORDER IN WHICH ALICE'S TWO SUMS ARE FORMED, fixed here and recorded,
#: because the interface's ``alice_povm_exact`` and ``alice_marginal_exact``
#: rows each ask their defining sum to round nowhere and NO CLAIM FIXES AN
#: ORDER for them -- while THE VERDICT CAN DEPEND ON IT. The frozen
#: ``O-ALICE-EXACT-ORDER`` exhibits a declared Alice POVM (BB84 at
#: ``p_Z = 0.9``) whose sum rounds in twenty of the twenty-four orders and
#: rounds nowhere in the other four.
#:
#: THE ORDER FIXED: for ``{M_x}``, the DECLARED ORDER OF ALICE'S OUTCOME
#: ALPHABET, left to right, entrywise, with no re-ordering and no
#: re-association; for ``tr tau_A``, INCREASING DIAGONAL INDEX, ``0`` to
#: ``d_A - 1``, left to right.
#:
#: WHY THAT ONE. It is the LEAST-COMMITTAL rule available: it introduces no
#: re-ordering of the datum, so the module adds nothing to what the declaration
#: presents, and it is a RULE rather than an accident -- the alphabet's order is
#: read from :attr:`ProtocolDeclaration.alice_outcomes` and never from the
#: iteration order of an intermediate container, so it is reproducible from the
#: artefact rather than from this process. It is deliberately NOT a
#: magnitude-sorted order: sorting smallest-first would admit
#: ``O-ALICE-EXACT-ORDER``'s ``p_Z = 0.9`` family, which is a genuine POVM, but
#: it would also make the verdict depend on a comparison of declared numbers,
#: turning a decided predicate into a measured one.
ALICE_SUMMATION_ORDER: str = (
    "{M_x}: the declared order of Alice's outcome alphabet, left to right, "
    "entrywise, with no re-ordering and no re-association. tr tau_A: "
    "increasing diagonal index, 0 to d_A - 1, left to right"
)


class AdmissionError(DeclarationError):
    """A declaration refused at the exact admission of ``def:declaration``.

    A subclass of :class:`~certiqs_key.meat_core.errors.DeclarationError`
    because it IS one: the declaration is refused and NO RESULT OF ANY KIND is
    produced. What it adds is the MACHINE-READABLE reason the interface spells
    and the Group A row that failed, so that a caller does not have to read
    prose to learn which predicate was decided against it.

    IT CARRIES NO MEASURED DEFECT: no defect is measured on declared data, so
    what a refusal carries is the PREDICATE and the
    INDEX -- the block, outcome, sector or entry at which the predicate first
    failed.
    """

    def __init__(
        self,
        message: str,
        *,
        reason: AdmissionRefusal,
        predicate: GroupAPredicate | None = None,
    ) -> None:
        """Store the machine-readable reason and the Group A row beside the prose."""
        super().__init__(message)
        self.reason = reason
        self.predicate = predicate


# ---------------------------------------------------------------------------
#  The declared summation order of eq:declorder
# ---------------------------------------------------------------------------


def declared_order_sum(blocks: Sequence[Matrix]) -> Matrix:
    """Return ``Sigma^{(s)}`` of ``eq:declorder``, formed left to right.

    ``S_0 = 0``, ``S_i = S_{i-1} + F_{v_i}``, entrywise, in binary64, WITH NO
    RE-ORDERING AND NO RE-ASSOCIATION -- the order is part of the declared
    outcome alphabet, and re-associating asks a different question because
    binary64 addition is not associative. Whether every one of those additions
    was exact is decided by
    :func:`certiqs_key.foundations.exact_admission.sum_rounds_nowhere` on the same
    sequence.
    """
    elements = [as_matrix(block) for block in blocks]
    total = np.zeros_like(elements[0], dtype=np.complex128)
    for element in elements:
        total = total + element
    return total


# ---------------------------------------------------------------------------
#  The sector-map comparison
# ---------------------------------------------------------------------------


def check_sector_map(
    declared_blocks: Sequence[str],
    sector_index_set: Sequence[str],
    where: str,
    *,
    declared_kind: str | None = None,
    consumer_kind: str | None = None,
) -> None:
    """Compare the producer's sector map with this module's, in three components.

    A declared operator arrives as a list of sector blocks plus the sector map,
    so an off-block entry is ABSENT FROM THE DATUM rather than small in it:
    "nothing can write one, NOTHING VERIFIES THAT NONE WAS WRITTEN, and no
    ``d_Q x d_Q`` matrix is assembled in order to be checked"
    (spec/architecture.md 2.9). Sector-block diagonality HOLDS BY CONSTRUCTION.

    WHAT IS LEFT TO COMPARE is the sector map, and a sector map is THE BLOCK
    KIND, THE BLOCK IDENTIFIERS AND THEIR ORDERING. All three are compared here
    against this module's own, and a disagreement is a refusal with a
    machine-readable reason, WHICH IS THE ONLY FAILURE MODE THE REPRESENTATION
    ADMITS.

    THE KIND IS COMPARED AND NOT CONSTRAINED. The contract names the kind as a
    component of the map and does not say which value its own map carries, so
    what is decided here is AGREEMENT and nothing else; which kinds exist and
    which an operator payload may declare belongs to the shared format
    (:class:`certiqs_key.domain.arrays.BlockKind`), one tier down. An ABSENT
    kind on either side is a disagreement: a map without a kind is not a map
    this module can compare its own against, and supplying one would decide a
    structural predicate on nobody's authority.

    DECIDED BEFORE THE NUMERICAL PREDICATES. The comparison is the platform's
    structural check, which every consumer performs; a disagreement refuses the
    run outright.

    THE ORDERING IS PART OF THE MAP AND NOT A PRESENTATION DETAIL:
    ``eq:declorder`` sums each sector's family in the declared order.

    Raises:
        AdmissionError: with reason ``sector_map_disagreement``.
    """
    producer = tuple(declared_blocks)
    consumer = tuple(sector_index_set)
    if declared_kind != consumer_kind or declared_kind is None:
        raise AdmissionError(
            f"{where}: the sector-map comparison of def:declaration -- the "
            f"producer's sector map declares block kind {declared_kind!r} and "
            f"this module's declares {consumer_kind!r}. The BLOCK KIND is a "
            "component of the sector map, beside the block identifiers and "
            "their ordering, and the structural check a consumer performs is "
            "the comparison of its own map with the producer's "
            "(spec/architecture.md 2.9). An ABSENT kind is a disagreement and "
            "not a default: a map without one is not a map this module can "
            "compare its own against, and supplying one would decide a "
            "structural predicate on nobody's authority. DECIDED EXACTLY, AT "
            "NO WINDOW",
            reason=AdmissionRefusal.SECTOR_MAP_DISAGREEMENT,
            predicate=GroupAPredicate.BOB_POVM_ADMISSION,
        )
    if producer == consumer:
        return
    missing = sorted(set(consumer) - set(producer))
    extra = sorted(set(producer) - set(consumer))
    if missing or extra:
        detail = (
            f"the producer declares blocks {list(producer)} and this module "
            f"holds sectors {list(consumer)}"
            + (f"; missing here: {missing}" if missing else "")
            + (f"; not in the declared sector index set: {extra}" if extra else "")
        )
    else:
        detail = (
            f"the identifiers agree and THE ORDERING DOES NOT: the producer "
            f"declares {list(producer)} and this module holds {list(consumer)}. "
            "The ordering is part of the sector map, because eq:declorder "
            "sums each sector's family in the declared order and binary64 "
            "addition is not associative"
        )
    raise AdmissionError(
        f"{where}: the sector-map comparison of def:declaration -- "
        f"{detail}. A declared operator arrives as a list of sector blocks "
        "plus the sector map, so sector-block diagonality holds BY "
        "CONSTRUCTION and the only structural failure the representation "
        "admits is this disagreement (spec/architecture.md 2.9). It is decided "
        "EXACTLY, at no window and before any numerical predicate, and nothing "
        "is projected, re-ordered or renamed to make the two maps agree",
        reason=AdmissionRefusal.SECTOR_MAP_DISAGREEMENT,
        predicate=GroupAPredicate.BOB_POVM_ADMISSION,
    )


# ---------------------------------------------------------------------------
#  The receiver family: bob_povm_admission and bob_povm_summation_exact
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class BobPovmAdmission:
    """What the exact admission decided about the declared receiver family.

    THE RECORD OF A DECISION AND NOT OF A MEASUREMENT. Every field is a verdict
    -- a boolean per block, a round-nowhere verdict per sector -- because no
    defect is measured on declared data (the interface's ``not_outputs``,
    ``tolerance_report``). It travels into ``map_validation_report`` as the
    admission outcome of the declared family.

    An instance of this class EXISTS ONLY FOR AN ADMITTED FAMILY: the admission
    raises on the first failure, so :attr:`exactly_admissible` is ``True`` on
    every value a caller ever holds. It is a field rather than a constant so
    that the record says what it decided rather than what its existence
    implies.
    """

    #: Bob's joint outcome alphabet in its DECLARED order -- the order
    #: ``eq:declorder`` forms the sum in.
    outcomes: tuple[str, ...]
    #: The declared sector index set, in its declared order.
    sectors: tuple[str, ...]
    #: Whether each declared block is EXACTLY Hermitian, keyed by outcome then
    #: sector.
    per_block_hermitian: Mapping[str, Mapping[str, bool]]
    #: Whether each declared block is EXACTLY positive semidefinite, keyed the
    #: same way. ``False`` on a block whose exact Hermiticity failed, because
    #: :func:`~certiqs_key.foundations.exact_admission.is_psd_exact` is not run
    #: there -- positive semidefiniteness is a property of a Hermitian operator.
    per_block_positive: Mapping[str, Mapping[str, bool]]
    #: Whether each sector's family sums EXACTLY to the identity of that block.
    per_sector_complete: Mapping[str, bool]
    #: The round-nowhere verdict per sector, with the first inexact addition
    #: named.
    per_sector_summation: Mapping[str, RoundsNowhereResult]
    #: Whether every one of the above holds.
    exactly_admissible: bool


def admit_bob_povm_exact(
    family: Mapping[str, Mapping[str, Matrix]],
    sectors: Sequence[str],
) -> BobPovmAdmission:
    """Decide the ``bob_povm_admission`` and ``bob_povm_summation_exact`` rows.

    ``family`` maps the joint outcome ``v`` to the sector blocks
    ``F_v^{(s)}``; ``sectors`` is the declared sector index set in its declared
    order.

    THE FAMILY IS EXACTLY ADMISSIBLE OR THE RUN IS REFUSED. Per sector block:
    ``F_v`` exactly Hermitian, ``F_v >= 0`` exactly, and the sector sum
    ``sum_v F_v^{(s)} = 1_{Q_s}`` exactly, ACCUMULATED IN THE DECLARED ORDER OF
    ``V`` and verified to round nowhere. A family failing any of these is
    refused, naming the predicate, and NOTHING IS REPAIRED.

    THIS IS THE ROW A TOLERANCE WOULD HAVE LIVED ON. Admission decided against
    a declared ``tau_num`` would take the Hermiticity defect, the negative part
    and the completeness defect each at most ``tau_num``, with a nonzero defect
    admitted for exploration and carrying no key-length claim. The exact
    reading is the STRICTER of the two spec/architecture.md 2.8 licenses, so
    nothing that passes here could fail the tolerance policy.

    THE SECTOR MAP IS NOT DECIDED HERE: it is a comparison of sector maps
    (:func:`check_sector_map`) made where the two maps meet, which is before a
    :class:`~certiqs_key.meat_core.declaration.declaration.ProtocolDeclaration`
    exists at all.

    Raises:
        DeclarationError: if the family or the sector index set is empty, or a
            declared element carries no block on a declared sector.
        AdmissionError: naming the predicate that failed and the index.
    """
    outcomes = tuple(family)
    if not outcomes:
        raise DeclarationError(
            "def:admissible-declaration (iii): Bob's POVM is empty, so the admission "
            "rule has no "
            "family to decide"
        )
    sector_order = tuple(sectors)
    if not sector_order:
        raise DeclarationError(
            "def:declaration: the declared sector index set is empty, so "
            "eq:declorder has no block to sum on"
        )

    per_block_herm: dict[str, dict[str, bool]] = {}
    per_block_pos: dict[str, dict[str, bool]] = {}
    for outcome in outcomes:
        per_block_herm[outcome] = {}
        per_block_pos[outcome] = {}
        for sector in sector_order:
            if sector not in family[outcome]:
                raise DeclarationError(
                    f"def:admissible-declaration (iii): bob_povm[{outcome!r}] declares "
                    "no block "
                    f"on sector {sector!r}"
                )
            block = as_matrix(family[outcome][sector])
            hermitian_ok = is_hermitian_exact(block)
            # NOT RUN ON A BLOCK THAT FAILS EXACT HERMITICITY:
            # :func:`~certiqs_key.foundations.exact_admission.is_psd_exact`
            # raises there rather than report a failed test where none was run,
            # and positive semidefiniteness is a property of a Hermitian
            # operator. `False` here means "not decided positive".
            positive_ok = is_psd_exact(block) if hermitian_ok else False
            per_block_herm[outcome][sector] = hermitian_ok
            per_block_pos[outcome][sector] = positive_ok
            if not hermitian_ok:
                raise AdmissionError(
                    f"def:declaration, the exact-admissibility paragraph: the "
                    f"declared bob_povm block at outcome {outcome!r}, sector "
                    f"{sector!r} is NOT EXACTLY HERMITIAN. def:admissible-declaration "
                    "(iii) asks "
                    "Hermiticity of every declared receiver element per sector "
                    "block, and it is decided entry by entry on the declared "
                    "binary64 numbers read as the dyadic rationals they are -- "
                    "at no window, because there is no tolerance in this "
                    "module to be decided at. The objects the objective is "
                    "built from are not defined on these numbers: the positive "
                    "semidefinite square root of eq:Vmsm exists exactly when "
                    "the block is Hermitian and positive semidefinite, and "
                    "Hermitizing, flooring the negative part or substituting a "
                    "nearby exact family would each be a repair of declared "
                    "data. An implementation that wants such a run to proceed "
                    "must obtain exactly admissible numbers from the supplier "
                    "that constructed them",
                    reason=AdmissionRefusal.DECLARATION_NOT_EXACTLY_ADMISSIBLE,
                    predicate=GroupAPredicate.BOB_POVM_ADMISSION,
                )
            if not positive_ok:
                raise AdmissionError(
                    f"def:declaration, the exact-admissibility paragraph: the "
                    f"declared bob_povm block at outcome {outcome!r}, sector "
                    f"{sector!r} is NOT EXACTLY POSITIVE SEMIDEFINITE. Decided "
                    "by a rational LDL^* with the zero-pivot rule -- no "
                    "eigenvalue is computed and no threshold appears -- "
                    "because numpy.linalg.eigvalsh returns a slightly negative "
                    "smallest eigenvalue on a block that is exactly positive "
                    "semidefinite and exactly singular, and comparing that "
                    "floor against zero would refuse declared families this "
                    "contract admits. Nothing is projected or clamped here",
                    reason=AdmissionRefusal.DECLARATION_NOT_EXACTLY_ADMISSIBLE,
                    predicate=GroupAPredicate.BOB_POVM_ADMISSION,
                )

    per_sector_complete: dict[str, bool] = {}
    per_sector_sum: dict[str, RoundsNowhereResult] = {}
    for sector in sector_order:
        blocks = [as_matrix(family[outcome][sector]) for outcome in outcomes]
        admission = admit_family_exact(blocks)
        per_sector_complete[sector] = admission.complete
        per_sector_sum[sector] = admission.rounds_nowhere
        # THE SUMMATION ROW IS DECIDED FIRST, BEFORE EXACT COMPLETENESS, and
        # the order is the interface's. The reason is
        # that a family whose declared-order sum ROUNDS is refused for THAT
        # rather than for the exact completeness failure the rounding produces:
        # the informative refusal names the additions, because the remedy is
        # the producer's and is to emit numbers whose defining sums close
        # exactly in binary64. The frozen family of three entries fl(1/3) is
        # exactly that case -- its COMPUTED sum is 1.0, its real sum is
        # 1 - 2^-54 -- and the registry pins `bob_povm_summation_rounds` for it.
        rounds = admission.rounds_nowhere
        if not rounds.ok:
            index = rounds.first_inexact_index
            raise AdmissionError(
                f"def:declaration, eq:declorder: on sector {sector!r} the "
                "declared-order completeness sum of the receiver family "
                f"ROUNDS. The first inexact addition is at outcome index "
                f"{index!r} of the declared order {list(outcomes)}"
                + (
                    f", at entry {list(rounds.first_inexact_entry)} "
                    f"({rounds.first_inexact_part})"
                    if rounds.first_inexact_entry is not None
                    else ""
                )
                + ". THE ROW IS SEPARATE FROM THE COMPLETENESS ROW FOR A "
                "REASON: a completeness defect of zero on a sum THAT ROUNDED "
                "says only that the COMPUTED sum is the identity. The witness "
                "is (1, 2^-60, 2^-60) on a one-dimensional sector, whose three "
                "defects all vanish while the real sum is 1 + 2^-59, so the "
                "generated measurement is not an isometry and the key length "
                "is not defined for the declared numbers. The supplier's "
                "remedy is to emit numbers whose defining sums close exactly "
                "in binary64, dyadic entries sufficing; this module never "
                "repairs them",
                reason=AdmissionRefusal.BOB_POVM_SUMMATION_ROUNDS,
                predicate=GroupAPredicate.BOB_POVM_SUMMATION_EXACT,
            )
        if not admission.complete:
            raise AdmissionError(
                f"def:declaration, the exact-admissibility paragraph: on "
                f"sector {sector!r} the declared bob_povm family does not sum "
                "EXACTLY to the identity of that block; the squared entrywise "
                f"residue of the exact sum is "
                f"{admission.completeness_residue_squared}. def:admissible-declaration "
                "(iii) "
                "asks completeness per sector and the proofs of "
                "thm:protocol-channel (i) "
                "and (iii) read that relation as an identity of REAL "
                "operators -- it is what makes the generated measurement "
                "isometry an isometry. Decided exactly, at no window, and "
                "nothing is renormalized",
                reason=AdmissionRefusal.DECLARATION_NOT_EXACTLY_ADMISSIBLE,
                predicate=GroupAPredicate.BOB_POVM_ADMISSION,
            )

    return BobPovmAdmission(
        outcomes=outcomes,
        sectors=sector_order,
        per_block_hermitian={k: dict(v) for k, v in per_block_herm.items()},
        per_block_positive={k: dict(v) for k, v in per_block_pos.items()},
        per_sector_complete=per_sector_complete,
        per_sector_summation=per_sector_sum,
        exactly_admissible=True,
    )


def admit_declaration(declaration: ProtocolDeclaration) -> BobPovmAdmission:
    """Decide the exact admission of a declaration's ``bob_povm``.

    THE ONE DECISION SITE. Both entry points reach the admission rule through
    this function -- ``validate_declaration`` on the bundle path and ``solve``
    on the in-memory path -- so the rule is applied once and cannot drift
    between them.

    IT TAKES NO TOLERANCE, and there is no signature it could take one in: this
    module declares no numerical tolerance, reads none and emits none
    (spec/architecture.md 2.8, "Modules receive no tolerance to reason with").
    """
    return admit_bob_povm_exact(declaration.bob_povm, declaration.sector_index_set)


# ---------------------------------------------------------------------------
#  Alice's declared data: alice_povm_exact and alice_marginal_exact
# ---------------------------------------------------------------------------


def admit_alice_povm_exact(declaration: ProtocolDeclaration) -> RoundsNowhereResult:
    """Decide the interface's ``alice_povm_exact`` row.

    ``M_x = M_x^dagger`` and ``sum_x M_x = 1_A`` entrywise, ``M_x >= 0`` by the
    exact decision, ALL AT EXACTLY 0, AND THE COMPLETENESS SUM VERIFIED TO
    ROUND NOWHERE -- every one of its ``|X| - 1`` entrywise additions exact in
    binary64, in the order :data:`ALICE_SUMMATION_ORDER` fixes and this
    function records.

    WHY THE ROUNDING CLAUSE IS THERE. A defect of 0 on the COMPUTED sum does
    not say ``sum_x M_x = 1_A`` holds of the declared numbers, while the sites
    that consume that relation -- the proofs of ``thm:protocol-channel`` (i),
    (iii) and the mass identity -- read it as an identity of REAL operators.
    The witness is
    ``(1, 2^-60, 2^-60)`` on a one-dimensional ``A``: it passes with all
    defects 0 while ``sum_x M_x = 1 + 2^-59``, and the generated measurement
    isometry is then not an isometry.

    WHAT IT COSTS, disclosed rather than discovered: the clause can refuse a
    GENUINE POVM whose declared-order sum happens to round -- FAIL-CLOSED, and
    avoidable by the producer. This module never repairs the numbers.

    Returns:
        The round-nowhere verdict on ``{M_x}``, for the record.

    Raises:
        AdmissionError: naming ``alice_povm_exact``.
    """
    outcomes = declaration.alice_outcomes
    if not outcomes:
        raise AdmissionError(
            "def:admissible-declaration (iii): alice_povm is empty, so sum_x M_x is "
            "not defined",
            reason=AdmissionRefusal.DECLARATION_NOT_EXACTLY_ADMISSIBLE,
            predicate=GroupAPredicate.ALICE_POVM_EXACT,
        )
    elements = [as_matrix(declaration.alice_povm[x]) for x in outcomes]
    admission = admit_family_exact(elements)
    if admission.admissible:
        return admission.rounds_nowhere
    detail = {
        "hermiticity": (
            "elements "
            f"{[outcomes[i] for i in admission.non_hermitian]} are not EXACTLY "
            "Hermitian"
        ),
        "positivity": (
            "elements "
            f"{[outcomes[i] for i in admission.indefinite]} are not EXACTLY "
            "positive semidefinite (decided by a rational LDL^* and not by an "
            "eigenvalue)"
        ),
        "completeness": (
            "the exact sum sum_x M_x is not 1_A; squared entrywise residue "
            f"{admission.completeness_residue_squared}"
        ),
        "declared_order_sum": (
            "the completeness sum ROUNDS: the first inexact addition is at "
            f"outcome index {admission.rounds_nowhere.first_inexact_index!r} "
            f"of {list(outcomes)}"
        ),
    }
    raise AdmissionError(
        "def:declaration, the exact-admissibility paragraph (the "
        "alice_povm_exact row): the declared alice_povm is refused at EXACTLY "
        "0, there being no window in this module to decide it at. Failing: "
        + "; ".join(detail[name] for name in admission.failures)
        + f". The summation order is the module's and is recorded: "
        f"{ALICE_SUMMATION_ORDER}. Nothing is repaired here -- an instance "
        "meets this by declaring numbers that are exactly representable and "
        "whose defining sums close exactly in binary64, dyadic entries "
        "sufficing, and by snapping anything that does not BEFORE this module "
        "sees the data",
        reason=AdmissionRefusal.DECLARATION_NOT_EXACTLY_ADMISSIBLE,
        predicate=GroupAPredicate.ALICE_POVM_EXACT,
    )


def admit_alice_marginal_exact(declaration: ProtocolDeclaration) -> None:
    """Decide the interface's ``alice_marginal_exact`` row.

    ``tau_A = tau_A^dagger`` and ``tr tau_A = 1``, ``tau_A >= 0`` by the exact
    decision, on the declared ``tau_A``, WITH THE TRACE FORMED BY ADDITIONS
    VERIFIED TO ROUND NOWHERE, in the order :data:`ALICE_SUMMATION_ORDER` fixes
    and this function records.

    ``tr tau_A = 1`` is read as an identity of REAL numbers in the proof of
    ``thm:choi`` and in ``rem:modes-da1``, and ``tau_A = diag(1, 2^-60, 2^-60)``
    would otherwise pass with a computed trace of 1.

    A SINGULAR ``tau_A`` IS ADMISSIBLE -- the support frame of
    ``lem:choi-marginal`` carries it -- which is exactly the case the exact
    positivity decision must get right and an eigensolver floor gets wrong.

    A NO-OP IN UNTRUSTED-SOURCE MODE, where the marginal slot holds ``none`` and
    there is no ``tau_A`` to decide anything about.

    Raises:
        AdmissionError: naming ``alice_marginal_exact``.
    """
    if not declaration.is_trusted_source:
        return
    tau = declaration.trusted_marginal
    failures: list[str] = []
    if not is_hermitian_exact(tau):
        failures.append("tau_A is not EXACTLY Hermitian")
    elif not is_psd_exact(tau):
        failures.append(
            "tau_A is not EXACTLY positive semidefinite (decided by a rational "
            "LDL^* and not by an eigenvalue)"
        )
    if trace_residue_exact(tau) != 0:
        failures.append(
            f"the exact trace of tau_A is not 1 (|tr tau_A - 1| = "
            f"{trace_residue_exact(tau)})"
        )
    # The round-nowhere clause on the trace, in the module's fixed order:
    # increasing diagonal index, left to right. The diagonal entries are laid
    # out as 1x1 blocks so that the shared kernel decides the same question it
    # decides for a family.
    diagonal = [
        np.asarray([[tau[i, i]]], dtype=np.complex128) for i in range(tau.shape[0])
    ]
    rounds = sum_rounds_nowhere(diagonal)
    if not rounds.ok:
        failures.append(
            "the trace sum ROUNDS: the first inexact addition is at diagonal "
            f"index {rounds.first_inexact_index!r}"
        )
    if not failures:
        return
    raise AdmissionError(
        "def:declaration, the exact-admissibility paragraph (the "
        "alice_marginal_exact row): the declared alice_marginal is refused at "
        "EXACTLY 0, there being no window in this module to decide it at. "
        "Failing: "
        + "; ".join(failures)
        + f". The trace order is the module's and is recorded: "
        f"{ALICE_SUMMATION_ORDER}. Nothing is repaired here",
        reason=AdmissionRefusal.DECLARATION_NOT_EXACTLY_ADMISSIBLE,
        predicate=GroupAPredicate.ALICE_MARGINAL_EXACT,
    )
