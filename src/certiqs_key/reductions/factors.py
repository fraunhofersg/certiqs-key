"""The emission of several measuring parties: ``thm:emitted-product``, as code.

WHY THE PRODUCT IS NEVER FORMED. The emission is a factorised family, with no
snap, and not the product of two stations' targets passed through the emission
normaliser. Forming the product has three obstructions: a product sector -- one
station's data block times the other's flag -- fits neither kind of
``def:reduction-instance`` (I2), the stability clause fails at the lattice scale for
weighted-flag values, and a normalised product would declare a NON-PRODUCT measurement
for two separated stations. All three vanish if the product is never formed as a
declared datum.

WHAT IS EMITTED INSTEAD, and it is the whole of this module: THE ORDERED LIST
OF THE FACTORS' ARTEFACTS, one per measuring party, each with its own party
label, sector map, target, channel witness, transported operators, constraint
list, licence, chain and emission record -- AND THE COMBINATION RULE, which is
a RULE AND NOT A DATUM,

    ``F_v = (x)_f F^f_{v_f}``,  ``M^dec_v = (x)_f M^dec,f_{v_f}``,
    ``v = (v_f)_f in V = prod_f V^f``,

read in the DECLARED ORDER OF THE FACTORS, the last factor varying fastest
(``subsystem_order_factors``).

**NO PRODUCT OPERATOR IS EMITTED, DECLARED, ROUNDED OR SNAPPED.** That is the
point of the row and it is binding on this file: "there is no product datum, so
there is no second emission, no second normalizer pass and no further
displacement -- every displacement, kept or moved class and rounding
direction is a factor's and is recorded in that factor's
``emission_record``" (``thm:emitted-product`` (v)). The reason is arithmetic as
well as structural: a Kronecker product of two families on the ``2^-kappa``
lattice lies on the ``2^-2kappa`` lattice, so a declared product would have to
be re-normalised against ``kappa``. SO NO FUNCTION OF THIS FILE FORMS A
KRONECKER PRODUCT: the product sector map, the product alphabet and the
product classes are COMBINATORIAL (labels, dimensions and orders), every
predicate of ``spec/architecture.md`` 2.9's admission has already been decided
PER FACTOR by that factor's own emission, and
:meth:`~certiqs_key.domain.families.FactorisedFamily.product_block` -- which
does form one, for a numerical consumer -- is called by nothing here. A test
fails if any Kronecker product is formed on this path.

THE PRODUCT CLASS WEIGHTS ARE NOT EMITTED AS NUMBERS EITHER, and could not be:
"each factor weight lies on that factor's declared lattice, and a product of
two lattice numbers lies in general on a FINER LATTICE ONLY and need not be a
binary64 number at all, exactly as for the blocks" (``thm:emitted-product``
(iv)). They are formed in the exact substrate by whoever needs one.

ONE FACTOR IS TODAY'S ARTEFACT, BYTE FOR BYTE. "At one factor the combination
rule is the identity, the product sector map is that factor's, the product
channel is that factor's channel, and every statement above is ``thm:emit``'s
and ``thm:licence`` (i)-(iv)'s for that instance (``thm:emitted-product``
(vi)). SO THIS ROW ADDS NOTHING TO A ONE-FACTOR ARTEFACT AND IS ABSENT FROM
IT." :func:`reduce_factors` of one factor calls
:func:`certiqs_key.reductions.emit.reduce` once and hands back exactly the
artefact that call emitted; nothing of this file touches it.

WHAT THIS MODULE ADDS TO THE SHARED FORMAT AND WHAT IT TAKES FROM IT. The
product sector map and the factorised family are the merged stage-1 types
:class:`~certiqs_key.foundations.blocks.FactorisedSectorMap`,
:class:`~certiqs_key.foundations.blocks.SectorFactor`,
:class:`~certiqs_key.foundations.blocks.SystemTag` and
:class:`~certiqs_key.domain.families.FactorisedFamily`: this module declares no
second product convention and flattens nothing of its own. What it adds is what
those types do not carry: which artefact each factor emitted, the combination
rule as an emitted record, the joint entry list with its ``party_local`` tags,
and the licence's party-local row.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from certiqs_key.domain.families import FactorFamily, FactorisedFamily
from certiqs_key.foundations.blocks import (
    BlockKind,
    BlockOperator,
    FactorisedSectorMap,
    Label,
    SectorFactor,
    SectorStructure,
    SystemTag,
)
from certiqs_key.reductions.artifact import ProofReductionArtifact, ReductionOutcome
from certiqs_key.reductions.constraints import (
    AttackSetLicence,
    ConstraintEntry,
    EntryDischarge,
    PartyLocalLicence,
    admissible_set_expression,
    party_local_entry,
    party_local_scalar_set_expression,
    party_local_set_expression,
)
from certiqs_key.reductions.emit import outcome_label, reduce
from certiqs_key.reductions.errors import MalformedInputError
from certiqs_key.reductions.inputs import ReductionCall
from certiqs_key.reductions.instance import InstanceBuilder
from certiqs_key.reductions.reasons import (
    FailClosedRule,
    Refusal,
    RefusalReason,
)
from certiqs_key.reductions.sectors import declared_party, joined_sector_label
from certiqs_key.reductions.validation import (
    rule_constraint_channel,
    rule_licence_presence,
    rule_licensed_hermiticity,
)

__all__ = [
    "COMBINATION_RULE",
    "NO_PRODUCT_OPERATOR_IS_EMITTED",
    "PRODUCT_CLASS_WEIGHTS",
    "FactorCall",
    "FactorEmission",
    "FactorEmissionOutcome",
    "assemble_factor_emissions",
    "entry_link_witness",
    "factor_sector_map",
    "reduce_factors",
]

#: The combination rule of ``thm:emitted-product``, Eq. ``eq:producttarget``,
#: EMITTED AS A RULE AND NOT AS A DATUM.
COMBINATION_RULE: str = (
    "F_v = (x)_f F^f_{v_f} and M^dec_v = (x)_f M^dec,f_{v_f} over the product "
    "alphabet V = prod_f V^f, in the declared order of the factors, the LAST "
    "FACTOR VARYING FASTEST (eq:producttarget; the subsystem_order_factors "
    "convention). The product channel is Lambda = (x)_f Lambda_f and the "
    "product sector map has index set prod_f S^f in the product order, "
    "identifiers the factors' identifiers joined in that order, dimensions the "
    "products and projectors Pi_s = (x)_f Pi^f_{s_f} (thm:emitted-product (i), "
    "(ii))"
)

#: ``interface.yaml``, ``factor_emission.no_product_operator_is_emitted``:
#: BINDING, AND THE POINT OF THE ROW.
NO_PRODUCT_OPERATOR_IS_EMITTED: str = (
    "NO ENTRY OF ANY F_v, OF ANY M^dec_v OR OF ANY PRODUCT CONSTRAINT OPERATOR "
    "IS EMITTED, DECLARED, ROUNDED OR SNAPPED: there is no product datum, so "
    "there is no second emission, no second normalizer pass and no further "
    "displacement -- every displacement, kept or moved class and rounding "
    "direction is a factor's and is recorded in that factor's "
    "emission_record (thm:emitted-product (v)). A consumer that needs a product "
    "block forms it from the factors' blocks, under its own number model"
)

#: ``thm:emitted-product`` (iv), on the product class weights.
PRODUCT_CLASS_WEIGHTS: str = (
    "V_t = prod_f V^f_{t_f} with q_t = prod_f q^f_{t_f}, formed IN THE EXACT "
    "SUBSTRATE (def:substrate) by whoever needs one and NOT EMITTED AS A NUMBER "
    "OF THIS MODULE -- each factor weight lies on that factor's declared "
    "lattice, and a product of two lattice numbers lies in general on a FINER "
    "LATTICE ONLY and need not be a binary64 number (thm:emitted-product (iv))"
)


@dataclass(frozen=True)
class FactorCall:
    """One factor of a call that declares several instances, one per party.

    ``call`` and ``builder`` are exactly what
    :func:`certiqs_key.reductions.emit.reduce` takes for one instance: this
    type adds no input row and narrows none. The factor's PARTY LABEL is the
    declaration's own (``call.declaration.party_label``, the
    ``sector_declaration`` row's optional key, Bob's where it is absent), and
    ``sector_block_kind`` is the instance's declared kind, which the shared
    format's sector map requires and never defaults -- the same discipline
    :mod:`certiqs_key.reductions.docking` states for it: supplying one would be
    deciding what somebody else's decomposition is licensed by.
    """

    call: ReductionCall
    builder: InstanceBuilder
    sector_block_kind: BlockKind | str
    #: THE FACTOR'S OWN LABEL, which is what a party-local entry's SCOPE names
    #: and what a consumer compares against the emitted factor list. ``None``
    #: takes the default of :func:`factor_label`, the factor's position in the
    #: declared order. IT IS NOT THE PARTY LABEL: "NOTHING REQUIRES TWO FACTORS
    #: TO CARRY DIFFERENT LABELS" (the ``factor_emission`` row), so two
    #: stations of one party are two factors of one party label and the scope
    #: must still name exactly one of them.
    factor_label: Label | None = None

    @property
    def party(self) -> Label:
        """Return the factor's declared party, Bob's where none is declared."""
        return declared_party(self.call.declaration.party_label)


def factor_label(position: int, declared: Label | None = None) -> Label:
    """Return the label of the factor at ``position``: the declared one or ``f<i>``.

    THE WIRE SPELLING IS A LABEL AND THE CONSUMER COMPARES IT AGAINST THE
    FACTOR LIST, which is what the consuming interfaces type it as:
    ``protocol-compiler``'s ``constraint_scope`` row is "one factor label per
    entry ... The label of the measured factor the entry's operator is written
    against, passed through unchanged", its ``entry_scope_and_tag`` validation
    row checks that "every constraint entry's scope NAMES A MEASURED FACTOR of
    the emitted sector map" and refuses ``constraint_scope_not_a_factor`` on "A
    COMPARISON OF A LABEL AGAINST THE FACTOR LIST", and ``meat-core``'s
    ``constraint_scope_and_party_local_tag`` row types it the same way. So the
    scope is a label, not an index, and the emitted factor list carries the
    same labels so that the comparison has both sides.

    IT IS NOT THE PARTY LABEL, and that is the whole reason this function
    exists: a party may measure on two factors, the compiler's own party labels
    are drawn from a two-member set, and a scope that named a party would name
    two factors there. THE DEFAULT IS THE POSITION IN THE DECLARED ORDER,
    ``f0``, ``f1``, ..., which is unique by construction and readable against
    ``subsystem_order_factors``; a caller that has its own names declares them.
    """
    return f"f{position}" if declared is None else declared


def factor_sector_map(
    artefact: ProofReductionArtifact, block_kind: BlockKind | str
) -> SectorStructure:
    """Return one factor's emitted sector map, in the shared format's type.

    THE MAP IS THE TYPE AND NOT A DESCRIPTION OF ONE: the identifiers in the
    declared order, the dimensions, and the block kind the instance declared.
    The pair ``(group, name)`` is joined by
    :func:`certiqs_key.reductions.sectors.joined_sector_label`, one spelling for
    the whole repository, and a join that would collide is refused rather than
    merged -- two sectors of an emitted target under one identifier would be a
    product factor nobody can read back.
    """
    labels = tuple(
        joined_sector_label(label)
        for label in artefact.target_descriptor.sectors.labels
    )
    if len(set(labels)) != len(labels):
        raise MalformedInputError(
            "two sectors of a factor's sector set collide when their "
            "(group, name) pair is joined into one identifier "
            "(def:reduction-instance (I2)); the factor emission refuses rather "
            "than merging two sectors of an emitted target"
        )
    return SectorStructure(
        labels=labels,
        dims=tuple(artefact.target_descriptor.sectors.dimensions),
        block_kind=(
            block_kind if isinstance(block_kind, BlockKind) else BlockKind(block_kind)
        ),
    )


@dataclass(frozen=True)
class FactorEmission:
    """The ``factor_emission`` output row: the factors' artefacts and the rule.

    PRESENT EXACTLY WHEN THE CALL DECLARES MORE THAN ONE INSTANCE. At one
    factor :func:`reduce_factors` emits the artefact alone and this record is
    absent, as in every one-factor emission.

    ``sector_map`` and ``family`` are the shared format's
    (:class:`~certiqs_key.foundations.blocks.FactorisedSectorMap`,
    :class:`~certiqs_key.domain.families.FactorisedFamily`): the product sector
    map and the factorised family, both of which carry the product as a RULE
    over the factors' own blocks. Neither forms a product operator and neither
    is asked to.

    ``entries`` is the joint list ``CList = bigsqcup_f {(O^_k, bowtie_k, c_k;
    f)}`` of ``thm:emitted-product`` (iii), each entry SCOPED TO ITS FACTOR --
    by that factor's LABEL, not by its party's (:func:`factor_label`) -- and
    carrying the same operator, the same relation and the same constant as the
    entry that factor emitted. ``licence`` is the licence record whose
    party-local row is built PER ENTRY (:class:`PartyLocalLicence`).

    ``factors`` is the declared ordered list of factor labels, and it is what a
    consumer compares a scope against.
    """

    artefacts: tuple[ProofReductionArtifact, ...]
    #: The factor labels, in the product order. A scope names one of these.
    factors: tuple[Label, ...]
    #: The party of each factor, in the same order. TWO FACTORS MAY CARRY ONE
    #: PARTY LABEL -- two stations of one party are two factors -- so this is
    #: carried BESIDE the factor label and never in place of it.
    parties: tuple[Label, ...]
    sector_map: FactorisedSectorMap
    family: FactorisedFamily
    entries: tuple[ConstraintEntry, ...]
    licence: AttackSetLicence | None
    #: Per factor, the witness identity of that factor's TRAILING link -- the
    #: link its entries sit on (:func:`entry_link_witness`) -- in the product
    #: order. The product channel is ``(x)_f Lambda_f`` and is a RULE over
    #: these: no composed channel object is built, and none could be -- an
    #: instance's constructor may read a family no artefact carries.
    channel_witnesses: tuple[str, ...]
    combination_rule: str = COMBINATION_RULE

    def __post_init__(self) -> None:
        """Refuse a factor list whose labels do not name its factors.

        THE LABELS ENUMERATE A SET, because a scope names ONE factor and a
        consumer decides it by "A COMPARISON OF A LABEL AGAINST THE FACTOR
        LIST" (``protocol-compiler``'s ``entry_scope_and_tag`` row). A repeated
        factor label would leave that comparison naming two factors, which is
        the ambiguity the factor label exists to remove -- and it is a defect of
        a PRODUCER, not a declaration a caller makes, so it is refused here and
        not by a fail-closed row.
        """
        if len(set(self.factors)) != len(self.factors):
            raise MalformedInputError(
                f"the factor labels {list(self.factors)} repeat one; a "
                "party_local entry's scope names ONE factor of the declared "
                "list and a consumer decides it by comparing the label against "
                "that list (cor:entries, the tag paragraphs)"
            )

    @property
    def count(self) -> int:
        """Return the number of factors."""
        return len(self.artefacts)

    def product_alphabet(self) -> tuple[Label, ...]:
        """Return ``prod_f V^f``, delegating to the shared format's family.

        The last factor varies fastest and a product letter is the factors'
        letters joined by the shared separator -- the same convention the
        product SECTOR identifier uses, declared once in
        :mod:`certiqs_key.foundations.blocks` and not again here.
        """
        return self.family.alphabet()

    def product_sector_map(self) -> SectorStructure:
        """Return the flattened product sector map, in the product order.

        COMBINATORIAL: identifiers, dimensions and a block kind. It names the
        blocks of ``F_v`` and carries none of them; the block at
        ``s = (s_f)_f`` is the Kronecker product of the factors' blocks BY THE
        RULE (``thm:emitted-product`` (i)), formed by a consumer that needs one
        and by nothing here.
        """
        return self.sector_map.flattened()

    def as_machine_record(self) -> dict[str, object]:
        """Return the ``factor_emission`` value: the list, the rule, no product.

        The artefacts appear WHOLE and in the declared order, each under its
        FACTOR LABEL with its party beside it, because the row's content is "THE
        ORDERED LIST OF THE FACTORS' ARTEFACTS ... each a complete artefact of
        this module". Every operator in the record is a factor's own block list;
        the product is named by the rule and by the flattened map's labels and
        dimensions, and no entry of any product operator appears anywhere in it.

        AT ONE FACTOR THERE IS NO VALUE FOR THIS KEY AND THIS METHOD REFUSES.
        The row is "PRESENT EXACTLY WHEN THE CALL DECLARES MORE THAN ONE
        INSTANCE ... ABSENT FOR A ONE-FACTOR EMISSION", so a one-factor
        emission has an ARTEFACT and no ``factor_emission``: what a caller wants
        back there is :attr:`FactorEmissionOutcome.artefact`, and a record here
        would be a value for a key the accepted row says is absent.
        """
        if self.count == 1:
            raise MalformedInputError(
                "a ONE-FACTOR emission has no `factor_emission` value: the row "
                "is present exactly when the call declares MORE THAN ONE "
                "instance and is ABSENT from a one-factor emission (the "
                "factor_emission output row; "
                "thm:emitted-product (vi)). What a caller reads there is the "
                "artefact itself, FactorEmissionOutcome.artefact"
            )
        flattened = self.product_sector_map()
        return {
            "factors": [
                {
                    "factor": label,
                    "party": party,
                    "channel_witness": witness,
                    "artefact": artefact.as_machine_record(),
                }
                for label, party, witness, artefact in zip(
                    self.factors,
                    self.parties,
                    self.channel_witnesses,
                    self.artefacts,
                    strict=True,
                )
            ],
            "combination_rule": self.combination_rule,
            "product_sector_map": {
                "sector_index_set": list(flattened.labels),
                "sector_dims": list(flattened.dims),
                "sector_block_kind": str(flattened.block_kind),
                "factor_list": list(self.factors),
                "party_per_factor": list(self.sector_map.parties),
                "system_per_factor": [str(tag) for tag in self.sector_map.systems],
            },
            "product_alphabet": list(self.product_alphabet()),
            "product_channel": (
                "Lambda = (x)_f Lambda_f over the factors' own channel "
                "witnesses, in the declared order: "
                + ", ".join(self.channel_witnesses)
            ),
            "product_class_weights": PRODUCT_CLASS_WEIGHTS,
            "constraint_list": [
                {
                    "label": entry.label,
                    "relation": str(entry.relation),
                    "constant": str(entry.constant),
                    "tag": None if entry.tag is None else str(entry.tag),
                    "scope": entry.scope,
                    "certified_against": entry.certified_against,
                }
                for entry in self.entries
            ],
            "attack_set_license": (
                None if self.licence is None else self.licence.as_machine_record()
            ),
            "no_product_operator_is_emitted": NO_PRODUCT_OPERATOR_IS_EMITTED,
        }


@dataclass(frozen=True)
class FactorEmissionOutcome:
    """What a factor emission returns: the emission OR a refusal, never both.

    ``outcomes`` carries every factor's own
    :class:`~certiqs_key.reductions.artifact.ReductionOutcome` whatever
    happened, refusal or not, because each factor's verification report is that
    factor's and a caller diagnosing a refusal reads the report of the factor
    that refused. The refusal a caller receives is THE FIRST FACTOR'S IN THE
    DECLARED ORDER, for the reason the core returns the first failing row in
    the interface's row order: two calls failing the same way name the same
    thing.
    """

    emission: FactorEmission | None
    outcomes: tuple[ReductionOutcome, ...]
    refusal: Refusal | None

    def __post_init__(self) -> None:
        """Refuse an outcome that is neither a refusal nor an emission, or both."""
        if (self.emission is None) == (self.refusal is None):
            raise MalformedInputError(
                "a factor emission returns the emission OR a refusal and never "
                "both: a failure produces a refusal with a machine-readable "
                "reason and NO ARTEFACT (the fail_closed convention)"
            )

    @property
    def emitted(self) -> bool:
        """Whether an emission was produced."""
        return self.emission is not None

    @property
    def artefact(self) -> ProofReductionArtifact | None:
        """Return the single artefact of a ONE-FACTOR emission, or ``None``.

        At one factor the emission is that artefact and nothing else, which is
        what a one-factor caller wants back: ``thm:emitted-product`` (vi) and
        the ``factor_emission`` row's ``one_factor_is_todays_artefact``.
        """
        if self.emission is None or self.emission.count != 1:
            return None
        return self.emission.artefacts[0]


def reduce_factors(
    factors: Sequence[FactorCall],
    *,
    declared_factor_order: Sequence[Label] | None = None,
) -> FactorEmissionOutcome:
    """Emit one artefact PER MEASURING PARTY, plus the combination rule.

    ``thm:emitted-product``. Each factor is reduced by
    :func:`certiqs_key.reductions.emit.reduce`, on its own declared inputs and
    its own builder, and NOTHING OF THIS FUNCTION REACHES INSIDE ONE OF THOSE
    CALLS: a factor's artefact is the artefact that call emitted, which is why
    a one-factor call emits exactly today's artefact.

    WHAT THIS FUNCTION DECIDES, AND IT ADDS NO ROW AND NO REASON STRING. The
    ``alphabet_order`` row covers the factor order: the
    order of the factors is DECLARED DATA and is the order the product
    alphabet and the product sector map are read in, so a
    ``declared_factor_order`` that disagrees with the list is refused
    ``alphabet_or_order_mismatch`` rather than reordering a declared product.
    The ``constraint_channel`` row covers tagged entries: a tagged entry
    names a factor of the declared list and is certified against THAT FACTOR'S
    own channel witness. And the ``licensed_hermiticity`` row, decided on the
    joint list, which is per factor's blocks because a tagged entry IS a
    factor's block list.

    TWO STATIONS OF ONE PARTY ARE TWO FACTORS AND ARE EMITTED, and that is what
    the FACTOR LABEL is for: "NOTHING REQUIRES TWO FACTORS TO CARRY DIFFERENT
    LABELS" (the ``factor_emission`` row) is about PARTY labels, and a scope
    names a factor (:func:`factor_label`). The labels of the declared list must
    enumerate a set, which :class:`FactorEmission` decides, because a scope must
    name exactly one factor; the parties need not.

    EVERY FACTOR DECLARES THE SAME SOURCE MODE OR THE LIST IS MALFORMED. See
    :func:`_one_source_mode`: ``thm:emitted-product`` (iii) licenses the joint
    list in ONE licensed class, and no refusal string of this module has a row
    that is true of a mixed list.

    Args:
        factors: the declared ordered list of factors, one per measuring party
            and one per measured system. ONE FACTOR IS THE BASIC-FORMAT CASE and is
            every declared instance of this repository.
        declared_factor_order: the caller's declared order of the factors, BY
            FACTOR LABEL, VALIDATED against the list and never constructed from
            it. ``None`` declares none and validates nothing.
    """
    if not factors:
        raise MalformedInputError(
            "a factor emission is over AT LEAST ONE factor; the one-factor case "
            "is today's artefact (thm:emitted-product (vi))"
        )
    labels = _factor_labels(factors)
    _one_source_mode(factors, labels)
    outcomes = tuple(reduce(factor.call, factor.builder) for factor in factors)
    refused = next(
        (outcome.refusal for outcome in outcomes if outcome.refusal is not None),
        None,
    )
    if refused is not None:
        return FactorEmissionOutcome(
            emission=None, outcomes=outcomes, refusal=refused
        )
    artefacts = tuple(
        outcome.artifact for outcome in outcomes if outcome.artifact is not None
    )
    emission = assemble_factor_emissions(
        factors, artefacts, declared_factor_order=declared_factor_order
    )
    if isinstance(emission, Refusal):
        return FactorEmissionOutcome(
            emission=None, outcomes=outcomes, refusal=emission
        )
    return FactorEmissionOutcome(emission=emission, outcomes=outcomes, refusal=None)


def _factor_labels(factors: Sequence[FactorCall]) -> tuple[Label, ...]:
    """Return the factors' declared/default labels in product order."""
    return tuple(
        factor_label(position, factor.factor_label)
        for position, factor in enumerate(factors)
    )


