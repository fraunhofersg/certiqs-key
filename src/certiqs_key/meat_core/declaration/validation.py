"""Bundle validation: the checks of spec/architecture.md 3.6, as hard errors.

"Before constructing a problem, ``meat-core`` validates its bundle. ... A failure
is a hard error, never a warning and never a repair: a bundle that does not
validate produces no result at all." Nothing in this module warns, repairs, or
substitutes a default. Its outcomes are what the ``map_validation_report``
output row carries.

What is checked here is what the claim files state, clause by clause:
``def:admissible-declaration`` (i)-(viii), ``def:admissible-acceptance-set``, the
declared test-statistics model that ``reductions/ass:tsm`` covers, and the input domains
of the interface's ``inputs`` table. The operator-bundle format
(:mod:`certiqs_key.domain.validation`) has already checked what a file can be
wrong about as data -- shapes, dtypes, totality of the tables, alphabet keying;
it deliberately does not check positivity, POVM completeness, block-diagonality,
homogeneity or convexity, and those are exactly what this module adds.

THIS VALIDATOR IS THE ENGINE'S OWN AND IS NOT A CALL INTO THE COMPILER'S. The
compiler decided its own V1-V8 on the numbers before it emitted them; a
consumer decides and never infers, so the decision is taken again here, by an
implementation that was not written against the compiler's and is not adjusted
for it. A disagreement between the two is a defect and not a merge conflict,
which is what tests/golden/test_protocol_compiler_docking.py exists for.

Two clauses are not decidable here and say so:

* **def:admissible-declaration (vii), ``W`` nonempty.** With an empty constraint list
  the feasible set is never empty -- ``omega = tau_A x rho`` on any single sector is
  feasible -- and that is asserted. With a nonempty list, nonemptiness is a
  semidefinite feasibility question; a backend's infeasibility report at
  solve time is a hard error, but it is numerical and decides nothing
  exactly (``def:admissible-declaration``). The compiler establishes it
  one-sidedly on the declaration it emits.
* **A-ATK and A-SRC.** Both are supplier obligations, and BOTH ARE THEIR
  OWNERS' rather than this module's (``protocol-compiler/ass:atk`` and
  ``transmitter/ass:src``). A-SOUND is no row beside them: the soundness of
  an emitted entry is a conclusion of reductions' theorems
  (``reductions/rem:sound-and-atk``). This module never verifies them;
  ``attack_set_license`` and ``source_replacement_license`` are attestations,
  and their PRESENCE is what this module acts on (the gates of
  :mod:`certiqs_key.meat_core.finitekey.keylength`), never their content.

THE DECLARED DATA IS EXACTLY ADMISSIBLE OR THE RUN IS REFUSED
============================================================
THIS MODULE TAKES NO TOLERANCE (spec/architecture.md 2.8: "Modules receive no
tolerance to reason with: no module has a tolerance input"). The admission of
``bob_povm`` is not decided against a DECLARED ``tau_num``, and no family with a
nonzero defect is admitted for exploration; :func:`validate_declaration` takes
no tolerance argument to decide it with.

WHAT DECIDES IT is :mod:`certiqs_key.meat_core.declaration.admission`, the
exact admission of ``def:declaration``: the sector map compared in its three
components, Hermiticity and positive semidefiniteness per block, completeness
per sector, and the declared-order completeness sum verified to round nowhere,
EVERY ONE DECIDED EXACTLY AND AT NO WINDOW. A declaration failing any of them
is refused, naming the predicate and the index, and NOTHING IS REPAIRED --
which is exactly why the non-evaluable case is refused rather than computed:
``sqrt(F_v)`` would otherwise be taken of a repaired operator.

EVERY IDENTITY THIS MODULE DECIDES ON DECLARED DATA IS DECIDED EXACTLY, Alice's
``tau_A`` and ``{M_x}`` included -- through
:func:`~certiqs_key.meat_core.declaration.admission.admit_alice_povm_exact` and
:func:`~certiqs_key.meat_core.declaration.admission.admit_alice_marginal_exact`,
each with a ROUND-NOWHERE clause on its defining sum -- and so are the
constraint operators, whose Hermiticity is the interface's
``constraint_operator_exact`` row and not a type condition.

WHAT IS CHECKED PER SOURCE MODE
===============================
``rem:modes-da1`` makes the marginal slot the mode, so the mode changes what is
well-formed:

* TRUSTED (``tau_A`` declared): ``tau_A`` is a ``d_A x d_A`` state -- positive
  semidefinite and ``tr tau_A = 1``, ``def:admissible-declaration`` (ii). A SINGULAR
  ``tau_A`` is admissible and must not be refused (``rem:basis-invariance``);
  ``tau_A = 0`` is inadmissible on two independent grounds, both named in the
  error. Each ``Theta_k`` is Hermitian on ``A``.
* UNTRUSTED (slot value ``none``): there is no marginal to check, and each
  ``Theta_k`` is a real scalar ``c_k`` (``def:homog`` (b)). An operator
  right-hand side is refused: ``rem:homog`` (a) exhibits a licensed attack set
  for which reading it as ``c_k 1_A`` empties the feasible set at ``d_A >= 2``,
  so the two are not two conventions for one restriction.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from fractions import Fraction

import numpy as np

from certiqs_key.domain.manifest import OperatorBundleManifest
from certiqs_key.foundations.exact_admission import is_hermitian_exact
from certiqs_key.meat_core.acceptance.geometry import (
    SINGLETON,
    AcceptanceDefect,
    acceptance_verdict,
)
from certiqs_key.meat_core.declaration.admission import (
    AdmissionError,
    BobPovmAdmission,
    admit_alice_marginal_exact,
    admit_alice_povm_exact,
    admit_declaration,
)
from certiqs_key.meat_core.declaration.declaration import ProtocolDeclaration, RhsTag
from certiqs_key.meat_core.errors import DeclarationError, UnsupportedDeclarationError
from certiqs_key.meat_core.objective.branch import sifting_map
from certiqs_key.meat_core.objective.linalg import as_matrix
from certiqs_key.meat_core.reasons import GroupAPredicate
from certiqs_key.meat_core.reasons import RefusalReason as AdmissionRefusal

#: ``<module-id>@<contract_version>`` of the ACCEPTED contract this code
#: implements (the interface's ``artifact_bindings``), the contract version
#: being one spec/modules/meat-core/module.yaml carries. An artefact
#: claiming any other spec version is not this module's to consume, and AN
#: ARTEFACT MAY NOT CLAIM A DRAFT VERSION. The expectations that spell the
#: string are edited BY HAND when it moves, never regenerated from the code.
MATHEMATICAL_SPEC_VERSION = "meat-core@1.28.0"

#: The conventions of the interface that a bundle must declare, and the only
#: values this module accepts for them. ``test_statistics_model`` is the sharp
#: one: a profile wishing to use ``fixed_fraction`` must supply a
#: trusted-selector argument OUTSIDE this contract and be reviewed again, and
#: nothing here licenses it (``reductions/ass:tsm``, inherited).
REQUIRED_ASSUMPTIONS: Mapping[str, object] = {
    "test_statistics_model": "output_state",
    "round_homogeneity": True,
    "log_base": 2,
    "entropy_units": "bits",
    "entropy_variant": "sandwiched-renyi",
    "arrow": "up",
}


def validate_declaration(declaration: ProtocolDeclaration) -> BobPovmAdmission:
    """Raise on the first violation of admissibility or of an input-row domain.

    Admissibility is ``def:admissible-declaration``, decided as
    ``req:declaration-admission`` requires.

    IT TAKES NO TOLERANCE ARGUMENT, and there is no signature it could take one
    in. A ``tau_num`` would be a datum of the REQUEST deciding the admission of
    ``bob_povm``; admission is exact, so the only argument this function has is
    the declaration it decides.

    THE ORDER IS THE INTERFACE'S ``fail_closed`` ORDER, as far as this function
    reaches it: every required datum is present and in its domain, then the
    declared families are exactly admissible, then the maps are generated from
    what was admitted. The numerical admission runs LAST and deliberately: a
    declaration whose SHAPE is wrong -- a missing block, a wrong dimension, an
    untotal table -- has no well-defined family to decide. Every check before it
    is a type or domain condition.

    Returns:
        The exact-admission record of the declared receiver family, for the
        ``map_validation_report``. There is no second branch to report: a
        declaration is exactly admissible or this function raises.

    Raises:
        DeclarationError: naming the component and the clause it violates.
        AdmissionError: a subclass carrying the machine-readable reason the
            interface spells -- ``sector_map_disagreement``,
            ``bob_povm_summation_rounds`` or
            ``declaration_not_exactly_admissible`` -- and the Group A row that
            failed.
        UnsupportedDeclarationError: for a well-formed declaration outside this
            implementation's coverage (an acceptance-set geometry it does not
            read).
    """
    _validate_dimensions(declaration)
    _validate_marginal(declaration)
    _validate_povms(declaration)
    _validate_partition(declaration)
    _validate_tables(declaration)
    _validate_key_map(declaration)
    _validate_constraints(declaration)
    validate_acceptance_set(declaration)
    return admit_declaration(declaration)


def _validate_dimensions(declaration: ProtocolDeclaration) -> None:
    """Check the dimension and alphabet domains of the `inputs` table."""
    if declaration.alice_dim < 1:
        raise DeclarationError("the `inputs` table: alice_dim must satisfy d_A >= 1")
    if not declaration.sector_index_set:
        raise DeclarationError(
            "the `inputs` table: the sector index set must be nonempty"
        )
    if len(set(declaration.sector_index_set)) != len(declaration.sector_index_set):
        raise DeclarationError(
            "the `inputs` table: the sector index set repeats a sector"
        )
    for sector in declaration.sector_index_set:
        if declaration.sector_dims.get(sector, 0) < 1:
            raise DeclarationError(
                f"the `inputs` table: sector {sector!r} must have d_s >= 1"
            )
    if declaration.rounds < 1:
        raise DeclarationError("the `inputs` table: rounds must satisfy n >= 1")
    if declaration.key_value_count < 1:
        raise DeclarationError(
            "the `inputs` table: the raw-key alphabet Z = {0, ..., d_Z - "
            "1} needs d_Z >= 1"
        )
    if not declaration.acceptance_values:
        raise DeclarationError("the `inputs` table: the acceptance alphabet is empty")


def _validate_marginal(declaration: ProtocolDeclaration) -> None:
    """Check the MARGINAL SLOT against def:admissible-declaration (ii).

    The slot holds ``tau_A`` in ``S_=(A)`` or the value ``none``, and its value
    IS the source mode (contract Remark ``rem:modes-da1``). In untrusted-source
    mode there is nothing to check and nothing missing.

    SHAPE HERE, ARITHMETIC IN THE ROW THAT OWNS IT. Hermiticity, positivity and
    ``tr tau_A = 1`` are the `declared_thresholds` table's
    ``alice_marginal_exact`` row, decided at EXACTLY 0 and at no window, by
    :func:`~certiqs_key.meat_core.declaration.admission.admit_alice_marginal_exact`,
    whose trace is additionally verified to round nowhere. What is left here is the
    shape, which the format decides, and the ``tau_A = 0`` refusal, which is a
    NAMED case of ``transmitter/rem:source-mode`` (c) rather than a defect of
    the trace, and deserves its own two grounds.
    """
    if declaration.alice_marginal is None:
        return
    tau = as_matrix(declaration.alice_marginal)
    if tau.shape != (declaration.alice_dim, declaration.alice_dim):
        raise DeclarationError(
            f"def:admissible-declaration (ii): tau_A has shape {tau.shape}, expected "
            f"({declaration.alice_dim}, {declaration.alice_dim})"
        )
    if not bool(np.any(tau != 0)):
        # Remark transmitter/rem:source-mode (c), stated with BOTH of its grounds: an
        # implementation that rejects tau_A = 0 for only one of them will accept
        # the other spelling of the same mistake. DECIDED EXACTLY, against the
        # entries and not against a magnitude derived from them: tau_A = 0 is a
        # declared object and not a small one.
        raise DeclarationError(
            "Remark transmitter/rem:source-mode (c): tau_A = 0 is inadmissible, and it "
            "is "
            "not how the absent marginal is expressed. Two independent "
            "grounds: (1) def:admissible-declaration (ii) requires the marginal slot "
            "to "
            "hold a NORMALIZED state, tr tau_A = 1; (2) even without "
            "normalization, omega_A = 0 forces tr omega = 0 and hence "
            "omega = 0, so the feasible set is empty against "
            "def:admissible-declaration (vii) and "
            "Eq. eq:hlow-def would be an infimum over nothing. The absent "
            "marginal is the slot value `none` (machine value null); the "
            "trivial marginal is d_A = 1 with tau_A = [1]; tau_A = 0 is neither"
        )
    admit_alice_marginal_exact(declaration)


def _validate_povms(declaration: ProtocolDeclaration) -> None:
    """Check both POVMs against def:admissible-declaration (iii).

    SHAPE HERE, ARITHMETIC IN THE ROWS THAT OWN IT. Alice's side is the
    ``alice_povm_exact`` row of `declared_thresholds` and Bob's side is its
    ``bob_povm_admission`` and ``bob_povm_summation_exact`` rows; all three are
    decided at EXACTLY 0, at no window, with a round-nowhere clause on the
    defining sum. NEITHER IS DECIDED HERE and neither is decided against a
    constant this module chose.
    """
    d_a = declaration.alice_dim
    if not declaration.alice_povm:
        raise DeclarationError(
            "def:admissible-declaration (iii): Alice's POVM is empty"
        )
    for x, element in declaration.alice_povm.items():
        operator = as_matrix(element)
        if operator.shape != (d_a, d_a):
            raise DeclarationError(
                f"def:admissible-declaration (iii): M_{x} has shape {operator.shape}, "
                f"expected ({d_a}, {d_a})"
            )
    admit_alice_povm_exact(declaration)

    if not declaration.bob_povm:
        raise DeclarationError(
            "def:admissible-declaration (iii): Bob's POVM is empty"
        )
    # SHAPE ONLY. The POSITIVITY, HERMITICITY and COMPLETENESS of the declared
    # {F_v} are decided EXACTLY in
    # :func:`certiqs_key.meat_core.declaration.admission.admit_declaration`,
    # which `validate_declaration` calls last -- so this loop applies no
    # predicate of its own to Bob's side at all. What remains here is a TYPE
    # condition: that every declared element carries a block on every declared
    # sector, of the declared width. A type says what shape a datum has, not
    # how near one number is to another, and is decided rather than measured.
    for sector in declaration.sector_index_set:
        width = declaration.sector_dims[sector]
        for v, blocks in declaration.bob_povm.items():
            if sector not in blocks:
                raise DeclarationError(
                    f"def:admissible-declaration (iii): F_{v} declares no block on "
                    f"sector {sector!r}; every Bob POVM element is "
                    "sector-block-diagonal, so every block is part of the "
                    "declaration"
                )
            block = as_matrix(blocks[sector])
            if block.shape != (width, width):
                raise DeclarationError(
                    f"def:admissible-declaration (iii): F_{v}^({sector}) has shape "
                    f"{block.shape}, expected ({width}, {width})"
                )


def _validate_tables(declaration: ProtocolDeclaration) -> None:
    """Check totality of the declared function tables, def:admissible-declaration (i).

    The announcement tables are total on the READOUT alphabets ``O_A``, ``O_B``,
    not on ``X`` and ``V``: def:admissible-declaration (viii) makes a party's
    announcement a function of its own readout. Under the default partition the
    two coincide.
    """
    partition = declaration.partition
    for o_a in partition.alphabet_alice:
        if o_a not in declaration.announce_alice:
            raise DeclarationError(
                "def:admissible-declaration (i): a_A is not total; no announcement "
                f"for {o_a!r}"
            )
    for o_b in partition.alphabet_bob:
        if o_b not in declaration.announce_bob:
            raise DeclarationError(
                "def:admissible-declaration (i): a_B is not total; no announcement "
                f"for {o_b!r}"
            )
    for x in declaration.alice_outcomes:
        for v in declaration.bob_outcomes:
            kappa = declaration.announcement(x, v)
            if kappa not in declaration.accept_statistic:
                raise DeclarationError(
                    f"def:admissible-declaration (i): phi is not total; no acceptance "
                    f"value for the announcement class {kappa}"
                )
            if declaration.accept_statistic[kappa] not in declaration.acceptance_values:
                raise DeclarationError(
                    f"def:admissible-declaration (i): phi maps {kappa} outside the "
                    "declared acceptance alphabet"
                )


def _validate_key_map(declaration: ProtocolDeclaration) -> None:
    """Check ``r`` against def:admissible-declaration (iv), (v) and (viii)."""
    for x in declaration.alice_outcomes:
        for v in declaration.bob_outcomes:
            if (x, v) not in declaration.key_map:
                raise DeclarationError(
                    "def:admissible-declaration (i): r is not total; no value at "
                    f"{(x, v)}"
                )
            value = declaration.raw_key(x, v)
            if value is None:
                continue
            if not 0 <= value < declaration.key_value_count:
                raise DeclarationError(
                    f"def:admissible-declaration (iv): r{(x, v)} = {value} lies "
                    "outside "
                    f"Z = {{0, ..., {declaration.key_value_count - 1}}}"
                )
    # def:admissible-declaration (v): announcement-determined sifting. sifting_map
    # raises on the first class that mixes sifted and unsifted outcome pairs.
    sifting_map(declaration)
    _validate_holder(declaration)


def _validate_partition(declaration: ProtocolDeclaration) -> None:
    """Check the party partition ``P`` of contract Definition ``def:declaration``.

    Part (a) only, which is the only part any derivation consumes: both readout
    maps are TOTAL on ``X x V`` and land in their declared alphabets, and both
    announcement tables are total on the alphabet their party actually reads.
    Part (b) carries a ``protocol-compiler`` obligation this module never
    verifies, so it is checked for coverage in the bundle format and not
    re-litigated here.
    """
    partition = declaration.partition
    for x in declaration.alice_outcomes:
        for v in declaration.bob_outcomes:
            for name, table, alphabet in (
                ("pi_A", partition.readout_alice, partition.alphabet_alice),
                ("pi_B", partition.readout_bob, partition.alphabet_bob),
            ):
                if (x, v) not in table:
                    raise DeclarationError(
                        f"def:admissible-declaration (viii): the readout map {name} is "
                        f"not total; no value at {(x, v)}"
                    )
                if table[(x, v)] not in alphabet:
                    raise DeclarationError(
                        f"def:admissible-declaration (viii): {name}{(x, v)} = "
                        f"{table[(x, v)]!r} lies outside the declared readout "
                        f"alphabet {list(alphabet)}"
                    )


def _validate_holder(declaration: ProtocolDeclaration) -> None:
    """Check party computability: def:admissible-declaration (viii), ``eq:partycomp``.

    The declared key holder must compute the raw key from ITS OWN READOUT and
    the announcements: there must be a total ``r_h`` with
    ``r(x, v) = r_h(pi_h(x, v), a(x, v))``. Equivalently -- and this is what is
    checked -- two outcome pairs that agree on ``(pi_h, a)`` must carry the same
    raw-key value.

    The WIDE READING IS LOAD-BEARING. A narrower reading would ask only
    that ``r`` be a function of the holder's own OUTCOME ``x`` (or ``v``); the
    contract records that this "would make it vacuous for any declaration that
    places both parties' data in ``v`` ... while guaranteeing nothing about what
    the key holder can in fact compute". Under the DEFAULT partition
    ``pi_A(x, v) = x`` and ``pi_B(x, v) = v``, so the check below reduces to the
    narrower condition verbatim.

    Without it no party could compute ``Z_1^n``, and the error-correction and
    verification steps of C14 would be undefined rather than merely optimistic.
    """
    holder = str(declaration.key_holder)
    seen: dict[tuple[str, tuple[str, str]], int | None] = {}
    for x in declaration.alice_outcomes:
        for v in declaration.bob_outcomes:
            kappa = declaration.announcement(x, v)
            own = declaration.readout(holder, x, v)
            key = (own, kappa)
            value = declaration.raw_key(x, v)
            if key in seen and seen[key] != value:
                raise DeclarationError(
                    "def:admissible-declaration (viii): the raw-key map is not "
                    f"computable by the declared key holder {holder!r}. With "
                    f"own readout {own!r} and announcement {kappa} the map "
                    f"takes both {seen[key]!r} and {value!r}"
                )
            seen[key] = value


def _validate_constraints(declaration: ProtocolDeclaration) -> None:
    """Check the declared list ``L`` against def:admissible-declaration (iii) and (vi).

    The right-hand side is declared in ONE OF TWO TAGGED FORMS (Definition
    ``def:homog``) and what each tag requires of ``bound`` is
    a TYPE condition, decided rather than measured and at no window. The
    ``homogeneous`` tag carries the real scalar ``c_k`` and is available in
    BOTH modes: a trusted-mode scalar is the LICENSED form. The ``general`` tag
    carries a Hermitian ``Theta_k`` on ``A`` and exists in trusted-source mode
    only:
    Remark ``rem:homog`` (a) exhibits a licensed attack set -- ``O = 1_Q``,
    ``succeq``, ``c = 1``, every CPTP map admissible -- for which reading an
    untrusted-mode entry as ``Theta_k = c_k 1_A`` forces ``omega_A >= 1_A``,
    contradicting ``tr omega = 1`` and emptying the feasible set at
    ``d_A >= 2``, although the attack set it came from restricts nothing.

    ADMISSIBLE IS NOT LICENSED, and this function decides only the first. A
    ``general`` entry is well-formed input and every structural and numerical
    claim is proved for it; whether the list may reach a key length is part (i)
    of the two-part gate, in
    :func:`certiqs_key.meat_core.finitekey.keylength.licensed_class_check`.
    """
    d_a = declaration.alice_dim
    for index, entry in enumerate(declaration.constraint_list):
        for sector in declaration.sector_index_set:
            if sector not in entry.operator_blocks:
                raise DeclarationError(
                    f"def:admissible-declaration (iii): constraint {index} declares no "
                    f"block on sector {sector!r}; O_k is sector-block-diagonal"
                )
            width = declaration.sector_dims[sector]
            block = as_matrix(entry.operator_blocks[sector])
            if block.shape != (width, width):
                raise DeclarationError(
                    f"def:admissible-declaration (iii): constraint {index} block "
                    f"{sector!r} has shape {block.shape}, expected "
                    f"({width}, {width})"
                )
            if not is_hermitian_exact(block):
                # THE INTERFACE'S ``constraint_operator_exact`` ROW, AND THE
                # PREDICATE IS DECIDED EXACTLY. A ``HERMITICITY_TOLERANCE``
                # would be a WINDOW ON DECLARED DATA -- the one
                # thing spec/architecture.md 2.8 forbids a module outside the
                # instance. def:admissible-declaration (iii) asks Hermiticity of hat O_k
                # per sector block and def:declaration's exact-admissibility
                # paragraph decides it at exactly zero. Positivity is asked of
                # NO constraint operator: def:admissible-declaration (iii), def:homog
                # and the compiler's def:target D(vi) ask Hermiticity only, and no
                # proof of this module reads more.
                raise AdmissionError(
                    f"def:declaration, the exact-admissibility paragraph (the "
                    f"constraint_operator_exact row): constraint {index} block "
                    f"{sector!r} is NOT EXACTLY HERMITIAN. def:admissible-declaration "
                    "(iii) asks "
                    "hat O_k Hermitian block by block and sector-block "
                    "diagonal; the predicate is decided entry by entry on the "
                    "declared binary64 numbers, at no window, and nothing is "
                    "symmetrized",
                    reason=AdmissionRefusal.DECLARATION_NOT_EXACTLY_ADMISSIBLE,
                    predicate=GroupAPredicate.CONSTRAINT_OPERATOR_EXACT,
                )
        # PART (i)'s DATUM, TYPED AGAINST THE MODE. Definition def:homog
        # declares the right-hand side in ONE OF TWO TAGGED FORMS, and what
        # each tag requires of `bound` is a TYPE condition -- decided, never
        # measured, and at no window.
        if entry.rhs_tag is RhsTag.HOMOGENEOUS:
            if not entry.is_scalar:
                raise DeclarationError(
                    f"Definition def:homog: entry {index} declares the "
                    "`homogeneous` form, whose right-hand side is the REAL "
                    "SCALAR c_k, and carries an operator. The operator form "
                    "is the `general` tag"
                )
            if not math.isfinite(entry.scalar_bound):
                raise DeclarationError(
                    f"def:admissible-declaration (vi): c_{index} = "
                    f"{entry.scalar_bound!r} is not a real number"
                )
        elif not declaration.is_trusted_source:
            raise DeclarationError(
                f"Definition def:homog (b): entry {index} declares the "
                "`general` form -- a Hermitian Theta_k on A -- but this "
                "declaration is in UNTRUSTED-source mode, where the "
                "right-hand side IS a real scalar c_k and the operator form "
                "does not exist. It is not an equivalent spelling: Remark "
                "rem:homog (a) exhibits a licensed attack set for which "
                "Theta_k = c_k 1_A forces omega_A >= 1_A and empties the "
                "feasible set at d_A >= 2, although the attack set it came "
                "from restricts nothing"
            )
        else:
            if entry.is_scalar:
                raise DeclarationError(
                    f"Definition def:homog: entry {index} declares the "
                    "`general` form, whose right-hand side is a Hermitian "
                    "Theta_k on A, and carries a scalar. The scalar form is "
                    "the `homogeneous` tag"
                )
            bound = as_matrix(entry.operator_bound)
            if bound.shape != (d_a, d_a):
                raise DeclarationError(
                    f"def:admissible-declaration (vi): Theta_{index} has shape "
                    f"{bound.shape}, expected ({d_a}, {d_a}) on A"
                )
            if not is_hermitian_exact(bound):
                raise AdmissionError(
                    f"def:declaration, the exact-admissibility paragraph (the "
                    f"constraint_operator_exact row): Theta_{index} is NOT "
                    "EXACTLY HERMITIAN. def:admissible-declaration (vi) types the "
                    "`general` "
                    "right-hand side as a Hermitian operator on A, and the "
                    "predicate is decided at no window",
                    reason=AdmissionRefusal.DECLARATION_NOT_EXACTLY_ADMISSIBLE,
                    predicate=GroupAPredicate.CONSTRAINT_OPERATOR_EXACT,
                )


def validate_acceptance_set(declaration: ProtocolDeclaration) -> None:
    """Check the acceptance set against def:admissible-acceptance-set.

    ``req:acceptance-set-admission``: the engine admits an acceptance set only
    when it decides, exactly on the declared data, that the set is admissible
    -- a geometry tag every well-formed datum of which denotes a closed convex
    subset of the simplex, and data well formed for that tag -- and refuses
    every other. Both geometries are decided here: a polytope through
    :func:`~certiqs_key.meat_core.acceptance.geometry.acceptance_verdict`, a
    singleton's vector below. PUBLIC because it is the symbol that
    requirement's ``implements`` names.

    Two geometries, checked differently because they fail differently. A
    ``polytope`` is checked by
    :func:`~certiqs_key.meat_core.acceptance.geometry.acceptance_verdict`: the data
    first for well-formedness against the form it claims, and only then the
    denotation for emptiness -- an empty acceptance set SATISFIES
    def:admissible-acceptance-set, so the refusal cannot come from the definition and
    has to be decided.

    A ``singleton`` is its own validation predicate: a vector that is
    non-negative and SUMS TO ONE EXACTLY, over the rationals. Contract Section
    2.6's ``acceptance_data_exact`` row declares the window "exactly 0" and the
    kind "exact rational arithmetic, the exact island", and the conventions makes
    the acceptance data the ONE exception to the binary64 number model: "every
    declared number is a binary64 datum and IS the value it declares, WITH THE
    SINGLE EXCEPTION of the acceptance data of def:admissible-acceptance-set, which are
    exact rationals". So the comparison is made over :class:`fractions.Fraction` and
    admits nothing a window would have admitted.

    THERE IS NO WINDOW. A constant this module chose would decide a declared
    predicate the contract puts at exactly 0 -- an UNDECLARED DEFAULT, which
    spec/architecture.md 2.8 forbids a module to supply. A declaration whose
    frequencies do not close exactly is refused, and the remedy is the
    producer's: emit exact rationals, or snap at the instance before this
    module sees the data.
    """
    acceptance = declaration.acceptance_set
    verdict = acceptance_verdict(declaration)
    if verdict.defect is AcceptanceDefect.UNSUPPORTED_GEOMETRY:
        raise UnsupportedDeclarationError(verdict.detail)
    if verdict.defect is AcceptanceDefect.EMPTY:
        # NOT attributed to def:admissible-acceptance-set, which an empty set SATISFIES
        # -- it is a closed convex subset of the simplex. The refusal stands and comes
        # from elsewhere: Eq. eq:bacc-def is vacuous on it, which the detail
        # says in its own words.
        raise DeclarationError(verdict.detail)
    if verdict.defect is not None:
        raise DeclarationError(f"def:admissible-acceptance-set: {verdict.detail}")
    if acceptance.geometry != SINGLETON:
        return
    frequencies = acceptance.frequencies
    if len(frequencies) != len(declaration.acceptance_values):
        raise DeclarationError(
            f"def:admissible-acceptance-set: the accepted frequency vector has "
            f"{len(frequencies)} entries but the acceptance alphabet has "
            f"{len(declaration.acceptance_values)}"
        )
    if any(value < 0.0 for value in frequencies):
        raise DeclarationError(
            "def:admissible-acceptance-set: the acceptance set is a subset of the "
            "probability simplex; a declared frequency is negative"
        )
    total = sum((Fraction(value) for value in frequencies), Fraction(0))
    if total != 1:
        raise DeclarationError(
            "def:admissible-acceptance-set: the accepted frequency vector does not sum "
            "to 1. "
            f"Its EXACT sum is {total} ({float(total)!r} as a binary64 datum), "
            "and `declared_thresholds`'s acceptance_data_exact row "
            "decides this "
            "at exactly 0 in exact rational arithmetic -- the acceptance data "
            "being the one exception to the binary64 number model (Section "
            "2.5, the exact island). Nothing is repaired and no window is "
            "applied; a producer emits exact rationals, or snaps at the "
            "instance before this module sees the data"
        )


def validate_manifest_bindings(manifest: OperatorBundleManifest) -> None:
    """Raise unless the manifest binds to this contract with these conventions.

    Two things a bundle must get right before its numbers are read at all: the
    ``mathematical_spec_version`` of the conventions, and the declared
    conventions of that section -- above all the ``output_state``
    test-statistics model of Assumption A-TSM, whose violation is a security
    break rather than a configuration difference.
    """
    if manifest.mathematical_spec_version != MATHEMATICAL_SPEC_VERSION:
        raise DeclarationError(
            "the conventions: mathematical_spec_version must be "
            f"{MATHEMATICAL_SPEC_VERSION!r} for a bundle this module consumes; "
            f"got {manifest.mathematical_spec_version!r}"
        )
    for key, expected in REQUIRED_ASSUMPTIONS.items():
        if key not in manifest.assumptions:
            raise DeclarationError(
                f"the conventions: the bundle does not declare {key!r}. "
                "Assumptions are data (spec/architecture.md 2.4) and an "
                "undeclared convention is not a default"
            )
        declared = manifest.assumptions[key]
        if declared != expected:
            raise DeclarationError(
                f"the conventions: {key!r} must be {expected!r} for this "
                f"contract; the bundle declares {declared!r}. In particular no "
                "fixed_fraction test-statistics model is licensed anywhere in "
                "this contract (Assumption A-TSM)"
            )
