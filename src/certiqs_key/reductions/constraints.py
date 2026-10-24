"""Constraint typing, certificates and the A-ATK licence of ``thm:licence``.

THE RECIPE, STATED ONCE
=======================
Corollary ``cor:pullback`` "is the recipe every constraint in this contract is
built by: pick an operator ``O^`` on ``Q``, compute its pull-back, and read off
what the physical device already guarantees about it". Everything in this file
is that recipe: :func:`classify_certificate` computes nothing about a device and
decides only which of Corollary ``cor:pullback``'s three cases the PULL-BACK
discharges, exactly.

THE CERTIFICATE IS DECIDED, NEVER TRUSTED
=========================================
A caller declaring a carried operator supplies ``(bowtie_k, c_k)`` and a claimed
certificate case, and neither is a certificate. Corollary ``cor:entries`` (iii)
emits a requested entry only on a DECIDED CERTIFICATE: a condition on the
emitted numbers and the request's declared constants, decided exactly from
them, that a claim stated for the instance proves sufficient for
Eq. ``eq:certificate``

    ``O_k = Lambda^dagger(O^_k) bowtie_k c_k 1_B``   as operators on ``H(B)``.

:func:`certify_carried_operators` recognises the three writings a claim gives
one for (a default carried operator, ``cor:entries`` (i); the class-marginal
entry, (ii); the two-sector entry of ``wpfss/cor:two-sector-decided``, on the
instance that claim is stated for) and decides that condition; every other
requested operator, and one whose condition fails, is
``constraint_without_certificate`` (``req:uncertified-operator-refused``): the
conventions block's ``fail_closed`` convention says "NO LICENCE IS EMITTED
WITHOUT ITS CERTIFICATE", and a certificate the module took on trust would be a
licence emitted without one.

EVERY CONSTRAINT THIS MODULE EMITS IS OF CASE (i)
=================================================
Corollary ``cor:transported`` closes with that sentence and it is a scope
statement, not a summary: "Case (i) carries the identity and inequality
certificates: they hold on EVERY reachable state whatever the adversary is
allowed to send ... Case (ii) is an assumption about the input and is sound only
for the ``S^ph`` it was assumed on; the artifact records which of the two a
given entry is. EVERY CONSTRAINT THIS MODULE EMITS IS OF CASE (i)." So
:class:`ConstraintEntry` carries a
:class:`~certiqs_key.reductions.reasons.CertificateKind` -- one of the three cases
WITHIN (i) -- and there is no representation for an assumed constraint at all.

WHAT THE LICENCE DOES NOT LICENSE
=================================
Remark ``rem:notlicensed`` (a)-(f) lists six things, each of which an
implementation could wrongly claim, and :class:`AttackSetLicence` claims none of
them. Transcribed because the list is what the record is bounded by:
(a) a TRUSTED MARGINAL -- "nothing here licenses declaring ``tau_A``"; (b)
CONSTRAINTS ON THE PURIFYING REGISTER -- "no constraint on Eve's side
information is expressible in this format or admitted by it"; (c)
DATA-DEPENDENT CONSTRAINTS -- refused; (d) JOINT MULTI-ROUND CONSTRAINTS --
"admissibility is PER ROUND ... no constraint on the joint ``n``-round state is
licensed or expressible"; (e) REUSE UNDER ANOTHER PROOF TECHNIQUE -- "the
artifact NAMES THE TECHNIQUE THE LICENCE WAS ISSUED FOR"; (f) ANYTHING ABOUT THE
DEVICE -- whether the receiver satisfies Eq. ``eq:certificate`` "is NOT PROVED
HERE AND CANNOT BE: it is Assumption A-RECV".

WHAT THE SUBMODULES HOLD, AND THE ONE GENERAL ENTRY BUILDER
===========================================================
There are two flag-state entry builders, ``fss_instance_entry`` and
the general :func:`restricted_entry`; a branching target has a branch structure
the first does not know about.

* ``fss_instance_entry`` and ``two_sector_entry`` are ``wpfss``'s: they are written
  against the transported cutoff pair ``(Pi_{<=N}, Pi_Flag)`` of the flat
  target, which is one squasher's construction. They live in
  :mod:`certiqs_key.reductions.wpfss.construction`.
* There is no entry builder of one branching model. Restricting the target
  element to one branch and subtracting that branch's flag projector is the
  register instance's entry rule, stated over a sector set rather than over
  one model's construction, and it is :func:`restricted_entry` below. Taking
  the whole target element instead would pull back to a sum over every
  branch, including the uncharacterised ones, about which nothing is assumed,
  and would not be the corollary's entry at all; that is about BRANCHES and
  not about any one model.

AT A ONE-BRANCH INSTANCE THE RESTRICTION IS THE IDENTITY, which is why the flat
and the branching entry coincide there: the branch IS the whole target and its
flag sectors ARE the flag sectors.

THE LICENCE IS A THEOREM WITH A NAMED HYPOTHESIS, NOT AN ATTESTATION
====================================================================
Remark ``rem:gateweight`` says why that matters and why the record names five
things rather than asserting one: the consuming gate "DEGENERATES: at
``d_A = 1`` every 1x1 Hermitian right-hand side is a multiple of ``tau_A``, and
in untrusted-source mode the entry type is scalar by construction, so IN BOTH
CASES PART (i) REJECTS NOTHING and the gate rests ENTIRELY on part (ii)" -- the
presence of this licence, "WHICH NO PROGRAM CAN VERIFY". So the record names the
theorem, the hypothesis it was discharged on PER ENTRY, PER ENTRY THE CLAIM THAT
DISCHARGES IT and, where that claim reads a supplier's fact, the supplier
artefact under A-RECV by version (``req:licence-record``), the source mode, and
the adjoint-form set; a consumer gating on presence is gating on something that
can be read back to its hypothesis.
"""

from __future__ import annotations

from collections.abc import Callable, Collection, Mapping, Sequence
from dataclasses import dataclass, replace
from enum import StrEnum
from fractions import Fraction
from typing import Final

from certiqs_key.foundations.exact import (
    Matrix,
    add,
    dimension,
    equal,
    identity,
    is_hermitian,
    is_square,
    lattice_floor,
    loewner_ge,
    on_lattice_scalar,
    scale,
    subtract,
    zeros,
)
from certiqs_key.reductions.errors import MalformedInputError
from certiqs_key.reductions.inputs import (
    CarriedOperatorRequest,
    ConstraintForm,
    JointOutcome,
    ProbeDeclaration,
)
from certiqs_key.reductions.reasons import (
    CertificateKind,
    FailClosedRule,
    Refusal,
    RefusalReason,
    Relation,
    SourceMode,
)
from certiqs_key.reductions.sectors import SectorSet

__all__ = [
    "CERTIFICATE_LOCATORS",
    "RECEIVER_FACT",
    "TWO_SECTOR_DECIDED_CLAIM",
    "WRITING_CLASS_MARGINAL",
    "WRITING_DEFAULT_CARRIED",
    "WRITING_TWO_SECTOR",
    "AttackSetLicence",
    "CertifiedEntry",
    "ConstraintEntry",
    "DeclaredForm",
    "EntryDischarge",
    "EntryTag",
    "EntryWriting",
    "PartyLocalLicence",
    "admissible_set_expression",
    "certificate_holds",
    "certify_carried_operators",
    "classify_certificate",
    "flag_sum_over_setting",
    "issue_licence",
    "party_local_entry",
    "party_local_scalar_set_expression",
    "party_local_set_expression",
    "probe_expectation_entry",
    "restricted_entry",
    "rounded_constant",
    "theta_typing",
]


class DeclaredForm(StrEnum):
    """The consuming contract's declared FORM, as a tag on an emitted entry.

    The outputs table, ``constraint_list``: "**THE FORM IS EMITTED WITH THE ENTRY**,
    as the tag value ``homogeneous`` IN TRUSTED-SOURCE MODE, because the
    consumer's part (i) security gate is a **TYPE** CHECK ON THE DECLARED TAG
    AND COMPARES NO NUMBERS (``meat-core`` 1.0.0 ``constraint_list`` input row,
    Rem. ``rem:cgate``): THE DOCKING IS BY KEY AND NOTHING ABOUT THE FORM IS
    INFERRED AT EITHER END."

    ONE MEMBER, AND THAT IS THE CONTRACT'S SHAPE. The outputs table names one tag
    value and names it for one mode. In untrusted-source mode the entry carries
    "THE SCALAR FORM, THE ONLY ONE THAT EXISTS THERE", for which the contract
    fixes no tag string, so the field is ``None`` there rather than carrying a
    string this module invented: emitting ``homogeneous`` in untrusted mode
    would assert a form the contract names only for trusted mode, and inventing
    a second string would put a value on the consumer's type gate that the
    consumer's own vocabulary does not contain. OPEN CHOICE, NARROWED AND NOT
    DECIDED -- the narrowest reading the contract's own sentences license.
    """

    HOMOGENEOUS = "homogeneous"


class EntryTag(StrEnum):
    """The reading an emitted entry is to be read in, as a tag (``cor:entries``).

    ONE MEMBER. ``cor:entries``, "The
    reading an emitted entry carries, as a tag": an entry is emitted UNTAGGED
    as ``(O^, bowtie, c)`` and read in the form of the declared source mode --
    which is :class:`DeclaredForm` and is a different field, the form of the
    right-hand side -- "or, where the measured system is a DECLARED product
    ``Q = (x)_f Q_f`` of party-scoped factors, it is emitted with the tag
    ``party_local`` and a SCOPE as ``(O^, bowtie, c; f)``".

    THE SCOPE IS NOT OPTIONAL WITH THE TAG: the tag names a reading whose
    subject is one factor's ``Q_f``, so a tag without a factor would name no
    operator inequality at all. :class:`ConstraintEntry` refuses the two apart.

    WHERE IT MAY BE EMITTED, and this is a rule and not a convention: only
    against a certificate discharged on THAT FACTOR'S OWN CHANNEL
    (``thm:licence`` (v)), "a certificate on the joint channel does not license
    it, and does not almost license it", ``lem:party-local`` (iv) exhibiting a
    channel that satisfies the scalar bound and violates the operator one. In
    this module the tag is emitted in ONE PLACE, the emission of several
    measuring parties (``thm:emitted-product`` (iii);
    :mod:`certiqs_key.reductions.factors`), and every entry of a one-factor
    emission is untagged and is what it was.
    """

    PARTY_LOCAL = "party_local"