def assemble_factor_emissions(
    factors: Sequence[FactorCall],
    artefacts: Sequence[ProofReductionArtifact],
    *,
    declared_factor_order: Sequence[Label] | None = None,
) -> FactorEmission | Refusal:
    """Assemble already-emitted factor artefacts without reducing them again.

    A run that prepared and executed each station separately still needs the
    reductions-owned product rule, scoped entries and joint licence.  This is
    the same assembly path :func:`reduce_factors` uses after every factor has
    emitted successfully; it repeats the list-level mode, order, channel and
    Hermiticity checks, and never reruns a receiver or reduction.
    """
    if not factors:
        raise MalformedInputError(
            "a factor emission is over AT LEAST ONE factor; the one-factor "
            "case is today's artefact (thm:emitted-product (vi))"
        )
    if len(factors) != len(artefacts):
        raise MalformedInputError(
            "one already-emitted artefact is required for every FactorCall in "
            f"the declared order; got {len(artefacts)} artefacts for "
            f"{len(factors)} factors"
        )
    labels = _factor_labels(factors)
    parties = tuple(factor.party for factor in factors)
    _one_source_mode(factors, labels)
    order_refusal = _factor_order_refusal(labels, declared_factor_order)
    if order_refusal is not None:
        return order_refusal
    return _assemble(factors, artefacts, labels, parties)


