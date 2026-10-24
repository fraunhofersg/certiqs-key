"""PC3 -- public choices are WEIGHTS, never fractions. TWO FORMS.

``def:weighted``, ``lem:weighted``, ``thm:choice-encoding``, ``rem:relabel``. The
``test_statistics_model`` convention calls ``output_state`` "BINDING, and the
strongest convention this module carries": every
per-round public choice of known bias -- a basis choice, a test-versus-
generation round type, a probe setting -- is a component of the joint outcome
and enters as a WEIGHT INSIDE the POVM elements, ``N_{u,t} = q_t N_{u|t}``.

Both forms validate binary64 weight inputs before using them. The first-form
guard refuses an off-lattice declared weight before it could appear as (S)
failing at addition one. Ordinary user inputs are prepared and
recorded by the run boundary; this core neither converts them nor adds a
numerical tolerance.

THE EMITTED ALPHABET IS A DISJOINT UNION AND NOT A PRODUCT
==========================================================
Definition ``def:weighted`` indexes the family by
``V = sqcup_{t in T_pub} U_t x {t}``. With residual alphabets that DIFFER
between choices -- a probe setting with three outcomes beside a basis with
two -- a product would not even type, and the disjoint union is what makes the
choice value recoverable from the outcome index alone, which is what Theorem
``thm:choice-encoding`` (iii) needs. :func:`weighted_family` therefore returns the joint
alphabet and the choice of each of its members alongside the matrices, rather
than leaving either to be inferred.

THE SECOND FORM: ROUTE C
========================
``def:weighted`` has a SETTING-DEPENDENT form on Bob's side, applied AFTER the reduction
chain to the family the last link delivered:

    ``N_(v,f) = P(f | t(v)) F_v``   over the support
    ``V_P = {(v, f) : P(f | t(v)) > 0}``

with a declared total setting map ``t : V -> T`` -- the class map of the
reductions artefact's joint alphabet where the chain was emitted by
``reductions``, declared with the family otherwise -- and a stochastic matrix
``P(f | t)`` on ``T x F``. :func:`setting_weighted_family` is that form and
:class:`ChoiceWeighting` is the input record the ``choice_weighting``
row types.

FOUR THINGS ABOUT IT THAT ARE DECISIONS AND NOT DETAILS.

1. ``P`` IS READ THROUGH THE SETTING AND THROUGH NOTHING ELSE. It is declared
   on ``T x F`` and reaches an outcome only through ``t(v)``; a weighting
   presented indexed by ``V``, by the device outcome, or by any component of
   ``v`` other than its setting is REFUSED BY TYPE with
   ``choice_weight_depends_on_outcome``, "because a value ``f`` whose weight
   varied with the device outcome would be inferred from that outcome and is
   not a choice". The refusal is BY TYPE and nothing is measured: the record
   below has no field through which an outcome-indexed weighting could arrive,
   and :func:`refuse_outcome_dependent_weighting` is for a caller that presents
   one out of band, exactly as :func:`refuse_fixed_fraction` is.
2. ZERO ENTRIES ARE ADMITTED AND THE SUPPORT IS WHAT THEY ARE FOR. "A pair
   ``(v, f)`` with ``P(f | t(v)) = 0`` is not an outcome, is not emitted and
   indexes nothing, so every emitted element carries a strictly positive
   weight, exactly as ``q_t > 0`` requires of the first form."
3. THE PRODUCT ORDER OF ``V_P`` IS FIXED BY ``def:weighted`` AND NOT HERE:
   ``v`` in the declared order of ``V``, and within each ``v``, ``f`` in the
   declared order of ``F``, the pairs off the support omitted.
4. :func:`choice_mass` IS ASSERTED OF THE FIRST FORM AND OF IT ALONE
   (``lem:weighted`` (iii)). What holds of the second is
   :func:`forget_choice` -- ``sum_f N_(v,f) = F_v``, an exact operator
   identity (Eq. ``eq:forgetf``) -- and :func:`choice_marginal`, which is a
   function of the state through the setting marginal (Eq. ``eq:fmarginal``)
   and equals a state-independent ``q_f`` exactly in the setting-independent
   case. No identity of the form ``eq:choicemass`` is asserted for it, and
   ``choice_mass`` raises rather than answering for a family built by the
   second construction.

THE CONDITIONAL FAMILIES ARE DECIDED
====================================
``def:weighted`` reads
"``{N_{u|t}}_u`` is a POVM on ``S``" as exact admissibility in the sense of
``def:exact`` and DECIDES IT -- of each ``t`` separately, on the declared
numbers, BEFORE ANY PRODUCT IS FORMED -- with its own refusal
``conditional_family_not_admissible``. :func:`decide_conditional_families` is
that decision and :func:`conditional_family_order` is the order its (S) leg is
read in.

WHY IT CANNOT BE LEFT TO THE EMITTED FAMILY'S OWN FIVE CONDITIONS, which is the
whole reason the decision exists: ``ex:condfamily`` is two weights ``1/2`` and the
one-outcome families ``diag(1/2, 3/2)`` and ``diag(3/2, 1/2)``, whose weighted
family ``{diag(1/4, 3/4), diag(3/4, 1/4)}`` satisfies (T), (H), (P), (C) and
(S) and passes check V1 and check V3 -- while NEITHER conditional family is a
POVM. "(C) on the emitted family is ONE identity and the inner sums enter it
only through that one combination, so a deficit under one choice value is paid
for by a surplus under another" (``rem:condfamily``). Versions through 0.1.1
admitted that specification; this one refuses it.

WHAT THAT COSTS A CONSUMER OF THE DECLARATION IT WOULD HAVE EMITTED: nothing
visible, which is why the decision has to be taken on the SPECIFICATION.
``thm:choice-encoding`` (iii) emits no ``q_t`` outside a POVM element, so no slot
carries the declared weight; the emitted operators are a consistent POVM implementing a
round-type probability OTHER than the one the ``public_choices`` record
declares and ``ass:coin`` reads, and the failure is between the specification
and the declaration the module built from it.

WHAT EXACTNESS BUYS, AND WHAT IT DOES NOT SAY
=============================================
Theorem ``thm:choice-encoding`` (ii): for every state, the marginal probability of the
choice value ``t`` computed from the emitted declaration equals the declared
weight ``q_t``. :func:`choice_mass` is Eq. ``eq:choicemass``, and it is exact
in the substrate, so the identity is an equality of rationals and not an
approximation. Remark ``rem:exactness`` says what it does NOT say: the number
``q_t`` appears only AFTER summing over ``u``, and the individual terms
``tr[N_{u,t} omega]`` do depend on ``omega``. "That is the whole difference
between the two models", and Assumption ``ass:coin`` is where the physical
content sits -- a choice correlated with the adversary is not a choice of known
bias, and no encoding repairs that.

THE REFUSED ALTERNATIVE, AND WHY NO INPUT KEY IS INVENTED FOR IT
================================================================
Theorem ``thm:choice-encoding`` (iv): the alternative encoding -- the conditional
families together with a separate state-independent fraction applied OUTSIDE the
operators -- "is never emitted"; Requirement ``req:no-fixed-fraction`` refuses a
specification requesting it with the reason ``fixed_fraction_requested``. The
inputs table gives that request no field to arrive in: ``public_choices`` is
typed ``(T_pub, q, {N_{u|t}})`` with no model selector, and no other input row
carries one. The frozen registry routes the question to a human as a
change-request candidate.

This module takes both readings at once, and invents nothing. The substantive
obligation holds BY CONSTRUCTION: :func:`weighted_family` is the only path
from a ``certiqs_key.protocol_compiler.spec.PublicChoices`` record to
emitted matrices, it multiplies the weight in, and no other function of this
package emits a ``q_t`` anywhere outside a POVM element. And for a caller that selects
a model out of
band, :func:`refuse_fixed_fraction` returns the refusal with the verbatim
reason -- WITHOUT adding an input machine key, the interface's machine keys
being binding on this implementation.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from fractions import Fraction

from certiqs_key.foundations.blocks import BlockOperator, Label
from certiqs_key.foundations.errors import HypothesisError, MalformedInputError
from certiqs_key.foundations.exact import (
    Binary64Value,
    Cx,
    Matrix,
    add,
    dimension,
    equal,
    identity,
    is_binary64,
    is_hermitian,
    is_positive_semidefinite,
    kron,
    matmul,
    real_part,
    round_to_binary64,
    scalar_is_binary64,
    scale,
    sum_in_declared_order,
    trace,
    zeros,
)
from certiqs_key.protocol_compiler.reasons import Refusal, RefusalReason
from certiqs_key.protocol_compiler.spec import (
    DirectPovm,
    Party,
    PovmPresentation,
    PublicChoices,
)
from certiqs_key.protocol_compiler.transcript import (
    SUMMATION_PREDICATE,
    PredicateOutcome,
    PredicateSource,
)

__all__ = [
    "ChoiceWeighting",
    "ConditionalFamilyDecision",
    "EmissionDecision",
    "PovmResolution",
    "SettingWeightedFamily",
    "WeightedFamily",
    "choice_marginal",
    "choice_mass",
    "conditional_family_order",
    "decide_conditional_families",
    "decide_emission",
    "decide_setting_emission",
    "forget_choice",
    "is_povm",
    "refuse_fixed_fraction",
    "refuse_outcome_dependent_weighting",
    "resolve_povm",
    "setting_joint_label",
    "setting_weighted_family",
    "weighted_family",
]


def _party_prefix(party: Party) -> str:
    """Return how the transcript spells the declaring party.

    WHY THE TRANSCRIPT SPELLS ONE AT ALL: ONE specification may present both
    Alice's family and the receiver's physical family as choice-weighted
    families (``def:spec`` (a) and (b)), and the two may carry THE SAME joint
    labels -- the BB84 instance's do. Two decisions on two families would then
    share a ``(source, element, block)`` key, and the ``gate_report`` row's
    record would collapse them.

    IT IS THE PARTY'S OWN LABEL AND NOT A SECOND SPELLING. A mapping from
    :class:`~certiqs_key.protocol_compiler.spec.Party` to two letters here
    would be a hand-maintained mirror of that enum's values (PRINCIPLES.md
    section 7), and the label the declaration itself carries is the one a
    consumer already holds.
    """
    return str(party)


@dataclass(frozen=True)
class WeightedFamily:
    """The emitted family of Eq. ``eq:weighted``, with its disjoint-union index.

    ``alphabet`` is ``V = sqcup_t U_t x {t}`` in the emitted order,
    ``elements`` carries ``N_{u,t} = q_t N_{u|t}`` -- the weight is ALREADY
    INSIDE -- and ``choice_of`` records which ``t`` each member belongs to, so
    that Theorem ``thm:choice-encoding`` (iii)'s "the choice value is recoverable from
    the outcome index alone" is a property of the record and not of a convention.
    """

    alphabet: tuple[Label, ...]
    elements: dict[Label, Matrix]
    choice_of: dict[Label, Label]
    weights: dict[Label, Fraction]
    party: Party
    #: What CONSTRUCTING this family decided, for the ``gate_report`` row's
    #: transcript: the two decisions :func:`weighted_family` takes on the
    #: declared weight list (``req:weight-list``), ``sum_t q_t = 1`` on the
    #: EXACT total and condition (S) on its declared-order accumulation. The
    #: representability of the products is :func:`decide_emission`'s, which
    #: concatenates this field in front of its own -- ONE DECISION SITE PER
    #: DECISION, and the transcript reads in the order the decisions were
    #: taken.
    predicates: tuple[PredicateOutcome, ...] = ()
    #: ``req:weight-list``'s refusal, ``choice_weights_not_normalized``, where
    #: the declared weights' exact sum is not 1 or their declared-order
    #: accumulation rounds at some addition; ``None`` where the list is
    #: normalized. THE FAMILY IS TABULATED EITHER WAY -- every product is
    #: formed exactly, and a caller that builds a fixture from it reads the
    #: same matrices -- and it is NEVER EMITTED with a refusal beside it:
    #: :func:`decide_emission` returns this refusal before it decides
    #: anything else, so :func:`resolve_povm` hands a caller the refusal and
    #: no family.
    refusal: Refusal | None = None
    #: (S) on ``sum_t q_t``: every addition of the declared-order accumulation
    #: is exact. One leg of the decision ``refusal`` records.
    weights_sum_rounds_nowhere: bool = True

    def ordered(self) -> tuple[Matrix, ...]:
        """Return the emitted matrices in the emitted alphabet order."""
        return tuple(self.elements[label] for label in self.alphabet)

    def members_of(self, choice: Label) -> tuple[Label, ...]:
        """Return the joint labels belonging to one public choice."""
        return tuple(
            label for label in self.alphabet if self.choice_of[label] == choice
        )


def _joint_label(outcome: Label, choice: Label) -> Label:
    """Return the DEFAULT emitted label of one member of the disjoint union.

    Definition ``def:weighted`` indexes the family by ``sqcup_t U_t x {t}``, so
    the default spelling writes the outcome first. It is a SPELLING and not a
    structure: the outputs table says "semantic labels are metadata; indices are
    binding", and an instance that declares ``joint_labels`` -- as the BB84
    instance does, writing the choice first -- gets its own names over
    the same disjoint union.
    """
    return f"({outcome},{choice})"


def weighted_family(choices: PublicChoices) -> WeightedFamily:
    """Return the choice-weighted family of Definition ``def:weighted``.

    ``V = sqcup_t U_t x {t}`` and ``N_{u,t} = q_t N_{u|t}``.

    THE DECLARED WEIGHT LIST IS DECIDED HERE, AS ``req:weight-list`` STATES.
    Each ``q_t`` must be a binary64 number (``req:binary64-weights``) and
    strictly positive, decided by its sign; a weight failing either is refused
    BY TYPE and raises :class:`~certiqs_key.foundations.errors.MalformedInputError`,
    since no list of such numbers is a weight list at all. The list is then
    decided as a whole: ``sum_t q_t = 1`` EXACTLY, on the declared numbers,
    with the sum accumulated in the order the ``public_choices`` record lists
    ``T_pub`` in (``foundations/req:declared-order``) and required to round at
    no addition. A list failing either leg is refused with
    ``choice_weights_not_normalized``, carried on the returned family's
    ``refusal`` and returned by :func:`decide_emission` before any other
    decision, so no declaration is emitted.

    WHY THE TWO LEGS ARE ONE REASON. They separate in both directions. At the
    decimal literals ``fl(0.9)``, ``fl(0.1)`` the exact sum is ``1 + 2**-55``
    and the second addition rounds to exactly ``1``; at ``2**-54``, ``1/2``,
    ``1/2 - 2**-54`` the exact sum is ``1`` and the second partial sum,
    ``2**-54 + 1/2``, is not a binary64 number. Either way the declared numbers
    and their binary64 accumulation do not agree on a unit sum, and the remedy
    is the same: declare weights whose sum is exactly 1, which the instance
    entry point does for ordinary decimal inputs by the shared snapping rule
    (``req:weight-preparation``; ``foundations/def:snap``).

    WHY THE EQUALITY IS READ ON THE EXACT TOTAL, AND HERE. Deciding it on the
    computed binary64 total would admit ``fl(0.9) + fl(0.1)`` and leave the
    refusal to check V3's condition-(S) leg on the completeness sum the weights
    carry, under another name. ``req:weight-list`` names this one, and it can
    be the reason a caller receives only if the list is decided before the
    family the weights build: where every conditional family is exactly
    complete, an exact weight sum other than 1 makes the emitted family fail
    (C) or (S), so a later decision would always be V3's.
    """
    exact_total = Fraction(0)
    first_inexact: int | None = None
    for position, choice in enumerate(choices.choices, start=1):
        weight = choices.weights[choice]
        if not isinstance(weight, Fraction):  # pragma: no cover - typing guard
            raise MalformedInputError("a declared choice weight is an exact rational")
        # Both forms declare binary64 weights. Enforce that input domain
        # before accumulation: an off-lattice summand is not an (S) failure.
        # Ordinary user numbers are prepared and recorded outside this core.
        if not is_binary64(weight):
            raise MalformedInputError(
                f"q({choice!r}) = {weight} is not a binary64 number; "
                "def:weighted declares q with binary64 entries and this "
                "module decides its conditions on declared numbers"
            )
        if weight <= 0:
            # The DOMAIN condition, decided by its SIGN. Definition
            # def:weighted: "a declared weight that is zero or negative is
            # refused by type", and Definition def:exact "carries no
            # strict-inequality row because none is wanted".
            raise MalformedInputError(
                f"the declared weight of {choice!r} is {weight}; Definition "
                "def:weighted requires q_t > 0"
            )
        exact_total += weight
        # Before the first inexact addition the computed partial sum IS the
        # exact one, so the first addition that rounds is the first position
        # whose exact partial sum is not a binary64 number. 1-BASED IN THE
        # DECLARED ORDER, the convention foundations.exact's SummationVerdict
        # and TraceVerdict use for the same question.
        if first_inexact is None and not is_binary64(exact_total):
            first_inexact = position
    # BOTH DECISIONS ARE RECORDED HERE, WHERE THEY ARE TAKEN. The
    # ``gate_report`` row's first compilation-map item is "sum_t q_t = 1
    # decided exactly with the sum accumulated in the order the
    # ``public_choices`` record lists T_pub in"; condition (S) on that sum is
    # the second. Both are taken in the one pass above, so both are recorded
    # whatever their outcomes.
    weight_family = f"{_party_prefix(choices.party)}:{{q_t}}"
    sums_to_one = exact_total == 1
    rounds_nowhere = first_inexact is None
    predicates = (
        PredicateOutcome(
            source=PredicateSource.COMPILATION_MAP,
            predicate="sum_t q_t = 1",
            element=weight_family,
            block=None,
            outcome=sums_to_one,
        ),
        PredicateOutcome(
            source=PredicateSource.COMPILATION_MAP,
            predicate=SUMMATION_PREDICATE,
            element=weight_family,
            block=None,
            outcome=rounds_nowhere,
            first_failure_index=first_inexact,
            first_inexact_index=first_inexact,
        ),
    )
    refusal: Refusal | None = None
    if not (sums_to_one and rounds_nowhere):
        refusal = Refusal(
            reason=RefusalReason.CHOICE_WEIGHTS_NOT_NORMALIZED,
            detail=_weight_list_detail(
                choices, exact_total, sums_to_one, first_inexact
            ),
        )

    alphabet: list[Label] = []
    elements: dict[Label, Matrix] = {}
    choice_of: dict[Label, Label] = {}
    for choice in choices.choices:
        weight = choices.weights[choice]
        conditional = choices.conditional_elements[choice]
        for outcome in choices.conditional_alphabets[choice]:
            if outcome not in conditional:
                raise MalformedInputError(
                    f"no conditional matrix N_{{{outcome}|{choice}}}"
                )
            label = (
                _joint_label(outcome, choice)
                if choices.joint_labels is None
                else choices.joint_labels[(outcome, choice)]
            )
            if label in elements:
                raise MalformedInputError(
                    f"the disjoint union collides at {label!r}; U_t x {{t}} is "
                    "a DISJOINT union"
                )
            alphabet.append(label)
            elements[label] = scale(weight, conditional[outcome])
            choice_of[label] = choice
    return WeightedFamily(
        alphabet=tuple(alphabet),
        elements=elements,
        choice_of=choice_of,
        weights=dict(choices.weights),
        party=choices.party,
        predicates=predicates,
        refusal=refusal,
        weights_sum_rounds_nowhere=rounds_nowhere,
    )


def _weight_list_detail(
    choices: PublicChoices,
    exact_total: Fraction,
    sums_to_one: bool,
    first_inexact: int | None,
) -> str:
    """Return the detail of a ``choice_weights_not_normalized`` refusal.

    It names the declaring party, the declared order, the exact sum and the
    first addition of the declared-order accumulation that rounds, so that a
    reader sees which leg of ``req:weight-list`` failed, or that both did.
    """
    order = list(choices.choices)
    total = (
        "is exactly 1"
        if sums_to_one
        else f"is exactly {exact_total}, not 1"
    )
    accumulation = (
        "every addition of its declared-order accumulation is exact"
        if first_inexact is None
        else (
            "its declared-order accumulation rounds first at addition "
            f"{first_inexact}"
        )
    )
    return (
        f"the declared weight list {{q_t}} of party {str(choices.party)!r} is "
        f"not normalized: its sum in the declared order {order} {total}, and "
        f"{accumulation}. req:weight-list refuses a weight list whose exact "
        "sum is not 1 or whose declared-order accumulation rounds, and no "
        "declaration is emitted; ordinary decimal weights are prepared onto an "
        "exact unit sum at the instance entry point (req:weight-preparation)"
    )


@dataclass(frozen=True)
class PovmResolution:
    """What :func:`resolve_povm` returns: an emitted family, or a refusal.

    NEVER BOTH AND NEVER NEITHER, which is the same rule
    ``compile.CompilationResult`` enforces one level up
    and for the same reason: the ``fail_closed`` convention requires "a refusal
    with a machine-readable reason and NO declaration", so a resolution that
    carried a family beside a refusal would be a half-emission this contract
    does not have a shape for.

    A REFUSAL HERE IS DATA AND NOT AN EXCEPTION. The claims name both reasons
    a resolution can carry -- ``choice_weights_not_normalized``
    (``req:weight-list``) and ``emitted_value_not_representable``
    (``def:weighted``) -- so the failure IS one of the contract's enumerated
    refusals and must reach the caller as the record the outputs table types,
    not as a raised error a caller cannot act on.
    """

    povm: DirectPovm | None
    refusal: Refusal | None
    #: The emission decision, where one was taken. ``None`` for a
    #: :class:`~certiqs_key.protocol_compiler.spec.DirectPovm` presentation, which this
    #: module was HANDED rather than constructed and on which Definition
    #: ``def:weighted``'s emission obligation therefore does not bear.
    emission: EmissionDecision | None = None

    def __post_init__(self) -> None:
        """Refuse a resolution that emits and refuses, or does neither."""
        if (self.povm is None) == (self.refusal is None):
            raise MalformedInputError(
                "a POVM resolution carries a family or a refusal and never "
                "both and never neither (the conventions, fail_closed)"
            )

    def require(self) -> DirectPovm:
        """Return the family, for a caller that has already handled refusal."""
        if self.povm is None:  # pragma: no cover - guarded at every call site
            raise HypothesisError(
                "this resolution refused; there is no emitted family to take"
            )
        return self.povm


def resolve_povm(presentation: PovmPresentation) -> PovmResolution:
    """Return the emitted family a presentation denotes, or the refusal.

    Definition ``def:compile`` fills the POVM slots from the specification,
    "weighted by Definition ``def:weighted`` where a choice family is
    presented". This is that one line, and it is the ONLY path in this package
    from a public-choice record to emitted matrices -- which is what makes
    Theorem ``thm:choice-encoding`` (iii)'s exclusivity clause true of the code and not
    only of the contract.

    AND IT IS WHY THE EMISSION DECISION IS TAKEN *ON* THIS PATH RATHER THAN
    BESIDE IT. Definition ``def:weighted``: "the compiler decides, BEFORE
    EMITTING ANYTHING, that every entry of every ``N_{u,t}`` is a binary64
    number ... If either decision fails, the compiler refuses -- with
    ``emitted_value_not_representable`` in the first case and with the
    predicate that failed in the second -- and emits no declaration." Because
    this function is the only route from a choice record to matrices, a
    :func:`decide_emission` that merely EXISTED beside it would leave the
    obligation undischarged on every real compilation and the
    ``emitted_value_not_representable`` row unreachable through
    ``compile.compile_specification``.

    THE WEIGHT LIST IS DECIDED ON THE SAME PATH AND FIRST. :func:`weighted_family`
    decides ``req:weight-list`` on the declared weights, and a list whose exact
    sum is not 1 or whose declared-order accumulation rounds is refused with
    ``choice_weights_not_normalized`` before the products are decided, so a
    presentation such as ``fl(0.9)``, ``fl(0.1)`` never reaches check V3.

    THE SECOND DECISION IS NOT TAKEN HERE, AND ITS ABSENCE IS NOT AN OMISSION.
    "The family it forms satisfies Definition ``def:exact`` -- (H), (P), (C)
    and, on its own declared-order sum over ``V``, (S)" is decided by check V3
    on the emitted family, in the emitted index order, and refuses with
    ``alice_povm_summation_rounds`` / ``bob_povm_summation_rounds`` naming the
    predicate that failed. Deciding it twice would give one failure two names.

    A ``DirectPovm`` PRESENTATION CARRIES NO EMISSION OBLIGATION. the conventions
    (``no_snapping``): "AN EMITTED MATRIX ENTRY THAT THIS MODULE WAS HANDED IS
    THE ENTRY IT WAS HANDED", and "the ONE OBJECT THIS MODULE CONSTRUCTS rather
    than passes through is the choice-weighted family". So the obligation
    attaches to the weighted branch and to nothing else.

    AND THE REPRESENTABILITY DECISION IS TAKEN ON EVERY PRODUCT THIS MAP FORMS,
    EMITTED OR NOT, which ``def:weighted`` states outright
    and which this function discharges because it is the only route:
    :func:`~certiqs_key.protocol_compiler.compile.compile_specification` calls
    it on the RECEIVER's presentation before the chain stage, and at a
    non-trivial receiver segment those products are the physical family
    (C2) and (C4) read and are never emitted. The string is unchanged
    (``emitted_value_not_representable`` keeps its 0.3.0 spelling), and what
    widened is its stated subject, not this module's behaviour.

    THE ITERATED CASE THE SAME CLAUSE NAMES HAS NO INPUT SHAPE HERE, and that is
    why no second decision site exists for it: ``def:weighted``'s composition
    sentence covers a presentation that declares several independent choices,
    whose intermediate families are this map's own products, and
    :class:`~certiqs_key.protocol_compiler.spec.PublicChoices` declares
    ``{N_{u|t}}_u`` as MATRICES and not as a nested presentation -- so an
    iterated presentation cannot arrive, this map forms no intermediate family,
    and every product it does form passes through this function or through
    :func:`setting_weighted_family`. An input row for iteration would be a scope
    change and is not invented here.

    THE CONDITIONAL FAMILIES ARE DECIDED BEFORE THIS FUNCTION RUNS, and not in
    it: they are declared input and the decision precedes every product
    (:func:`decide_conditional_families`; fail-closed row 1).
    """
    if isinstance(presentation, DirectPovm):
        return PovmResolution(povm=presentation, refusal=None, emission=None)
    family = weighted_family(presentation)
    decision = decide_emission(family)
    if decision.refusal is not None:
        return PovmResolution(povm=None, refusal=decision.refusal, emission=decision)
    return PovmResolution(
        povm=DirectPovm(alphabet=family.alphabet, elements=family.elements),
        refusal=None,
        emission=decision,
    )


def is_povm(elements: tuple[Matrix, ...], dim: int) -> bool:
    """Whether ``{E_i}`` is a POVM on a ``dim``-dimensional space.

    ``E_i >= 0`` for every ``i`` and ``sum_i E_i = 1``. This is Lemma
    ``lem:weighted`` (i) read as a check, and it is exactly the completeness
    and positivity half of check V3.
    """
    if not elements:
        return False
    total: Matrix = zeros(dim, dim)
    for element in elements:
        if dimension(element) != dim:
            raise MalformedInputError(
                f"a POVM element of dimension {dimension(element)} on a "
                f"{dim}-dimensional space"
            )
        # A non-Hermitian operator is not positive semidefinite, and asking the
        # exact LDL^* about one is a hypothesis violation rather than a false
        # answer -- so the verdict is settled here instead of raising.
        if not is_hermitian(element) or not is_positive_semidefinite(element):
            return False
        total = add(total, element)
    return equal(total, identity(dim))


@dataclass(frozen=True)
class ConditionalFamilyDecision:
    """Definition ``def:weighted``'s decision on each ``{N_{u|t}}_u``.

    THE FIRST FAILURE AND NOTHING AFTER IT. ``def:weighted``: the refusal names
    "the declaring party, and the choice value, the predicate, the block and
    the index of the FIRST failure -- for (S), the index of the first inexact
    addition; the decision stops there and does not enumerate the rest". So
    ``predicates`` ends at the decision that failed, exactly as
    :class:`~certiqs_key.protocol_compiler.validation.CheckOutcome` ends at
    V3's, and ``refusal`` carries that one failure.
    """

    refusal: Refusal | None
    #: The per-predicate transcript, keyed per (party, choice value, block) as
    #: the ``gate_report`` row's last enumeration item asks, plus the one (T)
    #: entry the presentation carries as a whole.
    predicates: tuple[PredicateOutcome, ...] = ()

    @property
    def admitted(self) -> bool:
        """Whether every conditional family of the presentation was admitted."""
        return self.refusal is None


def _presentation_label(choices: PublicChoices, outcome: Label, choice: Label) -> Label:
    """Return the emitted joint label of one ``(u, t)`` of a presentation."""
    if choices.joint_labels is None:
        return _joint_label(outcome, choice)
    return choices.joint_labels[(outcome, choice)]


def conditional_family_order(
    choices: PublicChoices,
    choice: Label,
    arriving_order: Sequence[Label] | None = None,
) -> tuple[Label, ...]:
    """Return ``U_t`` in the order condition (S) is decided in on ``{N_{u|t}}_u``.

    ``def:weighted``, "In which order (S) is read on a conditional family": the
    family the weighting produces is indexed by ONE alphabet carrying ONE order
    -- ``X`` where the presentation is Alice's, the physical receiver alphabet
    where it is Bob's -- and (S) on the conditional family of a choice value is
    decided in "the RESTRICTION of that order to the elements the choice value
    ``t`` contributes --- a total order on ``U_t`` whatever the presentation
    listed, so no compatibility of the record's listing with it is required and
    none is decided". Where a declared order arrives with that alphabet the
    compiler takes it (``def:compile``'s binding rule, unchanged); "where none
    arrives, the choice the compiler makes and emits is the record's own
    listing".

    ``arriving_order`` IS THAT ARRIVING ORDER, AS JOINT LABELS, or ``None``.
    Alice's presentation has one -- ``X`` arrives ordered with the source part
    (``def:spec`` (a)) -- and a receiver presentation in this input shape has
    none: the physical alphabet IS what the weighting produces, so the record's
    own listing is the free choice and is emitted
    (:func:`~certiqs_key.protocol_compiler.compile.compile_specification`).

    AND NO PRESENTATION IS REFUSED FOR AN ORDER. Where the arriving order does
    not enumerate this presentation's joint labels -- a supplier that declared
    ``X`` over other names -- there is no restriction to take, so the record's
    listing is used and nothing is refused: "what is fixed here is which order a
    decision is read in, not what a supplier may declare".
    """
    listed = choices.conditional_alphabets[choice]
    if arriving_order is None:
        return tuple(listed)
    outcome_of = {
        _presentation_label(choices, outcome, choice): outcome for outcome in listed
    }
    restricted = tuple(
        outcome_of[label] for label in arriving_order if label in outcome_of
    )
    if len(restricted) != len(listed) or set(restricted) != set(listed):
        return tuple(listed)
    return restricted


def decide_conditional_families(
    choices: PublicChoices,
    system_dim: int,
    arriving_order: Sequence[Label] | None = None,
    factor: Label | None = None,
) -> ConditionalFamilyDecision:
    """Decide the exact admissibility of every ``{N_{u|t}}_u`` of a presentation.

    Definition ``def:weighted``: "``{N_{u|t}}_u`` is a POVM on ``S``" is exact
    admissibility in the sense of Definition ``def:exact``, and "THAT ONE THE
    COMPILER DECIDES TOO, of each ``t`` in ``T_pub`` separately, on the declared
    numbers, BEFORE IT FORMS ANY PRODUCT and therefore before the interface
    conditions on the chain are decided": (H), (P) and (C) per block; (S) on
    the completeness sum in the order :func:`conditional_family_order` returns;
    and (T) as the agreement of the maps the conditional families themselves
    carry. A failure is ``conditional_family_not_admissible``.

    WHY THIS FUNCTION AND NOT :func:`is_povm`, WHICH DECIDES THE SAME NUMBERS.
    ``is_povm`` returns ONE boolean over (H), (P) and (C) and decides no (S) at
    all, and the refusal this decision owes names "the predicate, the block and
    the index of the FIRST failure". An aggregate verdict cannot be keyed by the
    predicate that failed, and the ``gate_report`` row asks for one entry per
    decision. The two must not disagree, and
    ``tests/unit/test_protocol_conditional_families.py`` holds them together on
    the same data.

    WHERE THE CALLER IS, AND WHY IT IS NOT :func:`resolve_povm`. This decision
    is the compilation map's and precedes every product, including the products
    a receiver presentation hands to the chain, so it is taken in
    :func:`~certiqs_key.protocol_compiler.compile.compile_specification` before
    stage 1 -- fail-closed row 1, "IT RUNS BEFORE THE CHAIN ROW". Taking it
    inside :func:`resolve_povm` would take it AFTER the caller had already
    committed to forming that presentation's products and would tie it to a
    function whose subject is the emission.

    THREE READINGS THIS IMPLEMENTATION HAD TO FIX, BECAUSE THE TYPED INPUT
    CARRIES LESS THAN THE CLAIM'S FOUR-COMPONENT COMPARISON DOES, AND EACH IS
    THE REFUSING READING RATHER THAN THE PERMISSIVE ONE.

    1. (T) IS DECIDED IN THE ONE COMPONENT THE RECORD DECLARES. The claim reads
       (T) as the agreement "in block kind, in block identifiers, in their order
       and in their dimensions" of the maps THE CONDITIONAL FAMILIES THEMSELVES
       CARRY. A ``public_choices`` record declares one dense array per outcome
       and NO SECTOR MAP -- there is no block kind, no identifier and no order
       on the wire for any of them -- so three of the four components have no
       declared subject and the fourth, the dimension, is the whole of what is
       comparable. It is compared, across every conditional family of the
       presentation, and a disagreement REFUSES under (T) rather than reaching
       the arithmetic below with two shapes. On Alice's ``A`` the claim calls
       (T) empty; the dimension comparison is taken there too, because a
       presentation whose arrays have two shapes is not a block list against one
       map on either party's side.
    2. THE BLOCK COMPONENT OF THE KEY IS ``None``. The same absence: the record
       declares one undecomposed array per outcome, so the "per block" decision
       is taken on that one array and is recorded with no block identifier --
       inventing one from the emitted sector map would assert that the declared
       arrays are ITS blocks, which at a non-trivial receiver segment is false
       (the physical family "lives on the physical receiver space, which is not
       ``Q``").
    3. (H) AND (P) ARE KEYED PER (party, choice value) and carry the 1-based
       index of the outcome, in the order of item (1) above, at which they first
       failed. The ``gate_report`` row asks for "(H), (P), (C) and (S) per block
       and per choice value ... KEYED PER (SOURCE, PARTY, CHOICE VALUE t,
       BLOCK)", so the family and not the single ``N_{u|t}`` is the element, and
       the outcome index is what the row calls "the index at which a failed
       predicate failed".

    ``system_dim`` IS THE DECLARED DIMENSION OF THE SYSTEM THE PRESENTATION
    MEASURES -- ``d_A`` where it is Alice's, the physical receiver dimension
    where it is Bob's -- AND IS WHAT (C) IS COMPARED AGAINST. Definition
    ``def:exact`` (C) is ``Sigma = 1_{Q_s}``, the identity on the DECLARED
    system, and Definition ``def:weighted`` asks that ``{N_{u|t}}_u`` be "a POVM
    ON ``S``": a family whose arrays agree with one another but live on another
    space is a POVM on nothing this specification declares, and reading (C)
    against the arrays' own dimension would admit it. It is required rather than
    defaulted so that no caller can take the weaker reading by omission.

    WHICH PREDICATE NAMES THAT FAILURE IS (C) AND NOT (T), and the choice is
    the claim's order of predicates. (T) is stated as the agreement of the maps
    THE CONDITIONAL FAMILIES THEMSELVES CARRY -- one map per presentation,
    against which the weighted family is a block list -- and no comparison is
    made against a map this module holds, so
    widening (T) to reach ``system_dim`` would decide a comparison no claim
    states. (C) already names it: its right-hand side IS the identity on the
    declared system. So a uniformly wrong-dimension presentation passes (T),
    (H) and (P) -- of arrays that are Hermitian and positive semidefinite on
    their own space -- and is refused at (C), which is where the claim puts the
    comparison it fails.

    ``factor`` NAMES THE MEASURED FACTOR whose physical family this is, where
    the specification presents several (``def:spec`` (b')): two factors may carry the
    same party label, so the transcript key is prefixed ``<factor>:`` and the
    refusal names the factor as well as the party. ``None`` -- Alice's
    presentation, and the receiver's at one measured factor -- keeps the
    party prefix alone.
    """
    prefix = (
        _party_prefix(choices.party)
        if factor is None
        else f"{factor}:{_party_prefix(choices.party)}"
    )
    declarer = f"party {str(choices.party)!r}" + (
        "" if factor is None else f" at measured factor {factor!r}"
    )
    recorded: list[PredicateOutcome] = []

    def refusing(detail: str) -> ConditionalFamilyDecision:
        """Return the decision that stopped at the first failure."""
        return ConditionalFamilyDecision(
            refusal=Refusal(
                reason=RefusalReason.CONDITIONAL_FAMILY_NOT_ADMISSIBLE,
                detail=detail,
            ),
            predicates=tuple(recorded),
        )

    # --- (T): the maps the conditional families carry agree ----------------
    dims: list[tuple[Label, Label, int]] = []
    for choice in choices.choices:
        conditional = choices.conditional_elements[choice]
        for outcome in choices.conditional_alphabets[choice]:
            if outcome not in conditional:
                raise MalformedInputError(
                    f"no conditional matrix N_{{{outcome}|{choice}}}; the record "
                    "tabulates one operator per declared outcome"
                )
            dims.append((choice, outcome, dimension(conditional[outcome])))
    declared_dim = dims[0][2]
    disagreement = next(
        (
            (position, entry)
            for position, entry in enumerate(dims, start=1)
            if entry[2] != declared_dim
        ),
        None,
    )
    recorded.append(
        PredicateOutcome(
            source=PredicateSource.COMPILATION_MAP,
            predicate="(T)",
            element=f"{prefix}:{{N_(u|t)}}",
            block=None,
            outcome=disagreement is None,
            first_failure_index=None if disagreement is None else disagreement[0],
        )
    )
    if disagreement is not None:
        choice, outcome, dim = disagreement[1]
        return refusing(
            f"the conditional families declared by {declarer} "
            f"do not carry one map: N_{{{outcome}|{choice}}} is an operator of "
            f"dimension {dim} where the first declared conditional operator has "
            f"dimension {declared_dim}. Condition (T) of def:exact is decided "
            "and never measured, and it is read here on the map the conditional "
            "families themselves carry (def:weighted; rem:condfamily)"
        )

    # --- (H), (P), (C), (S), per choice value, first failure only ----------
    for choice in choices.choices:
        conditional = choices.conditional_elements[choice]
        order = conditional_family_order(choices, choice, arriving_order)
        family = f"{prefix}:{{N_(u|{choice})}}"
        hermitian_at: int | None = None
        for index, outcome in enumerate(order, start=1):
            if not is_hermitian(conditional[outcome]):
                hermitian_at = index
                break
        recorded.append(
            PredicateOutcome(
                source=PredicateSource.COMPILATION_MAP,
                predicate="(H)",
                element=family,
                block=None,
                outcome=hermitian_at is None,
                first_failure_index=hermitian_at,
            )
        )
        if hermitian_at is not None:
            return refusing(
                _conditional_detail(
                    declarer, choice, "(H)", order[hermitian_at - 1], hermitian_at
                )
                + " is not Hermitian"
            )
        positive_at: int | None = None
        for index, outcome in enumerate(order, start=1):
            if not is_positive_semidefinite(conditional[outcome]):
                positive_at = index
                break
        recorded.append(
            PredicateOutcome(
                source=PredicateSource.COMPILATION_MAP,
                predicate="(P)",
                element=family,
                block=None,
                outcome=positive_at is None,
                first_failure_index=positive_at,
            )
        )
        if positive_at is not None:
            return refusing(
                _conditional_detail(
                    declarer, choice, "(P)", order[positive_at - 1], positive_at
                )
                + " is not positive semidefinite"
            )
        # (C) IS READ ON THE COMPUTED TOTAL AND (S) ON THE ADDITIONS THAT FORMED
        # IT, exactly as check V3 reads the same pair on the emitted family:
        # "(C) alone says that the COMPUTED sum is the identity" (def:exact).
        verdict = sum_in_declared_order([conditional[outcome] for outcome in order])
        # THE RIGHT-HAND SIDE IS THE IDENTITY ON THE DECLARED SYSTEM, not on
        # whatever space the declared arrays happen to live on: def:exact (C)
        # is Sigma = 1_{Q_s} and def:weighted asks for a POVM ON S. `equal`
        # compares shapes first and answers False across a dimension mismatch,
        # so the sum of a uniformly wrong-dimension family is refused here.
        complete = verdict.computed_total_equals(identity(system_dim))
        recorded.append(
            PredicateOutcome(
                source=PredicateSource.COMPILATION_MAP,
                predicate="(C)",
                element=family,
                block=None,
                outcome=complete,
            )
        )
        if not complete:
            return refusing(
                f"the conditional family {{N_(u|{choice})}} declared by "
                f"{declarer} is not a measurement: its computed "
                f"completeness sum over U_{choice} is not the identity on the "
                f"declared {system_dim}-dimensional system (the declared "
                f"operators are {declared_dim}-dimensional), so condition (C) "
                "of def:exact fails on the one declared block, of the declared "
                "numbers and through no rounding. def:weighted decides each "
                "conditional family before it forms any product, and nothing "
                "here is rescaled, renormalised or repaired (ex:condfamily; "
                "rem:condfamily)"
            )
        recorded.append(
            PredicateOutcome(
                source=PredicateSource.COMPILATION_MAP,
                predicate=SUMMATION_PREDICATE,
                element=family,
                block=None,
                outcome=verdict.rounds_nowhere,
                first_failure_index=(
                    None if verdict.rounds_nowhere else verdict.first_inexact_index
                ),
                first_inexact_index=(
                    None if verdict.rounds_nowhere else verdict.first_inexact_index
                ),
            )
        )
        if not verdict.rounds_nowhere:
            return refusing(
                f"the completeness sum of the conditional family "
                f"{{N_(u|{choice})}} declared by {declarer} "
                f"ROUNDS: the first inexact addition is at element "
                f"{verdict.first_inexact_index} of the order condition (S) is "
                "read in -- the restriction, to the elements this choice value "
                "contributes, of the order on the alphabet that indexes the "
                f"weighted family, which here is {list(order)}. Condition (S) "
                "is on the ADDITIONS and not on the operands (def:exact)"
            )
    return ConditionalFamilyDecision(refusal=None, predicates=tuple(recorded))


def _conditional_detail(
    declarer: str,
    choice: Label,
    predicate: str,
    outcome: Label,
    index: int,
) -> str:
    """Return the opening of a refusal naming party (and factor), choice and index."""
    return (
        f"the conditional family {{N_(u|{choice})}} declared by "
        f"{declarer} is not exactly admissible: condition "
        f"{predicate} of def:exact fails on the one declared block at element "
        f"{index} of the decided order, where N_{{{outcome}|{choice}}}"
    )


@dataclass(frozen=True)
class EmissionDecision:
    """Definition ``def:weighted``'s decision on ``q_t N_{u|t}``, BEFORE emission.

    "The products ``q_t N_{u|t}`` are formed EXACTLY on the declared dyadic
    numbers. A product of two binary64 numbers NEED NOT BE ONE, so the compiler
    decides, BEFORE EMITTING ANYTHING, that every entry of every ``N_{u,t}`` is
    a binary64 number and that the emitted family satisfies Definition
    ``def:exact``." This record carries the representability decision, the
    weight-list decision it rests on, and the refusal the first failing one
    produces.

    THIS IS THE ONE EMISSION OBLIGATION THIS MODULE CARRIES, and the route it
    takes among spec/architecture.md 2.9's three is stated in the same
    definition: "THIS MODULE REFUSES, AND IT DECLARES NO ``k``." It does not
    round and it does not snap its own emission.
    """

    #: (S) on ``sum_t q_t``, accumulated "in the order the `public_choices`
    #: record lists T_pub in" -- an alphabet ``idx`` does not index, so the
    #: order is declared WITH THE RECORD and not through the index map. It is
    #: :func:`weighted_family`'s decision, carried here; a list failing it is
    #: refused with ``choice_weights_not_normalized`` (``req:weight-list``).
    weights_sum_rounds_nowhere: bool
    #: Every entry of every emitted ``N_{u,t}`` is a binary64 number. ``None``
    #: where the weight list was refused first and no product was decided.
    every_product_is_binary64: bool | None
    #: The first ``(joint label, flat entry index)`` whose exact product is not
    #: a binary64 number, or ``None``.
    first_unrepresentable: tuple[Label, int] | None
    refusal: Refusal | None
    #: THE PER-PREDICATE TRANSCRIPT of this emission decision, under the source
    #: ``compilation_map``: the row's last enumeration item is where a decision
    #: "taken in FILLING eq:declaration rather than in checking it is
    #: recorded". For the first form it carries :class:`WeightedFamily`'s own
    #: ``sum_t q_t = 1`` and condition (S) on that sum, then the
    #: representability of the products PER EMITTED LABEL; for the second form
    #: it carries the representability alone, the row sums of ``P`` and the
    #: support being decided in :func:`setting_weighted_family`.
    predicates: tuple[PredicateOutcome, ...] = ()


def decide_emission(family: WeightedFamily) -> EmissionDecision:
    """Decide Definition ``def:weighted``'s emission condition on a weighted family.

    THE WEIGHT LIST COMES FIRST. :func:`weighted_family` decided
    ``req:weight-list`` on the declared weights -- ``sum_t q_t = 1`` exactly,
    accumulated in the order the ``public_choices`` record lists ``T_pub`` in
    and rounding at no addition -- and recorded both legs in
    ``family.predicates``. Where it refused, this function returns that
    refusal, ``choice_weights_not_normalized``, with the transcript ending at
    the failed decision, and decides no product: the first failure is the one
    named, and nothing after it is decided. The ``summation_order`` convention
    fixes that order with the record rather than through ``idx``, and the sum
    is re-accumulated by no consumer, so this function does not accumulate it
    again.

    THEN THE PRODUCTS. Every entry of every ``q_t N_{u|t}`` must be a binary64
    number; the first label whose product is not is refused with
    ``emitted_value_not_representable``, naming that label and the flat entry
    index. The emitted family's own completeness sum is not decided here: check
    V3 decides it on the emitted family, in the emitted index order, under
    ``alice_povm_summation_rounds`` / ``bob_povm_summation_rounds``.
    """
    recorded: list[PredicateOutcome] = list(family.predicates)
    if family.refusal is not None:
        return EmissionDecision(
            weights_sum_rounds_nowhere=family.weights_sum_rounds_nowhere,
            every_product_is_binary64=None,
            first_unrepresentable=None,
            refusal=family.refusal,
            predicates=tuple(recorded),
        )

    prefix = _party_prefix(family.party)
    first: tuple[Label, int] | None = None
    for label in family.alphabet:
        element = family.elements[label]
        for i, row in enumerate(element):
            for j, entry in enumerate(row):
                if not scalar_is_binary64(entry):
                    first = (label, i * len(row) + j)
                    break
            if first is not None:
                break
        # THE DECISION IS RECORDED PER EMITTED LABEL, and the loop stops at the
        # first label that fails: the labels after it are not decided and carry
        # no entry. The index is the FLAT ENTRY INDEX inside that label's
        # matrix, which is the "entry index at which it FIRST failed" the row
        # asks for and the same number the refusal detail names.
        recorded.append(
            PredicateOutcome(
                source=PredicateSource.COMPILATION_MAP,
                predicate="every entry of the emitted N_(u,t) is a binary64 number",
                element=f"{prefix}:{label}",
                block=None,
                outcome=first is None,
                first_failure_index=None if first is None else first[1],
            )
        )
        if first is not None:
            break

    refusal: Refusal | None = None
    if first is not None:
        refusal = Refusal(
            reason=RefusalReason.EMITTED_VALUE_NOT_REPRESENTABLE,
            detail=(
                f"the exact product q_t N_{{u|t}} at outcome {first[0]!r}, flat "
                f"entry {first[1]}, is not a binary64 number; this module "
                "REFUSES rather than snapping its own emission (Definition "
                "def:weighted; spec/architecture.md 2.9), and it declares no k"
            ),
        )
    return EmissionDecision(
        weights_sum_rounds_nowhere=family.weights_sum_rounds_nowhere,
        every_product_is_binary64=first is None,
        first_unrepresentable=first,
        refusal=refusal,
        predicates=tuple(recorded),
    )


def choice_mass(
    family: WeightedFamily,
    choice: Label,
    state: Matrix,
    complementary_dim: int,
) -> Fraction:
    """Return ``sum_{u in U_t} tr[(1_R (x) N_{u,t}) omega]`` -- Eq. ``eq:choicemass``.

    Lemma ``lem:weighted`` (iii), in the party-neutral bipartite form the
    contract states: for a choice declared on Bob's side the operator is
    ``1_A (x) N_{u,t}`` and for one on Alice's side it is ``N_{u,t} (x) 1_Q``,
    with the factor order the ``subsystem_order`` convention declares -- ``A``
    first, always -- and the value insensitive to it because the trace is.

    ``complementary_dim`` is the dimension of the OTHER factor. The returned
    value equals the declared weight ``q_t`` for every state, which is the
    content of PC3 (ii); it is computed here rather than asserted so that a
    test can compare it against the declared weight.
    """
    complement = identity(complementary_dim)
    total = Cx(Fraction(0), Fraction(0))
    for label in family.members_of(choice):
        element = family.elements[label]
        joint = (
            kron(complement, element)
            if family.party is Party.BOB
            else kron(element, complement)
        )
        if dimension(joint) != dimension(state):
            raise HypothesisError(
                "the state and the joint operator live on different spaces; "
                "Lemma lem:weighted (iii) is stated on omega in S_=(R S)"
            )
        total = total + trace(matmul(joint, state))
    return real_part(total, f"the choice mass of {choice!r}")


def refuse_fixed_fraction(detail: str) -> Refusal:
    """Return the refusal of Theorem ``thm:choice-encoding`` (iv), with the VERBATIM reason.

    The reason string is the contract's own and is not this module's to spell.
    Nothing in the inputs table carries a field through which a ``fixed_fraction``
    request could arrive, and NO KEY IS ADDED HERE: this function exists for a
    caller that selects a test-statistics model out of band, so that the
    refusal named in the conventions has a code path even on the reading where the
    request is inexpressible in the typed input. Either way the verdict is the
    same and is not in doubt: NO DECLARATION IS EMITTED, and no artifact of
    this module ever carries a ``fixed_fraction`` test-statistics model.
    """  # noqa: E501
    return Refusal(reason=RefusalReason.FIXED_FRACTION_REQUESTED, detail=detail)


# ---------------------------------------------------------------------------
#  ROUTE C: the setting-dependent form, applied AFTER the chain
#
#  def:weighted's second construction, lem:weighted (i), (ii), (iv), thm:choice-encoding
#  (v)-(viii) and rem:relabel.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ChoiceWeighting:
    """The ``choice_weighting`` input record ``(F, t: V -> T, P(f | t))``.

    OPTIONAL, AND AT MOST ONE PER MEASURED FACTOR, whichever party's label the
    factor carries (``ReceiverPart.choice_weighting``). Absent is the
    ordinary case: with no such record the emitted family is the chain's
    ``{F_v}`` unchanged (``rem:relabel``, "What version 1 emits").

    THE RECORD HAS NO FIELD THROUGH WHICH AN OUTCOME-INDEXED WEIGHTING COULD
    ARRIVE, AND THAT IS THE REFUSAL ``choice_weight_depends_on_outcome``
    IMPLEMENTED AS A TYPE. ``matrix`` is keyed by ``(t, f)`` with ``t`` in the
    SETTING alphabet, never by ``v`` and never by a device outcome:
    ``def:weighted`` says ``P`` "is declared on ``T x F`` and reaches an
    outcome only through ``t(v)``". A caller that has such a weighting out of
    band gets :func:`refuse_outcome_dependent_weighting`, exactly as the
    fixed-fraction request gets :func:`refuse_fixed_fraction`.

    THE SETTING MAP IS DECLARED DATA AND IS READ, NOT DECIDED. Where the chain
    was emitted by ``reductions``, ``t`` IS that artefact's class map and is
    taken from it; where the family is declared directly it is declared with
    it, the singleton ``T = {*}`` being the case of no setting. What this
    module decides of ``t`` is that it is a TOTAL map ``V -> T``, which it does
    in :func:`setting_weighted_family` and which V1's totality clause decides
    again on the emitted tables.
    """

    #: ``F``, the choice alphabet, WITH ITS DECLARED ORDER. Finite, non-empty.
    choice_alphabet: tuple[Label, ...]
    #: ``T``, the setting alphabet. Finite, non-empty.
    setting_alphabet: tuple[Label, ...]
    #: ``t : V -> T``, total on the family's alphabet.
    setting_of: Mapping[Label, Label]
    #: ``P(f | t)``, keyed ``(t, f)``. Binary64 entries; zeros admitted.
    matrix: Mapping[tuple[Label, Label], Fraction]

    def __post_init__(self) -> None:
        """Refuse a presentation that tabulates no stochastic matrix at all."""
        if not self.choice_alphabet:
            raise MalformedInputError(
                "the choice alphabet is finite and NON-EMPTY (def:weighted)"
            )
        if len(set(self.choice_alphabet)) != len(self.choice_alphabet):
            raise MalformedInputError(
                "the choice alphabet enumerates a set; one value repeats"
            )
        if not self.setting_alphabet:
            raise MalformedInputError(
                "the setting alphabet is finite and NON-EMPTY (def:weighted)"
            )
        if len(set(self.setting_alphabet)) != len(self.setting_alphabet):
            raise MalformedInputError(
                "the setting alphabet enumerates a set; one value repeats"
            )

    def weight(self, setting: Label, choice: Label) -> Fraction:
        """Return ``P(choice | setting)``, refusing an untabulated cell."""
        try:
            return self.matrix[(setting, choice)]
        except KeyError as exc:
            raise MalformedInputError(
                f"P is not tabulated at (t, f) = ({setting!r}, {choice!r}); a "
                "stochastic matrix on T x F is tabulated at every cell"
            ) from exc


@dataclass(frozen=True)
class SettingWeightedFamily:
    """The emitted family of Eq. ``eq:weighted-t``, over the support ``V_P``.

    ``alphabet`` is ``V_P`` IN THE PRODUCT ORDER ``def:weighted`` fixes --
    "``v`` in the declared order of ``V`` and, within each ``v``, ``f`` in the
    declared order of ``F``, the pairs off the support omitted" -- and
    ``elements`` carries ``N_(v,f) = P(f | t(v)) F_v`` with the weight ALREADY
    INSIDE.

    ``pairs`` records which ``(v, f)`` each emitted label is, so that
    ``thm:choice-encoding`` (iii)'s "the choice value is recoverable from the outcome
    index alone" is a property of the record and not of a convention, and so that
    :func:`forget_choice` can sum over ``f`` at fixed ``v`` without parsing a
    label.
    """

    alphabet: tuple[Label, ...]
    elements: dict[Label, BlockOperator]
    pairs: dict[Label, tuple[Label, Label]]
    #: The family the chain delivered, unweighted, in its own declared order.
    source_alphabet: tuple[Label, ...]
    weighting: ChoiceWeighting
    #: THE PER-PREDICATE TRANSCRIPT of the second form's construction, under
    #: the source ``compilation_map`` and in the order the decisions were
    #: taken: each row sum of ``P`` with its (S) leg, then the support decision
    #: on each pair, then the representability of each emitted product. IT IS
    #: CARRIED ON THE CONSTRUCTED FAMILY AND NOT ON THE REFUSAL, because a
    #: refusal emits no declaration and therefore no ``gate_report``: the
    #: transcript of a refused route-C weighting reaches no consumer, and
    #: :func:`_decide_stochastic`'s own return value is what a test reads.
    predicates: tuple[PredicateOutcome, ...] = ()

    def ordered(self) -> tuple[BlockOperator, ...]:
        """Return the emitted operators in the emitted alphabet order."""
        return tuple(self.elements[label] for label in self.alphabet)

    def members_of_outcome(self, outcome: Label) -> tuple[Label, ...]:
        """Return the emitted labels belonging to one chain outcome ``v``."""
        return tuple(
            label for label in self.alphabet if self.pairs[label][0] == outcome
        )


def setting_joint_label(outcome: Label, choice: Label) -> Label:
    """Return the emitted label of one member of the support.

    A SPELLING AND NOT A STRUCTURE, exactly as :func:`_joint_label` is for the
    first form: the binding index is the one ``label_index_map`` assigns, and
    an instance that declares its own joint labels gets its own names over the
    same support.
    """
    return f"({outcome},{choice})"


@dataclass(frozen=True)
class _StochasticDecision:
    """Whether ``P`` is stochastic, and what deciding it recorded.

    A RECORD AND NOT A PAIR, for the reason
    :class:`~certiqs_key.protocol_compiler.chain._ConditionDecision` gives: two
    collections returned positionally are two collections a caller can unpack
    the wrong way round without the types objecting.
    """

    refusal: Refusal | None
    predicates: tuple[PredicateOutcome, ...] = ()


def _decide_stochastic(weighting: ChoiceWeighting) -> _StochasticDecision:
    """Decide ``P >= 0`` by sign and each row sum exactly, or return the refusal.

    THE ROW SUM IS ACCUMULATED IN THE DECLARED ORDER OF ``F`` and is required
    to round nowhere, which is condition (S) read on a row of scalars exactly
    as :func:`weighted_family` reads it on the weight list of the first form.
    Both legs refuse: the round-nowhere half is inside
    ``choice_weight_not_stochastic``'s condition ("or that sum rounds"), as it
    is inside ``choice_weights_not_normalized``'s for the first form
    (``req:weight-list``).

    THE ROW SUMS ARE DECIDED FOR EVERY ``t`` IN ``T``, including a setting no
    ``v`` realizes: ``P`` is declared on ``T x F``, and a row that is not a
    distribution is not a declared datum this module accepts, whether or not
    some outcome reaches it.

    WHAT THE TRANSCRIPT CARRIES OF THIS FUNCTION: the row sum per SETTING and
    its (S) leg, which is the row's "each row sum ``sum_f P(f | t) = 1``
    decided exactly in the declared order of ``F`` and required to round
    nowhere". The SIGN decision is not keyed and that is the row's own
    exclusion: its scope note leaves out "the domain condition ``q_t > 0`` on a
    declared weight, refused by its SIGN rather than measured, and likewise
    ``P(f | t) >= 0``". What the row DOES key is the support that the signs
    decide, and that is recorded where the support is formed, in
    :func:`setting_weighted_family`.
    """
    recorded: list[PredicateOutcome] = []
    for setting in weighting.setting_alphabet:
        running = Fraction(0)
        computed: Binary64Value = Fraction(0)
        row_first_inexact: int | None = None
        for position, choice in enumerate(weighting.choice_alphabet, start=1):
            weight = weighting.weight(setting, choice)
            if not is_binary64(weight):
                # THE DECLARED ENTRIES ARE BINARY64 NUMBERS, which is the
                # `choice_weighting` row's domain and not a decided
                # condition: a value that is not one is not a presentation of
                # an input this module types, so no clause of def:weighted can
                # be read against it and refusing it would have to invent a
                # reason. The three legs below -- sign, row sum, rounding --
                # are the conditions, and each has a reason.
                raise MalformedInputError(
                    f"P({choice!r} | {setting!r}) = {weight} is not a binary64 "
                    "number; def:weighted declares P with binary64 entries and "
                    "this module decides its conditions on declared numbers"
                )
            if weight < 0:
                return _StochasticDecision(
                    refusal=Refusal(
                        reason=RefusalReason.CHOICE_WEIGHT_NOT_STOCHASTIC,
                        detail=(
                            f"P({choice!r} | {setting!r}) = {weight} is negative; "
                            "def:weighted decides P >= 0 BY SIGN"
                        ),
                    ),
                    predicates=tuple(recorded),
                )
            if not is_binary64(running + weight):
                row_first_inexact = position
                recorded.append(
                    PredicateOutcome(
                        source=PredicateSource.COMPILATION_MAP,
                        predicate=SUMMATION_PREDICATE,
                        element=f"P( . | {setting})",
                        block=None,
                        outcome=False,
                        first_failure_index=row_first_inexact,
                        first_inexact_index=row_first_inexact,
                    )
                )
                return _StochasticDecision(
                    refusal=Refusal(
                        reason=RefusalReason.CHOICE_WEIGHT_NOT_STOCHASTIC,
                        detail=(
                            f"the row sum of P( . | {setting!r}), accumulated in "
                            f"the declared order of F, ROUNDS at {choice!r}; "
                            "def:weighted requires it to round nowhere"
                        ),
                    ),
                    predicates=tuple(recorded),
                )
            running += weight
            computed = round_to_binary64(computed + weight)
        # (S) HOLDS OF THIS ROW: every addition forming it was exact, which the
        # loop above decided one addition at a time and returned at the first
        # that was not. The equality is decided after them, and the transcript
        # is in that order.
        recorded.append(
            PredicateOutcome(
                source=PredicateSource.COMPILATION_MAP,
                predicate=SUMMATION_PREDICATE,
                element=f"P( . | {setting})",
                block=None,
                outcome=True,
            )
        )
        recorded.append(
            PredicateOutcome(
                source=PredicateSource.COMPILATION_MAP,
                predicate="sum_f P(f | t) = 1",
                element=f"P( . | {setting})",
                block=None,
                outcome=running == 1,
            )
        )
        if running != 1:
            return _StochasticDecision(
                refusal=Refusal(
                    reason=RefusalReason.CHOICE_WEIGHT_NOT_STOCHASTIC,
                    detail=(
                        f"the row sum of P( . | {setting!r}) is {running} and not "
                        f"exactly 1 (the computed binary64 total is {computed})"
                    ),
                ),
                predicates=tuple(recorded),
            )
    return _StochasticDecision(refusal=None, predicates=tuple(recorded))


def setting_weighted_family(
    alphabet: Sequence[Label],
    family: Mapping[Label, BlockOperator],
    weighting: ChoiceWeighting,
    joint_labels: Mapping[tuple[Label, Label], Label] | None = None,
) -> SettingWeightedFamily | Refusal:
    """Return Eq. ``eq:weighted-t``'s family over the support, or the refusal.

    ``alphabet`` is ``V`` in the DECLARED ORDER OF THE SUPPLIER -- the target
    alphabet of the last link of the receiver segment, whose order the compiler
    TAKES rather than choosing one (``def:compile``) -- and ``family`` is
    ``{F_v}`` as block lists against the emitted sector map.

    THREE DECISIONS ARE TAKEN HERE.

    1. ``t`` IS TOTAL ON ``V`` AND LANDS IN ``T``. A missing or out-of-range
       value is MALFORMED rather than refused: the map is not a map, and no
       clause of ``def:weighted`` can be read against it.
    2. ``P`` IS STOCHASTIC (:func:`_decide_stochastic`), with
       ``choice_weight_not_stochastic``.
    3. THE PRODUCTS ARE BINARY64 -- decided HERE, by
       :func:`decide_setting_emission`, AFTER the family is formed and BEFORE
       it is returned, with ``emitted_value_not_representable``. That is the
       same obligation ``def:weighted`` states of ``q_t N_{u|t}`` and
       states of ``P(f | t(v)) F_v`` as well.

    AND THE DECISION IS TAKEN ON THIS PATH RATHER THAN BESIDE IT, for the
    reason :func:`resolve_povm` gives at length for the first form: this
    function is the ONLY route from a weighting record to emitted matrices, so
    a :func:`decide_setting_emission` that merely EXISTED beside it would leave
    the obligation undischarged on every real compilation and the
    ``emitted_value_not_representable`` row unreachable through
    :func:`~certiqs_key.protocol_compiler.compile.compile_specification`.

    The support is decided by THE SIGN OF EACH ENTRY (Eq. ``eq:support``): a
    pair with ``P(f | t(v)) = 0`` is not an outcome, is not emitted and indexes
    nothing.
    """
    settings = set(weighting.setting_alphabet)
    for outcome in alphabet:
        if outcome not in weighting.setting_of:
            raise MalformedInputError(
                f"the declared setting map is not total: no t({outcome!r}). "
                "def:weighted asks for a TOTAL map V -> T"
            )
        if weighting.setting_of[outcome] not in settings:
            raise MalformedInputError(
                f"t({outcome!r}) = {weighting.setting_of[outcome]!r} is not in "
                "the declared setting alphabet"
            )
        if outcome not in family:
            raise MalformedInputError(f"no operator F_{outcome!r} in the family")

    stochastic = _decide_stochastic(weighting)
    if stochastic.refusal is not None:
        return stochastic.refusal
    recorded: list[PredicateOutcome] = list(stochastic.predicates)

    emitted: list[Label] = []
    elements: dict[Label, BlockOperator] = {}
    pairs: dict[Label, tuple[Label, Label]] = {}
    for outcome in alphabet:
        setting = weighting.setting_of[outcome]
        operator = family[outcome]
        for choice in weighting.choice_alphabet:
            weight = weighting.weight(setting, choice)
            # THE SUPPORT IS A DECISION AND IS RECORDED AS ONE, per pair: the
            # row keys "the support decided by the sign of each entry
            # (def:weighted, Eq. eq:support)". ITS OUTCOME IS MEMBERSHIP AND
            # NOT A VIOLATION -- ``False`` here records a pair OFF the support,
            # which "is not an outcome, is not emitted and indexes nothing" and
            # is no defect -- so it carries no first-failure index, there being
            # no failure to index.
            recorded.append(
                PredicateOutcome(
                    source=PredicateSource.COMPILATION_MAP,
                    predicate="(v, f) in V_P, by the sign of P(f | t(v))",
                    element=f"{_party_prefix(Party.BOB)}:({outcome},{choice})",
                    block=None,
                    outcome=weight > 0,
                )
            )
            if weight == 0:
                # eq:support: a zero-weight pair IS NOT AN OUTCOME. It is not
                # emitted and it indexes nothing, so every emitted element
                # carries a strictly positive weight.
                continue
            label = (
                setting_joint_label(outcome, choice)
                if joint_labels is None
                else joint_labels[(outcome, choice)]
            )
            if label in elements:
                raise MalformedInputError(
                    f"the support collides at {label!r}; V_P is indexed by "
                    "DISTINCT pairs (v, f)"
                )
            emitted.append(label)
            elements[label] = BlockOperator.of(
                operator.sector_map,
                [scale(weight, block) for block in operator.blocks],
            )
            pairs[label] = (outcome, choice)
    constructed = SettingWeightedFamily(
        alphabet=tuple(emitted),
        elements=elements,
        pairs=pairs,
        source_alphabet=tuple(alphabet),
        weighting=weighting,
    )
    decision = decide_setting_emission(constructed)
    if decision.refusal is not None:
        return decision.refusal
    # THE TRANSCRIPT IS ASSEMBLED ONTO THE FAMILY THAT IS RETURNED, in the
    # order the three groups of decisions were taken: the row sums of P, the
    # support, then the representability of the products. The family is rebuilt
    # rather than mutated because it is frozen, and nothing else about it
    # changes.
    return replace(
        constructed, predicates=tuple(recorded) + decision.predicates
    )


def decide_setting_emission(family: SettingWeightedFamily) -> EmissionDecision:
    """Decide ``def:weighted``'s representability condition on the products.

    "A product of two binary64 numbers need not be one, so the compiler
    decides, before emitting anything, that every entry of every ``N_(v,f)`` is
    a binary64 number." The same obligation, the same refusal string, and the
    same route among the three of spec/architecture.md 2.9: THIS MODULE
    REFUSES, AND IT DECLARES NO ``k``.

    THE WEIGHT-SUM LEG OF :class:`EmissionDecision` IS ``True`` HERE AND SAYS
    NOTHING, because for this form the row sums of ``P`` are decided -- AND
    REFUSED ON -- in :func:`_decide_stochastic` before any product is formed.
    The field is kept so that one record shape serves both constructions.
    """
    first: tuple[Label, int] | None = None
    recorded: list[PredicateOutcome] = []
    for label in family.alphabet:
        operator = family.elements[label]
        flat = 0
        for block in operator.blocks:
            for row in block:
                for entry in row:
                    if not scalar_is_binary64(entry):
                        first = (label, flat)
                        break
                    flat += 1
                if first is not None:
                    break
            if first is not None:
                break
        # PER EMITTED LABEL, stopping at the first that fails, exactly as
        # :func:`decide_emission` records the same obligation on the first
        # form. The flat index counts entries ACROSS THE BLOCKS of the emitted
        # block list, which is the index the refusal detail names.
        recorded.append(
            PredicateOutcome(
                source=PredicateSource.COMPILATION_MAP,
                predicate="every entry of the emitted N_(v,f) is a binary64 number",
                element=f"{_party_prefix(Party.BOB)}:{label}",
                block=None,
                outcome=first is None,
                first_failure_index=None if first is None else first[1],
            )
        )
        if first is not None:
            break

    refusal: Refusal | None = None
    if first is not None:
        refusal = Refusal(
            reason=RefusalReason.EMITTED_VALUE_NOT_REPRESENTABLE,
            detail=(
                f"the exact product P(f | t(v)) F_v at outcome {first[0]!r}, "
                f"flat entry {first[1]}, is not a binary64 number; this module "
                "REFUSES rather than snapping its own emission (def:weighted; "
                "spec/architecture.md 2.9), and it declares no k"
            ),
        )
    return EmissionDecision(
        weights_sum_rounds_nowhere=True,
        every_product_is_binary64=first is None,
        first_unrepresentable=first,
        refusal=refusal,
        predicates=tuple(recorded),
    )


def _sum_blocks(blocks: Sequence[Matrix]) -> Matrix:
    """Return the entrywise sum of same-shaped blocks, exactly."""
    total = blocks[0]
    for block in blocks[1:]:
        total = add(total, block)
    return total


def forget_choice(family: SettingWeightedFamily, outcome: Label) -> BlockOperator:
    """Return ``sum_f N_(v,f)`` -- Eq. ``eq:forgetf`` of ``lem:weighted`` (iv).

    "Forgetting the choice value returns the family the chain delivered", an
    EXACT OPERATOR IDENTITY: the omitted terms of the inner sum are exactly the
    zero entries of the row ``P( . | t(v))``, so the inner sum IS the row sum,
    which is one. It is computed here rather than asserted so that a test can
    compare it against ``F_v``.
    """
    members = family.members_of_outcome(outcome)
    if not members:
        raise HypothesisError(
            f"no emitted element carries the chain outcome {outcome!r}; "
            "eq:forgetf is stated for every v in V, and every v has at least "
            "one member because every row of P sums to one"
        )
    sector_map = family.elements[members[0]].sector_map
    block_lists = [family.elements[label].blocks for label in members]
    return BlockOperator.of(
        sector_map,
        [
            _sum_blocks([block_list[index] for block_list in block_lists])
            for index in range(sector_map.count)
        ],
    )


def choice_marginal(
    family: SettingWeightedFamily,
    choice: Label,
    state: Matrix,
) -> Fraction:
    """Return ``sum_v tr[N_(v,f) omega]`` -- Eq. ``eq:fmarginal``.

    ``lem:weighted`` (iv). THE VALUE MAY DEPEND ON THE STATE, and that is the
    point of computing it rather than asserting it: it "depends on ``omega``
    only through the SETTING MARGINAL", equals a state-independent ``q_f`` when
    ``P(f | t) = q_f`` for every ``t``, is state-independent as well when every
    class sum ``Pi_t`` is a multiple of the identity, "and otherwise is, in
    general, a function of the state".

    NO IDENTITY OF THE FORM ``eq:choicemass`` IS ASSERTED HERE and none may be
    read off this function: :func:`choice_mass` is ``lem:weighted`` (iii) and
    is stated of the setting-INDEPENDENT form and of it alone. What covers a
    state-dependent marginal downstream is ``reductions/ass:tsm`` (A-TSM),
    which this module names and does not use.
    """
    total = Cx(Fraction(0), Fraction(0))
    for label in family.alphabet:
        if family.pairs[label][1] != choice:
            continue
        operator = family.elements[label].dense()
        if dimension(operator) != dimension(state):
            raise HypothesisError(
                "the state and the emitted operator live on different spaces; "
                "eq:fmarginal is stated on omega in L(S)"
            )
        total = total + trace(matmul(operator, state))
    return real_part(total, f"the choice marginal of {choice!r}")


def refuse_outcome_dependent_weighting(detail: str) -> Refusal:
    """Return ``choice_weight_depends_on_outcome``, the type-level refusal.

    ``thm:choice-encoding`` (viii): "a weighting presented through anything but the
    setting map -- indexed by ``V``, by the device outcome, or by any component of
    ``v`` other than ``t(v)`` -- is refused with
    ``choice_weight_depends_on_outcome``". WITHIN THE TYPED INPUT SUCH A
    WEIGHTING IS INEXPRESSIBLE -- :class:`ChoiceWeighting` keys ``P`` by
    ``(t, f)`` and has no other route -- so this function exists for a caller
    that presents one out of band, exactly as :func:`refuse_fixed_fraction`
    does for the fixed-fraction request. NO INPUT KEY IS ADDED FOR IT, and
    adding one would be adding the very field the refusal exists to forbid.
    """
    return Refusal(
        reason=RefusalReason.CHOICE_WEIGHT_DEPENDS_ON_OUTCOME, detail=detail
    )