@dataclass(frozen=True)
class ConstraintEntry:
    """One entry ``(O^_k, bowtie_k, c_k)`` of ``CList``, with its certificate.

    Definition ``def:licensed``: "In both cases the entries are written
    ``(O^_k, bowtie_k, c_k)``" -- and at 1.0.0 the outputs table fixes the third
    component's TYPE: "every one of which carries **A REAL SCALAR** ``c_k`` as
    its third component, **IN BOTH SOURCE MODES**". ``theta_typing`` records
    which typing the declared mode gives the right-hand side, in the contract's
    own words, so that a consumer reads the type from the artifact rather than
    re-deriving it.

    ``form`` is a SERIALIZED FIELD, not a property a
    consumer derives. See :class:`DeclaredForm`. "AN IMPLEMENTATION THAT OMITS
    IT HAS BROKEN A TYPE GATE ON THE CONSUMER'S SIDE THAT COMPARES NO NUMBERS
    AND THEREFORE CANNOT RECOVER FROM THE OMISSION."

    ``THIS MODULE EMITS NO OPERATOR Theta_k IN EITHER MODE``: "an entry
    carrying a Hermitian ``Theta_k`` is a ``general`` entry there, ADMISSIBLE
    INPUT BUT NEVER LICENSED, so a list containing one carries NO KEY-LENGTH
    CLAIM (Def. ``def:attset``)." The field is typed ``Fraction`` and there is
    no operator-valued alternative to construct.

    ``certified_against`` names the channel witness the certificate was
    discharged on; the fail-closed table refuses an entry certified against a channel
    that is not its own link's witness.

    ``constant_is_declared`` mirrors Assumption A-CONST. A ``False`` here is
    ``data_dependent_constant``; nothing infers the value.

    ``O^_k`` IS CARRIED AS ITS SECTOR-BLOCK LIST, one square block per sector in
    the sector map's order, exactly as ``target_povm`` and every transported
    operator are. It is an operator on ``Q`` like any other, and
    spec/architecture.md 2.8 admits one form for those -- "from construction to
    bundle, an operator is a list of sector blocks plus the sector map that
    names them ... no full ``d_Q x d_Q`` matrix is materialized on a live path"
    -- so the ``target_descriptor`` row's "NO FULL dim H(Q) x dim H(Q) ARRAY IS
    EMITTED, HERE OR ANYWHERE IN THIS ARTIFACT" is true of this list too. The
    direct sum is what the list MEANS and is no object this module builds.
    The one place a dense array still
    enters is a CALLER's declaration through ``carried_operators``, and only as
    INPUT: :func:`certify_carried_operators` splits it against the sector map
    once, refusing it where an off-sector entry would be truncated.
    """

    label: str
    #: ``O^_k`` as its sector-block list, in the declared sector order.
    operator: tuple[Matrix, ...]
    relation: Relation
    #: ``c_k``, A REAL SCALAR IN BOTH SOURCE MODES (the outputs table, 1.0.0).
    constant: Fraction
    certificate_kind: CertificateKind
    certified_against: str
    theta_typing: str
    constant_is_declared: bool = True
    #: The declared form, emitted WITH the entry. ``homogeneous`` in
    #: trusted-source mode; ``None`` in untrusted-source mode, where the
    #: contract names the scalar form and fixes no tag string for it.
    form: DeclaredForm | None = None
    #: The READING the entry is to be read in (``cor:entries``, the tag
    #: paragraphs). ``None`` -- UNTAGGED -- on every entry of a one-factor
    #: emission, which is every entry this repository emits today; see
    #: :class:`EntryTag`.
    tag: EntryTag | None = None
    #: THE SCOPE OF A ``party_local`` TAG: the label of the FACTOR ``f`` the
    #: entry is scoped to -- the factor's own label and NOT its party's, two
    #: factors being allowed to carry one party label -- the operator being an
    #: operator on THAT FACTOR'S ``Q_f`` alone and carried as a sector-block
    #: list against that factor's sector map. ``None`` exactly when :attr:`tag`
    #: is. The consuming interfaces type it the same way and decide it by "A
    #: COMPARISON OF A LABEL AGAINST THE FACTOR LIST"
    #: (``protocol-compiler``'s ``constraint_scope`` row and its
    #: ``constraint_scope_not_a_factor`` refusal; ``meat-core``'s
    #: ``constraint_scope_and_party_local_tag`` row).
    scope: str | None = None

    def __post_init__(self) -> None:
        """Refuse a tag without its scope, or a scope without its tag.

        A REFUSAL OF A MALFORMED RECORD AND NOT A FAIL-CLOSED ROW: no
        declaration reaches this, because the tag is emitted in one place
        (``thm:emitted-product`` (iii)) and never declared by a caller. What it
        catches is a producer that tagged an entry without saying which factor
        the operator lives on -- a tag that names a reading with no subject --
        or scoped one without saying it is to be read party-locally, which a
        consumer's type gate would then read as the untagged entry it is not.
        """
        if (self.tag is None) != (self.scope is None):
            raise MalformedInputError(
                "a party_local entry carries BOTH the tag and its factor scope "
                "(cor:entries: the entry is emitted as (O^, bowtie, c; f) with "
                "O^ an operator on that factor's Q_f alone); this entry carries "
                f"tag={self.tag!r} and scope={self.scope!r}"
            )


@dataclass(frozen=True)
class CertifiedEntry:
    """One caller-requested entry that survived certification, with its record.

    Three things travel together because the emitted artifact separates them:
    the entry goes into ``constraint_list``, the locator into the
    constraint-certificate row's detail ("Decided before this row, per entry"),
    and the rounding direction into ``emission_record``, which is where
    ``thm:emit`` (iv) says the direction of every rounded bound is recorded.

    ``rounding`` is ``None`` where the declared constant was already on the
    lattice and nothing was rounded -- the ordinary case, and one the record
    should not claim a direction for.
    """

    entry: ConstraintEntry
    #: THE CLAIM THAT DISCHARGES THE ENTRY'S CERTIFICATE, which the licence
    #: record names per entry (``req:licence-record``).
    locator: str
    rounding: str | None = None
    #: The writing in the form ``eq:instance-entry`` by which the entry was
    #: recognised, which the reference companion reads to form the entry's
    #: companion form (``reductions/cor:reference-companion`` (vi)).
    writing: EntryWriting | None = None
    #: Whether the discharging claim reads a fact a supplier's claims state
    #: (Assumption A-RECV), so that the licence names the supplier artefact for
    #: this entry (``req:licence-record``). ``False`` for a default carried
    #: operator, whose certificate is the positivity of ``Lambda^dagger`` alone.
    reads_supplier: bool = True


#: The three shapes of a requested entry this module recognises, by the
#: writing of ``eq:instance-entry`` it is recognised at.
WRITING_CLASS_MARGINAL: Final[str] = "class_marginal"
WRITING_TWO_SECTOR: Final[str] = "two_sector"
WRITING_DEFAULT_CARRIED: Final[str] = "default_carried"


@dataclass(frozen=True)
class EntryWriting:
    """A requested entry's writing in the form ``eq:instance-entry``.

    ``reductions/cor:reference-companion`` (vi): the companion form of an entry
    is formed at the writing by which the engine recognised it, and a writing
    need not be unique, so the recognition records the one it used.

    * ``class_marginal`` -- Remark ``rem:unsound``'s ``sum_y F_(y,t)`` at the
      setting ``setting``: coefficient ``1`` for every ``v`` of the class on
      every sector and ``Z = 0`` (``cor:entries`` (ii)).
    * ``two_sector`` -- Eq. ``eq:two-sector-entry``, ``F_e - a Pi_{<=N} - b Pi_Flag``:
      coefficient ``1`` for ``outcome`` on every sector of ``branch``, every
      other coefficient ``0``, and ``Z = -a Pi_{<=N} - b Pi_Flag`` with
      ``a = below`` read on ``data_part`` and ``b = above`` on ``flag_part``
      (``wpfss/cor:two-sector-decided``; ``wpfss/cor:flat-companion``).
    * ``default_carried`` -- a default carried operator of ``cor:entries``
      (i), a sum of sector projectors in the instance's transported set:
      every coefficient ``0`` and ``Z`` the operator itself, so its companion
      form is the operator (``cor:reference-companion`` (vi)).
    """

    kind: str
    setting: str | None = None
    outcome: JointOutcome | None = None
    below: Fraction = Fraction(0)
    above: Fraction = Fraction(0)
    branch: tuple[int, int] = (0, 0)
    data_part: tuple[int, int] = (0, 0)
    flag_part: tuple[int, int] = (0, 0)


def theta_typing(mode: SourceMode, constant: Fraction) -> str:
    """Return how Definition ``def:licensed`` types ``Theta_k`` in ``mode``.

    "``Theta_k = c_k tau_A`` with ``c_k in R`` in TRUSTED-SOURCE MODE, the
    state-level entry reading ``tr_Q[(1_A (x) O^_k) omega] bowtie_k c_k tau_A``;
    and ``Theta_k = c_k in R`` in UNTRUSTED-SOURCE MODE, the entry reading
    ``tr[(1_A (x) O^_k) omega] bowtie_k c_k`` -- A COMPARISON OF REAL NUMBERS."

    The string names ``tau_A`` and does not carry it: Theorem ``thm:licence``
    (iv) says "the identification of the right-hand side is THE DECLARATION'S
    AND NOT THIS CONTRACT'S", and Remark ``rem:notlicensed`` (a) adds that
    "nothing here licenses declaring ``tau_A``".
    """
    if mode is SourceMode.TRUSTED:
        return f"Theta = c tau_A with c = {constant} (def:licensed, trusted-source)"
    return f"Theta = c = {constant}, a real number (def:licensed, untrusted-source)"


def certificate_holds(pullback: Matrix, relation: Relation, constant: Fraction) -> bool:
    """Decide Eq. ``eq:certificate`` exactly: ``O bowtie c 1_B``.

    The Loewner comparisons are exact (:mod:`certiqs_key.foundations.exact`); a
    non-Hermitian pull-back raises rather than returning ``False``, because the
    order has no truth value there and a ``False`` would report a tested and
    failed certificate where none was tested.
    """
    if not is_hermitian(pullback):
        raise MalformedInputError(
            "Eq. eq:certificate compares Hermitian operators; a non-Hermitian "
            "pull-back is not a presentation of a carried operator"
        )
    scaled = scale(constant, identity(len(pullback)))
    if relation is Relation.GE:
        return loewner_ge(pullback, scaled)
    if relation is Relation.LE:
        return loewner_ge(scaled, pullback)
    return loewner_ge(pullback, scaled) and loewner_ge(scaled, pullback)


def classify_certificate(
    pullback: Matrix, relation: Relation, constant: Fraction
) -> CertificateKind | None:
    """Return which case of Corollary ``cor:pullback`` discharges the entry.

    (i) IDENTITY, when ``O_k = c 1_B`` exactly -- "``tr_Q[(O^_k (x) 1_R)sigma] =
    c sigma_R``; in particular ``tr[O^_k sigma] = c``".
    (ii) POSITIVITY, when ``O_k >= 0`` and the declared relation is ``>=`` with
    ``c = 0`` -- "``tr_Q[(O^_k (x) 1_R)sigma] >= 0``".
    (iii) SPECTRAL, when ``a 1 <= O_k <= b 1`` -- here, when the declared
    one-sided bound holds at a constant that is not the degenerate ``>= 0``.

    ``None`` means Eq. ``eq:certificate`` FAILS for the declared pair, which is
    ``constraint_without_certificate``. Note the order: the identity case is
    tested first because it is the strongest, and an entry that is an exact
    multiple of the identity is recorded as such rather than as a two-sided
    bound.
    """
    if not certificate_holds(pullback, relation, constant):
        return None
    scaled = scale(constant, identity(len(pullback)))
    if equal(pullback, scaled):
        return CertificateKind.IDENTITY
    if relation is Relation.GE and constant == 0:
        return CertificateKind.POSITIVITY
    return CertificateKind.SPECTRAL