def _one_source_mode(
    factors: Sequence[FactorCall], labels: Sequence[Label]
) -> None:
    """Refuse a factor list whose factors declare DIFFERENT source modes.

    THE CONSERVATIVE READING, AND NO EXISTING REFUSAL STRING'S ROW IS TRUE OF
    IT. ``thm:emitted-product`` (iii) licenses the joint list "with its entries
    read party-locally (Definition def:licensed), or as scalars on the lifted
    operators ..., or any mixture", and ``def:licensed`` types a licensed
    right-hand side BY THE DECLARED SOURCE MODE: ``Theta_k = c_k tau_A`` in
    trusted mode, ``Theta_k = c_k`` in untrusted mode. A joint list whose
    factors declared different modes would be typed in two licensed classes at
    once, and no admissible set of ``def:attset`` is stated over two, so the
    emission has nothing to name in its licence.

    WHY IT IS RAISED AND NOT REFUSED WITH A REASON STRING. The strings
    of ``interface.yaml`` each have a row, and every row's subject is a datum of
    ONE declaration or the emitted family: the nearest candidates were
    ``alphabet_or_order_mismatch`` (alphabets, sector order and basis order),
    ``route_not_single_valued`` (one artefact carrying two routes) and
    ``licence_missing`` (the presence iff), and a mixed-mode factor LIST is none
    of the three. The file binds that no further string exists, so this is
    a MALFORMED FACTOR LIST -- not a presentation of a product of instances at
    all, exactly as an empty list is not -- and is raised where the list is
    read, before any factor is reduced.
    """
    modes = {factor.call.declaration.source_mode for factor in factors}
    if len(modes) > 1:
        spelled = ", ".join(
            f"{label}: {factor.call.declaration.source_mode.value}"
            for label, factor in zip(labels, factors, strict=True)
        )
        raise MalformedInputError(
            "every factor of one emission declares THE SAME source mode; this "
            f"list declares more than one ({spelled}). def:licensed types a "
            "licensed right-hand side by the declared mode, and thm:emitted-"
            "product (iii) licenses the joint list in ONE licensed class, so a "
            "mixed list has no admissible set of def:attset to name; no refusal "
            "reason of interface.yaml has a row that is true of it, and this "
            "file binds that no further string exists"
        )


def _factor_order_refusal(
    labels: Sequence[Label], declared: Sequence[Label] | None
) -> Refusal | None:
    """Decide the factor half of the ``alphabet_order`` row.

    "THE ORDER OF THE FACTORS agrees with the order the product alphabet and
    the product sector map are read in ... It is VALIDATED against the declared
    product set and grouping and NEVER CONSTRUCTED IN PLACE OF A MISSING
    DECLARATION." The order is declared BY FACTOR LABEL, which is what a scope
    names and what a consumer compares against the factor list; the parties are
    carried beside the labels and two factors may share one.
    """
    if declared is not None and tuple(declared) != tuple(labels):
        return Refusal(
            reason=RefusalReason.ALPHABET_OR_ORDER_MISMATCH,
            rule=str(FailClosedRule.ALPHABET_ORDER),
            detail=(
                f"the declared factor order {list(declared)} is not the order of "
                f"the declared factor list {list(labels)}; the order of the "
                "factors is DECLARED DATA and is the order the product "
                "alphabet, the product sector map and every Kronecker product "
                "of the combination rule are read in "
                "(subsystem_order_factors), and it is validated here and never "
                "constructed"
            ),
        )
    return None


def entry_link_witness(artefact: ProofReductionArtifact) -> str:
    """Return the witness of the link a factor's entries sit on: its squashing link.

    ``thm:licence`` (v) licenses a party-local entry on THAT FACTOR'S channel
    ``Lambda_f``, the composite of the factor's chain, whose entries sit on
    its last link, the instance's squashing link; so the witness each
    factor's entries are checked against is that link's, per factor and
    against that factor's own artefact (``lem:party-local`` (iv)).
    """
    return artefact.squashing_channel.identity