def probe_expectation_entry(
    target_elements: Sequence[Sequence[Matrix]],
    probe_weight: Fraction,
    *,
    label: str,
    certified_against: str,
    mode: SourceMode,
) -> ConstraintEntry:
    """Remark ``rem:unsound``'s SOUND form: ``O^ = sum_y F_(y,t)``, ``=``, ``c = q_t``.

    THE EXPECTATION IDENTITY, NOT THE OPERATOR IDENTITY. The physical model
    satisfies ``sum_y M_(y,t) = q_t 1_B`` "because the weight ``q_t`` is Bob's
    own", and the pull-back of ``sum_y F_(y,t)`` is therefore ``q_t 1_B``
    exactly -- which is Corollary ``cor:pullback`` (i) and gives
    ``tr[(sum_y F_(y,t)) sigma] = q_t`` on every reachable ``sigma``.

    THE OPERATOR IDENTITY ON ``Q`` IS FALSE and is refused
    (``unsound_constraint_requested``): "the squashed operators generally satisfy
    only ``Lambda+(sum_y F_(y,t)) = q_t 1_B``, while ``sum_y F_(y,t) != q_t 1_Q``
    ON THE FLAG SECTOR of a flag-shaped target", and imposing it "would exclude
    reachable states and void Theorem ``thm:transfer``, which is A SECURITY BREAK
    RATHER THAN A RATE LOSS".

    The entry is NOT emitted by default on either route -- "adding an entry on
    the encoded route would force a licence there and contradict that route's
    definition" -- and "remains AVAILABLE ON REQUEST ... on the LICENSED route
    and under the licence that route requires". Its constant ``q_t`` is a
    declared protocol parameter, so Assumption A-CONST is satisfied.

    THE ELEMENTS ARRIVE AS THEIR SECTOR-BLOCK LISTS and the sum is taken BLOCK
    BY BLOCK, which is the same operator and builds no ``dim H(Q) x dim H(Q)``
    array.
    """
    if not target_elements:
        raise MalformedInputError("the sum is over a non-empty set of outcomes")
    accumulated = tuple(target_elements[0])
    for element in target_elements[1:]:
        accumulated = tuple(
            add(left, right) for left, right in zip(accumulated, element, strict=True)
        )
    return ConstraintEntry(
        label=label,
        operator=accumulated,
        relation=Relation.EQ,
        constant=probe_weight,
        certificate_kind=CertificateKind.IDENTITY,
        certified_against=certified_against,
        theta_typing=theta_typing(mode, probe_weight),
        form=DeclaredForm.HOMOGENEOUS if mode is SourceMode.TRUSTED else None,
    )


def restricted_entry(
    target_element: Sequence[Matrix],
    sectors: SectorSet,
    branch: tuple[int, int],
    flag: tuple[int, int],
    weight: Fraction,
    *,
    label: str,
    certified_against: str,
    mode: SourceMode,
    constant: Fraction = Fraction(0),
    form: DeclaredForm | None = None,
) -> ConstraintEntry:
    """Return an entry of Eq. ``eq:instance-entry``, restricted to ONE branch.

    ``O^ = F_o|_R - p_o Pi_F``, with ``R`` the branch's sector block and ``F``
    the branch's scalar sectors, ``bowtie = >=`` and ``c = 0``: the form
    ``def:reduction-instance`` (I4) states and ``cor:entries`` (iii) emits,
    with the branch's register element carried along by the register
    instance's entry rule (``cor:register-instance`` (ii)). WHAT DISCHARGES IT
    IS THE INSTANCE'S AND IS NAMED BY THE INSTANCE, not here: a flat
    instance's entry is ``wpfss/cor:fssinstance``'s and a branching instance's
    is ``cor:register-instance`` (ii)'s, and each builder supplies its own
    locator.

    TWO THINGS MAKE IT AN ENTRY OF THE BRANCH AND NOT OF THE TARGET. The target
    element is RESTRICTED TO THE BRANCH, and the projector subtracted is the
    BRANCH'S flag projector rather than the flag projector of the whole target.
    An entry built from the unrestricted element would pull back to a sum over
    every branch -- including ones about which nothing is assumed -- and would
    not be the instance's entry at all.

    NOTE WHAT IS NOT POSITIVE: ``O^`` itself. Its flag block has the entry
    ``-p_o`` at every outcome other than ``o``, so it is NOT a positive operator
    on ``Q``; what is positive is its PULL-BACK, "which is the whole content of
    the certificate" (Corollary ``cor:pullback`` (ii)). An implementation that
    tested positivity on ``Q`` would refuse the default entry.

    ``constant`` IS THE EMITTED ``c`` AND IT IS ALWAYS ``0`` HERE. Corollary
    ``cor:entries`` (i) gives the entry as ``(O^, >=, 0)`` with no condition and
    no alternative: NO CONSTANT IS SHIFTED, there being no declared operator
    tolerance to shift it by. The parameter is a surviving hook of that
    apparatus and is not reached: its only caller passes ``Fraction(0)``.

    THE TARGET ELEMENT ARRIVES AS ITS SECTOR-BLOCK LIST AND SO DOES THE ENTRY
    OPERATOR, which is the form the instance carries every operator on ``Q`` in
    (spec/architecture.md 2.8-2.9). Both summands are block-diagonal by construction --
    the element restricted to a run of whole sectors, and a multiple of a sum of
    sector projectors -- so the entry is built one block at a time and no
    ``dim H(Q) x dim H(Q)`` array is written anywhere on this path.

    Args:
        target_element: ``F_o`` as its sector-block list, in the sector order.
        sectors: the instance's sector set, which fixes every block's place.
        branch: ``(start, length)`` of the branch's sector block.
        flag: ``(start, length)`` of the branch's scalar sectors.
        weight: the certified weight ``p_o``.
        label: the entry's label.
        certified_against: the channel witness the certificate is discharged on.
        mode: the declared source mode, which types the right-hand side.
        constant: the emitted ``c``; see above.
        form: the declared form tag, or ``None`` to read it off the mode.
    """
    flag_projector = sectors.block_projector(*flag)
    operator = tuple(
        subtract(
            block if inside else zeros(dimension(block)),
            scale(weight, flag_block),
        )
        for block, inside, flag_block in zip(
            target_element,
            sectors.sectors_inside(*branch),
            flag_projector,
            strict=True,
        )
    )
    return ConstraintEntry(
        label=label,
        operator=operator,
        relation=Relation.GE,
        constant=constant,
        certificate_kind=CertificateKind.POSITIVITY,
        certified_against=certified_against,
        theta_typing=theta_typing(mode, constant),
        form=(
            form
            if form is not None
            else (DeclaredForm.HOMOGENEOUS if mode is SourceMode.TRUSTED else None)
        ),
    )


def rounded_constant(
    constant: Fraction, relation: Relation, lattice_exponent: int
) -> tuple[Fraction, str]:
    """Round a declared constant in the direction that ENLARGES the feasible set.

    Corollary ``cor:entries`` (iii): DOWN for ``>=``, UP for ``<=``. The
    equality case never reaches here -- it is REFUSED rather than split into a
    pair, "an equality having no loosening direction" -- and that refusal is
    :func:`_off_lattice_constant_refusal`, which runs first.

    Returns the constant and the direction taken. The rounding happens BEFORE
    the certificate is discharged ("it is FIRST rounded onto the lattice"), so
    what is certified and what is emitted are the same number; the direction
    "IS RECORDED PER ENTRY" and the record is ``emission_record``
    (``thm:emit`` (iv); spec/architecture.md 2.9, condition (D-DIR)).

    WHY THE ROUNDING IS SAFE, in the corollary's own words: at ``c <= c'`` for
    ``>=``, "``Lambda-dagger(O^) >= c' 1_B >= c 1_B``", so the entry survives at
    the rounded constant "while ``AttSet_CList`` ONLY GROWS --- WHICH IS THE
    SAFE DIRECTION, A SMALLER ADMISSIBLE SET BEING THE ONE IN WHICH Theorem
    ``thm:licence``'s INCLUSION CAN FAIL".

    THE RETURNED VALUE IS ALWAYS ON THE LATTICE, and that is why a constant of
    modulus above one does not reach here. Eq. ``eq:latinv`` has TWO conjuncts
    -- ``2^kappa c`` integral AND ``|c| <= 1`` -- and rounding onto the lattice
    repairs only the first: ``3/2`` is already an integer multiple of
    ``2^-kappa`` and no rounding moves it into the band. Such a constant is
    REFUSED by :func:`_off_lattice_constant_refusal`, under every relation and
    before this function is called; a
    call that reaches here with one is a programming error and raises, rather
    than returning a value off ``eq:latinv`` with a direction nothing moved in.

    THE EQUALITY CASE IS GUARDED IN THE SAME SHAPE AND FOR THE SAME REASON.
    Both of this function's impossible
    inputs are now enforced rather than one: an off-lattice equality has NO
    LOOSENING DIRECTION, so moving its constant produces a DIFFERENT constraint
    rather than a weaker one -- which is precisely why ``cor:entries`` (iii)
    refuses that case -- and returning a rounded value for it would be
    returning a constraint nobody declared, with a direction that means nothing
    for ``=``.
    """
    if abs(constant) > 1:
        raise MalformedInputError(
            f"the declared constant {constant} has modulus above one, which no "
            "rounding onto the lattice repairs (eq:latinv); the constant rule "
            "refuses it before this function is reached"
        )
    if relation is Relation.EQ and not on_lattice_scalar(constant, lattice_exponent):
        raise MalformedInputError(
            f"the declared constant {constant} is off the 2^-{lattice_exponent} "
            "lattice under the relation '=', which cor:entries (iii) REFUSES "
            "rather than rounding: an equality has no loosening direction, so "
            "a rounded equality is a different constraint and not a weaker "
            "one; the constant rule refuses it before this function is reached"
        )
    if on_lattice_scalar(constant, lattice_exponent):
        return constant, "unchanged: the declared constant is already on the lattice"
    if relation is Relation.GE:
        return (
            lattice_floor(constant, lattice_exponent),
            "down, cor:entries (iii): a lower c enlarges the feasible set for "
            ">= and AttSet_CList only grows",
        )
    return (
        -lattice_floor(-constant, lattice_exponent),
        "up, cor:entries (iii): a higher c enlarges the feasible set for <= "
        "and AttSet_CList only grows",
    )


def admissible_set_expression(
    entries: Sequence[ConstraintEntry], mode: SourceMode
) -> str:
    """Return the adjoint-form admissible set, in the consumer's own spelling.

    Eq. ``eq:attset`` (trusted-source mode) and Eq. ``eq:attsetun``
    (untrusted-source mode), quoted verbatim by Definition ``def:attset`` from
    ``meat-core`` 0.5.0 Def. ``def:roundmodel``. The two are distinguished BY THE
    OUTPUT SYSTEM NAMED IN THE ARGUMENT, which is why the string carries it:
    ``A_CList(E', Q E'')`` in trusted mode and ``A_CList(E', A Q E'')`` in
    untrusted mode, "with the constraint operator LIFTED to the larger supplied
    system, ``1_A (x) O^_k (x) 1_E''``, because in this mode ``A_j`` is an
    OUTPUT of the attack channel".

    The relation symbols are the OPERATOR spelling in both modes, which
    Definition ``def:attset``'s note on the relation symbols fixes: "the split in
    the consuming contract runs between two LEVELS, not between the two source
    modes ... this contract states operator conditions throughout and so uses the
    operator spelling, and everything it emits (``>=`` with ``c = 0``; ``=`` with
    ``c = q_t``) IS ADMITTED UNDER EITHER".
    """
    conditions = "; ".join(
        f"A+({'1_A (x) ' if mode is SourceMode.UNTRUSTED else ''}"
        f"{entry.label} (x) 1_E'') {entry.relation.value} {entry.constant} 1_E'"
        for entry in entries
    )
    if mode is SourceMode.TRUSTED:
        return (
            "A_CList(E', Q E'') = { A in CPTP(E', Q E'') : "
            f"{conditions} }} (eq:attset)"
        )
    return (
        "A_CList(E', A Q E'') = { A in CPTP(E', A Q E'') : "
        f"{conditions} }} (eq:attsetun)"
    )


def party_local_entry(
    entry: ConstraintEntry, factor: str, *, one_factor: bool
) -> ConstraintEntry:
    """Return the entry read party-locally, or -- at one factor -- the untagged one.

    THE TWO HALVES OF ``cor:entries``' TAG PARAGRAPHS, in one place.

    *Where the measured system is a declared product* the entry is emitted with
    the tag ``party_local`` and the SCOPE ``f``, at THE SAME OPERATOR, THE SAME
    RELATION AND THE SAME CONSTANT: "each entry scoped to its factor and
    carrying the same operator, the same relation and the same constant"
    (``thm:emitted-product`` (iii)). Nothing is re-derived and nothing is
    rounded; the certificate that licenses the reading is the one that factor's
    instance already discharged on that factor's own channel, which is what
    ``certified_against`` names and what the ``constraint_channel`` row decides.

    *At one factor the answer is THE UNTAGGED ENTRY AND NOT A REFUSAL*, which
    is the decision ``cor:entries`` writes down and the ``constraint_list``
    row's ``party_local_on_a_one_factor_emission`` repeats, and NO REASON
    STRING IS INVENTED FOR IT. The reason is case-independent: the untagged
    entry is IMPLIED by the party-local reading of the same triple -- in
    untrusted-source mode it is that reading's trace (``lem:party-local``
    (iii)), in trusted-source mode the same operator inequality under the
    marginal condition -- and is licensed on THE SAME certificate by
    ``thm:licence`` (i)-(iv). What it gives up is a RATE LOSS AND NEVER A
    SOUNDNESS LOSS, and only in untrusted-source mode at ``d_A > 1``, where the
    party-local reading is an operator inequality on ``A`` of which the emitted
    entry is the trace.
    """
    if one_factor:
        return entry
    return replace(entry, tag=EntryTag.PARTY_LOCAL, scope=factor)


def party_local_set_expression(
    entry: ConstraintEntry, factor: str, mode: SourceMode
) -> str:
    """Return the PARTY-LOCAL condition of ``def:attset``, Eq. ``eq:attsetpl``.

    The condition that cuts the admissible set out for ONE tagged entry, "in
    place of the scalar condition of eq:attset or eq:attsetun", with ``Q_{f^c}``
    the product of the other factors and ``R`` "``A`` in untrusted-source mode
    and trivial in trusted-source mode".

    IT IS A STRING AND DECIDES NOTHING, as every set expression of this module
    is: the licence NAMES the set the composed attacks are asserted to lie in,
    and what asserts the inclusion is ``thm:licence`` (v).
    """
    retained = "A " if mode is SourceMode.UNTRUSTED else ""
    return (
        f"(id_R' (x) A)+( X (x) ({entry.label} - {entry.constant} 1_Q_{factor}) "
        f"(x) 1_E'' ) {entry.relation.value} 0 for every finite-dimensional R' "
        f"and every X >= 0 on R' {retained}Q_{{{factor}^c}} (eq:attsetpl)"
    )


def party_local_scalar_set_expression(entry: ConstraintEntry, factor: str) -> str:
    """Return the SCALAR set the same tagged entry is also admissible in.

    ``def:attset``: "Taking ``R'`` trivial and ``X = 1`` in eq:attsetpl gives
    the scalar condition for the LIFTED operator ``1_{Q_{f^c}} (x) O^_k``, so
    the set with party-local entries is CONTAINED IN the set with the same
    entries read as scalars." The licence names both, so "a consumer that does
    not admit the party-local form may read it that way" at the SAME constant
    (``thm:licence`` (v); the ``constraint_list`` row's
    ``where_the_tag_is_emitted``).
    """
    return (
        f"the scalar condition for the lifted operator 1 (x) {entry.label} (x) 1 "
        f"at the same c = {entry.constant}, the factor being {factor} "
        "(def:attset, the sentence after eq:attsetpl)"
    )


@dataclass(frozen=True)
class PartyLocalLicence:
    """What the licence record names FOR ONE ``party_local`` ENTRY.

    ``interface.yaml``, ``attack_set_license.party_local_entries``: "PER ENTRY
    AND NEVER PER ARTEFACT. Where an entry is tagged ``party_local`` the record
    names, FOR THAT ENTRY: ``thm:licence`` (v) as the part that licenses it; THE
    FACTOR ``f`` AND THAT FACTOR'S CHANNEL WITNESS ``Lambda_f``; the certificate
    ``Lambda_f^dagger(O^_k) bowtie_k c_k 1_{B_f}`` DISCHARGED ON THAT FACTOR'S
    CHANNEL, with the supplier fact that discharges it (that factor's A-RECV and
    artefact version); the party-local admissible set of ``def:attset``,
    Eq. ``eq:attsetpl``, as the set the composed attacks are asserted to lie in;
    AND THE SCALAR SET THE SAME ENTRY IS ALSO ADMISSIBLE IN, for the lifted
    operator ``1 (x) O^_k (x) 1`` at the SAME ``c_k``."

    WHAT IS NOT NAMED IS A JOINT CHANNEL: there is none, the emission being
    factorised, "and a certificate against one would not license the tag
    anyway" (``lem:party-local`` (iv)).
    """

    entry_label: str
    #: THE FACTOR the entry is scoped to, by its factor LABEL: what the scope
    #: names and what a consumer compares against the emitted factor list
    #: (``protocol-compiler``'s ``constraint_scope`` row, "one factor label per
    #: entry").
    factor: str
    #: THE PARTY OF THAT FACTOR, carried BESIDE the factor label and never in
    #: place of it: "NOTHING REQUIRES TWO FACTORS TO CARRY DIFFERENT LABELS"
    #: (the ``factor_emission`` row), so two stations of one party are two
    #: factors of one party and only the factor label names one of them.
    party: str
    factor_channel_witness: str
    certificate: str
    discharging_receiver_fact: str | None
    factor_spec_version: str | None
    admissible_set: str
    also_admissible_as_a_scalar: str
    part: str = "Theorem thm:licence (v)"

    def as_machine_record(self) -> dict[str, object]:
        """Return this entry's party-local record, for the emitted licence."""
        return {
            "entry": self.entry_label,
            "part": self.part,
            "factor": self.factor,
            "party": self.party,
            "factor_channel_witness": self.factor_channel_witness,
            "certificate": self.certificate,
            "discharging_receiver_fact": self.discharging_receiver_fact,
            "factor_spec_version": self.factor_spec_version,
            "admissible_set": self.admissible_set,
            "also_admissible_as_a_scalar": self.also_admissible_as_a_scalar,
        }


#: The supplier fact a discharge reads where it reads one (Assumption A-RECV).
RECEIVER_FACT: Final[str] = (
    "Assumption A-RECV: the receiver artifact's claims are the device's"
)


@dataclass(frozen=True)
class EntryDischarge:
    """What discharges ONE entry's certificate: ``req:licence-record``, per entry.

    "Per entry, what discharges that hypothesis: the claim that establishes the
    certificate under Corollary ``cor:entries`` -- the instance's own claim for
    an entry of its list, that corollary for a default carried operator and for
    the class-marginal entry, the claim giving the decided certificate for a
    requested entry -- and, where that claim reads a fact a supplier's claims
    state, the supplier's artefact under Assumption A-RECV, named by its
    version."

    ``supplier_fact`` and ``supplier_version`` are BOTH ``None`` exactly where
    the claim reads no supplier fact (a default carried operator, whose
    certificate is the positivity of ``Lambda^dagger``; a branch-weight entry,
    decided on the declared register POVM), and both set otherwise.
    """

    entry: str
    claim: str
    supplier_fact: str | None = None
    supplier_version: str | None = None

    def __post_init__(self) -> None:
        """Refuse a supplier fact without its version, or the reverse."""
        if (self.supplier_fact is None) != (self.supplier_version is None):
            raise MalformedInputError(
                "a discharge that reads a supplier fact names the supplier "
                "artefact by version (req:licence-record); entry "
                f"{self.entry!r} carries fact={self.supplier_fact!r} and "
                f"version={self.supplier_version!r}"
            )

    def as_machine_record(self) -> dict[str, object]:
        """Return this entry's discharge, for the emitted licence."""
        return {
            "entry": self.entry,
            "claim": self.claim,
            "supplier_fact": self.supplier_fact,
            "supplier_version": self.supplier_version,
        }