def _assemble(
    factors: Sequence[FactorCall],
    artefacts: Sequence[ProofReductionArtifact],
    labels: Sequence[Label],
    parties: Sequence[Label],
) -> FactorEmission | Refusal:
    """Build the emission from the factors' artefacts: no product is formed.

    The sector map is a product of the factors' own maps, each carrying the
    party that factor declared and the system ``Q`` it decomposes -- every
    factor here is a MEASURED system, ``{F_v}`` being a measurement on the
    measured systems, and the retained ``A`` factor of the shared format is not
    a factor of this emission. The family is one
    :class:`~certiqs_key.domain.families.FactorFamily` per factor over that
    factor's own alphabet and blocks.
    """
    maps = tuple(
        factor_sector_map(artefact, factor.sector_block_kind)
        for factor, artefact in zip(factors, artefacts, strict=True)
    )
    sector_map = FactorisedSectorMap(
        factors=tuple(
            SectorFactor(
                party=party,
                sectors=sectors,
                system=SystemTag.Q,
                label=label,
            )
            for label, party, sectors in zip(labels, parties, maps, strict=True)
        )
    )
    families: list[FactorFamily] = []
    for factor, artefact, sectors in zip(factors, artefacts, maps, strict=True):
        order = factor.call.declaration.joint_alphabet
        families.append(
            FactorFamily.of(
                party=declared_party(factor.call.declaration.party_label),
                alphabet=[
                    outcome_label(
                        outcome, factor.call.declaration.probe_declaration.settings
                    )
                    for outcome in order
                ],
                members=[
                    BlockOperator.of(sectors, artefact.target_povm[outcome])
                    for outcome in order
                ],
            )
        )
    family = FactorisedFamily.of(sector_map, families)
    witnesses = tuple(entry_link_witness(artefact) for artefact in artefacts)
    one_factor = len(artefacts) == 1
    scoped = tuple(
        (label, artefact, party_local_entry(entry, label, one_factor=one_factor))
        for label, artefact in zip(labels, artefacts, strict=True)
        for entry in artefact.constraint_list
    )
    entries = tuple(entry for _, _, entry in scoped)
    # THE TWO WIDENED ROWS ARE DECIDED PER FACTOR, AGAINST THAT FACTOR'S OWN
    # ARTEFACT, which is what makes "that factor's own channel witness" mean the
    # witness of the artefact the entry came from -- the hypothesis thm:licence
    # (v) states. A witness IDENTITY is a description and need not distinguish
    # two factors (a pair of stations of one device model emits the same string
    # twice), so a single pass over a label-keyed mapping would accept an entry
    # of one factor certified against another's channel in exactly that case,
    # which is the unsound direction lem:party-local (iv) exhibits.
    for label, artefact, entry in scoped:
        witness = entry_link_witness(artefact)
        channel_refusal = rule_constraint_channel(
            (entry,), witness, factor_witnesses={label: witness}
        )
        if channel_refusal is not None:
            return channel_refusal
        hermiticity_refusal = rule_licensed_hermiticity(
            (entry,),
            artefact.route,
            lattice_exponent=artefact.emission_record.lattice_exponent,
        )
        if hermiticity_refusal is not None:
            return hermiticity_refusal
    # AND THE INVARIANT THE PER-FACTOR PASS ESTABLISHES IS ASSERTED OVER THE
    # WHOLE EMISSION, so that what the passes above decide entry by entry is
    # also a statement about the joint list a consumer receives: every tagged
    # entry's scope is a factor of the declared list, and its certificate is
    # that factor's own channel witness.
    # It is a check on THIS FUNCTION and not on declared data -- the scopes are
    # written here -- so a failure is a defect of the producer and is raised.
    declared_witnesses = dict(zip(labels, witnesses, strict=True))
    for entry in entries:
        if entry.tag is None:
            continue
        if declared_witnesses.get(entry.scope or "") != entry.certified_against:
            raise MalformedInputError(
                f"the emitted entry {entry.label!r} is scoped to "
                f"{entry.scope!r} and certified against "
                f"{entry.certified_against!r}, which is not that factor's own "
                "channel witness; thm:licence (v) licenses the party-local "
                "reading ON THAT FACTOR'S CHANNEL and on nothing else"
            )
    licence = _joint_licence(factors, artefacts, scoped, labels, parties)
    # THE PRESENCE IFF, decided on the joint list as emit.reduce decides it on
    # one artefact: a list with entries and no licence (an entry whose factor's
    # licence names no discharge for it, req:licence-record) is refused
    # licence_missing rather than emitted without its record.
    presence_refusal = rule_licence_presence(entries, licence is not None)
    if presence_refusal is not None:
        return presence_refusal
    return FactorEmission(
        artefacts=tuple(artefacts),
        factors=tuple(labels),
        parties=tuple(parties),
        sector_map=sector_map,
        family=family,
        entries=entries,
        licence=licence,
        channel_witnesses=witnesses,
    )