@dataclass(frozen=True)
class AttackSetLicence:
    """The licence record, PRESENT EXACTLY WHEN ``CList`` is non-empty.

    It NAMES these things and asserts none of them about a device: the theorem
    (Theorem ``thm:licence``), the hypothesis it was discharged on
    (Eq. ``eq:certificate`` PER ENTRY), PER ENTRY what discharges it -- the
    claim and, where that claim reads a supplier's fact, the supplier artefact
    under Assumption A-RECV by version (:class:`EntryDischarge`;
    ``req:licence-record``) -- the source mode, and the adjoint-form set the
    composite attacks are asserted to lie in.

    ``discharging_receiver_fact`` and ``receiver_spec_version`` name the
    supplier fact and artefact ONCE for the record, and are ``None`` exactly
    where no entry's discharge reads one; every instance the engine builds
    today hands a receiver artefact, and every licence it emits has an entry
    whose discharge reads it.

    ``technique`` is item (e) of Remark ``rem:notlicensed``: a licence is "not
    automatically compatible with a postselection-based reduction", so "THE
    ARTIFACT NAMES THE TECHNIQUE THE LICENCE WAS ISSUED FOR". THE TECHNIQUE IS
    NAMED AT THE CONSUMER PIN THIS CONTRACT DECLARES, WHICH IS ``meat-core``
    1.0.0: sec:openitems states "THE CONSUMER PIN IS THE ACCEPTED 1.0.0", and
    ``def:roundmodel`` -- the technique this licence is issued for -- is quoted
    from `meat-core` 1.0.0 throughout (thm:licence's proof).
    Naming a superseded version here would name a technique no accepted
    contract carries, which is exactly what item (e) exists to prevent.
    """

    theorem: str
    hypothesis_per_entry: tuple[str, ...]
    #: Per entry, in the order of :attr:`hypothesis_per_entry`: what
    #: discharges that entry's certificate (``req:licence-record``).
    discharge_per_entry: tuple[EntryDischarge, ...]
    discharging_receiver_fact: str | None
    receiver_spec_version: str | None
    source_mode: SourceMode
    admissible_set: str
    technique: str = "MEAT: the squashed round model of meat-core 1.0.0 def:roundmodel"
    #: THE PARTY-LOCAL ROW, PER ENTRY AND NEVER PER ARTEFACT
    #: (:class:`PartyLocalLicence`). EMPTY on every licence this repository
    #: emits today, every entry of a one-factor emission being untagged, and
    #: the key is then ABSENT from the machine record rather than present and
    #: empty: a licence that names no party-local entry carries the record of
    #: one without the row, field for field.
    party_local_entries: tuple[PartyLocalLicence, ...] = ()

    def __post_init__(self) -> None:
        """Refuse a record whose entries are not each discharged.

        ``req:licence-record``: "it emits the record only when every entry has
        its certificate and what discharges it". The two per-entry lists are
        one entry each, in one order.
        """
        if len(self.discharge_per_entry) != len(self.hypothesis_per_entry):
            raise MalformedInputError(
                "the licence names, per entry, the certificate and what "
                "discharges it (req:licence-record); this record names "
                f"{len(self.hypothesis_per_entry)} certificate(s) and "
                f"{len(self.discharge_per_entry)} discharge(s)"
            )

    def discharge_statement(self) -> str:
        """Return what discharges each entry, in prose, for a licence statement.

        One clause per entry: the claim, and the supplier fact with the
        supplier artefact's version where the claim reads one
        (``req:licence-record``).
        """
        return "; ".join(
            f"{item.entry} by {item.claim}"
            + (
                ""
                if item.supplier_fact is None
                else f", reading {item.supplier_fact} ({item.supplier_version})"
            )
            for item in self.discharge_per_entry
        )

    def as_machine_record(self) -> dict[str, object]:
        """Return the licence as a machine record, for the emitted artifact.

        ``party_local_entries`` APPEARS EXACTLY WHERE THERE IS ONE. One licence
        record "may carry both readings and entries of both kinds"
        (``interface.yaml``, ``attack_set_license.party_local_entries``), so
        the key sits beside the rest rather than replacing anything; with no
        tagged entry there is nothing for it to name and the record is the one
        a one-factor emission has always carried.
        """
        record: dict[str, object] = {
            "theorem": self.theorem,
            "hypothesis_per_entry": list(self.hypothesis_per_entry),
            "discharge_per_entry": [
                item.as_machine_record() for item in self.discharge_per_entry
            ],
            "discharging_receiver_fact": self.discharging_receiver_fact,
            "receiver_spec_version": self.receiver_spec_version,
            "source_mode": str(self.source_mode),
            "admissible_set": self.admissible_set,
            "technique": self.technique,
        }
        if self.party_local_entries:
            record["party_local_entries"] = [
                item.as_machine_record() for item in self.party_local_entries
            ]
        return record


def issue_licence(
    entries: Sequence[ConstraintEntry],
    mode: SourceMode,
    receiver_spec_version: str,
    *,
    discharged_by: Mapping[str, str],
    supplier_free: Collection[str] = frozenset(),
) -> AttackSetLicence | None:
    """Return the licence for a non-empty entry list, or ``None`` for an empty one.

    THE PRESENCE RULE IS AN IFF and both directions are refusals with DIFFERENT
    reasons (``licence_missing``, ``licence_without_constraints``). This function
    is the only place a licence is built, so the two cannot come apart: an empty
    list returns ``None`` and cannot be given one.

    PER ENTRY, WHAT DISCHARGES IT (``req:licence-record``): ``discharged_by``
    maps every entry's label to the claim that establishes its certificate --
    the instance's own locator for an entry the instance built
    (``ReductionInstance.module_built_locators``), the locator the builder
    recorded for a requested one (``requested_locators``) -- and
    ``supplier_free`` names the entries whose claim reads no supplier fact.
    Every other entry's discharge names the supplier artefact by
    ``receiver_spec_version`` under A-RECV. "It emits the record only when every
    entry has its certificate and what discharges it": an entry with no
    discharging claim gets NO LICENCE, and the presence row then refuses the
    list ``licence_missing`` rather than a record being emitted that names
    nothing for it.
    """
    if not entries:
        return None
    if any(entry.label not in discharged_by for entry in entries):
        return None
    discharges = tuple(
        EntryDischarge(entry=entry.label, claim=discharged_by[entry.label])
        if entry.label in supplier_free
        else EntryDischarge(
            entry=entry.label,
            claim=discharged_by[entry.label],
            supplier_fact=RECEIVER_FACT,
            supplier_version=receiver_spec_version,
        )
        for entry in entries
    )
    reads_supplier = any(item.supplier_fact is not None for item in discharges)
    return AttackSetLicence(
        theorem="Theorem thm:licence (PR11)",
        hypothesis_per_entry=tuple(
            f"eq:certificate for {entry.label}: "
            f"Lambda+({entry.label}) {entry.relation.value} {entry.constant} 1_B"
            for entry in entries
        ),
        discharge_per_entry=discharges,
        discharging_receiver_fact=RECEIVER_FACT if reads_supplier else None,
        receiver_spec_version=receiver_spec_version if reads_supplier else None,
        source_mode=mode,
        admissible_set=admissible_set_expression(entries, mode),
    )


def flag_sum_over_setting(
    target_povm: Sequence[Matrix],
    joint_alphabet: Sequence[tuple[str, str]],
    setting: str,
) -> Matrix:
    """Return ``sum_y F_(y,t)`` for a fixed ``t``, in the declared order of ``V``.

    ON DENSE ELEMENTS, BECAUSE THE RESULT IS A DECLARED OPERATOR: this is how a
    caller builds the probe-expectation ``hat O`` of Remark ``rem:unsound``
    before declaring it through ``carried_operators``, and a declared operator
    on ``Q`` is one array. The EMITTED family is a list of sector blocks and is
    never this (spec/architecture.md 2.8-2.9).
    """
    selected = [
        element
        for element, outcome in zip(target_povm, joint_alphabet, strict=True)
        if outcome[1] == setting
    ]
    if not selected:
        raise MalformedInputError(f"no outcome carries the setting {setting}")
    accumulated = selected[0]
    for element in selected[1:]:
        accumulated = add(accumulated, element)
    return accumulated


#: THE CLAIM THAT DISCHARGES A CALLER-REQUESTED ENTRY, by the writing it was
#: recognised at: the decided certificates the ``carried_operators`` row's
#: ``certificate_rule`` lists for the instances this engine builds. Recorded
#: per entry in the verification report and named per entry by the licence
#: (``req:licence-record``). The identity instance's decided certificate
#: (``cor:emitted-identity``) has no entry here: no builder of this engine
#: emits that instance, so no request can reach it.
CERTIFICATE_LOCATORS: Final[Mapping[str, str]] = {
    WRITING_DEFAULT_CARRIED: (
        "cor:entries (i): a default carried operator Pi of the instance's "
        "transported set, Lambda+(Pi) >= 0 because Lambda+ is a positive map "
        "(def:reduction-instance), at c = 0 with >="
    ),
    WRITING_CLASS_MARGINAL: (
        "cor:entries (ii), the expectation form of rem:unsound: "
        "Lambda+(sum_y F_(y,t)) = q_t 1_B, discharged where the instance "
        "discharges the class-marginal identity eq:instance-classmarginal "
        "(def:reduction-instance (I4)) -- by lem:linear (ii) on a single-branch "
        "instance, and branch by branch on a branching one "
        "(cor:register-instance)"
    ),
    WRITING_TWO_SECTOR: (
        "wpfss/cor:two-sector-decided: eq:two-sector-pullback; the condition "
        "eq:two-sector-condition decided on the emitted preserved blocks and "
        "b <= p_e, p_e the certified weight of eq:certweights (imported under "
        "A-RECV)"
    ),
}

#: The claim stating the two-sector writing's decided certificate, for the one
#: instance it is stated for: the flat instance of ``wpfss/prop:flat-instance``
#: on the licensed route. The flat builder passes it to
#: :func:`certify_carried_operators`; a builder of another instance passes
#: ``None`` and the writing is refused there.
TWO_SECTOR_DECIDED_CLAIM: Final[str] = "reductions/wpfss/cor:two-sector-decided"


def _off_lattice_constant_refusal(
    requested: CarriedOperatorRequest, lattice_exponent: int
) -> Refusal | None:
    """Corollary ``cor:entries`` (iii): the REFUSAL half of the constant rule.

    "WHERE A DECLARED CONSTANT DOES NOT SATISFY Eq. eq:latinv IT IS FIRST
    ROUNDED ONTO THE LATTICE IN THE DIRECTION THAT ENLARGES THE FEASIBLE SET
    FOR ``bowtie`` --- DOWN FOR ``>=``, UP FOR ``<=`` --- and **AN EQUALITY
    ENTRY WHOSE CONSTANT IS OFF THE LATTICE IS REFUSED RATHER THAN SPLIT INTO A
    PAIR**, an equality having NO LOOSENING DIRECTION; the direction taken is
    recorded per entry."

    THIS FUNCTION DECIDES THE REFUSAL HALF AND RUNS FIRST. The rounding half is
    :func:`rounded_constant`, applied by :func:`certify_carried_operators` to
    the request before either certificate is attempted, so that the certificate
    is discharged at the constant the entry carries and not at the one the
    caller wrote.

    THERE ARE TWO REFUSING CASES, BECAUSE Eq. ``eq:latinv`` HAS TWO CONJUNCTS.

    * ``|c| > 1``, UNDER EVERY RELATION. The band is not a convenience: it "is
      what makes the value's significand fit in kappa bits and therefore what
      makes it exactly a binary64 number"
      (:func:`certiqs_key.foundations.exact.on_lattice_scalar`). NO ROUNDING ONTO
      THE LATTICE REPAIRS IT -- ``3/2`` is already an integer multiple of
      ``2^-kappa`` -- so rounding such a constant would move nothing, record a
      direction nothing was moved in, and emit an entry whose constant is not
      the "declared constant ON THE LATTICE" of
      ``def:reduction-instance`` (I4). It is refused instead, naming the band.
    * an EQUALITY entry whose constant is off the lattice, which is refused
      "RATHER THAN SPLIT INTO A PAIR".

    The band is decided first, so that the refusal a caller reads names the
    conjunct that cannot be repaired rather than the relation.
    """
    if on_lattice_scalar(requested.constant, lattice_exponent):
        return None
    if abs(requested.constant) > 1:
        return Refusal(
            reason=RefusalReason.CONSTRAINT_WITHOUT_CERTIFICATE,
            rule=str(FailClosedRule.CONSTRAINT_CERTIFICATE),
            detail=(
                f"carried operator {requested.label!r} declares the constant "
                f"c = {requested.constant}, whose modulus is above one; "
                "eq:latinv asks for 2^kappa c integral AND |c| <= 1, and NO "
                "ROUNDING ONTO THE LATTICE REPAIRS THE SECOND, so cor:entries "
                "(iii)'s rounding does not reach this case and the entry is "
                "refused rather than emitted off eq:latinv"
            ),
        )
    if requested.relation is Relation.EQ:
        return Refusal(
            reason=RefusalReason.CONSTRAINT_WITHOUT_CERTIFICATE,
            rule=str(FailClosedRule.CONSTRAINT_CERTIFICATE),
            detail=(
                f"carried operator {requested.label!r} is an EQUALITY entry "
                f"whose declared constant c = {requested.constant} is not on "
                f"the declared 2^-{lattice_exponent} lattice; cor:entries (iv) "
                "refuses it RATHER THAN SPLITTING IT INTO A PAIR, an equality "
                "having no loosening direction"
            ),
        )
    return None


def _blocks_equal(left: Sequence[Matrix], right: Sequence[Matrix]) -> bool:
    """Whether two sector-block lists are equal BLOCK BY BLOCK, exactly.

    The block-list spelling of :func:`certiqs_key.foundations.exact.equal` on the
    direct sums they mean: equal block counts and equal blocks. Both lists are
    read against the same sector map, so nothing outside the blocks exists to
    compare (spec/architecture.md 2.9).
    """
    return len(left) == len(right) and all(
        equal(one, other) for one, other in zip(left, right, strict=True)
    )


def _first_diagonal_entry(
    blocks: Sequence[Matrix], inside: Sequence[bool]
) -> Fraction:
    """Return the ``(0, 0)`` real entry of the first block the range covers.

    Eq. ``eq:two-sector-entry``'s two scalars ``a`` and ``b`` are read off ONE
    DIAGONAL ENTRY of the residual, the one at the start of the range, exactly
    as the ambient reading took ``residual[start][start]``: the range is a run
    of whole sectors (``SectorSet.sectors_inside``), so its first entry is the
    ``(0, 0)`` entry of its first block. ``0`` where the range covers no sector,
    which is the empty-data-part case the caller guards on ``data_length``.
    """
    for block, covered in zip(blocks, inside, strict=True):
        if covered:
            return block[0][0].re
    return Fraction(0)


def _declared_sector_blocks(
    requested: CarriedOperatorRequest, sectors: SectorSet
) -> tuple[Matrix, ...] | Refusal:
    """Split a CALLER's declared ``hat O`` against the sector map, or REFUSE it.

    THE ONE PLACE A DENSE ARRAY ENTERS THIS MODULE, AND ONLY AS INPUT. The
    ``carried_operators`` input row admits a requested operator in the form
    ``hat O = sum_v sum_s alpha_{v,s} Pi_s F_v Pi_s + Z`` with ``Z`` a real
    combination of sector projectors, "declared as one array"; every operator
    of that form is sector-block-diagonal, so splitting it against the sector
    map loses nothing and the entry travels in the one operator form
    spec/architecture.md 2.8-2.9 admits.

    AN ARRAY THAT IS NOT OF THAT FORM IS REFUSED RATHER THAN TRUNCATED. Reading
    the diagonal blocks of an operator with a nonzero off-sector entry would
    emit a DIFFERENT operator from the one declared, silently -- the truncation
    that is the latent risk of carrying
    an entry densely, and the case 2.9's reasoning says "cannot be constructed
    once a producer emits per sector". It can be declared, so it is decided
    here and refused, naming the row and the entry that would have moved. The
    refusal is the row's own (``constraint_without_certificate``, the fail-closed
    table's constraint-certificate rule): an operator outside the admitted form
    "is REFUSED ``constraint_without_certificate`` rather than emitted at any
    constant", and this is one such operator.
    """
    operator = requested.operator
    total = sectors.total_dimension
    if not is_square(operator) or len(operator) != total:
        return Refusal(
            reason=RefusalReason.CONSTRAINT_WITHOUT_CERTIFICATE,
            rule=str(FailClosedRule.CONSTRAINT_CERTIFICATE),
            detail=(
                f"carried operator {requested.label!r} is not a square array of "
                f"dimension dim H(Q) = {total}, the sector map's own dimension "
                "(def:reduction-instance (I2)), so it names no operator on Q "
                "and no certificate can be discharged for it"
            ),
        )
    offsets = sectors.offsets()
    sector_of = [
        position
        for position, (start, stop) in enumerate(offsets)
        for _ in range(start, stop)
    ]
    for i in range(total):
        for j in range(total):
            if sector_of[i] == sector_of[j] or operator[i][j].is_zero:
                continue
            return Refusal(
                reason=RefusalReason.CONSTRAINT_WITHOUT_CERTIFICATE,
                rule=str(FailClosedRule.CONSTRAINT_CERTIFICATE),
                detail=(
                    f"carried operator {requested.label!r} has the nonzero "
                    f"entry ({i}, {j}), which lies OUTSIDE THE SECTOR BLOCKS "
                    f"of the sector map: it couples sector "
                    f"{sectors.labels[sector_of[i]]!r} to sector "
                    f"{sectors.labels[sector_of[j]]!r}. The carried_operators "
                    "row admits the form sum_v sum_s alpha_{v,s} Pi_s F_v Pi_s "
                    "+ Z, every operator of which is sector-block-diagonal, "
                    "and an entry is carried as its SECTOR-BLOCK LIST like "
                    "every other operator on Q (the target_descriptor row: NO "
                    "FULL dim H(Q) x dim H(Q) ARRAY IS EMITTED, HERE OR "
                    "ANYWHERE IN THIS ARTIFACT). Reading the diagonal blocks "
                    "of this array would emit an operator the caller did not "
                    "declare, so it is refused rather than truncated"
                ),
            )
    return tuple(
        tuple(
            tuple(operator[i][j] for j in range(start, stop))
            for i in range(start, stop)
        )
        for start, stop in offsets
    )


def _probe_expectation_certificate(
    requested: CarriedOperatorRequest,
    declared_blocks: tuple[Matrix, ...],
    *,
    source_mode: SourceMode,
    probe: ProbeDeclaration,
    target_povm: Sequence[Sequence[Matrix]],
    order: Sequence[JointOutcome],
    extra_hypothesis: Callable[[], str | None] | None,
) -> tuple[tuple[ConstraintEntry, str, EntryWriting], ...] | Refusal | None:
    """Remark ``rem:unsound``'s SOUND entry, recognised and certified from data.

    ``O^ = sum_y F_(y,t)``, ``bowtie = =``, ``c = q_t``. Eq. ``eq:certificate``
    asks for ``Lambda^dagger(O^) = q_t 1_B``. On a SINGLE-BRANCH instance that
    is a theorem: ``sum_y M_{(y,t)} = q_t 1`` is Lemma ``lem:linear`` (ii)'s
    completeness computation, a statement about the conditional families the
    receiver artifact supplies.

    ON A BRANCHING INSTANCE THE PULL-BACK IS NOT ONE IDENTITY BUT A SUM OVER
    BRANCHES, ``sum_b (sum_y M_{(y,t)|b}) (x) N_b``, and the summands are not
    alike: a branch whose POVM is arbitrary -- "possibly unknown, possibly
    chosen by the adversary" -- makes ``sum_y M_{(y,t)|b} = q_t 1`` no theorem
    at all. ``extra_hypothesis`` IS WHERE SUCH AN INSTANCE PUTS THE CONDITION:
    it returns ``None`` when every branch carries the probe weight and
    otherwise the prose naming what failed, and the entry is then REFUSED
    ``constraint_without_certificate``. Emitting it without that would be a
    licence without its certificate, and the constraint would exclude states
    reachable through such a branch -- "A SECURITY BREAK RATHER THAN A RATE
    LOSS".

    ONE ENTRY IS EMITTED AND NOT A PAIR. Corollary ``cor:entries`` (ii) gives
    the single equality entry ``(O^, =, q_t)`` with the declared ``q_t`` as its
    constant; there is no tolerance ``delta_t`` that would widen it to a
    ``(q_t -/+ delta_t)`` pair.

    RECOGNITION IS EXACT: the requested operator must EQUAL ``sum_y F_(y,t)``
    for a declared setting, entry for entry, and the declared constant must
    equal that setting's ``q_t``. Nothing is inferred from a label.

    ``target_povm`` IS THE EMITTED FAMILY AS SECTOR-BLOCK LISTS and
    ``declared_blocks`` is the caller's array split against the same sector map
    by :func:`_declared_sector_blocks`, so the comparison is block by block and
    no ``dim H(Q) x dim H(Q)`` array is built to make it.
    """
    if requested.relation is not Relation.EQ:
        return None
    for setting in probe.settings:
        selected = [
            tuple(target_povm[index])
            for index, outcome in enumerate(order)
            if outcome[1] == setting
        ]
        if not selected:
            continue
        accumulated = selected[0]
        for element in selected[1:]:
            accumulated = tuple(
                add(left, right)
                for left, right in zip(accumulated, element, strict=True)
            )
        if not _blocks_equal(declared_blocks, accumulated):
            continue
        if requested.constant != probe.weights[setting]:
            return None
        undischarged = None if extra_hypothesis is None else extra_hypothesis()
        if undischarged is not None:
            return Refusal(
                reason=RefusalReason.CONSTRAINT_WITHOUT_CERTIFICATE,
                rule=str(FailClosedRule.CONSTRAINT_CERTIFICATE),
                detail=(
                    f"carried operator {requested.label!r} is the probe "
                    "expectation entry of rem:unsound, whose certificate "
                    "Lambda+(sum_y F_(y,t)) = q_t 1_B is a theorem only where "
                    "EVERY branch carries the probe weight; " + undischarged
                ),
            )
        return (
            (
                ConstraintEntry(
                    label=requested.label,
                    operator=declared_blocks,
                    relation=Relation.EQ,
                    constant=requested.constant,
                    certificate_kind=CertificateKind.IDENTITY,
                    certified_against=requested.certified_against,
                    theta_typing=theta_typing(source_mode, requested.constant),
                    constant_is_declared=requested.constant_is_declared,
                    form=(
                        DeclaredForm.HOMOGENEOUS
                        if source_mode is SourceMode.TRUSTED
                        else None
                    ),
                ),
                CERTIFICATE_LOCATORS[WRITING_CLASS_MARGINAL],
                EntryWriting(kind=WRITING_CLASS_MARGINAL, setting=setting),
            ),
        )
    return None