def _factor_discharges(
    artefact: ProofReductionArtifact,
) -> tuple[EntryDischarge, ...] | None:
    """Return the discharge a factor's own licence names for each of its entries.

    In the order of the factor's ``constraint_list``, the order its licence was
    issued in (``issue_licence``), and checked entry by entry against it. The
    discharges are read BY POSITION, so two factors whose entries carry one
    label (two stations of one device model do) are never confused. ``None``
    where the factor has entries and its licence does not name a discharge for
    each of them in that order: the joint list then gets no licence and
    :func:`assemble_factor_emissions` refuses it ``licence_missing``
    (``req:licence-record``: "it emits the record only when every entry has its
    certificate and what discharges it").
    """
    licence = artefact.attack_set_license
    entries = artefact.constraint_list
    if licence is None:
        return None if entries else ()
    discharges = licence.discharge_per_entry
    if len(discharges) != len(entries) or any(
        discharge.entry != entry.label
        for discharge, entry in zip(discharges, entries, strict=True)
    ):
        return None
    return tuple(discharges)


def _supplier_version(discharges: Sequence[EntryDischarge]) -> str:
    """Return the supplier version the first supplier-reading discharge names."""
    return next(
        str(item.supplier_version)
        for item in discharges
        if item.supplier_version is not None
    )