def _default_carried_certificate(
    requested: CarriedOperatorRequest,
    declared_blocks: tuple[Matrix, ...],
    *,
    source_mode: SourceMode,
    default_carried: Sequence[tuple[str, Sequence[Matrix]]],
) -> tuple[ConstraintEntry, str, EntryWriting] | None:
    """``cor:entries`` (i): a default carried operator requested AS AN ENTRY.

    "Every operator of the instance's default carried set -- every sector
    projector ``Pi_s`` ... together with the sums of sector projectors that
    instance transports besides -- is emitted at ``c = 0`` with ``>=`` ... and
    it becomes an entry of ``CList`` only where a caller requests it as an
    entry." Its certificate ``Lambda^dagger(Pi) >= 0`` (Eq.
    ``eq:entrysector``) holds for every instance, ``Lambda^dagger`` being a
    positive map, so the decided certificate is the recognition itself: the
    declared operator EQUALS, block by block, an operator of the instance's
    transported set (``default_carried``, which (I3) makes contain every sector
    projector and the sums the instance transports), every block of it is the
    identity or zero (a sum of distinct sector projectors, entries ``0`` and
    ``1``, on the lattice at every ``kappa``), and the request is ``>=`` at
    ``c = 0``. A projector at another relation or another constant is not this
    entry and falls through to the other writings, and then to the refusal.

    THE DISCHARGE READS NO SUPPLIER FACT: positivity of the adjoint is a
    property of the channel alone, so the licence names this corollary for the
    entry and no receiver artefact (``req:licence-record``).
    """
    if requested.relation is not Relation.GE or requested.constant != 0:
        return None
    if not all(
        equal(block, identity(dimension(block)))
        or equal(block, zeros(dimension(block)))
        for block in declared_blocks
    ):
        return None
    for label, carried in default_carried:
        if not _blocks_equal(declared_blocks, carried):
            continue
        entry = ConstraintEntry(
            label=requested.label,
            operator=declared_blocks,
            relation=Relation.GE,
            constant=Fraction(0),
            certificate_kind=CertificateKind.POSITIVITY,
            certified_against=requested.certified_against,
            theta_typing=theta_typing(source_mode, Fraction(0)),
            constant_is_declared=requested.constant_is_declared,
            form=(
                DeclaredForm.HOMOGENEOUS if source_mode is SourceMode.TRUSTED else None
            ),
        )
        locator = (
            CERTIFICATE_LOCATORS[WRITING_DEFAULT_CARRIED]
            + f"; the transported operator {label}"
        )
        return (entry, locator, EntryWriting(kind=WRITING_DEFAULT_CARRIED))
    return None


def _two_sector_certificate(
    requested: CarriedOperatorRequest,
    declared_blocks: tuple[Matrix, ...],
    *,
    source_mode: SourceMode,
    target_povm: Sequence[Sequence[Matrix]],
    order: Sequence[JointOutcome],
    sectors: SectorSet,
    branch: tuple[int, int],
    data_part: tuple[int, int],
    flag_part: tuple[int, int],
    weights: Mapping[JointOutcome, Fraction],
    claim: str | None,
    missing_claim: str,
) -> tuple[ConstraintEntry, str, EntryWriting] | Refusal | None:
    """Eq. ``eq:two-sector-entry``, recognised and its decided certificate decided.

    ``O^ = F^FSS_e - a Pi_{<=N} - b Pi_Flag`` with ``bowtie = >=`` and
    ``c = 0``, whose pull-back is ``wpfss/cor:two-sector-decided`` (i),
    Eq. ``eq:two-sector-pullback``:
    ``(+)_{m<=N} (A'^(m)_e - a 1) (+) (blk M^{>N}_e - b 1)``.

    Returns ``None`` where the declared operator is not of this writing (the
    caller then refuses it as an operator no claim gives a decided certificate
    for), the entry with its locator and writing where the decided certificate
    holds, and a REFUSAL where the operator IS of this writing and either no
    claim stated for the instance gives its decided certificate (``claim`` is
    ``None``) or the certificate fails at the emitted numbers
    (``req:uncertified-operator-refused``). A refusal names which, so that a
    caller reading it learns whether the constants or the instance were the
    reason.

    ``a`` AND ``b`` ARE RECOVERED FROM THE DECLARED OPERATOR, not taken on
    trust, and Eq. ``eq:two-sector-condition`` is decided on the emitted
    numbers, exactly (``wpfss/cor:two-sector-decided`` (ii)-(iii)):

    * ``A'^(m)_e - a 1 >= 0`` on every EMITTED data block of the branch, by the
      exact Loewner test (``lem:exactpsd``), which (iii) shows NECESSARY as
      well;
    * ``b <= p_e``, one comparison of rationals, which with
      Eq. ``eq:certweights`` gives ``blk M^{>N}_e >= p_e 1 >= b 1`` for the
      certified weight -- the supplier's claim, imported under Assumption
      A-RECV, which this module never verifies (its ``verification`` field is
      ``never``).

    Remark ``rem:published`` defines ``a`` and ``b`` as minimum eigenvalues, but
    what makes the entry admissible is the decided certificate holding, not
    their being minimal: a caller declaring smaller values gets a weaker but
    equally certified entry, and one declaring larger values gets
    ``constraint_without_certificate``.

    WHAT MAY NEVER BE EMITTED, and is not: the CAP form
    ``W <= (p(e) - a)/(b - a)``, which "contains the run's OBSERVED ``p(e)``"
    and which Assumption A-CONST excludes. Nothing here forms one.

    THE CONSTANT IS ``0`` AND NO CONSTANT IS SHIFTED: "UNDER EXACT
    ADMISSIBILITY THERE IS NO SUCH DISPLACEMENT". ``a`` and ``b`` do not shift
    either: they "are DECLARED DEVICE CONSTANTS -- statements about the
    PHYSICAL receiver -- and NOT quantities recomputed from the declaration".

    ``target_povm`` IS THE EMITTED FAMILY AS SECTOR-BLOCK LISTS and
    ``declared_blocks`` the caller's array split against the same sector map,
    so every step here -- the restriction to the branch, the two recovered
    scalars, the rebuilt operator and the two halves of the condition -- is
    taken BLOCK BY BLOCK. The below-cutoff half is decided per data block
    rather than on the direct sum, which is the same decision: a
    block-diagonal operator is ``>= a 1`` exactly when each of its blocks is.
    The first outcome at which the declared operator is of this writing decides
    the request.
    """
    if requested.relation is not Relation.GE or requested.constant != 0:
        return None
    leq = sectors.block_projector(*data_part)
    flag = sectors.block_projector(*flag_part)
    in_branch = sectors.sectors_inside(*branch)
    in_data = sectors.sectors_inside(*data_part)
    in_flag = sectors.sectors_inside(*flag_part)
    _, data_length = data_part
    for index, outcome in enumerate(order):
        element = tuple(
            block if inside else zeros(dimension(block))
            for block, inside in zip(target_povm[index], in_branch, strict=True)
        )
        residual = tuple(
            subtract(block, declared)
            for block, declared in zip(element, declared_blocks, strict=True)
        )
        below = _first_diagonal_entry(residual, in_data)
        above = _first_diagonal_entry(residual, in_flag)
        rebuilt = tuple(
            subtract(
                subtract(block, scale(below, leq_block)), scale(above, flag_block)
            )
            for block, leq_block, flag_block in zip(element, leq, flag, strict=True)
        )
        if not _blocks_equal(rebuilt, declared_blocks):
            continue
        if claim is None:
            return Refusal(
                reason=RefusalReason.CONSTRAINT_WITHOUT_CERTIFICATE,
                rule=str(FailClosedRule.CONSTRAINT_CERTIFICATE),
                detail=(
                    f"carried operator {requested.label!r} is the two-sector "
                    "entry eq:two-sector-entry, and no claim stated for this "
                    "instance gives a decided certificate for it (cor:entries "
                    "(iii); req:uncertified-operator-refused): "
                    f"{TWO_SECTOR_DECIDED_CLAIM} is stated for the flat "
                    "instance of wpfss/prop:flat-instance alone"
                    + (f"; {missing_claim}" if missing_claim else "")
                ),
            )
        if data_length and not all(
            loewner_ge(block, scale(below, identity(dimension(block))))
            for block, inside in zip(target_povm[index], in_data, strict=True)
            if inside
        ):
            return Refusal(
                reason=RefusalReason.CONSTRAINT_WITHOUT_CERTIFICATE,
                rule=str(FailClosedRule.CONSTRAINT_CERTIFICATE),
                detail=(
                    f"carried operator {requested.label!r} is the two-sector "
                    f"entry eq:two-sector-entry at a = {below}, b = {above}, "
                    "and its decided certificate fails at the emitted numbers: "
                    "some emitted block below the cutoff of its outcome does "
                    f"not clear a = {below} ({claim} (ii), the first condition "
                    "of eq:two-sector-condition, which its part (iii) shows "
                    "necessary)"
                ),
            )
        if above > weights[outcome]:
            return Refusal(
                reason=RefusalReason.CONSTRAINT_WITHOUT_CERTIFICATE,
                rule=str(FailClosedRule.CONSTRAINT_CERTIFICATE),
                detail=(
                    f"carried operator {requested.label!r} is the two-sector "
                    f"entry eq:two-sector-entry at a = {below}, b = {above}, "
                    "and its decided certificate fails at the emitted numbers: "
                    f"b = {above} exceeds the certified weight "
                    f"p_e = {weights[outcome]} of its outcome ({claim} (ii), "
                    "the second condition of eq:two-sector-condition)"
                ),
            )
        entry = ConstraintEntry(
            label=requested.label,
            operator=declared_blocks,
            relation=Relation.GE,
            constant=Fraction(0),
            certificate_kind=CertificateKind.POSITIVITY,
            certified_against=requested.certified_against,
            theta_typing=theta_typing(source_mode, Fraction(0)),
            constant_is_declared=requested.constant_is_declared,
            form=(
                DeclaredForm.HOMOGENEOUS if source_mode is SourceMode.TRUSTED else None
            ),
        )
        writing = EntryWriting(
            kind=WRITING_TWO_SECTOR,
            outcome=outcome,
            below=below,
            above=above,
            branch=branch,
            data_part=data_part,
            flag_part=flag_part,
        )
        return (entry, CERTIFICATE_LOCATORS[WRITING_TWO_SECTOR], writing)
    return None


def _label_collision(
    requested_operators: Sequence[CarriedOperatorRequest],
    instance_labels: Collection[str],
) -> Refusal | None:
    """Refuse a requested label that repeats an entry label, fail-closed.

    THE ENTRY LABEL IS THE KEY of every per-entry record the artefact carries:
    the discharge and the supplier fact the licence names
    (``req:licence-record``), the requested-entry locators the certificate row
    reports, and the writing the reference companion forms an entry at
    (``cor:reference-companion`` (vi)). A requested entry under the label of
    one of the instance's own entries, or two requested entries under one
    label, would make those records credit one entry with another's claim and
    drop the supplier fact it reads. So the request is refused, naming the
    label, rather than keyed by a position no consumer reads: the caller names
    its entries, and one name per entry is what the records need.
    """
    seen: set[str] = set(instance_labels)
    for requested in requested_operators:
        if requested.label in seen:
            owner = (
                "an entry the instance builds itself"
                if requested.label in instance_labels
                else "another requested entry"
            )
            return Refusal(
                reason=RefusalReason.CONSTRAINT_WITHOUT_CERTIFICATE,
                rule=str(FailClosedRule.CONSTRAINT_CERTIFICATE),
                detail=(
                    f"carried operator {requested.label!r} repeats the label of "
                    f"{owner}; every emitted entry is named by its label, which "
                    "keys what discharges its certificate in the licence "
                    "(req:licence-record), so an entry whose label is not its "
                    "own cannot be credited with its certificate and is refused"
                ),
            )
        seen.add(requested.label)
    return None


def certify_carried_operators(
    requested_operators: Sequence[CarriedOperatorRequest],
    *,
    source_mode: SourceMode,
    probe: ProbeDeclaration,
    target_povm: Sequence[Sequence[Matrix]],
    order: Sequence[JointOutcome],
    sectors: SectorSet,
    branch: tuple[int, int],
    data_part: tuple[int, int],
    flag_part: tuple[int, int],
    weights: Mapping[JointOutcome, Fraction],
    lattice_exponent: int,
    default_carried: Sequence[tuple[str, Sequence[Matrix]]],
    two_sector_claim: str | None,
    two_sector_missing_claim: str = "",
    instance_labels: Collection[str],
    extra_hypothesis: Callable[[], str | None] | None = None,
) -> tuple[CertifiedEntry, ...] | Refusal:
    """Certify every caller-requested operator, or refuse -- never drop one.

    ``reductions/cor:entries`` (i)-(iii) and
    ``reductions/req:uncertified-operator-refused``: a requested operator is
    emitted only where a claim stated for the instance gives a DECIDED
    CERTIFICATE for it -- a condition on the emitted numbers and the request's
    declared constants, decided exactly from them, that the claim proves
    sufficient for Eq. ``eq:certificate`` -- and that condition holds. Nothing
    is taken from the request on trust: its ``certificate_kind`` is read by
    nobody, and the request's operator, relation and constant are what is
    decided. The ``carried_operators`` row's ``certificate_rule`` lists the
    decided certificates stated; for the instances this engine builds they are
    recognised here, in this order:

    * a DEFAULT CARRIED OPERATOR requested as an entry, at ``c = 0`` with
      ``>=`` (``cor:entries`` (i)), on every instance
      (:func:`_default_carried_certificate`);
    * the CLASS-MARGINAL ENTRY where the instance discharges the class-marginal
      identity (``cor:entries`` (ii); :func:`_probe_expectation_certificate`);
    * the TWO-SECTOR ENTRY Eq. ``eq:two-sector-entry`` on the instance a claim
      states its decided certificate for -- ``two_sector_claim``, which the flat
      builder passes as ``wpfss/cor:two-sector-decided`` and every other
      builder as ``None`` (:func:`_two_sector_certificate`). On an instance
      with no such claim the writing is REFUSED, ``two_sector_missing_claim``
      naming the claim that would admit it.

    Every other requested operator is refused ``constraint_without_certificate``,
    and so is one whose decided certificate fails at the emitted numbers.

    Each surviving entry is returned WITH THE LOCATOR OF THE CLAIM THAT
    DISCHARGED IT, WITH WHETHER THAT CLAIM READS A SUPPLIER FACT, and WITH THE
    DIRECTION ITS CONSTANT WAS ROUNDED IN, so that the verification report and
    the licence (``req:licence-record``) can name the first two per entry, and
    the emission record can carry the third.

    THE DECLARED CONSTANT IS ROUNDED BEFORE ANY CERTIFICATE IS DECIDED.
    Corollary ``cor:entries`` (iii): a constant off the lattice "is FIRST
    rounded onto the lattice in the direction that enlarges the feasible set
    for ``bowtie``" -- down for ``>=``, up for ``<=`` -- and the entry is
    emitted at that constant, so the number decided and the number emitted
    are one. TWO CASES ARE REFUSED BEFORE THE ROUNDING, both by
    :func:`_off_lattice_constant_refusal`: a constant of modulus above one,
    under every relation, because no rounding onto the lattice repairs the
    modulus band of Eq. ``eq:latinv``; and an EQUALITY entry off the lattice,
    an equality having no loosening direction.

    An OPERATOR-form request never reaches here: the unsound-transplant row
    refuses it first.

    THE CALLER'S ARRAY IS SPLIT ONCE AND THE FAMILY IS NEVER ASSEMBLED. A
    caller-declared ``hat O`` is an operator on ``Q`` -- the ``carried_operators``
    input row states its admitted form as ``sum_v sum_s alpha_{v,s} Pi_s F_v
    Pi_s + Z``, declared as one array -- and that declaration is THE ONE PLACE
    A DENSE ARRAY ENTERS THIS MODULE, AND ONLY AS INPUT. It is split against
    the sector map by :func:`_declared_sector_blocks`, which REFUSES an array
    with a nonzero off-sector entry rather than truncating it, and everything
    afterwards -- the recognition, the certificate and the emitted entry -- is
    block by block. Nothing here builds a ``dim H(Q) x dim H(Q)`` array, on any
    route and for any request (assembling the family densely here as soon as
    one carried operator was requested would be exactly that).

    Args:
        requested_operators: the request's ``carried_operators``.
        source_mode: the declared source mode, which types a right-hand side.
        probe: the declared probe alphabet and its ``q_t``.
        target_povm: the emitted family, in the declared order of ``V``, each
            element as its SECTOR-BLOCK LIST (spec/architecture.md 2.8-2.9).
        order: the declared order of ``V``.
        sectors: the instance's sector set.
        branch: ``(start, length)`` of the branch the entries are read on.
        data_part: ``(start, length)`` of that branch's data sectors.
        flag_part: ``(start, length)`` of that branch's scalar sectors.
        weights: the certified weights by outcome.
        lattice_exponent: the declared ``kappa``.
        default_carried: the instance's transported set as ``(label,
            sector-block list)`` pairs, its default carried operators.
        two_sector_claim: the claim stating the two-sector writing's decided
            certificate for this instance, or ``None`` where none is stated.
        two_sector_missing_claim: where ``two_sector_claim`` is ``None``, the
            claim that would admit the writing, for the refusal's detail.
        instance_labels: the labels of the entries the instance built itself,
            which no requested entry may repeat (:func:`_label_collision`).
        extra_hypothesis: an extra condition a branching instance requires of
            the probe-expectation certificate; see
            :func:`_probe_expectation_certificate`.
    """
    if not requested_operators:
        return ()
    collision = _label_collision(requested_operators, instance_labels)
    if collision is not None:
        return collision
    entries: list[CertifiedEntry] = []
    for declared in requested_operators:
        if declared.form is ConstraintForm.OPERATOR:
            continue
        # (I4) -- every coefficient and every constant of an emitted entry a
        # declared lattice value -- is not decided here: the constant is
        # rounded onto the lattice below, and the operator's entries (``a`` and
        # ``b`` of the two-sector writing among them) are decided by the
        # licensed route's lattice row, rule_licensed_hermiticity, on every
        # emitted entry before the licence is issued (req:licensed-entry-lattice).
        # What is decided here, exactly over the rationals, is the certificate.
        off_lattice = _off_lattice_constant_refusal(declared, lattice_exponent)
        if off_lattice is not None:
            return off_lattice
        constant, direction = rounded_constant(
            declared.constant, declared.relation, lattice_exponent
        )
        requested = (
            declared
            if constant == declared.constant
            else replace(declared, constant=constant)
        )
        rounding = None if constant == declared.constant else direction
        declared_blocks = _declared_sector_blocks(requested, sectors)
        if isinstance(declared_blocks, Refusal):
            return declared_blocks
        default = _default_carried_certificate(
            requested,
            declared_blocks,
            source_mode=source_mode,
            default_carried=default_carried,
        )
        if default is not None:
            entry, locator, writing = default
            entries.append(
                CertifiedEntry(
                    entry=entry,
                    locator=locator,
                    rounding=rounding,
                    writing=writing,
                    reads_supplier=False,
                )
            )
            continue
        probe_entry = _probe_expectation_certificate(
            requested,
            declared_blocks,
            source_mode=source_mode,
            probe=probe,
            target_povm=target_povm,
            order=order,
            extra_hypothesis=extra_hypothesis,
        )
        if isinstance(probe_entry, Refusal):
            return probe_entry
        if probe_entry is not None:
            entries.extend(
                CertifiedEntry(
                    entry=entry, locator=locator, rounding=rounding, writing=writing
                )
                for entry, locator, writing in probe_entry
            )
            continue
        two_sector = _two_sector_certificate(
            requested,
            declared_blocks,
            source_mode=source_mode,
            target_povm=target_povm,
            order=order,
            sectors=sectors,
            branch=branch,
            data_part=data_part,
            flag_part=flag_part,
            weights=weights,
            claim=two_sector_claim,
            missing_claim=two_sector_missing_claim,
        )
        if isinstance(two_sector, Refusal):
            return _with_rounding(two_sector, declared.constant, constant, rounding)
        if two_sector is None:
            return _with_rounding(
                Refusal(
                    reason=RefusalReason.CONSTRAINT_WITHOUT_CERTIFICATE,
                    rule=str(FailClosedRule.CONSTRAINT_CERTIFICATE),
                    detail=(
                        f"carried operator {requested.label!r}: no claim stated "
                        "for this instance gives a decided certificate for this "
                        "operator (cor:entries (iii); "
                        "req:uncertified-operator-refused). It is not a default "
                        "carried operator of the instance's transported set at "
                        ">= 0 (cor:entries (i)), not the class-marginal entry of "
                        "a setting the instance discharges at its declared q_t "
                        "(cor:entries (ii)), and not the two-sector entry "
                        "eq:two-sector-entry; no certificate is taken from the "
                        "request on trust"
                    ),
                ),
                declared.constant,
                constant,
                rounding,
            )
        entry, locator, writing = two_sector
        entries.append(
            CertifiedEntry(
                entry=entry, locator=locator, rounding=rounding, writing=writing
            )
        )
    return tuple(entries)


def _with_rounding(
    refusal: Refusal, declared: Fraction, constant: Fraction, rounding: str | None
) -> Refusal:
    """Append to a refusal's detail the rounding the declared constant took."""
    if rounding is None:
        return refusal
    return replace(
        refusal,
        detail=refusal.detail
        + f"; its declared constant {declared} was first rounded to {constant} "
        f"({rounding})",
    )