def _joint_licence(
    factors: Sequence[FactorCall],
    artefacts: Sequence[ProofReductionArtifact],
    scoped: Sequence[tuple[Label, ProofReductionArtifact, ConstraintEntry]],
    labels: Sequence[Label],
    parties: Sequence[Label],
) -> AttackSetLicence | None:
    """Return the licence of the joint list, BUILT PER ENTRY over that list.

    PRESENT EXACTLY WHEN THE JOINT LIST IS NON-EMPTY, which is the presence rule
    of every licence this module issues.

    IT IS THE JOINT LIST'S LICENCE AND NOT A COPY OF ONE FACTOR'S. The record
    "NAMES: the theorem, the hypothesis it was discharged on (the certificate,
    PER ENTRY), the supplier fact that discharges it (A-RECV with the artifact's
    module_version), the source mode, the adjoint-form set the composite attacks
    are asserted to lie in, AND THE CONSTANTS THE ENTRIES CARRY", so each of
    those is assembled over EVERY entry of the joint list (copying the shared fields
    from the first factor would give an artefact version and a hypothesis list that name
    one factor's entries only):

    * ``hypothesis_per_entry`` carries one line per joint entry, naming its
      factor and the certificate discharged on THAT factor's channel;
    * ``discharge_per_entry`` carries, per joint entry, the discharge its
      factor's own licence names for it at its position
      (``req:licence-record``), and ``discharging_receiver_fact`` and
      ``receiver_spec_version`` are DERIVED from them: A-RECV per factor, and
      by factor the supplier artefact of every factor one of whose entries'
      discharges reads it, because A-RECV "NAMES THE RECEIVER ARTIFACT BY
      VERSION" and there is one per factor; both ``None`` where no discharge
      reads a supplier fact;
    * ``admissible_set`` names the condition of every entry -- the party-local
      condition eq:attsetpl for a tagged one and the scalar condition for an
      untagged one -- so that the set the composed attacks are asserted to lie
      in is the one the whole list cuts out;
    * ``source_mode`` is the one mode every factor declared, which
      :func:`_one_source_mode` has already established.

    WHAT THE PARTY-LOCAL ROW NAMES, per entry: ``thm:licence`` (v); the FACTOR
    and that factor's channel witness, with the party beside it; the certificate
    discharged ON THAT FACTOR'S CHANNEL, with the supplier fact and artefact
    version its discharge reads (``None`` where it reads none);
    ``def:attset``'s party-local set, Eq.
    ``eq:attsetpl``; and the scalar set the same entry is ALSO admissible in,
    for the lifted operator at the same constant. WHAT IS NOT NAMED IS A JOINT
    CHANNEL: there is none, the emission being factorised.

    AT ONE FACTOR IT IS THE ARTEFACT'S OWN LICENCE, THE OBJECT AND NOT A COPY.
    "At one factor ... what is emitted is that instance's artefact, every entry
    untagged" (``thm:emitted-product`` (vi)), so the licence of a one-factor
    emission is the record :func:`certiqs_key.reductions.constraints.issue_licence`
    already issued for that artefact: re-assembling it here would emit a second,
    differently-worded record for one licence and put the one-factor emission a
    wording apart from today's artefact.
    """
    if not scoped:
        return None
    if len(artefacts) == 1:
        return artefacts[0].attack_set_license
    per_factor: dict[Label, tuple[EntryDischarge, ...]] = {}
    for label, artefact in zip(labels, artefacts, strict=True):
        found = _factor_discharges(artefact)
        if found is None:
            return None
        per_factor[label] = found
    position: dict[Label, int] = dict.fromkeys(labels, 0)
    party_of: Mapping[Label, Label] = dict(zip(labels, parties, strict=True))
    mode = factors[0].call.declaration.source_mode
    rows: list[PartyLocalLicence] = []
    hypotheses: list[str] = []
    discharges: list[EntryDischarge] = []
    reading: list[Label] = []
    conditions: list[str] = []
    for factor, artefact, entry in scoped:
        # PER ENTRY, WHAT DISCHARGES IT (req:licence-record): the discharge
        # that factor's own licence names for the entry AT ITS POSITION, which
        # the factor's instance established on that factor's channel.
        discharge = per_factor[factor][position[factor]]
        position[factor] += 1
        discharges.append(discharge)
        if discharge.supplier_fact is not None and factor not in reading:
            reading.append(factor)
        scope = entry.scope
        witness = entry_link_witness(artefact)
        named = "the one factor" if scope is None else f"factor {scope}"
        certificate = (
            f"eq:certificate for {entry.label} on {named}: "
            f"{witness}+({entry.label}) {entry.relation.value} "
            f"{entry.constant} 1_B"
        )
        hypotheses.append(certificate)
        if entry.tag is None or scope is None:
            conditions.append(
                admissible_set_expression((entry,), mode)
            )
            continue
        conditions.append(party_local_set_expression(entry, scope, mode))
        rows.append(
            PartyLocalLicence(
                entry_label=entry.label,
                factor=scope,
                party=party_of[scope],
                factor_channel_witness=witness,
                certificate=(
                    f"Lambda_{scope}+({entry.label}) "
                    f"{entry.relation.value} {entry.constant} 1_B_{scope}, "
                    "discharged on THAT FACTOR'S channel (thm:emitted-product "
                    "(iii))"
                ),
                discharging_receiver_fact=(
                    None
                    if discharge.supplier_fact is None
                    else "Assumption A-RECV: that factor's receiver artefact's "
                    "claims are that factor's device's"
                ),
                factor_spec_version=discharge.supplier_version,
                admissible_set=party_local_set_expression(entry, scope, mode),
                also_admissible_as_a_scalar=party_local_scalar_set_expression(
                    entry, scope
                ),
            )
        )
    return AttackSetLicence(
        theorem="Theorem thm:licence (PR11), with (v) per tagged entry",
        hypothesis_per_entry=tuple(hypotheses),
        discharge_per_entry=tuple(discharges),
        discharging_receiver_fact=(
            "Assumption A-RECV, PER FACTOR: each factor's receiver artefact's "
            "claims are that factor's device's"
            if reading
            else None
        ),
        receiver_spec_version=(
            "; ".join(
                f"{label}: {_supplier_version(per_factor[label])}"
                for label in labels
                if label in reading
            )
            if reading
            else None
        ),
        source_mode=mode,
        admissible_set=(
            "the composed attacks lie in the set cut out by every entry of the "
            "joint list: " + "; ".join(conditions)
        ),
        party_local_entries=tuple(rows),
    )
